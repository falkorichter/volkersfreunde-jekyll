# CLAUDE.md — volkersfreunde.de

Static Jekyll 4 archive of the WordPress blog volkersfreunde.de (2007–2025) with a port of the
theme *Volkersfreunde 4.0*. Built by GitHub Pages via `.github/workflows/pages.yml`. Details in
`README.md`.

## Build

```bash
RBENV_VERSION=3.1.2 bundle exec jekyll build    # → _site/
RBENV_VERSION=3.1.2 bundle exec jekyll serve    # http://localhost:4000
python3 _migration/compare_builds.py [REV]      # compare every generated page with REV (default HEAD)
```

The system Ruby is too old (no matching bundler), so always use rbenv 3.1.2. Never commit `_site/`.
After changes to layouts, includes or plugins, run `compare_builds.py` and check that only the
intended pages differ.

## Language

Visible texts on the site are **German**. Code comments, commit messages and the README are English.

Always write **Makespace**, never "Makerspace" ("Maker" is a masculine word in German, and we want
to avoid the gender debate). This applies to all texts, alt texts, and commit messages.

## Archive rules

- **Keep URLs:** posts keep their WordPress permalink (`permalink:` in the front matter), as do
  `/category/…`, `/tag/…` (display name → slug in `_data/{categories,tags}.yml`) and `/page/N/`.
  Never change an existing `permalink`.
- Posts render with `render_with_liquid: false` (old bodies contain literal `{{ … }}`/`{% … %}`),
  so no Liquid inside posts.
- Posts are Markdown only where the result is identical to the HTML (`_migration/html2md.py`
  verifies this). Everything else stays `.html` on purpose. When converting a post, remove it from
  `exclude` in `.pages.yml`.
- Theme changes go in `assets/css/style.css` and are marked with a `port:` comment; no CSS/JS frameworks.
- No external resources (fonts, scripts, trackers, iframes). Dead embeds are replaced by a note
  (`.embed-gone`), and YouTube or other videos are only linked, never embedded.
- Lightbox: `assets/js/lightbox.js` picks up post images automatically.

## Editing

- **Edit button:** `_includes/edit-page.html` (included by `_layouts/three-column.html` and
  `_layouts/page-nosidebars.html`) shows "✏️ Diese Seite bearbeiten" under every post and page →
  GitHub's editor for `page.path` (repo/branch in `_config.yml` under `repository`/`branch`).
  Generated category/tag archives get no button.
- CMS: [Pages CMS](https://pagescms.org), config in `.pages.yml` (Markdown posts only). Keep it in sync
  when posts get new front-matter fields.

## Images and privacy

- Ship photos without metadata (phone photos contain GPS data): re-save them with Pillow.
- Photos of children: make faces (including profiles and the backs of heads) unrecognizable. Also
  hide handwritten names, access codes and licence plates.
- Don't publish home addresses or other people's email addresses (even if they appear in sources).

## Branches and pull requests

Whoever pushes a branch (not `main`) always opens a pull request for it with `gh pr create`. The
description says **what** changes, **why** and **how it was tested** (build, `compare_builds.py`,
pages looked at), and its title matches the commit message. For visible changes, add screenshots of
the affected pages (desktop and phone); if nothing is visible, say why there are none.
