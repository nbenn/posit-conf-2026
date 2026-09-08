#!/usr/bin/env python3
"""Memorisation drill sheets, generated from the speaker notes in index.qmd.

Six views of the same script, one per level of the fade-out ladder:

    full      the notes as written
    fade-5    every fifth word blanked
    fade-3    every third word blanked
    fade-2    every second word blanked
    letters   first letter of every word (the actor's cue sheet)
    openers   first word of every sentence, one per line (the on-stage card)

Blanks keep their width and punctuation, so the rhythm of the sentence stays
visible while the words are gone. On screen a tap reveals one word and the
level tabs switch views; printed, every level comes out as its own section.
The rehearsal plan in cards/drill-plan.md is included as the last tab.

    python3 cards/make-drill.py                  # -> cards/drill.html
    python3 cards/make-drill.py --fragment out    # body only, for embedding

Reads the notes straight out of index.qmd, like make-cards.py, so the sheets
cannot drift from the deck. Needs pandoc on the PATH, as make-cards.py does.
"""

import argparse
import html
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
QMD = ROOT / "index.qmd"
PLAN = HERE / "drill-plan.md"
OUT = HERE / "drill.html"

LEVELS = [
    ("full", "Full", 0),
    ("fade5", "1 in 5", 5),
    ("fade3", "1 in 3", 3),
    ("fade2", "1 in 2", 2),
    ("letters", "First letters", 1),
    ("openers", "Openers", 0),
]


def pandoc(text, to, *opts):
    out = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", to, "--wrap=none", *opts],
        input=text, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def plain(md):
    """Markdown to plain text on one line; the words are what is drilled."""
    return re.sub(r"\s+", " ", pandoc(md, "plain")).strip()


# --- parsing -----------------------------------------------------------------

def slides(src):
    """One record per slide with notes, in deck order."""
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

    out, elapsed = [], 0
    for ch in chunks:
        body = "\n".join(ch["body"])
        note = re.search(
            r"::: \{\.notes\}\n<!-- (.+?) — ~(\d+) s \((.+?)\) -->\n(.*?)\n:::",
            body, re.S,
        )
        if not note:
            continue
        secs = int(note.group(2))
        screen = [m.group(1).strip() for m in
                  re.finditer(r"::: \{\.takeaway\}\n(.*?)\n:::", body, re.S)]
        paras = [plain(p) for p in re.split(r"\n\s*\n", note.group(4).strip())]
        out.append({
            "n": len(out) + 1,
            "title": plain(ch["title"]),
            "secs": secs,
            "start": elapsed,
            "screen": plain(" · ".join(screen)),
            "paras": paras,
        })
        elapsed += secs
    return out


# --- rendering -----------------------------------------------------------------

WORD = re.compile(r"^([^\w]*)(\w[\w'’\-]*)(.*)$", re.U)


def tokens(text):
    """Split into (lead, core, tail) triples; core is the part that gets blanked."""
    out = []
    for tok in text.split(" "):
        m = WORD.match(tok)
        if m:
            out.append(m.groups())
        else:
            out.append(("", "", tok))
    return out


def render_para(text, level, every):
    """One paragraph at one level. Reveal markers like (4) are never blanked."""
    parts, i = [], 0
    for lead, core, tail in tokens(text):
        if not core or re.fullmatch(r"\d+(-\d+)?", core):
            parts.append(html.escape(lead + core + tail))
            continue
        i += 1
        e = html.escape
        if level == "full":
            parts.append(e(lead + core + tail))
        elif level == "letters":
            parts.append(
                f"{e(lead)}<span class=w>{e(core[0])}"
                f"<span class='b r'>{e(core[1:])}</span></span>{e(tail)}"
            )
        elif i % every == 0:
            parts.append(f"{e(lead)}<span class=b>{e(core)}</span>{e(tail)}")
        else:
            parts.append(e(lead + core + tail))
    return "<p>" + " ".join(parts) + "</p>"


def openers(paras):
    """First word of each sentence, in order, punctuation kept as a cue."""
    text = " ".join(paras)
    sents = re.split(r"(?<=[.!?:])\s+(?=[(\"“A-Z])", text)
    out = []
    for s in sents:
        m = re.match(r"^(\(\d+(?:-\d+)?\)\s*)?(\S+)", s)
        if m:
            out.append((m.group(1) or "") + m.group(2))
    return out


