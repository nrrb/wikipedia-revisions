from wikitools import wiki, api
import argparse
import dateutil.parser
import calendar
import shutil
import os
import csv
import cStringIO
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
	def __init__(self, page_title):
		self.page_title = page_title
		self.subcategories = []
		self.articles = []
		self.are_articles_loaded = False
		self.are_subcategories_loaded = False
		self.is_loaded = False
		self.excluded = False
		return

	def __repr__(self):
		return repr(dict(page_title=self.page_title, type='category'))

	def load(self, depth=0, debug=False, 
				excluded_articles=[], 
				excluded_categories=[]):
		if depth < 0:
			return
		self.excluded_articles = excluded_articles
		self.excluded_categories = excluded_categories
		self.load_articles()
		for article in self.articles:
			if article.page_title in self.excluded_articles:
				article.excluded = True
			else:
				article.load_revisions()
		self.is_loaded = True
		if depth > 0:
			self.load_subcategories()
			for category in self.subcategories:
				if category.page_title in self.excluded_categories:
					category.excluded = True
				else:
					category.load(depth=depth-1, debug=debug,
									excluded_articles=excluded_articles,
									excluded_categories=excluded_categories)

	def all_articles(self):
		articles = set()
		articles.update([a for a in self.articles if not a.excluded])
		for category in self.subcategories:
			if not category.excluded:
				articles.update(category.all_articles())
		return list(articles)

	def all_revisions(self):
		revisions = []
		for article in self.all_articles():
			revisions += article.revisions
		return revisions

	def load_articles(self):
		"""
		Given the proper name of a category on Wikipedia, this will return
		a list of all proper page titles (not categories) found within that
		category.
		"""
		params = {'action': 'query', 
					'list': 'categorymembers', 
					'cmtitle': self.page_title, 
					'cmtype': 'page',
					'cmlimit': '500'}
		results = wikipedia_query(params)
		if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
#			print "(%dP) %s" % (len(results['categorymembers']), self.page_title)
			for i, page in enumerate(results['categorymembers']):
#				print "\t%d. %s" % (i+1, page['title'])
				self.articles.append(WikiArticle(page_title=page['title'],
												page_id=page['pageid']))
		self.are_articles_loaded = True

	def load_subcategories(self):
		params = {'action': 'query',
					'list': 'categorymembers',
					'cmtitle': self.page_title,
					'cmtype': 'subcat',
					'cmlimit': '500'}
		results = wikipedia_query(params)
		subcategories = []
		if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
#			print "(%dC) %s" % (len(results['categorymembers']), self.page_title)
			for i, category in enumerate(results['categorymembers']):
#				print "\t%d. %s" %(i+1, category['title'])
				self.subcategories.append(WikiCategory(page_title=category['title']))
			self.are_subcategories_loaded = True
				
class WikiArticle:
	def __init__(self, page_title, page_id=-1):
		self.page_title = page_title
		self.page_id = page_id
		self.revisions = []
		self.are_revisions_loaded = False
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

	def load_revisions(self):
		result = wikipedia_query({'action': 'query', 
								'titles': self.page_title, 
								'prop': 'revisions', 
								'rvprop': 'ids|timestamp|user|userid|size',
								'rvlimit': str(self.query_limit)})
		if result and 'pages' in result.keys():
			page_number = result['pages'].keys()[0]
			revisions = result['pages'][page_number]['revisions']
			revisions = sorted(revisions, key=lambda revision: revision['timestamp'])
#			print "(%dR) %s" % (len(revisions), self.page_title)
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
				self.revisions.append(WikiRevision(dict(page_title=self.page_title, 
													page_id=self.page_id,
													user=revision['user'],
													user_id=str(revision['userid']),
													timestamp=str(seconds_since_epoch),
													rev_id=str(revision['revid']),
													size=str(revision['size']))))
			self.are_revisions_loaded = True

class WikiRevision:
	def __init__(self, values_dict):
		self.values = values_dict
		return
	def __repr__(self):
		return repr(self.values)
	
	def keys(self):
		return self.values.keys()

class DictUnicodeWriter(object):
	"""
	Code borrowed from http://stackoverflow.com/a/5838817
	"""
	def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwds):
		# Redirect output to a queue
		self.queue = cStringIO.StringIO()
		self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)
		self.stream = f
		self.encoder = codecs.getincrementalencoder(encoding)()

	def writerow(self, D):
		self.writer.writerow({k:v.encode("utf-8") for k,v in D.items()})
		# Fetch UTF-8 output from the queue ...
		data = self.queue.getvalue()
		data = data.decode("utf-8")
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


