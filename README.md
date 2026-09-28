# volkersfreunde — static Jekyll archive

The blog **volkersfreunde.de** ("Computer, Medien und Berliner Kultur", 2007–2025),
converted from WordPress to a static Jekyll site with a port of its theme
*Volkersfreunde 4.0* (`volkersfreunde40`, by Friedrich Maiwald).

Live preview: https://falkorichter.github.io/volkersfreunde-jekyll/

```sh
bundle install
bundle exec jekyll serve      # http://localhost:4000
```

## What's here

| Path | What |
|---|---|
| `_layouts/`, `_includes/`, `assets/css/style.css` | the ported theme (changes marked `port:` in the CSS) |
| `_posts/` | 401 posts (Markdown where possible, see below), original URLs `/<slug>/` |
| `_pages/` | Impressum, Kontakt, RSS (the old nav) and the year archive `/archiv/` |
| `assets/images/YYYY/MM/`, `assets/files/YYYY/MM/` | images and documents used by the posts |
| `assets/images/theme/` | theme graphics |
| `assets/js/lightbox.js` | lightbox for post images and galleries (counter, ←/→, swipe, Esc) |
| `_data/{categories,tags}.yml` | display name → original slug, keeps `/category/…` and `/tag/…` URLs |
| `_plugins/taxonomy_pages.rb` | generates the category/tag archive pages |
| `_plugins/baseurl_links.rb` | prefixes root links in post bodies when built under a sub-path |
| `feed-redirect.html` | `/feed/` (the old WordPress feed URL) forwards to `/feed.xml` |
| `_migration/export_rest.py` | the exporter (see below) |
| `_migration/html2md.py`, `kramdown_render.rb`, `compare_builds.py` | HTML → Markdown conversion and its checks (see [Markdown posts](#markdown-posts)) |

## URLs

Only the **post URLs** are preserved: every post is a folder with an `index.html` at its old
address `/<slug>/`, as are the category (`/category/<slug>/`), tag (`/tag/<slug>/`) and paging
(`/page/N/`) URLs. The site is **static only**: no `.htaccess` or other server rules, `404.html`
is picked up by the host, the feed is `/feed.xml`. Old image URLs (`/wp-content/…`) are
intentionally not redirected.

## Re-running the export

The content comes from the local, cleaned WordPress copy of the blog (docker compose
service `wordpress`, http://localhost:8080, in the parent migration project):

```sh
python3 _migration/export_rest.py    # rewrites _posts/, assets/images/YYYY/, assets/files/
```

It reads the REST API, whose output already has the umlauts decoded and the injected SEO spam
removed (by the local WordPress' cleanup plugin). On top of that it:

- keeps the `<!--more-->` teasers balanced (home page "weiter lesen »"),
- moves every referenced file to `assets/images|files/YYYY/MM/` and rewrites the links,
- links WordPress attachment pages and unlinked previews (`foo-480x336.jpg`, `.thumbnail.jpg`,
  `wpid-thumb-N.jpg`) straight to the original image, for the lightbox,
- converts old Flash YouTube/Vimeo players to iframes; Flash players that can't play anywhere
  any more (issuu, blip.tv, TED, …) become a short note,
- switches embedded iframes to https and repairs links written without `http://`,
- unwraps links to WordPress-only paths (`/wp-login.php`, missing plugin files),

and writes `_migration/export-report.json`.

## Markdown posts

Posts are stored as **Markdown** (`_posts/*.md`) where that is possible *without changing the
page*, and stay **HTML** (`_posts/*.html`) otherwise — currently 181 of 401 posts are
Markdown. Posts with embeds (videos, maps, Flash notes), `<div>`/`<span>` markup, inline styles etc.
stay HTML on purpose.

How it works (`_migration/html2md.py`, used by the exporter):

1. **Convert** only a safe subset of HTML: paragraphs, line breaks, links, bold/italic, inline
   code, headings, lists, quotes, rules and images. Image size and alignment and link targets are
   kept as kramdown attribute lists, e.g. `![Foto](/assets/…/a.jpg){: .alignleft width="300"}`.
   Anything else → the post stays HTML.
2. **Verify**: the Markdown is rendered with Jekyll's own Markdown converter and default
   kramdown settings (`_migration/kramdown_render.rb`) and compared with the original HTML
   (normalized: whitespace, entities and attribute order don't count; `loading`/`decoding`
   and the `wp-block-paragraph` class are ignored). Only an identical result becomes `.md`.

Tools:

```sh
python3 _migration/html2md.py --dry-run          # how many HTML posts would convert
python3 _migration/html2md.py [_posts/x.html …]  # convert in place (x.html -> x.md), verified
python3 _migration/compare_builds.py [REV]       # build REV (default HEAD) and the working
                                                 # tree, compare every generated page
```

`compare_builds.py` exits with 1 if the content of any post or page differs. Switching to
Markdown changed no post content; the only differences were list pages (category/tag archives),
whose short 55-word teasers now end a word or two earlier, and `<meta name="description">`,
which shows `…`/`–` instead of `&#8230;`/`&#8211;` (fixed for HTML posts too).
Needs Ruby with Jekyll (`RBENV_VERSION=3.1.2` locally).

## GitHub Pages

Built by `.github/workflows/pages.yml` on every push to `main` (repo setting *Pages → Source:
GitHub Actions*): it runs the custom `_plugins/` and passes the Pages address as `url`/`baseurl`.
`_config.yml` keeps `url: https://www.volkersfreunde.de` and `baseurl: ""` for the real domain.

## Dropped on purpose
Comments, the podcast (podPress/Podlove players, the `podcast` category), all WordPress plugins,
the Meta/Admin, FireStats and App.net widgets, and Google Analytics.
