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

**Drawn rather than traced**: capital `X`. It is the only such glyph, and the
reason it exists is that a font for modern English needs one.

No Kelmscott volume sampled prints a capital `X`, and the rule behind that is
the interesting part -- see the table below. Rather than leave the alphabet
short, the letter is built from the face's own strokes: two half-height copies
of Troy's `V`, one rotated, so their points meet at the centre and their four
flared terminals land at the four corners. It inherits the face's weight,
modulation and terminal shapes rather than being invented outright, but it is
drawn, and it is recorded as drawn.

Two earlier constructions failed usefully. Stretching V's diagonals across the
full width doubled their horizontal thickness and made the letter far too
heavy. Shearing them apart preserved the weight but left V's converging foot as
two bare spikes where an X wants terminals. A donor has to supply the *ends* you
need, not only the slopes -- which is what taking V whole, twice, does.

**Composed from the fount's own marks**: `:` `'` `"`. None was printed in the
sampled pages, and none needed drawing. A colon is two of the existing period,
one on the baseline and one at the x-height. An apostrophe is a raised comma --
it was cut as one for centuries, so lifting the comma to the cap line gives the
mark this face would have had, with its own weight and its own tail. A double
quote is two of those.

**Still absent**: `!` `(` `)`.

Capital `X` is not printed in the sampled corpus, and every route to it was
checked rather than assumed:

| Where a capital `X` might appear | What is actually there |
|---|---|
| Chaucer / Boece book numbering | capital roman -- but the books only run I to V |
| Prose and metre headings | red Latin incipits, not numerals |
| The Astrolabe's forty-odd conclusions | *arabic* figures -- which is where this font's digits come from |
| Godefrey's chapter numbers | "capitulo Cxij" -- capital C, **lowercase** xij |
| Psalmi Penitentiales' psalm numbers | "Ps. xxxi.", "Ps. xxxvii.", "Ps. l." -- **lowercase**, and past ten |
| The Chaucer's colophon | "the 8th day of May, 1896" -- arabic |
| Words beginning with `X` | Middle English has none |

The rule behind all of it: **the Kelmscott Press sets roman numerals in
lowercase**. Capital roman appears only in running heads -- "Book II.", "Book
III." -- and no work in these volumes has more than five books. Everything that
counts higher (chapters, psalms, sections) is set lowercase. So the corpus does
reach and pass ten repeatedly; it simply never does so in capitals.

Note the Godefrey case, which is the closest miss: the numbering does reach and
pass ten, so the letter is printed -- as a *lowercase* `x`, which this font
already has from body text. Every apparent capital `X` in the OCR is an `I`
misread; the running head the transcription gives as "Book XX" reads **Book II**
on the page.

Capital `F` took two attempts and the first was wrong. Troy sets a lowercase `f`
even at the start of a line -- "ful sykerly they slepten" -- so the capital
occurs almost nowhere in body text, and the only instances are in the display
heading of the Canterbury Tales opening. The `F` of "AND FIRST" is *fused to the
following `I`*, and connected-component analysis returns them as one glyph: the
enclosed white shape that reads as the letter's counter is really the gap
between F and I. That version shipped briefly and was wrong. The `F` of
"THEREOF" at the end of the same heading is isolated, and is the one in the font.

Nothing in this font is drawn. Every glyph is traced from printed impressions
of Morris's type. Two dots are reconstructed rather than traced, and both use
the fount's own marks: the tittle on `j` is `i`'s dot, and the dot under `?` is
the period. Both are lost to segmentation rather than absent from the page --
mark re-attachment joins a small component to the letter below it, which is
right for `i` and wrong for `?`.
