# Reproducing this repository

Built on {{TODAY}} from the laws.gov.fj API, by the scripts in `tools/build/` (copied there as run).

| Script | sha256 |
| --- | --- |
| fetch.py | `{{SHA_FETCH_PY}}` |
| build.py | `{{SHA_BUILD_PY}}` |
| docs.py | `{{SHA_DOCS_PY}}` |

## Steps

```sh
# 1. The list of Acts and each Act's table of contents (about 400 requests).
python fetch.py catalogue
# 2. The HTML of every table-of-contents entry (about 50,000 requests, 16 at a time; resumable).
#    "Document not found" answers are cached too and retried after a day.
python fetch.py sections
# 3. Build. --today dates the documentation commit and is the latest date allowed.
python build.py ../fiji-law --today {{TODAY}}
```

## robots.txt and bulk data

This was checked on 2026-10-28, before and after the crawl. `https://www.laws.gov.fj/robots.txt` and `https://laws.gov.fj/robots.txt` both answer 404, whether asked as a browser, as `ClaudeBot` or as `GPTBot`. So there are no rules at all, and none aimed at AI crawlers (ClaudeBot, Claude-Web, anthropic-ai, GPTBot and the like). The site's page says `<meta name="robots" content="index, follow">`, and the API answers carry no `X-Robots-Tag`. The site offers no bulk download or dump: its API (read from the site's own JavaScript) serves one table of contents per Act and one entry per request. Hence the crawl.

## Fetch rate

laws.gov.fj has no robots.txt (the address answers 404), so it sets no Crawl-delay. `fetch.py` sends at most 16 requests at a time and makes no further ones while those are open. Each answer takes about 1.4 s, so the rate came to about 7 to 10 requests a second, and fetching all ~50,000 entries took about 1.5 hours. A failed request is retried up to 4 times, waiting 2, 4, 6 and 8 s. A 404 or "Document not found" answer is cached and is not asked again for a day.

The scripts call `curl` (not Python's HTTP client) and keep every answer under `.cache/` (git-ignored). [`data/source-sha256.tsv`](data/source-sha256.tsv) lists the sha256 of each cached answer. With the same answers, `build.py` gives the same commit hashes, because it writes the whole history in one `git fast-import` stream, sorted, with fixed dates.

## What the build produced

- {{LAWS}} laws: {{ACTS}} Acts, {{SUBSIDIARY}} pieces of subsidiary legislation; {{UNITS}} unit files.
- {{COMMITS}} commits: {{CONSOLIDATED}} consolidated (one per law) and one documentation commit.
- Consolidation dates from {{FIRST}} to {{LAST}}.
- {{UNREADABLE}} entries the site would not serve (`data/unreadable.csv`).

## Checks

```sh
git rev-list --merges --count main                  # 0
git log --format='%ad %(trailers:key=Kind,valueonly)' --date=short main | sort -c -r -k1,1   # dates never go back
python tools/in_force_on.py {{TODAY}} acts/arbitration-act-1965 S1A
```

Rebuilding twice from the same cache gives the same `git rev-parse HEAD`.
