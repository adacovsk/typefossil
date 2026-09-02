# Provenance of the fonts in this repository

Everything here is traced from photographs of books printed before 1900. This
file records which books, so the claim can be checked rather than taken on
trust.

## Kelmscott Troy

**What it is.** A digitisation of the *Troy* type, cut for William Morris's
Kelmscott Press and first used in 1892. Troy is a semi-gothic face — roman
proportions with blackletter detail — and it is the larger of the two sizes;
the smaller cut of the same design is called *Chaucer*.

**Primary source.** *The History of Godefrey of Boloyne and of the Conquest of
Iherusalem*, Kelmscott Press, 1893, set throughout in Troy. Scanned by the
Internet Archive, identifier
[`TheHistoryOfGodefreyOfBoloyneAndOfTheConquestOfIherusalem`](https://archive.org/details/TheHistoryOfGodefreyOfBoloyneAndOfTheConquestOfIherusalem),
page images at 4928 × 7353. Sixty-one text pages contributed roughly 67,000
glyph instances.

**Secondary source.** *The Works of Geoffrey Chaucer*, Kelmscott Press, 1896 —
the Kelmscott Chaucer — identifier
[`MorrisChaucer`](https://archive.org/details/MorrisChaucer), page images at
6461 × 9900. Used for characters Godefrey never prints. It is set in the
Chaucer cut, so its masters are scaled to Troy's x-height before use; because
the smaller cut is optically a little heavier, this is a starting point that
wants an eye on it rather than a purely mechanical conversion.

**Why a second source was needed at all.** A book is a sample of a fount, not
an inventory of it. Middle English prose printed in 1893 simply does not
contain every character a usable font needs:

- **Arabic numerals appear nowhere in the body text.** Morris set numbers as
  roman numerals. The only arabic figures in the Kelmscott corpus are the folio
  numbers at the foot of each page, which is where this font's digits come from.
- **`j` and `z` are effectively absent.** Middle English does not distinguish
  `i` from `j`, and `z` is vanishingly rare.
- **Most capitals are scarce.** Chapter openings use large decorated woodcut
  initials rather than type, so a capital only appears where a sentence or a
  proper noun begins mid-paragraph.

Where a character could not be found in either source, that is recorded in the
font's build output rather than papered over.

## Copyright status

**The letterforms.** Morris died in 1896 and the types date from 1892–93. The
designs are in the public domain everywhere.

**The scans.** A faithful photographic reproduction of a flat public-domain
work acquires no new copyright of its own. This is settled in the United States
(*Bridgeman Art Library v. Corel*, 1999) and is the position the Internet
Archive itself takes. The scans are therefore usable as source material, not
merely as reference.

**This digitisation.** The outline data, metrics and font software are new work
and are copyright the contributors, licensed under the SIL Open Font License
1.1 — see `LICENSES/OFL-1.1.txt`. No Reserved Font Name is asserted.

**What was deliberately not used.** Existing digital fonts of these faces exist,
including Dieter Steffmann's widely distributed "Morris Roman" (which, despite
the name, is Troy rather than Morris's actual roman). None was used as a source,
a reference, or a tracing base, and none is redistributed here. Those files
carry their own end-user licence terms — the 1001Fonts FFC licence, in that
case, forbids modifying or building upon the font — and such terms bind as
contract regardless of the underlying design being public domain. Working from
the printed page avoids the question entirely, and produces a better result: the
1896 press sheets are a closer record of the punches than anyone's 2000s
redrawing.

## What Kelmscott Troy contains, and what it does not

Built from 67,110 glyph instances across 61 pages of Godefrey, plus 162,397
instances across 48 pages of the Chaucer for the characters Godefrey lacks.

**Present** (47): `a`–`z` except `z`, `A B E G H I J L M N O P S T W Y`, and
`, . ; ? - &`.

**Absent, and why.** Every gap is a property of the corpus rather than of the
pipeline, and each was searched for specifically:

- **`z`** — not found in any sampled page. The Chaucer's OCR reports `z` words
  (`zodiak`, `azimut`, `Zephirus`), but blackletter OCR maps yogh and long-s to
  `z`, so most of those are spurious; the genuinely `z`-bearing text was not in
  the sampled range. Middle English uses the letter very rarely.
- **Capitals `C D F K Q R U V X Z`** — Godefrey sets chapter openings as woodcut
  initials rather than type, so its type capitals are scarce; the Chaucer
  capitalises every verse line and supplied sixteen, but not these.
- **Digits `0` and `3`** — the other eight come from Chaucer folio numbers, the
  only arabic figures in the corpus. Folio numbers in the sampled range simply
  did not yield a clean master for these two.
- **`! " ' ( ) :`** — not observed in the sampled pages.

**The fix for all of these is more source, not more processing.** Each is a
letter the sampled books do not print often enough. Kelmscott issued some fifty
volumes in these two types; adding one more Troy-set book would likely close
most of the capital gaps, and the Chaucer's glossary — alphabetical, so every
initial appears — is the obvious target for the rest.

Nothing in this font is composed or invented. Every glyph is traced from
printed impressions of Morris's type.
