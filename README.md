# The laws of Fiji, as a git repository

The consolidated legislation of Fiji as a git repository: 381 Acts (including the Constitution of 2013, in the Schedule to its Promulgation Act) and 913 pieces of subsidiary legislation. The source is the [Laws of Fiji](https://www.laws.gov.fj) website, run by the Office of the Attorney-General. There is one file per section, regulation, schedule or form (42547 files), with one paragraph per line, so `git blame` and `git diff` work line by line.

**What this repository is not, yet: a history.** laws.gov.fj publishes only the current consolidated text of each law and keeps no earlier versions. So each law is a single commit holding its whole current text. Nothing before that text can be reconstructed from this source, so there is no line-by-line history before the consolidation date. New consolidations will be added from now on as later commits, so the history grows forward from here. The amendment history that the site prints is kept: each Act's Table of Amendments and the history note under each section are in the files and in [`data/amendments.csv`](data/amendments.csv).

The record holds 1294 laws, consolidated between 1928-02-28 and 2026-10-28, in 1295 commits.

## A lawyer's questions as git commands

| Question | Command |
| --- | --- |
| What does section 1A of the Arbitration Act 1965 say? | `python tools/in_force_on.py 2026-10-28 acts/arbitration-act-1965 S1A` |
| The whole of a law, in order | `python tools/in_force_on.py 2026-10-28 acts/arbitration-act-1965` |
| Which laws amended an Act, and when they commenced | `cat acts/arbitration-act-1965/title.md` (its Table of Amendments) |
| What a section's history note says | `grep -h '^\[' acts/arbitration-act-1965/S1A.md` |
| Every section an amending Act touched, by its notes | `grep -i 'Act 44 of 2017' data/amendments.csv` |
| What changed in a law since this build (after later builds) | `git log -p -- acts/arbitration-act-1965` |
| Which consolidation last wrote each line | `git blame acts/arbitration-act-1965/S2.md` |
| The list of laws, with their dates | [`laws.csv`](laws.csv) |

Each file starts with any Part or Division headings above it (`## PART 1 PRELIMINARY`), then its own heading as laws.gov.fj gives it (`# s 1A Scope of application`). Then come its paragraphs, one per line: `(1) ...`, `(a) ...`, with a defined term in quotes (`"court" means the High Court; and`). Last is the history note the consolidation prints, copied as it is: `[s 1A insrt Act 44 of 2017 s 57, effective 4 December 2018]`. Each law's `title.md` holds its title, long title and Table of Amendments, and its `index.txt` lists its files in the order of the law.

## The dates, and which one we use

For each law laws.gov.fj gives one date: the date the law was last updated on the site. **Each commit is dated by that date**, at noon Fiji standard time (UTC+12), and the date is also in the `Consolidated:` trailer. For 257 laws the site gives no date. Those are dated by the day the text was retrieved (`Date-source: retrieved`; the others have `Date-source: last-updated`). It is a publication date for the consolidation. It is not the date any amendment took effect, and it is not proof that the text was in force on that day. Commencement dates are in each Table of Amendments, and effective dates are in the section history notes (`effective 4 December 2018`). [`data/amendments.csv`](data/amendments.csv) lists both kinds of date and does not convert one into the other.

`tools/in_force_on.py` answers for any date on or after a law's consolidation date. For an earlier date it says there is no version, because the source has none.

## What "author" means

Every law-text commit has the same author: `Laws of Fiji (Office of the Attorney-General) <laws-of-fiji@laws-gov-fj.invalid>`, with the trailer `Kind: consolidated`. The address cannot exist. The author is the publisher of the consolidation, not a lawmaker. No line is credited to an amending law, because without the earlier text nobody can tell which words an amendment wrote. The history notes say which law inserted, amended or substituted a section. They are kept as text and are not used to credit lines. In the shared design for these repositories, a change is credited to an amending law only when the source shows the text before and after it. When later consolidations are added and the text changes, that change will be credited to an amending law only where a new history note names one. Otherwise it is labelled `Kind: unexplained` and authored by the publisher.

There are 1294 consolidated commits, 0 amendment commits and 0 unexplained ones. The Tables of Amendments name 3030 distinct amending laws in 4292 rows, and the sections carry 12744 history notes.

## What it does not show

- Any text before the current consolidation. laws.gov.fj has none.
- Amendments that have not commenced or have not been incorporated. Some Tables of Amendments have a footnote saying so, and it is copied into `title.md`.
- Repealed and omitted laws. The site publishes these only as scanned PDF volumes ("Omitted and repealed laws"), and they are not included.
- Acts as made. The site's "Laws as published" PDFs, from 2014, are not included.
- Pictures in the text (marked `[image]`) and the site's page and paragraph numbering (`[ARB 1]`).
- Table-of-contents entries whose text the site would not serve, laws listed with an empty table of contents, and laws with no last-update date (267 rows in all). They are listed in [`data/unreadable.csv`](data/unreadable.csv).

This is a research aid. The Laws of Fiji website says that it is not authoritative and gives no assurance of accuracy, and the same is true of this repository.

## How it is checked

`tools/build/` holds the build as it was run. [`data/source-sha256.tsv`](data/source-sha256.tsv) has the sha256 of every answer from the laws.gov.fj API that the build read. The build is deterministic: from the same answers it gives the same commit hashes. See [`REPRODUCE.md`](REPRODUCE.md). Before publishing, the build was checked for these things:
- the text `tools/in_force_on.py` prints for sample sections matches the live site;
- every commit's trailers parse;
- there are no merges, no dates that go backwards and no dates after the build date;
- two builds from the same cache give the same HEAD.

## How it is built

`fetch.py` reads the site's own JSON API: the list of Acts by initial letter, each Act's table of contents (`get_act_by_id`), which also lists its subsidiary legislation, and the HTML of every entry in it (`retrieve_html`). `build.py` turns each entry into lines, puts Part headings on the first file below them, and writes one commit per law with `git fast-import`. No AI model takes part in building or checking it.

## Licence

Source: the Laws of Fiji website (https://www.laws.gov.fj), Office of the Attorney-General, Republic of Fiji. The site states no licence. The wording was not changed; it was only split into files and lines. **This repository is private. Check the Copyright Act 1999 (Fiji) before making it public.** Lexifina's own contributions (the tools, the arrangement and the commit messages) are CC0. See [`LICENSE`](LICENSE).
