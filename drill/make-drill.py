#!/usr/bin/env python3
"""Memorisation drill sheets, generated from the speaker notes in index.qmd
and the beat annotations in drill/beats.md.

Seven views of the talk, one per rung of the ladder in drill/plan.md:

    full       the notes as written, to read aloud
    beats      one line per beat saying what it does, the sentences hidden
    letters    one line per clause, the keyword whole, every other word an initial
    clauses    one line per clause, only its keyword showing
    sentences  one keyword per sentence
    joins      cards: the end of a sentence in front, the next sentence behind
    starts     draw a slide, a beat or a sentence and go on to the end of the slide
    nothing    the slide picture alone, plus the whole talk as first letters
    paper      the talk as written, one sentence per line, to print and mark slips on

The annotations live in drill/beats.md, the notes split by hand:

    # 3 A block                          a slide, in deck order
    ## The contract                      a beat, and what it does, one line
    Each block has data [inputs],        one clause per line, one keyword each
    and a single [[output]].             [[..]] marks the sentence keyword
    ! That is the whole [[contract]].    ! marks a sentence where a slip would show

A sentence ends at a full stop, question or exclamation mark, at a blank line
or at a beat heading. The words are checked against the notes in index.qmd and the build fails if they drift,
so the annotations cannot lag the deck. After a rewrite, `--template` prints
a fresh, unannotated split of the notes to start from.

    python3 drill/make-drill.py                  # -> drill/index.html
    python3 drill/make-drill.py --template       # the notes split, no keywords
    python3 drill/make-drill.py --fragment out    # body only, for embedding

Needs pandoc on the PATH, as cards/make-cards.py does. Published with the
deck as /drill/, see _quarto.yml; the pictures come from cards/thumbs/.
"""

import argparse
import html
import json
import random
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
QMD = ROOT / "index.qmd"
BEATS = HERE / "beats.md"
PLAN = HERE / "plan.md"
OUT = HERE / "index.html"

# Slide pictures, captured by cards/make-cards.py. Position 1 in the deck is
# the title slide, so notes slide n is slide-{n+1:02d}.jpg.
THUMBS = "../cards/thumbs"

LEVELS = ["full", "beats", "letters", "clauses", "sentences", "joins", "starts",
          "nothing", "paper"]
LABELS = {
    "full": "Full", "beats": "Beats", "letters": "Letters", "clauses": "Clauses",
    "sentences": "Sentences", "joins": "Joins", "starts": "Starts",
    "nothing": "Nothing", "paper": "Paper",
}
HINTS = {
    "full": "Read aloud with the deck, twice. Then close it and tell each "
            "slide in your own words: what it argues, not what it says.",
    "beats": "One line per beat: what it does. Say the beat from that line, "
             "then tap it to check.",
    "letters": "Every word as its first letter, the keyword whole. Recite as "
               "written; the letters are the check. Tap a line to see it whole.",
    "clauses": "One line per clause, keyword only. Bold is the sentence "
               "keyword. Recite as written, then tap a line to check it.",
    "sentences": "One keyword per sentence. Tap to check. A dot marks a "
                 "sentence where a slip would show.",
    "joins": "The end of a sentence. Say the next one, then Show. Missed "
             "sends the card to the back of the deck.",
    "starts": "Draw a slide, a beat or a sentence, and go on from there to "
              "the end of the slide. Then Show.",
    "nothing": "The picture and the clicker, nothing else. Tap the picture "
               "to check. The pocket check at the end is the whole talk as "
               "first letters, for the day itself.",
    "paper": "The talk as written, one sentence per line, numbered as on the "
             "other sheets. Print this tab on two pages and mark each slip on it.",
}

e = html.escape


def pandoc(text, to, *opts):
    out = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", to, "--wrap=none", *opts],
        input=text, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def plain(md):
    """Markdown to plain text on one line; the words are what is drilled."""
    return re.sub(r"\s+", " ", pandoc(md, "plain")).strip()


# --- the deck ------------------------------------------------------------------

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


WORD = re.compile(r"^([^\w]*)(\w[\w'’\-]*)(.*)$", re.U)


def tokens(text):
    """Split into (lead, core, tail) triples; core is the word itself."""
    out = []
    for tok in text.split(" "):
        m = WORD.match(tok)
        out.append(m.groups() if m else ("", "", tok))
    return out


def words(text):
    """The words alone, for comparing the two sources."""
    return re.findall(r"\w[\w'\-]*", text.replace("’", "'").lower())


