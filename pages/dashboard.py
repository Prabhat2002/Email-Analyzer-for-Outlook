import streamlit as st
import os
from datetime import date, timedelta
from dotenv import load_dotenv
from utils.db import init_db, get_cached_emails, upsert_email, emails_exist_for_range
from utils.graph import fetch_emails
from utils.ai import batch_classify

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

st.set_page_config(
    page_title="MailMind — Dashboard",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Global CSS (same design system) ──────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Sans:wght@300;400;500&family=DM+Mono:wght@400;500&display=swap');

:root {
    --ink:     #0d0d0d;
    --paper:   #f5f0e8;
    --cream:   #ede8dc;
    --accent:  #c8410a;
    --gold:    #c9a84c;
    --muted:   #7a7065;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--paper) !important;
    font-family: 'DM Sans', sans-serif;
    color: var(--ink);
}
[data-testid="stAppViewContainer"] {
    background-image: repeating-linear-gradient(
        0deg, transparent, transparent 39px,
        rgba(13,13,13,0.035) 39px, rgba(13,13,13,0.035) 40px);
}
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] {
    background: var(--cream) !important;
    border-right: 1px solid rgba(13,13,13,0.1);
}
#MainMenu, footer, header { visibility: hidden; }

.stButton > button {
    background: var(--ink) !important; color: var(--paper) !important;
    border: none !important; border-radius: 2px !important;
    font-family: 'DM Mono', monospace !important; font-size: 0.75rem !important;
    letter-spacing: 0.12em !important; text-transform: uppercase !important;
    padding: 0.6rem 1.5rem !important; transition: all 0.2s !important;
}
.stButton > button:hover {
    background: var(--accent) !important;
    box-shadow: 0 4px 16px rgba(200,65,10,0.25) !important;
}

.stDateInput > div > div > input {
    border: 1px solid rgba(13,13,13,0.15) !important;
    border-radius: 2px !important; font-family: 'DM Sans', sans-serif !important;
    background: white !important;
}

[data-testid="metric-container"] {
    background: white; border: 1px solid rgba(13,13,13,0.07);
    border-radius: 3px; padding: 0.8rem 1rem;
}
[data-testid="metric-container"] [data-testid="stMetricLabel"] {
    font-family: 'DM Mono', monospace; font-size: 0.65rem;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--muted);
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-family: 'Playfair Display', serif; font-size: 2rem; font-weight: 700;
}

.streamlit-expanderHeader {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important; background: white !important;
    border-radius: 0 !important;
}
.streamlit-expanderContent {
    background: white !important;
    border-top: 1px solid rgba(13,13,13,0.06) !important;
}

.stProgress > div > div > div > div { background: var(--accent) !important; }
.stSpinner > div { border-top-color: var(--accent) !important; }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: var(--muted); border-radius: 2px; }

