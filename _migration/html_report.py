#!/usr/bin/env python3
"""
Why are posts still HTML, and what would a conversion to Markdown lose?

  python3 _migration/html_report.py        # writes _data/html_report.json (shown on /statistiken/)

For every _posts/*.html it lists the markup outside html2md's safe subset (grouped into
features below), and tries the opportunistic conversion (html2md.convert_lenient: Markdown
where possible, the rest kept as raw HTML blocks), checked with Jekyll's own kramdown.
Needs Ruby with Jekyll (RBENV_VERSION=3.1.2).
"""
import glob
import json
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import html2md  # noqa: E402

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# feature id -> (label, what plain Markdown would lose, does kramdown have its own syntax?)
FEATURES = {
    "iframe": ("Eingebettete Videos und Karten (iframe)",
               "Der Player bzw. die Karte – reines Markdown kann nichts einbetten, übrig bliebe ein Link.", False),
    "audio": ("Audio-Player (audio)", "Der Player – übrig bliebe ein Link auf die MP3-Datei.", False),
    "script": ("Skripte und eingebettetes CSS (script, style)",
               "Das Verhalten bzw. Aussehen, das die Skripte und Styles erzeugen.", False),
    "embed-gone": ("Hinweis „Flash-Video nicht mehr abspielbar“",
                   "Der gestaltete Hinweiskasten – er würde zu einem normalen Absatz.", False),
    "figure": ("Bilder mit Bildunterschrift (figure, figcaption)",
               "Die Verbindung von Bild und Unterschrift; die Unterschrift würde ein normaler Absatz.", False),
    "style": ("Inline-Styles (style=…)",
              "Farben, Schriftgrößen, Abstände und Ausrichtungen, die direkt am Element stehen.", False),
    "align": ("Ausrichtung per align=… (Absätze, Tabellen)",
              "Zentrierte oder rechtsbündige Absätze.", False),
    "class": ("CSS-Klassen und Sprungmarken an Absätzen, Listen, Links (class, id)",
              "Gestaltung über Klassen (z. B. WordPress-Galerien) und Anker für Links innerhalb der Seite. "
              "kramdown kann Klassen mit {: .klasse} setzen, das Ergebnis ist aber kaum noch lesbar.", True),
    "div": ("Container (div, span)", "Gruppierungen mit eigener Gestaltung, z. B. Galerien und Hinweiskästen.", False),
    "strike": ("Durchgestrichener Text (strike, s)", "Das Durchstreichen – kramdown hat dafür keine Syntax.", False),
    "abbr": ("Abkürzungen mit Erklärung (abbr)",
             "Nichts, wenn man kramdowns Abkürzungen (*[HTML]: …) nutzt – die gelten dann aber für den ganzen Beitrag.", True),
    "dl": ("Definitionslisten (dl, dt, dd)", "Die CSS-Klassen der Liste; kramdown kennt Definitionslisten.", True),
    "table": ("Tabellen (table)", "Breiten und Ausrichtung der Zellen; kramdown kennt einfache Tabellen.", True),
    "pre": ("Vorformatierter Text (pre)", "Nichts – als Codeblock darstellbar, nur der Umbau fehlt noch.", True),
    "small": ("Kleine Schrift, Zitate (small, cite)", "Die Auszeichnung (kleinere Schrift bzw. Werktitel).", False),
    "comment": ("HTML-Kommentare", "Nichts Sichtbares – Kommentare sind ohnehin unsichtbar.", True),
    "broken": ("Kaputtes HTML aus WordPress (z. B. <size>, <your>)",
               "Nichts Gewolltes – das sind Reste von Tippfehlern im alten Editor.", False),
    "other": ("Sonstiges (Attribute an Bildern, Zeilenumbrüchen, Links …)",
              "Kleinigkeiten wie style an Bildern oder Zeilenumbrüche mit clear.", False),
    "render": ("Nur feine Unterschiede beim Rendern",
               "Fast nichts: ein Zeilenumbruch am Absatzende, leere Sprungmarken-Links, ein Leerzeichen innerhalb "
               "von fett/kursiv oder Listen, die kramdown mit etwas mehr Abstand setzt. Alle Elemente "
               "sind Markdown-fähig, nur das Ergebnis ist nicht Zeichen für Zeichen gleich.", True),
}
KNOWN_TAGS = html2md.BLOCK | html2md.INLINE | {
    "iframe", "audio", "source", "script", "style", "figure", "figcaption", "div", "span", "strike",
    "s", "abbr", "dl", "dt", "dd", "table", "tbody", "thead", "tr", "td", "th", "pre", "small",
    "cite", "object", "embed", "param", "video", "sup", "sub", "u", "del", "ins", "font", "center"}


