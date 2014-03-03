#!/usr/bin/env python
# Public: fm-item.py
#
# SupFubot project - Maintance Item Event Status Processor
# For details see:
# https://github.com/jbestell/fumaint

import time
import argparse
from time import strftime
from time import mktime
from datetime import datetime
import json
from lxml import html
import lxml.html
import requests

#Name this script
name = "hpcloud-maintenance-notification-processor"

# Path to the incidents directory
indt_path = '/home/hpcsint/prod/fumaint/windows/'

# Get incidents passed to script
parser = argparse.ArgumentParser()
#parser.add_argument('incident', help='4-digit number of incident to parse and store')
parser.add_argument('maintenance_file', help='<path to file with maintenance windows to scrape>')
args = parser.parse_args()

# Fancy reassignment of string to POSIX timestamp. In our current context:
# "Monday, February 24, 2014 11:30 AM UTC" strptime([var],"%A, %B %d, %Y %I:%M %p %Z") -->  strftime("%s",[var])
def timestamp (str, informat, outformat):
	"Convert a string date to a POSIX timestamp"
	global time
	str = time.strptime(str, informat)
	str = strftime(outformat,str)
	return str;

# Get the Current 'node', basically signifying the working incident in Drupal's niceurl config
nodes  = args.maintenance_file

# grabs the file written by fustatus-scrape and reads it in as a list for processing
with open(nodes) as f:
        nodes = f.read()
nodes =  nodes.replace("[", "").replace("]", "").strip().split(', ')

# Type can be Incident or Maintenance but really almost always incident
# !!CONSIDER REMOVING
type = "maintenance"


for nodeid in nodes:
	current_link = nodeid

	# The working permalink to the incident report
	start_url = "https://community.hpcloud.com/status/" + type + "/" + current_link

	# Use LXML to grab the document and save it as an object
	entry  = requests.get("https://community.hpcloud.com/status/" + type + "/" + current_link)
	tree = html.fromstring(entry.text)

	# locating XPATH matches in one spot node ID is in CSS id
	node_match   = '//*[@id="node-' + current_link
	# match_desc   = node_match + '"]/div/div[last()]/div/div/text()'
	match_desc   = node_match + '"]/div/div[last()]/div/div/descendant::*/text()'
	# 'status' is always the last element in the group of children, so use XPATH thusly
	#match_status = node_match + '"]/div/div[1]/div[last()]/div[last()]/div/text()'
	match_start1 = node_match + '"]/div/div[1]/div[2]/div/div/div[1]/span/text()'
	match_start2 = node_match + '"]/div/div[1]/div[1]/div/div/div[1]/span/text()'
	match_start3 = node_match + '"]/div/div[1]/div[2]/div/div/div[1]/span/text()'
	match_end1   = node_match + '"]/div/div[1]/div[2]/div/div/div[2]/span/text()'
	match_end2   = node_match + '"]/div/div[1]/div[1]/div/div/div[2]/span/text()'
	match_end3   = node_match + '"]/div/div[1]/div[2]/div/div/div[2]/span/text()'


	# Build a list object using XPATH and some local variable magic
	item = {}
	item['nodeId'] = current_link
	item['link'] = start_url
	#Set these to 'None' for now, as they are to be modified later in the cycle
	item['status'] = 'static'
	item['sub_status'] = None
	item['interval'] = None
	# Get the description - join if multiple descendant paragraphs.
	item['desc'] = tree.xpath(str(match_desc))
	item['desc'] = " ".join(item['desc'])

	#item['status'] = tree.xpath(str(match_status))[0].upper()


	# This is the tricky bit - there can be as many as four //div/ child matches for <div class="filed-label">
	# and it varies based on whether:
	# -> the affected product is set
	# -> the end time is toggled
	# End time is a little easier to deal with as it only occurs at the end of an incident, or a post-mortem
	# 'confession' post or after-incident advisory. In all cases we need to match and capture all of these
	# items whether or not they exist.

	# A Status of RESOLVED is the best indicator that the End Field might be populated, so use it for conditionals.
	if item['status'] in ('static'):
			try:
					#Matches if Product is Set
					item['time_start'] = timestamp(tree.xpath(match_start1)[0], "%A, %B %d, %Y %I:%M %p %Z", "%s")

			except IndexError:


					item['time_start'] = timestamp(tree.xpath(match_start2)[0], "%A, %B %d, %Y %I:%M %p %Z", "%s")

			try:

					# Matches if Product AND End Date is Shown  /div/div[1]/div[2]/div/div/div[2]/span/text()')[0]

									item['time_end'] = timestamp(tree.xpath(match_end1)[0], "%A, %B %d, %Y %I:%M %p %Z", "%s")

			except IndexError:
					try:
							# Matches if only Start and End Date is Shown /div/div[1]/div[1]/div/div/div[2]/span
							item['time_end'] = timestamp(tree.xpath(match_end2)[0], "%A, %B %d, %Y %I:%M %p %Z", "%s")

					except IndexError:
							# Resolved, but No Product or End Date - Set it to Start Date (legacy)
							item['time_end'] = item['time_start']

					else:
							# All Three: Product, Start and End are set /div/div[1]/div[2]/div/div/div[2]/span
							item['time_end'] = timestamp(tree.xpath(match_end3)[0], "%A, %B %d, %Y %I:%M %p %Z", "%s")


			else:
					# Pass for all other conditions (ultimate)
					#item['time_end'] = None
					pass

	# If the status is ONGOING or MONITORING
	elif item['status'] in (current_status[0], current_status[1]):

			try:
					# ONG / MON - Matches Start if Product IS set.
					item['time_start'] = timestamp(tree.xpath(match_start1)[0], "%A, %B %d, %Y %I:%M %p %Z", "%s")

			except IndexError:

					# ONG / MON - Matches Start if Product IS NOT set.
					item['time_start'] = timestamp(tree.xpath(match_start2)[0], "%A, %B %d, %Y %I:%M %p %Z", "%s")

			#no END Date, so...
			item['time_end'] = None

	else:
			# For all other scenarios, just null them both out.
			item['time_start'] = None
			item['time_end'] = None


	try:
			f = open(indt_path + current_link + '.json','w')
			f.write(str(item) + '\n')
			f.close()
	except IOError:
			print "Error: can\'t find file or read data"
	else:
				print current_link + ".json written successfully"
# for debugging
print nodes
