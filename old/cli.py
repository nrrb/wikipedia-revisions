import argparse

def process_arguments():
# Syntax:
#
# $ python wikirevs.py -a/--article article_name -o/--output /path/filename.csv
# $ python wikirevs.py -c/--category category_name -o/--output /path/filename.csv [-d/--depth N -x/--exclude article1,article2,Category:three]
# 
# The depth parameter defaults to 0 if not specified. 	parser = argparse.ArgumentParser(description='Retrieve revision information for Wikipedia article(s).')
	parser = argparse.ArgumentParser(description='Retrieve revision information for Wikipedia article(s).')
	parser.add_argument('-article', metavar='article_title', dest='article',
						help='The name of a Wikipedia article (e.g. Upper-atmospheric_lightning).')
	parser.add_argument('-category', metavar='category_title', dest='category',
						help='The name of a Wikipedia category (e.g.Category:Lightning).')
	parser.add_argument('-output', metavar='output_path', dest='output_file', type=argparse.FileType('wb'), required=True,
						help='Full path to output CSV file (e.g. /home/nick/Documents/lightning.csv).')
	optional = parser.add_argument_group('Optional for Categories')
	optional.add_argument('-depth', metavar='depth', dest='depth', default=0,
						help='The crawling depth for the given category, integer >= 0. Default is 0.')
	optional.add_argument('-exclude', metavar='article_or_category', nargs='+', dest='excluded', default=[],
						help='A list of articles and categories to exclude from the results.')
	args = parser.parse_args()	
	# Who knows, maybe you intend to overwrite an existing file! 
	# if os.path.exists(args.output_filename):
	# 	parser.exit(status=-1, message='Output file specified already exists, I don't want to overwrite your stuff.\n')


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
