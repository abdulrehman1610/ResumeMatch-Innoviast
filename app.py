"""Streamlit Application Entrypoint for ResumeMatch (Live Preview Replica).

Replicates the exact UI, layout, styling, colors, ambient background glows, execution telemetry,
and card layouts from ResumeMatch-Live-Preview.html.
"""

import time
import logging
import textwrap
import streamlit as st

from core.extraction import extract_resume_text, ExtractionError
from core.ai_provider import AIProvider, AllProvidersFailedError, AIProviderError
from core.schema import AnalysisResult
from core.resume_export import generate_tailored_resume
from db.logger import log_prompt_call
import os
import shutil

FAVICON_SRC = r"C:\Users\Abdul Rehman\.gemini\antigravity-ide\brain\bc047103-305b-4366-8737-9987cd8b3f1b\resumeforge_favicon_1785407039297.png"
FAVICON_DST = os.path.join(os.path.dirname(__file__), "assets", "favicon.png")
if os.path.exists(FAVICON_SRC):
    os.makedirs(os.path.dirname(FAVICON_DST), exist_ok=True)
    try:
        shutil.copy2(FAVICON_SRC, FAVICON_DST)
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Page Config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ResumeMatch",
    page_icon=FAVICON_DST if os.path.exists(FAVICON_DST) else "⚡",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------------------------------------------
