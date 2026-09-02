# posit::conf 2026 — lightning talk draft (5 min slot, target 4:30–4:45)

**Title (as submitted):** AI-assisted, interactive pipeline building with blockr

## Lodestar

**Question:** How do you make the next app cheaper than this one?

**Premise:** Shiny has always been a framework for rapid prototyping, and a coding
assistant accelerates that further. But the acceleration applies to *starting* —
every new app still starts from scratch.

**Answer:** By imposing restrictions — like the ones blockr imposes. Not the only
solution, not necessarily the best one, but one that has worked really well for us.

**Axis:** reuse (problem) → bounded contracts + a small stable API (mechanism) →
restrictions (cause).

## Three-layer goal

- **Learn** — well-placed restrictions are valuable: they discretize the solution
  space and save *us* from *ourselves*. The same restriction that limits the shape
  is what lets the pieces connect.
- **Do** — build your own block.
- **Feel** — recognition (we have all built the app that couldn't be taken apart
  afterwards) → surprise (the counterintuitive turn: less freedom, better apps).

## Audience

Programmers who create data apps. Not the no-code creators, not the viewers.
Consequence: the GUI is not the point, it's a consequence.

⚠ *The lego image recruits the low-code pitch whether you invite it or not. One
clause somewhere — the bricks are things you write, in R — keeps it out.*

## Beats (270 s)

### 1 · Situation — 35 s
- Shiny has always been a framework for rapid prototyping. You get something
  impressive in front of someone fast.
- A coding assistant accelerates that further.
- But no real problem is solved at prototype speed. The work is what comes after:
  feature requests, shifting understanding of the problem, fixes layered on
  workarounds.
- ⚠ *Consultancy line ("small data science consultancy, many Shiny apps over the
  years") = credibility, not common ground. One clause, not a paragraph — and only
  if it buys you belief for the demo later.*

### 2 · Complication — 35 s
- 🖼 **play-doh** — colors that started out distinct, now permanently one thing.
- Play-doh doesn't run out. It just gets browner. Every re-form mixes what used to be
  separate, and nothing un-mixes it.
- Everything is tailor-made, so nothing carries over to the next project. The logic
  you would want to reuse can't be separated from the app it grew inside.
- What accelerated is the starting. Every new app still starts from scratch.
- ⚠ *No AI line in this beat. Beat 1 established the acceleration and the image
  carries the rest — the room joins them unaided, and a connection they make
  themselves can't feel staged.*
- ⚠ *Optional: the dataset-manipulation client app, one sentence only. It's a
  garnish here, not evidence — the rewrite isn't validated and you don't have time
  to say so properly.*

### 3 · Question + hook — 20 s
- 🖼 **lego** — two different models, obviously sharing brick types.
- So: how do you make the next app cheaper than this one?
- **By taking things away.** By adding restrictions.
- The stud is the trade: the thing that limits what shapes you can build is the same
  thing that lets the pieces connect.
- Concede it out loud — you are building an approximation of the perfect shape. When
  that is acceptable, you get a material that is far easier to wield.
- ⚠ *This is the memorable line. It should be short enough to land in one breath
  and quotable enough to survive to the hallway.*

### 4 · The restriction, concretely — 70 s
- A Shiny module can have arbitrary inputs, arbitrary outputs, side effects, and
  any communication channel you care to invent.
- A block: one or more **data inputs**, some **user parameters**, exactly **one
  data output**. That's it. That's the stud.
- Join block: `x`, `y` in; join type + join columns as parameters; one table out.
- (Pseudo) code for how that block is implemented.
- ⚠ *This beat is doing double duty: it explains the restriction AND it is the only
  place the audience sees what "build a block" actually means. If the code doesn't
  make the ask feel achievable, the ask doesn't land. Biggest time risk in the talk.*

### 5 · Bridge — 35 s
- Small, well-scoped units of computation with a simple, stable API.
- So logic lives in general-purpose blocks; the framework handles communication and
  reactivity.
- The tailoring lives in configuration now, so the code carries over.
- A board is a small vocabulary: blocks, and the links between them. That turns
  authoring into assembly — and assembly doesn't take a big model.
- **This is not an impressive use of AI. That's rather the point.**
- ⚠ *"The code carries over" is the sentence connecting complication to payoff. If it
  takes more than one breath, you can't afford both ends of the argument.*
- ⚠ *Don't name the package on the slide — blockr.ai is on the way out,
  blockr.assistant on the way in. "The assistant" stays true whichever has shipped.*

### 6 · Evidence — 50 s
- A real, complex app we built.
- Almost entirely general-purpose blocks — the same ones we use across very
  different projects. **This is the central question answered, on screen.**
- **One** custom block, where the problem genuinely demanded it. Lego ships
  specialty pieces too.
- ⚠ *The custom block is the point, not a footnote: it shows the abstraction holding
  AND shows the escape hatch. That is the objection a skeptic is already forming.*
- ⚠ *Danger zone: this is where the "look how nice it is" pitch smuggles itself back
  in and eats the clock.*

### 7 · Ask + close — 25 s
- The assistant assembles. Someone still has to author the parts.
- Your turn: build a block — with a coding assistant or without, however you prefer.
- ⚠ *Say "coding assistant" here rather than just "assistant". The line before it is
  about the board assistant, and the two blur badly under one word.*
- Testimony, honestly bounded: this worked for us. YMMV — but keep the epistemic
  humility and drop the shrug.
- Landing: that's the five minutes, and there's no Q&A. There's a lot more to show,
  so come find me — I'm at this one on my own, and I'd rather talk to you than to
  my laptop.
- ⚠ *The joke needs a beat before it and none after. Land it and stop — don't add a
  thank-you that steps on it.*

## Images

Two photographs, shot as a pair — same background, same lighting — so they read as a
controlled comparison rather than two stock images.

- **Play-doh (beat 2).** Pristine colors in frame *together with* the mixed lump.
  One image then carries before and after; unopened tubs alone would only say
  "unused", and the point is irreversibility.
- **Lego (beat 3).** Two different models built from obviously shared brick types.
  Loose bricks beside a single model say *modular*; two models say *reused*, which is
  the actual claim. Build them recognizably blocky — if the shape comes out too good,
  the concession stops being honest.

## Budget check

270 s at conference pace ≈ 620–670 spoken words. Roughly 1.5 pages double-spaced.
Seven beats is already at the limit — every beat added costs one that exists.