class Scanner(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.found = set()
        self.feed(text)
        self.close()

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        f = self.found
        if tag in ("iframe", "object", "embed", "video"):
            f.add("iframe")
        elif tag in ("audio", "source"):
            f.add("audio")
        elif tag in ("script", "style"):
            f.add("script")
        elif tag in ("figure", "figcaption"):
            f.add("figure")
        elif tag in ("div", "span"):
            f.add("embed-gone" if "embed-gone" in (a.get("class") or "") else "div")
        elif tag in ("strike", "s", "del"):
            f.add("strike")
        elif tag == "abbr":
            f.add("abbr")
        elif tag in ("dl", "dt", "dd"):
            f.add("dl")
        elif tag in ("table", "tbody", "thead", "tr", "td", "th"):
            f.add("table")
        elif tag == "pre":
            f.add("pre")
        elif tag in ("small", "cite", "sup", "sub", "u", "font", "center", "ins"):
            f.add("small")
        elif tag not in KNOWN_TAGS:
            f.add("broken")
        if "style" in a:
            f.add("style")
        if "align" in a and tag != "img":
            f.add("align")
        allowed = html2md.ALLOWED_ATTRS.get(tag, set())
        extra = set(a) - allowed - html2md.IGNORED_ATTRS - {"style", "align"}
        if tag == "p" and "class" in a and not set((a["class"] or "").split()) - html2md.IGNORED_CLASSES:
            extra.discard("class")
        if tag in html2md.BLOCK | html2md.INLINE and extra:
            f.add("class" if extra & {"class", "id"} else "other")

    def handle_comment(self, data):
        if f"<!--{data}-->" != html2md.MORE:
            self.found.add("comment")


def main():
    files = sorted(glob.glob(os.path.join(SITE, "_posts", "*.html")))
    posts, bodies = [], {}
    for f in files:
        front, body = html2md._split_front_matter(open(f, encoding="utf-8").read())
        title = re.search(r'^title:\s*"?(.*?)"?\s*$', front, re.M).group(1).replace('\\"', '"')
        link = re.search(r"^permalink:\s*(\S+)", front, re.M).group(1)
        found = Scanner(body).found or {"render"}
        bodies[f] = body
        posts.append({"file": os.path.relpath(f, SITE), "title": title, "url": link,
                      "features": [k for k in FEATURES if k in found]})

    lenient = html2md.convert_lenient_verified(bodies)
    for p, f in zip(posts, files):
        md, raw, same = lenient[f]
        p["lenient_identical"] = same
        p["html_blocks"] = raw
        # Share of the visible text that stays inside HTML blocks
        text = len(re.sub(r"<[^>]+>|\s+", "", bodies[f])) or 1
        raw_text = sum(len(re.sub(r"<[^>]+>|\s+", "", c)) for c in html2md._Segmenter(bodies[f]).chunks
                       if html2md.convert(c) is None and c != html2md.MORE)
        p["html_share"] = round(100 * raw_text / text)

    features = []
    for k, (label, lost, kramdown) in FEATURES.items():
        members = [p for p in posts if k in p["features"]]
        if members:
            features.append({"id": k, "label": label, "lost": lost, "kramdown_syntax": kramdown,
                             "posts": len(members), "only": sum(1 for p in members if len(p["features"]) == 1)})
    features.sort(key=lambda x: -x["posts"])
    report = {
        "html_posts": len(posts),
        "lenient_identical": sum(p["lenient_identical"] for p in posts),
        "features": features,
        "posts": posts,
    }
    with open(os.path.join(SITE, "_data", "html_report.json"), "w", encoding="utf-8") as out:
        json.dump(report, out, ensure_ascii=False, indent=1)
        out.write("\n")
    print(f"{len(posts)} HTML posts, {report['lenient_identical']} identical as Markdown with HTML blocks",
          file=sys.stderr)
    for x in features:
        print(f"  {x['posts']:4} ({x['only']:3} only this)  {x['label']}", file=sys.stderr)


if __name__ == "__main__":
    main()
