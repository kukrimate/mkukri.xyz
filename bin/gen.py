#!/usr/bin/python3
# Blog generator script

# List of pages
GEN_PAGES = [ "index", "projects", "writeups" ]

# Read in templates
def read_file(name):
	with open(name) as f:
		return f.read()

template_page = read_file("src/templates/page.html")
template_nav  = read_file("src/templates/nav.html")

import configparser
import markdown
import re
import sys

def parse_metadata(s):
	parser = configparser.ConfigParser()
	parser.optionxform = str
	parser.read_string("[CONFIGPARSER_IS_CRAP]\n%s" %s)
	return dict(parser["CONFIGPARSER_IS_CRAP"])

def md_to_page(s):
	return markdown.markdown(re.sub("\\<!--[\\s\\S]*--\\>", "", s))

def template_gen(template, subs):
	result = template
	for k in subs:
		result = result.replace("{%s}" %k, subs[k])
	return ''.join(map(lambda x: x.strip(), result.split('\n')))

# Generate navbar
navbar = []
for page in GEN_PAGES:
	subs = {
		"GEN_HREF": "%s.html" %page,
		"GEN_LINK": page
	}
	navbar.append(template_gen(template_nav, subs))
navbar = ''.join(navbar)

# Generate pages
for page in GEN_PAGES:
	with open("src/%s.md" %page) as f:
		page_md = f.read()

	metadata = re.match("\\<!--GEN_META([\\s\\S]*)--\\>", page_md)
	if metadata == None:
		print("WARN: page %s has no metadata, skipping!" %page, file=sys.stderr)
		continue

	subs = parse_metadata(metadata.group(1))
	subs["GEN_NAVBAR"] = navbar
	subs["GEN_CONTENT"] = md_to_page(page_md)

	with open("%s.html" %page, "w") as f:
		f.write(template_gen(template_page, subs))
