#!/usr/bin/env python3
"""Speaker notes as wide flash cards, four to a landscape A4 sheet, ready to cut.

Reads the notes straight out of index.qmd so the cards cannot drift from the
deck. Output is a self-contained HTML page: print it from the browser with
margins set to None and scale 100%.

    python3 make-cards.py        # -> speaker-cards.html
"""

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
QMD = HERE / "index.qmd"
HTML = HERE / "speaker-cards.html"

BODY_PT = 10.4
FLOOR_PT = 7.4
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


# Landscape A4 quartered into 148.5x105mm cards — the proportions of a 6x4"
# index card, and the same two sheets the portrait layout needed.
CSS = """
@page {{ size: A4 landscape; margin: 0; }}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  font-family: "Source Sans Pro", "Helvetica Neue", Arial, sans-serif;
  color: #111;
  print-color-adjust: exact;
  -webkit-print-color-adjust: exact;
}}
.sheet {{
  width: 297mm; height: 210mm;
  display: grid;
  grid-template-columns: 148.5mm 148.5mm;
  grid-template-rows: 105mm 105mm;
  page-break-after: always;
}}
.sheet:last-child {{ page-break-after: auto; }}
.card {{
  padding: 5mm 6mm 4mm;
  border: 0.2mm dashed #c4c4c4;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}}
.head {{
  display: flex; align-items: baseline; gap: 2.5mm;
  border-bottom: 0.35mm solid #222;
  padding-bottom: 1.2mm; margin-bottom: 1.6mm;
  flex: none;
}}
.num {{
  font-size: 8pt; font-weight: 700; color: #fff; background: #222;
  border-radius: 1mm; padding: 0.3mm 1.4mm; flex: none;
}}
.title {{ font-size: 12.5pt; font-weight: 700; flex: 1; line-height: 1.1; }}
.time {{ font-size: 10.5pt; font-weight: 700; flex: none; }}
.screen {{
  font-size: 8.4pt; color: #555; line-height: 1.25;
  margin-bottom: 2.2mm; flex: none;
}}
.screen b {{ font-weight: 700; color: #333; }}
.screen i, .screen em {{ font-style: italic; }}
.notes {{ font-size: {body}pt; line-height: 1.33; flex: 1; min-height: 0; overflow: hidden; }}
.notes p {{ margin: 0 0 1.6mm; }}
.notes p:last-child {{ margin-bottom: 0; }}
.notes code {{ font-family: "Source Code Pro", monospace; font-size: 0.92em; }}
.foot {{
  font-size: 7.6pt; color: #888; border-top: 0.2mm solid #ddd;
  padding-top: 1.2mm; margin-top: 2mm;
  display: flex; justify-content: space-between; flex: none;
}}
.blank {{ border: 0.2mm dashed #c4c4c4; }}
table.run {{ width: 100%; border-collapse: collapse; font-size: 9.4pt; }}
table.run td {{ padding: 0.9mm 0; border-bottom: 0.15mm solid #e6e6e6; }}
table.run td:first-child {{ width: 6mm; color: #999; }}
table.run td.r {{ text-align: right; white-space: nowrap; padding-left: 3mm; }}
table.run tr:last-child td {{ border-bottom: none; }}
"""

# Shrink a card's prose until it fits, rather than letting `overflow: hidden`
# eat the last line. This has to run in the browser that prints, because font
# metrics differ between machines and a size measured elsewhere proves nothing.
# It re-runs once fonts have settled and again before printing.
FIT_JS = """<script>
function fitCards() {
  for (const card of document.querySelectorAll('.card')) {
    const notes = card.querySelector('.notes');
    if (!notes) continue;
    // `.notes` is the flex filler, so it is exactly the leftover space and its
    // scrollHeight is the height the prose actually wants. Measuring the card
    // instead cannot work: a flex item with `min-height: 0` shrinks to fit
    // whatever is left, so the sum of the children always equals the card.
    let pt = %BODY%, lh = 1.33;
    notes.style.fontSize = pt.toFixed(2) + 'pt';
    notes.style.lineHeight = lh.toFixed(2);
    const over = () => notes.scrollHeight > notes.clientHeight + 0.5;
    while (over() && pt > %FLOOR%) {
      pt -= 0.1;
      notes.style.fontSize = pt.toFixed(2) + 'pt';
    }
    while (over() && lh > 1.14) {
      lh -= 0.01;
      notes.style.lineHeight = lh.toFixed(2);
    }
    card.dataset.pt = pt.toFixed(2);
    card.dataset.lh = lh.toFixed(2);
    card.dataset.slack = Math.round(notes.clientHeight - notes.scrollHeight);
  }
}
fitCards();
if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitCards);
window.addEventListener('beforeprint', fitCards);
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
    out = [f"<!doctype html><meta charset=utf-8><title>Speaker cards</title>"
           f"<style>{CSS.format(body=BODY_PT)}</style>"]
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
    sheets = -(-len(cards) // PER_SHEET)
    print(f"{len(cards)} cards on {sheets} landscape A4 sheet(s) -> {HTML.name}, "
          f"{mmss(cards[-1]['elapsed'])} total")


if __name__ == "__main__":
    main()
