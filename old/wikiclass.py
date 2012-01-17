from wikitools import wiki, api
import dateutil.parser
import calendar

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

def category_articles(category_name, excluded=[], depth=10):
	print 'Exploring %s' % (category_name)
	articles = []
	if category_name in excluded:
		return articles
	if depth < 0:
		return articles
	r = wikipedia_query({'list': 'categorymembers', 
						'cmtitle': category_name, 
						'cmtype': 'page',
						'cmlimit': '500'})	
	if 'categorymembers' in r.keys() and len(r['categorymembers']) > 0:
		for i, page in enumerate(r['categorymembers']):
			a = dict(title=page['title'], id=page['pageid'])
			if a['title'] not in excluded:
				articles.append(a)
	r = wikipedia_query({'list': 'categorymembers',
						'cmtitle': category_name,
						'cmtype': 'subcat',
						'cmlimit': '500'})
	subcategories = []
	if 'categorymembers' in r.keys() and len(r['categorymembers']) > 0:
		for i, category in enumerate(r['categorymembers']):
			c = category['title']
			if c not in excluded:
				subcategories.append(c)
	for category in subcategories:
		articles = articles + category_articles(category, excluded=excluded, depth=depth-1)
	return articles

def article_revisions(article_name, page_id=''):
	revisions = []
	result = wikipedia_query({'titles': article_name, 
							'prop': 'revisions', 
							'rvprop': 'ids|timestamp|user|userid|size',
							'rvlimit': '5000'})
	if result and 'pages' in result.keys():
		page_number = result['pages'].keys()[0]
		r = result['pages'][page_number]['revisions']
		r = sorted(r, key=lambda revision: revision['timestamp'])
		for i, revision in enumerate(r):
			# The timestamp as supplied by wikitools is in the standard ISO 
			# timestamp format. We may want to use this more flexibly in Python, 
			# so we'll convert it to number of seconds since the UNIX epoch.
			seconds_since_epoch = iso_time_to_epoch(revision['timestamp'])
			# Special handling for anonymous/malformed revision authors
			if 'userhidden' in revision.keys():
				revision['user'] = "userhidden"
				revision['userid'] = ''
			if 'userid' in revision.keys() and revision['userid']==0 and 'anon' in revision.keys():
				# Then we'll take the user, which contains an IP address,
				# and re-format it from vvv.xxx.yyy.zzz to 
				# vvvxxxyyyzzz0000000000
				ip = revision['user']
				revision['userid'] = ''.join(['0'*(3-len(o))+o for o in ip.split('.')]) + '0'*10
			revisions.append(dict(page_title=article_name,
								page_id=page_id,
								user=revision['user'],
								user_id=str(revision['userid']),
								timestamp=str(seconds_since_epoch),
								rev_id=str(revision['revid']),
								size=str(revision['size'])))
	return revisions	