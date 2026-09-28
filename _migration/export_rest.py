#!/usr/bin/env python3
"""
Export the blog posts from the local WordPress (docker compose, http://localhost:8080)
into this Jekyll site.

Source: the WordPress REST API. Its `content.rendered` is what WordPress itself shows:
umlauts decoded correctly, paragraphs/typography applied, shortcodes gone, and spam +
old-host URLs already cleaned by wp-local/.../mu-plugins/vf-local-cleanup.php.

Writes (and replaces on every run):
  _posts/YYYY-MM-DD-<slug>.html       one file per published post
  wp-content/…, downloads/…           only the files the posts reference, same paths,
                                      so old image/file URLs keep working
  _migration/export-report.json       what was done / what is missing

Read-only towards WordPress. Usage (from the site/ folder):
  python3 _migration/export_rest.py
"""
import html
import json
import os
import re
import shutil
import sys
import urllib.request
from html.parser import HTMLParser
from urllib.parse import unquote

WP = os.environ.get("WP_URL", "http://localhost:8080")
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(SITE)
# Where referenced files are copied from, in order. wp-local/ is the content-checked copy.
FILE_SOURCES = [os.path.join(PROJECT, "wp-local"), os.path.join(PROJECT, "ftp-content")]
# Only passive file types are copied (never php/html/js/swf/svg from the compromised host).
COPY_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".pdf", ".rtf", ".txt", ".java"}
DROP_CATEGORIES = {"podcast"}  # podcast is dropped (README scope)
MORE = "<!--more-->"


def get_all(endpoint, fields=None):
    items, page = [], 1
    while True:
        url = f"{WP}/wp-json/wp/v2/{endpoint}?per_page=100&page={page}"
        if fields:
            url += "&_fields=" + ",".join(fields)
        with urllib.request.urlopen(url, timeout=120) as r:
            items += json.load(r)
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                return items
        page += 1


# --- content cleanup ------------------------------------------------------------

OLD_PATH = r"/wp-content/+customers/webs/\d+/www/_subdomains/volkersfreunde/wp-content/"


