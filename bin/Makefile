CFLAGS := -std=c89 -Wall

all: md2html

md2html: md2html.o
	$(CC) $(LDFLAGS) -o $@ $^

%.o: %.c
	$(CC) $(CFLAGS) -c -o $@ $^

clean:
	rm -f *.o md2html
