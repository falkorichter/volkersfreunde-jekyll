#!/usr/bin/env ruby
# frozen_string_literal: true

# Checks the content files for galleries that are not written in Markdown.
# New galleries must use the Markdown form (see CLAUDE.md, "Images and galleries"):
#
#   ![Alt text 1](/assets/images/2026/11/foo-01.jpg)
#   ![Alt text 2](/assets/images/2026/11/foo-02.jpg)
#   {: .gallery}
#
# HTML gallery markup (<div class="gallery">, <a class="lightbox">, WordPress/NextGEN gallery
# markup, [gallery] shortcodes) is reported with file and line; the exit code is 1, so the
# pull request check and the Pages build fail. Only the files in LEGACY are exempt.
#
# Usage: ruby _scripts/check_galleries.rb [files …]   (no files = whole repository)

ROOT = File.expand_path("..", __dir__)

# Legacy WordPress import, not converted: these posts keep the gallery markup WordPress
# generated (the archive keeps old posts as they were, see CLAUDE.md). Don't add new files here.
LEGACY = %w[
  _posts/2007-06-02-mit-muke-gewonnen.html
  _posts/2007-06-04-grillen-bei-volker.html
  _posts/2007-06-08-another-world-is-possible.html
  _posts/2007-06-11-another-world-is-still-possible.html
  _posts/2007-06-11-die-schonsten-kommen-aus-berlin.html
  _posts/2007-06-11-und-zum-fruhstuck-ham-and-eggs.html
  _posts/2007-06-12-nach-der-uni-an-den-see.html
  _posts/2008-05-07-gewonnen.html
  _posts/2008-08-08-volkersfreunde-im-gameslab.html
  _posts/2021-03-09-tinkercad.html
].freeze

# directories with templates, scripts, generated output or assets – not content
SKIP_DIRS = %w[_site _layouts _includes _plugins _scripts _migration assets vendor node_modules .git .github .jekyll-cache].freeze
CONTENT_EXT = %w[.md .markdown .html .htm].freeze
# documentation that shows HTML on purpose (not published)
SKIP_FILES = %w[CLAUDE.md README.md CHANGELOG.md].freeze

PATTERNS = [
  [/<div\b[^>]*class=["'][^"']*\bgallery\b/i, "HTML-Galerie (<div class=\"gallery\">)"],
  [/<a\b[^>]*class=["'][^"']*\blightbox\b/i, "HTML-Lightbox-Link (<a class=\"lightbox\">)"],
  [/\bwp-block-gallery\b|\bgallery-item\b|\[gallery[\s\]]/i, "WordPress-Galerie"],
  [/\bngg-(?:widget|gallery)/i, "NextGEN-Galerie"]
].freeze

def content_files(args)
  candidates =
    if args.empty?
      # tracked + new files git knows about (ignores _site, .gitignore'd files …)
      Dir.chdir(ROOT) { `git ls-files --cached --others --exclude-standard`.split("\n") }
    else
      args
    end
  candidates.select do |f|
    CONTENT_EXT.include?(File.extname(f).downcase) && File.file?(File.expand_path(f, ROOT)) &&
      !SKIP_FILES.include?(f) && !f.start_with?(".") &&
      SKIP_DIRS.none? { |d| f == d || f.start_with?("#{d}/") }
  end.sort
end

problems = []
legacy_seen = []
files = content_files(ARGV)
files.each do |rel|
  path = File.expand_path(rel, ROOT)
  File.foreach(path).with_index(1) do |line, no|
    PATTERNS.each do |re, what|
      next unless line.match?(re)

      if LEGACY.include?(rel)
        legacy_seen << rel
      else
        problems << "#{rel}:#{no}: #{what}"
      end
    end
  end
end

if problems.empty?
  puts "✓ Alle neuen Galerien sind Markdown (#{files.size} Dateien geprüft, " \
       "#{legacy_seen.uniq.size} alte WordPress-Beiträge ausgenommen)"
  exit 0
end

puts "✗ #{problems.size} Galerie-Stelle(n) nicht in Markdown:"
problems.each { |p| puts "  #{p}" }
puts <<~HINT

  Galerien bitte als Markdown schreiben – Bilder direkt untereinander, darunter {: .gallery}:

    ![Alt-Text 1](/assets/images/2026/11/foo-01.jpg)
    ![Alt-Text 2](/assets/images/2026/11/foo-02.jpg)
    {: .gallery}

  Das Plugin _plugins/galleries.rb macht daraus Vorschaubilder und Lightbox (siehe CLAUDE.md).
HINT
# GitHub annotations, so the problems show up directly in the pull request
if ENV["GITHUB_ACTIONS"]
  problems.each do |p|
    file, line, msg = p.split(":", 3)
    puts "::error file=#{file},line=#{line}::Galerie nicht in Markdown:#{msg}"
  end
end
exit 1