# --- the annotations -------------------------------------------------------------

MARK = re.compile(r"\[\[([^\]]+)\]\]|\[([^\]]+)\]")
SENT_END = re.compile(r"[.!?][\"”’)]*$")


def parse_beats(src):
    """Slides, each a list of beats, each a list of sentences made of clauses."""
    out, slide, beat, sent = [], None, None, None

    def end_sentence():
        nonlocal sent
        if sent:
            if sum(c["sk"] for c in sent["clauses"]) != 1:
                sys.exit("beats.md: a sentence needs exactly one [[keyword]]: "
                         + repr(" ".join(c["text"] for c in sent["clauses"])))
            sent["key"] = next(c["key"] for c in sent["clauses"] if c["sk"])
            sent["text"] = " ".join(c["text"] for c in sent["clauses"])
            beat["sents"].append(sent)
        sent = None

    def end_beat():
        nonlocal beat
        end_sentence()
        if beat and beat["sents"]:
            slide["beats"].append(beat)
        beat = None

    for no, raw in enumerate(src.split("\n"), 1):
        line = raw.strip()
        if line.startswith("# "):
            end_beat()
            if slide:
                out.append(slide)
            m = re.match(r"# (\d+)\s*(.*)", line)
            if not m:
                sys.exit(f"beats.md:{no}: a slide heading needs its number: {line!r}")
            slide = {"n": int(m.group(1)), "title": m.group(2), "beats": []}
        elif line.startswith("## "):
            if slide is None:
                sys.exit(f"beats.md:{no}: a beat before any slide heading")
            end_beat()
            beat = {"purpose": line[3:].strip(), "sents": []}
        elif not line:
            end_sentence()
        else:
            if beat is None:
                sys.exit(f"beats.md:{no}: text before any beat heading")
            protected = line.startswith("!")
            if protected:
                line = line[1:].strip()
            marks = list(MARK.finditer(line))
            if len(marks) != 1:
                sys.exit(f"beats.md:{no}: one [keyword] per clause: {line!r}")
            m = marks[0]
            key = m.group(1) or m.group(2)
            pre, post = line[:m.start()], line[m.end():]
            if "[" in pre + post or "]" in pre + post:
                sys.exit(f"beats.md:{no}: a stray bracket outside the keyword: {line!r}")
            if sent is None:
                sent = {"clauses": [], "protected": False}
            sent["protected"] = sent["protected"] or protected
            sent["clauses"].append({
                "pre": pre, "key": key, "post": post,
                "sk": m.group(1) is not None, "text": pre + key + post,
            })
            if SENT_END.search(post):
                end_sentence()
    end_beat()
    if slide:
        out.append(slide)
    return out


def check(annotated, deck):
    """The annotated notes must carry the deck's words, slide for slide."""
    if len(annotated) != len(deck):
        sys.exit(f"beats.md has {len(annotated)} slides, index.qmd has {len(deck)}")
    for a, d in zip(annotated, deck):
        if a["n"] != d["n"]:
            sys.exit(f"beats.md: slide {a['n']} sits at position {d['n']}")
        have = words(" ".join(s["text"] for b in a["beats"] for s in b["sents"]))
        want = words(" ".join(d["paras"]))
        if have != want:
            i = next((i for i, (x, y) in enumerate(zip(have, want)) if x != y),
                     min(len(have), len(want)))
            lo = max(0, i - 4)
            sys.exit(
                f"beats.md drifts from index.qmd on slide {d['n']} "
                f"({d['title']}) at word {i + 1}:\n"
                f"  beats.md:  ... {' '.join(have[lo:i + 5])}\n"
                f"  index.qmd: ... {' '.join(want[lo:i + 5])}"
            )
        if a["title"] != d["title"]:
            print(f"note: slide {d['n']} is titled {d['title']!r} in the deck, "
                  f"{a['title']!r} in beats.md", file=sys.stderr)


def template(sls):
    """The notes split into sentences and clauses, one per line, unannotated."""
    out = []
    for sl in sls:
        out.append(f"# {sl['n']} {sl['title']}\n\n## (what this beat does)")
        for p in sl["paras"]:
            for s in re.split(r"(?<=[.!?])\s+(?=[(\"“A-Z])", p):
                out.append("\n" + "\n".join(re.split(r"(?<=[,;:])\s+|\s+(?=–)", s)))
        out.append("")
    return "\n".join(out)


# --- the views -------------------------------------------------------------------

def clock(s):
    return f"{s // 60}:{s % 60:02d}"


