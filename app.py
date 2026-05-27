import streamlit as st
import os
from dotenv import load_dotenv
from utils.auth import get_auth_url, exchange_code_for_token, get_user_info
from utils.db import init_db

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

st.set_page_config(
    page_title="MailMind — AI Email Intelligence",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

:root {
    --ink:       #0d0d0d;
    --paper:     #f5f0e8;
    --cream:     #ede8dc;
    --accent:    #c8410a;
    --gold:      #c9a84c;
    --muted:     #7a7065;
    --high-bg:   #fff4f0;
    --med-bg:    #fffbf0;
    --low-bg:    #f5f5f5;
    --high-bd:   #c8410a;
    --med-bd:    #c9a84c;
    --low-bd:    #b0a898;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--paper) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--ink);
}

[data-testid="stAppViewContainer"] {
    background-image:
        radial-gradient(ellipse 80% 40% at 50% 0%, rgba(200,65,10,0.06) 0%, transparent 70%),
        repeating-linear-gradient(0deg, transparent, transparent 39px, rgba(13,13,13,0.04) 39px, rgba(13,13,13,0.04) 40px);
}

[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: var(--cream) !important; border-right: 1px solid rgba(13,13,13,0.1); }

/* Hide default Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

/* Buttons */
.stButton > button {
    background: var(--ink) !important;
    color: var(--paper) !important;
    border: none !important;
    border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 0.65rem 1.8rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: var(--accent) !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px rgba(200,65,10,0.25) !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stDateInput > div > div > input,
.stSelectbox > div > div {
    background: white !important;
    border: 1px solid rgba(13,13,13,0.15) !important;
    border-radius: 2px !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--ink) !important;
}
.stDateInput > div > div > input:focus,
.stTextInput > div > div > input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 2px rgba(200,65,10,0.12) !important;
}

/* Metrics */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid rgba(13,13,13,0.08);
    border-radius: 2px;
    padding: 1rem 1.2rem;
}

/* Expander */
.streamlit-expanderHeader {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    background: white !important;
    border-radius: 2px !important;
}

/* Spinner */
.stSpinner > div { border-top-color: var(--accent) !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid rgba(13,13,13,0.1) !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 0.75rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.6rem 1.4rem !important;
    border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}

/* Divider */
hr { border-color: rgba(13,13,13,0.08) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--muted); border-radius: 2px; }
</style>
""", unsafe_allow_html=True)


def render_hero():
    st.markdown("""
    <div style="text-align:center; padding: 3.5rem 1rem 2rem;">
        <div style="font-family:'DM Mono',monospace; font-size:0.72rem; letter-spacing:0.22em;
                    text-transform:uppercase; color:#c8410a; margin-bottom:1rem;">
            ✦ AI-Powered Inbox Intelligence ✦
        </div>
        <h1 style="font-family:'Playfair Display',serif; font-size:clamp(2.8rem,6vw,4.8rem);
                   font-weight:900; line-height:1.05; margin:0 0 1rem; color:#0d0d0d;">
            Mail<span style="color:#c8410a;">Mind</span>
        </h1>
        <p style="font-family:'DM Sans',sans-serif; font-size:1.05rem; color:#7a7065;
                  max-width:520px; margin:0 auto 2.5rem; line-height:1.7;">
            Connect your Outlook. Pick a date range. Get AI-ranked emails with instant summaries — 
            so you never miss what matters.
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_feature_cards():
    cols = st.columns(3, gap="medium")
    features = [
        ("⚡", "Instant Ranking", "Groq-powered AI classifies every email as High, Medium, or Low priority in seconds."),
        ("📝", "Smart Summaries", "One-line TL;DR for every email — no more reading walls of text."),
        ("🗄️", "Cached & Fast", "PostgreSQL stores results so re-runs are instant. No re-processing needed."),
    ]
    for col, (icon, title, desc) in zip(cols, features):
        with col:
            st.markdown(f"""
            <div style="background:white; border:1px solid rgba(13,13,13,0.07);
                        border-radius:3px; padding:1.6rem; height:100%;">
                <div style="font-size:1.8rem; margin-bottom:0.8rem;">{icon}</div>
                <div style="font-family:'Playfair Display',serif; font-size:1.05rem;
                            font-weight:700; margin-bottom:0.5rem;">{title}</div>
                <div style="font-size:0.87rem; color:#7a7065; line-height:1.6;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)


# ── Init DB ───────────────────────────────────────────────────────────────────
init_db()

# ── Session state ─────────────────────────────────────────────────────────────
if "access_token" not in st.session_state:
    st.session_state.access_token = None
if "user_info" not in st.session_state:
    st.session_state.user_info = None

# ── OAuth callback handling ───────────────────────────────────────────────────
params = st.query_params
if "code" in params and not st.session_state.access_token:
    with st.spinner("Authenticating with Microsoft…"):
        token = exchange_code_for_token(params["code"])
        if token:
            st.session_state.access_token = token
            st.session_state.user_info = get_user_info(token)
            st.query_params.clear()
            st.rerun()

# ── Main render ───────────────────────────────────────────────────────────────
if not st.session_state.access_token:
    render_hero()
    render_feature_cards()

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("""
        <div style="background:white; border:1px solid rgba(13,13,13,0.08);
                    border-radius:3px; padding:2rem; text-align:center;">
            <div style="font-family:'DM Mono',monospace; font-size:0.7rem;
                        letter-spacing:0.15em; text-transform:uppercase;
                        color:#7a7065; margin-bottom:1.2rem;">
                Step 1 of 1
            </div>
            <div style="font-family:'Playfair Display',serif; font-size:1.3rem;
                        font-weight:700; margin-bottom:0.5rem;">
                Connect Outlook
            </div>
            <div style="font-size:0.85rem; color:#7a7065; margin-bottom:1.5rem;">
                Sign in with your Microsoft account to grant read-only email access.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔗  Connect Microsoft Outlook", use_container_width=True):
            auth_url = get_auth_url()
            st.markdown(f'<meta http-equiv="refresh" content="0; url={auth_url}">', unsafe_allow_html=True)
            st.markdown(f"[Click here if not redirected]({auth_url})")

    st.markdown("""
    <div style="text-align:center; margin-top:3rem; font-family:'DM Mono',monospace;
                font-size:0.65rem; letter-spacing:0.12em; text-transform:uppercase; color:#b0a898;">
        Read-only access · No emails stored in plain text · Powered by Groq + PostgreSQL
    </div>
    """, unsafe_allow_html=True)

else:
    # Authenticated — redirect to dashboard
    st.switch_page("pages/dashboard.py")
