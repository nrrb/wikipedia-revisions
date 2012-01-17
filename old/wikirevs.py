from wikitools import wiki, api
import dateutil.parser
import calendar
import os
import codecs

def wikipedia_query(query_params):
	"""
	An extremely basic wrapper for the wikitools api.
	"""
	site = wiki.Wiki() # This defaults to en.wikipedia.org
	request = api.APIRequest(site, query_params)
	result = request.query()
	return result[query_params['action']]

class WikiCategory:
	# When an object is instantiated, the crawling begins. 
	def __init__(self, page_title, depth=0, excluded=[], verbose=False):
		self.page_title = page_title
		self.subcategories = []
		self.articles = []
		self.excluded = (page_title in excluded)
		self.depth = depth
		self.excluded = excluded
		self.verbose = verbose
		self._load()
		return
	def __repr__(self):
		return repr(dict(page_title=self.page_title, type='category'))
	def _load(self):
		if self.verbose:
			print 'Crawling %s:' % self.page_title
		if self.excluded:
			return
		if self.depth < 0:
			return
		self._load_articles()
		if self.verbose:
			print 'Found %d articles in %s.' % (len(self.articles), self.page_title)
		for article in self.articles:
			if article.page_title in self.excluded:
				article.excluded = True
		if depth > 0:
			self._load_subcategories()
	def collect_articles(self):
		# In its basic state, the WikiCategory object only stores a list of articles immediately
		# listed on the wiki page. Articles that link from any sub-categories are not explicitly 
		# included. We must traverse the tree of categories and collect the articles as leaves.  
		articles = set()
		articles.update([a for a in self.articles if not a.excluded])
		for category in self.subcategories:
			if not category.excluded:
				articles.update(category.collect_articles())
		return list(articles)
	def revisions(self):
		revisions = []
		for article in self.collect_articles():
			revisions += article.revisions()
		return revisions
	def _load_articles(self):
		results = wikipedia_query({'action': 'query', 
									'list': 'categorymembers', 
									'cmtitle': self.page_title, 
									'cmtype': 'page',
									'cmlimit': '500'})
		if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
			for i, page in enumerate(results['categorymembers']):
				self.articles.append(WikiArticle(page_title=page['title'],
													page_id=page['pageid']))
				self.articles[-1].excluded = (page['title'] in self.excluded)
	def _load_subcategories(self):
		results = wikipedia_query({'action': 'query',
									'list': 'categorymembers',
									'cmtitle': self.page_title,
									'cmtype': 'subcat',
									'cmlimit': '500'})
		subcategories = []
		if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
			for i, category in enumerate(results['categorymembers']):
				self.subcategories.append(WikiCategory(page_title=category['title'], 
														depth=self.depth-1, 
														excluded=self.excluded))
				
class WikiArticle:
	def __init__(self, page_title, page_id=-1):
		self.page_title = page_title
		self.page_id = page_id
		self.query_limit = 5000
		self.excluded = False
		return
	def __repr__(self):
		return repr(dict(page_title=self.page_title, page_id=self.page_id, type='article'))
	def __eq__(self, other):
		return (self.page_title == other.page_title)
	def __cmp__(self, other):
		return cmp(self.page_title, other.page_title)
	def __hash__(self):
		return hash(self.page_title)
	def revisions(self):
		revs = []
		result = wikipedia_query({'action': 'query', 
								'titles': self.page_title, 
								'prop': 'revisions', 
								'rvprop': 'ids|timestamp|user|userid|size',
								'rvlimit': str(self.query_limit)})
		if result and 'pages' in result.keys():
			page_number = result['pages'].keys()[0]
			revisions = result['pages'][page_number]['revisions']
			revisions = sorted(revisions, key=lambda revision: revision['timestamp'])
			for i, revision in enumerate(revisions):
				# The timestamp as supplied by wikitools is in the standard ISO 
				# timestamp format. We may want to use this more flexibly in Python, 
				# so we'll convert it to number of seconds since the UNIX epoch.
				iso_timestamp = revision['timestamp']
				py_timestamp = dateutil.parser.parse(iso_timestamp)
				seconds_since_epoch = calendar.timegm(py_timestamp.timetuple())
				if 'userhidden' in revision.keys():
					revision['user'] = "userhidden"
					revision['userid'] = ''
				if 'userid' in revision.keys() and revision['userid'] == 0 and 'anon' in revision.keys():
					# Then we'll take the user, which contains an IP address,
					# and re-format it from vvv.xxx.yyy.zzz to 
					# vvvxxxyyyzzz0000000000
					ip = revision['user']
					revision['userid'] = ''.join(['0'*(3-len(octet))+octet for octet in ip.split('.')]) + "0000000000"
				revs.append(WikiRevision(dict(page_title=self.page_title, 
												page_id=self.page_id,
												user=revision['user'],
												user_id=str(revision['userid']),
												timestamp=str(seconds_since_epoch),
												rev_id=str(revision['revid']),
												size=str(revision['size']))))

class WikiRevision:
	def __init__(self, values_dict):
		self.values = values_dict
		return
	def __repr__(self):
		return repr(self.values)	
	def keys(self):
		return self.values.keys()




def RunProgram():
	root_category = WikiCategory(root_category)
	# Pre-load all sub-category and article objects
	root_category.load(depth=category_depth, 
						excluded=excluded)
	# Get 'em!!
	revisions = root_category.all_revisions()		