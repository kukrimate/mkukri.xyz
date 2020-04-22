#!/usr/bin/python3
# Blog generator script

GEN_TEMPLATE = "template"
GEN_PAGES    = [ "index", "projects", "writeups" ]

import configparser
import formatter
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
	return formatter.format_html(result)

# Read template
with open("src/%s.html" %GEN_TEMPLATE) as f:
	template = f.read()

# Generate pages
for page in GEN_PAGES:
	with open("src/%s.md" %page) as f:
		page_md = f.read()

	metadata = re.match("\\<!--GEN_META([\\s\\S]*)--\\>", page_md)
	if metadata == None:
		print("WARN: page %s has no metadata, skipping!" %page, file=sys.stderr)
		continue

	subs = parse_metadata(metadata.group(1))
	subs["GEN_CONTENT"] = md_to_page(page_md)

	with open("%s.html" %page, "w") as f:
		f.write(template_gen(template, subs))