def dot(s):
    return "<span class=dot title='a slip here would show'></span>" if s["protected"] else ""


def sent_html(s):
    """A sentence as running text, its keyword bold."""
    return " ".join(
        f"{e(c['pre'])}<b class=k>{e(c['key'])}</b>{e(c['post'])}" if c["sk"]
        else e(c["text"])
        for c in s["clauses"]
    )


def thumb(sl):
    return f"{THUMBS}/slide-{sl['n'] + 1:02d}.jpg"


def head(sl):
    return (
        f"<div class=head><span class=num>{sl['n']}</span>"
        f"<span class=title>{e(sl['title'])}</span>"
        f"<span class=time>{clock(sl['start'])} · {sl['secs']}s</span></div>"
    )


def view_full(sl, screen=False):
    out = f"<div class=screen>{e(sl['screen'])}</div>" if screen and sl["screen"] else ""
    return out + "".join(f"<p>{e(p)}</p>" for p in sl["paras"])


def view_beats(sl):
    out = []
    for b in sl["beats"]:
        body = " ".join(dot(s) + sent_html(s) for s in b["sents"])
        out.append(
            f"<div class='beat rv'><div class=purpose>{e(b['purpose'])}</div>"
            f"<div class='hid body'><p>{body}</p></div></div>"
        )
    return "".join(out)


def initials(text):
    """Every word cut to its first letter, punctuation and markers kept."""
    return " ".join(
        lead + core + tail if not core or core.isdigit() else lead + core[0] + tail
        for lead, core, tail in tokens(text)
    )


def view_clauses(sl, ini=False):
    """One line per clause: the keyword, and either nothing else or initials."""
    def part(text):
        hid = f"<span class=hid>{e(text)}</span>"
        return f"<span class=ini>{e(initials(text))}</span>{hid}" if ini else hid

    out, n = [], 0
    for b in sl["beats"]:
        out.append(f"<div class=purpose-h>{e(b['purpose'])}</div>")
        for s in b["sents"]:
            n += 1
            rows = []
            for i, c in enumerate(s["clauses"]):
                lead = f"<span class=n>{n}</span>{dot(s)}" if i == 0 else ""
                rows.append(
                    f"<div class='cl rv{' sub' if i else ''}'>{lead}{part(c['pre'])}"
                    f"<span class='k{' sk' if c['sk'] else ''}'>{e(c['key'])}</span>"
                    f"{part(c['post'])}</div>"
                )
            out.append(f"<div class=sent>{''.join(rows)}</div>")
    return "".join(out)


def view_sentences(sl):
    out, n = [], 0
    for b in sl["beats"]:
        out.append(f"<div class=purpose-h>{e(b['purpose'])}</div><ol class=sk start={n + 1}>")
        for s in b["sents"]:
            n += 1
            out.append(
                f"<li class=rv>{dot(s)}<span class=k>{e(s['key'])}</span>"
                f"<span class=hid> · {sent_html(s)}</span></li>"
            )
        out.append("</ol>")
    return "".join(out)


def view_nothing(sl):
    return (
        f"<div class='shot rv'><img src='{thumb(sl)}' alt=''>"
        f"<div class='hid notes'>{view_full(sl)}</div></div>"
    )


def letters(text):
    """First letter of every word, the rest of the word behind a tap."""
    parts = []
    for lead, core, tail in tokens(text):
        if not core or re.fullmatch(r"\d+", core):
            parts.append(e(lead + core + tail))
        else:
            parts.append(
                f"{e(lead)}<span class='w rv'>{e(core[0])}"
                f"<span class=hid>{e(core[1:])}</span></span>{e(tail)}"
            )
    return " ".join(parts)


def pocket(sls):
    """The whole talk as first letters, one sentence per line, by slide."""
    groups = []
    for sl in sls:
        rows = "".join(
            f"<div class=pk>{dot(s)}{letters(s['text'])}</div>"
            for b in sl["beats"] for s in b["sents"]
        )
        groups.append(
            f"<div class=pks><div class=pkh><span class=num>{sl['n']}</span> "
            f"{e(sl['title'])}</div>{rows}</div>"
        )
    return (
        "<section class='slide pocket'>"
        "<div class=head><span class=title>Pocket check</span></div>"
        "<p class=hint>The whole talk as first letters, one sentence per line. "
        "A dot marks a sentence where a slip would show. Tap a letter for its "
        "word.</p><div class=pkb>" + "".join(groups) + "</div></section>"
    )


