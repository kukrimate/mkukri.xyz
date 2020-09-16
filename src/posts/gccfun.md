<!--GEN_META
GEN_TITLE=Unexpected issues with GCC
GEN_DESCRIPTION=how unfortunate sofware design can waste days of development time
GEN_KEYWORDS=gcc,compiler,bitfields,mno-ms-bitfields
GEN_AUTHOR=Máté Kukri
GEN_TIMESTAMP=2020-09-16 23:52
GEN_COPYRIGHT=Copyright (C) Máté Kukri, 2020
-->
Probably every programmer has used gcc at some point and it seems to work fine
most of the time. However there are some insane design choices(?) made by the
gcc developers that can waste your life. This article shows one of them that
I happened to run into.

I was working on an UEFI project, initially using a version of gcc built to
target `x86_64-w64-mingw32`, life was good gcc built the code and my new
hypervisor looked like it was hypervising. Then one day I had the crazy idea
that UEFI is cool and all, but making this thing portable is probably a good
idea.

The first step I took to achieve my portability goals was rebuilding the
project using a SysV ABI ELF toolchain. I built gcc targeting `x86_64-elf`,
than started porting. While the program internally now used the SysV ABI the
final executable was still linked into PE32+ file to be run under UEFI. After
marking the `efi_main` function as `__attribute__((ms_abi))` and fixing the
assembly code to use the new ABI I was ready to build. After fixing a few
other oversights, I managed to build a binary to appeared to initially work.
But a wierd new bug appeared out of nowhere, the processor started complaining
that the VMCB (or Virtual Machine Control Block) was invalid. After spending
two days quadruple checking the ABI I still wasn't able to make that error go
away.

Day 3 comes and I resort to single stepping my testing VM in gdb, this was when
I discovered that to my horror that the offsets into my VMCB struct were
different between the two compiler targets. Here is when I can hear the reader
yelling the word "alingment", but the struct was marked as `__attribute__((packed))`
all along. A few `offsetof` prints later I discovered that on the ELF
compiler the offsets differed from the AMD manual. After bisecting the struct
using more offsetofs I found that the struct definition was incorrect all along.

But than how an incorrectly defined packed struct could possibly work just fine
and magically have the correct offsets on the MinGW compiler? Turns out to MSVC
people the word packed doesn't mean a struct actually needs to be packed. And
sadly the gcc developers decided it was great idea to copy MSVC's brain damage
and enable by it default on MinGW target. I am sure the users of the two broken
libraries out there that rely on this are really happy that they can use their
broken struct definitions on MinGW without changes. But if you are expecting a
sane compiler, I am afraid you are out of luck.

Turns out the "magic" fix is specifying the `-mno-ms-bitfields` flag to gcc and
the behaviour disappears. Brilliant....
