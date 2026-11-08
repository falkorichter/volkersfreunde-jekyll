/*
 * "Markdown-Vorschau" for posts that are still stored as HTML (_includes/edit-page.html).
 * Opportunistic conversion in the browser: every top-level piece of the post that fits the
 * safe Markdown subset (paragraphs, headings, lists, quotes, links, emphasis, images – the same
 * subset as _migration/html2md.py) becomes Markdown, everything else stays as an HTML block,
 * which kramdown passes through unchanged. The result is not verified; the file on GitHub is
 * only changed if someone pastes it there.
 * The page is fetched again, so the conversion sees the original markup (lightbox.js changes the DOM).
 */
(function () {
  var button = document.querySelector(".md-preview-button");
  if (!button || typeof HTMLDialogElement !== "function" || !window.fetch || !window.DOMParser) return;
  var front = JSON.parse(document.getElementById("md-preview-front").textContent);
  var baseurl = button.getAttribute("data-baseurl") || "";
  button.hidden = false;

  var BLOCK = { P: 1, H1: 1, H2: 1, H3: 1, H4: 1, H5: 1, H6: 1, UL: 1, OL: 1, BLOCKQUOTE: 1, HR: 1 };
  var ALLOWED = {
    A: ["href", "title", "target", "rel"],
    IMG: ["src", "alt", "title", "width", "height", "class", "align"],
    P: ["class"]
  };
  var IGNORED = ["loading", "decoding"];

  function Unsupported() {}

  function url(u) {
    if (baseurl && u.indexOf(baseurl + "/") === 0) u = u.slice(baseurl.length); // see _plugins/baseurl_links.rb
    if (/[<>]/.test(u)) throw new Unsupported();
    return /[\s()]/.test(u) ? "<" + u + ">" : u;
  }

  function attrs(el) {
    var allowed = ALLOWED[el.tagName] || [], out = {};
    for (var i = 0; i < el.attributes.length; i++) {
      var a = el.attributes[i];
      if (IGNORED.indexOf(a.name) >= 0) continue;
      if (el.tagName === "P" && a.name === "class" && a.value.trim() === "wp-block-paragraph") continue;
      if (allowed.indexOf(a.name) < 0 || el.tagName === "P") throw new Unsupported();
      if (/["}]/.test(a.value)) throw new Unsupported();
      out[a.name] = a.value;
    }
    return out;
  }

  function ial(a, skip) {
    var parts = [];
    Object.keys(a).forEach(function (k) {
      if (skip.indexOf(k) >= 0) return;
      if (k === "class") a[k].split(/\s+/).filter(Boolean).forEach(function (c) { parts.push("." + c); });
      else parts.push(k + '="' + a[k] + '"');
    });
    return parts.length ? "{: " + parts.join(" ") + "}" : "";
  }

  function escape(text) {
    return text.replace(/([\\`*_\[\]{}<>|#!$"'])/g, "\\$1").replace(/--/g, "-\\-").replace(/\.\.\./g, "\\...");
  }

  function emphasis(el, mark) {
    var inner = inline(el.childNodes);
    if (!inner.trim() || inner !== inner.trim()) throw new Unsupported();
    return mark + inner + mark;
  }

  function inline(nodes) {
    var out = "";
    Array.prototype.forEach.call(nodes, function (n) {
      if (n.nodeType === 3) { out += escape(n.textContent.replace(/\s+/g, " ")); return; }
      if (n.nodeType !== 1) throw new Unsupported();
      var a = attrs(n), title;
      switch (n.tagName) {
        case "BR": out += "  \n"; break;
        case "STRONG": case "B": out += emphasis(n, "**"); break;
        case "EM": case "I": out += emphasis(n, "*"); break;
        case "CODE":
          if (n.children.length || /`/.test(n.textContent)) throw new Unsupported();
          out += "`" + n.textContent + "`";
          break;
        case "IMG":
          if (!a.src) throw new Unsupported();
          title = a.title ? ' "' + a.title + '"' : "";
          out += "![" + escape(a.alt || "") + "](" + url(a.src) + title + ")" + ial(a, ["src", "alt", "title"]);
          break;
        case "A":
          var text = inline(n.childNodes);
          if (!a.href || !text.trim()) throw new Unsupported();
          title = a.title ? ' "' + a.title + '"' : "";
          out += "[" + text + "](" + url(a.href) + title + ")" + ial(a, ["href", "title"]);
          break;
        default: throw new Unsupported();
      }
    });
    return out.replace(/  \n +/g, "  \n");
  }

  function block(el) {
    attrs(el);
    var t = el.tagName, text;
    if (t === "P") {
      text = inline(el.childNodes).trim();
      if (/^(\d+\.|[-+*>]|={2,}|-{2,})\s/.test(text)) throw new Unsupported();
      return text;
    }
    if (/^H[1-6]$/.test(t)) {
      text = inline(el.childNodes).trim();
      if (text.indexOf("\n") >= 0) throw new Unsupported();
      return "######".slice(0, +t[1]) + " " + text;
    }
    if (t === "HR") return "***";
    if (t === "BLOCKQUOTE") {
      return blocks(el.childNodes).split("\n").map(function (l) { return l ? "> " + l : ">"; }).join("\n");
    }
    if (t === "UL" || t === "OL") {
      var lines = [], number = 1;
      Array.prototype.forEach.call(el.childNodes, function (li) {
        if (li.nodeType === 3 && !li.textContent.trim()) return;
        if (li.tagName !== "LI") throw new Unsupported();
        attrs(li);
        var marker = t === "OL" ? number++ + ". " : "* ", pad = " ".repeat(marker.length);
        var parts = Array.prototype.slice.call(li.childNodes);
        var nested = parts.filter(function (c) { return c.tagName === "UL" || c.tagName === "OL"; });
        var own = parts.filter(function (c) { return nested.indexOf(c) < 0; });
        var item = inline(own).trim();
        if (!item) throw new Unsupported();
        item.split("\n").forEach(function (l, i) { lines.push((i ? pad : marker) + l); });
        nested.forEach(function (sub) {
          block(sub).split("\n").forEach(function (l) { lines.push(pad + l); });
        });
      });
      return lines.join("\n");
    }
    throw new Unsupported();
  }

  function blocks(nodes) {
    var out = [];
    Array.prototype.forEach.call(nodes, function (n) {
      if (n.nodeType === 3 && !n.textContent.trim()) return;
      if (n.nodeType !== 1 || !BLOCK[n.tagName]) throw new Unsupported();
      var b = block(n);
      if (b) out.push(b);
    });
    return out.join("\n\n");
  }

  // Top level: Markdown where possible, otherwise the piece stays HTML.
  function convert(root) {
    var out = [], raw = 0;
    Array.prototype.forEach.call(root.childNodes, function (n) {
      if (n.nodeType === 3) {
        if (n.textContent.trim()) { out.push(n.textContent.trim()); raw++; }
        return;
      }
      if (n.nodeType === 8) { out.push("<!--" + n.textContent + "-->"); return; }
      if (n.nodeType !== 1 || n.className === "clear") return;
      if (n.tagName === "SPAN" && n.id === "more" && !n.childNodes.length) { out.push("<!--more-->"); return; }
      try {
        if (!BLOCK[n.tagName]) throw new Unsupported();
        var md = block(n);
        if (md) out.push(md);
      } catch (e) {
        if (!(e instanceof Unsupported)) throw e;
        out.push(n.outerHTML);
        raw++;
      }
    });
    return { markdown: out.join("\n\n") + "\n", raw: raw };
  }

  function frontMatter() {
    var lines = ["---"];
    Object.keys(front).forEach(function (k) {
      var v = front[k];
      if (v === null || v === "") return;
      // JSON strings and arrays are valid YAML; dates and numbers stay plain
      lines.push(k + ": " + (k === "date" || typeof v === "number" ? v : JSON.stringify(v)));
    });
    return lines.join("\n") + "\n---\n\n";
  }

  var dialog = document.createElement("dialog");
  dialog.className = "md-preview";
  dialog.setAttribute("aria-label", "Markdown-Vorschau");
  dialog.innerHTML =
    '<button type="button" class="md-preview-close" aria-label="Schließen">×</button>' +
    "<h3>Markdown-Vorschau</h3>" +
    '<p class="md-preview-note"></p>' +
    '<textarea spellcheck="false" aria-label="Markdown"></textarea>' +
    '<p class="md-preview-actions">' +
    '<button type="button" class="md-preview-copy">Kopieren</button> ' +
    '<button type="button" class="md-preview-download">Als .md herunterladen</button> ' +
    '<a class="md-preview-edit" target="_blank" rel="noopener">Im GitHub-Editor öffnen</a>' +
    "</p>";
  document.body.appendChild(dialog);
  var textarea = dialog.querySelector("textarea");
  var note = dialog.querySelector(".md-preview-note");
  var copy = dialog.querySelector(".md-preview-copy");
  dialog.querySelector(".md-preview-edit").href = button.getAttribute("data-edit");
  dialog.querySelector(".md-preview-close").addEventListener("click", function () { dialog.close(); });
  dialog.addEventListener("click", function (e) { if (e.target === dialog) dialog.close(); });

  copy.addEventListener("click", function () {
    textarea.select();
    var done = function () { copy.textContent = "Kopiert ✓"; setTimeout(function () { copy.textContent = "Kopieren"; }, 2000); };
    if (navigator.clipboard) navigator.clipboard.writeText(textarea.value).then(done, function () { document.execCommand("copy"); done(); });
    else { document.execCommand("copy"); done(); }
  });

  dialog.querySelector(".md-preview-download").addEventListener("click", function () {
    var a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([textarea.value], { type: "text/markdown" }));
    a.download = button.getAttribute("data-file").split("/").pop().replace(/\.html$/, ".md");
    document.body.appendChild(a);
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 0);
  });

  var cached = null;
  button.addEventListener("click", function () {
    textarea.value = "";
    note.textContent = "Wird umgewandelt …";
    dialog.showModal();
    if (cached) return show(cached);
    fetch(location.href, { credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); })
      .then(function (html) {
        var doc = new DOMParser().parseFromString(html, "text/html");
        var root = doc.querySelector(".entry.single .entry-content");
        if (!root) throw new Error("no content");
        cached = convert(root);
        show(cached);
      })
      .catch(function () { note.textContent = "Die Umwandlung hat nicht geklappt – bitte im GitHub-Editor bearbeiten."; });
  });

  function show(result) {
    textarea.value = frontMatter() + result.markdown;
    note.innerHTML = "";
    note.appendChild(document.createTextNode(
      "Ungeprüfte Umwandlung im Browser: " +
      (result.raw === 0 ? "alles ist Markdown. " :
        result.raw === 1 ? "1 Abschnitt bleibt HTML, der Rest ist Markdown. " :
          result.raw + " Abschnitte bleiben HTML, der Rest ist Markdown. ") +
      "Der Beitrag selbst bleibt HTML. Zum Übernehmen im GitHub-Editor den Text ersetzen und den " +
      "Dateinamen von .html auf .md ändern. "));
    var more = document.createElement("a");
    more.href = button.getAttribute("data-stats");
    more.textContent = "Warum noch HTML?";
    note.appendChild(more);
  }
})();
