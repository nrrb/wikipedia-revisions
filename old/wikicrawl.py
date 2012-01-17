import argparse
import inspect
from wikiclass import *
import csv
from cStringIO import StringIO
from codecs import getincrementalencoder

def write_csv(revisions, field_order, output_file, include_header=False):	
	class DictUnicodeWriter(object):
		"""
		Code borrowed from http://stackoverflow.com/a/5838817
		"""
		def __init__(self, f, fieldnames, dialect=csv.excel, encoding="utf-8", **kwds):
			# Redirect output to a queue
			self.queue = StringIO()
			self.writer = csv.DictWriter(self.queue, fieldnames, dialect=dialect, **kwds)
			self.stream = f
			self.encoder = getincrementalencoder(encoding)()
		def writerow(self, D):
			self.writer.writerow({k:v.encode("utf-8") for k,v in D.items()})
			# Fetch UTF-8 output from the queue ...
			data = self.queue.getvalue()
			data = data.decode("utf-8")
			# ... and reencode it into the target encoding
			data = self.encoder.encode(data)
			# write to the target stream
			self.stream.write(data)
			# empty queue
			self.queue.truncate(0)
		def writerows(self, rows):
			for D in rows:
				self.writerow(D)
		def writeheader(self):
			self.writer.writeheader()
	dw = DictUnicodeWriter(output_file, 
						field_order,
						delimiter=',',
						quotechar='"')
	if include_header:
		dw.writeheader()
	for revision in revisions:
		for k, v in revision.values.items():
			# Some of these are integers and need to be converted to strings for the CSV writer
			revision.values[k] = unicode(v)
		dw.writerow(revision.values)	

def process_arguments():
	parser = argparse.ArgumentParser(description='Retrieve revision information for Wikipedia article(s).')
	parser.add_argument('-title', metavar='title', dest='title',
						help='The name of a Wikipedia article or category (e.g. Upper-atmospheric_lightning or Category:Lightning).')
	parser.add_argument('-output', metavar='output_path', dest='output_file', type=argparse.FileType('a'), required=True,
						help='Full path to output CSV file (e.g. /home/nick/Documents/lightning.csv).')
	optional = parser.add_argument_group('Optional arguments for when a CATEGORY is specified:')
	optional.add_argument('-depth', metavar='depth', dest='depth', type=int, default=10,
						help='The crawling depth for the given category, integer >= 0. Default is 0.')
	optional.add_argument('-exclude', metavar='article_or_category', nargs='+', dest='exclusions', default=[],
						help='A list of articles and categories to exclude from the results.')
	args = parser.parse_args()
	# We want to convert this from a Namespace to a dict and ignore the hidden attributes
	args = dict([(k, v) for k,v in inspect.getmembers(args) if k.find('_')!=0])
	if args['title'].lower().find('category:')==0:
		args['category'] = args['title']
	else:
		args['article'] = args['title']
	return args

def main(args):
	'''
	Input: dictionary with following keys:
		'title' - the title of the article or category to be scraped
		'article' - if 'title' represents an article, this is defined by that title
		'category' - if 'title' represents a category, this is defined by that title
		'depth' - integer
		'exclusions' - list of category or article names (strings) to exclude
		'output_file' - file object, where revisions should be written
	'''
	# Assemble the list of all articles, plural if a category was given and we must crawl
	articles = []
	if 'article' in args:
		articles = [WikiArticle(args['article'])]
	elif 'category' in args:
		c = WikiCategory(args['category'], args['depth'], args['exclusions'], 
								verbose=False)
		articles = c.collect_articles()
	# For each article, get the revisions and assemble into a master list
	revisions = []
	for i,article in enumerate(articles):
		print '[%d/%d] Revisions: "%s"' % (i+1, len(articles), article.page_title)
		revisions += article.revisions()
	# Write the revisions to the output file with proper ordering of fields
	write_csv(revisions, 
				['page_id', 'user_id', 'page_title', 'user', 'timestamp', 'rev_id', 'size'],
				args['output_file'])	
	# Done.
	args['output_file'].close()

if __name__=="__main__":
	args = process_arguments()
	main(args)