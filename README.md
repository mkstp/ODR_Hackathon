# MinorSafe AI Guardrail System

**No minor harm. No legal surprise. ODP before ODR.**

---

## What We're Building

MinorSafe is an AI safety layer that sits between minors and AI applications. It detects legally risky or emotionally harmful conversation patterns early and redirects them — before harm becomes litigation.

The core insight: standard content moderation asks *"is this answer dangerous?"* MinorSafe asks *"is this interaction developing toward foreseeable harm?"*

This reframes AI safety from reactive content moderation into proactive **Online Dispute Prevention (ODP)**.

---

## The Problem

Generative AI systems expose minors to legal, emotional, and safety risks. Existing safeguards filter individual responses. They do not detect risk patterns that develop across a conversation over time.

Recent litigation involving AI platforms has raised unresolved questions about:
- Platform duty of care toward minors
- Foreseeability of harm
- Cross-border dispute resolution
- Smart contract enforcement of agreed outcomes

---

## Architecture

```
Minor's question
      ↓
Age-Aware Classifier        ← is the user a minor?
      ↓
Legal-Harm Classifier       ← which harm category does this touch?
      ↓
Pattern-Risk Tracker        ← cumulative session risk score
      ↓
Response Controller         ← safe answer / warning / refusal / escalation
      ↓
ODR Trigger (Red)           ← smart contract initiates dispute process
```

---

## Risk Levels

| Level | Meaning | System Action |
|---|---|---|
| Green | Normal interaction | Standard response |
| Yellow | Borderline risk | Warning + safer answer |
| Orange | Elevated risk | Restrict details + suggest trusted adult |
| Red | Serious risk | Refuse + crisis resources + ODR escalation |

---

## Harm Categories Detected

- Criminal liability exposure
- School disciplinary risk
- Cyberbullying / harassment
- Privacy violations
- Age bypass / fake ID
- Sexting / intimate image sharing
- Self-harm language
- Drugs / weapons
- Running away / unsafe meetings
- Emotional dependency on AI

---

## ODR Escalation Layer

When a conversation reaches Red, MinorSafe triggers an Online Dispute Prevention process rather than a simple refusal. A smart contract architecture enforces the escalation pathway:

- Complaint is logged and timestamped
- Relevant parties (parent/guardian, platform) are notified
- An ODR process is initiated: negotiation → mediation → arbitration → enforcement

Smart contracts handle outcome enforcement (settlements, platform compliance, refunds) but do not determine liability, causation, or damages — those require human judgment.

---

## Safe Redirect Principle

The system does not simply refuse. Example:

> **Minor asks:** How can I fake my age online?
>
> **MinorSafe responds:** I can't help bypass age restrictions. I can explain why age verification rules exist and how to safely ask a parent or platform for access.

---

## Today's Build Scope (Hackathon)

We are building the core pipeline end-to-end:

1. Age-aware session setup
2. Legal-harm classifier (Claude API)
3. Pattern-risk tracker (cumulative session state)
4. Response controller (risk-appropriate outputs)
5. ODR escalation trigger at Red

Parent/guardian dashboard, full cross-border ODR framework, and smart contract implementation are scoped for the deck — not the prototype.

---

## Team

- Marc St-Pierre
- Gregory Wataro
- Michael Fong
