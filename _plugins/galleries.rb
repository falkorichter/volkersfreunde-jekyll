# frozen_string_literal: true

# Markdown galleries for new Markdown posts (the old WordPress galleries in the imported .html
# posts stay as they are).
#
# In Markdown, put the images on consecutive lines (no blank line between them) and mark the
# paragraph with {: .gallery}:
#
#   ![Alt text 1](/assets/images/2026/11/foo-01.jpg)
#   ![Alt text 2](/assets/images/2026/11/foo-02.jpg)
#   {: .gallery}
#
# Kramdown renders that as <p class="gallery"><img …><img …></p>. After rendering, this hook
# turns it into
#
#   <div class="md-gallery"><a href="foo-01.jpg"><img src="foo-01-600w.jpg" alt="…" loading="lazy"></a>…</div>
#
# assets/js/lightbox.js opens every image link in .entry-content, so the links need no class;
# the styles are in assets/css/style.css ("port: Markdown galleries").
#
# - Thumbnail: "<name>-600w.<ext>" next to the image if it exists, otherwise the image itself.
# - The class is "md-gallery", not "gallery": the old WordPress galleries already use div.gallery
#   (with inline styles), so the new styles must not apply to them.
# - A gallery with a single image gets "md-gallery-single".
# - Every image needs an alt text, otherwise the build stops.
# - Videos: a Markdown image pointing to a local .mp4/.webm, alone in its paragraph, becomes
#   <video class="post-video" controls>, with "<name>.jpg" as poster if that file exists.
#
# Runs before baseurl_links.rb (priority :high), which then prefixes the generated links.
module Volkersfreunde
  module Galleries
    IMG_RE = /<img\b([^>]*?)\s*\/?>/m.freeze
    ATTR_RE = /([a-zA-Z-]+)="([^"]*)"/.freeze
    GALLERY_RE = %r{<p class="(gallery(?:\s[^"]*)?)">(.*?)</p>}m.freeze
    VIDEO_RE = %r{<p>\s*(<img\b[^>]*?src="/[^"]+\.(?:mp4|webm)"[^>]*?/?>)\s*</p>}m.freeze

    module_function

    def attrs(tag)
      tag.scan(ATTR_RE).to_h
    end

    def exists?(site, url)
      return false unless url.start_with?("/") && !url.start_with?("//")

      File.file?(File.join(site.source, url))
    end

    def thumb_for(site, src)
      thumb = src.sub(/(\.[a-zA-Z0-9]+)\z/, '-600w\1')
      exists?(site, thumb) ? thumb : src
    end

    def gallery(site, doc, classes, inner)
      images = inner.scan(IMG_RE).map { |m| attrs(m[0]) }
      return nil if images.empty? || inner.gsub(IMG_RE, "").strip != ""

      classes = ["md-gallery"] + (classes.split - ["gallery"])
      classes << "md-gallery-single" if images.size == 1
      links = images.map do |a|
        src = a["src"].to_s
        if a["alt"].to_s.strip.empty?
          raise Jekyll::Errors::FatalException,
                "Galerie: Bild ohne Alt-Text in #{doc.relative_path}: #{src}"
        end
        %(  <a href="#{src}"><img src="#{thumb_for(site, src)}" alt="#{a['alt']}" loading="lazy"></a>)
      end
      %(<div class="#{classes.uniq.join(' ')}">\n#{links.join("\n")}\n</div>)
    end

    def video(site, img_tag)
      a = attrs(img_tag)
      src = a["src"]
      poster = src.sub(/\.[a-zA-Z0-9]+\z/, ".jpg")
      poster_attr = exists?(site, poster) ? %( poster="#{poster}") : ""
      label = a["alt"].to_s.strip.empty? ? "" : %( aria-label="#{a['alt']}")
      %(<video class="post-video" controls preload="none" playsinline#{poster_attr} src="#{src}"#{label}></video>)
    end

    def process(doc)
      return unless doc.output && doc.output_ext == ".html" && doc.output.include?("<p")

      site = doc.site
      out = doc.output.gsub(GALLERY_RE) do
        gallery(site, doc, Regexp.last_match(1), Regexp.last_match(2)) || Regexp.last_match(0)
      end
      doc.output = out.gsub(VIDEO_RE) { video(site, Regexp.last_match(1)) }
    end
  end
end

Jekyll::Hooks.register [:pages, :documents], :post_render, priority: :high do |doc|
  Volkersfreunde::Galleries.process(doc)
end
