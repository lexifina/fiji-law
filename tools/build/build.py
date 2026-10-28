"""Build the Fiji law repository from the laws.gov.fj cache (fetch.py).

    python scripts/fiji-law/build.py ~/Documents/fiji-law --today YYYY-MM-DD [--limit N]

laws.gov.fj publishes only the current consolidated text of each Act and piece of subsidiary legislation; it keeps no
past versions. So the history here starts at that text:

1. Every Act and every piece of subsidiary legislation is one law. Each node of its table of contents (section,
   regulation, schedule, form...) becomes one file, one paragraph per line; headings of Parts and Divisions go on
   top of the first file under them as `##` lines. The Act's front matter and its Table of Amendments are `title.md`.
2. Each law is one commit, `Kind: consolidated`, by the publisher, dated noon Fiji standard time (UTC+12) on the
   date laws.gov.fj gives as that law's last update (`act_last_updated`). Its amendment history, as the site prints
   it, stays in the files (`[s 1A insrt Act 44 of 2017 s 57, effective 4 December 2018]`) and is listed in
   data/amendments.csv. No line is credited to an amending law, because the text before each amendment is not
   published.
3. Later builds from a newer cache append a commit per law whose text changed (`Kind: consolidated` again, dated
   by its new last-update date); this build writes the whole history from the cache in one git fast-import, so the
   same cache always gives the same hashes.
"""
import argparse
import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).parent
CACHE = HERE / '.cache'
ACTS = CACHE / 'acts'
HTML = CACHE / 'html'

COMMITTER = 'Lexifina <fiji@lexifina.com>'
PUBLISHER = ('Laws of Fiji (Office of the Attorney-General)', 'laws-of-fiji@laws-gov-fj.invalid')
SITE = 'https://www.laws.gov.fj'
MONTHS = {m: i for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                                      'september', 'october', 'november', 'december'], 1)}


# ---------------------------------------------------------------------------------------------------- html

BLOCK = {'p', 'div', 'li', 'ul', 'ol', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'section', 'table', 'tr', 'blockquote',
         'dl', 'thead', 'tbody', 'br', 'form', 'label'}


def norm(s: str) -> str:
    s = s.replace(' ', ' ').replace(' ', ' ').replace('\xa0', ' ').replace('​', '').replace('\xad', '')
    return re.sub(r'\s+', ' ', s).strip()


class ToLines(HTMLParser):
    """Section HTML -> one line per paragraph. Skips hidden anchors and the section's own title block (the heading
    is written from the table of contents instead); a definition term stays on the line of its meaning; table
    cells are joined with ' | '."""

    def __init__(self, skip_title: bool = True):
        super().__init__(convert_charrefs=True)
        self.lines: list[str] = []
        self.cur: list[str] = []
        self.stack: list[tuple[str, bool]] = []  # (tag, skipping)
        self.skip = 0
        self.title_skipped = not skip_title
        self.cell = 0
        self.cells_in_row = 0
        self.after_dt = False

    def flush(self):
        t = norm(''.join(self.cur))
        if t:
            self.lines.append(t)
        self.cur = []

    def handle_starttag(self, tag, attrs):
        if tag in ('col', 'colgroup', 'img', 'br', 'hr', 'input', 'meta', 'link'):
            if self.skip:
                return
            if tag == 'img':
                self.cur.append(' [image] ')
            elif tag == 'br' and not self.cell:
                self.flush()
            return
        a = dict(attrs)
        cls = (a.get('class') or '').split()
        skip = False
        if tag == 'style' or 'hidden' in cls or 'hiddendiv' in cls:
            skip = True
        elif tag == 'div' and 'title' in cls and not self.title_skipped:
            self.title_skipped = True
            skip = True
        self.stack.append((tag, skip))
        if skip:
            self.skip += 1
            return
        if self.skip:
            return
        if tag in ('td', 'th'):
            if self.cells_in_row:
                self.cur.append(' | ')
            self.cells_in_row += 1
            self.cell += 1
            return
        if tag == 'tr':
            self.flush()
            self.cells_in_row = 0
            return
        if tag == 'dt':
            self.flush()
            self.cur.append('"')
            return
        if tag == 'dd':
            return
        if tag in BLOCK and not self.cell:
            if self.after_dt:
                return
            self.flush()
        elif tag in BLOCK and self.cell:
            self.cur.append(' ')

    def handle_endtag(self, tag):
        # pop to the matching tag (the source HTML is well formed, but be forgiving)
        idx = None
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                idx = i
                break
        if idx is None:
            return
        popped = self.stack[idx:]
        del self.stack[idx:]
        for _, sk in popped:
            if sk:
                self.skip -= 1
        if any(sk for _, sk in popped) or self.skip:
            return
        if tag in ('td', 'th'):
            self.cell = max(0, self.cell - 1)
            return
        if tag == 'tr':
            self.flush()
            self.cells_in_row = 0
            return
        if tag == 'dt':
            # the closing quote goes right after the term
            while self.cur and not self.cur[-1].strip():
                self.cur.pop()
            self.cur.append('" ')
            self.after_dt = True
            return
        if tag in BLOCK and not self.cell:
            self.after_dt = False
            self.flush()
        elif tag == 'dd':
            self.after_dt = False
            self.flush()

    def handle_data(self, data):
        if not self.skip:
            self.cur.append(data)

    def close(self):
        super().close()
        self.flush()


