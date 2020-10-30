#!/usr/bin/python3
# Blog generator script

# Pages (determines navbar order)
pages = [ "blog", "about", "projects", "git" ]

# External links
external = {
	"git": "http://git.mkukri.xyz"
}

# Index page
index = "blog"

# Read in templates
def read_file(name):
	with open(name) as f:
		return f.read()

# Page templates
template_nav  = read_file("src/templates/nav.html")
template_page = read_file("src/templates/page.html")

# Post templates
template_post_small = read_file("src/templates/post_small.html")
template_post_single= read_file("src/templates/post_single.html")

import configparser
import subprocess
import datetime
import os
import re

# Get metadata from a md file
def md_meta(s):
	meta = re.match("\\<!--GEN_META([\\s\\S]*)--\\>", s).group(1)
	parser = configparser.ConfigParser()
	parser.optionxform = str
	parser.read_string("[CONFIGPARSER_IS_CRAP]\n%s" %meta)
	return dict(parser["CONFIGPARSER_IS_CRAP"])

# Get content from a md file
def md_content(s):
	proc = subprocess.run("./md2html/md2html",
		stdout=subprocess.PIPE,
		input=re.sub("\\<!--[\\s\\S]*--\\>", "", s).encode())
	return proc.stdout.decode()

# Generate a page from a template and substitutions
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
	if page in external:
		subs = {
			"GEN_HREF": external[page],
			"GEN_LINK": page
		}
	else:
		href = page if page != index else "index"
		subs = {
			"GEN_HREF": "/%s.html" %href,
			"GEN_LINK": page
		}
	navbar.append(template_gen(template_nav, subs))
navbar = ''.join(navbar)

#
# Generate posts
#

def post_date(timestamp):
	return datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M')

def single_filename(timestamp, name):
	date = post_date(timestamp)
	return date.strftime('%Y/%m/%d') + '/%s.html' %name

posts = []

for post in os.listdir("src/posts"):
	post = os.path.splitext(post)[0]

	with open("src/posts/%s.md" %post) as f:
		post_md = f.read()

	subs = md_meta(post_md)
	subs["GEN_NAVBAR"] = navbar
	subs["GEN_CONTENT"] = md_content(post_md)
	path = single_filename(subs["GEN_TIMESTAMP"], post)
	subs["GEN_MORE_HREF"] = path

	# Generate single post
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w") as f:
		f.write(template_gen(template_post_single, subs))

	# Generate small post
	posts.append((post_date(subs["GEN_TIMESTAMP"]),
				template_gen(template_post_small, subs)))

posts.sort(key=lambda x: x[0], reverse=True)
posts = ''.join(map(lambda x: x[1], posts))

#
# Generate pages
#
for page in pages:
	if page in external:
		continue

	with open("src/pages/%s.md" %page) as f:
		page_md = f.read()

	subs = md_meta(page_md)
	subs["GEN_NAVBAR"] = navbar
	subs["GEN_CONTENT"] = md_content(page_md)
	if page == "blog":
		subs["GEN_CONTENT"] += posts

	if index == page:
		page = "index"
	with open("%s.html" %page, "w") as f:
		f.write(template_gen(template_page, subs))
