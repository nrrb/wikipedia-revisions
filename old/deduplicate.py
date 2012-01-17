def deduplicate(input_file,sep_char):
    lines=[]
    line_num=0
    edgelist=[]
    for line in open(input_file):
        line_num=line_num+1
        line=line.rstrip().split(sep_char)
        edgelist.append((line[0],line[1]))
    unique=list(set(edgelist))
    reverse=edgelist[:]
    reverse.reverse()
    for i in range(len(unique)):
        weight=str(edgelist.count(unique[i]))
        firstposition=str(edgelist.index(unique[i]))
        lastposition=str(len(edgelist)-reverse.index(unique[i])-1)
        unique[i]=unique[i] + (weight, firstposition, lastposition)
    return edgelist,unique