def html_lines(h: str, skip_title: bool = True) -> list[str]:
    p = ToLines(skip_title)
    p.feed(h or '')
    p.close()
    out = []
    for l in p.lines:
        l = re.sub(r'^"\s+', '"', l)
        l = re.sub(r'^"([^"]*?)\s+"', r'"\1"', l)
        if l:
            out.append(l)
    return out


# ---------------------------------------------------------------------------------------------------- tree

def safe_name(lid: str) -> str:
    return lid.replace('/', '_').replace('\\', '_').replace(':', '_')


def strip_prefix(lid: str) -> str:
    s = re.sub(r'^LOF_LOF\.VOL\d+\.SGM_', '', lid)
    s = re.sub(r'^LOF\.CAP[^.]*\.SGM_', '', s)
    s = re.sub(r'^LOF\.', '', s)
    return s


def walk(nodes, depth=0):
    for n in nodes:
        yield n, depth
        yield from walk(n.get('SectionData') or [], depth + 1)


def slug(t: str) -> str:
    t = t.lower().replace('&', ' and ').replace('’', '').replace("'", '')
    t = re.sub(r'[^a-z0-9]+', '-', t).strip('-')
    return t[:90].rstrip('-') or 'law'


def clean_title(t: str) -> str:
    t = norm(t)
    t = re.sub(r'^\[[^\]]*\]\s*', '', t)
    return t


def heading_text(t: str) -> str:
    t = clean_title(t)
    return re.sub(r'\s*\[(?:ss?|regs?|rr?|paras?|cls?|arts?|by-laws?|Os?|rules?)\b[^\]]*\]\s*$', '', t, flags=re.I).strip()


def parse_day(s: str) -> str | None:
    m = re.match(r'^\s*(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})\s*$', s or '')
    if not m or m.group(2).lower() not in MONTHS:
        return None
    return f'{int(m.group(3)):04d}-{MONTHS[m.group(2).lower()]:02d}-{int(m.group(1)):02d}'


def load_laws(limit: int | None) -> list[dict]:
    """Every Act and piece of subsidiary legislation, with its nodes in document order."""
    laws: list[dict] = []
    for f in sorted(ACTS.glob('*.json'), key=lambda p: int(p.stem)):
        data = json.loads(f.read_text('utf-8'))
        act_id = f.stem
        parent = None
        for block in data:
            is_sub = (block.get('ActName') or '').strip().lower() == 'subsidiary legislation'
            current = None
            for top in block.get('Sections') or []:
                lid = top['LegalId']
                if lid.endswith('.BODY') or current is None:
                    code = strip_prefix(lid)[:-5] if lid.endswith('.BODY') else strip_prefix(lid)
                    current = {'act_id': act_id, 'kind': 'subsidiary' if is_sub else 'act', 'code': code,
                               'body': lid, 'title': norm(top['Title']), 'nodes': [],
                               'parent': parent['title'] if (is_sub and parent) else '',
                               'parent_code': parent['code'] if (is_sub and parent) else ''}
                    laws.append(current)
                    if not is_sub and parent is None:
                        parent = current
                for n, depth in walk([top]):
                    current['nodes'].append({'lid': n['LegalId'], 'title': n['Title'], 'pos': int(n.get('Position') or 0), 'file': n.get('FileName') or '',
                                             'depth': depth, 'repealed': n.get('IsRepealed') == 'true',
                                             'status': n.get('Status')})
    # document order, ties by tree order
    for law in laws:
        # Position is an offset inside the node's HTML file. Laws split over numbered volume files
        # (vol110081000.htm, vol110081003.htm, ...) are ordered by file, then offset; others by offset alone.
        vol = all(re.fullmatch(r'vol\d+\.htm', n['file']) for n in law['nodes'])
        law['nodes'] = [n for _, n in sorted(enumerate(law['nodes']), key=lambda x: (
            (int(x[1]['file'][3:-4]) if vol else 0), x[1]['pos'], x[0]))]
        seen = set()
        law['nodes'] = [n for n in law['nodes'] if not (n['lid'] in seen or seen.add(n['lid']))]
    # folders: acts/<slug>, subsidiary/<slug>; deterministic tie-break by code
    used: dict[str, str] = {}
    for law in sorted(laws, key=lambda l: (l['kind'], l['code'], l['act_id'])):
        base = f"{'acts' if law['kind'] == 'act' else 'subsidiary'}/{slug(law['title'])}"
        d = base
        k = 2
        while d in used and used[d] != law['code']:
            d = f'{base}-{k}'
            k += 1
        used[d] = law['code']
        law['dir'] = d
    laws.sort(key=lambda l: l['dir'])
    return laws[:limit] if limit else laws


