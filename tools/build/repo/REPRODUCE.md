# Reproducing this repository

Built on {{TODAY}} from the laws.gov.fj API, by the scripts in `tools/build/` (copied there as run).

| Script | sha256 |
| --- | --- |
| build.py | `{{SHA_BUILD_PY}}` |
| docs.py | `{{SHA_DOCS_PY}}` |

## Steps

```sh
# 1. The retrieved files: the list of Acts, each Act's table of contents and the HTML of every entry in it
#    (sha256 in data/source-sha256.tsv), where build.py reads them.
# 3. Build. --today dates the documentation commit and is the latest date allowed.
python build.py ../fiji-law --today {{TODAY}}
```

## Bulk data

The site offers no bulk download or dump: its API serves one table of contents per Act and one entry per page.

[`data/source-sha256.tsv`](data/source-sha256.tsv) lists the sha256 of each retrieved file. With the same files, `build.py` gives the same commit hashes, because it writes the whole history in one `git fast-import` stream, sorted, with fixed dates.

## What the build produced

- {{LAWS}} laws: {{ACTS}} Acts, {{SUBSIDIARY}} pieces of subsidiary legislation; {{UNITS}} unit files.
- {{COMMITS}} commits: {{CONSOLIDATED}} consolidated (one per law) and one documentation commit.
- Consolidation dates from {{FIRST}} to {{LAST}}.
- {{UNREADABLE}} entries left out (`data/unreadable.csv`).

## Checks

```sh
git rev-list --merges --count main                  # 0
git log --format='%ad %(trailers:key=Kind,valueonly)' --date=short main | sort -c -r -k1,1   # dates never go back
python tools/in_force_on.py {{TODAY}} acts/arbitration-act-1965 S1A
```

Rebuilding twice from the same retrieved files gives the same `git rev-parse HEAD`.
