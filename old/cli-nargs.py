#!/usr/bin/python
import argparse
import inspect
from wikirevs import *

def article_revisions(article):
	# Input: article name
	# Output: list of dictionaries representing revisions


def crawl_articles_in_category(category, depth=0, exclusions=[]):


def process_arguments():
	sample_arguments = '''-article Article1 -category Category:One -depth 2 -output /home/nick/Documents/data.csv 
							-exclude Article2 Category:Two Article3'''
	parser = argparse.ArgumentParser(description='Retrieve revision information for Wikipedia article(s).')
	parser.add_argument('-article', metavar='article_title', dest='article',
						help='The name of a Wikipedia article (e.g. Upper-atmospheric_lightning).')
	parser.add_argument('-category', metavar='category_title', dest='category',
						help='The name of a Wikipedia category (e.g.Category:Lightning).')
	parser.add_argument('-output', metavar='output_path', dest='output_file', type=argparse.FileType('wb'), required=True,
						help='Full path to output CSV file (e.g. /home/nick/Documents/lightning.csv).')
	optional = parser.add_argument_group('Optional arguments for when a CATEGORY is specified:')
	optional.add_argument('-depth', metavar='depth', dest='depth', type=int, default=0,
						help='The crawling depth for the given category, integer >= 0. Default is 0.')
	optional.add_argument('-exclude', metavar='article_or_category', nargs='+', dest='excluded', default=[],
						help='A list of articles and categories to exclude from the results.')
	args = parser.parse_args(sample_arguments.split())
	# args = parser.parse_args()
	# We want to convert this from a Namespace to a dict and ignore the hidden attributes
	args = dict([(k, v) for k,v in inspect.getmembers(args) if k.find('_')!=0])
	return args

args = process_arguments()
all_articles = []
if 'article' in args:
	all_articles = [args['article']]
elif 'category' in args:
	# Only if there is no article specified will the category argument be processed
	all_articles = crawl_articles_in_category(args['category'], args['depth'], args['exclusions'])

all_revisions = []
for article in all_articles:
	all_revisions += article_revisions()

