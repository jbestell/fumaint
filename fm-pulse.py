#!/usr/bin/env python
# Public: fs-pulse.py
#
# SupFubot project - Interval Maintenance Window Scraper
# For details see:
# https://github.com/jbestell/fustatus

from lxml import html
import lxml.html
import requests


#Name this script
name = "hpcloud-maintenance-window-scraper"

# Path to the incidents directory
indt_path = '/home/hpcsint/prod/fumaint/windows/'
indt_file = 'current'

# Type can be Incident or Maintenance but really almost always incident
type = "maintenance"

# Use LXML to grab the document and save it as an object
entry  = requests.get("https://community.hpcloud.com/status")
tree = html.fromstring(entry.text)

# Grabs all of the incident links and splits out the url portion, we just need the nodeId's as integers
# aww yiss list comprehensions (freddie)
links = [i.split('/')[3] for i in tree.xpath("//a[contains(@href, 'maintenance')]/@href")]
links = [ int(x) for x in links ]

# Reassign to remove nasty duplicates issue when no end date is set (bug)
links = list(set(links))


# Writes to file to be grabbed by fustatus-item
f = open(indt_path + indt_file,'w')
f.write(str(links) + '\n')
f.close()


# Debugging
#with open(indt_path + indt_file) as f:
#        nodes = f.read()
#print nodes.replace("[", "").replace("]", "").strip().split(',')
#print links
