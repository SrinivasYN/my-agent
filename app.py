"""Weekly Status Report Agent: turns rough team updates into a clean report.

Built for Zero to Live AI Agent on Cloud.
"""
import os

import pandas as pd
import streamlit as st

from agent import run, to_markdown
from demo import SECTIONS
from prompts import SYSTEM_PROMPT

st.set_page_config(page_title="Weekly Status Report Agent", page_icon="📋", layout="wide")


def setting(name: str, default: str = "") -> str:
    """Read a setting from Streamlit secrets first, then from the environment."""
    try:
        value = st.secrets.get(name, "")
    except Exception:
        value = ""
    return str(value or os.getenv(name, default)).strip()


API_KEY = setting("AI_API_KEY")
BASE_URL = setting("AI_BASE_URL", "https://api.openai.com/v1")
MODEL = setting("AI_MODEL", "gpt-4o-mini")

STATUS_COLOUR = {"Green": "#16a34a", "Amber": "#d97706", "Red": "#dc2626"}
SECTION_ICON = {"Highlights": "🌟", "Progress": "✅", "Risks": "⚠️", "Blockers": "⛔", "Next week": "📅"}

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.8rem; max-width: 1180px;}
      .hero {background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 100%); color: #ffffff; padding: 22px 28px;
             border-radius: 14px; margin-bottom: 16px;}
      .hero h1 {font-size: 1.75rem; margin: 0 0 6px 0; color: #ffffff; font-weight: 700;}
      .hero p {margin: 0; font-size: 1.02rem; opacity: 0.9;}
      .card {background: #ffffff; color: #0f172a; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px 18px; margin-bottom: 12px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.05);}
      .card h4 {margin: 0 0 10px 0; font-size: 1.05rem; font-weight: 600;}
      .item {padding: 7px 0; border-top: 1px dashed #e2e8f0; font-size: 0.95rem; line-height: 1.45;}
      .item:first-of-type {border-top: none;}
      .tag {display: inline-block; font-size: 0.75rem; padding: 2px 8px; border-radius: 999px; background: #eef2ff; color: #3730a3;
            margin-left: 6px; font-weight: 500;}
      .status {display: inline-block; color: #ffffff; font-weight: 700; padding: 6px 14px; border-radius: 999px; font-size: 0.95rem;}
      .step {color: #0f172a; padding: 9px 13px; border-left: 4px solid #16a34a; background: #f8fafc; margin-bottom: 8px; border-radius: 6px;}
      .step.bad {border-left-color: #d97706;}
      .footer {color: #64748b; font-size: 0.82rem; margin-top: 32px; padding-top: 14px; border-top: 1px solid #e2e8f0; text-align: center;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="hero"><h1>📋 Weekly Status Report Agent</h1>'
    "<p>Turn rough team updates into a clean, executive-ready weekly status report.</p></div>",
    unsafe_allow_html=True,
)

st.info("ℹ️ **Notice:** Live external systems (Jira, email, databases) are not connected. The agent uses your input notes and sample data.")

if API_KEY:
    st.success(f"Using AI model ({MODEL}).")
else:
    st.info("Demo mode: simple rule-based sorting active. Add an AI key in secrets to switch to a real model.")

SAMPLES = {
    "Sample 1: Standard sprint (sample1.txt)": "samples/sample1.txt",
    "Sample 2: Mobile & platform sprint (sample2.txt)": "samples/sample2.txt",
    "Sample 3: Messy notes & typos (sample3.txt)": "samples/sample3.txt",
    "Sample 4: Very short update (sample4.txt)": "samples/sample4.txt",
    "Sample 5: Missing critical info (sample5.txt)": "samples/sample5.txt",
    "Default sample (sample_updates.txt)": "sample_updates.txt",
}


def read(p: str) -> str:
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


if "updates" not in st.session_state:
    st.session_state.updates = ""

left, right = st.columns([1, 1.35], gap="large")

with left:
    pick = st.selectbox("Choose a sample input", list(SAMPLES))
    c1, c2 = st.columns(2)
    if c1.button("Load sample updates", use_container_width=True):
        st.session_state.updates = read(SAMPLES[pick])
    up = c2.file_uploader("or upload a .txt file", type=["txt", "md", "csv"], label_visibility="collapsed")
    if up is not None and st.session_state.get("_uploaded") != up.name:
        st.session_state.updates = up.read().decode("utf-8", errors="ignore")
        st.session_state._uploaded = up.name

    updates = st.text_area(
        "Rough team updates for the week",
        key="updates",
        height=330,
        placeholder="Paste rough updates from stand-ups, Jira tickets, chats, or emails (one note per line)...",
    )
    go = st.button("Write my report", type="primary", use_container_width=True)

with right:
    if go:
        if not updates.strip():
            st.warning("Paste some notes first, or click 'Load sample updates'.")
        else:
            with st.spinner("Analyzing updates, writing report, and checking work..."):
                try:
                    result, steps = run(updates, SYSTEM_PROMPT, API_KEY, BASE_URL, MODEL)
                except Exception as err:
                    st.error(f"The AI model could not answer. Check your key and model name, then try again. Details: {err}")
                    st.stop()
            st.session_state.result, st.session_state.steps = result, steps

    result = st.session_state.get("result")
    steps = st.session_state.get("steps", [])

    if not result:
        st.markdown(
            '<div class="card"><h4>How it works</h4>'
            '<div class="item">1. Paste your rough updates, or click <b>Load sample updates</b>.</div>'
            '<div class="item">2. Click <b>Write my report</b>.</div>'
            '<div class="item">3. The agent sorts notes into sections, checks its own work, and flags missing info.</div></div>',
            unsafe_allow_html=True,
        )
    else:
        items = result.get("items", [])
        count = lambda s: len([i for i in items if i.get("section") == s])
        colour = STATUS_COLOUR.get(result.get("status", ""), "#6b7280")

        st.markdown(
            f'<span class="status" style="background:{colour}">Overall status: {result.get("status", "Not enough information")}</span>'
            f'&nbsp;&nbsp;<span style="color:#475569">{result.get("status_reason", "")}</span>',
            unsafe_allow_html=True,
        )
        st.write("")

        if result.get("headline"):
            st.markdown(
                f'<div class="card" style="border-left:6px solid {colour}"><h4>What matters most this week</h4>'
                f'<div style="font-size:1.05rem">{result["headline"]}</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown(f"**Summary:** {result.get('summary', 'Not enough information.')}")

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Highlights", count("Highlights"))
        k2.metric("Risks", count("Risks"))
        k3.metric("Blockers", count("Blockers"))
        k4.metric("Questions", len(result.get("questions", [])))

        tab_report, tab_register, tab_actions, tab_email, tab_questions, tab_steps = st.tabs(
            ["Report", "Risks and blockers", "Actions and decisions", "Email to sponsor", "Questions for the team", "Agent steps"]
        )

        with tab_report:
            for s in SECTIONS:
                rows = [i for i in items if i.get("section") == s]
                body = "".join(
                    f'<div class="item">{i.get("text", "")}'
                    + (f'<span class="tag">👤 {i["owner"]}</span>' if i.get("owner") else "")
                    + (f'<span class="tag">📅 {i["due"]}</span>' if i.get("due") else "")
                    + "</div>"
                    for i in rows
                ) or '<div class="item">Nothing to report.</div>'
                st.markdown(f'<div class="card"><h4>{SECTION_ICON[s]} {s}</h4>{body}</div>', unsafe_allow_html=True)

        with tab_register:
            reg = [i for i in items if i.get("section") in ("Risks", "Blockers")]
            if reg:
                st.dataframe(
                    pd.DataFrame([
                        {
                            "Type": i["section"][:-1],
                            "Impact": i.get("impact") or "Not known",
                            "Owner": i.get("owner") or "Not known",
                            "Due": i.get("due") or "Not known",
                            "Item": i.get("text", ""),
                        }
                        for i in reg
                    ]),
                    use_container_width=True,
                    hide_index=True,
                )
            else:
                st.write("No risks or blockers this week.")

        with tab_actions:
            st.markdown("**Top actions this week**")
            for n, a in enumerate(result.get("actions", []) or [], 1):
                st.markdown(
                    f'<div class="step"><b>{n}. {a.get("action", "")}</b><br><span style="color:#475569">Owner: {a.get("owner") or "Not known"}'
                    f'  ·  Why: {a.get("why", "")}</span></div>',
                    unsafe_allow_html=True,
                )
            if not result.get("actions"):
                st.write("No actions needed.")
            st.markdown("**Decisions needed**")
            for dcs in result.get("decisions", []) or ["None this week."]:
                st.markdown(f"- {dcs}")

        with tab_email:
            st.text_area("Ready to copy and send", result.get("email", "") or "Not enough information.", height=240)

        with tab_questions:
            for q in result.get("questions", []) or ["No information is missing."]:
                st.markdown(f"- {q}")

        with tab_steps:
            for n, s in enumerate(steps, 1):
                st.markdown(
                    f'<div class="step {"" if s["ok"] else "bad"}"><b>{n}. {s["name"]}</b> {"✓" if s["ok"] else "!"}<br>'
                    f'<span style="color:#475569">{s["detail"]}</span></div>',
                    unsafe_allow_html=True,
                )

        st.download_button("Download the report", to_markdown(result), file_name="weekly-status-report.md", use_container_width=True)
        st.warning("⚠️ **Please check before using:** Review and verify this generated report before sending or sharing it with stakeholders.")

st.markdown('<div class="footer">Built by Srinivas YN at Zero to Live, Future Proof India</div>', unsafe_allow_html=True)
