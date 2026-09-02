# posit::conf 2026 — lightning talk draft (5 min slot, target 4:30–4:45)

## Lodestar

**Question:** How do you stop a Shiny data app from rotting as it grows?

**Answer:** By imposing restrictions — like the ones blockr imposes. Not the only
solution, not necessarily the best one, but one that has worked really well for us.

**Axis:** rot (problem) → reuse + a small stable API (mechanism) → restrictions (cause).

## Three-layer goal

- **Learn** — well-placed restrictions are valuable: they discretize the solution
  space and save *us* from *ourselves*.
- **Do** — build your own block.
- **Feel** — recognition (we all got here the same way) → surprise (the
  counterintuitive turn: less freedom, better apps).
  ⚠ *Open: you also listed "thrilled at how amazing a blockr app looks vs. how
  little goes into it". That's the second value proposition. Deliberate or cut.*

## Audience

Programmers who create data apps. Not the no-code creators, not the viewers.
Consequence: the GUI is not the point, it's a consequence.

## Beats (270 s)

### 1 · Situation — 40 s
- Shiny lets you build something impressive in an afternoon.
- Most of us are not software engineers by trade. We arrived via scripting data
  analyses — simple, procedural code.
- Then suddenly we're reasoning about every possible ordering of state changes in
  an interactive app.
- ⚠ *Consultancy line ("small data science consultancy, many Shiny apps over the
  years") = credibility, not common ground. One clause, not a paragraph — and only
  if it buys you belief for the demo later.*

### 2 · Complication — 35 s
- Reasonable initial clarity. Then: feature requests, shifting understanding of the
  problem, fixes layered on hacks layered on workarounds.
- The code base spirals. Everything is tailor-made, so nothing carries over to the
  next project.
- ⚠ *Optional: the dataset-manipulation client app, one sentence only. It's a
  garnish here, not evidence — the rewrite isn't validated and you don't have time
  to say so properly.*

### 3 · Question + hook — 20 s
- So: how do we improve on an already very expressive framework?
- **By taking things away.** By adding restrictions.
- ⚠ *This is the memorable line. It should be short enough to land in one breath
  and quotable enough to survive to the hallway.*

### 4 · The restriction, concretely — 70 s
- A Shiny module can have arbitrary inputs, arbitrary outputs, side effects, and
  any communication channel you care to invent.
- A block: one or more **data inputs**, some **user parameters**, exactly **one
  data output**. That's it.
- Join block: `x`, `y` in; join type + join columns as parameters; one table out.
- (Pseudo) code for how that block is implemented.
- ⚠ *This beat is doing double duty: it explains the restriction AND it is the only
  place the audience sees what "build a block" actually means. If the code doesn't
  make the ask feel achievable, the ask doesn't land. Biggest time risk in the talk.*

### 5 · Bridge — 30 s
- Small, well-scoped units of computation with a simple, stable API.
- So logic lives in general-purpose blocks; the framework handles communication and
  reactivity; per-app work collapses to configuration.
- A well-maintained, reused component is a component that doesn't rot.
- ⚠ *This is the sentence that connects your complication to your payoff. If it
  takes more than one breath, you can't afford both ends of the argument.*

### 6 · Evidence — 50 s
- A real, complex app we built.
- Almost entirely general-purpose blocks — the same ones we use across very
  different projects.
- **One** custom block, where the problem genuinely demanded it.
- ⚠ *The custom block is the point, not a footnote: it shows the abstraction holding
  AND shows the escape hatch. That is the objection a skeptic is already forming.*
- ⚠ *Danger zone: this is where the "look how nice it is" pitch smuggles itself back
  in and eats the clock.*

### 7 · Ask + close — 25 s
- Your turn: build a block.
- Testimony, honestly bounded: this worked for us. YMMV — but keep the epistemic
  humility and drop the shrug. Warm ending, not a cold one.
- ⚠ *Needs a landing line. Yours, not mine.*

## Open decisions

1. **Beat 4 vs beat 6 for time.** 70 s + 50 s = 120 s, nearly half the talk, on the
   two beats that both need screen time. One of them will have to give.
2. **Whether "thrill at the app" stays** in the emotional goal, given it pulls
   against the restriction argument.
3. **Title.** Not discussed.
4. **The number.** Rejected, deliberately — LOC is gameable and invites dismissal.
   Nothing quantitative replaces it; the demo's shape carries the load instead.

## Budget check

270 s at conference pace ≈ 620–670 spoken words. Roughly 1.5 pages double-spaced.
Seven beats is already at the limit — every beat added costs one that exists.
