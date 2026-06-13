# Project Charter: MinorSafe AI Guardrail System

## Overarching Objective

Build a functional prototype of MinorSafe — an AI safety layer that sits between minors and AI applications to detect legally risky or emotionally harmful conversations early, and redirect them before harm becomes litigation. The system turns reactive content moderation into proactive Online Dispute Prevention (ODP).

## Project Purpose

MinorSafe detects legally risky and emotionally harmful conversation patterns as they develop across a session — before any single harmful output is produced. It intervenes with risk-appropriate responses and escalates serious cases to an ODR process.

## Scope Commitments

- **In scope:** Core detection pipeline (age-aware session setup, legal-harm classifier, pattern-risk tracker, response controller, ODR escalation trigger at Red)
- **In scope:** Claude API as LLM backbone with session state for cumulative risk tracking
- **In scope:** Simple chat UI with a visible risk meter (Green / Yellow / Orange / Red)
- **In scope:** System prompt specification defining harm categories and risk thresholds
- **In scope:** Slide deck covering full product vision
- **Out of scope:** Parent/guardian notification dashboard (deck-only)
- **Out of scope:** Full cross-border ODR framework (deck-only)
- **In scope:** Smart contract simulation layer — pre-dispute prevention automation (clause-based intervention at Yellow / Orange / Red) and dispute-trigger automation (ODR case opened at Red)
- **Out of scope:** Post-dispute smart contract enforcement (settlement and award execution) — deck-only

## Validation Conditions

**VC-001:** The pipeline correctly classifies at least 4 of 5 scripted harm scenarios at the appropriate risk level (Green / Yellow / Orange / Red).
- **Applies to:** DEL-001 (pipeline prototype), DEL-002 (system prompt specification)
- **Check method:** Automated test using scripted conversation fixtures

**VC-002:** When a conversation reaches Red risk level, the system produces an ODR escalation record (timestamped log entry with session context).
- **Applies to:** DEL-001 (pipeline prototype)
- **Check method:** Automated test

**VC-003:** The response controller produces risk-appropriate output for each of the four risk levels — standard response, warning, restricted detail, and refusal with crisis resources.
- **Applies to:** DEL-001 (pipeline prototype)
- **Check method:** Automated test

**VC-004:** The cumulative pattern-risk tracker updates session risk score across multiple turns, not per-message only.
- **Applies to:** DEL-001 (pipeline prototype)
- **Check method:** Automated test using a multi-turn scripted session

**VC-005:** The system prompt specification addresses all ten listed harm categories with defined thresholds and response rules.
- **Applies to:** DEL-002 (system prompt specification)
- **Check method:** Manual review against the harm category list

---
