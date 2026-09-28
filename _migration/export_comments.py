#!/usr/bin/env python3
"""
Export the approved comments (incl. pingbacks/trackbacks) of a local WordPress into this
Jekyll site, so they can be shown read-only under the posts.

Blog-agnostic on purpose: it only needs a WP-CLI that can reach the old database, and
posts in _posts/ that carry `wp_id:` in their front matter (the post exporter writes it).
See _migration/COMMENTS.md for how to reuse it for another blog.

Source: WP-CLI runs a tiny PHP snippet inside the *clean* local WordPress (never the old,
untrusted install). The comment text goes through WordPress' own `comment_text` filters
(paragraphs, typography, clickable links with rel="nofollow ugc"), so it looks exactly
like it did on the blog. The REST API is not used: it hides pingbacks/trackbacks from
anonymous clients. E-mail addresses and IPs are never exported.

Writes (and replaces on every run):
  _data/comments.json                 {"<wp_id>": {"count": N, "comments": [ … ]}}
  _migration/comments-report.json     counts, skipped comments, spam suspects

Usage (from the site/ folder, Docker stack running):
  python3 _migration/export_comments.py
  python3 _migration/export_comments.py --wp-cli "docker compose run --rm -T madrid-cli" \
      --old-host madrid.falkorichter.de
  python3 _migration/export_comments.py --from-json dump.json   # offline, from --dump-json
"""
import argparse
import html
import json
import os
import re
import shlex
import subprocess
import sys
from datetime import datetime

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_project(start):
    """Nearest folder above the site that holds the docker compose file."""
    d = start
    while True:
        if any(os.path.isfile(os.path.join(d, n)) for n in
               ("docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml")):
            return d
        if os.path.dirname(d) == d:
            return os.path.dirname(start)
        d = os.path.dirname(d)


PROJECT = os.environ.get("WP_PROJECT_DIR") or find_project(SITE)  # where WP-CLI is run

# Runs inside WordPress via `wp eval-file -`. Prints one JSON array.
DUMP_PHP = r"""<?php
$out = [];
$comments = get_comments(['status' => 'approve', 'type' => '', 'number' => 0,
                          'orderby' => 'comment_date_gmt', 'order' => 'ASC']);
foreach ($comments as $c) {
    $out[] = [
        'id'          => (int) $c->comment_ID,
        'post_id'     => (int) $c->comment_post_ID,
        'post_status' => get_post_status($c->comment_post_ID),
        'post_type'   => get_post_type($c->comment_post_ID),
        'parent'      => (int) $c->comment_parent,
        'type'        => $c->comment_type ?: 'comment',
        'author'      => $c->comment_author,
        'author_url'  => $c->comment_author_url,
        'user_id'     => (int) $c->user_id,
        'date'        => $c->comment_date,
        'date_gmt'    => $c->comment_date_gmt,
        'content'     => apply_filters('comment_text', get_comment_text($c), $c, []),
    ];
}
echo wp_json_encode($out);
"""

# Things that should never show up in a kept comment. Only reported, not dropped:
# review the report and pass --exclude for real spam.
SPAM_RE = re.compile(
    r"viagra|cialis|levitra|casino|poker|payday|loan|insurance|replica|porn|xxx|"
    r"position\s*:\s*absolute|top\s*:\s*-\d{3,}px|display\s*:\s*none", re.I)


def dump_via_wp_cli(cmd):
    res = subprocess.run(shlex.split(cmd) + ["eval-file", "-"], input=DUMP_PHP, cwd=PROJECT,
                         capture_output=True, text=True)
    if res.returncode != 0:
        sys.exit(f"WP-CLI failed ({cmd}):\n{res.stderr}")
    # docker compose may print status lines on stdout before the JSON
    return json.loads(res.stdout[res.stdout.index("["):])


def site_posts():
    """wp_id -> post file name, for every post in _posts/."""
    posts = {}
    posts_dir = os.path.join(SITE, "_posts")
    for name in sorted(os.listdir(posts_dir)):
        with open(os.path.join(posts_dir, name), encoding="utf-8") as f:
            head = f.read(4096)
        m = re.search(r"^wp_id:\s*(\d+)\s*$", head, re.M)
        if m:
            posts[int(m.group(1))] = name
    return posts


def iso_local(date, date_gmt):
    """'2012-12-05 13:36:08' + GMT '2012-12-05 12:36:08' -> '2012-12-05T13:36:08+01:00'."""
    local = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    if not date_gmt or date_gmt.startswith("0000"):
        return local.isoformat()
    minutes = round((local - datetime.strptime(date_gmt, "%Y-%m-%d %H:%M:%S")).total_seconds() / 60)
    sign = "+" if minutes >= 0 else "-"
    return f"{local.isoformat()}{sign}{abs(minutes) // 60:02d}:{abs(minutes) % 60:02d}"


