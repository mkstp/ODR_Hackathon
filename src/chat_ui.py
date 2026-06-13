import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone

import altair as alt
import pandas as pd
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from src import odr_escalation_trigger, pattern_risk_tracker, response_controller, session_manager, smart_contract
from src.harm_classifier import HarmClassifier
from src.mock_classifier import SCENARIO_NAMES, MockClassifier
from src.models import EscalationRecord, ResponsePayload, Session, Turn

_RISK_ICON = {
    "Green": "🟢",
    "Yellow": "🟡",
    "Orange": "🟠",
    "Red": "🔴",
}


def render_risk_meter(risk_level: str) -> None:
    icon = _RISK_ICON.get(risk_level, "⚪")
    st.metric(label="Risk Level", value=f"{icon} {risk_level}")


def render_message(payload: ResponsePayload) -> None:
    st.markdown(payload.message)
    if payload.crisis_resources:
        st.markdown("**If you need help right now:**")
        for resource in payload.crisis_resources:
            st.markdown(f"- {resource}")


def _render_risk_chart(turn_log: list) -> None:
    bands_df = pd.DataFrame([
        {"y": 0.00, "y2": 0.30, "zone": "Green"},
        {"y": 0.30, "y2": 0.55, "zone": "Yellow"},
        {"y": 0.55, "y2": 0.80, "zone": "Orange"},
        {"y": 0.80, "y2": 1.01, "zone": "Red"},
    ])
    zone_color = alt.Color(
        "zone:N",
        scale=alt.Scale(
            domain=["Green", "Yellow", "Orange", "Red"],
            range=["#00CC44", "#FFD700", "#FF8C00", "#DC143C"],
        ),
        legend=None,
    )
    bands = (
        alt.Chart(bands_df)
        .mark_rect(opacity=0.12)
        .encode(
            y=alt.Y("y:Q", scale=alt.Scale(domain=[0, 1]), title="Risk Score"),
            y2=alt.Y2("y2:Q"),
            color=zone_color,
        )
    )
    thresholds_df = pd.DataFrame([
        {"y": 0.30, "level": "Yellow"},
        {"y": 0.55, "level": "Orange"},
        {"y": 0.80, "level": "Red"},
    ])
    rules = (
        alt.Chart(thresholds_df)
        .mark_rule(strokeDash=[4, 4], opacity=0.5)
        .encode(
            y="y:Q",
            color=alt.Color(
                "level:N",
                scale=alt.Scale(
                    domain=["Yellow", "Orange", "Red"],
                    range=["#CCB000", "#CC5500", "#AA0000"],
                ),
                legend=None,
            ),
        )
    )
    if turn_log:
        df = pd.DataFrame(turn_log)
        line = (
            alt.Chart(df)
            .mark_line(point=True, color="steelblue")
            .encode(
                x=alt.X("turn:Q", title="Turn"),
                y=alt.Y("cumulative_score:Q", scale=alt.Scale(domain=[0, 1]), title=None),
                tooltip=[
                    alt.Tooltip("turn:Q", title="Turn"),
                    alt.Tooltip("cumulative_score:Q", title="Score", format=".2f"),
                    alt.Tooltip("risk_level:N", title="Level"),
                ],
            )
        )
        chart = alt.layer(bands, rules, line)
    else:
        chart = alt.layer(bands, rules)

    st.altair_chart(
        chart.properties(height=150, title="Risk Trajectory"),
        width="stretch",
    )


def _render_latest_classification(entry: dict) -> None:
    icon = _RISK_ICON.get(entry["risk_level"], "⚪")
    st.markdown("**Latest Classification**")
    col_a, col_b = st.columns(2)
    col_a.metric("Category", entry["harm_category"])
    col_b.metric("Turn Score", f"{entry['turn_risk_score']:.2f}")
    st.markdown(f"**Level:** {icon} {entry['risk_level']}")
    if entry.get("reasoning"):
        with st.expander("Reasoning"):
            st.markdown(entry["reasoning"])


def _render_session_summary(session: Session, turn_log: list) -> None:
    st.markdown("**Session Summary**")
    categories = list(dict.fromkeys(
        e["harm_category"] for e in turn_log if e["harm_category"] != "none"
    ))
    col_a, col_b = st.columns(2)
    col_a.metric("Turns", len(turn_log))
    col_b.metric("Cumulative Score", f"{session.cumulative_risk_score:.2f}")
    st.markdown(f"**Categories detected:** {', '.join(categories) if categories else 'None'}")
    escalated_label = "🔴 Yes" if session.escalated else "No"
    st.markdown(f"**Escalated:** {escalated_label}")


