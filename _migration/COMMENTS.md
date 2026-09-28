# Old WordPress comments → Jekyll (read-only)

The site shows the blog's old comments under each post, frozen as they were. There is no
comment form: the blog is an archive.

| Piece | What |
|---|---|
| `_migration/export_comments.py` | Exporter: WordPress (via WP-CLI) → `_data/comments.json` |
| `_data/comments.json` | `{"<wp_id>": {"count": N, "comments": [ … ]}}`, replies nested in `replies` |
| `_includes/comments.html` | `comments.php` port: heading + `<ol class="commentlist">` |
| `_includes/comment.html` | One comment in `wp_list_comments()` markup; recursive for replies |
| `_layouts/post.html` | `{% include comments.html %}` after the tags (as in `single.php`) |
| `_layouts/home.html` | "N Kommentare" link per post (only when it has comments) |
| `assets/css/style.css` | `/* ===== COMMENTS ===== */` from the theme + `comment*.png` |
| `_migration/comments-report.json` | Counts, comments of posts not in the site, spam suspects |

volkersfreunde: 394 approved comments on 163 posts (365 comments, 21 pingbacks,
8 trackbacks, 2007–2012, 2 threaded replies). No spam among them (Akismet had kept it out).

## Run it

Needs the Docker stack from the project root (`docker compose up -d`). From `site/`:

```sh
python3 _migration/export_comments.py
bundle exec jekyll build
```

Re-running replaces `_data/comments.json`. The post exporter (`export_rest.py`) doesn't
touch comments, so the two can run in any order.

## Why it works like this

- **WP-CLI, not the REST API.** Anonymous REST calls only return `type=comment`;
  pingbacks/trackbacks give 401. `wp eval-file -` runs a small PHP snippet inside the
  **clean** local WordPress (never the old, hacked install), with no credentials needed.
- **WordPress renders the text.** The snippet passes each comment through the
  `comment_text` filters, so paragraphs, typography, clickable links and
  `rel="nofollow ugc"` are exactly what the blog showed. Umlauts are right because WP-CLI
  uses the same latin1 DB connection as the local WordPress.
- **Matched by `wp_id`**, not by URL or slug. It survives permalink changes, and every
  post the exporter writes has it.
- **Privacy:** only name, website, date and text are exported, which is what the blog
  showed publicly. No e-mail, no IP, no avatars (Gravatar URLs are e-mail hashes and would
  load a third-party service).
- **Dates** keep the blog's own local time and offset (`date` vs. `date_gmt`).
- Links to the local WordPress (`localhost:8080`) and to the old domain become
  site-relative (so internal pingbacks point to the Jekyll pages). Smiley images from
  s.w.org become their emoji. Author "URLs" that aren't URLs (`---`, free text) are dropped.
- Post bodies use `render_with_liquid: false`. Comment text comes from `_data`, and Liquid
  never parses data output, so `{{ }}` in comments is safe too.

## Reuse it for another blog (e.g. madrid.falkorichter.de)

Prerequisites: the other blog runs locally in the same pattern (clean WordPress + WP-CLI
service in `docker-compose.yml`), and its Jekyll posts have `wp_id:` in their front matter.

1. Copy `_migration/export_comments.py` into the new site's `_migration/`.
2. Run it with that blog's WP-CLI service, local URL and old domain:
   ```sh
   python3 _migration/export_comments.py \
     --wp-cli "docker compose run --rm -T madrid-cli" \
     --local-url http://localhost:8090 --old-host madrid.falkorichter.de
   ```
   It finds `docker-compose.yml` by walking up from the site folder (override with
   `WP_PROJECT_DIR`). Not Docker? Pass any WP-CLI command, e.g. `--wp-cli "wp --path=/srv/wp"`.
3. Check `_migration/comments-report.json`:
   - `spam_suspects`: keyword/hidden-style hits. Drop real spam with `--exclude 123,456`
     (or delete it in the local WordPress first).
   - `not_in_site`: comments on pages/drafts/posts that weren't exported.
     Expected if you skipped those.
4. Copy `_includes/comments.html` + `_includes/comment.html`, add
   `{% include comments.html %}` to the post layout, and adapt the texts
   (German: "sagt:", "um", `site.months_de`; English themes: "says:", "at") and the CSS to
   that theme's `comments.php` / `style.css`. The data format stays the same.
5. Optional: the per-post counter from `_layouts/home.html`
   (`site.data.comments[post.wp_id | append: ""].count`).

Liquid gotcha: in the recursive `comment.html`, only use `include.comment` / `include.depth`.
A plain `assign` is page-global and a caller's `for c in …` shadows it, which recurses forever
("Nesting too deep").

Offline/debugging: `--dump-json raw.json` saves the WP-CLI dump; `--from-json raw.json`
re-runs the conversion without WordPress.
