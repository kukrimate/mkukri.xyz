# blog
Tools used to generate my blog. With all the jekyll madness going on I decided
that Ruby wasn't worth it, and wrote something similar, but way simpler in
POSIX-compliant sh.

## basics
Just run `bin/gen.sh` to generate the main tree. `src` has all the source files
for user generated content. `gen.rc` tells the generator how to lay things out.