.stTabs [data-baseweb="tab-list"] {
    border-bottom: 2px solid rgba(13,13,13,0.08) !important; gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Mono', monospace !important; font-size: 0.72rem !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    padding: 0.5rem 1.2rem !important; border-radius: 0 !important;
}
.stTabs [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
}
</style>
""", unsafe_allow_html=True)


# ── Guard: must be logged in ──────────────────────────────────────────────────
init_db()

if "access_token" not in st.session_state or not st.session_state.access_token:
    st.warning("Please connect your Outlook account first.")
    if st.button("← Back to Login"):
        st.switch_page("app.py")
    st.stop()

token     = st.session_state.access_token
user_info = st.session_state.get("user_info", {})
user_email = user_info.get("mail") or user_info.get("userPrincipalName", "unknown")
user_name  = user_info.get("displayName", "there")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 1rem 0 1.5rem;">
        <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.18em;
                    text-transform:uppercase; color:#c8410a; margin-bottom:0.4rem;">
            ✦ MailMind
        </div>
        <div style="font-family:'Playfair Display',serif; font-size:1.3rem; font-weight:700;">
            {user_name}
        </div>
        <div style="font-size:0.78rem; color:#7a7065; margin-top:0.2rem;">{user_email}</div>
    </div>
    <hr style="border-color:rgba(13,13,13,0.1); margin: 0 0 1.5rem;">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="font-family:'DM Mono',monospace; font-size:0.65rem; letter-spacing:0.15em;
                text-transform:uppercase; color:#7a7065; margin-bottom:0.8rem;">
        Date Range
    </div>
    """, unsafe_allow_html=True)

    mode = st.radio(
        "Quick select",
        ["Today", "Last 3 Days", "Last Week", "Last 2 Weeks", "Custom"],
        label_visibility="collapsed"
    )

    today = date.today()
    if mode == "Today":
        start_d, end_d = today, today
    elif mode == "Last 3 Days":
        start_d, end_d = today - timedelta(days=2), today
    elif mode == "Last Week":
        start_d, end_d = today - timedelta(days=6), today
    elif mode == "Last 2 Weeks":
        start_d, end_d = today - timedelta(days=13), today
    else:
        start_d = st.date_input("From", today - timedelta(days=6))
        end_d   = st.date_input("To",   today)

    st.markdown("<br>", unsafe_allow_html=True)

    force_refresh = st.checkbox("Force re-fetch from Outlook", value=False)

    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("⚡  Analyze Emails", use_container_width=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.72rem; color:#b0a898; line-height:1.7;">
        <b>Priority Guide</b><br>
        🔴 High — Urgent action needed<br>
        🟡 Medium — Important, not urgent<br>
        ⚪ Low — FYI / no action needed
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    if st.button("🔓  Sign Out", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")


# ── Header ────────────────────────────────────────────────────────────────────
start_str = start_d.strftime("%d %b")
end_str   = end_d.strftime("%d %b %Y")
range_label = start_str if start_d == end_d else f"{start_str} – {end_str}"

st.markdown(f"""
<div style="padding: 2rem 0 1.5rem;">
    <div style="font-family:'DM Mono',monospace; font-size:0.68rem; letter-spacing:0.2em;
                text-transform:uppercase; color:#c8410a; margin-bottom:0.5rem;">
        Inbox Intelligence
    </div>
    <h1 style="font-family:'Playfair Display',serif; font-size:2.4rem;
               font-weight:900; margin:0; line-height:1.1;">
        {range_label}
    </h1>
</div>
<hr style="border-color:rgba(13,13,13,0.08); margin-bottom:1.5rem;">
""", unsafe_allow_html=True)


# ── Main Logic ────────────────────────────────────────────────────────────────
def render_email_card(email: dict, index: int):
    priority = email.get("priority", "MEDIUM")
    colors = {
        "HIGH":   ("#c8410a", "#fff4f0", "🔴"),
        "MEDIUM": ("#c9a84c", "#fffbf0", "🟡"),
        "LOW":    ("#7a7065", "#f5f5f5", "⚪"),
    }
    border_c, bg_c, dot = colors.get(priority, colors["MEDIUM"])

    received = email.get("received_at", "")
    if received and "T" in str(received):
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(str(received).replace("Z", "+00:00"))
            received_fmt = dt.strftime("%d %b, %I:%M %p")
        except Exception:
            received_fmt = str(received)[:16]
    else:
        received_fmt = str(received)[:16] if received else ""

    label = f"{dot} {email.get('subject', '(No Subject)')[:60]}"
    if email.get("sender_name"):
        label += f"  ·  {email['sender_name']}"

    with st.expander(label, expanded=(index == 0 and priority == "HIGH")):
        col_a, col_b = st.columns([2, 1])
        with col_a:
            st.markdown(f"""
            <div style="margin-bottom:0.8rem;">
                <span style="font-family:'DM Mono',monospace; font-size:0.65rem;
                             letter-spacing:0.12em; text-transform:uppercase;
                             color:white; background:{border_c};
                             padding:0.2rem 0.6rem; border-radius:2px;">
                    {priority}
                </span>
            </div>
            <div style="font-family:'Playfair Display',serif; font-size:1.05rem;
                        font-weight:700; margin-bottom:0.4rem; line-height:1.3;">
                {email.get('subject', '(No Subject)')}
            </div>
            <div style="font-size:0.82rem; color:#7a7065; margin-bottom:0.8rem;">
                From: <b>{email.get('sender_name','')}</b>
                &lt;{email.get('sender_email','')}&gt;
            </div>
            """, unsafe_allow_html=True)

            # Summary box
            st.markdown(f"""
            <div style="background:{bg_c}; border-left:3px solid {border_c};
                        padding:0.8rem 1rem; border-radius:0 3px 3px 0;
                        margin-bottom:0.8rem;">
                <div style="font-family:'DM Mono',monospace; font-size:0.62rem;
                            letter-spacing:0.12em; text-transform:uppercase;
                            color:{border_c}; margin-bottom:0.3rem;">
                    AI Summary
                </div>
                <div style="font-size:0.88rem; line-height:1.6; color:#0d0d0d;">
                    {email.get('summary','No summary available.')}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Body preview
            if email.get("body_preview"):
                st.markdown(f"""
                <div style="font-size:0.82rem; color:#7a7065; line-height:1.6;
                            border-top:1px solid rgba(13,13,13,0.07); padding-top:0.8rem;">
                    <span style="font-family:'DM Mono',monospace; font-size:0.6rem;
                                 letter-spacing:0.1em; text-transform:uppercase; color:#b0a898;">
                        Preview
                    </span><br>
                    {email.get('body_preview','')[:400]}…
                </div>
                """, unsafe_allow_html=True)

        with col_b:
            st.markdown(f"""
            <div style="text-align:right; font-family:'DM Mono',monospace;
                        font-size:0.72rem; color:#7a7065; padding-top:0.3rem;">
                {received_fmt}
            </div>
            """, unsafe_allow_html=True)


def render_emails_section(emails: list, title: str, color: str, icon: str):
    if not emails:
        return
    st.markdown(f"""
    <div style="margin: 2rem 0 0.8rem;">
        <div style="display:flex; align-items:center; gap:0.6rem;">
            <span style="font-size:1.1rem;">{icon}</span>
            <span style="font-family:'Playfair Display',serif; font-size:1.3rem;
                         font-weight:700;">{title}</span>
            <span style="font-family:'DM Mono',monospace; font-size:0.68rem;
                         letter-spacing:0.1em; background:{color}22;
                         color:{color}; padding:0.15rem 0.5rem; border-radius:2px;
                         margin-left:0.3rem;">{len(emails)}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    for i, email in enumerate(emails):
        render_email_card(email, i)


if run:
    if start_d > end_d:
        st.error("Start date must be before end date.")
        st.stop()

    start_str_db = start_d.isoformat()
    end_str_db   = end_d.isoformat()

    # Check cache
    if not force_refresh and emails_exist_for_range(user_email, start_str_db, end_str_db):
        emails = get_cached_emails(user_email, start_str_db, end_str_db)
        st.toast(f"✦ Loaded {len(emails)} emails from cache", icon="🗄️")
    else:
        # Fetch from Outlook
        with st.status("Fetching emails from Outlook…", expanded=True) as status:
            st.write("📬 Connecting to Microsoft Graph…")
            raw_emails = fetch_emails(token, start_str_db, end_str_db)
            st.write(f"📧 Found {len(raw_emails)} emails. Running AI analysis…")

            if not raw_emails:
                status.update(label="No emails found for this period.", state="error")
                st.stop()

            # Progress bar
            progress_bar = st.progress(0)
            progress_text = st.empty()

            def update_progress(current, total):
                progress_bar.progress(current / total)
                progress_text.markdown(f"""
                <div style="font-family:'DM Mono',monospace; font-size:0.72rem;
                            color:#7a7065; text-align:center; margin-top:0.3rem;">
                    Analyzing {current} / {total} emails…
                </div>
                """, unsafe_allow_html=True)

            enriched = batch_classify(raw_emails, progress_callback=update_progress)

            # Save to DB
            st.write("💾 Saving to database…")
            for email in enriched:
                upsert_email({
                    "id":           email["id"],
                    "user_email":   user_email,
                    "subject":      email.get("subject", ""),
                    "sender_name":  email.get("sender_name", ""),
                    "sender_email": email.get("sender_email", ""),
                    "received_at":  email.get("received_at", ""),
                    "body_preview": email.get("body_preview", ""),
                    "full_body":    email.get("full_body", ""),
                    "priority":     email.get("priority", "MEDIUM"),
                    "summary":      email.get("summary", ""),
                })

            status.update(label="✦ Analysis complete!", state="complete", expanded=False)
            emails = get_cached_emails(user_email, start_str_db, end_str_db)

    if not emails:
        st.info("No emails found for this date range.")
        st.stop()

    # ── Stats row ─────────────────────────────────────────────────────────────
    high   = [e for e in emails if e.get("priority") == "HIGH"]
    medium = [e for e in emails if e.get("priority") == "MEDIUM"]
    low    = [e for e in emails if e.get("priority") == "LOW"]

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Emails", len(emails))
    with c2: st.metric("🔴 High Priority", len(high))
    with c3: st.metric("🟡 Medium Priority", len(medium))
    with c4: st.metric("⚪ Low Priority", len(low))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_all, tab_high, tab_med, tab_low = st.tabs([
        f"All ({len(emails)})",
        f"High Priority ({len(high)})",
        f"Medium ({len(medium)})",
        f"Low / No Action ({len(low)})",
    ])

    with tab_all:
        render_emails_section(high,   "High Priority",       "#c8410a", "🔴")
        render_emails_section(medium, "Medium Priority",     "#c9a84c", "🟡")
        render_emails_section(low,    "Low / No Action Needed", "#7a7065", "⚪")

    with tab_high:
        if high:
            render_emails_section(high, "High Priority", "#c8410a", "🔴")
        else:
            st.markdown("""
            <div style="text-align:center; padding:3rem; color:#7a7065;
                        font-family:'Playfair Display',serif; font-size:1.1rem;">
                ✨ No high-priority emails — inbox looking good!
            </div>
            """, unsafe_allow_html=True)

    with tab_med:
        if medium:
            render_emails_section(medium, "Medium Priority", "#c9a84c", "🟡")
        else:
            st.info("No medium-priority emails.")

    with tab_low:
        if low:
            render_emails_section(low, "Low / No Action Needed", "#7a7065", "⚪")
        else:
            st.info("No low-priority emails.")

else:
    # Empty state
    st.markdown("""
    <div style="text-align:center; padding: 5rem 2rem;">
        <div style="font-size:3.5rem; margin-bottom:1.5rem; opacity:0.3;">✉</div>
        <div style="font-family:'Playfair Display',serif; font-size:1.5rem;
                    font-weight:700; color:#0d0d0d; margin-bottom:0.5rem;">
            Ready to Analyze
        </div>
        <div style="font-size:0.9rem; color:#7a7065; max-width:360px; margin:0 auto; line-height:1.7;">
            Select a date range from the sidebar and click <b>Analyze Emails</b> 
            to get AI-powered insights on your inbox.
        </div>
    </div>
    """, unsafe_allow_html=True)
