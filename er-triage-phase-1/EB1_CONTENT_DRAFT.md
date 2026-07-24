# What Building an Agentic AI System for ER Triage Taught Me About the Gap Between "It Works" and "It's Safe to Ship"

*Draft — EB1/EB2-NIW content angle: Agentic AI in Healthcare Product. Practitioner voice, grounded, no AI hype. For Substack/LinkedIn.*

---

Most agentic AI demos I see follow the same arc: connect a model to some tools, show it completing a multi-step task, ship it. That arc works fine for low-stakes automation. It falls apart the moment the task is "help decide how urgently a patient needs to be seen."

I spent the last several months building an AI co-pilot for ER triage nurses — not as a client engagement, as a personal engineering project, precisely because I wanted to find out where that arc breaks and what it actually takes to fix it. Three things surprised me enough to write about.

## 1. The model being right isn't the hard part. Knowing when to trust it is.

The system's core job is deceptively simple: read a nurse's free-text description of a patient's complaint, plus their vitals, and classify acuity on the standard 1–5 ESI scale — then, for anything urgent, retrieve the right clinical guideline and draft a structured brief.

GPT-4o is good at this. Give it "crushing chest pain radiating to the left arm, diaphoretic, thirty minutes" and it correctly flags a suspected STEMI essentially every time. The hard problem isn't getting the model to the right answer on the cases you tested. It's building a system that fails safely on the ones you didn't — and building the discipline to actually verify that, rather than assuming it.

Early in the build, I ran a 300-case synthetic evaluation and got 97.67% recall — every miss clustered in stroke presentations. My first instinct was to fix the retrieval layer: re-weight the embeddings, add clinical synonyms, tune the knowledge base. That would have been the wrong fix. When I actually traced it, the failure was two unrelated bugs stacked on top of each other: the evaluation script itself was sending a differently-shaped query than the production system ever sends (baking raw vitals digits into the same string as the complaint, which production never does), and separately, the live ingestion pipeline had silently dropped one document out of twenty-four — the stroke-specific guideline had simply never made it into the vector index.

Neither of those is a "the AI is wrong" problem. Both are "the system around the AI is wrong" problems. Fixing the actual bugs took the recall to 100/300 with zero changes to the model or its prompt. The instinct to blame the model — or the knowledge base — first is exactly the instinct that would have burned a week tuning something that wasn't broken.

## 2. Safety-critical prompt design means being deliberately less clever, not more

The system screens every complaint against ten emergent conditions — stroke, anaphylaxis, sepsis, suicidal ideation, and others — each requiring a confidence score before it surfaces an alert to the nurse. The obvious design is to let the model use everything available: complaint text and vitals together, weighing all the evidence.

That obvious design is unsafe. In testing, a version of the prompt that let extreme vitals count as evidence would occasionally imply a condition the complaint text never actually described — inferring "severe headache" from a patient who only said they felt "dizzy," because an elevated blood pressure reading nudged the model toward pattern-matching a hypertensive crisis. That's a hallucinated symptom, and in a clinical context, a hallucinated symptom feeding a false alert is arguably worse than a missed one — it erodes the nurse's trust in every alert that follows.

The fix wasn't a smarter prompt. It was a deliberately dumber, more rigid one: a flag can only fire if the model can quote a literal phrase from the complaint text naming the condition's defining symptom. Vitals are permitted to *corroborate* a flag already established by the text — never to establish one on their own. That constraint took several rounds to actually hold; the model kept finding ways to rationalize around it (inferring related symptoms, treating an extreme vital as sufficient on its own) until the prompt explicitly named the disqualifying reasoning pattern and forbade it directly.

The generalizable lesson: in a domain where a false positive has a real cost, the right prompt-engineering move is often to remove a degree of freedom from the model, not add one.

## 3. The best architecture decision I made this month was the one I almost shipped wrong

Two separate parts of the system needed to reason about the same clinical red flags from the same complaint text — the main triage classifier, and a second endpoint feeding the nurse-facing alert screens. They'd been built as two independent prompts, and by the time I noticed, they'd already drifted apart: one had a condition and a safety check the other didn't.

The obvious fix was to have the second endpoint just call the first one directly to reuse its answer. Obvious, and wrong: the first endpoint doesn't stop at classification — it goes on to run a retrieval step and a second model call to draft a full clinical brief. Reusing it wholesale would have meant paying for that entire downstream chain on every alert-screen request, doubling real cost for output that screen never uses, while also coupling two systems that are supposed to fail independently of each other.

The fix that shipped: pull the shared reasoning into its own callable unit, invoked internally by both callers, with neither paying for work it doesn't need. It took maybe 20% longer to build than the naive integration. Under real pressure to wrap the project and move on to the next one, that 20% was the easiest thing in the world to skip — and the thing I'd have regretted skipping most.

---

None of this required a bigger model or a cleverer prompt. It required treating the system around the model — the evaluation harness, the failure-mode analysis, the architecture's cost and coupling implications — as seriously as the model itself. That's the part of "agentic AI" that doesn't show up in a demo video, and it's the part I'd argue actually determines whether one of these systems is safe to put in front of a real user.

*Live demo, full architecture, and evaluation methodology: [er-triage-ai-co-pilot.pages.dev](https://er-triage-ai-co-pilot.pages.dev)*
