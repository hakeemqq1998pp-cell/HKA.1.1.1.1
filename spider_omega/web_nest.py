"""Public-page crawler that builds a persistent local nest per website."""
import hashlib
import sqlite3
import time
from collections import deque
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

AGENT = "THE-SPIDER-OMEGA/1.0 (polite research crawler)"
class Extractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title, self.text, self.links = [], [], []
        self.in_title = False
        self.skip = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title": self.in_title = True
        if tag in ("script", "style", "noscript"): self.skip += 1
        if tag == "a" and a.get("href"): self.links.append(a["href"])
    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
        if tag in ("script", "style", "noscript") and self.skip: self.skip -= 1
    def handle_data(self, data):
        s = " ".join(data.split())
        if not s: return
        if self.in_title: self.title.append(s)
        if not self.skip: self.text.append(s)

def clean_url(url):
    p = urlparse(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        return None
    return urldefrag(url)[0]

def make_nest(seed):
    host = urlparse(seed).hostname
    key = hashlib.sha256(host.encode()).hexdigest()[:10]
    folder = Path("spider_nests") / (host.replace(":", "_")[:50] + "_" + key)
    folder.mkdir(parents=True, exist_ok=True)
    dbpath = folder / "nest.sqlite3"
    with sqlite3.connect(dbpath) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS pages(
            url TEXT PRIMARY KEY, title TEXT, body TEXT,
            saved_at TEXT DEFAULT CURRENT_TIMESTAMP, keywords TEXT)""")
    return dbpath

def robots_allowed(origin, url):
    robots = origin + "/robots.txt"
    try:
        req = Request(robots, headers={"User-Agent": AGENT})
        with urlopen(req, timeout=5) as r:
            lines = r.read(200000).decode("utf-8", "replace").splitlines()
        from urllib.robotparser import RobotFileParser
        rp = RobotFileParser()
        rp.parse(lines)
        return rp.can_fetch(AGENT, url)
    except Exception:
        return False

def fetch_page(url, host):
    req = Request(url, headers={"User-Agent": AGENT, "Accept": "text/html"})
    with urlopen(req, timeout=8) as r:
        final = clean_url(r.geturl())
        if not final or urlparse(final).hostname != host:
            return None
        if "text/html" not in r.headers.get("Content-Type", "").lower():
            return None
        raw = r.read(1000001)
        if len(raw) > 1000000: return None
        charset = r.headers.get_content_charset() or "utf-8"
        return raw.decode(charset, "replace"), final

def crawl_site(seed_url, max_pages=20, max_depth=2, keywords=None, delay=2):
    seed = clean_url(seed_url)
    if not seed: raise ValueError("Use a valid public http(s) URL without embedded credentials.")
    host = urlparse(seed).hostname
    origin = "{}://{}".format(urlparse(seed).scheme, urlparse(seed).netloc)
    dbpath = make_nest(seed)
    queue, seen = deque([(seed, 0)]), set()
    terms = [x.strip().lower() for x in (keywords or []) if x.strip()]
    stored, notes = 0, []
    robots = {}
    while queue and stored < max(1, min(int(max_pages), 100)):
        url, depth = queue.popleft()
        if url in seen: continue
        seen.add(url)
        if origin not in robots: robots[origin] = robots_allowed(origin, url)
        if not robots[origin]:
            notes.append("robots.txt unavailable or disallows crawling: " + url)
            break
        try:
            page = fetch_page(url, host)
            if page is None: continue
            html, final = page
            ex = Extractor()
            ex.feed(html)
            title = " ".join(ex.title)[:500]
            body = " ".join(ex.text)[:100000]
            found = [k for k in terms if k in (title + " " + body).lower()]
            with sqlite3.connect(dbpath) as db:
                db.execute("""INSERT OR REPLACE INTO pages(url,title,body,keywords)
                    VALUES(?,?,?,?)""", (final, title, body, ", ".join(found)))
            stored += 1
            if depth < max_depth:
                for href in ex.links:
                    nxt = clean_url(urljoin(final, href))
                    if not nxt or urlparse(nxt).hostname != host or nxt in seen: continue
                    if urlparse(nxt).path.lower().endswith((".pdf",".jpg",".png",".zip",".mp4")): continue
                    queue.append((nxt, depth + 1))
        except (HTTPError, URLError, TimeoutError, ValueError) as e:
            notes.append("{}: {}".format(url, str(e)[:140]))
        if queue: time.sleep(max(1.0, min(float(delay), 10.0)))
    return {"database": str(dbpath), "stored": stored, "notes": notes[:8], "seed": seed}

def search_nests(query, limit=20):
    found, term = [], "%" + query.strip() + "%"
    for path in Path("spider_nests").glob("*/nest.sqlite3"):
        try:
            with sqlite3.connect(path) as db:
                rows = db.execute("""SELECT title,url,substr(body,1,600),saved_at,keywords
                    FROM pages WHERE title LIKE ? OR body LIKE ?
                    ORDER BY saved_at DESC LIMIT ?""",
                    (term, term, max(1, min(limit, 100)))).fetchall()
                found.extend(rows)
        except sqlite3.Error:
            pass
    return found[:max(1, min(limit, 100))]
