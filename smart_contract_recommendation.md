# Smart Contract Integration — Recommendation

**Context:** Gregory's notes propose adding a "smart contract" feature to MinorSafe.

---

## The Core Issue: Terminology Mismatch

What Gregory describes is mostly **automated rule-based intervention logic** — if score > threshold, then disable functions / require guardian confirmation / preserve logs. That is not a smart contract in the technical sense (blockchain-deployed, cryptographically enforced code on Ethereum or similar). It is conditional business logic — which MinorSafe already has in `response_controller.py` and `odr_escalation_trigger.py`.

---

## What's Worth Keeping

The **conceptual framing** is strong and hackathon-friendly:

- *"Smart contracts before arbitration"* — distinctive positioning
- *"Automate the prevention, not the judgment"* — clear, memorable slogan
- Gregory is right that most blockchain ODR work focuses on enforcement; using smart contracts as a *preventive* mechanism is a genuine differentiator

These ideas belong in the deck and the pitch. They don't need to be built to be argued.

---

## What to Actually Build: A Simulation Layer

Rather than integrating real blockchain infrastructure (which would consume remaining build time and introduce unnecessary failure points), add a thin **smart contract simulation module** — `src/smart_contract.py` — that:

1. Defines rule clauses as **explicit named conditions**, not anonymous threshold checks
2. Logs which **clause** triggered each action (e.g., `CLAUSE_3: guardian_confirmation_required`)
3. Surfaces the active clause in the **compliance dashboard** alongside the existing risk meter

This gives the demo the language and framing of smart contracts without the Web3 integration overhead.

### Example clause structure

```python
CLAUSES = {
    "CLAUSE_1": {
        "condition": "cumulative_risk_score > 0.30",
        "action": "limit_conversation_duration",
        "description": "Yellow threshold exceeded — session time-limited.",
    },
    "CLAUSE_2": {
        "condition": "cumulative_risk_score > 0.55",
        "action": "require_guardian_confirmation",
        "description": "Orange threshold exceeded — guardian confirmation required.",
    },
    "CLAUSE_3": {
        "condition": "cumulative_risk_score > 0.80 OR turn_risk_level == Red",
        "action": "disable_ai_functions + trigger_odr_escalation",
        "description": "Red threshold exceeded — AI functions suspended, ODR case opened.",
    },
}
```

### In the pitch, you can honestly say:
> "In production, these rule clauses would be deployed as on-chain smart contracts — immutable, auditable, and enforceable without platform discretion. For this prototype, they run as verifiable deterministic logic with the same clause structure."

---

## What to Leave in the Deck Only

Gregory's **evidence preservation clause** (freeze deletion, preserve chat logs on complaint, notify platform) is the most legally meaningful smart contract use case he mentions. It is also completely out of scope for a local Streamlit prototype — it is a platform-level infrastructure concern.

Acknowledge it in the slides as **production architecture**, not as something the prototype demonstrates.

---

## Summary

| Component | Recommendation |
|---|---|
| Smart contract framing + slogans | ✅ Keep — strong pitch material |
| Blockchain / Solidity / Web3 integration | ❌ Skip — scope risk, no demo value |
| `smart_contract.py` simulation layer | ✅ Build — wire clause names into dashboard |
| Evidence preservation clause | 📊 Deck only — production architecture slide |

---

*Prepared for MinorSafe / ODR Hackathon, June 2026.*
