def weighted_graph_import(unique):
    G=nx.Graph()
    for i in range(len(unique)):
        from_id=unique[i][0]
        to_id=unique[i][1]
        weightvar=unique[i][2]
        startvar=unique[i][3]
        endvar=unique[i][4]
        G.add_edge(from_id,to_id,weight=weightvar,start=startvar,end=endvar)
    return G
