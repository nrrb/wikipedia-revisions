# coding: utf-8
_sample_article_name = 'Social_network'
_sample_category_name = 'Category:21st-century_aviation_accidents_and_incidents'

def wikipedia_query(query_params):
	"""
	An extremely basic wrapper for the wikitools api.
	"""
	from wikitools import wiki, api
	site = wiki.Wiki() # This defaults to en.wikipedia.org
	request = api.APIRequest(site, query_params)
	result = request.query()
	return result[query_params['action']]

def page_revisions(page_title, rvlimit=5000, debug=False):
	"""
	Given the proper name of a page on Wikipedia, this will return
	basic identifying information all revisions. Each revision entry
	will inclue the original page title, the user who made the 
	revision, the timestamp of the revision (in seconds since the
	UNIX epoch - 1/1/1970), and the unique revision id for the
	page.
	"""
	import dateutil.parser
	import calendar
	if debug:
		print "Getting revisions for page '%s'." % page_title
	result = wikipedia_query({'action': 'query', 
								'titles': page_title, 
								'prop': 'revisions', 
								'rvlimit': str(rvlimit)})
	revisions = []
	if result and 'pages' in result.keys():
		page_number = result['pages'].keys()[0]
		revisions = result['pages'][page_number]['revisions']
		revisions = sorted(revisions, key=lambda revision: revision['timestamp'])
		if debug:
			print "~~@ Found %d revisions." % len(revisions)
		for i, revision in enumerate(revisions):
			# The timestamp as supplied by wikitools is in the standard ISO 
			# timestamp format. We may want to use this more flexibly in Python, 
			# so we'll convert it to number of seconds since the UNIX epoch.
			iso_timestamp = revision['timestamp']
			py_timestamp = dateutil.parser.parse(iso_timestamp)
			seconds_since_epoch = calendar.timegm(py_timestamp.timetuple())
			revisions[i] = {'title': page_title, 
							'user': revision['user'], 
							'timestamp': seconds_since_epoch, 
							'revid': revision['revid']}
	return revisions

def category_pages(category_title, depth=1, debug=False):
	"""
	Given the proper name of a category on Wikipedia, this will return
	a list of all proper page titles (not categories) found within that
	category. With 'depth' set to 1 (default), this will return only
	the pages found immediately within the given category. If depth is
	2, pages belonging to the subcategories will also be included.

	*** Be very cautious with setting depth higher than 2, as the number
	of pages and sub-categories grows exponentially with depth.
	"""
	params = {'action': 'query', 
				'list': 'categorymembers', 
				'cmtitle': category_title, 
				'cmtype': 'page',
				'cmlimit': '500'}
	if debug:
		print "Querying Wikipedia for sub-pages of '%s'..." % (category_title)
		print "Depth = %d" % depth
	results = wikipedia_query(params)
	pages = []
	if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
		if debug:
			print "Found %d sub-pages!" % (len(results['categorymembers']))
		pages = [page['title'] for page in results['categorymembers']]
		if depth > 1:
			subcategories = category_subcategories(category_title, debug=debug)
			for subcategory in subcategories:
				pages += category_pages(subcategory, depth=depth - 1, debug=debug)
				if depth > 2:
					subsubcategories = category_subcategories(subcategory, debug=debug)
					for subsubcategory in subsubcategories:
						if subsubcategory not in subcategories:
							subcategories.append(subsubcategory)
	return pages

def category_subcategories(category_title, debug=False):
	"""
	Given the proper name of a category on Wikipedia, this
	will return a list of the titles only of all sub-categories. If
	there are no sub-categories, the list returned is empty. 
	"""
	params = {'action': 'query',
				'list': 'categorymembers',
				'cmtitle': category_title,
				'cmtype': 'subcat',
				'cmlimit': '500'}
	if debug:
		print "Querying Wikipedia for sub-categories of '%s'..." % (category_title)
	results = wikipedia_query(params)
	subcategories = []
	if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
		if debug:
			print "Found %d sub-categories!" % (len(results['categorymembers']))
		subcategories = [category['title'] for category in results['categorymembers']]
	return subcategories
			

def main():
	import csv
	pages = category_pages(_sample_category_name, depth=2, debug=True)
	all_revisions = []
	for page in pages:
		all_revisions += page_revisions(page, debug=True)
	csv_file = open(_sample_category_name + ".csv", "wb")
	dw = csv.DictWriter(csv_file, 
						['title', 'user', 'timestamp', 'revid'],
						delimiter=',', 
						quotechar='"')
	dw.writerows(all_revisions)
	csv_file.close()

if __name__ == "__main__":
	main()
