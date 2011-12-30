import argparse

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
	if os.path.exists(os.get
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

if __name__=="__main__":
	articles, categories, excluded_articles, excluded_categories, depth, outfilename = get_arguments()
	all_articles = articles[:]
	for category in categories:
