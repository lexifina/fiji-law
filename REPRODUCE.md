# Reproducing this repository

Built on 2026-10-28 from the laws.gov.fj API, by the scripts in `tools/build/` (copied there as run).

| Script | sha256 |
| --- | --- |
| build.py | `e52d6f7974d10c6501511b4c0bb5554c6466fc7de76c926d95157a47be503a43` |
| docs.py | `6c3c06f1ef67cd02473a96d506851cb4419e1bac2ccd2de30bfe92092c14c1ff` |

## Steps

```sh
# 1. The retrieved files: the list of Acts, each Act's table of contents and the HTML of every entry in it
#    (sha256 in data/source-sha256.tsv), where build.py reads them.
# 3. Build. --today dates the documentation commit and is the latest date allowed.
python build.py ../fiji-law --today 2026-10-28
```

## Bulk data

The site offers no bulk download or dump: its API serves one table of contents per Act and one entry per page.

[`data/source-sha256.tsv`](data/source-sha256.tsv) lists the sha256 of each retrieved file. With the same files, `build.py` gives the same commit hashes, because it writes the whole history in one `git fast-import` stream, sorted, with fixed dates.

## What the build produced

- 1294 laws: 381 Acts, 913 pieces of subsidiary legislation; 42547 unit files.
- 1295 commits: 1294 consolidated (one per law) and one documentation commit.
- Consolidation dates from 1928-02-28 to 2026-10-28.
- 267 entries left out (`data/unreadable.csv`).

## Checks

```sh
git rev-list --merges --count main                  # 0
git log --format='%ad %(trailers:key=Kind,valueonly)' --date=short main | sort -c -r -k1,1   # dates never go back
python tools/in_force_on.py 2026-10-28 acts/arbitration-act-1965 S1A
```

Rebuilding twice from the same retrieved files gives the same `git rev-parse HEAD`.
