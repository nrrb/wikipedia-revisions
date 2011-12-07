# coding: utf-8
#from unidecode import unidecode
article_name = 'Social_network'
#article_name_ascii = unidecode(article_name)	

def wiki_page_revisions(page_title, rvlimit=5000):
	from wikitools import wiki
	from wikitools import api
	import dateutil.parser
	import calendar
	site = wiki.Wiki() # This defaults to en.wikipedia.org
	params = {'action': 'query', 'titles': page_title, 'prop': 'revisions', 'rvlimit': str(rvlimit)}
	request = api.APIRequest(site, params)
	result = request.query()
	revisions = []
	if result:
		page_number = result['query']['pages'].keys()[0]
		revisions = result['query']['pages'][page_number]['revisions']
		revisions = sorted(revisions, key=lambda revision: revision['timestamp'])
		for i, revision in enumerate(revisions):
			#revisions[i]['user_ascii'] = unidecode(revisions[i]['user'])
			# The timestamp as supplied by wikitools is in the standard ISO timestamp format
			# We may want to use this more flexibly in Python, so we'll convert it to
			# number of seconds since the UNIX epoch
			iso_timestamp = revision['timestamp']
			py_timestamp = dateutil.parser.parse(iso_timestamp)
			seconds_since_epoch = calendar.timegm(py_timestamp.timetuple())
			revisions[i]['timestamp'] = seconds_since_epoch
			revisions[i]['title'] = page_title
	return revisions

def main():
	revisions = wiki_page_revisions(article_name)
	#
	gdyn = gexf.Gexf("Nick Bennett", "Dynamic Graph File Test")
	graph = gdyn.addGraph("directed", "dynamic", "Dynamic Graph Test")
	graph.addNode("0", article_name_ascii)
	for i in range(1, len(revisions)+1):
		# Since we've used the 0th node for the article node, we must start with 1 for the revision nodes
		node_id = str(i)
		node_name = revisions[i-1]['revid']
		n = graph.addNode(node_id, node_name)
	for i in range(1, len(revisions)+1):
		edge_id = str(i-1)
		node1_id = "0"
		node2_id = str(i)
		edge_start = str(revisions[i-1]['timestamp'])
		if i < len(revisions):
			# Except for the most recent revision, make every revision "end" when the next 
			# most recent revision starts
			edge_end = str(revisions[i]['timestamp'])
			e = graph.addEdge(edge_id, node1_id, node2_id, start=edge_start, end=edge_end)
		else:
			e = graph.addEdge(edge_id, node1_id, node2_id, start=edge_start)
	output_file = open(article_name_ascii + ".gexf", "w")
	gdyn.write(output_file)



if __name__ == "__main__":
	main()
