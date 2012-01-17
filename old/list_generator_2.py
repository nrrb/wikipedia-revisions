# Brian Keegan, 2012
# This function creates text files containing a list of Wikipedia categories which will be passed to a scraping algorithm.
# Two files are created for each category type, events before 2001 (Wikipedia's founding) and after 2001

#Define schema for naming category types
topics=[('fires', "Category:{0}_fires"),
        ('health', "Category{0}_health_disasters"),
        ('industrial', "Category:{0}_industrial_disasters"),
        ('natural', "Category:{0}_natural_disasters"),
        ('transport', "Category:Transport_disasters_in_{0}"),
        ('terrorist', "Category:Terrorist_incidents_in_{0}"),
        ('conflicts', "Category:Conflicts_in_{0}"),
        ('crimes', "Category:{0}_crimes")]
start_year = 1990
end_year = 2000

files_pre2k = dict([(topic, open('{0}_pre2k.txt'.format(topic), 'a')) for topic,c in topics])
if 2000 < start_year < end_year:
    files_post2k = dict([(topic, open('{0}_post2k.txt'.format(topic), 'a')) for topic,c in topics])

for topic, cat_string in topics:
    for year in range(start_year, end_year+1):
        category = cat_string.format(year)
        if year <= 2000:
            files_pre2k[topic].write(category.encode('UTF-16') + '\r\n')
        else:
            files_post2k[topic].write(category.encode('UTF-16') + '\r\n')
for topic,c in topics:
    files_pre2k[topic].close()
    if 2000 < start_year < end_year:
        files_post2k[topic].close()
