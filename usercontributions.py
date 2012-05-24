####################################################
## Wikipedia revision history crawling by article ##
## by Nicholas Bennett and Brian Keegan		  ##
## Copyright 2012				  ##
####################################################

from wikitools import wiki, api
import random
import dateutil.parser
import codecs
import calendar
import argparse
import inspect
import re

_DEPTH = 5 # Crossing our fingers that this doesn't break the Internet
_FIELDORDER = [u'pageid',u'userid',u'title',u'user',u'timestamp',u'revid',u'size',u'ns',u'comment']
_ENCODING = 'UTF-8'
_CSV_QUOTECHAR = u'"'
_CSV_DELIMITER = u'\t'
_CSV_ENDLINE = u'\r\n'

def is_ip(ip_string, masked=False):
	# '''
	# Input:
	# ip_string - A string we'd like to check if it matches the pattern of a valid IP address.
	# Output:
	# A boolean value indicating whether the input was a valid IP address.
	# '''
	if not isinstance(ip_string, str) and not isinstance(ip_string, unicode):
		return False
	if masked:
		ip_pattern = re.compile('((([\d]{1,3})|([Xx]{1,3}))\.){3}(([\d]{1,3})|([Xx]{1,3}))', re.UNICODE)
	else:
		ip_pattern = re.compile('([\d]{1,3}\.){3}([\d]{1,3})', re.UNICODE)
	if ip_pattern.match(ip_string):
		return True
	else:
		return False
    
def parse_arguments():
	parser = argparse.ArgumentParser(description='Batch processing of crawling Wikipedia categories.')
	parser.add_argument('-u', metavar='filename', dest='user_file', type=argparse.FileType('r'), required=True,
						help='The name of a text file containing a list of Wikipedia users to crawl.')
	args = parser.parse_args()
	# We want to convert this from a Namespace to a dict and ignore the hidden attributes
	args = dict([(k, v) for k, v in inspect.getmembers(args) if k.find('_') != 0])
	return args

def write_csv(revisions, field_order, output_file, all_fields=False):
	# For each revision, we'll assume that its keys contain at least the members
	# of the list field_order. These values will then be printed in the order
	# specified by the field_order list. If the revision contains any other 
	# keys, those will be printed in arbitrary order (consistent within each
	# file though) after the specified fields. 
	with output_file as f:
		for revision in revisions:
			line = ''
			def wrap(x):
				return unicode(_CSV_QUOTECHAR + unicode(x) + _CSV_QUOTECHAR + _CSV_DELIMITER + ' ')
			for field in field_order:
				line += wrap(revision[field])
			f.write(line)
			if all_fields:
				other_fields = set(revision.keys()).difference(set(field_order))
				for field in other_fields:
					line += wrap(revision[field])
			f.write(_CSV_ENDLINE)

def iso_time_to_epoch(iso_timestamp):
	py_timestamp = dateutil.parser.parse(iso_timestamp)
	seconds_since_epoch = calendar.timegm(py_timestamp.timetuple())
	return seconds_since_epoch

def wikipedia_query(query_params):
	"""
	An extremely basic wrapper for the wikitools api.
	"""
	site = wiki.Wiki() # This defaults to en.wikipedia.org
	query_params['action'] = 'query'
	request = api.APIRequest(site, query_params)
	result = request.query()
	return result[query_params['action']]

def user_revisions(user, revision_properties=['ids','title', 'timestamp', 'comment', 'size']):
        '''
        Input: 
        article - The name of a wikipedia user, e.g. 'User:Madcoverboy' 
        revision_properties - A list of properties to be returned for each revision. The full list
                of properties can be found here: https://www.mediawiki.org/wiki/API:Properties#revisions_.2F_rv
        Output:
        revisions - A list of revisions for the given article, each given as a dictionary. This will
                include all properties as described by revision_properties, and will also include the
                title and id of the source article. 
        '''

        revisions = []
        result = wikipedia_query({'list': 'usercontribs',
                                  'ucuser': user,
                                  'ucprop': '|'.join(revision_properties),
                                  'uclimit': '500',
                                  'ucdir': 'newer'})
        if result and 'usercontribs' in result.keys():
                r = result['usercontribs']
                r = sorted(r, key=lambda revision: revision['timestamp'])
                for revision in r:
                        # Sometimes the size key is not present, so we'll set it to 0 in those cases
                        revision['size'] = revision.get('size', 0)
                        # The timestamp as supplied by wikitools is in the standard ISO 
                        # timestamp format. We may want to use this more flexibly in Python, 
                        # so we'll convert it to number of seconds since the UNIX epoch.
                        revision['timestamp'] = iso_time_to_epoch(revision['timestamp'])
                        revisions.append(revision)
        return revisions

