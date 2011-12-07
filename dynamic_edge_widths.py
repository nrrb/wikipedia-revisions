# encoding: utf-8
from wiki_revs import wiki_page_revisions
from gexf import Gexf

article_name = "Social_network"

revisions = wiki_page_revisions(article_name)
editors = {}
for revision in revisions:
	editors.setdefault(revision['user'], [])
	editors[revision['user']].append({'time': revision['timestamp'], 
										'id': revision['revid']})
max_editor = reduce(lambda e1,e2: e1 if len(editors[e1]) > len(editors[e2]) else e2, editors)
edits = editors[max_editor]

gdyn = Gexf("Nick Bennett", "Testing Dynamic Edge Widths")
graph = gdyn.addGraph("directed", "dynamic", "Testing Dynamic Edge Widths")
graph.addNode("0", article_name)
graph.addNode("1", max_editor)
weight_attribute_id = graph.addEdgeAttribute("weight", "0", mode="dynamic", force_id="weight")
e = graph.addEdge("1","0")

for i, edit in enumerate(edits):
	edit['time'] = float(edit['time'])
	edge_start = str(edit['time'])
	edge_end = str(edit['time']+60)
	e.addAttribute(weight_attribute_id, "2", start=edge_start, end=edge_end)
	if i < len(edits)-1:
		e.addAttribute(weight_attribute_id, "1", start=str(edit['time']+60), end=str(float(edits[i+1]['time'])))
		

gdyn.write(open("test.gexf","w"))

