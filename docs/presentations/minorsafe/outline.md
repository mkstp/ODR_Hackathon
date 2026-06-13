# Slide Outline: MinorSafe

## Deck Metadata
- **Title:** MinorSafe: AI Safety for Minors with an ODR Backbone
- **Subtitle:** Online Dispute Prevention Before It Becomes a Case
- **Author:** Marc St-Pierre
- **Date:** June 2026
- **Sections:** The Problem, MinorSafe, Built by Experts

---

## Slides

### Slide 1
layout: cover
section: —
message: —
content_type: —
source_ref: —

### Slide 2
layout: content
section: —
message: AI platforms are already in conversations with millions of minors — the unresolved question is who is responsible when those conversations cause harm.
content_type: text
source_ref: README.md — "Recent litigation involving AI platforms has raised unresolved questions about platform duty of care toward minors"

### Slide 3
layout: section
section: The Problem
message: —
content_type: —
source_ref: —

### Slide 4
layout: content
section: The Problem
message: Existing content moderation asks whether a single response is dangerous — it cannot detect whether a conversation is becoming dangerous.
content_type: text
source_ref: README.md — "The core insight: standard content moderation asks 'is this answer dangerous?' MinorSafe asks 'is this interaction developing toward foreseeable harm?'"

### Slide 5
layout: section
section: MinorSafe
message: —
content_type: —
source_ref: —

### Slide 6
layout: content
section: MinorSafe
message: MinorSafe reframes AI safety as Online Dispute Prevention — intervening before harm becomes a dispute, not after.
content_type: text
source_ref: README.md — "This reframes AI safety from reactive content moderation into proactive Online Dispute Prevention (ODP)"

### Slide 7
layout: content-image
section: MinorSafe
message: A five-module pipeline classifies harm, tracks cumulative session risk, and triggers an ODR escalation automatically at Red.
content_type: image
source_ref: README.md — Architecture section; project_charter.md — Scope Commitments

### Slide 8
layout: content
section: MinorSafe
message: A working prototype — dual-pane UI with a live compliance dashboard and three scripted demo scenarios — is ready to run today.
content_type: text
source_ref: change_and_decision_log.jsonl — Session 5 (dual-pane UI), Session 6 (MockClassifier, demo auto-advance), Session 7 (demo scenario redesign)

### Slide 9
layout: content
section: MinorSafe
message: Smart contracts serve as the bridge between ODP and ODR — automating prevention before a dispute, case-management during, and settlement enforcement after.
content_type: text
source_ref: project_charter.md — Scope Commitments (smart contract simulation layer); change_and_decision_log.jsonl — Session 7 (smart contract simulation layer decision)

### Slide 10
layout: section
section: Built by Experts
message: —
content_type: —
source_ref: —

### Slide 11
layout: content
section: Built by Experts
message: The harm classification system was designed by legal experts — 14 harm categories with legally precise thresholds, authored directly into the system prompt.
content_type: text
source_ref: change_and_decision_log.jsonl — Session 1 (system prompt authorship delegated to legal team), Session 4 (HARM_CATEGORIES updated to categories 2–6), Session 7 (system_prompt.md promoted to live system prompt, 14 final keys)

### Slide 12
layout: content
section: Built by Experts
message: The AI infrastructure was optimized for real-time safety at scale — prompt caching, a sliding context window, and turn-weighted risk scoring address core LLM limitations.
content_type: text
source_ref: change_and_decision_log.jsonl — Session 2 (sliding window, session state injection, linear turn weighting), Session 4 (prompt caching with cache_control ephemeral)

### Slide 13
layout: closing
section: —
message: —
content_type: —
source_ref: —

### Slide 14
layout: about
section: —
message: —
content_type: —
source_ref: —
