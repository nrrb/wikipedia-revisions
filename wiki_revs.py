# coding: utf-8
sample_article_name = 'Social_network'
sample_category_name = 'Category:21st_century'

def wikipedia_query(query_params):
	"""
	An extremely basic wrapper for the wikitools api.
	"""
	from wikitools import wiki, api
	site = wiki.Wiki() # This defaults to en.wikipedia.org
	request = api.APIRequest(site, query_params)
	result = request.query()
	return result[query_params['action']]

def wiki_page_revisions(page_title, rvlimit=5000):
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
	result = wikipedia_query({'action': 'query', 
								'titles': page_title, 
								'prop': 'revisions', 
								'rvlimit': str(rvlimit)})
	revisions = []
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
			revisions[i] = {'title': page_title, 
							'user': revision['user'], 
							'timestamp': seconds_since_epoch, 
							'revid': revision['revid']}
	return revisions

def category_pages(category_title, results_limit=500, recurse=False):
	"""
	Given the proper name of a category on Wikipedia, this will return
	a list of all proper page titles (not categories) found within that
	category. If 'recurse' is set to True, any subcategories of the
	given category will also be explored and the pages belonging to 
	those subcategories will also be returned. 
	"""
	params = {'action': 'query', 
				'list': 'categorymembers', 
				'cmtitle': category_title, 
				'cmtype': 'page',
				'cmlimit': str(results_limit),
				'cmsort': 'timestamp'}
	results = wikipedia_query(params)
	pages = []
	if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
		pages = [page['title'] for page in results]
	return pages

def category_subcategories(category_title, results_limit=500):
	"""
	Given the proper name of a category on Wikipedia, this
	will return a list of the titles only of all subcategories. If
	there are no subcategories, the list returned is empty. 
	"""
	params = {'action': 'query',
				'list': 'categorymembers',
				'cmtitle': category_title,
				'cmtype': 'subcat',
				'cmlimit': str(results_limit),
				'cmsort': 'timestamp'}
	results = wikitools_query(params)
	subcategories = []
	if 'categorymembers' in results.keys() and len(results['categorymembers']) > 0:
		subcategories = [category['title'] for category in results]
	return subcategories
			

def main():
	return

if __name__ == "__main__":
	main()