def clean(body):
    # Same spam patterns as vf-local-cleanup.php — defensive, should already be gone.
    body = re.sub(r"<!--maincontentstarts-->.*?<!--maincontentends-->", "", body, flags=re.S)
    body = re.sub(r'<style>#fredi3\{.*?</style>\s*<div id="fredi3">.*?</div>\s*</div>', "", body, flags=re.S)
    # Old server file paths stored directly in post bodies.
    body = re.sub(r"(?:https?://localhost:8080)?" + OLD_PATH, "/wp-content/", body)
    # Local WordPress URL -> site-relative.
    body = re.sub(r"https?://localhost:8080(?=/)", "", body)
    body = re.sub(r"https?://localhost:8080\b", "/", body)
    # podPress audio player (podcast dropped): Flash player, its script and the mp3 icon link.
    body = re.sub(r'<div class="podPress_content">.*?</object></div>\s*', "", body, flags=re.S)
    body = re.sub(r"<p><script[^>]*>\s*<!--\s*podPressShowHidePlayer.*?</script></p>\s*", "", body, flags=re.S)
    body = re.sub(r'<a href="[^"]*podpress_trac[^"]*"[^>]*><img[^>]*podPress_imgicon[^>]*/?></a>\s*', "", body)
    body = re.sub(r'<a href="[^"]*podpress_trac[^"]*"[^>]*>Download</a>', "", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip() + "\n"


# --- <!--more--> ------------------------------------------------------------------
# WordPress keeps the author's <!--more--> comment in the rendered HTML, but after
# wpautop it often sits inside a paragraph ("…Satz.<!--more--></p>"). Jekyll cuts the
# home-page teaser at the marker, so the elements still open there are closed before
# the marker and reopened after it; the teaser stays balanced HTML.

def alnum_count(text):
    return sum(1 for ch in text if ch.isalnum())


VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
# Opening one of these implicitly closes an open <p> (HTML parsing rules).
CLOSES_P = {"address", "article", "aside", "blockquote", "div", "dl", "fieldset", "figure", "footer", "form",
            "h1", "h2", "h3", "h4", "h5", "h6", "header", "hr", "ol", "p", "pre", "section", "table", "ul"}


class BlockEnds(HTMLParser):
    """Records (offset, alnum-so-far, open-tag stack) after every end tag."""

    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.text = text
        self.lines = [0]
        for line in text.splitlines(keepends=True):
            self.lines.append(self.lines[-1] + len(line))
        self.stack, self.count, self.ends = [], 0, []
        self.feed(text)
        self.close()

    def _offset(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if tag in CLOSES_P and self.stack and self.stack[-1][0] == "p":
            self.stack.pop()
        if tag == "li" and self.stack and self.stack[-1][0] == "li":
            self.stack.pop()
        if tag not in VOID:
            self.stack.append((tag, self.get_starttag_text()))

    def handle_endtag(self, tag):
        if tag in VOID or not any(t == tag for t, _ in self.stack):
            return
        while self.stack and self.stack.pop()[0] != tag:
            pass
        end = self.text.index(">", self._offset()) + 1
        self.ends.append((end, self.count, list(self.stack)))

    def handle_data(self, data):
        self.count += alnum_count(data)


def normalize_more(body):
    m = re.search(r"<!--more.*?-->", body)
    if not m:
        return body, False
    before, after = body[:m.start()], re.sub(r"<!--more.*?-->", "", body[m.end():])
    if not re.sub(r"<[^>]+>|\s|&nbsp;", "", after):
        return before + after, False  # nothing after the marker — no teaser needed
    open_at_marker = BlockEnds(before).stack
    # End tags right after the marker close reopened elements — don't reopen those at all.
    stack = list(open_at_marker)
    while True:
        m_end = re.match(r"\s*</([a-zA-Z0-9]+)\s*>", after)
        if not m_end or not any(t == m_end.group(1).lower() for t, _ in stack):
            break
        while stack.pop()[0] != m_end.group(1).lower():
            pass
        after = after[m_end.end():]
    close = "".join(f"</{t}>" for t, _ in reversed(open_at_marker))
    reopen = "".join(start for _, start in stack)
    body = before + close + "\n" + MORE + "\n" + reopen + after
    body = re.sub(r"<p>\s*</p>\s*", "", body)  # empty paragraphs left around the marker
    return body, True


# --- files ------------------------------------------------------------------------

def find_source(rel):
    """Locate a referenced file; tolerate case differences (old host was case-insensitive)."""
    for base in FILE_SOURCES:
        path = os.path.join(base, rel.lstrip("/"))
        if os.path.isfile(path):
            return path
        if "/uploads/" in path and not os.path.isfile(path):
            alt = path.replace("/wp-content/uploads/", "/wp-content/")  # old-style upload path
            if os.path.isfile(alt):
                return alt
        parent, name = os.path.split(path)
        if os.path.isdir(parent):
            for cand in os.listdir(parent):
                if cand.lower() == name.lower() and os.path.isfile(os.path.join(parent, cand)):
                    return os.path.join(parent, cand)
    return None


def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)  # JSON strings are valid YAML scalars


def main():
    posts = get_all("posts")
    cats = {c["id"]: html.unescape(c["name"]) for c in get_all("categories", ["id", "name"])}
    tags = {t["id"]: html.unescape(t["name"]) for t in get_all("tags", ["id", "name"])}
    users = {u["id"]: u["name"] for u in get_all("users", ["id", "name"])}

    posts_dir = os.path.join(SITE, "_posts")
    for name in os.listdir(posts_dir):
        if name.endswith((".html", ".md")):
            os.remove(os.path.join(posts_dir, name))
    for d in ("wp-content", "downloads"):
        shutil.rmtree(os.path.join(SITE, d), ignore_errors=True)

    refs, report = {}, {"posts": 0, "teasers": 0, "missing_files": {},
                        "skipped_file_types": {}, "copied_files": 0}
    for p in posts:
        body = clean(p["content"]["rendered"])
        body, has_teaser = normalize_more(body)
        report["teasers"] += has_teaser

        for m in re.finditer(r'(?:src|href)="(/(?:wp-content|downloads)/[^"#?]+)', body):
            refs.setdefault(unquote(m.group(1)), set()).add(p["slug"])

        permalink = re.sub(r"^https?://[^/]+", "", p["link"])
        categories = [cats[c] for c in p["categories"] if c in cats and cats[c] not in DROP_CATEGORIES]
        front = [
            "---",
            f"title: {yaml_str(html.unescape(p['title']['rendered']))}",
            f"date: {p['date_gmt'].replace('T', ' ')} +0000",
            f"permalink: {permalink}",
            f"author: {yaml_str(users.get(p['author'], ''))}",
            f"categories: {yaml_str(categories)}",
            f"tags: {yaml_str([tags[t] for t in p['tags'] if t in tags])}",
            f"wp_id: {p['id']}",
            "---",
        ]
        fname = f"{p['date'][:10]}-{p['slug']}.html"
        with open(os.path.join(posts_dir, fname), "w", encoding="utf-8") as f:
            f.write("\n".join(front) + "\n" + body)
        report["posts"] += 1

    for rel, used_by in sorted(refs.items()):
        ext = os.path.splitext(rel)[1].lower()
        if ext not in COPY_EXTS:
            report["skipped_file_types"][rel] = sorted(used_by)
            continue
        src = find_source(rel)
        if not src:
            report["missing_files"][rel] = sorted(used_by)
            continue
        dest = os.path.join(SITE, rel.lstrip("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        report["copied_files"] += 1

    with open(os.path.join(SITE, "_migration", "export-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"posts: {report['posts']}  teasers: {report['teasers']}  files: {report['copied_files']} copied, "
          f"{len(report['missing_files'])} missing, {len(report['skipped_file_types'])} skipped (type)")


if __name__ == "__main__":
    sys.exit(main())
