#!/usr/bin/python3
# Blog generator script

# Blog feeds
feeds = [ "blog", "writeups" ]

# Pages (determines navbar order)
pages = [ "about", "blog", "projects", "writeups" ]

# Index page
index = "about"

# Read in templates
def read_file(name):
	with open(name) as f:
		return f.read()

template_nav  = read_file("src/templates/nav.html")
template_page = read_file("src/templates/page.html")
template_post = read_file("src/templates/post.html")
template_single = read_file("src/templates/single.html")

import configparser
import markdown
import os
import re

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
	return result

#
# Generate navbar
#
navbar = []
for page in pages:
	href = page if page != index else "index"
	subs = {
		"GEN_HREF": "/%s.html" %href,
		"GEN_LINK": page
	}
	navbar.append(template_gen(template_nav, subs))
navbar = ''.join(navbar)

#
# Generate posts for feeds
#
for feed in feeds:
	if not os.path.isdir(feed):
		os.mkdir(feed)

	feed_content = ""

	for post in os.listdir("src/%s" %feed):
		with open("src/%s/%s" %(feed, post)) as f:
			post_md = f.read()

		post_meta = re.match("\\<!--GEN_META([\\s\\S]*)--\\>", post_md)
		subs = parse_metadata(post_meta.group(1))
		subs["GEN_NAVBAR"] = navbar
		subs["GEN_CONTENT"] = md_to_page(post_md)

		single_filename = "%s/%s.html" %(feed, os.path.splitext(post)[0])
		subs["GEN_MORE_HREF"] = single_filename
		with open(single_filename, "w") as f:
			f.write(template_gen(template_single, subs))

		feed_content += template_gen(template_post, subs)

	subs = {
		"GEN_TITLE": "%s feed" %feed,
		"GEN_DESCRIPTION": "blog posts in feed %s" %feed,
		"GEN_KEYWORDS": "personal,blog,%s" %feed,
		"GEN_AUTHOR": "Máté Kukri",
		"GEN_NAVBAR": navbar,
		"GEN_CONTENT": "<h1>%s</h1>" %(feed.title()) + feed_content
	}

	if index == feed:
		feed = "index"
	with open("%s.html" %feed, 'w') as f:
		f.write(template_gen(template_page, subs))

#
# Generate static pages
#
for page in pages:
	if page in feeds:
		continue

	with open("src/%s.md" %page) as f:
		page_md = f.read()

	metadata = re.match("\\<!--GEN_META([\\s\\S]*)--\\>", page_md)
	subs = parse_metadata(metadata.group(1))
	subs["GEN_NAVBAR"] = navbar
	subs["GEN_CONTENT"] = md_to_page(page_md)

	if index == page:
		page = "index"
	with open("%s.html" %page, "w") as f:
		f.write(template_gen(template_page, subs))
