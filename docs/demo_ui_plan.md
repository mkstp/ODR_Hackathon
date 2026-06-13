# Demo UI Plan: Dual-Pane Platform View

*Authored: 2026-06-13*

---

## Objective

Redesign `chat_ui.py` to make the MinorSafe safety layer visible during the demo. The current UI looks like any AI chat interface — classification, pattern-tracking, and escalation logic are invisible. The new layout exposes the platform's compliance view alongside the minor's chat view, making the product thesis legible in real time.

---

## Layout

Two columns rendered with `st.columns([3, 2])`:

| Left (60%) | Right (40%) |
|---|---|
| Minor's chat interface — unchanged | Platform compliance dashboard — live |

The left column is the current UI with no changes. All new work is in the right column.

---

## Right Column: Platform Dashboard

### 1. Risk Trajectory Chart

An Altair area or line chart showing cumulative risk score (y-axis, 0.0–1.0) over turn number (x-axis). Horizontal reference lines at the risk thresholds:

| Threshold | Level |
|---|---|
| 0.30 | Yellow |
| 0.55 | Orange |
| 0.80 | Red |

Background color bands (Green / Yellow / Orange / Red zones) make the current position immediately readable. The chart updates after every turn.

**Data source:** `st.session_state.turn_log` — a list of dicts appended in `handle_input` after each turn:
```python
{"turn": int, "cumulative_score": float, "risk_level": str}
```

### 2. Latest Classification

Displayed as a small card or `st.container` below the chart. Updates after every turn. Fields:

- **Harm category** — e.g. `cyberbullying_victim`
- **Turn risk score** — float, formatted to 2dp
- **Risk level assigned** — with color icon
- **Reasoning** — the LLM's `reasoning` field, shown in an `st.expander` to keep the panel compact

### 3. Session State Summary

A compact table or metric row:

- Turn count
- Cumulative risk score
- Harm categories detected this session (deduplicated list)
- Escalated: Yes / No

### 4. Escalation Record

Hidden until `session.escalated == True`. When triggered, renders the ODR record fields from `EscalationRecord`: session ID, timestamp, trigger turn, final risk score, harm categories. Styled with a red border or `st.error` container to signal severity.

---

## State Changes

Add one new key to `st.session_state`:

```python
st.session_state.turn_log: list[dict]  # initialised to [] alongside messages
```

In `handle_input`, after `pattern_risk_tracker.update()`, append:

```python
st.session_state.turn_log.append({
    "turn": len(session.turns),
    "cumulative_score": session.cumulative_risk_score,
    "risk_level": session.risk_level,
    "harm_category": result.harm_category,
    "turn_risk_score": result.turn_risk_score,
    "reasoning": result.reasoning or "",
})
```

No changes to `Session`, `Turn`, or any backend module.

---

## Implementation Scope

All changes are confined to `src/chat_ui.py`. No backend modules are touched. The existing `render_risk_meter` and `render_message` functions are preserved as-is and used in the left column.

Altair is already in `requirements.txt`.

---

## Definition of Done

- [ ] Dual-column layout renders without error on a fresh session
- [ ] Risk trajectory chart updates after every turn and correctly reflects thresholds
- [ ] Latest classification panel shows correct harm category and reasoning
- [ ] Session state summary is accurate throughout the session
- [ ] Escalation record appears (and only appears) when `session.escalated == True`
- [ ] Left column chat behavior is identical to current behavior
- [ ] App hot-reloads cleanly; no state errors on rerun