def join_cards(sls):
    """Every consecutive pair of sentences, across slides as well."""
    flat = [(sl, s) for sl in sls for b in sl["beats"] for s in b["sents"]]
    cards = []
    for (sa, a), (sb, b) in zip(flat, flat[1:]):
        last = a["clauses"][-1]["text"]
        front = ("… " if len(a["clauses"]) > 1 else "") + last
        cards.append({
            "s": sa["n"], "front": e(front), "click": sa is not sb,
            "bs": sb["n"], "title": e(sb["title"]), "back": dot(b) + sent_html(b),
        })
    return cards


def view_joins(cards, sls):
    opts = "<option value=all>All slides</option>" + "".join(
        f"<option value={sl['n']}>{sl['n']} · {e(sl['title'])}</option>" for sl in sls
    )
    deck = (
        "<div class=deck>"
        f"<div class=deckbar><select id=deck-filter>{opts}</select>"
        "<span id=deck-pos></span><span class=sp></span>"
        "<button class=big id=deck-shuffle>Shuffle</button></div>"
        "<div class=card id=card></div>"
        "<div class=deckbtns><button class='big primary' id=deck-show>Show</button>"
        "<button class=big id=deck-miss>Missed</button>"
        "<button class=big id=deck-next>Next</button></div>"
        "<p class=hint>Keys: space shows, then goes on; m marks a miss.</p></div>"
    )
    # Printed, the cards come out shuffled with a fixed seed: in deck order the
    # back of one card is the front of the next, which is reading, not recall.
    order = list(range(len(cards)))
    random.Random(2026).shuffle(order)
    rows = "".join(
        f"<tr><td><span class=tag>slide {cards[i]['s']}</span>{cards[i]['front']}"
        f"{' <span class=click>click</span>' if cards[i]['click'] else ''}</td>"
        f"<td>{cards[i]['back']}</td></tr>"
        for i in order
    )
    table = ("<p class='hint print-only'>Shuffled. Cover the right column.</p>"
             f"<table class=joins-print>{rows}</table>")
    return deck + table


def view_starts():
    return (
        "<div class=starts><div class=startbtns>"
        "<button class='big primary' data-start=slide>Draw a slide</button>"
        "<button class='big primary' data-start=beat>Draw a beat</button>"
        "<button class='big primary' data-start=sentence>Draw a sentence</button></div>"
        "<div class=card><div id=start-prompt><span class=tag>Draw something.</span></div>"
        "<div class=back id=start-answer hidden></div></div>"
        "<div class=deckbtns><button class=big id=start-show>Show</button></div></div>"
    )


def data(sls, cards):
    """What the joins deck and the starts panel need, embedded as JSON."""
    return {
        "slides": [{
            "n": sl["n"], "title": e(sl["title"]), "thumb": thumb(sl),
            "notes": view_full(sl),
            "beats": [
                {"purpose": e(b["purpose"]),
                 "from": sum(len(x["sents"]) for x in sl["beats"][:i])}
                for i, b in enumerate(sl["beats"])
            ],
            "sents": [
                {"key": e(s["key"]), "html": dot(s) + sent_html(s)}
                for b in sl["beats"] for s in b["sents"]
            ],
        } for sl in sls],
        "cards": cards,
    }


def view_paper(sl):
    """One numbered sentence per line, a small gap where a new beat starts."""
    out, n = [], 0
    for bi, b in enumerate(sl["beats"]):
        for si, s in enumerate(b["sents"]):
            n += 1
            nb = " nb" if si == 0 and bi else ""
            out.append(f"<div class='ps{nb}'><span class=n>{n}</span>{dot(s)}{sent_html(s)}</div>")
    return "".join(out)


def paper_head(sls, nwords, total):
    blank = "<span class=blank></span>"
    return (
        f"<div class=paper-h><span>{nwords} words · {clock(total)} at pace</span>"
        f"<span class=sp></span><span>Run{blank}Time{blank}Slips{blank}</span></div>"
    )


def render_slide(sl, inner, cls=""):
    return (f"<section class='slide{' ' + cls if cls else ''}'>{head(sl)}"
            f"<div class=notes>{inner}</div></section>")