def RunProgram():
	import tempfile
	from string import find

	# Get the name of the root category
	root_category = ''
	while root_category == '':
		root_category = raw_input("Enter a category name: ")
	if find(root_category.lower(), "category:") != 0:
		# Being a little too helpful, probably!
		root_category = u'Category:' + root_category
	# Get the depth of crawling from this root. A depth of 0 means
	# that only the immediate sub-pages (and sub-category names) will
	# be returned. A depth of 1 will then return the same information
	# but for each of those sub-category names of the root category. 
	try:
		category_depth = int(raw_input("Depth to crawl (0 or higher): "))
	except ValueError:
		print "Please enter an integer greater than or equal to 0."
	# Get any category or article names that you'd like excluded. 
	# allow for them to be separated by any combination of spaces, 
	# commas, semi-colons, and quotes. a best guess csv parser?
	excluded_all = raw_input("""Enter a list of category and/or article names to be excluded from the crawl. (separate names by commas): """)
	excluded_all = excluded_all.replace(',',' ').replace(';',' ')
	exclusions = excluded_all.split()
	exclusions = [ex.replace('_',' ') for ex in exclusions]
	ex_cat = [ex for ex in exclusions if find(ex.lower(),'category:')==0]
	ex_art = [ex for ex in exclusions if ex not in ex_cat]
	# Get the name of the desired output file
	output_filename = raw_input("""Enter output CSV filename: """)
	output_filepath = os.path.join(os.getcwd(), output_filename)

	root_category = WikiCategory(root_category)
	# Pre-load all sub-category and article objects
	root_category.load(depth=category_depth, 
						excluded_articles=ex_art, 
						excluded_categories=ex_cat)
	# Get 'em!!
	revisions = root_category.all_revisions()
	if len(revisions) > 0:
		# Write this quickly to a temp file in CSV format, lest we
		# have any problem re-saving to a new filename. 
		with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as csv_file:
			dw = DictUnicodeWriter(csv_file, 
								['page_id', 'user_id', 'page_title', 'user', 'timestamp', 'rev_id', 'size'],
								delimiter=',',
								quotechar='"')
			dw.writeheader()
			for revision in revisions:
				for k, v in revision.values.items():
					# Some of these are integers and need to be converted to strings for the CSV writer
					revision.values[k] = unicode(v)
				dw.writerow(revision.values)
#			print csv_file.name
		print "Saved temporarily to %s. Now moving to %s." % (csv_file.name, output_filepath)
		shutil.move(csv_file.name, output_filepath)
	else:
		print "There was nothing there!"

def process_arguments():
	parser = argparse.ArgumentParser(description='Retrieve revision information for Wikipedia article(s).')
	parser.add_argument('-c', '--category', metavar='category_title', dest='category',
						help='The name of a Wikipedia category (e.g. Category:2009_earthquakes).')
	parser.add_argument('-a', '--article', metavar='article_title', dest='article',
						help='The name of a Wikipedia article (e.g. 2009_Bhutan_earthquake).')
	parser.add_argument('-i', '--input', metavar='input_filename', dest='infilename',
						help='Name of input file a list of articles and categories, one per line.')
	parser.add_argument('-d', '--depth', metavar='depth', dest='depth', default=0,
						help='The crawling depth for the given category, integer >= 0. Default is 0.')
	parser.add_argument('-xc', metavar='excluded_categories', dest='excluded_categories',
						help='A list of categories to exclude from the results, separated by commas (e.g. Category:a,Category:b).')
	parser.add_argument('-xa', metavar='excluded_articles', dest='excluded_articles', 
						help='A list of articles to exclude from the results, separated by commas (e.g. article1,article2).')
	parser.add_argument('-xf', metavar='exclusions_filename', dest='exclusions_filename',
						help='Name of file containing list of articles and/or categories, one per line, to exclude from the results.')
	parser.add_argument('-o', '--output', metavar='output_filename', dest='outfilename', required=True,
						help='Name of output CSV file. *REQUIRED*')
	args = parser.parse_args()	
	if not (args.infilename or args.article or args.category):
		parser.exit(status=-1, message='At least one form of input (article, category, or infile) is needed!\n')
	articles = []
	categories = []
	excluded_articles = []
	excluded_categories = []
	if args.excluded_articles:
		excluded_articles = args.excluded_articles.split(',')
	if args.excluded_categories:
		excluded_categories = args.excluded_categories.split(',')
	if args.exclusions_filename:
		with open(args.exclusions_filename, 'rb') as exclusions_file:
			titles = exclusions_file.readlines()
		for title in titles:
			if title.find('Category:')==0:
				excluded_categories.append(title.rstrip())
			else:
				excluded_articles.append(title.rstrip())
	if args.article:
		articles.append(args.article)
	if args.category:
		categories.append(args.category)
	if args.infilename:
		titles = []
		with open(args.infilename, 'rb') as infile:	
			titles = infile.readlines()
		for title in titles:
			if title.find('Category:')==0:
				categories.append(title.rstrip())
			else:
				articles.append(title.rstrip())
	articles = list(set(articles))
	categories = list(set(categories))
	return (articles, categories, excluded_articles, excluded_categories, depth, outfilename)

if __name__=='__main__':
	articles, categories, excluded_articles, excluded_categories, depth, outfilename = get_arguments()
	all_articles = articles[:]
	for category in categories:
		