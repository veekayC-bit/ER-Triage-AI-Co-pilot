# AI Product Assessment Log
*Venkat Krishnan Chellappa — AI PM Phase Assessments*

---

## Assessment 1 — ER Patient Intake & Triage
**Date:** May 28, 2026
**Assessed by:** AI Phase Assessment Skill v2.0

---

## 🎯 AI Assessment: ER Patient Intake & Triage

**Overall Verdict: 🟡 PROCEED WITH CAUTION**

**Summary:** The core AI opportunity is real — free-text chief complaint parsing, critical flag detection, and documentation assistance are genuinely hard to do with rules and well-suited to AI. However, this is high-stakes clinical AI operating in a regulated, high-liability environment with a very high accuracy bar. The current scope is too broad for a single MVP build, bias risk in heterogeneous ER populations is non-trivial, and the FDA SaMD regulatory pathway will significantly impact timeline and cost. A narrowed first phase focused on documentation assistance and flag surfacing (not triage scoring) is the safer path.

---

### PHASE 0: Problem Framing
**Framing Quality: ⚠️ Needs sharpening**

**Current framing:** ER Triage Nurses perform patient intake daily using mixed structured/unstructured inputs across demographics, vitals, symptoms, risk flags, and clinical notes.

**What's missing:** The specific pain point isn't named. Is the problem documentation burden (nurses spending too long entering data)? Inconsistent triage decisions under cognitive load? Missed critical flags during high-volume periods? These lead to very different AI designs.

**Suggested sharper framing:**
> "ER Triage Nurses handle 50–200+ intake assessments per shift under high cognitive load. They manually synthesize structured vitals, free-text chief complaints, and physical documents to produce a triage priority and risk flag set. Under peak volume, critical flags (stroke symptoms, anaphylaxis, suicidal ideation) are at risk of being missed or delayed. The current workflow is primarily manual data entry with no AI-assisted synthesis or flagging."

---

### PART 1: Project Fit — 4/5 checks passed

| Check | Status | Key Finding |
|-------|--------|-------------|
| 1. Problem Fit | ✅ | High-frequency, high-stakes manual task — real pain, real people, real execution problem |
| 2. Is it Agentic? | ⚠️ | Reasoning + risk flagging qualifies, but mostly within-session; not strongly multi-step autonomous |
| 3. Not Rule-Based? | ✅ | Free-text chief complaint, nurse notes, and physical documents cannot be handled by rules |
| 4. MVP Scope | ⚠️ | Input list spans 9+ data categories — far too broad for a 6-week MVP; needs major scoping down |
| 5. Why Not ChatGPT? | ✅ | Requires EMR integration, structured clinical output, HIPAA compliance, and audit trail — well beyond a prompt |

---

### PART 2: ML Readiness — 6/10 green

| # | Check | Rating | Key Concern |
|---|-------|--------|-------------|
| 1 | Is ML Necessary? | 🟡 | Structured vitals fields need only forms; free-text + document parsing genuinely needs ML |
| 2 | Data Available? | 🟡 | Historical ER intake records likely exist but HIPAA constraints and labeling overhead are significant |
| 3 | ML Can Solve It? | 🟢 | Clinical NLP, named entity recognition, and risk flag detection are proven in literature and products |
| 4 | Meets Accuracy Bar? | 🟡 | Achievable as augmentation tool — full automation is off the table; human confirmation mandatory on all outputs |
| 5 | Can Scale? | 🟢 | Architecture generalises across facilities; some per-facility protocol configuration required |
| 6 | Fast Feedback? | 🟡 | Nurse override tracking provides near-real-time signal; outcome validation (was priority correct?) is slower |
| 7 | Legal / Regulatory? | 🔴 | HIPAA mandatory; likely FDA SaMD classification if AI influences triage decisions; high compliance overhead |
| 8 | Bias Risk? | 🔴 | ER populations are highly heterogeneous; healthcare AI has documented demographic bias — explicit cross-segment testing required |
| 9 | Explainability? | 🟡 | Clinicians must see why a flag was raised — achievable with citation/reasoning chains but must be designed in from day one |
| 10 | Judgeable Output? | 🟢 | Clear ground truth: nurse final decision + patient outcome; override rate is a strong quality signal |

