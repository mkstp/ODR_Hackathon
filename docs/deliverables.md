# Deliverables

*Deliverables are the discrete outputs a stakeholder would receive or evaluate at project completion. Defined collaboratively as project scope becomes clear.*

---

**DEL-001: MinorSafe Pipeline Prototype**
A runnable end-to-end prototype implementing the core detection pipeline: age-aware session setup, legal-harm classifier, pattern-risk tracker, response controller, and ODR escalation trigger at Red risk level.
Justification: The primary hackathon deliverable — a live demo that illustrates the pattern-detection differentiator and supports the pitch.

**DEL-002: System Prompt Specification**
A completed system prompt defining harm categories, risk thresholds, response rules per risk level, and safe redirect behaviors. Authored by Gregory Wataro and Michael Fong using `docs/system_prompt_guide.md`.
Justification: Required by the pipeline before any classifier logic can be implemented or tested; the specification is the contract between the legal team and the codebase.

**DEL-003: Pitch Deck**
A slide deck covering the full MinorSafe product vision, including architecture, risk levels, harm categories, ODR escalation layer, and features scoped out of the prototype (parent/guardian dashboard, smart contract enforcement).
Justification: The hackathon presentation artifact; communicates the full vision beyond what the prototype demonstrates.

Required topics:
- Core detection pipeline and risk meter (prototype demo)
- Harm categories and risk thresholds
- ODR escalation ladder (negotiation → mediation → arbitration → enforcement)
- Age classification and jurisdiction architecture: MinorSafe operates as middleware that receives a verified `user_age_group` from the integrating platform (which handles KYC and parental consent). Jurisdiction is inferred from IP geolocation at session start and used to apply the correct legal definition of minor (e.g. under-18 most jurisdictions, under-16 for certain EU digital rights contexts). This architecture directly addresses the "how do you know they're actually a minor?" objection — MinorSafe does not self-certify age; it trusts platform-level verification and applies jurisdiction-appropriate thresholds.
- Out-of-scope features for production (parent/guardian dashboard, smart contract enforcement)

---
