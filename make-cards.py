#!/usr/bin/env python3
"""Speaker notes as A6 flash cards, four to an A4 sheet, ready to cut.

Reads the notes straight out of index.qmd so the cards cannot drift from the
deck, and prints through headless Chromium — the deck has no LaTeX toolchain
and does not need one for this.

    python3 make-cards.py        # -> speaker-cards.pdf
"""

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
QMD = HERE / "index.qmd"
HTML = HERE / "speaker-cards.html"
PDF = HERE / "speaker-cards.pdf"

BODY_PT = 10.4
FLOOR_PT = 8.0
PER_SHEET = 4


def md(text):
    """Render a markdown fragment the way the deck's notes are written."""
    if not text.strip():
        return ""
    out = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html", "--wrap=none"],
        input=text, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def inline(text):
    """Same, minus the block wrapper, so it can follow a label on one line."""
    html = md(text)
    m = re.fullmatch(r"<p>(.*)</p>", html, re.S)
    return m.group(1) if m else html


def parse(src):
    """One record per slide that has notes, in deck order."""
    chunks, cur, fence = [], None, False
    for line in src.split("\n"):
        if line.startswith("```"):
            fence = not fence
        if not fence and line.startswith("## "):
            if cur:
                chunks.append(cur)
            cur = {"title": re.sub(r"\s*\{.*$", "", line[3:]).strip(), "body": []}
            continue
        if cur is not None:
            cur["body"].append(line)
    if cur:
        chunks.append(cur)

    cards, elapsed = [], 0
    for deck_pos, ch in enumerate(chunks, start=2):
        body = "\n".join(ch["body"])
        note = re.search(
            r"::: \{\.notes\}\n<!-- (.+?) — ~(\d+) s \((.+?)\) -->\n(.*?)\n:::",
            body, re.S,
        )
        if not note:
            continue
        elapsed += int(note.group(2))
        screen = [m.group(1).strip() for m in
                  re.finditer(r"::: \{\.takeaway\}\n(.*?)\n:::", body, re.S)]
        cards.append({
            "pos": deck_pos,
            "title": ch["title"],
            "secs": int(note.group(2)),
            "meta": note.group(3),
            "screen": inline(" · ".join(screen)) if screen else "",
            "notes": md(note.group(4)),
            "elapsed": elapsed,
        })
    return cards


CSS = """
@page {{ size: A4 portrait; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "Source Sans Pro", "Helvetica Neue", Arial, sans-serif;
  color: #111;
  -webkit-print-color-adjust: exact;
}}
.sheet {{
  width: 210mm; height: 297mm;
  display: grid;
  grid-template-columns: 105mm 105mm;
  grid-template-rows: 148.5mm 148.5mm;
  page-break-after: always;
}}
.sheet:last-child {{ page-break-after: auto; }}
.card {{
  padding: 6mm 6mm 4.5mm;
  border: 0.2mm dashed #c4c4c4;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}}
.head {{
  display: flex; align-items: baseline; gap: 2.5mm;
  border-bottom: 0.35mm solid #222;
  padding-bottom: 1.6mm; margin-bottom: 3mm;
}}
.num {{
  font-size: 8pt; font-weight: 700; color: #fff; background: #222;
  border-radius: 1mm; padding: 0.4mm 1.4mm; flex: none;
}}
.title {{ font-size: 12.5pt; font-weight: 700; flex: 1; line-height: 1.15; }}
.time {{ font-size: 10pt; font-weight: 700; color: #222; flex: none; }}
.screen {{
  font-size: 8.4pt; color: #555; font-style: italic;
  line-height: 1.3; margin-bottom: 3mm;
}}
.screen b {{ font-style: normal; font-weight: 700; color: #333; }}
.notes {{ font-size: {body}pt; line-height: 1.34; flex: 1; }}
.notes p {{ margin: 0 0 1.7mm; }}
.notes p:last-child {{ margin-bottom: 0; }}
.notes strong {{ font-weight: 700; }}
.notes code {{ font-family: "Source Code Pro", monospace; font-size: 0.92em; }}
.foot {{
  font-size: 7.6pt; color: #888; border-top: 0.2mm solid #ddd;
  padding-top: 1.4mm; margin-top: 2.5mm;
  display: flex; justify-content: space-between; flex: none;
}}
.blank {{ border: 0.2mm dashed #c4c4c4; }}
table.run {{ width: 100%; border-collapse: collapse; font-size: 9.6pt; flex: 1; }}
table.run td {{ padding: 1.5mm 0; border-bottom: 0.15mm solid #e6e6e6; vertical-align: top; }}
table.run td:first-child {{ width: 6mm; color: #999; }}
table.run td.r {{ text-align: right; white-space: nowrap; padding-left: 2mm; }}
table.run tr:last-child td {{ border-bottom: none; }}
"""