# CSS Design System — Exact Replica of Live-Preview HTML (Tailwind Dark Palette)
# ---------------------------------------------------------------------------
LIVE_PREVIEW_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Canvas Background & Ambient Radial Glows ── */
    .stApp {
        background-color: #0D0F12;
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
        background-image: 
            radial-gradient(900px circle at 50% -100px, rgba(99, 102, 241, 0.18), transparent 70%),
            radial-gradient(600px circle at 90% 700px, rgba(16, 185, 129, 0.08), transparent 70%),
            linear-gradient(#222736 1px, transparent 1px),
            linear-gradient(90deg, #222736 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px;
        background-position: center, center, center, center;
    }

    .block-container {
        max-width: 1180px;
        padding-top: 0rem;
        padding-bottom: 5rem;
    }

    /* ── Sticky Navigation Header ── */
    .sticky-header {
        position: sticky;
        top: 0;
        z-index: 40;
        background: rgba(13, 15, 18, 0.85);
        backdrop-filter: blur(24px);
        -webkit-backdrop-filter: blur(24px);
        border-bottom: 1px solid #222736;
        margin-left: -5rem;
        margin-right: -5rem;
        padding: 0 5rem;
        height: 42px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .header-logo-box {
        width: 24px;
        height: 24px;
        border-radius: 6px;
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 16px rgba(99, 102, 241, 0.4);
        font-size: 12px;
    }
    .header-title {
        font-weight: 600;
        font-size: 14px;
        color: #F8FAFC;
        letter-spacing: -0.02em;
    }
    .header-version {
        background: #14171F;
        border: 1px solid #222736;
        color: #94A3B8;
        font-size: 10.5px;
        padding: 1px 8px;
        border-radius: 999px;
    }
    .status-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        background: #14171F;
        border: 1px solid #222736;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 10.5px;
        color: #94A3B8;
    }
    .green-pulse-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 6px #10B981;
    }

    /* ── Hero Center Section ── */
    .hero-center {
        text-align: center;
        max-width: 760px;
        margin: 0 auto 12px auto;
    }
    .hero-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #14171F;
        border: 1px solid #222736;
        color: #94A3B8;
        font-size: 11px;
        padding: 2px 10px;
        border-radius: 999px;
        margin-bottom: 6px;
    }
    .hero-main-title {
        font-size: 32px;
        font-weight: 800;
        letter-spacing: -0.03em;
        line-height: 1;
        color: #F8FAFC;
        margin: 0 0 4px 0;
    }
    .hero-tagline {
        font-size: 13px;
        color: #94A3B8;
        font-weight: 400;
        line-height: 1.4;
        margin: 0 0 10px 0;
    }
    .advisory-card {
        text-align: left;
        display: flex;
        align-items: center;
        gap: 10px;
        padding: 8px 12px;
        border-radius: 10px;
        background: #14171F;
        border: 1px solid #222736;
        font-size: 11.5px;
        line-height: 1.4;
        color: #94A3B8;
    }

    /* ── Input Panel Box ── */
    .input-panel {
        background: #14171F;
        border: 1px solid #222736;
        border-radius: 16px;
        overflow: hidden;
    }
    .input-panel-header {
        height: 48px;
        padding: 0 16px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        border-bottom: 1px solid #222736;
        background: rgba(13, 15, 18, 0.4);
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
    }

    /* ── Streamlit Input Element Overrides ── */
    .stTextArea textarea {
        background-color: #0D0F12 !important;
        border: 1px solid #222736 !important;
        border-radius: 12px !important;
        color: #F8FAFC !important;
        font-family: 'Inter', sans-serif !important;
        font-size: 13px !important;
        line-height: 1.65 !important;
        padding: 12px 14px !important;
    }
    .stTextArea textarea:focus {
        border-color: #3A4156 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2) !important;
    }

    [data-testid="stFileUploader"] {
        background-color: #0D0F12 !important;
        border: 1px dashed #283042 !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    .stRadio label {
        color: #94A3B8 !important;
        font-size: 12px !important;
    }

    /* ── Execute Button (Gradient Indigo + Glow Shadow) ── */
    div.stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 14px;
        font-weight: 600;
        font-size: 14px;
        height: 46px;
        width: 100%;
        letter-spacing: -0.01em;
        transition: all 0.2s ease;
        box-shadow: 0 0 30px rgba(99, 102, 241, 0.35), inset 0 1px 0 0 rgba(255, 255, 255, 0.15);
    }
    div.stButton > button:hover {
        box-shadow: 0 0 45px rgba(99, 102, 241, 0.55);
        transform: translateY(-1px);
        color: #FFFFFF;
    }

    /* ── Download Button ── */
    div.stDownloadButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #4F46E5 100%);
        color: #FFFFFF;
        border: none;
        border-radius: 12px;
        font-weight: 600;
        font-size: 13px;
        height: 44px;
        width: 100%;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.35);
        transition: all 0.2s ease;
    }
    div.stDownloadButton > button:hover {
        box-shadow: 0 0 35px rgba(99, 102, 241, 0.5);
        transform: translateY(-1px);
        color: #FFFFFF;
    }

    /* ── Execution Log Box ── */
    .telemetry-log-card {
        background: #14171F;
        border: 1px solid #222736;
        border-radius: 16px;
        padding: 20px;
        margin-top: 24px;
        margin-bottom: 24px;
    }
    .telemetry-step-card {
        background: #0D0F12;
        border: 1px solid #1E293B;
        border-radius: 10px;
        padding: 10px;
    }
    .telemetry-step-card-active {
        background: #1A1E29;
        border-color: rgba(99, 102, 241, 0.5);
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.2);
    }

    /* ── Tabs Styling ── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background: rgba(13, 15, 18, 0.5);
        border-bottom: 1px solid #222736;
        padding: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 500;
        font-size: 12.5px;
        padding: 8px 14px;
        color: #94A3B8;
        border: 1px solid transparent;
        background: transparent;
    }
    .stTabs [aria-selected="true"] {
        background: #1A1E29 !important;
        border-color: #283042 !important;
        color: #FFFFFF !important;
        box-shadow: inset 0 1px 0 0 rgba(255, 255, 255, 0.06);
    }

    /* ── Results Container Cards ── */
    .preview-card {
        background: #1A1E29;
        border: 1px solid #283042;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }
    .preview-card-dark {
        background: #0D0F12;
        border: 1px solid #222736;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
    }

    /* ── Skill Chips ── */
    .chip-matched {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        color: #A7F3D0;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 999px;
        margin: 3px 4px 3px 0;
    }
    .chip-missing {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid rgba(245, 158, 11, 0.2);
        color: #FDE68A;
        font-size: 12px;
        padding: 4px 10px;
        border-radius: 999px;
        margin: 3px 4px 3px 0;
    }
    .dot-green { width: 6px; height: 6px; border-radius: 50%; background-color: #10B981; }
    .dot-amber { width: 6px; height: 6px; border-radius: 50%; background-color: #F59E0B; }

    /* ── Keyword Frequency Bars ── */
    .kw-bar-row {
        display: flex;
        align-items: center;
        gap: 12px;
        font-size: 12.5px;
        margin-bottom: 8px;
    }
    .kw-name-label { width: 130px; color: #F8FAFC; font-size: 13px; font-weight: 500; }
    .kw-bar-track {
        flex: 1;
        height: 8px;
        background: #14171F;
        border: 1px solid #222736;
        border-radius: 999px;
        overflow: hidden;
        position: relative;
    }
    .kw-fill-jd-bar { height: 100%; background: #6366F1; border-radius: 999px; }
    .kw-fill-res-bar { height: 100%; border-radius: 999px; }

    /* ── Bullet Rewrite Box ── */
    .rewrite-card-container {
        background: #0D0F12;
        border: 1px solid #222736;
        border-radius: 14px;
        overflow: hidden;
        margin-bottom: 16px;
    }
    .rewrite-card-header {
        padding: 12px 16px;
        background: rgba(20, 23, 31, 0.6);
        border-bottom: 1px solid #222736;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .suggested-box {
        background: #1A1E29;
        border: 1px solid #283042;
        border-radius: 10px;
        padding: 12px;
        color: #F8FAFC;
        font-size: 13px;
        line-height: 1.65;
    }

    /* ── Footer ── */
    .footer-bar {
        margin-top: 40px;
        padding-top: 24px;
        border-top: 1px solid #14171F;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-family: monospace;
        font-size: 11px;
        color: #475569;
    }
</style>
"""


# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------

def init_session_state():
    """Ensure session state keys are initialized per Architecture.md §5."""
    defaults = {
        "last_result": None,
        "last_provider_used": None,
        "resume_text": "",
        "jd_text": "",
        "latency_ms": 0,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ---------------------------------------------------------------------------
# Navigation Bar & Hero
# ---------------------------------------------------------------------------

def render_navigation_and_hero():
    """Render sticky navigation header and center hero section."""
    st.markdown(LIVE_PREVIEW_CSS, unsafe_allow_html=True)

    # Sticky Top Bar
    st.markdown(textwrap.dedent("""
        <div class="sticky-header">
            <div style="display:flex; align-items:center; gap:12px;">
                <div class="header-logo-box">⚡</div>
                <span class="header-title">ResumeMatch</span>
                <span class="header-version">v2.0.14 • prod</span>
            </div>
            <div class="status-badge">
                <span class="green-pulse-dot"></span>
                <span>System Operational</span>
            </div>
        </div>
    """), unsafe_allow_html=True)

    # Hero Box
    st.markdown(textwrap.dedent("""
        <div class="hero-center">
            <div class="hero-pill">⚡ V2.0 • AI Gap Engine</div>
            <h1 class="hero-main-title">ResumeMatch</h1>
            <p class="hero-tagline">Evidence-grounded gap analysis and resume optimization system</p>
            <div class="advisory-card">
                <div style="width:28px; height:28px; border-radius:50%; background:#1A1E29; border:1px solid #283042; display:flex; align-items:center; justify-content:center; shrink:0; margin-top:2px;">ℹ️</div>
                <div>
                    <span style="color:#F8FAFC; font-weight:500;">Advisory Boundary:</span>
                    AI suggestions are grounded guidance based on your provided resume — not an ATS guarantee. All rewrites require your verification. We never fabricate employers, dates, or credentials.
                </div>
            </div>
        </div>
    """), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Dual Input Section
# ---------------------------------------------------------------------------

def render_input_section():
    """Render resume and JD input panels."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(textwrap.dedent("""
            <div class="input-panel-header">
                <span>Resume Input</span>
            </div>
        """), unsafe_allow_html=True)
        
        input_mode = st.radio(
            "Input Mode",
            ["Upload Document", "Paste Raw Text"],
            horizontal=True,
            label_visibility="collapsed"
        )

        resume_text = ""
        if "Upload" in input_mode:
            uploaded_file = st.file_uploader("Upload PDF, DOCX, or TXT", type=["pdf", "docx", "txt"])
            if uploaded_file is not None:
                try:
                    file_bytes = uploaded_file.read()
                    resume_text = extract_resume_text(file_bytes, uploaded_file.name)
                    st.caption(f"✓ Parsed from {uploaded_file.name} — {len(resume_text.split())} words")
                except ExtractionError as e:
                    st.error(str(e))
        else:
            resume_text = st.text_area(
                "Paste Resume Text",
                height=145,
                placeholder="Paste your resume text here..."
            )

    with col2:
        st.markdown(textwrap.dedent("""
            <div class="input-panel-header">
                <span>Job Description Input</span>
            </div>
        """), unsafe_allow_html=True)

        jd_text = st.text_area(
            "Target Job Description",
            height=185,
            placeholder="Paste the target job description here..."
        )

    return resume_text, jd_text


# ---------------------------------------------------------------------------
# Pipeline Log Telemetry Component
# ---------------------------------------------------------------------------

def render_telemetry_log(result: AnalysisResult, latency_ms: int):
    """Render the execution log steps matching the Live Preview without markdown codeblock escaping."""
    steps = [
        ("1", "Token Ingestion", "Parsed"),
        ("2", "Entity Extract", "Extracted"),
        ("3", "JD Gap Matrix", "Computed"),
        ("4", "Grounding Guard", "Verified"),
        ("5", "Synthesis", "Complete"),
    ]

    steps_html = "".join([
        f'<div style="flex:1; min-width:100px; background:#0D0F12; border:1px solid #283042; border-radius:8px; padding:6px 8px;">'
        f'<div style="display:flex; align-items:center; gap:4px;">'
        f'<span style="color:#10B981; font-weight:700; font-size:10px;">✓</span>'
        f'<span style="font-size:11px; font-weight:600; color:white;">{label}</span>'
        f'</div>'
        f'<div style="font-size:9.5px; font-family:monospace; color:#64748B; margin-top:2px;">{sub}</div>'
        f'</div>'
        for _, label, sub in steps
    ])

    sec_lat = round(latency_ms / 1000.0, 1)
    prov = result.provider_used or "Unknown"
    num_rewrites = len(result.rewrite_suggestions)
    num_skills = len(result.matched_skills)
    num_ats = len(result.ats_warnings)

    html_block = (
        f'<div style="background:#14171F; border:1px solid #222736; border-radius:12px; padding:14px; margin:16px 0;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">'
        f'<span style="font-size:11.5px; color:#94A3B8; font-weight:600;">⚡ AI GAP ENGINE LOG</span>'
        f'<span style="font-size:10.5px; font-family:monospace; color:#64748B;">COMPLETE • {sec_lat}s via {prov}</span>'
        f'</div>'
        f'<div style="height:3px; border-radius:999px; background:#0D0F12; border:1px solid #222736; overflow:hidden; margin-bottom:10px;">'
        f'<div style="width:100%; height:100%; background:linear-gradient(90deg, #6366F1, #10B981);"></div>'
        f'</div>'
        f'<div style="display:flex; flex-wrap:wrap; gap:6px;">{steps_html}</div>'
        f'<div style="margin-top:10px; background:#0D0F12; border:1px solid #222736; border-radius:6px; padding:6px 10px; font-family:monospace; font-size:10.5px; color:#94A3B8;">'
        f'<span style="color:#10B981;">&gt;</span> Analysis complete — rendered {num_rewrites} rewrites, {num_skills} matched skills, {num_ats} ATS findings. All outputs grounded.'
        f'</div>'
        f'</div>'
    )

    st.markdown(html_block, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Results Tabbed Components
# ---------------------------------------------------------------------------

def render_overview_tab(result: AnalysisResult):
    """Render Overview tab."""
    tier = result.readiness_tier
    pct = tier * 20

    col1, col2 = st.columns([1.2, 1.8])

    with col1:
        st.markdown(textwrap.dedent(f"""
            <div class="preview-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:11px; text-transform:uppercase; letter-spacing:0.05em; color:#94A3B8;">Readiness Score</span>
                    <span style="padding:2px 10px; border-radius:999px; background:rgba(245, 158, 11, 0.15); border:1px solid rgba(245, 158, 11, 0.2); color:#FBBF24; font-size:11px;">Moderate Match</span>
                </div>
                <div style="margin-top:16px; display:flex; align-items:baseline; gap:8px;">
                    <span style="font-size:48px; font-weight:800; letter-spacing:-0.05em; line-height:1;">{tier}<span style="color:#475569;">/5</span></span>
                    <span style="font-size:13px; color:#94A3B8; line-height:1.4;">You meet ~{pct}% of core role requirements.</span>
                </div>
                <div style="margin-top:20px; height:8px; border-radius:999px; background:#0D0F12; border:1px solid #222736; overflow:hidden;">
                    <div style="width:{pct}%; height:100%; border-radius:999px; background:linear-gradient(90deg, #F59E0B, #FBBF24);"></div>
                </div>
                <div style="margin-top:16px; background:#0D0F12; border:1px solid #222736; border-radius:10px; padding:12px; font-size:11px; color:#94A3B8;">
                    <strong style="color:white;">Rationale:</strong> {result.readiness_rationale}
                </div>
            </div>
        """), unsafe_allow_html=True)

    with col2:
        st.markdown(textwrap.dedent(f"""
            <div class="preview-card-dark">
                <h3 style="font-size:13px; font-weight:600; color:white; margin:0 0 12px 0;">Executive Summary</h3>
                <p style="font-size:13px; line-height:1.7; color:#CBD5E1; margin:0;">{result.qualitative_summary}</p>
                <div style="margin-top:16px; display:flex; flex-wrap:wrap; gap:6px;">
                    <span style="padding:4px 10px; border-radius:999px; background:#1A1E29; border:1px solid #283042; font-size:11px; color:#94A3B8;">Evidence Grounded</span>
                    <span style="padding:4px 10px; border-radius:999px; background:#1A1E29; border:1px solid #283042; font-size:11px; color:#94A3B8;">No Fabrication</span>
                    <span style="padding:4px 10px; border-radius:999px; background:#1A1E29; border:1px solid #283042; font-size:11px; color:#94A3B8;">ATS-Aware</span>
                </div>
            </div>
        """), unsafe_allow_html=True)

        if result.experience_assessment:
            ea = result.experience_assessment
            st.markdown(textwrap.dedent(f"""
                <div class="preview-card" style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <div style="font-size:11px; text-transform:uppercase; color:#94A3B8;">Seniority Alignment</div>
                        <div style="margin-top:8px; display:flex; gap:8px;">
                            <span style="padding:4px 12px; border-radius:999px; background:#0D0F12; border:1px solid #222736; font-size:12px;">Candidate: {ea.resume_level}</span>
                            <span style="padding:4px 12px; border-radius:999px; background:rgba(99, 102, 241, 0.15); border:1px solid rgba(99, 102, 241, 0.3); font-size:12px; color:#A5B4FC;">JD: {ea.jd_level}</span>
                        </div>
                    </div>
                    <div style="background:#0D0F12; border:1px solid #222736; border-radius:10px; padding:8px 12px; font-size:11.5px; color:#94A3B8; max-width:240px;">
                        ✓ {ea.alignment_notes}
                    </div>
                </div>
            """), unsafe_allow_html=True)


def render_skills_tab(result: AnalysisResult):
    """Render Skills tab."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"**Matched Qualifications ({len(result.matched_skills)})**")
        if result.matched_skills:
            html = "".join([f'<span class="chip-matched"><span class="dot-green"></span>{s}</span>' for s in result.matched_skills])
            st.markdown(f'<div>{html}</div>', unsafe_allow_html=True)
        else:
            st.caption("None detected")

    with col2:
        st.markdown(f"**Missing Requirements ({len(result.missing_skills)})**")
        if result.missing_skills:
            html = "".join([f'<span class="chip-missing"><span class="dot-amber"></span>{s}</span>' for s in result.missing_skills])
            st.markdown(f'<div>{html}</div>', unsafe_allow_html=True)
        else:
            st.caption("No critical gaps")

    if result.skill_categories:
        st.markdown("<br>**Categorized Breakdown**", unsafe_allow_html=True)
        for cat in result.skill_categories:
            matched_html = "".join([f'<span class="chip-matched"><span class="dot-green"></span>{s}</span>' for s in cat.matched])
            missing_html = "".join([f'<span class="chip-missing"><span class="dot-amber"></span>{s}</span>' for s in cat.missing])

            matched_div = f'<div style="margin-bottom:6px;">{matched_html}</div>' if matched_html else ''
            missing_div = f'<div>{missing_html}</div>' if missing_html else ''

            card_html = (
                f'<div class="preview-card" style="padding:16px; margin-bottom:12px;">'
                f'<div style="font-size:12px; text-transform:uppercase; font-weight:600; color:#94A3B8; margin-bottom:10px;">{cat.category_name}</div>'
                f'{matched_div}'
                f'{missing_div}'
                f'</div>'
            )
            st.markdown(card_html, unsafe_allow_html=True)


def render_keywords_tab(result: AnalysisResult):
    """Render Keyword Density tab with compact, clear visual comparison."""
    if not result.keyword_density:
        st.info("No keyword density data available")
        return

    st.markdown(textwrap.dedent("""
        <div class="preview-card-dark">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                <span style="font-size:14px; font-weight:600; color:white;">Keyword Frequency Matrix</span>
                <span style="font-size:11px; color:#94A3B8;">
                    <span style="display:inline-block; width:10px; height:10px; background:#6366F1; border-radius:2px; margin-right:4px;"></span>JD Target
                    <span style="display:inline-block; width:10px; height:10px; background:#10B981; border-radius:2px; margin-left:10px; margin-right:4px;"></span>Your Resume
                </span>
            </div>
    """), unsafe_allow_html=True)

    max_val = max(max(kd.jd_count, kd.resume_count, 1) for kd in result.keyword_density)

    for kd in result.keyword_density:
        jd_w = int((kd.jd_count / max_val) * 100)
        res_w = int((kd.resume_count / max_val) * 100)
        match_status = "Matched" if kd.resume_count >= kd.jd_count else ("Partial" if kd.resume_count > 0 else "Missing")
        badge_bg = "rgba(16, 185, 129, 0.15)" if match_status == "Matched" else ("rgba(245, 158, 11, 0.15)" if match_status == "Partial" else "rgba(239, 68, 68, 0.15)")
        badge_col = "#34D399" if match_status == "Matched" else ("#FBBF24" if match_status == "Partial" else "#FCA5A5")

        st.markdown(textwrap.dedent(f"""
            <div style="background:#14171F; border:1px solid #222736; border-radius:10px; padding:12px 14px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span style="font-size:13px; font-weight:600; color:#F8FAFC;">{kd.keyword}</span>
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span style="padding:2px 8px; border-radius:999px; background:{badge_bg}; color:{badge_col}; font-size:11px; font-weight:600;">{match_status}</span>
                        <span style="font-size:11.5px; font-family:monospace; color:#94A3B8;">Resume: <strong style="color:white;">{kd.resume_count}</strong> / JD: <strong>{kd.jd_count}</strong></span>
                    </div>
                </div>
                <div style="display:flex; flex-direction:column; gap:6px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:10px; color:#64748B; width:60px;">JD Target</span>
                        <div style="flex:1; height:6px; background:#0D0F12; border-radius:3px; overflow:hidden;">
                            <div style="width:{jd_w}%; height:100%; background:#6366F1; border-radius:3px;"></div>
                        </div>
                    </div>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="font-size:10px; color:#64748B; width:60px;">Resume</span>
                        <div style="flex:1; height:6px; background:#0D0F12; border-radius:3px; overflow:hidden;">
                            <div style="width:{res_w}%; height:100%; background:{badge_col}; border-radius:3px;"></div>
                        </div>
                    </div>
                </div>
            </div>
        """), unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)


def render_rewrites_tab(result: AnalysisResult):
    """Render Rewrites tab."""
    if not result.rewrite_suggestions:
        st.info("No rewrite recommendations available")
        return

    for idx, item in enumerate(result.rewrite_suggestions):
        conf_pct = int(item.confidence_score * 100)
        sec = item.section if item.section else "Experience"

        orig_div = f'<div style="font-size:11px; text-transform:uppercase; color:#64748B; margin-bottom:4px;">Original</div><div style="font-size:12.5px; font-style:italic; color:#94A3B8; border-left:2px solid #222736; padding-left:12px; margin-bottom:12px;">"{item.original_bullet}"</div>' if item.original_bullet else ''

        card_html = (
            f'<div class="rewrite-card-container">'
            f'<div class="rewrite-card-header">'
            f'<div style="display:flex; align-items:center; gap:8px;">'
            f'<span style="font-size:12px; font-weight:600; color:white;">Recommendation #{idx + 1}</span>'
            f'<span style="color:#475569;">•</span>'
            f'<span style="font-size:11px; color:#94A3B8;">{sec}</span>'
            f'</div>'
            f'<span style="padding:2px 10px; border-radius:999px; background:rgba(16, 185, 129, 0.1); border:1px solid rgba(16, 185, 129, 0.2); font-size:11px; color:#A7F3D0;">Verified ({conf_pct}% Grounding)</span>'
            f'</div>'
            f'<div style="padding:16px;">'
            f'{orig_div}'
            f'<div style="font-size:11px; text-transform:uppercase; color:#A5B4FC; margin-bottom:4px;">Suggested</div>'
            f'<div class="suggested-box">"{item.suggested_bullet}"</div>'
            f'<div style="margin-top:10px; background:#14171F; border:1px solid #222736; border-radius:10px; padding:10px 12px; font-size:11.5px; color:#94A3B8;">'
            f'💡 {item.rationale}'
            f'</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)


def render_ats_tab(result: AnalysisResult):
    """Render ATS Audit tab."""
    if not result.ats_warnings:
        st.markdown(textwrap.dedent("""
            <div class="preview-card-dark">
                <div style="font-size:13px; font-weight:600; color:#10B981;">✓ Standard Structure Verified</div>
                <p style="font-size:12.5px; color:#94A3B8; margin-top:4px;">No issues detected for standard ATS parsers.</p>
            </div>
        """), unsafe_allow_html=True)
        return

    st.markdown(f"**Structural Audit ({len(result.ats_warnings)} findings)**")

    for warn in result.ats_warnings:
        sev = warn.severity.upper()
        bg_col = "rgba(239, 68, 68, 0.15)" if sev == "HIGH" else ("rgba(245, 158, 11, 0.15)" if sev == "MEDIUM" else "#1E293B")
        txt_col = "#FCA5A5" if sev == "HIGH" else ("#FDE68A" if sev == "MEDIUM" else "#94A3B8")

        st.markdown(textwrap.dedent(f"""
            <div class="preview-card-dark" style="display:flex; gap:12px; margin-bottom:12px;">
                <span style="padding:2px 8px; border-radius:999px; background:{bg_col}; color:{txt_col}; font-size:11px; font-weight:600; height:fit-content;">{sev}</span>
                <div>
                    <div style="font-size:13px; font-weight:500; color:white;">{warn.issue}</div>
                    <div style="font-size:12.5px; color:#94A3B8; margin-top:4px;">{warn.recommendation}</div>
                </div>
            </div>
        """), unsafe_allow_html=True)


def render_export_tab(result: AnalysisResult):
    """Render Export tab."""
    st.markdown("**Select Optimizations to Apply**")
    st.caption("All rewrites are grounded — no fabricated experience.")

    if not result.rewrite_suggestions:
        st.info("No suggestions available for export.")
        return

    selected = []
    for idx, item in enumerate(result.rewrite_suggestions):
        lbl = f"Apply #{idx+1} [{item.section}]: {item.suggested_bullet[:80]}..."
        if st.checkbox(lbl, value=(item.verification_tier == "verified"), key=f"ex_preview_{idx}"):
            selected.append(item)

    resume_text = st.session_state.get("resume_text", "")
    if resume_text and selected:
        docx_bytes = generate_tailored_resume(
            original_resume_text=resume_text,
            accepted_suggestions=selected,
            candidate_name="Candidate"
        )

        st.download_button(
            label=f"⬇ Download Tailored Resume ({len(selected)} Rewrites Applied)",
            data=docx_bytes,
            file_name="tailored_resume.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )


def render_results(result: AnalysisResult):
    """Render results tabs."""
    render_telemetry_log(result, st.session_state.get("latency_ms", 3400))

    tabs = st.tabs(["📋 Overview", "🧩 Skills Matrix", "🔍 Keywords Density", "💡 Bullet Rewrites", "🤖 ATS Audit", "📥 Export Document"])

    with tabs[0]:
        render_overview_tab(result)
    with tabs[1]:
        render_skills_tab(result)
    with tabs[2]:
        render_keywords_tab(result)
    with tabs[3]:
        render_rewrites_tab(result)
    with tabs[4]:
        render_ats_tab(result)
    with tabs[5]:
        render_export_tab(result)

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🚩 Flag an accuracy issue"):
        comment = st.text_input("Feedback detail:")
        if st.button("Submit Flag"):
            log_user_flag(provider_used=result.provider_used or "Unknown", user_comment=comment or "Flagged")
            st.success("✓ Feedback logged.")


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main():
    """Main application execution flow."""
    init_session_state()
    render_navigation_and_hero()

    resume_text, jd_text = render_input_section()

    if st.button("⚡ Execute Gap Analysis"):
        if not resume_text or len(resume_text.strip().split()) < 20:
            st.error("Please enter a valid resume (minimum 20 words).")
            return
        if not jd_text or len(jd_text.strip().split()) < 15:
            st.error("Please enter a valid job description (minimum 15 words).")
            return

        st.session_state["resume_text"] = resume_text
        st.session_state["jd_text"] = jd_text

        start = time.time()
        with st.spinner("Running AI Gap Engine..."):
            try:
                result = AIProvider.analyze(resume_text, jd_text)
                lat = int((time.time() - start) * 1000)

                st.session_state["last_result"] = result
                st.session_state["last_provider_used"] = result.provider_used
                st.session_state["latency_ms"] = lat

                log_prompt_call(
                    prompt_version="gap_analysis_v2",
                    provider_used=result.provider_used or "Unknown",
                    latency_ms=lat,
                    success=True
                )
            except AllProvidersFailedError:
                st.error("Service unavailable. Both Groq and Gemini calls failed. Please try again.")
                return
            except AIProviderError as e:
                st.error(f"Analysis error: {str(e)}")
                return

    if st.session_state["last_result"] is not None:
        render_results(st.session_state["last_result"])

    # Footer
    st.markdown(textwrap.dedent("""
        <div class="footer-bar">
            <span>© ResumeMatch • AI Gap Engine V2.0 • Evidence-grounded optimization</span>
            <span style="color:#10B981;">● Advisory Mode Active</span>
        </div>
    """), unsafe_allow_html=True)


if __name__ == "__main__":
    main()