> ⚠️ *Legal rating reflects general knowledge as of early 2026 and may not account for recent regulatory changes, jurisdiction-specific rules, or new enforcement actions. Do not treat this as legal advice — verify with a qualified healthcare compliance or legal expert before proceeding.*

---

### PART 3: AI PM Reasoning Layer

**R1 — Workflow Fit**
The design must fit invisibly into the triage workflow — nurses under pressure will not tolerate extra steps or validation clicks. The right model is AI working in the background: as the nurse enters the chief complaint, AI pre-structures it; as vitals are entered, AI surfaces risk flags in a sidebar; nurse reviews and confirms, not re-enters. Any design that adds cognitive overhead to a nurse already managing a distressed patient will be disabled or ignored within days of deployment.

**R2 — Capability Split**

| AI Should Own | Human Must Own |
|---|---|
| Free-text parsing → structured fields | Final triage priority / acuity score |
| Critical flag detection and surfacing | Clinical judgment on ambiguous presentations |
| Document ingestion (prescriptions, referrals) | Patient interaction and physical assessment |
| Documentation pre-population for review | Any action with direct patient care implications |
| Pattern recognition across combined inputs | Sign-off on all AI-generated outputs |

The split is clear: AI reduces documentation burden and surfaces signals. The nurse decides. This is non-negotiable.

**R3 — Risk & Failure Modes**

| Failure Mode | Consequence | Required Mitigation |
|---|---|---|
| False negative — misses stroke/MI/anaphylaxis flag | Patient harm, delayed care, clinical liability | Conservative recall threshold; mandatory human review; never suppress a flag silently |
| False positive fatigue — too many alerts | Nurses ignore all flags including real ones | Strict precision tuning on alert logic; track override rate as primary quality signal |
| Documentation bias — AI pre-populates incorrectly, nurse accepts | Inaccurate clinical record, downstream treatment error | All pre-populated fields shown as "suggested" with one-tap confirm; never auto-submit |
| Model drift — new presentation patterns not in training data | Silent degradation, missed emerging conditions | Monthly re-evaluation cadence; anomaly detection on input distribution shift |
| EMR integration failure | Nurses bypass tool entirely | Fallback to manual mode without data loss; integration tested in shadow mode before go-live |

**Precision vs Recall call:** For critical safety flags (stroke, anaphylaxis, chest pain, suicidal ideation) — strongly favour **recall**. Missing a real case is catastrophic; a false alarm is an extra 30 seconds of nurse attention. For documentation pre-population — favour **precision**. An incorrectly pre-filled field that gets accepted without review is a patient safety risk.

**R4 — Evaluation Design**
- **Primary metric:** Recall on critical condition flags (stroke, MI, anaphylaxis, sepsis indicators) — target ≥ 98% before clinical deployment
- **Secondary metrics:** Documentation pre-population accuracy; time-to-complete triage vs baseline; nurse satisfaction score
- **Confidence threshold:** Surface flag to nurse if confidence ≥ 70%; escalate urgency indicator if ≥ 90%
- **Human override tracking:** Mandatory from day one — every AI suggestion that a nurse accepts, modifies, or rejects is a labelled data point
- **Hallucination guard:** All AI-extracted fields from free text must cite the source string
- **Minimum bar before launch:** Shadow mode running in parallel with manual process for 30 days; critical flag recall validated by clinical expert panel on 500+ cases
- **Judge:** Clinical panel (ER physicians + nurses) + retrospective outcome matching

**R5 — Strategic Reasoning**
Why now: Clinical NLP has reached the capability threshold needed for reliable ER intake synthesis; FDA has published clearer SaMD guidance making the regulatory pathway navigable. Why this team: ER intake data generated by deployment creates a proprietary, labeled dataset that improves the model over time — this is the data moat. Workflow stickiness comes from deep EMR integration; once embedded in the triage workflow, switching is a major clinical change management project. The risk: the core AI architecture (LLM + NLP pipeline) is replicable; the defensible layer is hospital-specific fine-tuning, regulatory clearance, and clinical trust earned through deployment history.