# Shrink a card's prose until it fits rather than letting `overflow: hidden`
# eat the last line. Runs before Chromium prints, so the PDF carries the result.
FIT_JS = """<script>
for (const card of document.querySelectorAll('.card')) {
  const notes = card.querySelector('.notes');
  const cs = getComputedStyle(card);
  const inner = card.getBoundingClientRect().height
              - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
  const used = () => [...card.children]
      .reduce((s, e) => s + e.getBoundingClientRect().height, 0);
  let pt = %BODY%;
  while (used() > inner - 1 && pt > %FLOOR%) {
    pt -= 0.2;
    notes.style.fontSize = pt.toFixed(1) + 'pt';
  }
  card.dataset.pt = pt.toFixed(1);
}
</script>"""


def mmss(t):
    return f"{t // 60}:{t % 60:02d}"


def runsheet(cards):
    rows = "".join(
        f"<tr><td>{c['pos']}</td><td>{c['title']}</td>"
        f"<td class=r>{c['secs']} s</td><td class=r>{mmss(c['elapsed'])}</td></tr>"
        for c in cards
    )
    total = cards[-1]["elapsed"]
    return f"""<div class="card">
<div class="head"><span class="num">run</span>
<span class="title">Run sheet</span><span class="time">{mmss(total)}</span></div>
<table class="run">{rows}</table>
<div class="foot"><span>at 145 wpm</span><span>5:00 hard stop</span></div>
</div>"""


def build(cards):
    out = [f"<!doctype html><meta charset=utf-8><style>{CSS.format(body=BODY_PT)}</style>"]
    total = cards[-1]["elapsed"]
    for i in range(0, len(cards), PER_SHEET):
        out.append('<div class="sheet">')
        group = cards[i:i + PER_SHEET]
        for c in group:
            out.append(f"""<div class="card">
<div class="head"><span class="num">{c['pos']}/8</span>
<span class="title">{c['title']}</span><span class="time">~{c['secs']} s</span></div>
<div class="screen"><b>On screen:</b> {c['screen'] or '—'}</div>
<div class="notes">{c['notes']}</div>
<div class="foot"><span>{c['meta']}</span><span>{mmss(c['elapsed'])} / {mmss(total)}</span></div>
</div>""")
        spare = PER_SHEET - len(group)
        if spare and i + PER_SHEET >= len(cards):
            out.append(runsheet(cards))
            spare -= 1
        out += ['<div class="blank"></div>'] * spare
        out.append("</div>")
    out.append(FIT_JS.replace("%BODY%", str(BODY_PT)).replace("%FLOOR%", str(FLOOR_PT)))
    return "\n".join(out)


def main():
    cards = parse(QMD.read_text(encoding="utf-8"))
    if not cards:
        sys.exit("no notes blocks found in index.qmd")
    HTML.write_text(build(cards), encoding="utf-8")
    subprocess.run(
        ["chromium", "--headless", "--no-sandbox", "--disable-gpu",
         f"--print-to-pdf={PDF}", "--no-pdf-header-footer", HTML.as_uri()],
        check=True, capture_output=True,
    )
    sheets = -(-len(cards) // PER_SHEET)
    print(f"{len(cards)} cards on {sheets} A4 sheet(s) -> {PDF.name} "
          f"({PDF.stat().st_size // 1024} KB), {mmss(cards[-1]['elapsed'])} total")


if __name__ == "__main__":
    main()