def unit_id(law: dict, lid: str) -> str:
    rel = strip_prefix(lid)
    short = law['code'].split('.')[-1]
    if rel.startswith(law['code'] + '.'):
        rel = rel[len(law['code']) + 1:]
    elif f'.{short}.' in rel:
        rel = rel.split(f'.{short}.', 1)[1]
    elif rel.startswith(short + '.'):
        rel = rel[len(short) + 1:]
    elif rel.startswith('SCHEDULE.'):
        rel = rel.split('.', 1)[1]
    rel = re.sub(r'[^0-9A-Za-z._-]', '-', rel)
    return rel or 'unit'


HIST_RE = re.compile(r'\[[^\[\]]*\b(?:insrt|inserted|am|amended|subst|substituted|rep|repealed|renum|renumbered|'
                     r'corrected|effective)\b[^\[\]]*\]')
LAW_RE = re.compile(r'\b((?:Act|Decree|Ordinance|Promulgation|LN|Legal Notice|GN|Regulations?)\s+(?:No\s+)?\d+[A-Z]?\s+of\s+\d{4})')
EFF_RE = re.compile(r'\b(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})')


def build_law(law: dict) -> dict:
    """path -> text for one law; plus amendment rows and issues."""
    files: dict[str, str] = {}
    order: list[str] = []
    amend: list[list[str]] = []
    issues: list[dict] = []
    pending: list[str] = []  # headings waiting for the next file
    updated = []
    seen_ids: dict[str, int] = {}
    for n in law['nodes']:
        p = HTML / f"{safe_name(n['lid'])}.json"
        try:
            d = json.loads(p.read_text('utf-8'))
        except (OSError, json.JSONDecodeError):
            d = {'error': 'not fetched'}
        if 'error' in d:
            issues.append({'law': law['title'], 'node': n['lid'], 'issue': d.get('error')})
            continue
        if d.get('act_last_updated'):
            updated.append(d['act_last_updated'])
        is_body = n['lid'] == law['body']
        lines = html_lines(d.get('section_html') or '', skip_title=not is_body)
        for fn in d.get('FootNoteRels') or []:
            lines += [l for l in html_lines(fn.get('Html') or '', skip_title=False) if l not in lines]
        if is_body:
            head = [f"# {law['title']}"]
            desc = html_lines(d.get('act_description') or '')
            body_lines = head + desc + lines
            files[f"{law['dir']}/title.md"] = '\n'.join(body_lines) + '\n'
            order.append('title.md')
            # Table of Amendments rows
            for l in lines:
                cells = [c.strip() for c in l.split(' | ')]
                if len(cells) == 2 and cells[0] != 'Amending Legislation':
                    amend.append([law['dir'], 'title', 'table of amendments', cells[0], parse_day(cells[1]) or cells[1], l])
            continue
        if not lines:
            # a Part, Division or schedule group heading: put it on top of the next file
            h = heading_text(n['title'])
            if h:
                pending.append('#' * min(2 + n['depth'] // 99, 6) + ' ' + h)
            continue
        uid = unit_id(law, n['lid'])
        if uid in seen_ids:
            seen_ids[uid] += 1
            uid = f'{uid}~{seen_ids[uid]}'
        else:
            seen_ids[uid] = 1
        text_lines = [*pending, f"# {clean_title(n['title'])}", *lines]
        pending = []
        path = f"{law['dir']}/{uid}.md"
        files[path] = '\n'.join(text_lines) + '\n'
        order.append(f'{uid}.md')
        for l in lines:
            for note in HIST_RE.findall(l):
                laws_named = sorted(set(LAW_RE.findall(note)))
                effs = [parse_day(e) or e for e in EFF_RE.findall(note)]
                amend.append([law['dir'], uid, 'note', '; '.join(laws_named), '; '.join(effs), note])
    if pending:
        files[f"{law['dir']}/headings.md"] = '\n'.join(pending) + '\n'
        order.append('headings.md')
    if files:
        files[f"{law['dir']}/index.txt"] = '\n'.join(order) + '\n'
    days = sorted({x for x in (parse_day(u) for u in updated) if x})
    return {'files': files, 'amend': amend, 'issues': issues, 'updated': days[-1] if days else None,
            'updated_all': days}


# ---------------------------------------------------------------------------------------------------- write

def git_date(day: str, seq: int) -> str:
    """Noon Fiji standard time (UTC+12). Before 1970: 1970-01-01 plus seq seconds (real date in the trailer)."""
    d = datetime.strptime(day, '%Y-%m-%d')
    if d.year < 1970:
        return f'{seq} +1200'
    ts = int(datetime(d.year, d.month, d.day, 0, 0, tzinfo=timezone.utc).timestamp())  # noon at UTC+12 = 00:00 UTC
    return f'{ts} +1200'


def message(law: dict, day: str, built: dict) -> tuple[str, str, str]:
    name, email = PUBLISHER
    label = law['title'] if law['kind'] == 'act' else f"{law['title']} (under the {law['parent'].title() if law['parent'] else 'Act'})"
    retrieved = law.get('date_source') == 'retrieved'
    subject = (f"{law['title']}: as consolidated on laws.gov.fj, retrieved {day}" if retrieved else
               f"{law['title']}: as consolidated on laws.gov.fj, last updated {day}")
    n_notes = sum(1 for r in built['amend'] if r[2] == 'note')
    n_table = sum(1 for r in built['amend'] if r[2] == 'table of amendments')
    first = (f"The text of the {label} as laws.gov.fj publishes it. The site gives no last-update date for it, so it is dated by the day it was retrieved, {day}."
             if retrieved else f"The text of the {label} as laws.gov.fj publishes it, which the site gives as last updated on {day}.")
    body = [first,
            'laws.gov.fj keeps no earlier versions, so this commit holds the whole text and nobody is credited with',
            'single lines. The amendment history the site prints is kept in the files: the Table of Amendments in',
            f"title.md ({n_table} amending laws) and the history notes under sections ({n_notes} notes)."]
    trailers = ['Kind: consolidated', f'Consolidated: {day}', f"Law: {law['title']}",
                f"Law-kind: {'act' if law['kind'] == 'act' else 'subsidiary'}",
                f"Date-source: {'retrieved' if retrieved else 'last-updated'}"]
    if law['parent']:
        trailers.append(f"Parent-act: {law['parent']}")
    trailers.append(f"Source: {SITE}/acts/DisplayAct/{law['act_id']}")
    return f'{name} <{email}>', subject, '\n'.join([subject, '', *body, '', *trailers]) + '\n'


def fast_import(repo: Path, commits: list[tuple], docs: dict[str, bytes], today: str) -> None:
    buf = io.BytesIO()
    w = buf.write
    seq = 0
    for day, law, built in commits:
        seq += 1
        author, _, msg = message(law, day, built)
        when = git_date(day, seq)
        w(b'commit refs/heads/main\n')
        w(f'author {author} {when}\ncommitter {COMMITTER} {when}\n'.encode())
        m = msg.encode('utf-8')
        w(f'data {len(m)}\n'.encode() + m + b'\n')
        for path, text in sorted(built['files'].items()):
            t = text.encode('utf-8')
            w(f'M 100644 inline {path}\ndata {len(t)}\n'.encode() + t + b'\n')
        w(b'\n')
    when = git_date(today, seq + 1)
    msg = (f'Documentation: README, REPRODUCE, tools, laws.csv and data\n\n'
           f'Built from the laws.gov.fj cache on {today}.\n\nKind: documentation\n').encode()
    w(b'commit refs/heads/main\n')
    w(f'author {COMMITTER} {when}\ncommitter {COMMITTER} {when}\n'.encode())
    w(f'data {len(msg)}\n'.encode() + msg + b'\n')
    for path, data in sorted(docs.items()):
        w(f'M 100644 inline {path}\ndata {len(data)}\n'.encode() + data + b'\n')
    w(b'\n')
    r = subprocess.run(['git', '-C', str(repo), 'fast-import', '--quiet', '--force'], input=buf.getvalue(),
                       capture_output=True)
    if r.returncode:
        sys.exit(r.stderr.decode('utf-8', 'replace')[-3000:])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('repo', type=Path)
    ap.add_argument('--today', required=True)
    ap.add_argument('--limit', type=int)
    ap.add_argument('--workers', type=int, default=8)
    args = ap.parse_args()
    if not re.match(r'^\d{4}-\d{2}-\d{2}$', args.today):
        sys.exit('--today must be YYYY-MM-DD')

    laws = load_laws(args.limit)
    fo = CACHE / 'fetched_on.txt'
    fetched_on = fo.read_text('utf-8').strip() if fo.exists() else args.today
    if fetched_on > args.today:
        sys.exit(f'retrieval date {fetched_on} is after --today')
    # Acts whose table of contents is empty: listed, not built
    empty = []
    for f in sorted(ACTS.glob('*.json'), key=lambda p: int(p.stem)):
        for block in json.loads(f.read_text('utf-8')):
            if not block.get('Sections') and (block.get('ActName') or '').strip().lower() != 'subsidiary legislation':
                empty.append({'law': norm(block.get('ActName') or ''), 'node': f'ActId {f.stem}',
                              'issue': 'listed by laws.gov.fj with an empty table of contents; no text'})
    commits = []
    issues: list[dict] = list(empty)
    amend: list[list[str]] = []
    no_date = 0
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(args.workers) as pool:
        results = list(pool.map(build_law, laws, chunksize=4))  # ordered, so the result does not depend on timing
    for law, built in zip(laws, results):
        issues += built['issues']
        amend += built['amend']
        law['units'] = sum(1 for p in built['files'] if not p.endswith(('/title.md', '/index.txt', '/headings.md')))
        law['amendments_listed'] = sum(1 for r in built['amend'] if r[2] == 'table of amendments')
        law['notes'] = sum(1 for r in built['amend'] if r[2] == 'note')
        if not built['files']:
            law['consolidated'] = ''
            issues.append({'law': law['title'], 'node': law['body'], 'issue': 'no text'})
            continue
        day = built['updated']
        if not day or day > args.today:
            no_date += 1
            issues.append({'law': law['title'], 'node': law['body'],
                           'issue': f"last-update date {day or 'missing'}; dated by the retrieval date {fetched_on}"})
            day = fetched_on
            law['date_source'] = 'retrieved'
        law['consolidated'] = day
        commits.append((day, law, built))
    commits.sort(key=lambda c: (c[0], 0 if c[1]['kind'] == 'act' else 1, c[1]['dir']))
    print(f'{len(laws)} laws, {len(commits)} commits, {len(issues)} issues, {len(amend)} amendment rows', flush=True)

    import docs as docmod
    docs = docmod.render(laws, commits, issues, amend, args.today)

    repo = args.repo
    repo.mkdir(parents=True, exist_ok=True)
    remote = None
    if (repo / '.git').exists():
        r = subprocess.run(['git', '-C', str(repo), 'remote', 'get-url', 'origin'], capture_output=True, text=True)
        remote = r.stdout.strip() or None
        import os
        import shutil
        import stat

        def onerr(func, path, _):
            os.chmod(path, stat.S_IWRITE)
            func(path)
        shutil.rmtree(repo / '.git', onerror=onerr)
        for child in repo.iterdir():
            shutil.rmtree(child, onerror=onerr) if child.is_dir() else child.unlink()
    subprocess.run(['git', 'init', '-q', '-b', 'main', str(repo)], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'core.autocrlf', 'false'], check=True)
    subprocess.run(['git', '-C', str(repo), 'config', 'core.longpaths', 'true'], check=True)
    if remote:
        subprocess.run(['git', '-C', str(repo), 'remote', 'add', 'origin', remote], check=True)
    fast_import(repo, commits, docs, args.today)
    subprocess.run(['git', '-C', str(repo), 'checkout', '-q', '-f', 'main'], check=True)
    head = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    count = subprocess.run(['git', '-C', str(repo), 'rev-list', '--count', 'HEAD'], capture_output=True, text=True).stdout.strip()
    print(f'built {repo}: {count} commits, head {head}', flush=True)


if __name__ == '__main__':
    main()
