# Smart Contract-Inspired ODR Integration — Recommendation

**Context:** Gregory's notes propose adding a "smart contract" feature to MinorSafe. After clarification, the goal is: when harm thresholds are crossed, a smart contract-inspired rule fires automatically — capturing the transcript as evidence and opening an ODR case with the classifier's reasoning as the primary resource for dispute resolution.

---

## Framing: Smart Contract-Inspired, Not Blockchain

MinorSafe uses **smart contract-inspired logic** to trigger an ODR process automatically when harm thresholds are crossed — deterministic, pre-defined rules that fire without human discretion, capturing evidence and opening a case the way a real smart contract would enforce a clause.

We are not claiming blockchain. We are claiming the *design pattern*: if-this-then-that rules that are transparent, pre-committed, and automatic. This is intellectually honest and still distinctive — most ODR blockchain work focuses on enforcement; MinorSafe uses the pattern for **prevention and evidence capture**.

### Slogan options
- *"Smart contracts before arbitration."*
- *"Automate the prevention, not the judgment."*
- *"Don't automate who wins. Automate what gets preserved."*

---

## Consistent Terminology

Use these terms throughout the codebase, dashboard, and pitch:

| Term | Meaning |
|---|---|
| **Smart contract clause** | The named, pre-defined rule that fires (e.g., `ODR_CLAUSE_RED`) |
| **Contract execution** | The moment the clause condition is met and the ODR process triggers |
| **Evidence package** | The auto-captured transcript + classifier reasoning, produced at execution |
| **ODR case** | The dispute record the evidence package initiates |

The flow reads: *smart contract clause fires → contract executes → evidence package captured → ODR case opened.*

---

## What to Build

### 1. `src/smart_contract.py` — Clause definitions

Define named clauses that map threshold conditions to actions. These replace anonymous `if score > 0.8` checks with explicit, documentable rules.

```python
CLAUSES = {
    "ODR_CLAUSE_YELLOW": {
        "condition": "cumulative_risk_score >= 0.30",
        "action": "warn_user + limit_conversation_duration",
        "description": "Yellow threshold exceeded — session time-limited, user warned.",
    },
    "ODR_CLAUSE_ORANGE": {
        "condition": "cumulative_risk_score >= 0.55",
        "action": "restrict_responses + require_guardian_confirmation",
        "description": "Orange threshold exceeded — responses restricted, guardian confirmation required.",
    },
    "ODR_CLAUSE_RED": {
        "condition": "cumulative_risk_score >= 0.80 OR turn_risk_level == Red",
        "action": "disable_ai_functions + execute_odr_escalation",
        "description": "Red threshold exceeded — AI suspended, ODR case opened, evidence package captured.",
    },
}
```

### 2. Extend `odr_escalation_trigger.py` — Full evidence package

The current escalation trigger logs a thin record. Upgrade it to produce a complete **ODR evidence package** at contract execution:

- Session metadata (ID, timestamp, age group)
- The smart contract clause that fired, and on which turn
- Full transcript — every user message with its turn risk score
- Per-turn classifier reasoning from all flagged turns
- Harm category trajectory across the session
- A narrative summary of why the ODR case was opened

Output format: a structured JSON file (one per session) alongside the existing JSONL append log.

### 3. Update `chat_ui.py` — Surface the case in the dashboard

When `ODR_CLAUSE_RED` executes, the compliance dashboard should show:

- Which clause fired and when
- A collapsible preview of the evidence package
- A clear label: **"ODR Case Opened"** with the case ID

---

## What to Leave in the Deck Only

The **evidence preservation clause** Gregory describes — freezing deletion, notifying the platform, cross-border log preservation — is the most legally meaningful smart contract use case. It is also a platform-level infrastructure concern, not something a local Streamlit prototype can demonstrate.

Acknowledge it in the slides as **production architecture**: "In production, these clauses would be deployed on-chain — immutable, auditable, and enforceable across jurisdictions without platform discretion."

---

## Mapping to Existing Pipeline

| Existing module | Role in smart contract flow |
|---|---|
| `pattern_risk_tracker.py` | Monitors clause conditions each turn |
| `smart_contract.py` *(new)* | Defines and names the clauses |
| `odr_escalation_trigger.py` *(extended)* | Executes the contract, produces evidence package |
| `response_controller.py` | Delivers the user-facing output per clause level |
| `chat_ui.py` *(extended)* | Surfaces clause execution and case preview in dashboard |

---

*Prepared for MinorSafe / ODR Hackathon, June 2026.*
