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

Built from three sources, because no one of them prints the whole character set.

| Source | Contributes | Instances |
|---|---|---|
| Godefrey of Boloyne (1893), Troy type | lowercase | 67,110 across 61 pages |
| Kelmscott Chaucer (1896), Chaucer type | capitals | 162,397 across 48 pages |
| Chaucer, *Treatise on the Astrolabe* | `z`, digits, remaining capitals | 95,415 across 29 pages |

**Present** (58): `a`–`z`, `A B C E G H I J L M N O P S T V W Y`, `2`–`9`, and
`, . ; ? - &`.

**Why three sources.** A book is a sample of a fount, not an inventory of it,
and the gaps are systematic:

- **`z`** is barely used in Middle English. It appears in the Astrolabe, whose
  astronomical vocabulary carries *zodiak*, *azimut* and *zenith*, and
  essentially nowhere else in the corpus.
- **Arabic numerals** appear nowhere in Morris's literary text at all — he sets
  roman numerals throughout. The Astrolabe is the exception, because it states
  measurements: "in hir latitude of 2 degrees". Every digit in this font comes
  from there.
- **Capitals** are scarce in Godefrey, which opens chapters with woodcut
  initials rather than type. The Chaucer is verse and capitalises every line.

Locating the Astrolabe was itself a search: the OCR reports `z` throughout the
volume, but blackletter OCR maps yogh and long-s to `z`, so most of those are
spurious. Mapping the genuine z-words to a fraction of the text, and that
fraction to a leaf number, put it at leaves 414–442.

**Still absent**: `0`, `1`, capitals `C F K Q R U X Z`, and `! " ' ( ) :`.

These were searched for hard rather than assumed missing. The corpus sampled is
185 pages of Godefrey and 128 of the Chaucer -- roughly 370,000 glyph instances
-- and none of them contains these characters in usable form. A later pass
added 124 further Godefrey pages specifically hunting the capitals and found
none; its few capital clusters were blurrier than the Chaucer ones already in
the font and were discarded rather than allowed to regress it.

The reason is the text, not the sampling. Godefrey opens chapters with woodcut
initials rather than type, so it prints few capitals at all; the Chaucer's verse
capitals are frequent but follow the distribution of words that begin lines of
Middle English poetry, in which `Q`, `X` and `Z` scarcely appear. `0` and `1`
are absent for the same reason as the other digits nearly were -- arabic figures
occur only in the Astrolabe -- and those two simply did not recur often enough
there to average a clean master.

Nothing in this font is invented. Every glyph is traced from printed
impressions of Morris's type. The one composed element is the tittle on `j`,
which is `i`'s own dot from the same fount, restored because the `j` cluster
averaged without it.
