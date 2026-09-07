#!/usr/bin/env python3
"""Speaker notes as wide flash cards, four to a landscape A4 sheet, ready to cut.

Fronts carry the notes, backs carry a thumbnail of the slide, interleaved so the
sheets duplex-print. Reads the notes straight out of index.qmd so the cards
cannot drift from the deck. Print from the browser: margins None, scale 100%.

    python3 make-cards.py                  # -> speaker-cards.html
    python3 make-cards.py --mirror h       # if the backs land on the wrong cards
    python3 make-cards.py --force-shots    # re-capture the slide thumbnails

Which way the backs mirror depends on the printer's duplex setting, and the
"long edge / short edge" labels are not applied consistently across drivers.
Every card is numbered on both faces, so print two sheets first and look: if
2/8's notes back onto 3/8's picture, re-run with the other --mirror.
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).parent
QMD = HERE / "index.qmd"
CSS_SRC = HERE / "custom.css"
HTML = HERE / "speaker-cards.html"
SHOTS = HERE / "cards-img"
SHOT_W, SHOT_H, SHOT_Q = 1200, 800, 80
TITLE_POS = 1

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
/* A landscape sheet flipped about its long edge inverts the vertical axis, so
   a back printed upright lands upside down on the cut card. The whole face is
   turned — header with picture — because everything on one side of a sheet
   flips together, and turning only part of it leaves the two disagreeing.
   The rotation is inside the cell, so it moves nothing: which card backs which
   is set by the grid position alone. On screen the backs therefore read
   inverted, which is how you can tell the rotation is still applied. */
.back {{ transform: rotate(180deg); padding-bottom: 5mm; }}
.back .head {{ margin-bottom: 3mm; }}
.shot {{ flex: 1; min-height: 0; display: flex; align-items: center; justify-content: center; }}
.shot img {{ max-width: 100%; max-height: 100%; object-fit: contain; border: 0.2mm solid #ddd; }}
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


def capture(cards, force=False):
    """One JPEG per slide, via a throwaway render of the deck.

    The deck is rendered into a temp directory rather than in place: the
    project's own _site is usually being served by a live `quarto preview`,
    and rendering over it kills that.
    """
    SHOTS.mkdir(exist_ok=True)
    positions = [TITLE_POS] + [c["pos"] for c in cards]
    targets = {p: SHOTS / f"slide-{p:02d}.jpg" for p in positions}
    newest = max(QMD.stat().st_mtime, CSS_SRC.stat().st_mtime)
    if not force and all(
        t.exists() and t.stat().st_mtime > newest for t in targets.values()
    ):
        return targets

    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp) / "deck"
        shutil.copytree(
            HERE, build,
            ignore=shutil.ignore_patterns("_site", ".quarto", ".git",
                                          "speaker-cards.html", "cards-img"),
        )
        subprocess.run(["quarto", "render", str(build)],
                       check=True, capture_output=True)
        site = (build / "_site" / "index.html").as_uri()
        for pos, jpg in targets.items():
            png = Path(tmp) / f"{pos}.png"
            subprocess.run(
                ["chromium", "--headless", "--no-sandbox", "--disable-gpu",
                 "--hide-scrollbars", "--window-size=2100,1400",
                 "--virtual-time-budget=15000", f"--screenshot={png}",
                 f"{site}#/{pos - 1}"],
                check=True, capture_output=True,
            )
            subprocess.run(
                ["convert", str(png), "-resize", f"{SHOT_W}x{SHOT_H}",
                 "-quality", str(SHOT_Q), str(jpg)],
                check=True, capture_output=True,
            )
    return targets


# A sheet is 2x2, read top-left, top-right, bottom-left, bottom-right. Turning
# it over about its horizontal axis swaps the rows; about its vertical axis,
# the columns. Backs are emitted in whichever order puts each picture behind
# its own notes.
MIRRORS = {"v": [2, 3, 0, 1], "h": [1, 0, 3, 2]}


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
<div class="foot"><span>at 142 wpm, timed</span><span>5:00 hard stop</span></div>
</div>"""


def back(pos, title, secs, shot):
    time = f"~{secs} s" if secs is not None else ""
    return f"""<div class="card back">
<div class="head"><span class="num">{pos}/8</span>
<span class="title">{title}</span><span class="time">{time}</span></div>
<div class="shot"><img src="{shot}"></div>
</div>"""


def build(cards, shots, mirror):
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
        rel = lambda p: shots[p].relative_to(HERE).as_posix()
        faces = [back(c["pos"], c["title"], c["secs"], rel(c["pos"])) for c in group]

        spare = PER_SHEET - len(group)
        if spare and i + PER_SHEET >= len(cards):
            out.append(runsheet(cards))
            # The run sheet has no slide of its own, so its back carries the
            # one card the notes never cover: the title.
            faces.append(back(TITLE_POS, "Title", None, rel(TITLE_POS)))
            spare -= 1
        out += ['<div class="blank"></div>'] * spare
        out.append("</div>")

        faces += ['<div class="blank"></div>'] * (PER_SHEET - len(faces))
        out.append('<div class="sheet">')
        out += [faces[j] for j in MIRRORS[mirror]]
        out.append("</div>")
    out.append(FIT_JS.replace("%BODY%", str(BODY_PT)).replace("%FLOOR%", str(FLOOR_PT)))
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror", choices=["v", "h"], default="v",
                    help="how the sheet turns over: v swaps rows (long-edge "
                         "flip of a landscape sheet), h swaps columns")
    ap.add_argument("--force-shots", action="store_true",
                    help="re-capture the slide thumbnails even if current")
    args = ap.parse_args()

    cards = parse(QMD.read_text(encoding="utf-8"))
    if not cards:
        sys.exit("no notes blocks found in index.qmd")
    shots = capture(cards, force=args.force_shots)
    HTML.write_text(build(cards, shots, args.mirror), encoding="utf-8")
    sheets = -(-len(cards) // PER_SHEET) * 2
    print(f"{len(cards)} cards, fronts and backs, on {sheets} landscape A4 "
          f"sheet(s) -> {HTML.name}, {mmss(cards[-1]['elapsed'])} total "
          f"(mirror: {args.mirror})")


if __name__ == "__main__":
    main()