def clock(s):
    return f"{s // 60}:{s % 60:02d}"


def render_slide(sl, level, every):
    head = (
        f"<div class=head><span class=num>{sl['n']}</span>"
        f"<span class=title>{html.escape(sl['title'])}</span>"
        f"<span class=time>{clock(sl['start'])} · {sl['secs']}s</span></div>"
    )
    screen = f"<div class=screen>{html.escape(sl['screen'])}</div>" if sl["screen"] else ""
    if level == "openers":
        body = "<ol class=op>" + "".join(
            f"<li>{html.escape(w)}</li>" for w in openers(sl["paras"])) + "</ol>"
    else:
        body = "".join(render_para(p, level, every) for p in sl["paras"])
    return f"<section class=slide>{head}{screen}<div class=notes>{body}</div></section>"


CSS = """
/* The deck's greys. Dark is a real palette, not an inversion: the blank
   underline and the muted labels drop contrast on the dark ground too. */
:root {
  --ink: #1a1a1a; --mute: #707070; --line: #d4d4d4; --paper: #fff;
  --tab: #ededed; --blank: #9a9a9a;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ink: #e8e8e6; --mute: #9a9a9a; --line: #3a3b3f; --paper: #151618;
    --tab: #26272b; --blank: #6a6b70;
  }
}
:root[data-theme="dark"] {
  --ink: #e8e8e6; --mute: #9a9a9a; --line: #3a3b3f; --paper: #151618;
  --tab: #26272b; --blank: #6a6b70;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font-family: "Source Sans 3", "Source Sans Pro", "Helvetica Neue", Arial, sans-serif;
  font-size: 15px; line-height: 1.45;
}
nav.tabs button:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
@media (prefers-reduced-motion: no-preference) { nav.tabs button { transition: background .12s; } }
.wrap { max-width: 720px; margin: 0 auto; padding: 12px 16px 60px; }
nav.tabs {
  position: sticky; top: 0; background: var(--paper); z-index: 2;
  display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 0 10px;
  border-bottom: 1px solid var(--line); margin-bottom: 12px;
}
nav.tabs button {
  font: inherit; font-size: 13px; padding: 5px 10px; border-radius: 999px;
  border: 1px solid var(--line); background: var(--tab); color: var(--ink);
  cursor: pointer;
}
nav.tabs button.on { background: var(--ink); color: var(--paper); border-color: var(--ink); }
nav.tabs .sp { flex: 1; }
.level { display: none; }
.level.on { display: block; }
.hint { color: var(--mute); font-size: 13px; margin: 0 0 14px; }
.slide { margin: 0 0 26px; }
.head {
  display: flex; align-items: baseline; gap: 8px;
  border-bottom: 2px solid var(--ink); padding-bottom: 3px; margin-bottom: 4px;
}
.num {
  font-size: 11px; font-weight: 700; color: var(--paper); background: var(--ink);
  border-radius: 3px; padding: 1px 5px;
}
.title { font-weight: 700; flex: 1; }
.time { font-size: 13px; font-weight: 700; color: var(--mute); white-space: nowrap; }
.screen { font-size: 13px; color: var(--mute); margin-bottom: 8px; }
.notes p { margin: 0 0 9px; }
.b {
  color: transparent; border-bottom: 1px solid var(--blank);
  cursor: pointer; user-select: none;
}
.b.on, .reveal .b { color: inherit; border-bottom-color: transparent; }
.w { white-space: nowrap; }
/* First letters: the rest of the word is gone, not blanked, so the sheet is
   letters and punctuation only. Tapping the letter brings the word back. */
.w { cursor: pointer; }
.r { display: none; border: 0; }
.r.on, .reveal .r { display: inline; }
ol.op { margin: 0; padding-left: 26px; columns: 2; column-gap: 24px; }
ol.op li { break-inside: avoid; padding: 1px 0; }
.plan h1 { font-size: 20px; margin: 0 0 8px; }
.plan h2 { font-size: 16px; margin: 20px 0 6px; }
.plan h3 { font-size: 15px; margin: 14px 0 4px; }
.plan ul { padding-left: 22px; margin: 4px 0 8px; }
.plan li { margin: 2px 0; }
.plan code { font-family: "Source Code Pro", monospace; font-size: 0.92em; }
@media print {
  @page { size: A4; margin: 14mm; }
  :root { --ink: #111; --mute: #666; --line: #ccc; --paper: #fff; --blank: #777; }
  body { font-size: 11pt; }
  .wrap { max-width: none; padding: 0; }
  nav.tabs { display: none; }
  .level { display: block; page-break-before: always; }
  .level:first-of-type { page-break-before: auto; }
  .level > h1 { font-size: 14pt; margin: 0 0 6pt; }
  .b.on { color: transparent; border-bottom-color: var(--blank); }
  .r.on { display: none; }
  .slide { page-break-inside: avoid; }
}
@media screen { .level > h1 { display: none; } }
"""