def make_cleaner(local_urls, old_hosts):
    """Links to the local WordPress or the old domain(s) -> site-relative."""
    hosts = "|".join(re.escape(h) for h in old_hosts)
    patterns = [re.compile(re.escape(u.rstrip("/")) + r"(?=/|[\"'\s<]|$)") for u in local_urls]
    if hosts:
        patterns.append(re.compile(r"https?://(?:www\.)?(?:" + hosts + r")(?=/|[\"'\s<]|$)", re.I))

    def relative(text):
        for p in patterns:
            text = p.sub("", text)
        return re.sub(r"""(href=["'])(?=["'])""", r"\1/", text)  # bare host -> "/"

    def clean_content(body):
        # Smilies: WordPress turns ":-)" into an <img> from s.w.org; keep the emoji (alt) only.
        body = re.sub(r"<img[^>]*class=\"wp-smiley\"[^>]*alt=\"([^\"]*)\"[^>]*/?>", r"\1", body)
        body = re.sub(r"<img[^>]*alt=\"([^\"]*)\"[^>]*class=\"wp-smiley\"[^>]*/?>", r"\1", body)
        return relative(body).strip() + "\n"

    def clean_url(url):
        url = (url or "").strip()
        if not re.match(r"https?://[\w-]+(\.[\w-]+)+", url, re.I):
            if not re.fullmatch(r"[\w-]+(\.[\w-]+)*\.[a-z]{2,}(/\S*)?", url, re.I):
                return ""  # "", "http://", "---", free text people typed into the URL field
            url = "http://" + url
        return relative(f'href="{url}"')[6:-1]

    return clean_content, clean_url


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--wp-cli", default=os.environ.get("WP_CLI", "docker compose run --rm -T wpcli"),
                    help="command that runs WP-CLI against the local WordPress (run in %s)" % PROJECT)
    ap.add_argument("--local-url", action="append", default=None,
                    help="URL of the local WordPress, made relative (default: http://localhost:8080)")
    ap.add_argument("--old-host", action="append", default=None,
                    help="old domain(s) whose links become site-relative (default: volkersfreunde.de)")
    ap.add_argument("--exclude", default="", help="comma-separated comment IDs to drop (spam)")
    ap.add_argument("--from-json", help="read a dump written by --dump-json instead of calling WP-CLI")
    ap.add_argument("--dump-json", help="also save the raw WP-CLI dump here")
    args = ap.parse_args()
    local_urls = args.local_url or ["http://localhost:8080", "https://localhost:8080"]
    old_hosts = args.old_host or ["volkersfreunde.de"]
    exclude = {int(x) for x in args.exclude.split(",") if x.strip()}

    if args.from_json:
        with open(args.from_json, encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = dump_via_wp_cli(args.wp_cli)
        if args.dump_json:
            with open(args.dump_json, "w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False, indent=1)

    posts = site_posts()
    clean_content, clean_url = make_cleaner(local_urls, old_hosts)
    report = {"comments_in_wordpress": len(raw), "exported": 0, "posts_with_comments": 0,
              "by_type": {}, "excluded": sorted(exclude), "not_in_site": [], "spam_suspects": []}

    # Keep comments of posts that exist in the site; build the reply tree.
    kept = {}
    for c in raw:
        if c["id"] in exclude:
            continue
        if c["post_id"] not in posts:
            report["not_in_site"].append({k: c[k] for k in ("id", "post_id", "post_type", "post_status", "type", "author")})
            continue
        item = {
            "id": c["id"],
            "type": c["type"],
            "author": html.unescape(c["author"]).strip() or "Anonym",
            "author_url": clean_url(c["author_url"]),
            "by_user": c["user_id"] > 0,
            "date": iso_local(c["date"], c["date_gmt"]),
            "content": clean_content(c["content"]),
            "replies": [],
        }
        if SPAM_RE.search(item["content"] + " " + item["author_url"]):
            report["spam_suspects"].append({"id": c["id"], "post": posts[c["post_id"]], "author": item["author"]})
        kept[c["id"]] = (c, item)

    data = {}
    for cid, (c, item) in kept.items():  # raw is in date order, so replies follow their parent
        parent = kept.get(c["parent"])
        if parent and parent[0]["post_id"] == c["post_id"]:
            parent[1]["replies"].append(item)
        else:
            data.setdefault(str(c["post_id"]), {"count": 0, "comments": []})["comments"].append(item)
        data.setdefault(str(c["post_id"]), {"count": 0, "comments": []})["count"] += 1
        report["by_type"][item["type"]] = report["by_type"].get(item["type"], 0) + 1
        report["exported"] += 1
    report["posts_with_comments"] = len(data)

    data = dict(sorted(data.items(), key=lambda kv: int(kv[0])))
    with open(os.path.join(SITE, "_data", "comments.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(os.path.join(SITE, "_migration", "comments-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"comments: {report['exported']} exported on {report['posts_with_comments']} posts "
          f"{report['by_type']}; {len(report['not_in_site'])} not in site, "
          f"{len(exclude)} excluded, {len(report['spam_suspects'])} spam suspects "
          f"(see _migration/comments-report.json)")


if __name__ == "__main__":
    main()
