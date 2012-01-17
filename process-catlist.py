import wikicrawl
import argparse
import inspect

DEPTH = 10 # Crossing our fingers that this doesn't break the Internet

def parse_arguments():
	parser = argparse.ArgumentParser(description='Batch processing of crawling Wikipedia categories.')
	parser.add_argument('-categoryfile', metavar='filename', dest='category_file', type=argparse.FileType('r'), required=True,
						help='The name of a text file containing a list of Wikipedia categories to crawl.')
	parser.add_argument('-excludefile', metavar='filename', dest='exclude_file', type=argparse.FileType('r'),
						help='The name of a text file containing a list of Wikipedia categories and/or articles to exclude from crawling.')
	parser.add_argument('-depth', metavar='depth', dest='depth', type=int, default=DEPTH,
						help='The crawling depth for the categories, integer >= 0. Default is %d.' % (DEPTH))
	args = parser.parse_args()
	# We want to convert this from a Namespace to a dict and ignore the hidden attributes
	args = dict([(k, v) for k,v in inspect.getmembers(args) if k.find('_')!=0])
	return args

def main():
	args = parse_arguments()
	categories = args['category_file'].readlines()
	args['category_file'].close()
	exclusions = args['exclude_file'].readlines()
	args['exclude_file'].close()
	for i,cat in enumerate(categories):
		categories[i] = cat.rstrip().decode('UTF-8')
		print categories[i]
#	categories = [cat.rstrip().decode(category_encoding) for cat in categories]
	exclusions = [ex.rstrip().decode('UTF-8') for ex in exclusions]
	depth = args['depth']
	for category in categories:
		print 'Processing "%s".' % (category)
		output_filename = category.encode('UTF-8').replace(':', '-') + '.csv'
		output_file = open(output_filename, 'wb')
		wikicrawl.main(dict(title=category, 
							category=category, 
							depth=depth, 
							exclusions=exclusions,
							output_file=output_file))

if __name__=="__main__":
	main()
