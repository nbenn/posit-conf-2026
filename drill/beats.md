# 1 Any shape you want

## A toy with total freedom
[[Play-doh]].

It’s a fun [toy]:
you can create any [[shape]] you want with it.

## Freedom as a burden: no help from the material
To me [personally] though,
that much freedom always felt more like a [[burden]].

You don’t get much [[assistance]] from the material.

## So, lego
! I gravitated more towards [[lego]].

# 2 What carries over to your next app?

## Thesis: restrictions made me more creative
[[Restrictions]] and well-defined interfaces helped me be more creative.

## Pressing versus studs: assembly is built in
Two [[lumps]] of play-doh assemble however you press them together.

[[Assembly]] of two bricks on the other hand is mediated by studs.

## The trade: freedom for reuse, attention on the model
On the [[surface]],
lego [costs] you freedom.

There are [[shapes]] you simply cannot build.

What you get back is [[reuse]],
and with shaping [constraints],
you can spend your [attention] on the model instead of the material.

## Us: a consultancy, tailor-made apps, clay
Much of this [[applies]] to what we do.

I work at a small [[consultancy]],
and we have built a lot of [Shiny] apps over the years.

Every project felt like it needed to be [[tailor-made]],
so we ended up solving [similar] problems over and over again.

[[Code]] bases grew large and hard to change.

[[Clay]], basically.

## The question: what carries over?
Now how can we [[improve]]?

How can we have [[components]] carry over from one app to the next?

## The answer: limit the shape, define the interface
One way is by imposing [[restrictions]].

! If we [[limit]] the shape by defining an interface,
this [enables] reuse.

It lets you [[focus]] on what matters.

! And it applies to humans and current-gen coding [[assistants]] alike.

# 3 A block

## Define the block
The core [abstraction] we built for blockr is a block:
a well-defined [[unit]] of computation.

## Links and stacks
Blocks are connected by [[links]]
and can be assembled into [stacks].

## The contract: inputs, parameters, one output
! Each block has data [[inputs]],
user [parameters]
and a single [output].

! That is the whole [[contract]].

## Brick, stud, model: the stud is the interface
! The block is the [[brick]],
the link is the [stud]
and the stack is the [model].

! The stud is our [[interface]]:
simple and [well-defined].

# 4 A real app

## Where: BMS, clinical study data
We are using blockr at [[Bristol-Myers Squibb]]
to explore [clinical] data from studies.

## Docking panels you can move and resize
Our [[frontend]] here is built on a docking layout manager
and we have every block render a [panel] you can move and resize freely.

## Scale: a hundred blocks, a dozen views, many apps
These apps pull in up to one [[hundred]] blocks,
spread over a dozen [views].

And we’re [[rolling]] out many such apps,
specific to studies and their analysis [needs].

## Two extensions: overview on the left, assistant on the right
[[Blocks]] are not the only extension point.

There are [[extensions]] as well:

(1) On the [left],
we have a [[graphical]] overview,
showing blocks, their [connections] and stack membership.

(2) And on the [right],
an [[AI]] assistant,
which can [manipulate] and interrogate our app.

## Most blocks are general; one was built for this: the profile
Most blocks here are [[general]] purpose:
[reading] data,
[transforming] it,
displaying summary [tables] and visualizations that support drill-down.

! (3) But one block was built [specifically] for this use case:
the [[patient profile]] you can see in the middle.

# 5 Specialty pieces

## The library cannot cover everything
Our current [[library]] of general-purpose blocks
cannot [cover] every use case.

## Specialty pieces: a special shape, the standard studs
Similar to [[specialty]] pieces that come with certain lego sets,
sometimes you want a specific [shape],
which still comes with the [standard] studs.

## Hand-off: your own block, and here is one
We made it [[easy]] for you to do just that
by [integrating] your own blocks into a blockr app.

! Here’s what one [[looks]] like.

# 6 Anatomy of a block

## Name it
The [[head]] block:

## Parameters, seeded from the constructor
(1) First are user [[parameters]]:
here we need only one, [n].

(2) It is [[seeded]] by the corresponding constructor argument.

## Inputs
(3) Next are data [[inputs]]:
we again have only a single one: [x].

## The output is an expression, computed on demand
(4) The data [[output]] is represented by an expression,
so the result can be computed [on demand] from input data.

## State, to save and restore
! (5) And finally we return [[state]]:
this allows us to [save] and restore.

# 7 Build a block.

## The ask: build a block, by hand or with an assistant
Now it’s your [[turn]]:
build a [block].

Either by [hand],
or by pointing a coding assistant at the many [[examples]] we have created.

## The takeaway: what you don’t have to decide
! And [[look]] out for what you don’t have to decide.

! That’s normally the [[expensive]] part of making something reusable.

## Thanks
I’d like to thank my four [[collaborators]] for their contributions
– and you for your [attention].

## No Q&A: come find me
Unfortunately we don’t get a [[Q&A]].

! So if you have [[questions]] for me,
want to see or [hear] more,
come [find] me.
