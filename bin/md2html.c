/*
 * Markdown to HTML converter
 */

#include <stdio.h>

int
next(FILE *fp, int want)
{
	int ch;

	ch = fgetc(fp);
	if (ch != want)
		ungetc(ch, fp);
	return ch;
}

void *
decide(FILE *fp);

/* Nestable blocks */

void *
code(FILE *fp)
{
	int ch;

	printf("<code>");
	while ((ch = fgetc(fp)) != EOF)
		switch (ch) {
		case '`':
			printf("</code>");
			return decide;
		default:
			putchar(ch);
		}

	return NULL;
}

void *
esccode(FILE *fp)
{
	int ch;

	printf("<code>");
	while ((ch = fgetc(fp)) != EOF)
		switch (ch) {
		case '`':
			if (next(fp, '`') == '`') {
				printf("</code>");
				return decide;
			}
		default:
			putchar(ch);
		}

	return NULL;
}

/* Top level blocks */

void *
codeblock(FILE *fp)
{
	int ch;

	printf("<pre><code>");

	/* Skip leading newlines in multi-line codeblock */
	while (next(fp, '\n') == '\n');

	while ((ch = fgetc(fp)) != EOF)
		switch (ch) {
		case '`':
			if (next(fp, '`') == '`' &&
					next(fp, '`') == '`') {
				printf("</code></pre>");
				return decide;
			}
		default:
			putchar(ch);
		}

	return NULL;
}

void *
blockquote(FILE *fp)
{
	int ch;

	printf("<blockquote>");
	while ((ch = fgetc(fp)) != EOF)
		switch (ch) {
		case '\n':
			/* End of blockquote */
			if (next(fp, '\n') == '\n') {
				printf("</blockquote>");
				return decide;
			}
			/* Ignore > on subsequent lines */
			else if (next(fp, '>') == '>') {
				break;
			}
		default:
			putchar(ch);
		}

	return NULL;
}

void *
list(FILE *fp)
{
	int ch;

	printf("<ul><li>");
	while ((ch = fgetc(fp)) != EOF)
		switch (ch) {
		case '\n':
			if (next(fp, '*') == '*') {
				printf("</li><li>");
				break;
			} else if (next(fp, '\n') == '\n') {
				printf("</li></ul>");
				return decide;
			}
		default:
			putchar(ch);
		}

	return NULL;
}

void *
paragraph(FILE *fp)
{
	int ch;

	printf("<p>");
	while ((ch = fgetc(fp)) != EOF)
		switch (ch) {
		case '`':
			if (next(fp, '`') == '`') {
				if (next(fp, '`') == '`') { /* Code block */
					/* NOTE: codeblock imples end of p */
					printf("</p>");
					return codeblock;
				} else {                    /* Escaped code */
					esccode(fp);
				}
			} else {                            /* Inline code */
				code(fp);
			}
			break;
		case '#':
			/* Heading implies end of p */
			ungetc(ch, fp);
			printf("</p>");
			return decide;
		case '\n':
			/* Blockquote */
			if (next(fp, '>') == '>') {
				/* NOTE: blockquote also imples end of p */
				printf("</p>");
				return blockquote;

			}
			/* End of paragraph */
			else if (next(fp, '\n') == '\n') {
				printf("</p>");
				return decide;
			}
		default:
			putchar(ch);
		}

	/* End of file (also ends paragraph) */
	printf("</p>");
	return NULL;
}

#define _paste(x, y) x ## y
#define paste(x, y) _paste(x, y)
#define _string(x) # x
#define string(x) _string(x)
#define strpaste(x, y) string(paste(x, y))

#define heading(lvl) \
void * \
h##lvl(FILE *fp) \
{ \
	int ch; \
\
	printf("<" strpaste(h, lvl) ">"); \
	while ((ch = fgetc(fp)) != EOF) \
		switch (ch) { \
		case '\n': \
			printf("</" strpaste(h, lvl) ">"); \
			return decide; \
		default: \
			putchar(ch); \
		} \
\
	return NULL; \
}

/* Generate functions for each heading level */
heading(1)
heading(2)
heading(3)
heading(4)
heading(5)
heading(6)

void *
decide(FILE *fp)
{
	int ch, cnt;
	static void *headings[] = { h1, h2, h3, h4, h5, h6 };

	retry:
	switch ((ch = fgetc(fp))) {
	case EOF:
		return NULL;
	case '\n': /* Consume newlines at the start of top level blocks */
		goto retry;
	case '>':
		return blockquote;
	case '*':
		return list;
	case '#':
		cnt = 0;
		while (next(fp, '#') == '#')
			++cnt;
		return headings[cnt % 6];
	default:
		ungetc(ch, fp);
		return paragraph;
	}
}

typedef void *(*fn)(FILE *fp);

void
md2html(FILE *fp)
{
	fn curfn;

	for (curfn = decide; (curfn = curfn(fp)); );
}

int
main(int argc, char *argv[])
{
	FILE *fp;

	if (argc < 2) {
		fp = stdin;
	} else {
		if (!(fp = fopen(argv[1], "r"))) {
			perror(argv[1]);
			return 1;
		}
	}

	md2html(fp);
	fclose(fp);
	return 0;
}
