#!/usr/bin/env python3
"""
Export the blog posts from the local WordPress (docker compose, http://localhost:8080)
into this Jekyll site.

Source: the WordPress REST API. Its `content.rendered` is what WordPress itself shows:
umlauts decoded correctly, paragraphs/typography applied, shortcodes gone, and spam +
old-host URLs already cleaned by wp-local/.../mu-plugins/vf-local-cleanup.php.

Writes (and replaces on every run):
  _posts/YYYY-MM-DD-<slug>.md|.html   one file per published post: Markdown if html2md.py can
                                      convert it and it renders back identically, else HTML
  assets/images/YYYY/MM/…             images the posts reference (year/month of the old
  assets/files/YYYY/MM/…              upload path, else of the first post using them)
  _data/categories.yml, _data/tags.yml   display name -> slug of the terms the posts use
  _data/comments.json                 approved comments, shown read-only under the posts
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
from urllib.parse import quote, unquote

import html2md  # conservative HTML -> Markdown, only used when it renders back identically

WP = os.environ.get("WP_URL", "http://localhost:8080")
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(SITE)
# Where referenced files are copied from, in order. wp-local/ is the content-checked copy.
FILE_SOURCES = [os.path.join(PROJECT, "wp-local"), os.path.join(PROJECT, "ftp-content")]
# Only passive file types are copied (never php/html/js/swf/svg from the compromised host).
COPY_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".pdf", ".rtf", ".txt", ".java"}
DROP_CATEGORIES = {"podcast"}  # podcast is dropped (README scope)
MORE = "<!--more-->"


def get_all(endpoint, fields=None, extra=""):
    items, page = [], 1
    while True:
        url = f"{WP}/wp-json/wp/v2/{endpoint}?per_page=100&page={page}{extra}"
        if fields:
            url += "&_fields=" + ",".join(fields)
        with urllib.request.urlopen(url, timeout=120) as r:
            items += json.load(r)
            if page >= int(r.headers.get("X-WP-TotalPages", 1)):
                return items
        page += 1


# --- content cleanup ------------------------------------------------------------

OLD_PATH = r"/wp-content/+customers/webs/\d+/www/_subdomains/volkersfreunde/wp-content/"


def embed_iframe(m):
    """Flash <object>/<embed> players -> iframes (YouTube, Vimeo), keeping the size.
    Other Flash players (issuu, blip.tv, TED, Megavideo, …) can't play anywhere any more and
    would show an empty box: they become a short note, linked to the source if the embed names one."""
    obj = m.group(0)
    w = re.search(r'width[:=]"?(\d+)', obj)
    h = re.search(r'height[:=]"?(\d+)', obj)
    size = f' width="{w.group(1) if w else 425}" height="{h.group(1) if h else 344}"'
    yt = re.search(r"youtube\.com/v/([\w-]{11})", obj)
    vimeo = re.search(r"clip_id=(\d+)", obj)
    if yt:
        return f'<iframe{size} src="https://www.youtube-nocookie.com/embed/{yt.group(1)}" frameborder="0" loading="lazy" allowfullscreen></iframe>'
    if vimeo:
        return f'<iframe{size} src="https://player.vimeo.com/video/{vimeo.group(1)}" frameborder="0" loading="lazy" allowfullscreen></iframe>'
    source = re.search(r"blog_domain=(https?://[^&\"]+)", obj)
    link = f'<br /><a href="{html.escape(source.group(1))}">Zum Originalbeitrag</a>' if source else ""
    return f'<span class="embed-gone">Flash-Video (nicht mehr abspielbar){link}</span>'


def clean(body):
    # Same spam patterns as vf-local-cleanup.php — defensive, should already be gone.
    body = re.sub(r"<!--maincontentstarts-->.*?<!--maincontentends-->", "", body, flags=re.S)
    body = re.sub(r'<style>#fredi3\{.*?</style>\s*<div id="fredi3">.*?</div>\s*</div>', "", body, flags=re.S)
    # Old server file paths stored directly in post bodies.
    body = re.sub(r"(?:https?://localhost:8080)?" + OLD_PATH, "/wp-content/", body)
    # Relative (../wp-content/…) and the old shared-hosting URL of the same folder.
    body = re.sub(r"""(?<=["'])(?:\.\./)+wp-content/""", "/wp-content/", body)
    body = re.sub(r"https?://(?:www\.)?falkorichter\.de/+_subdomains/volkersfreunde/wp-content/", "/wp-content/", body)
    # Other relative links ("../other-post/") were written for a post at /<slug>/.
    body = re.sub(r"""(href=["'])(?:\.\./)+""", r"\1/", body)
    # Local WordPress URL -> site-relative.
    body = re.sub(r"https?://localhost:8080(?=/)", "", body)
    body = re.sub(r"https?://localhost:8080\b", "/", body)
    # podPress audio player (podcast dropped): Flash player, its script and the mp3 icon link.
    body = re.sub(r'<div class="podPress_content">.*?</object></div>\s*', "", body, flags=re.S)
    body = re.sub(r"<p><script[^>]*>\s*<!--\s*podPressShowHidePlayer.*?</script></p>\s*", "", body, flags=re.S)
    body = re.sub(r'<a href="[^"]*podpress_trac[^"]*"[^>]*><img[^>]*podPress_imgicon[^>]*/?></a>\s*', "", body)
    body = re.sub(r'<a href="[^"]*podpress_trac[^"]*"[^>]*>Download</a>', "", body)
    # Flash players -> iframes (or a note), see embed_iframe().
    body = re.sub(r"<object.*?</object>", embed_iframe, body, flags=re.S)
    body = re.sub(r"<embed[^>]*(?:\.swf|youtube\.com/v/)[^>]*>(?:</embed>)?", embed_iframe, body)
    # Embeds over https (http iframes are blocked as mixed content on an https site).
    body = re.sub(r'(<iframe[^>]*src=")http://', r"\1https://", body)
    # External scripts over plain http are blocked on an https site (and these services are
    # gone: Yahoo Pipes, an Ubuntu countdown). https ones (Gist, Twitter, Podigee) stay.
    body = re.sub(r'<script[^>]*src="http://[^"]*"[^>]*>.*?</script>', "", body, flags=re.S)
    # Links written without a scheme ("www.example.com/…") resolve as paths on this site.
    body = re.sub(r"""(href=["'])(www\.)""", r"\1http://\2", body)
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
        encoded = os.path.join(os.path.dirname(path), quote(os.path.basename(path)))
        if not os.path.isfile(path) and os.path.isfile(encoded):
            return encoded  # some uploads were saved with a literal "%20" in the name
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


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
REF_RE = re.compile(r"""((?:src|href)=(["']))(/(?:wp-content|downloads)/[^"'#?]+)""")


def new_location(rel, first_used):
    """/wp-content/2008/10/foo.jpg -> /assets/images/2008/10/foo.jpg.
    Files without a year/month in their old path get the date of the first post using them."""
    ext = os.path.splitext(rel)[1].lower()
    kind = "images" if ext in IMAGE_EXTS else "files"
    m = re.search(r"/(\d{4})/(\d{2})/", rel)
    year, month = m.groups() if m else (first_used[:4], first_used[5:7])
    name = re.sub(r"(?:%20|\s)+", "-", os.path.basename(rel))
    return f"/assets/{kind}/{year}/{month}/{name}"


RESIZED_RE = re.compile(r"^(.+?)(?:-\d+x\d+|\.thumbnail)(\.\w+)$")  # foo-480x336.png, foo.thumbnail.jpg


def original_of(path):
    """Full-size file for a WordPress preview: foo-480x336.png, foo.thumbnail.jpg,
    wpid-thumb-1431.jpg (WordPress for Android) -> foo.png, foo.jpg, wpid-1431.jpg."""
    candidates = []
    r = RESIZED_RE.match(path)
    if r:
        candidates.append(r.group(1) + r.group(2))
    base = candidates[0] if candidates else path
    if "/wpid-thumb-" in base:
        candidates.insert(0, base.replace("/wpid-thumb-", "/wpid-"))
    return next((c for c in candidates if find_source(c)), None)
IMG_RE = re.compile(r"""<img[^>]*\ssrc=["'](/wp-content/[^"']+)["'][^>]*>""")


def link_previews(body):
    """Wrap unlinked resized previews in a link to the original, so the lightbox can open it."""
    def wrap(m):
        start = m.start()
        if body.rfind("<a ", 0, start) > body.rfind("</a>", 0, start):
            return m.group(0)  # already inside a link
        original = original_of(unquote(m.group(1)))
        if not original:
            return m.group(0)
        return f'<a href="{quote(original)}">{m.group(0)}</a>'
    return IMG_RE.sub(wrap, body)


def author_url(url):
    """Comment author website; drop what people typed that is no URL ("http://---")."""
    return url if url and re.match(r"https?://[\w-]+(\.[\w-]+)+", url) else ""


def main():
    posts = get_all("posts")
    cat_terms = get_all("categories", ["id", "name", "slug"])
    tag_terms = get_all("tags", ["id", "name", "slug"])
    cats = {c["id"]: html.unescape(c["name"]) for c in cat_terms}
    tags = {t["id"]: html.unescape(t["name"]) for t in tag_terms}
    users = {u["id"]: u["name"] for u in get_all("users", ["id", "name"])}
    comments = get_all("comments", extra="&order=asc")
    # WordPress attachment pages (/<post>/<image>/) -> the image file itself
    attachments = {re.sub(r"^https?://[^/]+", "", a["link"]): clean(a["source_url"]).strip()
                   for a in get_all("media", ["link", "source_url"])}

    posts_dir = os.path.join(SITE, "_posts")
    for name in os.listdir(posts_dir):
        if name.endswith((".html", ".md")):
            os.remove(os.path.join(posts_dir, name))
    for d in ("wp-content", "downloads", "assets/images/uploads", "assets/files"):
        shutil.rmtree(os.path.join(SITE, d), ignore_errors=True)
    for year_dir in os.listdir(os.path.join(SITE, "assets", "images")):
        if re.fullmatch(r"\d{4}", year_dir):  # previous run's output; theme/ stays
            shutil.rmtree(os.path.join(SITE, "assets", "images", year_dir))

    report = {"posts": 0, "teasers": 0, "missing_files": {}, "skipped_file_types": {}, "copied_files": 0}

    # Pass 1: clean the bodies, collect referenced files (with the date of the first post using them).
    entries, refs = [], {}
    for p in sorted(posts, key=lambda p: p["date_gmt"]):
        body = clean(p["content"]["rendered"])
        body, has_teaser = normalize_more(body)
        report["teasers"] += has_teaser
        body = re.sub(r"""(href=["'])(/[^"'#?]+/)(?=["'])""",
                      lambda m: m.group(1) + attachments.get(m.group(2), m.group(2)), body)
        body = link_previews(body)
        for m in REF_RE.finditer(body):
            refs.setdefault(unquote(m.group(3)), {"first_used": p["date"], "used_by": set()})["used_by"].add(p["slug"])
        entries.append((p, body))

    # Pass 2: copy files to assets/{images,files}/YYYY/MM/ and remember old -> new.
    moved, taken = {}, {}
    for rel, info in sorted(refs.items()):
        used_by = sorted(info["used_by"])
        if os.path.splitext(rel)[1].lower() not in COPY_EXTS:
            report["skipped_file_types"][rel] = used_by
            continue
        src = find_source(rel)
        if not src:
            report["missing_files"][rel] = used_by
            continue
        new = new_location(rel, info["first_used"])
        stem, ext = os.path.splitext(new)
        n = 2
        while taken.get(new.lower(), src) != src:  # same name, different file -> suffix
            new, n = f"{stem}-{n}{ext}", n + 1
        taken[new.lower()] = src
        dest = os.path.join(SITE, new.lstrip("/"))
        if not os.path.exists(dest):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            report["copied_files"] += 1
        moved[rel] = new

    # Pass 3: rewrite links and write the posts.
    def relink(m):
        new = moved.get(unquote(m.group(3)))
        return m.group(1) + quote(new) if new else m.group(0)

    # Internal pages that exist on the new site; links to anything else lose their <a>
    # (e.g. a category that was deleted in 2008, a page that was never published).
    permalinks = {re.sub(r"^https?://[^/]+", "", p["link"]) for p in posts}
    used_cats = {c for p in posts for c in p["categories"] if cats.get(c) not in DROP_CATEGORIES}
    used_tags = {t for p in posts for t in p["tags"]}
    known = (permalinks
             | {f"/category/{c['slug']}/" for c in cat_terms if c["id"] in used_cats}
             | {f"/tag/{t['slug']}/" for t in tag_terms if t["id"] in used_tags}
             | {f"/page/{n}/" for n in range(2, len(posts) // 15 + 2)}
             | {f"/{name}/" for name in ("impressum", "kontakt", "rss-2", "archiv", "feed")}
             | {"/", "/feed.xml"})
    internal_link = re.compile(r"""<a([^>]*)\shref=["'](/(?!assets/)[^"'#?]*)(?:[#?][^"']*)?["']([^>]*)>(.*?)</a>""", re.S)

    def unwrap_unknown(m):
        path = unquote(m.group(2))
        if path in known or path.rstrip("/") + "/" in known:
            return m.group(0)
        report["dead_links_unwrapped"] += 1
        return m.group(4)

    dead_img = re.compile(r"""<img[^>]*\ssrc=["']/(?:wp-content|downloads)/[^>]*>""")
    dead_link = re.compile(r"""<a[^>]*\shref=["']/(?:wp-content/|downloads/|wp-admin/|wp-login\.php)[^>]*>(.*?)</a>""", re.S)
    report["dead_links_unwrapped"] = report["dead_images_removed"] = 0
    outputs = []
    for p, body in entries:
        body = REF_RE.sub(relink, body)
        # Whatever still points at WordPress paths never existed / only worked with WordPress:
        # keep the link text, drop images without a file.
        body, n = dead_img.subn("", body)
        report["dead_images_removed"] += n
        body, n = dead_link.subn(r"\1", body)
        report["dead_links_unwrapped"] += n
        body = internal_link.sub(unwrap_unknown, body)
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
        outputs.append((f"{p['date'][:10]}-{p['slug']}", "\n".join(front) + "\n", body))
        report["posts"] += 1

    # Simple posts become Markdown, but only if the Markdown renders back to the same HTML.
    markdown = html2md.convert_verified({name: body for name, _, body in outputs})
    for name, front, body in outputs:
        ext, text = (".md", markdown[name]) if name in markdown else (".html", body)
        with open(os.path.join(posts_dir, name + ext), "w", encoding="utf-8") as f:
            f.write(front + text)
    report["markdown_posts"] = len(markdown)

    # Sidebar/taxonomy data: display name -> original slug, only for terms the posts use.
    # Jekyll groups tags by name, so a name has one page; where the old blog had two terms with
    # the same name (tag "IMI-Showtime": imi-showtime and showtime), the one used more wins.
    def term_data(fname, terms, used, what):
        best = {}
        for t in terms:
            if t["id"] not in used:
                continue
            name = html.unescape(t["name"])
            count = sum(1 for p in posts if t["id"] in p[what])
            if name not in best or count > best[name][1]:
                best[name] = (t["slug"], count)
        with open(os.path.join(SITE, "_data", fname), "w", encoding="utf-8") as f:
            f.write(f"# Generated by _migration/export_rest.py: display name -> original URL slug\n")
            for name in sorted(best, key=str.lower):
                f.write(f"- name: {yaml_str(name)}\n  slug: {yaml_str(best[name][0])}\n")

    term_data("categories.yml", cat_terms, used_cats, "categories")
    term_data("tags.yml", tag_terms, used_tags, "tags")

    # Old comments, shown read-only under the posts.
    post_by_id = {p["id"]: p for p in posts}
    data = []
    for c in comments:
        p = post_by_id.get(c["post"])
        if not p or c["status"] != "approved":
            continue
        data.append({"id": c["id"], "url": re.sub(r"^https?://[^/]+", "", p["link"]),
                     "post_title": html.unescape(p["title"]["rendered"]),
                     "author": html.unescape(c["author_name"]), "author_url": author_url(c.get("author_url")),
                     "date": c["date"].replace("T", " "), "content": clean(c["content"]["rendered"]).strip()})
    with open(os.path.join(SITE, "_data", "comments.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    report["comments"] = len(data)

    with open(os.path.join(SITE, "_migration", "export-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"posts: {report['posts']} ({report['markdown_posts']} as Markdown)  teasers: {report['teasers']}  "
          f"comments: {report['comments']}  files: {report['copied_files']} copied, "
          f"{len(moved)} links moved, {len(report['missing_files'])} missing, "
          f"{len(report['skipped_file_types'])} skipped (type)")


if __name__ == "__main__":
    sys.exit(main())