CSS = """
/* The deck's greys. Dark is a real palette, not an inversion. */
:root { --ink: #1a1a1a; --mute: #707070; --line: #d4d4d4; --paper: #fff; --tab: #ededed; }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ink: #e8e8e6; --mute: #9a9a9a; --line: #3a3b3f; --paper: #151618; --tab: #26272b;
  }
}
:root[data-theme="dark"] {
  --ink: #e8e8e6; --mute: #9a9a9a; --line: #3a3b3f; --paper: #151618; --tab: #26272b;
}
* { box-sizing: border-box; }
[hidden] { display: none !important; }
body {
  margin: 0; background: var(--paper); color: var(--ink);
  font-family: "Source Sans 3", "Source Sans Pro", "Helvetica Neue", Arial, sans-serif;
  font-size: 15px; line-height: 1.45;
}
.wrap { max-width: 720px; margin: 0 auto; padding: 12px 16px 60px; }
nav.tabs {
  position: sticky; top: 0; background: var(--paper); z-index: 2;
  display: flex; flex-wrap: wrap; gap: 6px; padding: 8px 0 10px;
  border-bottom: 1px solid var(--line); margin-bottom: 12px;
}
nav.tabs button, button.big, select {
  font: inherit; font-size: 13px; padding: 5px 10px; border-radius: 999px;
  border: 1px solid var(--line); background: var(--tab); color: var(--ink);
  cursor: pointer;
}
nav.tabs button.on, button.primary { background: var(--ink); color: var(--paper); border-color: var(--ink); }
button:focus-visible, select:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
.sp { flex: 1; }
.level { display: none; }
.level.on { display: block; }
.hint { color: var(--mute); font-size: 13px; margin: 0 0 14px; }
.slide { margin: 0 0 26px; }
.head {
  display: flex; align-items: baseline; gap: 8px;
  border-bottom: 2px solid var(--ink); padding-bottom: 3px; margin-bottom: 6px;
}
.num {
  font-size: 11px; font-weight: 700; color: var(--paper); background: var(--ink);
  border-radius: 3px; padding: 1px 5px;
}
.title { font-weight: 700; flex: 1; }
.time { font-size: 13px; font-weight: 700; color: var(--mute); white-space: nowrap; }
.screen { font-size: 13px; color: var(--mute); margin-bottom: 8px; }
.notes p { margin: 0 0 9px; }
/* Anything with class rv reveals its hidden parts when tapped. */
.hid { display: none; }
.rv { cursor: pointer; }
.rv.on > .hid, body.reveal .hid { display: revert; }
.rv.on > .ini, body.reveal .ini { display: none; }
.k { font-weight: 700; }
.dot {
  display: inline-block; width: 6px; height: 6px; border-radius: 50%;
  background: var(--ink); margin: 0 6px 2px 0; vertical-align: middle;
}
/* Beats */
.beat { border-left: 2px solid var(--line); padding: 3px 12px; margin: 0 0 8px; }
.beat.on { border-left-color: var(--ink); }
.purpose { font-weight: 700; }
.beat .body p { margin: 4px 0 2px; }
/* Clauses and sentences */
.purpose-h {
  font-size: 12px; font-weight: 700; color: var(--mute); text-transform: uppercase;
  letter-spacing: .04em; margin: 12px 0 3px;
}
.sent { margin: 0 0 7px; }
.cl { position: relative; padding: 1px 0 1px 28px; }
.cl.sub { padding-left: 46px; }
.cl .n {
  position: absolute; left: 0; top: 4px; width: 22px; text-align: right;
  font-size: 11px; color: var(--mute);
}
.cl .k { font-weight: 400; }
.cl .k.sk { font-weight: 700; }
.cl.on .k { text-decoration: underline; text-decoration-color: var(--mute); text-underline-offset: 3px; }
ol.sk { margin: 0; padding-left: 26px; }
ol.sk li { padding: 1px 0; }
/* Cards, for the joins deck and the starts panel */
.card { border: 1px solid var(--line); border-radius: 8px; padding: 14px 16px; min-height: 120px; max-width: 560px; }
.front { font-size: 18px; }
.tag { display: block; font-size: 12px; color: var(--mute); margin-bottom: 4px; }
.click {
  display: inline-block; font-size: 11px; font-weight: 700; padding: 0 7px;
  border: 1px solid var(--ink); border-radius: 999px; vertical-align: 2px;
}
.back { border-top: 1px solid var(--line); margin-top: 12px; padding-top: 10px; font-size: 16px; }
.card p { margin: 0 0 6px; }
.deckbar, .deckbtns, .startbtns { display: flex; align-items: center; gap: 8px; margin: 0 0 10px; max-width: 560px; }
.deckbtns { margin-top: 10px; }
#deck-pos { font-size: 13px; color: var(--mute); }
.done { color: var(--mute); }
#start-prompt img { display: block; width: 100%; max-width: 360px; margin-top: 6px; border: 1px solid var(--line); }
#start-prompt .key { font-size: 26px; font-weight: 700; margin: 4px 0; }
#start-prompt .purpose { font-size: 18px; margin: 4px 0; }
/* Nothing */
.shot img { display: block; width: 100%; max-width: 360px; border: 1px solid var(--line); }
.shot .notes { margin-top: 8px; }
.pks { margin: 0 0 12px; }
.pkh { font-weight: 700; margin: 0 0 3px; }
.pk { margin: 0 0 4px; }
.w { white-space: nowrap; }
.pocket { margin-top: 30px; }
.print-only, .joins-print { display: none; }
/* Paper */
.ps { position: relative; padding: 1px 0 1px 28px; }
.ps .n {
  position: absolute; left: 0; top: 4px; width: 22px; text-align: right;
  font-size: 11px; color: var(--mute);
}
.ps.nb { margin-top: 6px; }
.paper-h {
  display: flex; gap: 12px; font-size: 13px; color: var(--mute);
  border-bottom: 1px solid var(--line); padding-bottom: 6px; margin-bottom: 14px;
}
.blank { display: inline-block; width: 52px; border-bottom: 1px solid var(--mute); margin: 0 12px 0 4px; }
/* Plan */
.plan h1 { font-size: 20px; margin: 0 0 8px; }
.plan h2 { font-size: 16px; margin: 20px 0 6px; }
.plan h3 { font-size: 15px; margin: 14px 0 4px; }
.plan ul { padding-left: 22px; margin: 4px 0 8px; }
.plan li { margin: 2px 0; }
.plan code { font-family: "Source Code Pro", monospace; font-size: 0.92em; }
@media screen { .level > h1.lv { display: none; } }
@media print {
  @page { size: A4; margin: 14mm; }
  :root { --ink: #111; --mute: #666; --line: #ccc; --paper: #fff; --tab: #fff; }
  body { font-size: 11pt; }
  .wrap { max-width: none; padding: 0; }
  nav.tabs, .deck, #lv-starts { display: none; }
  .level { display: block; page-break-before: always; }
  .level:first-of-type { page-break-before: auto; }
  /* Print this tab: only the open level, starting on the first page. */
  body.one .level:not(.on) { display: none; }
  body.one .level { page-break-before: auto; }
  #lv-paper > h1.lv, #lv-paper > .hint { display: none; }
  #lv-paper { font-size: 10.5pt; line-height: 1.5; }
  #lv-paper .slide { margin: 0 0 4mm; }
  #lv-paper .slide.pbreak { page-break-before: always; }
  #lv-paper .head { margin-bottom: 1.5mm; }
  .ps { padding: 0 24mm 0 8mm; }
  .ps .n { width: 6mm; top: 0; font-size: 8pt; }
  .ps.nb { margin-top: 2mm; }
  .paper-h { color: var(--ink); font-size: 10pt; margin-bottom: 4mm; }
  .blank { width: 18mm; border-bottom-color: var(--ink); margin: 0 5mm 0 1.5mm; }
  .level > h1.lv { font-size: 14pt; margin: 0 0 6pt; }
  .slide { page-break-inside: avoid; }
  .hid, .rv.on > .hid { display: none; }
  .rv.on > .ini { display: inline; }
  #lv-beats .hid { display: revert; }
  .print-only { display: block; }
  .joins-print { display: table; width: 100%; border-collapse: collapse; font-size: 10pt; }
  .joins-print td {
    vertical-align: top; width: 50%; padding: 4pt 6pt;
    border-bottom: 1px solid var(--line); page-break-inside: avoid;
  }
  .shot img { max-width: 70mm; }
  .pocket { page-break-before: always; border: 1px dashed var(--mute); padding: 5mm; }
  .pkb { columns: 2; column-gap: 8mm; font-size: 9pt; line-height: 1.3; }
  .pks { break-inside: avoid; }
}
"""

