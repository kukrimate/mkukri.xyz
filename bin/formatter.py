from bs4.builder._htmlparser import HTMLParserTreeBuilder
from bs4.element import HTMLAwareEntitySubstitution as HTML
from bs4 import BeautifulSoup

GEN_PRESERVE_TAGS = \
[ "script", "title", "h1", "h2", "h3", "h4", "h5", "li", "a", "pre", "code" ]

class CustomTreeBuilder(HTMLParserTreeBuilder):
     preserve_whitespace_tags = \
     	HTML.preserve_whitespace_tags.union(set(GEN_PRESERVE_TAGS))

def format_html(html):
	"""
	Format a HTML document, preserving the whitespaces inside tags listed
		above, indenting it with TABs
	"""
	bs4_result = BeautifulSoup(html, builder=CustomTreeBuilder()).prettify()
	reindented = []
	for l in bs4_result.split('\n'):
		lvl = len(l) - len(l.lstrip())
		reindented.append('\t' * lvl + l.strip())
	return '\n'.join(reindented)
