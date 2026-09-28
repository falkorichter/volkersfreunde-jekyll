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
| `_posts/` | 401 posts, original URLs `/<slug>/` |
| `_pages/` | Impressum, Kontakt, RSS (the old nav) and the year archive `/archiv/` |
| `assets/images/YYYY/MM/`, `assets/files/YYYY/MM/` | images and documents used by the posts |
| `assets/images/theme/` | theme graphics |
| `assets/js/lightbox.js` | lightbox for post images and galleries (counter, ←/→, swipe, Esc) |
| `_data/{categories,tags}.yml` | display name → original slug, keeps `/category/…` and `/tag/…` URLs |
| `_plugins/taxonomy_pages.rb` | generates the category/tag archive pages |
| `_plugins/baseurl_links.rb` | prefixes root links in post bodies when built under a sub-path |
| `feed-redirect.html` | `/feed/` (the old WordPress feed URL) forwards to `/feed.xml` |
| `_migration/export_rest.py` | the exporter (see below) |

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

## GitHub Pages

Built by `.github/workflows/pages.yml` on every push to `main` (repo setting *Pages → Source:
GitHub Actions*): it runs the custom `_plugins/` and passes the Pages address as `url`/`baseurl`.
`_config.yml` keeps `url: https://www.volkersfreunde.de` and `baseurl: ""` for the real domain.

## Dropped on purpose
Comments, the podcast (podPress/Podlove players, the `podcast` category), all WordPress plugins,
the Meta/Admin, FireStats and App.net widgets, and Google Analytics.
