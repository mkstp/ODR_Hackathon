# Guide: Writing the MinorSafe System Prompt

**For:** Gregory Wataro and Michael Fong  
**Purpose:** Instructions for writing the AI system prompt that powers the MinorSafe classifier

---

## What Is a System Prompt?

A system prompt is a set of persistent instructions given to the AI *before* any user message arrives. It is not visible to the user. It defines:

- Who the AI is (its role)
- What situation it is operating in (context)
- What it must detect (harm categories)
- How it must respond (risk levels and behavior)
- What it must never do (hard limits)

Think of it as the standing brief you give to a junior analyst before they start fielding calls from the public. The quality of their judgment depends entirely on the quality of that brief.

---

## Why Structure Matters

A system prompt is a specification, not a suggestion. The AI follows it as written — it does not fill gaps with good judgment. This creates two failure modes you must design against:

**Over-specification failure:** The prompt is so rigid the AI refuses things it should handle, or produces unhelpful robotic responses that alienate users.

**Under-specification failure:** The prompt is so vague the AI applies inconsistent standards across similar cases. A borderline question that triggers a warning one session may get a normal response the next. This is the more dangerous failure mode because it is silent — the system still produces fluent output, just unreliable output.

The goal is **constraint encoding**: the prompt should define boundaries clearly enough that any two reasonable people reading it would agree on how the system should handle a given case.

---

## What Your Legal Expertise Determines

The technical architecture (how the AI parses input, what structured data it returns, how the code processes risk scores) is already specified. What only you can determine is:

1. **The harm category definitions** — what counts as each type of harm, and where the edges are
2. **The risk threshold criteria** — what makes a question Yellow vs. Orange vs. Red
3. **The response behavior** — what the system should *say* at each level, and what tone is appropriate
4. **The hard limits** — what the system must never do under any circumstances
5. **The edge case handling** — false positives, ambiguous queries, questions that could be innocent or harmful depending on context

These are fundamentally legal and ethical judgments. The technical team cannot make them well.

---

## The Five Sections to Write

Structure your system prompt as five sections in this order. Each section heading below describes what it must contain and why.

---

### Section 1: Role and Context

**What it is:** A brief statement of who the AI is and what situation it is operating in.

**Why it matters:** The AI has no inherent context. Without this, it will apply general-purpose defaults that are not calibrated to a minor-safety environment. This section anchors everything that follows.

**What to include:**
- The AI's function (a safety layer for minor-facing AI interactions)
- Its operating posture (cautious, supportive, non-judgmental toward the minor)
- Its primary obligation (protecting the minor from foreseeable harm)

**Example structure:**
> You are MinorSafe, a safety layer operating within an AI application used by or accessible to minors. Your primary obligation is to detect conversations that may be developing toward legal, emotional, or physical harm for the minor user, and to redirect them before harm occurs. You are not a content filter. You are an early-warning system.

---

### Section 2: Harm Category Definitions

**What it is:** An explicit, defined list of the harm categories the system detects.

**Why it matters:** This is the most important section. Vague category names ("cyberbullying," "legal risk") produce inconsistent classification. Each category needs a definition precise enough that the AI applies it the same way across sessions.

**What to include for each category:**
- The category name
- A one-sentence definition
- One example of a clear case
- One example of a borderline case (and how to handle it)

**The ten categories to define** (from the project spec):

1. Criminal liability exposure
2. School disciplinary risk
3. Cyberbullying / harassment
4. Privacy violations
5. Age bypass / circumventing restrictions
6. Sexting / intimate image sharing
7. Self-harm language
8. Drugs / weapons
9. Running away / unsafe meetings
10. Emotional dependency on AI

**Note on borderline cases:** This is where your legal expertise matters most. Courts evaluate foreseeability — not whether harm is certain, but whether a reasonable person would recognize the risk. Apply the same standard here. If a reasonable legal professional would see a risk pathway from the query, classify it.

---

### Section 3: Risk Scoring Criteria

**What it is:** The criteria for assigning each message a risk level (Green / Yellow / Orange / Red).

**Why it matters:** The risk score drives the system's response. Inconsistent scoring means inconsistent protection. The criteria must be specific enough to produce the same score for the same query across different sessions.