def _render_escalation_record(record: EscalationRecord) -> None:
    with st.container(border=True):
        st.error("**ODR Escalation Record**")
        st.markdown(f"**Session:** `{record.session_id}`")
        st.markdown(f"**Timestamp:** {record.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        st.markdown(f"**Trigger Turn:** {record.trigger_turn_id}")
        st.markdown(f"**Final Score:** {record.final_risk_score:.2f}")
        st.markdown(f"**Turns at Escalation:** {record.turn_count}")
        st.markdown(f"**Categories:** {', '.join(record.harm_categories_detected)}")


def _render_active_clause(clause) -> None:
    if clause is None:
        return
    with st.container(border=True):
        st.markdown(f"**`{clause['key']}`** — {clause['description']}")
        st.caption(f"Action: `{clause['action']}`")


def render_dashboard(session: Session, turn_log: list, escalation_record, active_clause=None) -> None:
    render_risk_meter(session.risk_level)
    st.divider()
    _render_risk_chart(turn_log)
    if turn_log:
        st.divider()
        _render_latest_classification(turn_log[-1])
    st.divider()
    st.markdown("**Smart Contract**")
    _render_active_clause(active_clause)
    if active_clause is None:
        st.caption("No clause active — risk below Yellow threshold.")
    st.divider()
    _render_session_summary(session, turn_log)
    if session.escalated and escalation_record:
        st.divider()
        _render_escalation_record(escalation_record)


def handle_input(user_message: str, session: Session) -> ResponsePayload:
    result = st.session_state.classifier.classify(session, user_message)
    turn = Turn(
        turn_id=len(session.turns),
        user_message=user_message,
        classification=result,
        timestamp=datetime.now(timezone.utc),
    )
    session_manager.add_turn(session, turn)
    pattern_risk_tracker.update(session, result)
    st.session_state.active_clause = smart_contract.evaluate(session)
    st.session_state.turn_log.append({
        "turn": len(session.turns),
        "cumulative_score": session.cumulative_risk_score,
        "risk_level": session.risk_level,
        "harm_category": result.harm_category,
        "turn_risk_score": result.turn_risk_score,
        "reasoning": result.reasoning or "",
    })
    payload = response_controller.generate_response(session, result)
    if response_controller.should_escalate(session):
        record = odr_escalation_trigger.trigger(session)
        if record:
            odr_escalation_trigger.log_record(record, "escalation_log.jsonl")
            st.session_state.escalation_record = record
        session_manager.mark_escalated(session)
    return payload


def run() -> None:
    st.set_page_config(
        page_title="MinorSafe Demo",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.markdown("""
    <style>
        .block-container { padding-top: 0.75rem !important; padding-bottom: 0 !important; }
        h1 { margin-bottom: 0 !important; }
    </style>
    """, unsafe_allow_html=True)
    st.title("MinorSafe — AI Safety Guardrail")

    if "session" not in st.session_state:
        st.caption("Left: what the minor sees. Right: real-time compliance data for the platform operator only.")
        is_minor = st.checkbox("I am under 18", value=True, key="age_checkbox")
        st.divider()
        use_demo = st.checkbox("Demo mode (no API key required)", value=False, key="demo_mode")
        if use_demo:
            st.selectbox("Demo scenario", options=SCENARIO_NAMES, key="scenario_select")
        if st.button("Start conversation"):
            age_group = "minor" if is_minor else "unknown"
            st.session_state.session = session_manager.create_session(age_group)
            st.session_state.messages = []
            st.session_state.turn_log = []
            st.session_state.escalation_record = None
            if st.session_state.get("demo_mode"):
                scenario = st.session_state.get("scenario_select", SCENARIO_NAMES[0])
                st.session_state.classifier = MockClassifier(scenario)
            else:
                st.session_state.classifier = HarmClassifier()
            st.rerun()
        st.stop()

    # Guard for sessions started before turn_log was added
    if "turn_log" not in st.session_state:
        st.session_state.turn_log = []
    if "escalation_record" not in st.session_state:
        st.session_state.escalation_record = None
    if "active_clause" not in st.session_state:
        st.session_state.active_clause = None

    session: Session = st.session_state.session
    left, right = st.columns([3, 2], gap="large")

    with left:
        st.caption("**👤 MINOR'S VIEW** — what the user sees")
        st.divider()
        with st.container(height=420):
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        if (
            isinstance(st.session_state.classifier, MockClassifier)
            and len(session.turns) == 0
            and not st.session_state.get("demo_autoplay")
        ):
            if st.button("▶ Run demo", type="primary", use_container_width=True):
                st.session_state.demo_autoplay = True
                st.rerun()

        if user_input := st.chat_input("Type your message..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            payload = handle_input(user_input, session)

            st.session_state.messages.append({"role": "assistant", "content": payload.message})
            with st.chat_message("assistant"):
                render_message(payload)

            st.rerun()

    with right:
        st.caption("**🔍 PLATFORM COMPLIANCE VIEW** — invisible to the user")
        st.divider()
        with st.container(height=520):
            render_dashboard(
                session,
                st.session_state.turn_log,
                st.session_state.escalation_record,
                active_clause=st.session_state.get("active_clause"),
            )

    if st.session_state.get("demo_autoplay"):
        classifier = st.session_state.classifier
        step = len(session.turns)
        if isinstance(classifier, MockClassifier) and step < classifier.step_count:
            time.sleep(7)
            msg = classifier.get_step_message(step)
            st.session_state.messages.append({"role": "user", "content": msg})
            payload = handle_input(msg, session)
            st.session_state.messages.append({"role": "assistant", "content": payload.message})
            st.rerun()
        else:
            st.session_state.demo_autoplay = False


if __name__ == "__main__":
    run()
