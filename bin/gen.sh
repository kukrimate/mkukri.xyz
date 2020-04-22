#!/bin/sh
#
# Blog generator script
#

# Exit on error
set -e
# Source configuration
. src/gen.rc

# Generate static pages
for i in $GEN_STATIC; do
	eval $(sed "/###/Q" "src/$i.md")
	sed "s/{GEN_TITLE}/$GEN_TITLE/g" "src/template_header.html" | \
		sed "s/{GEN_DESCRIPTION}/$GEN_DESCRIPTION/g" | \
		sed "s/{GEN_KEYWORDS}/$GEN_KEYWORDS/g" | \
		sed "s/{GEN_AUTHOR}/$GEN_AUTHOR/g" > "$i.html"
	sed "1,/###/d" "src/$i.md" | markdown >> "$i.html"
	cat "src/template_footer.html" >> "$i.html"
done