def random_string(le, letters=True, numerals=False):
	def rc():
		charset = []
		cr = lambda x,y: range(ord(x), ord(y) + 1)
		if letters:
			charset += cr('a', 'z')
		if numerals:
			charset += cr('0', '9')
		return chr(random.choice(charset))
	def rcs(k):
		return [rc() for i in range(k)]
	return ''.join(rcs(le))

def clean_revision(rev):
	# We must deal with some malformed user/userid values. Some 
	# revisions have the following problems:
	# 1. no 'user' or 'userid' keys and the existence of the 'userhidden' key
	# 2. 'userid'=='0' and 'user'=='Conversion script' and 'anon'==''
	# 3. 'userid'=='0' and 'user'=='66.92.166.xxx' and 'anon'==''
	# 4. 'userid'=='0' and 'user'=='204.55.21.34' and 'anon'==''
	# In these cases, we must substitute a placeholder value
	# for 'userid' to uniquely identify the respective kind
	# of malformed revision as above. 
	revision = rev.copy()
	if 'userhidden' in revision:
		revision['user'] = random_string(15, letters=False, numerals=True)
		revision['userid'] = revision['user']
	elif 'anon' in revision:
		if revision['user']=='Conversion script':
			revision['user'] = random_string(14, letters=False, numerals=True)
			revision['userid'] = revision['user']
		elif is_ip(revision['user']):
			# Just leaving this reflection in for consistency
			revision['user'] = revision['user']
			# The weird stuff about multiplying '0' by a number is to 
			# make sure that IP addresses end up looking like this:
			# 192.168.1.1 -> 192168001001
			# This serves to prevent collisions if the numbers were
			# simply joined by removing the periods:
			# 215.1.67.240 -> 215167240
			# 21.51.67.240 -> 215167240
			# This also results in the number being exactly 12 decimal digits.
			revision['userid'] = ''.join(['0' * (3 - len(octet)) + octet \
											for octet in revision['user'].split('.')])
		elif is_ip(revision['user'], masked=True):
			# Let's distinguish masked IP addresses, like
			# 192.168.1.xxx or 255.XXX.XXX.XXX, by setting 
			# 'user'/'userid' both to a random 13 digit number
			# or 13 character string. 
			# This will probably be unique and easily 
			# distinguished from an IP address (with 12 digits
			# or characters). 
			revision['user'] = random_string(13, letters=False, numerals=True)
			revision['userid'] = revision['user']
	return revision

def main():
	args = parse_arguments()
	with args['user_file'] as f:
		users = f.readlines()
	users = [user.rstrip().lstrip().decode(_ENCODING) for user in users]

	for user in users:
		print '{0}'.format(user)
		output_filename = user.encode(_ENCODING).replace(':', '-') + '.csv'
		revisions = user_revisions(user)
		# Check for bad 'user'/'userid' values and correct them
		for i in xrange(len(revisions)):
			revisions[i] = clean_revision(revisions[i])
		with codecs.open(output_filename, 'w', _ENCODING) as output_file:
		 	# Rollin' up my sleeves and writing my own CSV outputter thingy
		 	write_csv(revisions, _FIELDORDER, output_file, all_fields=True)

if __name__=="__main__":
	main()

################################################################################
########################################################### Utility Functions ##
## Utility Functions ###########################################################
################################################################################

# To find a list of unique keys from a list of dictionary objects:

def uniq_keys(list_dicts):
    return list(set([k for d in list_dicts for k in d.keys()]))

# To find a list of unique keys from a list of dictionary objects, in a dictionary 
# with counts of how many objects had a given key. 

def uniqc_keys(list_dicts):
	all_keys = [k for d in list_dicts for k in d.keys()]
	unique_keys = list(set(all_keys))
	counts = [all_keys.count(key) for key in unique_keys]
	return dict(zip(unique_keys, counts))

# To find the list of unique elements in a list:

def uniq(L):
	return list(set(L))

# To get a list of tuples with the unique elements as the first value and 
# the count of that element in the original list as the second value:

def uniqc(L):
	return zip(uniq(L), [L.count(x) for x in uniq(L)])