---

### 💪 Top 3 Strengths
1. **Genuine AI-hard problem** — free-text chief complaints, nurse notes, and unstructured physical documents cannot be handled by rules; this is exactly where NLP adds irreplaceable value
2. **Built-in evaluation signal** — nurse override rate and outcome data create a continuous feedback loop that makes the model improve with use
3. **Proven analogues** — clinical triage AI (ESI decision support, sepsis detection, stroke recognition) has established literature and some FDA-cleared products; you're not in uncharted territory

### ⚠️ Top 3 Risks / Blockers
1. **Regulatory pathway (🔴)** — If AI influences triage priority, this likely classifies as FDA SaMD (potentially Class II, requiring 510(k) clearance). This is a 12–24 month and significant cost implication that is often discovered too late. Confirm classification before writing a single line of code.
2. **Demographic bias in training data (🔴)** — ER populations include elderly, paediatric, non-English speaking, and underserved patients. A model that works on the majority case and fails on edge demographics is a patient safety liability and a legal exposure.
3. **MVP scope is 10x too large** — The input specification covers 9+ data categories. Building all of this Phase 1 will take 12+ months and delay any user feedback. A focused first phase is essential.

### 🔜 Recommended Next Steps Before Moving to Next Phase
- **Narrow Phase 1 scope radically** — start with: (1) chief complaint free-text parsing only, (2) critical flag detection from the 10 risk conditions listed, (3) nurse note assistance. Leave vitals capture, medication tracking, and document ingestion for Phase 2+.
- **Engage a healthcare regulatory counsel now** — determine FDA SaMD classification before any architectural decisions. If it's Class II, the timeline and evidence requirements change everything.
- **Run a bias audit on available historical data** — before training anything, analyse existing intake records across demographic segments (age, gender, language, insurance status) to identify gaps that could propagate into the model.

---

### 📋 AI PM Reasoning Template

1. **What workflow problem exists?** ER Triage Nurses synthesize mixed structured/unstructured patient data under cognitive load and time pressure — critical flags at risk of being missed during peak volume
2. **Why is current software insufficient?** Current EHR forms capture structured data only; free-text chief complaints and unstructured documents are not processed or synthesized by the system
3. **Why is AI appropriate here?** Unstructured text, variable symptom presentations, and complex multi-signal risk detection exceed what rules can handle reliably
4. **What AI capability is needed?**
   - [x] Extraction (chief complaint → structured fields)
   - [x] Classification (risk flag detection)
   - [x] Anomaly detection (critical condition patterns)
   - [ ] Generation / drafting (nurse note assistance — Phase 2)
   - [ ] Summarisation (patient history synthesis — Phase 2)
5. **What are the risks if AI is wrong?** False negatives on critical flags = patient harm and clinical liability; incorrect pre-populated fields accepted without review = inaccurate clinical record
6. **What level of human oversight is required?** Mandatory — nurse confirms all AI outputs before they enter the clinical record; AI never acts autonomously on patient data
7. **How will success be measured?** Critical flag recall ≥ 98%, nurse override rate < 20% on documentation suggestions, triage completion time reduction vs baseline
8. **What is the smallest valuable MVP?** Chief complaint NLP parsing + 10 critical flag detection + confidence-gated alert surfacing — no EMR write without nurse confirmation
9. **What data/infrastructure is needed?** De-identified historical ER intake records (HIPAA-compliant), annotation pipeline for flag labelling, FHIR-compatible EMR integration layer
10. **Can the system realistically scale?** Yes — architecture generalises across facilities with per-facility protocol configuration; regulatory clearance is the scaling constraint, not technology

---

> ⚠️ *Assessment Confidence Notice: Scored on the description provided. The regulatory rating in particular may change significantly based on jurisdiction, specific AI capability scope, and intended use statement submitted to FDA. Treat this as a structured thinking tool, not an authoritative verdict.*

> 💰 *Cost & Effort Reminder: A 🟡 PROCEED WITH CAUTION verdict does not mean this is a fast or cheap build. Regulatory pathway, bias testing, and shadow-mode validation before clinical deployment are all significant effort items not reflected in this score.*

---
