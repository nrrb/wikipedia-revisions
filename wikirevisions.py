from wikitools import wiki, api
import dateutil.parser
import calendar
import csv
from cStringIO import StringIO
from codecs import getincrementalencoder
import argparse
import inspect

_DEPTH = 10 # Crossing our fingers that this doesn't break the Internet
_FIELDORDER = [u'page_id', u'userid', u'page_title', u'user', u'timestamp', u'revid', u'size']
_ENCODING = 'UTF-8'

def parse_arguments():
	parser = argparse.ArgumentParser(description='Batch processing of crawling Wikipedia categories.')
	parser.add_argument('-categoryfile', metavar='filename', dest='category_file', type=argparse.FileType('r'), required=True,
						help='The name of a text file containing a list of Wikipedia categories to crawl.')
	parser.add_argument('-excludefile', metavar='filename', dest='exclude_file', type=argparse.FileType('r'),
						help='The name of a text file containing a list of Wikipedia categories and/or articles to exclude from crawling.')
	parser.add_argument('-depth', metavar='depth', dest='depth', type=int, default=_DEPTH,
						help='The crawling depth for the categories, integer >= 0. Default is %d.' % (_DEPTH))
	args = parser.parse_args()
	# We want to convert this from a Namespace to a dict and ignore the hidden attributes
	args = dict([(k, v) for k,v in inspect.getmembers(args) if k.find('_')!=0])
	return args

def write_csv(revisions, field_order, output_file, include_header=False):	
	class DictUnicodeWriter(object):
		"""
		Code borrowed from http://stackoverflow.com/a/5838817
		"""
		def __init__(self, f, fieldnames, dialect=csv.excel, encoding=_ENCODING, **kwds):
			# Redirect output to a queue
			self.queue = StringIO()
			self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)
			self.stream = f
			self.encoder = getincrementalencoder(encoding)()
		def writerow(self, D):
			self.writer.writerow(dict((k, v.encode(_ENCODING)) for k,v in D.iteritems()))
			# Fetch UTF-8 output from the queue ...
			data = self.queue.getvalue()
			data = data.decode(_ENCODING)
			# ... and reencode it into the target encoding
			data = self.encoder.encode(data)
			# write to the target stream
			self.stream.write(data)
			# empty queue
			self.queue.truncate(0)
		def writerows(self, rows):
			for D in rows:
				self.writerow(D)
		def writeheader(self):
			self.writer.writeheader()
	dw = DictUnicodeWriter(output_file, 
						field_order,
						delimiter=',',
						quotechar='"')
	if include_header:
		dw.writeheader()
	for revision in revisions:
		for k, v in revision.items():
			# Some of these are integers and need to be converted to strings for the CSV writer
			revision[k] = unicode(v)
		dw.writerow(revision)

def iso_time_to_epoch(iso_timestamp):
	py_timestamp = dateutil.parser.parse(iso_timestamp)
	seconds_since_epoch = calendar.timegm(py_timestamp.timetuple())
	return seconds_since_epoch

def wikipedia_query(query_params):
	"""
	An extremely basic wrapper for the wikitools api.
	"""
	site = wiki.Wiki() # This defaults to en.wikipedia.org
	query_params['action'] = 'query'
	request = api.APIRequest(site, query_params)
	result = request.query()
	return result[query_params['action']]

def category_articles(category_name, excluded=[], depth=_DEPTH):
	'''
	Input: 
	category_name - The name of a Wikipedia(en) category, e.g. 'Category:2001_fires'. 
	excluded - A list of category and/or article names to be excluded from the results. If
		a category name is included, that category will not be explored for sub-articles. 
	Output:
	articles - A list of articles that are found within the given category or one of its
		subcategories, explored recursively. Each article will be a dictionary object with
		the keys 'title' and 'id' with the values of the individual article's title and 
		page_id respectively. 
	'''
	#print 'Exploring %s' % (category_name)
	articles = []
	if category_name in excluded:
		return articles
	if depth < 0:
		return articles
	results = wikipedia_query({'list': 'categorymembers', 
						'cmtitle': category_name, 
						'cmtype': 'page',
						'cmlimit': '500'})	
	if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
		for i, page in enumerate(results['categorymembers']):
			article = dict(title=page['title'], id=page['pageid'])
			if article['title'] not in excluded:
				articles.append(article)
	results = wikipedia_query({'list': 'categorymembers',
						'cmtitle': category_name,
						'cmtype': 'subcat',
						'cmlimit': '500'})
	subcategories = []
	if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
		for i, category in enumerate(results['categorymembers']):
			cat_title = category['title']
			if cat_title not in excluded:
				subcategories.append(cat_title)
	for category in subcategories:
		articles = articles + category_articles(category, excluded=excluded, depth=depth-1)
	return articles

