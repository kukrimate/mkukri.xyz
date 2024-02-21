<!--GEN_META
GEN_TITLE=It's not just Bitlocker, all linux TPM encryption is broken too
GEN_DESCRIPTION=We demonstrate a bypass of Linux TPM FDE
GEN_KEYWORDS=tpm,reset,fde
GEN_AUTHOR=Mate Kukri,birb007
GEN_TIMESTAMP=2024-02-15 23:08
GEN_COPYRIGHT=Copyright (C) birb007, Mate Kukri, 2023-2024
-->

The title is somewhat click-baity, but also true in a way, this only breaks
dTPMs and the reset attack was known prior, however some people seem to have
believed the misconception that encrypted parameters save such designs.

This research was done in collaboration with a good friend of mine known as
_birb_ on these parts, the full article describing this work is hosted on
his blog: <a href="https://hacky.solutions/blog/2024/02/tpm-attack">link</a>

<iframe width="560" height="315" src="https://www.youtube.com/embed/oY7tCZH2w60?si=qfCyHHxsrOyiiMYd" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

Please note that while the demo above is shown using a modular TPM card,
it is entirely possible to execute the same attack on a soldered TPM too:
- on some systems it is rather trivial as the LPC bus reset does not reset
  the CPU so it's just a matter of grounding the reset pin on the TPM
- on other systems, grounding the reset pin on the TPM would reset the CPU,
  so cutting the reset trace near the TPM is necessary