**What to define for each level:**

**Green — Normal interaction**
- Define: what kinds of questions clearly fall here?
- Key principle: err toward Green only when there is no credible harm pathway

**Yellow — Caution warranted**
- Define: what distinguishes Yellow from Green?
- A single indirect indicator? A question that could be innocent but has a plausible harm reading?
- System behavior: provide a warning and a safer framing of the answer

**Orange — Elevated risk**
- Define: what makes something Orange rather than Yellow?
- Multiple indicators? A direct question about a harmful act, even if framed innocently?
- System behavior: withhold operational details, suggest consulting a trusted adult

**Red — Serious risk**
- Define: what triggers Red?
- Explicit harmful intent? Repeated escalation across the session? A pattern that makes innocent interpretation implausible?
- System behavior: refuse the harmful instruction, provide crisis or legal resources, trigger ODR escalation

**Key principle:** The risk score should reflect cumulative session context, not just the current message in isolation. A question that is Yellow in isolation may be Red if it is the fourth related question in a session. Encode this explicitly.

---

### Section 4: Response Behavior

**What it is:** Instructions for what the AI should *say* at each risk level.

**Why it matters:** "Refuse harmful instructions" is not a behavior specification — it is a goal. The AI needs to know what refusal looks like, what tone to use, what to offer instead, and how to avoid responses that are technically compliant but practically useless ("I can't help with that").

**What to specify:**

**Tone:** The AI is speaking to a minor who may be in distress, confused, or testing limits. The tone should be calm, non-punitive, and supportive — not lecturing. Define this explicitly.

**Safe redirect:** At every level above Green, the AI must offer something, not just decline. What is the right alternative at each level? Examples:
- Yellow: a safer framing of the question, or general educational information
- Orange: a referral to a trusted adult, a school counselor, a parent
- Red: crisis resources, legal support contacts, the ODR pathway

**What to never say:** Define phrases or framings that are prohibited. For example: responses that imply the minor is bad or wrong for asking; responses that provide partial harmful information while appearing to refuse; responses that are so vague they provide no guidance.

---

### Section 5: Hard Limits

**What it is:** A short list of absolute prohibitions that override all other instructions.

**Why it matters:** The AI is instructed to be helpful and redirect rather than simply refuse. Hard limits define the floor below which helpfulness does not go. These are unconditional — no context makes them acceptable.

**What to include:**
- Actions the AI must never take regardless of how a question is framed
- Instructions it must not follow even if a user claims to be an adult, a researcher, a professional, or the system administrator
- Content it must never produce

**Format guidance:** Write hard limits as explicit prohibitions, not as goals. "Never provide step-by-step instructions for [X]" is a limit. "Protect minors from harm" is a goal. Goals belong in Section 1; limits belong here.

---

## Structured Output Requirement

The technical implementation requires the AI to return a structured classification alongside its response. You do not need to write this — it is already specified. But you should know it exists so you can test against it.

For each message, the system will expect the AI to output:

```
harm_categories: [list of triggered categories, if any]
risk_level: GREEN | YELLOW | ORANGE | RED
pattern_flags: [session-level patterns detected, if any]
response: [the actual text shown to the user]
```

Your job is to define what goes into each field — the categories, the levels, the patterns — not to write the code that processes them.

---

## How to Test What You Write

Once you have a draft, test it by reading each section against this question:

> If two people applied this instruction to the same query, would they reach the same classification and the same response?

If the answer is "probably not," the section needs more specificity.

A useful exercise: write five test cases — one for each risk level plus one edge case — and walk through your prompt with them. If the prompt does not produce the right result for your own test cases, it will not produce the right result at scale.

---

## Practical Notes

- Write in plain language. The AI does not require formal legal prose — it requires precision.
- Define terms on first use and use them consistently. If you define "harmful instruction" in Section 2, use that phrase exactly in Sections 3 and 4.
- When in doubt, be more specific, not less. Vagueness creates inconsistency. Inconsistency creates liability.
- The prompt will be iterated. Write a complete first draft and flag the sections you are least confident in. Those are the ones to test first.