JS = """<script>
(function () {
  const $ = s => document.querySelector(s);
  const $$ = s => Array.from(document.querySelectorAll(s));
  const D = JSON.parse($('#data').textContent);

  // Tabs. The last one used comes back on reload.
  const tabs = $$('nav.tabs button[data-level]'), levels = $$('.level');
  function show(id) {
    tabs.forEach(b => b.classList.toggle('on', b.dataset.level === id));
    levels.forEach(l => l.classList.toggle('on', l.id === 'lv-' + id));
    try { localStorage.setItem('drill-level', id); } catch (e) {}
    document.body.classList.remove('reveal');
  }
  tabs.forEach(b => b.addEventListener('click', () => show(b.dataset.level)));
  $('#reveal').addEventListener('click', () => document.body.classList.toggle('reveal'));
  let start = location.hash.slice(1);
  if (!$('#lv-' + start)) {
    start = 'full';
    try { start = localStorage.getItem('drill-level') || start; } catch (e) {}
  }
  show($('#lv-' + start) ? start : 'full');
  $('#print1').addEventListener('click', () => {
    document.body.classList.add('one');
    window.print();
  });
  window.addEventListener('afterprint', () => document.body.classList.remove('one'));

  // Anything with class rv reveals its hidden parts when tapped.
  document.addEventListener('click', e => {
    if (e.target.closest('button, select, a')) return;
    const r = e.target.closest('.rv');
    if (r) r.classList.toggle('on');
  });

  // Joins: a shuffled deck, one card at a time; a miss goes to the back.
  const deck = { order: [], i: 0, shown: false, missed: 0 };
  const filter = $('#deck-filter');
  function shuffle(a) {
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    return a;
  }
  function restart() {
    const f = filter.value;
    deck.order = shuffle(D.cards.map((c, i) => i)
      .filter(i => f === 'all' || String(D.cards[i].s) === f));
    deck.i = 0; deck.missed = 0;
    draw();
  }
  function draw() {
    const card = $('#card'), c = D.cards[deck.order[deck.i]];
    deck.shown = false;
    if (!c) {
      card.innerHTML = '<p class=done>Through the deck. ' + deck.missed +
        ' card' + (deck.missed === 1 ? '' : 's') + ' came round twice.</p>';
      $('#deck-pos').textContent = '';
      return;
    }
    card.innerHTML =
      '<div class=front><span class=tag>slide ' + c.s + '</span>' + c.front +
      (c.click ? ' <span class=click>click</span>' : '') + '</div>' +
      '<div class=back hidden>' +
      (c.click ? '<span class=tag>slide ' + c.bs + ' · ' + c.title + '</span>' : '') +
      c.back + '</div>';
    $('#deck-pos').textContent = (deck.i + 1) + ' / ' + deck.order.length;
  }
  function reveal() {
    const b = $('#card .back');
    if (b) { b.hidden = false; deck.shown = true; }
  }
  function next(miss) {
    if (deck.i >= deck.order.length) return;
    if (miss) { deck.order.push(deck.order[deck.i]); deck.missed++; }
    deck.i++;
    draw();
  }
  $('#deck-show').addEventListener('click', reveal);
  $('#deck-next').addEventListener('click', () => next(false));
  $('#deck-miss').addEventListener('click', () => next(true));
  $('#deck-shuffle').addEventListener('click', restart);
  filter.addEventListener('change', restart);
  document.addEventListener('keydown', e => {
    if (!$('#lv-joins').classList.contains('on')) return;
    if (e.target.matches('select, input, textarea')) return;
    if (e.key === ' ' || e.key === 'Enter') {
      e.preventDefault();
      if (deck.shown) next(false); else reveal();
    } else if (e.key === 'm') {
      next(true);
    }
  });
  restart();

  // Starts: a random landmark, then everything from there to the end of the slide.
  const beats = [], sents = [];
  D.slides.forEach(s => {
    s.beats.forEach(b => beats.push({ s: s, b: b }));
    s.sents.forEach((x, i) => sents.push({ s: s, i: i }));
  });
  let last = null;
  function pick(a) {
    let x;
    do { x = a[Math.floor(Math.random() * a.length)]; } while (a.length > 1 && x === last);
    return (last = x);
  }
  function drawStart(kind) {
    const p = $('#start-prompt'), a = $('#start-answer');
    a.hidden = true;
    if (kind === 'slide') {
      const s = pick(D.slides);
      p.innerHTML = '<span class=tag>slide ' + s.n + ' · ' + s.title + '</span>' +
        '<img src="' + s.thumb + '" alt="">';
      a.innerHTML = s.notes;
    } else if (kind === 'beat') {
      const d = pick(beats);
      p.innerHTML = '<span class=tag>slide ' + d.s.n + ' · ' + d.s.title + '</span>' +
        '<p class=purpose>' + d.b.purpose + '</p>';
      a.innerHTML = '<p>' + d.s.sents.slice(d.b.from).map(x => x.html).join(' ') + '</p>';
    } else {
      const d = pick(sents);
      p.innerHTML = '<span class=tag>slide ' + d.s.n + ' · ' + d.s.title + '</span>' +
        '<p class=key>' + d.s.sents[d.i].key + '</p>';
      a.innerHTML = '<p>' + d.s.sents.slice(d.i).map(x => x.html).join(' ') + '</p>';
    }
  }
  $$('button[data-start]').forEach(b => b.addEventListener('click', () => drawStart(b.dataset.start)));
  $('#start-show').addEventListener('click', () => { $('#start-answer').hidden = false; });
})();
</script>"""