def article_revisions(article, revision_properties=['ids', 'timestamp', 'user', 'userid', 'size']):
	'''
	Input: 
	article - A dictionary with keys 'title' and 'id', the title and page_id for the 
		wikipedia article of interest. This is meant to couple nicely with the output
		from the category_articles() function. 
	revision_properties - A list of properties to be returned for each revision. The full list
		of properties can be found here: https://www.mediawiki.org/wiki/API:Properties#revisions_.2F_rv
	Output:
	revisions - A list of revisions for the given article, each given as a dictionary. This will
		include all properties as described by revision_properties, and will also include the
		title and id of the source article. 
	'''
	if 'title' not in article or 'id' not in article:
		raise LookupError
	revisions = []
	result = wikipedia_query({'titles': article['title'], 
							'prop': 'revisions', 
							'rvprop': '|'.join(revision_properties),
							'rvlimit': '5000'})
	if result and 'pages' in result.keys():
		page_number = result['pages'].keys()[0]
		r = result['pages'][page_number]['revisions']
		r = sorted(r, key=lambda revision: revision['timestamp'])
		for i, revision in enumerate(r):
			revision[u'page_title'] = article['title']
			revision[u'page_id'] = article['id']
			# The timestamp as supplied by wikitools is in the standard ISO 
			# timestamp format. We may want to use this more flexibly in Python, 
			# so we'll convert it to number of seconds since the UNIX epoch.
			seconds_since_epoch = iso_time_to_epoch(revision['timestamp'])
			revision[u'timestamp'] = seconds_since_epoch
			revisions.append(revision)
	return revisions	

def main():
	args = parse_arguments()
	categories = args['category_file'].readlines()
	args['category_file'].close()
	exclusions = args['exclude_file'].readlines()
	args['exclude_file'].close()
	for i,cat in enumerate(categories):
		categories[i] = cat.rstrip().lstrip().decode(_ENCODING)
	exclusions = [ex.rstrip().lstrip().decode(_ENCODING) for ex in exclusions]
	depth = args['depth']
	for category in categories:
		print 'Processing "%s".' % (category)
		output_filename = category.encode(_ENCODING).replace(':', '-') + '.csv'
		articles = category_articles(category, excluded=exclusions, depth=depth)
		revisions = []
		for article in articles:
			revisions += article_revisions(article)
		############################################################
		# Here's where we fix the malformed user/userid values
		for i in xrange(len(revisions)):
			revision = revisions[i]
			if 'userhidden' in revision:
				revision['user'] = 'userhidden'
				revision['userid'] = ''
			if 'userid' in revision and revision['userid']==0 and 'anon' in revision:
				# Then we'll take the user, which contains an IP address,
				# and re-format it from vvv.xxx.yyy.zzz to 
				# vvvxxxyyyzzz0000000000
				ip = revision['user']
				revision['userid'] = ''.join(['0'*(3-len(o))+o for o in ip.split('.')]) + '0'*10				
		############################################################
			# Remove the extraneous keys
			revision = dict((k, v) for k, v in revision.iteritems() if k in _FIELDORDER)
			revisions[i] = revision
		with open(output_filename, 'w') as output_file:
			write_csv(revisions, _FIELDORDER, output_file)

def test():
	from pprint import pprint
	articles = category_articles('Category:2001_fires')
	revisions = article_revisions(articles[0])
	pprint(revisions[0])
	return revisions

if __name__=="__main__":
	main()

