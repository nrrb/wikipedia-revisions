from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base
import simplejson
import requests

# How many revisions are returned by each API call
# Keep this at 1 due to https://bugzilla.wikimedia.org/show_bug.cgi?id=29223
rvlimit=1

pageids = {\
28486453: 'http://en.wikipedia.org/w/index.php?title=2010_Copiap%C3%B3_mining_accident',
27046954: 'http://en.wikipedia.org/wiki/Deepwater_Horizon_oil_spill',
25804468: 'http://en.wikipedia.org/wiki/2010_Haiti_earthquake',
31150160: 'http://en.wikipedia.org/wiki/2011_T%C5%8Dhoku_earthquake_and_tsunami',
32496189: 'http://en.wikipedia.org/wiki/2011_Norway_attacks',
7746616: 'http://en.wikipedia.org/wiki/Death_of_Osama_bin_Laden',
168079: 'http://en.wikipedia.org/wiki/2010_FIFA_World_Cup',
2401717: 'http://en.wikipedia.org/wiki/Super_Bowl_XLV'}

# For running on sonicserver:
#engine = create_engine('mysql://wikirevs:5U5557f5LqmAG2s@localhost:3306/wikipedia_revisions', echo=False)
engine = create_engine('mysql://wiki:pedia@localhost:3306/wikipedia', echo=False)
Base = declarative_base(engine)

class Revision(Base):
	__tablename__ = 'revisions'
	__table_args__ = {'autoload': True, 'mysql_engine': 'MyISAM'}
	id = Column(Integer, primary_key=True, autoincrement=True)	
	pageid = Column(Integer)
	article_title = Column(Unicode(255))
	editor_id = Column(Integer)
	editor_name = Column(Unicode(255))
	revid = Column(Integer)
	parentid = Column(Integer)
	timestamp = Column(DateTime)
	comment = Column(UnicodeText)
	diff = Column(UnicodeText)

metadata = Base.metadata
Session = sessionmaker(bind=engine)
session = Session()

def store_revisions(revs_json, pageid):
	# Up to ['query']['pages']
	page_info = revs_json[str(pageid)]
	if 'revisions' not in page_info:
		return False
	for revision in page_info['revisions']:
		revid = revision['revid']
		parentid = revision.get('parentid', -1)

		revobj = Revision(pageid = pageid,
							article_title = page_info['title'],
							editor_id = revision.get('userid',-1),
							editor_name = revision.get('user','userhidden'),
							revid = revid,
							parentid = parentid,
							timestamp = revision['timestamp'],
							comment = revision.get('comment', ''),
							diff = revision['diff']['*'])
		session.add(revobj)
	return True

def get_revisions(revid, pageid):
	request = 'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&format=json&rvprop=ids%7Ctimestamp%7Cuser%7Cuserid%7Ccomment%7Ccontent&rvlimit='+str(rvlimit)+'&rvdiffto=prev&rvstartid='+str(revid)+'&pageids='+str(pageid)
	r = requests.get(request)
	sj = simplejson.loads(r.text)
	results = sj['query']['pages']
	return results

def get_revids(pageid):
	revids = list()
	first_request = 'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&format=json&rvprop=ids&rvlimit=500&pageids='+str(pageid)
	r = requests.get(first_request)
	sj = simplejson.loads(r.text)
	revs = sj['query']['pages'][str(pageid)]['revisions']
	revids += [rev['revid'] for rev in revs]
	revid_next = revs[-1]['parentid']
	while 'parentid' in revs[-1] and revid_next > 0:
		request = 'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&format=json&rvprop=ids&rvlimit=500&rvdiffto=prev&rvstartid='+str(revid_next)+'&pageids='+str(pageid)
		r = requests.get(request)
		sj = simplejson.loads(r.text)
		revs = sj['query']['pages'][str(pageid)]['revisions']
		revids += [rev['revid'] for rev in revs]
		revid_next = revs[-1]['parentid']
	return revids

if __name__=="__main__":
	for pageid in pageids:
		revids = get_revids(pageid)
		print 'There are %d revisions for pageid %d.' % (len(revids), pageid)
		revids_stored = session.query(Revision.revid).filter(Revision.pageid==pageid).all()
		revids_stored = [r[0] for r in revids_stored]
		revids = set(revids).symmetric_difference(set(revids_stored))
		print '%d revisions are already in the database, working on %d more.' % (len(revids_stored), len(revids))	
		for revid in revids:
			request = 'http://en.wikipedia.org/w/api.php?action=query&prop=revisions&format=json&rvprop=ids%7Ctimestamp%7Cuser%7Cuserid%7Ccomment%7Ccontent&rvlimit='+str(rvlimit)+'&rvdiffto=prev&rvstartid='+str(revid)+'&pageids='+str(pageid)
			revisions = get_revisions(revid, pageid)
			if not store_revisions(revisions, pageid):
				print 'Error storing revision with revid %d for pageid %d!' % (revid, pageid)
		session.commit()