def build(sls, plan_md, fragment=False):
    cards = join_cards(sls)
    total = sum(s["secs"] for s in sls)
    nwords = sum(len([t for t in tokens(p) if t[1] and not t[1].isdigit()])
                 for s in sls for p in s["paras"])
    nsent = sum(len(b["sents"]) for s in sls for b in s["beats"])
    tabs = "".join(f"<button data-level={k}>{LABELS[k]}</button>" for k in LEVELS)
    tabs += ("<button data-level=plan>Plan</button><span class=sp></span>"
             "<button id=reveal title='Show everything hidden'>Reveal all</button>"
             "<button id=print1 title='Print only the open tab'>Print this tab</button>")
    views = {
        "full": lambda sl: view_full(sl, screen=True),
        "beats": view_beats, "letters": lambda sl: view_clauses(sl, ini=True),
        "clauses": view_clauses,
        "sentences": view_sentences, "nothing": view_nothing,
    }
    body = [f"<div class=wrap><nav class=tabs>{tabs}</nav>"]
    for k in LEVELS:
        body.append(f"<div class=level id=lv-{k}><h1 class=lv>{LABELS[k]}</h1>"
                    f"<p class=hint>{e(HINTS[k])}</p>")
        if k == "joins":
            body.append(view_joins(cards, sls))
        elif k == "starts":
            body.append(view_starts())
        elif k == "paper":
            # Two pages: the break falls before the first slide that starts in
            # the second half of the sentences.
            body.append(paper_head(sls, nwords, total))
            cum, broken = 0, False
            for sl in sls:
                cls = ""
                if not broken and cum >= nsent / 2:
                    cls, broken = "pbreak", True
                body.append(render_slide(sl, view_paper(sl), cls))
                cum += sum(len(b["sents"]) for b in sl["beats"])
        else:
            body.extend(render_slide(sl, views[k](sl)) for sl in sls)
            if k == "nothing":
                body.append(pocket(sls))
        body.append("</div>")
    body.append(f"<div class='level plan' id=lv-plan>{pandoc(plan_md, 'html')}</div>")
    body.append(
        f"<p class=hint>{len(sls)} slides · {nwords} words · {nsent} sentences · "
        f"{clock(total)} at the pace marked in the notes.</p></div>"
    )
    blob = json.dumps(data(sls, cards), ensure_ascii=False).replace("</", "<\\/")
    body.append(f"<script type=application/json id=data>{blob}</script>")
    fonts = ("<link rel=stylesheet href='https://fonts.googleapis.com/css2?"
             "family=Source+Sans+3:wght@400;700&family=Source+Code+Pro&display=swap'>")
    inner = f"<title>Talk drill</title><style>{CSS}</style>" + "\n".join(body) + JS
    if fragment:
        return fonts + inner
    return ("<!doctype html>\n<html lang=en><head><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width, initial-scale=1'>"
            f"{fonts}</head><body>{inner}</body></html>\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fragment", metavar="FILE",
                    help="write body-only HTML here instead of drill/index.html")
    ap.add_argument("--template", action="store_true",
                    help="print the notes split into lines, ready to annotate")
    args = ap.parse_args()
    sls = slides(QMD.read_text())
    if not sls:
        sys.exit("no slides with notes found in index.qmd")
    if args.template:
        print(template(sls))
        return
    annotated = parse_beats(BEATS.read_text())
    check(annotated, sls)
    for sl, a in zip(sls, annotated):
        sl["beats"] = a["beats"]
    plan_md = PLAN.read_text() if PLAN.exists() else "# Plan\n\n(no plan.md)"
    if args.fragment:
        Path(args.fragment).write_text(build(sls, plan_md, fragment=True))
        print(f"wrote {args.fragment}")
    else:
        OUT.write_text(build(sls, plan_md))
        nsent = sum(len(b["sents"]) for s in sls for b in s["beats"])
        print(f"wrote {OUT.relative_to(ROOT)}: {len(sls)} slides, {nsent} sentences")


if __name__ == "__main__":
    main()