JS = """<script>
(function () {
  const tabs = document.querySelectorAll('nav.tabs button[data-level]');
  const levels = document.querySelectorAll('.level');
  function show(id) {
    tabs.forEach(b => b.classList.toggle('on', b.dataset.level === id));
    levels.forEach(l => l.classList.toggle('on', l.id === 'lv-' + id));
    try { localStorage.setItem('drill-level', id); } catch (e) {}
    document.body.classList.remove('reveal');
  }
  tabs.forEach(b => b.addEventListener('click', () => show(b.dataset.level)));
  document.getElementById('reveal').addEventListener('click', () =>
    document.body.classList.toggle('reveal'));
  document.addEventListener('click', e => {
    const w = e.target.closest('.w');
    const b = w ? w.querySelector('.b') : e.target.closest('.b');
    if (b) b.classList.toggle('on');
  });
  let start = 'full';
  try { start = localStorage.getItem('drill-level') || start; } catch (e) {}
  show(document.getElementById('lv-' + start) ? start : 'full');
})();
</script>"""


def build(sls, plan_md, fragment=False):
    total = sum(s["secs"] for s in sls)
    words = sum(len([t for t in tokens(p) if t[1]]) for s in sls for p in s["paras"])
    tabs = "".join(
        f"<button data-level={k}>{html.escape(label)}</button>" for k, label, _ in LEVELS
    ) + "<button data-level=plan>Plan</button>"
    tabs += f"<span class=sp></span><button id=reveal title='Show every blank'>Reveal all</button>"
    hints = {
        "full": "Read aloud, with the deck, twice. Then move one tab right.",
        "fade5": "Say the paragraph; tap a blank only if you are stuck.",
        "fade3": "Same. Two clean passes in a row before moving on.",
        "fade2": "Same. If you miss more than one word per slide, go back a tab.",
        "letters": "The cue sheet. Recite from the letters, then cover them and recite from nothing.",
        "openers": "One word per sentence. This is the card for the day of the talk.",
    }
    body = [f"<div class=wrap><nav class=tabs>{tabs}</nav>"]
    for key, label, every in LEVELS:
        body.append(f"<div class=level id=lv-{key}><h1>{html.escape(label)}</h1>")
        body.append(f"<p class=hint>{html.escape(hints[key])}</p>")
        body.extend(render_slide(s, key, every) for s in sls)
        body.append("</div>")
    body.append(f"<div class='level plan' id=lv-plan>{pandoc(plan_md, 'html')}</div>")
    body.append(
        f"<p class=hint>{len(sls)} slides · {words} words · {clock(total)} at the "
        f"pace marked in the notes.</p></div>"
    )
    fonts = ("<link rel=stylesheet href='https://fonts.googleapis.com/css2?"
             "family=Source+Sans+3:wght@400;700&family=Source+Code+Pro&display=swap'>")
    inner = f"<title>Talk drill</title><style>{CSS}</style>" + "\n".join(body) + JS
    if fragment:
        return fonts + inner
    return ("<!doctype html>\n<html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width, initial-scale=1'>"
            f"</head><body>{inner}</body></html>\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragment", metavar="FILE",
                    help="write body-only HTML here instead of cards/drill.html")
    args = ap.parse_args()
    sls = slides(QMD.read_text())
    if not sls:
        sys.exit("no slides with notes found in index.qmd")
    plan_md = PLAN.read_text() if PLAN.exists() else "# Plan\n\n(no drill-plan.md)"
    if args.fragment:
        Path(args.fragment).write_text(build(sls, plan_md, fragment=True))
        print(f"wrote {args.fragment}")
    else:
        OUT.write_text(build(sls, plan_md))
        print(f"wrote {OUT.relative_to(ROOT)}: {len(sls)} slides")


if __name__ == "__main__":
    main()
