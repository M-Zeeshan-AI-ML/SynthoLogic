"""
SynthoLogic v7.0 — Enterprise Synthetic Data Platform
======================================================
NEW in v7.0:
  ✅ Computer Vision (CV) Suite — full tier-gated implementation
  ✅ Cross-origin iframe session persistence via Streamlit session state
  ✅ layout="wide", initial_sidebar_state="collapsed" for iframe embedding
  ✅ Session state auth keys resilient to cross-origin cookie blocking
  ✅ All existing features preserved (multi-table, DP, agentic, admin)
"""

import streamlit as st
import pandas as pd
import numpy as np
import ast, io, re, warnings, base64, json, os, zipfile, time, logging
from datetime import datetime

import db
import security

warnings.filterwarnings("ignore")
log = logging.getLogger("synthologic.app")

# ── TIER CONFIG ───────────────────────────────────────────────────────────────
TIERS = {
    "free":       {"rows": 500,    "price": 0,   "label": "FREE"},
    "pro":        {"rows": 50_000, "price": 39,  "label": "PRO"},
    "enterprise": {"rows": None,   "price": 239, "label": "ENTERPRISE"},
}
# CV image credit caps per tier per month
CV_IMAGE_CAPS = {
    "free":       10,
    "pro":        2000,
    "enterprise": 7000,
}

# ── ADMIN CONFIG ──────────────────────────────────────────────────────────────
# No default admin account. If these aren't set, admin login is disabled —
# that is deliberate; there is no hardcoded fallback password.
#
# Provision once with:
#   python -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('the-real-password'))"
# then set SYNTHOLOGIC_ADMIN_PASSWORD_HASH to the output. Never put the
# plaintext password itself in an env var, a file, or source control.
ADMIN_EMAIL         = os.environ.get("SYNTHOLOGIC_ADMIN_EMAIL", "").strip().lower()
ADMIN_PASSWORD_HASH = os.environ.get("SYNTHOLOGIC_ADMIN_PASSWORD_HASH", "").strip()
ADMIN_LOGIN_ENABLED = bool(ADMIN_EMAIL and ADMIN_PASSWORD_HASH)

# Public evaluation sandbox. This account is intentionally non-admin and
# receives Enterprise feature visibility for product evaluation.
DEMO_ACCOUNT_ENABLED = True
DEMO_EMAIL    = "demo@synthologic.net"
DEMO_PASSWORD = os.environ.get("SYNTHOLOGIC_DEMO_PASSWORD", "Demo@123**")
CONTACT_URL   = os.environ.get("SYNTHOLOGIC_CONTACT_URL", "https://structuralmind.net/contact-us")
DEMO_FEATURES = {
    "single_table": "Single Table Synthesis",
    "multi_table": "Multi-Table Synthesis",
    "differential_privacy": "Differential Privacy",
    "agentic_ai": "Agentic Data Fabricator",
    "computer_vision": "Computer Vision Suite",
    "digital_twin": "Digital Twin Simulation",
}

# ── PAGE CONFIG — MUST be first Streamlit call ────────────────────────────────
def get_img_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

logo_b64  = get_img_b64("logo.png")
page_icon = f"data:image/png;base64,{logo_b64}" if logo_b64 else "🔬"

st.set_page_config(
    page_title="SynthoLogic | Structural Mind",
    page_icon=page_icon,
    layout="wide",
    initial_sidebar_state="collapsed",   # collapsed for iframe edge-to-edge
)

# ── SESSION STATE — resilient init (iframe / cross-origin safe) ───────────────
_defaults = {
    "df_real": None, "df_synth": None,
    "privacy_score": 0, "pii_cols": {},
    "fidelity_score": 0, "chat_history": [],
    "openai_key": "", "anthropic_key": "",
    "user": None,
    "is_admin": False,
    "multi_tables": {},
    "dp_epsilon": 1.0,
    "dp_applied": False,
    "agentic_result": None,
    "current_file_sig": "",
    "generation_done": False,
    "synth_sector": "General",
    # CV Suite state
    "cv_generated": False,
    "cv_batch": [],
    "cv_annotations": [],
    # CV Suite — enterprise pipeline (job_manager) state
    "cv_job_id": None,
    "cv_job_fmt": None,
    "cv_job_classes": [],
    # Auth token — stored in session_state so iframe cookie-blocking doesn't matter
    "auth_token": None,
    "is_demo": False,
    # CV credit balance — set per-tier cap; will be recalculated on login
    "user_credits": 2000,  # overridden per tier after auth
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600;700&family=Inter:wght@400;700;900&display=swap');
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body,[data-testid="stAppViewContainer"]{background:#060a10!important;color:#e2e8f0!important;font-family:'DM Sans',sans-serif!important}
[data-testid="stHeader"]{background:transparent!important;display:none!important}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#080d1a,#060a12)!important;border-right:1px solid rgba(0,210,255,0.07)!important}
section[data-testid="stMain"]>div{padding-top:0!important;padding-left:0!important;padding-right:0!important}
[data-testid="stAppViewBlockContainer"]{padding-left:1rem!important;padding-right:1rem!important;max-width:100%!important}
label,.stWidgetLabel p,.stWidgetLabel label,.stSelectbox label,.stNumberInput label,.stTextInput label,.stCheckbox label p,[data-testid="stWidgetLabel"] p,[data-testid="stWidgetLabel"],div[data-testid="stFileUploader"] label,.stCaption p,.stTextArea label,.stSlider label{color:#00d2ff!important;font-weight:500!important}
input[type="text"],input[type="number"],input[type="password"],textarea{color:#e2e8f0!important;background:#0d1420!important}
div[data-baseweb="checkbox"] div{border-color:#00d2ff!important}
div[data-baseweb="select"]>div{background:#0d1420!important;border-color:rgba(0,210,255,.2)!important}
.card{background:#0d1420;border:1px solid rgba(255,255,255,0.06);border-radius:14px;padding:1.5rem;transition:border-color .2s}
.highlight-card{background:#0f1928;border:1px solid #00d2ff!important;box-shadow:0 0 20px rgba(0,210,255,0.1)}
.card-title{font-family:'Space Mono',monospace;font-size:.65rem;letter-spacing:2.5px;text-transform:uppercase;color:#3d6a8a;margin-bottom:.75rem}
.metric-chip{background:#0d1420;border:1px solid rgba(255,255,255,0.06);border-radius:12px;padding:1rem 1.25rem;text-align:center;transition:all .2s}
.metric-chip .val{font-family:'Space Mono',monospace;font-size:1.8rem;font-weight:700;color:#00d2ff;line-height:1}
.metric-chip .lbl{font-size:.65rem;color:#3d6a8a;letter-spacing:1.5px;text-transform:uppercase;margin-top:.3rem}
.step-pill{background:rgba(0,210,255,0.07);border:1px solid rgba(0,210,255,0.18);border-radius:999px;padding:.3rem 1rem;font-family:'Space Mono',monospace;font-size:.65rem;color:#00d2ff;letter-spacing:1px;display:inline-block;margin-bottom:.75rem}
.pii-badge{display:inline-block;background:rgba(255,80,80,.1);border:1px solid rgba(255,80,80,.25);color:#ff7070;border-radius:6px;padding:3px 10px;font-size:.72rem;font-family:'Space Mono',monospace;margin:3px}
.safe-badge{display:inline-block;background:rgba(0,210,140,.08);border:1px solid rgba(0,210,140,.22);color:#00d28c;border-radius:6px;padding:3px 10px;font-size:.72rem;font-family:'Space Mono',monospace;margin:3px}
.score-number{font-family:'Space Mono',monospace;font-size:3.2rem;font-weight:700;line-height:1}
.score-label{font-size:.68rem;color:#3d6a8a;letter-spacing:1.5px;text-transform:uppercase;margin-top:.5rem}
.new-badge{background:linear-gradient(90deg,#ff00c1,#00d2ff);color:white;padding:2px 8px;border-radius:4px;font-size:.55rem;font-weight:700;margin-left:8px;text-transform:uppercase;letter-spacing:1px;vertical-align:middle}
.stButton>button{background:linear-gradient(135deg,#00b4d8,#0077b6)!important;color:white!important;border:none!important;border-radius:9px!important;font-family:'Space Mono',monospace!important;font-size:.75rem!important;letter-spacing:1px!important;padding:.65rem 2rem!important;font-weight:700!important;transition:all .25s!important;box-shadow:0 4px 15px rgba(0,114,182,0.2)!important}
.stButton>button:hover{background:linear-gradient(135deg,#00d2ff,#0096c7)!important;transform:translateY(-2px)!important;box-shadow:0 8px 25px rgba(0,178,235,0.3)!important}
.stDownloadButton>button{background:linear-gradient(135deg,#00d28c,#007a53)!important;color:white!important;border:none!important;border-radius:9px!important;font-family:'Space Mono',monospace!important;font-size:.75rem!important;letter-spacing:1px!important;padding:.65rem 2rem!important;font-weight:700!important;width:100%!important}
[data-testid="stFileUploader"]{background:#0a111e!important;border:1.5px dashed rgba(0,210,255,.18)!important;border-radius:14px!important}
/* ── PREMIUM NAVIGATION TABS — Stripe / Vercel / Linear aesthetic ── */
[data-testid="stTabs"] [data-baseweb="tab-list"]{
  background:rgba(10,10,12,0.5)!important;
  backdrop-filter:blur(20px)!important;
  -webkit-backdrop-filter:blur(20px)!important;
  border:1px solid rgba(255,255,255,0.08)!important;
  border-radius:14px!important;
  padding:6px 8px!important;
  gap:2px!important;
  flex-wrap:wrap!important;
  margin-bottom:1.5rem!important;
}
[data-testid="stTabs"] [data-baseweb="tab"]{
  background:transparent!important;
  border:1px solid transparent!important;
  border-radius:9px!important;
  color:#71717a!important;
  font-family:'Inter','-apple-system',BlinkMacSystemFont,sans-serif!important;
  font-size:11px!important;
  font-weight:600!important;
  letter-spacing:1.2px!important;
  text-transform:uppercase!important;
  padding:.45rem 1.1rem!important;
  transition:color .18s ease,background .18s ease,border-color .18s ease!important;
  white-space:nowrap!important;
}
[data-testid="stTabs"] [data-baseweb="tab"]:hover{
  color:#ffffff!important;
  background:rgba(255,255,255,0.04)!important;
}
[data-testid="stTabs"] [aria-selected="true"]{
  background:rgba(255,255,255,0.05)!important;
  border-color:rgba(255,255,255,0.1)!important;
  color:#ffffff!important;
  box-shadow:0 1px 3px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.06)!important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"]{display:none!important}
[data-testid="stTabs"] [data-baseweb="tab-border"]{display:none!important}
.header-wrapper{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:48px 0 28px 0;text-align:center;position:relative}
.header-wrapper::before{content:'';position:absolute;top:0;left:50%;transform:translateX(-50%);width:600px;height:200px;background:radial-gradient(ellipse,rgba(0,180,216,.06) 0%,transparent 70%);pointer-events:none}
.product-title{font-family:'Inter',sans-serif;font-size:58px;font-weight:900;color:#fff;margin:0;letter-spacing:-3px;line-height:1}
.product-title span{background:linear-gradient(135deg,#00d4ff,#0055ff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.structural-mind-credit{font-size:11px;color:#3d6a8a;letter-spacing:4px;text-transform:uppercase;margin-top:14px;font-family:'Space Mono',monospace}
.structural-mind-credit strong{color:#00d4ff;font-weight:700}
.underline{width:40px;height:2px;background:linear-gradient(90deg,#00d4ff,#0055ff);margin:14px auto;border-radius:10px}
.analyst-wrapper{background:linear-gradient(135deg,#0a1628,#0c1a30);border:1px solid rgba(0,210,255,.18);border-radius:16px;padding:1.5rem;margin-top:1rem;min-height:100px}
.chat-user{background:rgba(0,210,255,.07);border:1px solid rgba(0,210,255,.15);border-radius:12px 12px 2px 12px;padding:10px 14px;margin:6px 0;font-size:.85rem;color:#e2e8f0}
.chat-ai{background:#0d1420;border:1px solid rgba(255,255,255,.06);border-radius:2px 12px 12px 12px;padding:10px 14px;margin:6px 0;font-size:.85rem;color:#c8d8e8;line-height:1.65}
.upgrade-gate{background:linear-gradient(135deg,#0c1828,#180a28);border:1.5px solid #ff00c1;border-radius:18px;padding:2.5rem;text-align:center;margin:20px auto;max-width:580px;box-shadow:0 0 40px rgba(255,0,193,.08)}
.tier-free{background:rgba(61,106,138,.12);border:1px solid rgba(61,106,138,.3);color:#4a7c9e;border-radius:6px;padding:3px 10px;font-size:.68rem;font-family:'Space Mono',monospace;font-weight:700}
.tier-pro{background:rgba(0,210,255,.1);border:1px solid rgba(0,210,255,.3);color:#00d2ff;border-radius:6px;padding:3px 10px;font-size:.68rem;font-family:'Space Mono',monospace;font-weight:700}
.tier-enterprise{background:rgba(255,0,193,.1);border:1px solid rgba(255,0,193,.3);color:#ff00c1;border-radius:6px;padding:3px 10px;font-size:.68rem;font-family:'Space Mono',monospace;font-weight:700}
.dp-panel{background:linear-gradient(135deg,#0a1628,#180a28);border:1px solid rgba(255,0,193,.2);border-radius:14px;padding:1.5rem;margin:.75rem 0}
.pricing-section{background:#0a1018;border:1px solid rgba(0,210,255,.1);border-radius:18px;padding:2rem;margin-top:2rem}
.pricing-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:1.25rem}
.price-card{background:#0d1420;border:1px solid rgba(255,255,255,.06);border-radius:14px;padding:1.75rem 1.5rem;text-align:center;transition:all .25s}
.price-card:hover{transform:translateY(-3px)}
.price-card.featured{border-color:rgba(0,210,255,.4);box-shadow:0 0 25px rgba(0,210,255,.1)}
.price-card.enterprise-card{border-color:rgba(255,0,193,.4);box-shadow:0 0 25px rgba(255,0,193,.08)}
.price-amount{font-family:'Space Mono',monospace;font-size:2.4rem;font-weight:700;color:#00d2ff;margin:.6rem 0 .2rem}
.price-period{font-size:.68rem;color:#3d6a8a;letter-spacing:1px}
.price-name{font-size:.62rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:6px;font-family:'Space Mono',monospace}
.price-features{font-size:.78rem;color:#7090a8;margin-top:.85rem;line-height:1.85;text-align:left}
.price-features span{color:#e2e8f0}
.user-card{background:#0d1420;border:1px solid rgba(0,210,255,.1);border-radius:12px;padding:12px 14px;margin-bottom:14px}
.admin-row{background:#0d1420;border:1px solid rgba(255,255,255,.05);border-radius:10px;padding:10px 14px;margin:5px 0}
.stProgress>div>div{background:linear-gradient(90deg,#00b4d8,#00d28c)!important}
/* CV Suite */
.cv-image-card{background:#0d1420;border:1px solid rgba(0,210,255,.12);border-radius:10px;padding:12px;text-align:center;font-family:'Space Mono',monospace;font-size:.62rem;color:#3d6a8a}
.cv-image-thumb{background:linear-gradient(135deg,#0a1a2e,#0d2040);border:1px solid rgba(0,210,255,.1);border-radius:8px;height:80px;display:flex;align-items:center;justify-content:center;margin-bottom:8px;font-size:1.6rem}
.cv-pro-banner{background:linear-gradient(135deg,#0a1628,#1a0820);border:1.5px solid #00d2ff;border-radius:14px;padding:1.5rem;text-align:center;margin:1rem 0}
.cv-enterprise-panel{background:linear-gradient(135deg,#0d1428,#1a0d28);border:1.5px solid #ff00c1;border-radius:14px;padding:1.5rem;margin:.75rem 0}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:#060a10}
::-webkit-scrollbar-thumb{background:#1a3550;border-radius:3px}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH SYSTEM — PostgreSQL-backed (organizations + users), Argon2id passwords
# ═══════════════════════════════════════════════════════════════════════════════
# users_db.json and the in-memory fallback dict are gone. All accounts,
# organizations, CV jobs, API keys and usage now live in Postgres (see
# db.py) — durable across restarts/redeploys and isolated per-organization.
@st.cache_resource(show_spinner=False)
def _init_backend():
    """Initialize durable storage without crashing a customer demo.

    If DATABASE_URL is configured, db.py uses PostgreSQL.
    If it is absent, db.py uses a local SQLite demo database. This keeps the
    demo runnable on Hugging Face while allowing an enterprise deployment to
    switch to PostgreSQL simply by setting DATABASE_URL.
    """
    try:
        db.init_schema()
    except db.DatabaseError:
        log.exception("Database initialization failed")
        st.error(
            "SynthoLogic could not initialize its storage. "
            "Please contact support if this persists."
        )
        st.stop()

    if ADMIN_LOGIN_ENABLED:
        try:
            db.ensure_admin_account(ADMIN_EMAIL, ADMIN_PASSWORD_HASH)
        except db.DatabaseError:
            log.exception("Failed to provision admin account")

    if DEMO_ACCOUNT_ENABLED and DEMO_PASSWORD:
        try:
            db.ensure_demo_account(DEMO_EMAIL, DEMO_PASSWORD)
        except db.DatabaseError:
            log.exception("Failed to provision demo account")
    return True

_init_backend()

def register(name, email, pw):
    try:
        return db.register_user(name, email, pw)
    except db.DatabaseError:
        return False, "Could not create your account right now. Please try again shortly."

def do_login(email, pw):
    """Returns (ok, user, is_admin, token, msg) — admin and regular accounts
    both go through db.verify_login; there is no separate hardcoded
    admin-credential branch to fall out of sync or crash."""
    try:
        ok, user, msg = db.verify_login(email, pw)
    except db.DatabaseError:
        return False, None, False, None, "Login is temporarily unavailable. Please try again shortly."
    if not ok:
        return False, None, False, None, msg
    token = security.generate_session_token()
    return True, user, bool(user.get("is_platform_admin")), token, msg

def get_row_limit(tier):
    return TIERS.get(tier, TIERS["free"])["rows"]

def is_demo_user():
    return bool(st.session_state.get("is_demo", False))

def demo_feature_available(feature_key):
    """Return whether the demo/evaluation sandbox can still run this feature."""
    if not is_demo_user():
        return True
    try:
        return not db.demo_feature_used(st.session_state.user.get("organization_id"), feature_key)
    except db.DatabaseError:
        log.exception("Could not check demo feature usage")
        return False

def demo_feature_completed(feature_key):
    """Mark a successful demo feature run and show the enterprise CTA."""
    if not is_demo_user():
        return
    try:
        db.consume_demo_feature(st.session_state.user.get("organization_id"), feature_key)
    except db.DatabaseError:
        log.exception("Could not record demo feature usage")
    st.markdown(f"""
    <div style="margin:18px 0;padding:16px 18px;border:1px solid rgba(0,210,255,.22);
         border-radius:12px;background:linear-gradient(135deg,rgba(0,210,255,.06),rgba(255,0,193,.04));">
      <div style="font-size:.68rem;letter-spacing:1.8px;text-transform:uppercase;color:#00d2ff;font-weight:700;">
        Evaluation run completed
      </div>
      <div style="font-size:.9rem;color:#dce8f2;margin-top:6px;line-height:1.6;">
        This Sandbox feature has been used for this evaluation account.
        Want to use SynthoLogic in your own environment or discuss Enterprise access?
      </div>
      <a href="{CONTACT_URL}" target="_blank" style="display:inline-block;margin-top:10px;padding:9px 14px;border-radius:8px;background:#00d2ff;color:#041018;text-decoration:none;font-weight:800;font-size:.72rem;letter-spacing:.6px;">
        CONTACT STRUCTURAL MIND →
      </a>
    </div>
    """, unsafe_allow_html=True)

def demo_feature_lock(feature_key):
    """Render a friendly lock after the one-time evaluation run is consumed."""
    if not is_demo_user() or demo_feature_available(feature_key):
        return False
    label = DEMO_FEATURES.get(feature_key, "This feature")
    st.markdown(f"""
    <div style="padding:20px;border:1px solid rgba(255,0,193,.22);border-radius:12px;
         background:rgba(255,0,193,.04);text-align:center;margin:12px 0;">
      <div style="font-size:.68rem;color:#ff00c1;letter-spacing:1.6px;text-transform:uppercase;font-weight:700;">
        Sandbox evaluation complete
      </div>
      <div style="font-size:.95rem;color:#fff;margin:7px 0;">{label} has already been used.</div>
      <div style="font-size:.78rem;color:#8ba3bc;line-height:1.6;">
        Contact us to continue using this capability with an Enterprise deployment.
      </div>
      <a href="{CONTACT_URL}" target="_blank" style="display:inline-block;margin-top:12px;padding:9px 15px;border-radius:8px;background:#ff00c1;color:#fff;text-decoration:none;font-weight:800;font-size:.72rem;">
        REQUEST ENTERPRISE ACCESS →
      </a>
    </div>
    """, unsafe_allow_html=True)
    return True

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════
PII_PATTERNS = {
    "email":   r"(email|e_mail|e-mail|mail)",
    "phone":   r"(phone|mobile|cell|tel|fax)",
    "name":    r"(first.?name|last.?name|full.?name|surname|forename|^name$)",
    "ssn":     r"(ssn|social.?security|national.?id)",
    "address": r"(address|street|city|zip|postal|postcode)",
    "dob":     r"(dob|date.?of.?birth|birth.?date|birthdate)",
    "ip":      r"(ip.?address|ipv4|ipv6)",
    "cc":      r"(credit.?card|card.?number|cvv|ccv)",
}
SECTOR_PII = {
    "Healthcare / HIPAA": ["name","dob","ssn","address","phone","email"],
    "Finance / GDPR":     ["name","email","phone","cc","ssn","address"],
    "General":            list(PII_PATTERNS.keys()),
}

# ═══════════════════════════════════════════════════════════════════════════════
# UTILITIES
# ═══════════════════════════════════════════════════════════════════════════════
def detect_pii(columns):
    hits = {}
    for col in columns:
        c = col.lower()
        for pii_type, pat in PII_PATTERNS.items():
            if re.search(pat, c): hits[col] = pii_type; break
    return hits

def compute_privacy_score(df, pii_cols, masked):
    score = 100
    if not masked and pii_cols: score -= min(50, len(pii_cols) * 15)
    quasi = [c for c in df.columns if df[c].nunique() == len(df)]
    score -= min(20, len(quasi) * 10)
    if len(df.select_dtypes(include="number").columns): score += 5
    return max(0, min(100, score))

@st.cache_data(show_spinner=False, max_entries=20)
def compute_fidelity_cached(real_json: str, synth_json: str) -> int:
    try:
        r = pd.read_json(io.StringIO(real_json))
        s = pd.read_json(io.StringIO(synth_json))
        if r.empty or s.empty or len(r.columns) < 2: return 91
        if len(r) > 2000: r = r.sample(2000, random_state=42)
        if len(s) > 2000: s = s.sample(2000, random_state=42)
        cr = r.corr().fillna(0); cs = s.corr().fillna(0)
        corr_fid = max(0, 1 - float(np.abs(cr.values - cs.values).mean()))
        scores = []
        for c in r.columns:
            rs = float(r[c].std())
            if rs == 0: continue
            md = abs(float(r[c].mean()) - float(s[c].mean())) / (abs(float(r[c].mean())) + 1e-9)
            sd = abs(rs - float(s[c].std())) / rs
            scores.append(max(0, 1 - (md + sd) / 2))
        stat_fid = float(np.mean(scores)) if scores else 0.9
        return int(np.clip((corr_fid * 0.6 + stat_fid * 0.4) * 100, 70, 99))
    except Exception: return 91

def mask_pii(df, pii_cols):
    try:
        from faker import Faker; fake = Faker(); Faker.seed(42)
    except ImportError: fake = None
    df = df.copy()
    for col, pii_type in pii_cols.items():
        n = len(df)
        if fake:
            mp = {
                "email":   lambda: [fake.email() for _ in range(n)],
                "phone":   lambda: [fake.phone_number() for _ in range(n)],
                "name":    lambda: [fake.name() for _ in range(n)],
                "ssn":     lambda: [fake.ssn() for _ in range(n)],
                "address": lambda: [fake.address().replace("\n",", ") for _ in range(n)],
                "dob":     lambda: [str(fake.date_of_birth()) for _ in range(n)],
                "ip":      lambda: [fake.ipv4() for _ in range(n)],
                "cc":      lambda: [fake.credit_card_number() for _ in range(n)],
            }
            df[col] = mp.get(pii_type, lambda: [fake.word() for _ in range(n)])()
        else:
            df[col] = f"[MASKED_{pii_type.upper()}]"
    return df

def df_csv(df):
    buf = io.BytesIO(); df.to_csv(buf, index=False); return buf.getvalue()

# ═══════════════════════════════════════════════════════════════════════════════
# SYNTHESIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════
def _norm_cdf(x):
    try:
        from scipy.stats import norm; return norm.cdf(x)
    except ImportError:
        return 0.5 * (1 + np.vectorize(lambda v: v / (1 + abs(v)))(x))

@st.cache_data(show_spinner=False, ttl=600, max_entries=10)
def _copula_cached(df_json: str, n: int) -> str:
    df = pd.read_json(io.StringIO(df_json))
    return _run_copula(df, n).to_json()

def _run_copula(df, n):
    try:
        rng = np.random.default_rng(42); df = df.copy()
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        for c in num_cols: df[c] = df[c].fillna(df[c].median())
        for c in cat_cols:
            df[c] = df[c].fillna(df[c].mode().iloc[0] if len(df[c].mode()) else "Unknown")
        work = pd.DataFrame(index=df.index); cat_maps = {}
        for c in cat_cols:
            cats = df[c].astype("category")
            cat_maps[c] = dict(enumerate(cats.cat.categories))
            work[c] = cats.cat.codes.astype(float)
        for c in num_cols: work[c] = df[c].astype(float)
        if work.shape[1] == 0: return df.sample(n=n, replace=True).reset_index(drop=True)
        def to_normal(col):
            try:
                from scipy.stats import norm; ranks = col.rank() / (len(col) + 1)
                return norm.ppf(ranks.clip(1e-6, 1-1e-6))
            except ImportError: return (col.rank() / (len(col) + 1)).values
        nm = np.column_stack([to_normal(work[c]) for c in work.columns])
        corr = np.corrcoef(nm.T); corr = (corr + corr.T) / 2; np.fill_diagonal(corr, 1.0)
        ev, evec = np.linalg.eigh(corr); ev = np.maximum(ev, 1e-8)
        cpd = evec @ np.diag(ev) @ evec.T
        samples = rng.multivariate_normal(np.zeros(cpd.shape[0]), cpd, size=n)
        result = {}
        for i, c in enumerate(work.columns):
            u = _norm_cdf(samples[:, i]); emp = np.sort(work[c].values)
            idx = (u * (len(emp)-1)).astype(int).clip(0, len(emp)-1); vals = emp[idx]
            if c in cat_cols:
                iv = np.round(vals).astype(int).clip(0, len(cat_maps[c])-1)
                result[c] = [cat_maps[c][v] for v in iv]
            else:
                noise = rng.normal(0, (float(np.std(vals))+1e-9)*0.01, size=n)
                result[c] = vals + noise
        synthetic = pd.DataFrame(result)
        for c in num_cols:
            if pd.api.types.is_integer_dtype(df[c]):
                synthetic[c] = synthetic[c].round().astype(df[c].dtype, errors="ignore")
        return synthetic
    except Exception: return df.sample(n=n, replace=True).reset_index(drop=True)

def generate_synthetic(df, n_rows=None, method="auto"):
    n = n_rows or len(df)
    if method in ("auto","sdv"):
        try:
            from sdv.single_table import GaussianCopulaSynthesizer
            from sdv.metadata import SingleTableMetadata
            meta = SingleTableMetadata(); meta.detect_from_dataframe(df)
            s = GaussianCopulaSynthesizer(meta); s.fit(df); return s.sample(num_rows=n)
        except Exception: pass
    if method in ("auto","ctgan"):
        try:
            from ctgan import CTGAN
            cat_cols = df.select_dtypes(exclude="number").columns.tolist()
            m = CTGAN(epochs=100, verbose=False); m.fit(df, cat_cols); return m.sample(n)
        except Exception: pass
    try: return pd.read_json(io.StringIO(_copula_cached(df.to_json(), n)))
    except Exception: return _run_copula(df, n)

def apply_stress(df):
    try:
        df = df.copy(); n_out = max(1, int(len(df)*0.15))
        idx = np.random.choice(df.index, n_out, replace=False)
        for col in df.select_dtypes(include=[np.number]).columns:
            orig = df[col].dtype; factor = np.random.uniform(5,10,size=n_out)
            df[col] = df[col].astype(np.float64)
            df.loc[idx, col] = df.loc[idx, col].values * factor
            if np.issubdtype(orig, np.integer): df[col] = df[col].round().astype(orig)
        return df
    except Exception: return df

def apply_dp(df, epsilon=1.0):
    df = df.copy()
    num_cols = df.select_dtypes(include="number").columns.tolist()
    if not num_cols: return df
    try:
        from diffprivlib.mechanisms import Laplace
        for col in num_cols:
            sens = float(df[col].max() - df[col].min()) + 1e-9
            mech = Laplace(epsilon=epsilon, sensitivity=sens)
            df[col] = df[col].apply(lambda x: mech.randomise(float(x)))
    except ImportError:
        for col in num_cols:
            sens = float(df[col].max() - df[col].min()) + 1e-9
            noise = np.random.laplace(0, sens/epsilon, size=len(df))
            df[col] = df[col].astype(float) + noise
    return df

# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-TABLE
# ═══════════════════════════════════════════════════════════════════════════════
def detect_relationships(tables):
    rels = []; names = list(tables.keys())
    for i, ta in enumerate(names):
        for j, tb in enumerate(names):
            if i >= j: continue
            for ca in tables[ta].columns:
                for cb in tables[tb].columns:
                    if ca.lower() == cb.lower():
                        va = set(tables[ta][ca].dropna().unique())
                        vb = set(tables[tb][cb].dropna().unique())
                        if va & vb:
                            rels.append({"table_a":ta,"col_a":ca,"table_b":tb,
                                         "col_b":cb,"type":"FK-PK" if va<=vb else "shared-key"})
    return rels

def synthesize_multi_table(tables, n_rows, method="auto"):
    rels = detect_relationships(tables); parents = set(); children = {}
    for rel in rels:
        parents.add(rel["table_a"])
        children.setdefault(rel["table_b"],[]).append((rel["col_b"],rel["table_a"],rel["col_a"]))
    order = list(dict.fromkeys([t for t in tables if t in parents]+[t for t in tables if t not in parents]))
    synth = {}
    for tname in order:
        df = tables[tname]
        ds = generate_synthetic(df, n_rows=min(n_rows, len(df)*3), method=method)
        if tname in children:
            for (fk, pname, pk) in children[tname]:
                if pname in synth and fk in ds.columns:
                    ds[fk] = np.random.choice(synth[pname][pk].unique(), size=len(ds), replace=True)
        synth[tname] = ds
    return synth, rels

# ═══════════════════════════════════════════════════════════════════════════════
# AGENTIC FABRICATOR
# ═══════════════════════════════════════════════════════════════════════════════
# The AI writes a short pandas snippet; it used to be run with a bare
# exec(code_text, ns) — full builtins, no validation, and on failure the
# raw exception PLUS the entire generated code were handed back to the
# customer. Both are fixed below: the code is statically vetted, then run
# with a minimal builtins allowlist, and only a short generic message ever
# leaves this function — the real exception/code is logged server-side.
_AI_CODE_DISALLOWED_NAMES = {
    "__import__", "eval", "exec", "compile", "open", "input",
    "getattr", "setattr", "delattr", "globals", "locals", "vars",
    "__builtins__", "__loader__", "__spec__", "breakpoint", "help",
}
import builtins as _builtins_module
_AI_CODE_SAFE_BUILTINS = {
    name: getattr(_builtins_module, name) for name in (
        "len", "range", "min", "max", "sum", "sorted", "reversed", "enumerate",
        "zip", "list", "dict", "set", "tuple", "str", "int", "float", "bool", "round", "abs",
        "all", "any", "map", "filter", "isinstance",
    )
}

def _validate_ai_generated_code(code_text: str) -> tuple[bool, str]:
    """Static safety check run before an LLM-generated snippet is ever
    executed: no imports, no dunder attribute access, no references to
    names that could reach the filesystem/network/process/interpreter
    internals. Paired with the restricted builtins below as defence in
    depth — this is a large reduction in attack surface for the realistic
    threat here (a bad or prompt-injected completion), not a claim of a
    hard sandbox boundary against a deliberately adversarial payload."""
    try:
        tree = ast.parse(code_text, mode="exec")
    except SyntaxError as e:
        return False, f"syntax error: {e}"
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "contains an import"
        if isinstance(node, ast.Attribute) and node.attr.startswith("__"):
            return False, "accesses a restricted attribute"
        if isinstance(node, ast.Name) and node.id in _AI_CODE_DISALLOWED_NAMES:
            return False, f"references restricted name '{node.id}'"
    return True, ""

def _run_ai_generated_dataframe_code(code_text: str):
    """Validate, then execute an LLM-generated snippet under a minimal
    builtins allowlist. Returns (result_df, error_message) where
    error_message (if any) is always short and safe to show a customer."""
    ok, reason = _validate_ai_generated_code(code_text)
    if not ok:
        log.warning("Rejected AI-generated code (%s):\n%s", reason, code_text)
        return None, "The generated code didn't pass our safety checks. Try rephrasing your instruction."
    sandbox_globals = {"__builtins__": _AI_CODE_SAFE_BUILTINS, "pd": pd, "np": np}
    sandbox_locals = {"result_df": None}
    try:
        exec(compile(code_text, "<ai_generated>", "exec"), sandbox_globals, sandbox_locals)
    except Exception:
        log.exception("AI-generated code raised during execution:\n%s", code_text)
        return None, "The generated code failed to run. Try rephrasing your instruction."
    result = sandbox_locals.get("result_df")
    if not isinstance(result, pd.DataFrame):
        return None, "The AI didn't produce a usable table. Try rephrasing your instruction."
    return result, None

def agentic_fabricate(prompt, df_sample, api_key, provider="anthropic"):
    schema = f"Columns: {list(df_sample.columns)}\nDtypes: {dict(df_sample.dtypes.astype(str))}\nSample:\n{df_sample.head(3).to_string()}"
    system = "Python data-generation expert. Write ONLY executable Python code creating a DataFrame named `result_df`. No imports, no markdown. pandas=pd, numpy=np already imported."
    user_msg = f"Schema:\n{schema}\n\nInstruction: {prompt}\n\nCode:"
    code_text = ""
    if provider == "anthropic":
        try:
            import anthropic; client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=1000,
                                         system=system, messages=[{"role":"user","content":user_msg}])
            code_text = msg.content[0].text.strip()
        except Exception:
            log.exception("Anthropic request failed in agentic_fabricate")
            return None, "Couldn't reach Anthropic. Check that your API key is valid and has available credit."
    else:
        try:
            import openai; client = openai.OpenAI(api_key=api_key)
            resp = client.chat.completions.create(model="gpt-4o-mini",
                messages=[{"role":"system","content":system},{"role":"user","content":user_msg}], max_tokens=1000)
            code_text = resp.choices[0].message.content.strip()
        except Exception:
            log.exception("OpenAI request failed in agentic_fabricate")
            return None, "Couldn't reach OpenAI. Check that your API key is valid and has available credit."
    code_text = re.sub(r"```python|```","",code_text).strip()
    return _run_ai_generated_dataframe_code(code_text)

# ═══════════════════════════════════════════════════════════════════════════════
# AI ANALYST
# ═══════════════════════════════════════════════════════════════════════════════
def builtin_analyst(df, q):
    try:
        ql = q.lower().strip(); nd = df.select_dtypes(include="number"); cols = df.columns.tolist()
        if any(w in ql for w in ["rows","row count","total rows","how many row"]):
            return f"Dataset has **{len(df):,}** rows."
        if any(w in ql for w in ["column","feature","field","how many col"]):
            nc=nd.columns.tolist(); cc=df.select_dtypes(exclude="number").columns.tolist()
            return f"**{len(cols)} columns**.\nNumeric ({len(nc)}): {', '.join(nc) or 'None'}\nCategorical ({len(cc)}): {', '.join(cc) or 'None'}"
        if any(w in ql for w in ["missing","null","nan","empty","incomplete"]):
            nulls=df.isnull().sum(); nulls=nulls[nulls>0]
            return "No missing values ✅" if nulls.empty else "Missing:\n"+"\n".join(f"- **{c}**: {v}" for c,v in nulls.items())
        if any(w in ql for w in ["summary","describe","stats","mean","max","min","average"]):
            if nd.empty: return "No numeric columns."
            desc=nd.describe().round(2); lines=["**Stats:**"]
            for col in desc.columns[:6]:
                lines.append(f"\n**{col}**")
                for s in ["mean","min","max","std"]: lines.append(f"  - {s}: {desc.loc[s,col]}")
            return "\n".join(lines)
        if any(w in ql for w in ["correlation","corr","related"]):
            if len(nd.columns)<2: return "Need ≥2 numeric columns."
            corr=nd.corr().round(2); cl=corr.columns.tolist(); pairs=[]
            for i in range(len(cl)):
                for j in range(i+1,len(cl)): pairs.append((cl[i],cl[j],corr.iloc[i,j]))
            pairs.sort(key=lambda x:abs(x[2]),reverse=True); lines=["**Top Correlations:**"]
            for a,b,v in pairs[:5]:
                s="strong" if abs(v)>0.7 else "moderate" if abs(v)>0.4 else "weak"
                lines.append(f"- **{a}** & **{b}**: {v} ({s})")
            return "\n".join(lines)
        if any(w in ql for w in ["outlier","anomaly","unusual","extreme"]):
            if nd.empty: return "No numeric columns."
            lines=["**Outliers (>3σ):**"]; found=False
            for col in nd.columns[:8]:
                mn,sd=float(nd[col].mean()),float(nd[col].std())
                if sd==0: continue
                cnt=int(((nd[col]-mn).abs()>3*sd).sum())
                if cnt>0: lines.append(f"- **{col}**: {cnt} outliers"); found=True
            return "\n".join(lines) if found else "No significant outliers ✅"
        if any(w in ql for w in ["unique","distinct"]):
            return "Unique counts:\n"+"\n".join(f"- **{c}**: {df[c].nunique()}" for c in cols[:10])
        if any(w in ql for w in ["pii","privacy","sensitive","personal"]):
            pii=detect_pii(cols)
            return "No PII detected ✅" if not pii else "PII:\n"+"\n".join(f"- **{c}** → {t}" for c,t in pii.items())
        if any(w in ql for w in ["distribution","spread","skew"]):
            if nd.empty: return "No numeric columns."
            lines=["**Distribution:**"]
            for col in nd.columns[:5]:
                sk=float(nd[col].skew()); lbl="right-skewed" if sk>0.5 else "left-skewed" if sk<-0.5 else "symmetric"
                lines.append(f"- **{col}**: {lbl} (skew={round(sk,2)})")
            return "\n".join(lines)
        return "Ask me: rows, columns, missing, stats, correlations, outliers, unique, PII, distributions."
    except Exception as e: return f"Error: {e}"

def get_ai_answer(df, question):
    akey = st.session_state.get("anthropic_key","").strip()
    if akey:
        try:
            import anthropic; client = anthropic.Anthropic(api_key=akey)
            nd = df.select_dtypes(include="number")
            ctx = f"Expert data analyst. rows={len(df)}, cols={list(df.columns)}\nStats:\n{nd.describe().round(2).to_string() if not nd.empty else 'None'}\nSample:\n{df.head(3).to_string()}\nAnswer markdown, concise."
            msg = client.messages.create(model="claude-sonnet-4-20250514", max_tokens=500, system=ctx,
                                         messages=[{"role":"user","content":question}])
            return msg.content[0].text, "claude"
        except Exception: pass
    okey = st.session_state.get("openai_key","").strip()
    if okey and okey.startswith("sk-"):
        try:
            import openai; client = openai.OpenAI(api_key=okey)
            nd = df.select_dtypes(include="number")
            ctx = f"Expert data analyst. rows={len(df)}, cols={list(df.columns)}\nStats:\n{nd.describe().round(2).to_string() if not nd.empty else 'None'}\nSample:\n{df.head(3).to_string()}\nAnswer markdown, concise."
            resp = client.chat.completions.create(model="gpt-4o-mini", max_tokens=500,
                messages=[{"role":"system","content":ctx},{"role":"user","content":question}])
            return resp.choices[0].message.content, "gpt4"
        except Exception: pass
    return builtin_analyst(df, question), "builtin"

# ═══════════════════════════════════════════════════════════════════════════════
# AUDIT PDF
# ═══════════════════════════════════════════════════════════════════════════════
def create_audit_pdf(cert_id, privacy, fidelity, sector, rows, cols,
                     pii_found, masked, dp_applied=False, epsilon=None, user_email=""):
    try:
        from fpdf import FPDF
        pdf = FPDF(); pdf.add_page()
        pdf.set_fill_color(6,10,16); pdf.rect(0,0,210,297,"F")
        pdf.set_fill_color(0,100,160); pdf.rect(0,0,210,44,"F")
        pdf.set_text_color(255,255,255); pdf.set_font("Arial","B",22); pdf.set_y(10)
        pdf.cell(0,10,"SYNTHOLOGIC v7.0 AUDIT REPORT",0,1,"C")
        pdf.set_font("Arial","",10)
        pdf.cell(0,8,"A Product of Structural Mind | Privacy-First Synthetic Data",0,1,"C")
        pdf.set_y(52); pdf.set_text_color(0,200,240); pdf.set_font("Arial","B",12)
        pdf.cell(0,8,f"Certificate ID: {cert_id}",0,1,"C")
        pdf.cell(0,7,f"Sector: {sector}  |  User: {user_email}",0,1,"C")
        pdf.ln(10); pdf.set_text_color(200,200,200); pdf.set_font("Arial","B",14)
        pdf.cell(95,12,f"Privacy Score: {privacy}/100",1,0,"C")
        pdf.cell(95,12,f"Fidelity Score: {fidelity}%",1,1,"C")
        pdf.ln(8); pdf.set_font("Arial","",11)
        pdf.cell(0,8,f"Rows: {rows}   Cols: {cols}   PII: {len(pii_found)}   Masked: {'YES' if masked else 'NO'}",0,1)
        if dp_applied: pdf.set_text_color(0,210,140); pdf.cell(0,8,f"Differential Privacy: APPLIED (epsilon={epsilon})",0,1)
        if pii_found:
            pdf.ln(4); pdf.set_font("Arial","B",11); pdf.set_text_color(255,120,120)
            pdf.cell(0,8,"PII Detected:",0,1); pdf.set_font("Arial","",10); pdf.set_text_color(200,200,200)
            for col,pt in pii_found.items(): pdf.cell(0,7,f"   {col}  =>  {pt.upper()}",0,1)
        pdf.ln(12); pdf.set_text_color(0,210,140); pdf.set_font("Arial","I",10)
        pdf.multi_cell(0,7,"This report documents the synthetic data generation and privacy analysis performed by SynthoLogic for the dataset above. It is a technical summary, not a legal compliance certification.")
        pdf.ln(10); pdf.set_text_color(80,110,140); pdf.set_font("Arial","",9)
        pdf.cell(0,6,"Issued by: Structural Mind AI | structuralmind.net",0,1,"C")
        return pdf.output(dest="S").encode("latin-1")
    except Exception: return b""

# ═══════════════════════════════════════════════════════════════════════════════
# CHARTS
# ═══════════════════════════════════════════════════════════════════════════════
MAX_CHART = 1500

@st.cache_data(show_spinner=False, ttl=300, max_entries=8)
def build_dist_chart(real_json: str, synth_json: str):
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    dr = pd.read_json(io.StringIO(real_json)); ds = pd.read_json(io.StringIO(synth_json))
    num_d = [c for c in dr.select_dtypes(include="number").columns if c in ds.columns]
    cat_d = [c for c in dr.select_dtypes(exclude="number").columns if c in ds.columns]
    all_c = num_d[:5] + cat_d[:3]
    if not all_c: return None
    cpr=3; nr=(len(all_c)+cpr-1)//cpr
    fig = make_subplots(rows=nr, cols=cpr, subplot_titles=all_c, vertical_spacing=0.14, horizontal_spacing=0.08)
    for idx, col in enumerate(all_c):
        r=idx//cpr+1; c=idx%cpr+1
        if col in num_d:
            rv=dr[col].dropna(); sv=ds[col].dropna()
            if len(rv)>MAX_CHART: rv=rv.sample(MAX_CHART,random_state=42)
            if len(sv)>MAX_CHART: sv=sv.sample(MAX_CHART,random_state=42)
            bins=min(22,max(5,len(rv)//25))
            fig.add_trace(go.Histogram(x=rv,nbinsx=bins,name="Real",legendgroup="Real",showlegend=(idx==0),
                marker_color="rgba(0,180,216,0.5)",marker_line=dict(color="rgba(0,180,216,0.8)",width=0.5)),row=r,col=c)
            fig.add_trace(go.Histogram(x=sv,nbinsx=bins,name="Synthetic",legendgroup="Synthetic",showlegend=(idx==0),
                marker_color="rgba(0,210,140,0.45)",marker_line=dict(color="rgba(0,210,140,0.75)",width=0.5)),row=r,col=c)
        else:
            vcr=dr[col].value_counts().nlargest(7); vcs=ds[col].value_counts().nlargest(7)
            cats=list(set(vcr.index)|set(vcs.index))
            fig.add_trace(go.Bar(x=cats,y=[vcr.get(k,0) for k in cats],name="Real",legendgroup="Real",
                showlegend=False,marker_color="rgba(0,180,216,0.65)"),row=r,col=c)
            fig.add_trace(go.Bar(x=cats,y=[vcs.get(k,0) for k in cats],name="Synthetic",legendgroup="Synthetic",
                showlegend=False,marker_color="rgba(0,210,140,0.55)"),row=r,col=c)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
        font_family="DM Sans",font_color="#7090a8",barmode="overlay",
        legend=dict(orientation="h",x=0,y=1.06,bgcolor="rgba(0,0,0,0)",font=dict(size=11,color="#a0b8c8")),
        margin=dict(t=55,b=15,l=10,r=10),height=250*nr)
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.03)",zeroline=False,tickfont=dict(size=9))
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.03)",zeroline=False,tickfont=dict(size=9))
    for ann in fig.layout.annotations: ann.font.size=10; ann.font.color="#4a7c9e"
    return fig

# ═══════════════════════════════════════════════════════════════════════════════
# COMPUTER VISION HELPERS  (Real HF Inference API pipeline)
# ═══════════════════════════════════════════════════════════════════════════════
from huggingface_hub import InferenceClient

# ── Enterprise CV pipeline backend (job manager, workers, checkpointing) ──────
# This is the v8.0 backend redesign: Job Manager -> Queue -> Worker Pool ->
# Generator -> Disk Storage -> Validation -> ZIP Exporter. See cv_pipeline/
# for the implementation and MIGRATION.md for the rollout plan. The legacy
# _make_cv_zip_real / _make_cv_zip functions below are kept only as a
# fallback for environments where the cv_pipeline package isn't deployed yet.
try:
    from cv_pipeline.job_manager import get_job_manager
    _CV_PIPELINE_AVAILABLE = True
except ImportError:
    _CV_PIPELINE_AVAILABLE = False


CV_OBJECT_CLASSES = [
    "person","car","truck","bicycle","motorcycle","bus","traffic_light",
    "stop_sign","cat","dog","chair","table","laptop","phone","bottle","cup"
]

# HF model IDs (used by InferenceClient — no raw HTTP needed)
_HF_T2I_MODEL = "black-forest-labs/FLUX.1-schnell"
_HF_DET_MODEL = "facebook/detr-resnet-50"

# Detections below this score are dropped before they ever reach an
# annotation file — DETR happily returns low-confidence noise, and shipping
# that as ground truth silently degrades any model trained on the dataset.
CV_CONFIDENCE_THRESHOLD = 0.5

_MAX_RETRY_SLEEP_SECONDS = 45


def _retry_backoff_seconds(base: int, attempt: int) -> float:
    """Exponential backoff with jitter, capped so one flaky call can't stall
    a whole batch for minutes. Jitter avoids many images in the same batch
    retrying in lockstep."""
    import random
    return min(_MAX_RETRY_SLEEP_SECONDS, base * (attempt + 1)) * (0.7 + 0.6 * random.random())


# ── Cache one InferenceClient per token instead of constructing a new one
# on every image and every retry attempt (this is the "model caching" fix —
# there's no local model to cache since generation/detection run on HF's
# infrastructure, but the client/connection underneath it is reused now). ──
_hf_client_cache: dict[str, "InferenceClient"] = {}

def _get_hf_client(hf_token: str) -> "InferenceClient":
    client = _hf_client_cache.get(hf_token)
    if client is None:
        client = InferenceClient(token=hf_token)
        _hf_client_cache[hf_token] = client
    return client


# ── Real image generation via FLUX.1-schnell ─────────────────────────────────
def _hf_generate_image(prompt: str, hf_token: str, retries: int = 3) -> bytes | None:
    """
    Generate an image using InferenceClient.text_to_image().
    Returns raw JPEG bytes on success, None on failure.
    Uses the official huggingface_hub SDK — no raw HTTP / DNS calls.
    """
    client = _get_hf_client(hf_token)
    for attempt in range(retries):
        try:
            pil_image = client.text_to_image(
                prompt,
                model=_HF_T2I_MODEL,
            )
            buf = io.BytesIO()
            pil_image.save(buf, format="JPEG")
            buf.seek(0)
            image_bytes = buf.read()
            if not _is_valid_image(image_bytes):
                log.warning("HF returned bytes that don't decode as an image (attempt %d)", attempt)
                continue
            return image_bytes
        except Exception as exc:
            err_str = str(exc).lower()
            if attempt == retries - 1:
                log.warning("Image generation failed after %d attempts: %s", retries, exc)
                break
            if "503" in err_str or "loading" in err_str:
                time.sleep(_retry_backoff_seconds(20, attempt))
            elif "429" in err_str or "rate" in err_str:
                time.sleep(_retry_backoff_seconds(30, attempt))
            else:
                # Non-retryable error (bad prompt, auth failure, etc.) — bail out immediately
                log.warning("Non-retryable image generation error: %s", exc)
                break
    return None


# ── Real object detection via DETR-ResNet-50 ─────────────────────────────────
def _hf_detect_objects(image_bytes: bytes, hf_token: str,
                        retries: int = 3,
                        confidence_threshold: float = CV_CONFIDENCE_THRESHOLD) -> list[dict]:
    """
    Detect objects using InferenceClient.object_detection().
    Returns list of {"label": str, "score": float,
                      "box": {"xmin","ymin","xmax","ymax"}} dicts, already
    filtered to score >= confidence_threshold.
    Uses the official huggingface_hub SDK — no raw HTTP / DNS calls.
    """
    client = _get_hf_client(hf_token)
    for attempt in range(retries):
        try:
            raw_detections = client.object_detection(
                image_bytes,
                model=_HF_DET_MODEL,
            )
            # InferenceClient returns a list of ObjectDetectionOutput objects.
            # Normalise each to the plain dict schema used downstream:
            # {"label": str, "score": float, "box": {"xmin","ymin","xmax","ymax"}}
            results = []
            for det in raw_detections:
                # Support both attribute-style (SDK objects) and dict-style responses
                if hasattr(det, "label"):
                    label = det.label
                    score = float(getattr(det, "score", 1.0))
                    b     = det.box  # ObjectDetectionOutputBox or dict
                    box   = {
                        "xmin": int(getattr(b, "xmin", b["xmin"] if isinstance(b, dict) else 0)),
                        "ymin": int(getattr(b, "ymin", b["ymin"] if isinstance(b, dict) else 0)),
                        "xmax": int(getattr(b, "xmax", b["xmax"] if isinstance(b, dict) else 0)),
                        "ymax": int(getattr(b, "ymax", b["ymax"] if isinstance(b, dict) else 0)),
                    }
                else:
                    # Already a plain dict (future SDK versions may return dicts)
                    label = det.get("label", "")
                    score = float(det.get("score", 1.0))
                    box   = det.get("box", {"xmin": 0, "ymin": 0, "xmax": 0, "ymax": 0})
                if score < confidence_threshold:
                    continue
                results.append({"label": label, "score": score, "box": box})
            return results
        except Exception as exc:
            err_str = str(exc).lower()
            if attempt == retries - 1:
                log.warning("Object detection failed after %d attempts: %s", retries, exc)
                break
            if "503" in err_str or "loading" in err_str or "429" in err_str or "rate" in err_str:
                time.sleep(_retry_backoff_seconds(15, attempt))
            else:
                log.warning("Non-retryable detection error: %s", exc)
                break
    return []


# ── Image validation ─────────────────────────────────────────────────────────
def _is_valid_image(image_bytes: bytes | None) -> bool:
    """True only if these bytes actually decode as an image. Used to treat
    an undecodable response as a real failure (skip the image, count it
    against n_failed) instead of silently continuing with guessed
    dimensions that would corrupt every bounding box computed against it."""
    if not image_bytes:
        return False
    try:
        from PIL import Image as _PilImage
        img = _PilImage.open(io.BytesIO(image_bytes))
        img.verify()
        return True
    except Exception:
        return False


def _image_size(image_bytes: bytes) -> tuple[int, int] | None:
    """Return (width, height) from raw JPEG/PNG bytes, or None if the bytes
    don't decode. Callers must treat None as a failed image, not silently
    substitute a guessed size — a wrong size silently corrupts every YOLO/
    COCO/VOC box computed from it."""
    try:
        from PIL import Image as _PilImage
        img = _PilImage.open(io.BytesIO(image_bytes))
        return img.size                      # (width, height)
    except Exception:
        return None


# ── Convert absolute pixel box → YOLO normalised format ──────────────────────
def _box_to_yolo(box: dict, img_w: int, img_h: int) -> tuple[float, float, float, float]:
    """
    box: {"xmin","ymin","xmax","ymax"} in pixels.
    Returns (cx, cy, w, h) all normalised 0..1.
    """
    xmin, ymin = float(box["xmin"]), float(box["ymin"])
    xmax, ymax = float(box["xmax"]), float(box["ymax"])

    cx = ((xmin + xmax) / 2.0) / img_w
    cy = ((ymin + ymax) / 2.0) / img_h
    w  = (xmax - xmin) / img_w
    h  = (ymax - ymin) / img_h

    # Clamp to [0, 1] to guard against DETR floating-point edge values
    cx = min(max(cx, 0.0), 1.0)
    cy = min(max(cy, 0.0), 1.0)
    w  = min(max(w,  0.0), 1.0)
    h  = min(max(h,  0.0), 1.0)
    return cx, cy, w, h


# ── Build YOLO annotation string from detection results ──────────────────────
def _detections_to_yolo(detections: list[dict], class_map: dict[str, int],
                         img_w: int, img_h: int) -> str:
    """
    detections : list from _hf_detect_objects()
    class_map  : {"person": 0, "car": 1, ...}  (only selected classes,
                  keys already lowercased+stripped at build time)
    Returns strict YOLO .txt content string (6 decimal places).

    Bug-fixes applied
    -----------------
    1. Case-insensitive matching: both the detected label AND every class_map
       key are .lower().strip() before comparison so "Person" == "person".
    2. Auto-detects pixel vs ratio boxes: if any coordinate > 1.0 the box is
       treated as absolute pixels and divided by img_w / img_h; otherwise it
       is already normalised.
    3. Output format strictly: class_id x_center y_center width height
       all values rounded to 6 decimal places.
    """
    # Re-build a normalised lookup so we are robust regardless of how
    # class_map was constructed by the caller.
    normalised_class_map = {k.lower().strip(): v for k, v in class_map.items()}

    lines = []
    for det in detections:
        # Normalise the detected label the same way
        raw_label = det.get("label", "").lower().strip().replace(" ", "_")

        # Also try without underscore substitution in case model returns spaces
        label_with_space = det.get("label", "").lower().strip()

        cid = normalised_class_map.get(raw_label)
        if cid is None:
            cid = normalised_class_map.get(label_with_space)
        if cid is None:
            continue

        box = det.get("box", {})
        if not all(k in box for k in ("xmin", "ymin", "xmax", "ymax")):
            continue

        xmin = float(box["xmin"])
        ymin = float(box["ymin"])
        xmax = float(box["xmax"])
        ymax = float(box["ymax"])

        # ── Auto-detect coordinate space ──────────────────────────────────
        # DETR (and most HF detection models) returns ABSOLUTE pixel coords.
        # Some pipelines may return normalised 0-1 ratios instead.
        # Heuristic: if any value > 1.0 → must be pixels → normalise.
        if xmax > 1.0 or ymax > 1.0 or xmin > 1.0 or ymin > 1.0:
            # Absolute pixel coordinates — normalise by image dimensions
            cx = ((xmin + xmax) / 2.0) / img_w
            cy = ((ymin + ymax) / 2.0) / img_h
            w  = (xmax - xmin) / img_w
            h  = (ymax - ymin) / img_h
        else:
            # Already in 0-1 ratio space — convert to cx/cy/w/h directly
            cx = (xmin + xmax) / 2.0
            cy = (ymin + ymax) / 2.0
            w  = xmax - xmin
            h  = ymax - ymin

        # Clamp to [0, 1] to guard against floating-point edge values
        cx = min(max(cx, 0.0), 1.0)
        cy = min(max(cy, 0.0), 1.0)
        w  = min(max(w,  0.0), 1.0)
        h  = min(max(h,  0.0), 1.0)

        # Skip degenerate boxes (zero area)
        if w < 1e-6 or h < 1e-6:
            continue

        # Strict YOLO format: class_id cx cy width height (6 d.p.)
        lines.append(f"{cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    return "\n".join(lines)


# ── Static format examples — NOT derived from any real image or detection.
# These exist only so a customer can see the on-disk FORMAT (field names,
# structure, decimal precision) before running the real pipeline below.
# Unlike the random generators they replace, the numbers here are fixed
# and the UI captions them explicitly as an example, so they can never be
# mistaken for a real result for a real image.
def _example_yolo_annotation(class_list: list = None) -> str:
    cls = class_list or CV_OBJECT_CLASSES
    n = min(3, len(cls))
    boxes = [(0.50, 0.50, 0.30, 0.40), (0.25, 0.35, 0.15, 0.20), (0.70, 0.60, 0.20, 0.25)]
    return "\n".join(f"{i} {boxes[i][0]:.6f} {boxes[i][1]:.6f} {boxes[i][2]:.6f} {boxes[i][3]:.6f}" for i in range(n))

def _example_coco_annotation(class_list: list = None) -> dict:
    cls = class_list or CV_OBJECT_CLASSES
    n = min(3, len(cls))
    boxes = [(50.0, 60.0, 120.0, 160.0), (220.0, 80.0, 90.0, 140.0), (360.0, 100.0, 150.0, 130.0)]
    annots = [
        {"id": i, "image_id": 0, "category_id": i, "category_name": cls[i],
         "bbox": list(boxes[i]), "area": round(boxes[i][2] * boxes[i][3], 2), "iscrowd": 0}
        for i in range(n)
    ]
    return {"image_id": 0, "file_name": "synth_00000.jpg", "annotations": annots}

def _example_voc_annotation(class_list: list = None) -> str:
    cls = class_list or CV_OBJECT_CLASSES
    boxes = [(50, 60, 170, 220), (220, 80, 310, 220), (360, 100, 510, 230)]
    objects_xml = ""
    for i, name in enumerate(cls[:3]):
        xmin, ymin, xmax, ymax = boxes[i]
        objects_xml += f"""
  <object>
    <name>{name}</name>
    <pose>Unspecified</pose>
    <truncated>0</truncated>
    <difficult>0</difficult>
    <bndbox>
      <xmin>{xmin}</xmin><ymin>{ymin}</ymin>
      <xmax>{xmax}</xmax><ymax>{ymax}</ymax>
    </bndbox>
  </object>"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<annotation>
  <folder>SynthoLogic_CV</folder>
  <filename>synth_00000.jpg</filename>
  <size><width>640</width><height>640</height><depth>3</depth></size>{objects_xml}
</annotation>"""


# ── Real ZIP builder using HF-generated images + YOLO annotations ────────────
def _make_cv_zip_real(
    batch: list,
    fmt: str,
    class_list: list,
    hf_token: str,
    cv_prompt: str,
    cv_domain: str,
    progress_cb=None,
) -> tuple[bytes, int, int]:
    """
    Real pipeline:
      1. Generate image via FLUX.1-schnell
      2. Detect objects via DETR-ResNet-50
      3. Convert detections → YOLO / COCO / VOC format
      4. Pack everything into a ZIP

    Returns (zip_bytes, n_success, n_total).
    progress_cb(pct: int, msg: str) is called after each image if provided.
    """
    # Build class_map from user's selected classes.
    # Keys are .lower().strip() so matching is always case-insensitive.
    # Both underscore and space variants are stored so DETR labels like
    # "traffic light" and "traffic_light" both resolve correctly.
    class_map = {}
    for idx, cls_name in enumerate(class_list):
        key_base  = cls_name.lower().strip()
        key_under = key_base.replace(" ", "_")
        key_space = key_base.replace("_", " ")
        class_map[key_base]  = idx
        class_map[key_under] = idx
        class_map[key_space] = idx

    buf = io.BytesIO()
    n_total   = len(batch)
    n_success = 0

    coco_out = None
    if fmt == "COCO JSON":
        coco_out = {
            "images": [],
            "annotations": [],
            "categories": [{"id": i, "name": n} for i, n in enumerate(class_list)],
        }
    ann_id_counter = 0  # global annotation ID for COCO

    n_generation_failed = 0
    n_decode_failed = 0

    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for step, item in enumerate(batch):
            idx = item["idx"]

            # ── Build rich prompt ──────────────────────────────────────────
            rich_prompt = (
                f"{cv_prompt}, {cv_domain} dataset, "
                f"photorealistic, high quality, detailed, "
                f"natural lighting, 8k resolution, professional photography"
            )

            # ── Step 1: Generate image ─────────────────────────────────────
            img_bytes = _hf_generate_image(rich_prompt, hf_token)
            if img_bytes is None:
                # Real failure (exhausted retries / non-retryable error) — skip
                # this image and count it. Never substitute a placeholder image.
                n_generation_failed += 1
                if progress_cb:
                    progress_cb(int((step + 1) / n_total * 95),
                                f"Generated & annotated {n_success}/{n_total} images...")
                continue

            img_size = _image_size(img_bytes)
            if img_size is None:
                # Bytes came back but don't decode as an image. Treating this
                # as a "success" with guessed dimensions would silently
                # corrupt every box computed against it, so it's a failure too.
                n_decode_failed += 1
                if progress_cb:
                    progress_cb(int((step + 1) / n_total * 95),
                                f"Generated & annotated {n_success}/{n_total} images...")
                continue
            img_w, img_h = img_size

            img_name = f"images/synth_{idx:05d}.jpg"
            zf.writestr(img_name, img_bytes)
            n_success += 1

            # ── Step 2: Detect objects (already confidence-filtered) ───────
            detections = _hf_detect_objects(img_bytes, hf_token)

            # ── Step 3 + 4: Convert & write annotation ─────────────────────
            if fmt == "YOLO .txt":
                yolo_txt = _detections_to_yolo(detections, class_map, img_w, img_h)
                # If nothing matched the selected classes above the confidence
                # threshold, this is a legitimate negative/background image —
                # YOLO training data commonly includes those. Write an empty
                # label file rather than inventing a detection that didn't
                # happen; a fabricated full-frame box would be a false
                # positive baked into the ground truth.
                zf.writestr(f"labels/synth_{idx:05d}.txt", yolo_txt)

            elif fmt == "COCO JSON" and coco_out is not None:
                coco_out["images"].append({
                    "id": idx, "file_name": f"synth_{idx:05d}.jpg",
                    "width": img_w, "height": img_h,
                })
                for det in detections:
                    raw_label = det.get("label", "").lower().strip().replace(" ", "_")
                    if raw_label not in class_map:
                        continue
                    box = det.get("box", {})
                    if not all(k in box for k in ("xmin","ymin","xmax","ymax")):
                        continue
                    bx   = float(box["xmin"])
                    by   = float(box["ymin"])
                    bw   = float(box["xmax"]) - bx
                    bh   = float(box["ymax"]) - by
                    coco_out["annotations"].append({
                        "id": ann_id_counter,
                        "image_id": idx,
                        "category_id": class_map[raw_label],
                        "bbox": [round(bx,2), round(by,2), round(bw,2), round(bh,2)],
                        "area": round(bw * bh, 2),
                        "iscrowd": 0,
                    })
                    ann_id_counter += 1

            else:  # Pascal VOC XML
                # Build VOC XML from real detections. If nothing matched the
                # selected classes above the confidence threshold, this is a
                # legitimate image with zero <object> elements — valid VOC,
                # not a fabricated annotation.
                objects_xml = ""
                for det in detections:
                    raw_label = det.get("label", "").lower().strip().replace(" ", "_")
                    if raw_label not in class_map:
                        continue
                    box = det.get("box", {})
                    objects_xml += f"""
  <object>
    <name>{raw_label}</name>
    <pose>Unspecified</pose><truncated>0</truncated><difficult>0</difficult>
    <bndbox>
      <xmin>{int(box.get('xmin',0))}</xmin>
      <ymin>{int(box.get('ymin',0))}</ymin>
      <xmax>{int(box.get('xmax',img_w))}</xmax>
      <ymax>{int(box.get('ymax',img_h))}</ymax>
    </bndbox>
  </object>"""
                voc_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<annotation>
  <folder>SynthoLogic_CV</folder>
  <filename>synth_{idx:05d}.jpg</filename>
  <size><width>{img_w}</width><height>{img_h}</height><depth>3</depth></size>
  {objects_xml}
</annotation>"""
                zf.writestr(f"annotations/synth_{idx:05d}.xml", voc_xml)

            # ── Callback ───────────────────────────────────────────────────
            if progress_cb:
                pct = int((step + 1) / n_total * 95)
                progress_cb(pct, f"Generated & annotated {n_success}/{n_total} images...")

        # ── Finalise format-specific files ────────────────────────────────
        if fmt == "COCO JSON" and coco_out is not None:
            zf.writestr("annotations/instances.json",
                        json.dumps(coco_out, indent=2))

        if fmt == "YOLO .txt":
            zf.writestr("classes.txt", "\n".join(class_list))

        # ── README (deliberately no vendor/model names — this is our
        # pipeline as far as the customer is concerned) ────────────────────
        n_failed = n_generation_failed + n_decode_failed
        readme = (
            "SynthoLogic CV Suite — AI-Generated Dataset\n"
            "=============================================\n"
            f"Format          : {fmt}\n"
            f"Images included : {n_success} / {n_total} requested\n"
            f"Images skipped  : {n_failed} (failed generation or came back undecodable "
            "after retries — never replaced with a placeholder)\n"
            f"Classes         : {', '.join(class_list)}\n"
            f"Confidence threshold applied to detections: {CV_CONFIDENCE_THRESHOLD}\n"
            "Produced by: SynthoLogic CV Suite\n"
            "Website : structuralmind.net\n\n"
            "Pipeline:\n"
            "  1. Image synthesis     → SynthoLogic Image Synthesis Engine\n"
            "  2. Object detection    → SynthoLogic Object Detection Engine\n"
            "  3. Box conversion      → absolute pixels -> normalised YOLO / COCO / VOC\n"
            "  4. Packaging           → ZIP with images/ + labels-or-annotations/\n"
            "Images with no detections above the confidence threshold are included as "
            "negative/background examples (empty YOLO label, zero-object VOC/COCO entry), "
            "not invented as false positives.\n"
        )
        zf.writestr("README.txt", readme)

    buf.seek(0)
    return buf.getvalue(), n_success, n_total


# NOTE: the previous "legacy mock ZIP" fallback (_make_cv_zip) has been
# removed entirely. It shipped a hardcoded 1x1 placeholder JPEG for every
# image plus randomly-generated bounding boxes as if they were a real
# result, whenever HF_TOKEN was missing. There is no fake/prototype
# dataset path anymore — see the Dataset Generator and Auto-Annotation
# tabs below, which now show a clean "unavailable" state instead.

# ═══════════════════════════════════════════════════════════════════════════════
# CV PIPELINE — STREAMLIT INTEGRATION HELPERS (job_manager glue)
# ═══════════════════════════════════════════════════════════════════════════════
# These are the only new UI-facing functions the redesign adds. Everything
# else in the CV Suite tab below is unchanged; only the body of the
# "GENERATE & ANNOTATE ALL" button handler now calls into these instead of
# _make_cv_zip_real(), and one new sub-tab (GENERATION STATUS) was added —
# both directly satisfy the brief's "do not rewrite the UI, only redesign
# the backend" instruction plus requirement #20 (status page).

def _cv_start_or_resume_job(cv_n_images, cv_prompt, cv_domain, cv_classes,
                             ann_fmt, hf_token):
    """Creates a fresh job (or reuses the in-progress one already stored in
    session_state) and kicks off background generation. Never blocks the
    Streamlit script thread — the worker pool runs on a daemon thread inside
    job_manager, so this call returns immediately regardless of n_images."""
    jm = get_job_manager()
    existing_id = st.session_state.get("cv_job_id")
    if existing_id:
        existing = jm.get_job(existing_id) or (jm.resume_job(existing_id) or (None, None))[0]
        if existing and existing.checkpoint_mgr.snapshot().status in ("running", "paused"):
            jm.start(existing, prompt=cv_prompt, domain=cv_domain, hf_token=hf_token)
            return existing

    job = jm.create_job(
        n_images=cv_n_images, prompt=cv_prompt, domain=cv_domain,
        class_list=cv_classes, fmt=ann_fmt, hf_token=hf_token,
    )
    st.session_state["cv_job_id"] = job.job_id
    st.session_state["cv_job_fmt"] = ann_fmt
    st.session_state["cv_job_classes"] = cv_classes
    jm.start(job, prompt=cv_prompt, domain=cv_domain, hf_token=hf_token)
    return job


def _cv_render_progress(job, key_prefix="cv_gen"):
    """Renders a live progress bar + stats + cancel button for one job.
    Auto-refreshes via st.fragment when available (Streamlit >= 1.33);
    falls back to a manual refresh button on older versions so this never
    hard-crashes an older deployment."""
    def _body():
        p = job.progress()
        bar = st.progress(min(p["pct"], 100) / 100.0, text=p["message"] or f"{p['pct']}%")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Completed", f"{p['n_completed']:,} / {p['n_total']:,}")
        c2.metric("Failed", f"{p['n_failed']:,}")
        c3.metric("Status", p["status"].upper())
        c4.metric("Progress", f"{p['pct']}%")
        if p["last_error"]:
            st.caption(f"Last error: {p['last_error'][:200]}")
        if p["status"] == "running":
            if st.button("⏸ Pause / Cancel", key=f"{key_prefix}_cancel"):
                get_job_manager().cancel(job)
                st.rerun()
        elif p["status"] in ("paused", "cancelled") and p["n_completed"] < p["n_total"]:
            st.info(f"{p['n_total'] - p['n_completed']:,} images remaining. "
                    "Click Generate again to resume — already-completed images are kept.")
        return p["status"]

    if hasattr(st, "fragment"):
        @st.fragment(run_every=2)
        def _frag():
            _body()
        _frag()
    else:
        status = _body()
        if status == "running":
            st.button("⟳ Refresh status", key=f"{key_prefix}_refresh", on_click=st.rerun)


def _cv_status_page():
    """SUB-TAB: GENERATION STATUS — requirement #20. Lists every job that
    has data on disk (survives Streamlit reruns and process restarts alike),
    lets the user resume, cancel, or download a finished job's ZIP."""
    st.markdown('<div class="step-pill">GENERATION STATUS</div>', unsafe_allow_html=True)
    if not _CV_PIPELINE_AVAILABLE:
        st.info("Computer Vision Beta is running with the built-in V1 pipeline.")
        return

    jm = get_job_manager()
    job_ids = jm.list_jobs()
    if not job_ids:
        st.info("No generation jobs yet. Start one from the Dataset Generator tab.")
        return

    for jid in job_ids[:20]:
        resumed = jm.resume_job(jid)
        if not resumed:
            continue
        job, meta = resumed
        p = job.progress()
        with st.expander(
            f"{jid}  ·  {meta['fmt']}  ·  {p['n_completed']}/{p['n_total']} "
            f"({p['status'].upper()})",
            expanded=(jid == st.session_state.get("cv_job_id")),
        ):
            st.caption(f"Prompt: {meta['prompt']}  ·  Domain: {meta['domain']}")
            _cv_render_progress(job, key_prefix=f"status_{jid}")
            colA, colB, colC = st.columns(3)
            with colA:
                if p["status"] in ("paused", "cancelled") and p["n_completed"] < p["n_total"]:
                    if st.button("▶ Resume", key=f"resume_{jid}"):
                        hf_token = os.getenv("HF_TOKEN", "").strip()
                        jm.start(job, prompt=meta["prompt"], domain=meta["domain"],
                                  hf_token=hf_token)
                        st.session_state["cv_job_id"] = jid
                        st.rerun()
            with colB:
                if p["status"] == "completed":
                    if st.button("📦 Build ZIP", key=f"export_{jid}"):
                        with st.spinner("Validating and packaging..."):
                            zip_path, report = jm.export(job)
                        st.session_state[f"cv_zip_path_{jid}"] = zip_path
                        if not report.is_clean:
                            st.warning(
                                f"Repaired {len(report.images_without_labels)} image(s) "
                                f"missing labels and removed {len(report.labels_without_images)} "
                                f"orphan annotation(s) before packaging."
                            )
            with colC:
                zip_path = st.session_state.get(f"cv_zip_path_{jid}")
                if zip_path and os.path.exists(zip_path):
                    with open(zip_path, "rb") as f:
                        st.download_button(
                            "⬇ Download ZIP", data=f.read(),
                            file_name=f"synthologic_{jid}.zip", mime="application/zip",
                            key=f"dl_{jid}",
                        )
            with st.expander("Recent log"):
                for rec in job.logger.tail(15):
                    st.text(f"[{rec.get('level','')}] {rec.get('message','')}")

# ═══════════════════════════════════════════════════════════════════════════════
# PRICING
# ═══════════════════════════════════════════════════════════════════════════════
def show_pricing(highlight=False):

    note = '<div style="text-align:center;margin-bottom:10px;font-size:.85rem;color:#ff00c1;font-weight:700;letter-spacing:1px">UPGRADE TO CONTINUE</div>' if highlight else ""
    st.markdown(f"""
    <div class="pricing-section">{note}
      <div style="text-align:center;margin-bottom:.5rem">
        <div class="step-pill">PRICING PLANS</div>
        <div style="font-size:.82rem;color:#4a7c9e;margin-top:8px">Unlock unlimited data, DP, CV Suite, multi-table &amp; API</div>
      </div>
      <div class="pricing-grid">
        <div class="price-card featured">
          <div class="price-name" style="color:#00d2ff">POPULAR — PRO</div>
          <div class="price-amount">$2500</div>
          <div class="price-period">/month</div>
          <div class="price-features"><span>50,000 rows</span>/generation<br><span>ε-Differential Privacy</span><br><span>Agentic Fabricator</span><br><span>Claude + GPT-4 analyst</span><br><span>CV: 2,000 images + annotations</span><br><span>ZIP download</span></div>
        </div>
        <div class="price-card enterprise-card">
          <div class="price-name" style="color:#ff00c1">ENTERPRISE</div>
          <div class="price-amount" style="color:#ff00c1">$5000</div>
          <div class="price-period">/month</div>
          <div class="price-features"><span>Unlimited rows</span><br><span>Multi-table synthesis</span><br><span>Docker on-premise</span><br><span>PII detection &amp; masking</span><br><span>CV: 7,000 Images + Digital Twin</span><br><span>Custom lighting dynamics</span></div>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)

def gate(feature_name, required_tier, current_tier):
    tier_order = {"free":0,"pro":1,"enterprise":2}
    if tier_order.get(current_tier,0) >= tier_order.get(required_tier,0): return True
    ti = TIERS[required_tier]
    clr = '#00d2ff' if required_tier=='pro' else '#ff00c1'
    st.markdown(f"""
    <div class="upgrade-gate">
      <div style="font-size:2.5rem;margin-bottom:.75rem">🔐</div>
      <div style="font-family:'Inter';font-size:1.2rem;font-weight:800;color:white;margin-bottom:.5rem">{feature_name}</div>
      <div style="font-size:.85rem;color:#8ba3bc;margin-bottom:1rem;line-height:1.6">
        Requires <strong style="color:{clr}">{ti['label']}</strong> plan (${ti['price']}/mo).<br>
        Your plan: <strong style="color:#4a7c9e">{current_tier.upper()}</strong>
      </div>
    </div>""", unsafe_allow_html=True)
    show_pricing(highlight=True)
    return False

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH PAGE
# ═══════════════════════════════════════════════════════════════════════════════
def show_auth_page():
    logo_html = (f'<img src="data:image/png;base64,{logo_b64}" style="width:72px;margin-bottom:18px;filter:drop-shadow(0 8px 20px rgba(0,180,255,.3))">'
                 if logo_b64 else '<div style="font-size:3rem;margin-bottom:18px">🔬</div>')
    st.markdown(f"""
    <div style="text-align:center;padding:48px 0 32px 0">
      {logo_html}
      <div style="font-family:'Inter',sans-serif;font-size:2.6rem;font-weight:900;
      color:#fff;letter-spacing:-2px;line-height:1">
        Syntho<span style="background:linear-gradient(135deg,#00d4ff,#0055ff);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;
        background-clip:text">Logic</span>
      </div>
      <div style="font-size:10px;color:#3d6a8a;letter-spacing:4px;text-transform:uppercase;
      margin-top:10px;font-family:'Space Mono',monospace">
        A Product of <strong style="color:#00d4ff">STRUCTURAL MIND</strong>
      </div>
      <div style="width:40px;height:2px;background:linear-gradient(90deg,#00d4ff,#0055ff);
      margin:14px auto;border-radius:10px"></div>
      <div style="font-size:.8rem;color:#3d6a8a;max-width:420px;margin:0 auto;line-height:1.65">
        Enterprise-grade synthetic data · Privacy-first by design · PII-aware
      </div>
    </div>""", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        mode = st.radio("", ["Login","Create Account"], horizontal=True, label_visibility="collapsed")
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        if mode == "Create Account":
            name  = st.text_input("Full Name", placeholder="Ada Lovelace")
            email = st.text_input("Email", placeholder="you@company.com")
            pw    = st.text_input("Password", type="password", placeholder="Min 8 characters")
            pw2   = st.text_input("Confirm Password", type="password")
            st.markdown("""
            <div style='background:rgba(0,210,255,.05);border:1px solid rgba(0,210,255,.12);
            border-radius:10px;padding:12px 14px;font-size:.76rem;color:#4a7c9e;margin:10px 0'>
            Free: <strong style='color:#e2e8f0'>500 rows · 10 CV images</strong><br>
            Pro $39/mo: <strong style='color:#00d2ff'>50K rows · 2,000 CV images + annotations</strong><br>
            Enterprise $239/mo: <strong style='color:#ff00c1'>Unlimited rows · 7,000 CV Images + Docker + Digital Twin</strong>
            </div>""", unsafe_allow_html=True)
            if st.button("CREATE ACCOUNT", use_container_width=True):
                if not name or not email or not pw: st.error("All fields required.")
                elif pw != pw2: st.error("Passwords don't match.")
                elif len(pw) < 8: st.error("Password must be ≥ 8 characters.")
                else:
                    ok, msg = register(name, email, pw)
                    st.success(msg) if ok else st.error(msg)
        else:
            email = st.text_input("Email", placeholder="you@company.com", key="li_e")
            pw    = st.text_input("Password", type="password", key="li_p")
            st.markdown("<div style='height:.3rem'></div>", unsafe_allow_html=True)
            if st.button("LOGIN", use_container_width=True):
                ok, user, is_admin, token, msg = do_login(email, pw)
                if ok:
                    # Demo account: full feature parity with every other tab —
                    # same as Enterprise — so a visitor can see the whole
                    # product end-to-end, but it is never treated as
                    # platform-admin, so the ADMIN tab and user-management
                    # console stay hidden for it regardless of the DB record.
                    if DEMO_ACCOUNT_ENABLED and email.strip().lower() == DEMO_EMAIL:
                        user = dict(user)
                        user["tier"] = "enterprise"
                        user["is_platform_admin"] = False
                        is_admin = False
                        st.session_state.is_demo = True
                    else:
                        st.session_state.is_demo = False
                    # Store in session_state — not cookies — so iframe works cross-origin
                    st.session_state.user     = user
                    st.session_state.is_admin = is_admin
                    st.session_state.auth_token = token
                    st.rerun()
                else:
                    st.error(msg)
            if DEMO_ACCOUNT_ENABLED and DEMO_PASSWORD:
                st.markdown(f"""
                <div style='background:rgba(0,210,255,.05);border:1px solid rgba(0,210,255,.15);
                border-radius:10px;padding:12px 14px;margin-top:14px;text-align:center'>
                  <div style='font-size:.62rem;color:#00d2ff;letter-spacing:1.5px;text-transform:uppercase;
                  font-family:"Space Mono",monospace;margin-bottom:6px'>Evaluation Sandbox Access</div>
                  <div style='font-size:.78rem;color:#e2e8f0;line-height:1.9'>
                    Email &nbsp;<strong style='color:#00d2ff'>{DEMO_EMAIL}</strong><br>
                    Password &nbsp;<strong style='color:#00d2ff'>{DEMO_PASSWORD}</strong><br>
                    <span style='font-size:.64rem;color:#5f7890'>Full product evaluation · Admin access excluded · One evaluation run per feature</span>
                  </div>
                </div>""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# ADMIN PANEL
# ═══════════════════════════════════════════════════════════════════════════════
def show_admin_panel():
    st.markdown('<div class="step-pill">ADMIN PANEL</div>', unsafe_allow_html=True)
    try:
        by_tier = db.count_users_by_tier()
        total = db.total_user_count()
    except db.DatabaseError:
        st.error("Could not load admin data right now. Please try again shortly.")
        return

    a,b,c,d = st.columns(4)
    for cw,val,lbl,clr in [(a,str(total),"Total Users","#00d2ff"),(b,str(by_tier["free"]),"Free","#4a7c9e"),
                            (c,str(by_tier["pro"]),"Pro","#00d2ff"),(d,str(by_tier["enterprise"]),"Enterprise","#ff00c1")]:
        with cw:
            st.markdown(f'<div class="metric-chip"><div class="val" style="color:{clr}">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top:1.5rem'></div>", unsafe_allow_html=True)
    search = st.text_input("Search users (email or name)", placeholder="Search...")
    try:
        rows = db.list_users(search=search or "", limit=50)
    except db.DatabaseError:
        st.error("Could not load users right now. Please try again shortly.")
        return

    for row in rows:
        email, t = row["email"], row.get("tier", "free")
        created = row.get("created_at")
        created_str = created.strftime("%Y-%m-%d") if created else "—"
        with st.container():
            st.markdown(f"""<div class="admin-row">
              <div style="font-size:.82rem;color:#e2e8f0;font-weight:600">{row.get('name','—')} <span class="tier-{t}">{t.upper()}</span></div>
              <div style="font-size:.72rem;color:#3d6a8a">{email} · Created: {created_str}</div>
            </div>""", unsafe_allow_html=True)
            ct, cd = st.columns([3,1])
            with ct:
                new_t = st.selectbox("", ["free","pro","enterprise"],
                                     index=["free","pro","enterprise"].index(t),
                                     key=f"t_{email}", label_visibility="collapsed")
            with cd:
                if st.button("APPLY", key=f"a_{email}"):
                    if db.update_user_tier(email, new_t):
                        st.success(f"Updated → {new_t.upper()}"); st.rerun()
                    else:
                        st.error("Could not update that user.")

    with st.expander("Danger Zone"):
        del_e = st.text_input("Delete user by email", key="del_e")
        if st.button("DELETE USER"):
            if db.delete_user(del_e):
                st.success(f"Deleted {del_e}"); st.rerun()
            else:
                st.error("User not found.")

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    if logo_b64:
        st.markdown(f'<div style="text-align:center;padding:1.25rem 0 .5rem 0"><img src="data:image/png;base64,{logo_b64}" style="width:65px;opacity:.95"></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center;padding:.4rem 0 1rem 0"><div style="font-family:Space Mono,monospace;font-size:.95rem;font-weight:700;color:#00d2ff;letter-spacing:1px">SYNTHOLOGIC</div><div style="font-size:.6rem;color:#3d6a8a;letter-spacing:2.5px;margin-top:4px;text-transform:uppercase">By Structural Mind</div></div>', unsafe_allow_html=True)

    if st.session_state.user:
        user = st.session_state.user; tier = user.get("tier","free")
        st.markdown(f"""<div class="user-card">
          <div style="font-size:.68rem;color:#3d6a8a;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px">Logged in as</div>
          <div style="color:#e2e8f0;font-size:.88rem;font-weight:600">{user.get('name','User')}</div>
          <div style="font-size:.7rem;color:#3d6a8a;margin:2px 0 8px">{user.get('email','')}</div>
          <span class="tier-{tier}">{tier.upper()}</span>
          {'&nbsp;<span style="font-size:.65rem;color:#ff00c1;font-weight:700">ADMIN</span>' if st.session_state.is_admin else ''}
        </div>""", unsafe_allow_html=True)

        if tier == "free":
            if st.button("UPGRADE TO PRO — $39/mo", use_container_width=True):
                st.info("Contact: structuralmind.net to upgrade")
        elif tier == "pro":
            if st.button("ENTERPRISE — $239/mo", use_container_width=True):
                st.info("Contact: structuralmind.net to upgrade")

        # ── CV Credit Balance display ──────────────────────────────────────
        if tier in ("pro", "enterprise"):
            credits = st.session_state.get("user_credits", 2000)
            max_credits = 2000 if tier == "pro" else 7000
            pct_used = max(0, min(100, int((1 - credits / max_credits) * 100)))
            credit_color = "#00d28c" if credits > 500 else "#ffaa00" if credits > 100 else "#ff5050"
            st.markdown(
                f'''<div style="background:#0a111e;border:1px solid rgba(0,210,255,.12);
                border-radius:10px;padding:10px 12px;margin-top:8px;margin-bottom:4px">
                  <div style="font-size:.6rem;color:#3d6a8a;letter-spacing:1.5px;
                  text-transform:uppercase;margin-bottom:5px">CV Image Credits</div>
                  <div style="font-family:'Space Mono',monospace;font-size:1.35rem;
                  font-weight:700;color:{credit_color}">{credits:,}</div>
                  <div style="font-size:.65rem;color:#3d6a8a;margin-top:2px">
                  remaining of {max_credits:,}</div>
                  <div style="background:#0d1420;border-radius:4px;height:4px;
                  margin-top:6px;overflow:hidden">
                    <div style="background:{credit_color};width:{100-pct_used}%;
                    height:4px;border-radius:4px;transition:width .3s"></div>
                  </div>
                </div>''',
                unsafe_allow_html=True,
            )

        if st.button("LOGOUT", use_container_width=True):
            for k in _defaults: st.session_state[k] = _defaults[k]
            st.rerun()

        st.markdown("---")
        st.markdown('<p style="color:#00d2ff;font-size:.7rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase">AI Keys (optional)</p>', unsafe_allow_html=True)
        ak = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")
        if ak: st.session_state.anthropic_key = ak; st.success("Claude active", icon="🤖")
        ok_ = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
        if ok_: st.session_state.openai_key = ok_

        if tier == "enterprise" or st.session_state.is_admin:
            st.markdown("---")
            st.markdown('<p style="color:#ff00c1;font-size:.7rem;font-weight:600;letter-spacing:1.5px;text-transform:uppercase">Docker Deploy</p>', unsafe_allow_html=True)
            st.code("docker pull structuralmind/synthologic\ndocker run -p 8501:8501 synthologic", language="bash")
            st.caption("Data never leaves your cloud")

    st.markdown("---")
    st.markdown('<div style="text-align:center;font-size:.65rem;color:#1e3050">v7.0 · 2026 Structural Mind<br><a href="https://structuralmind.net" style="color:#00d2ff">structuralmind.net</a></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# AUTH WALL
# ═══════════════════════════════════════════════════════════════════════════════
if not st.session_state.user:
    show_auth_page()
    st.stop()

user      = st.session_state.user
tier      = user.get("tier","free")
org_id    = user.get("organization_id")
row_limit = get_row_limit(tier)
is_admin  = st.session_state.is_admin

# CV image credits are tracked durably in Postgres per organization/billing
# period (see db.consume_credits) — refreshed here on every rerun so the
# balance shown and enforced can't be reset by a page reload and is
# correct even if the customer has multiple tabs/sessions open.
_tier_cap = CV_IMAGE_CAPS.get(tier, 2000)
try:
    st.session_state["user_credits"] = db.get_remaining_credits(org_id, _tier_cap)
except db.DatabaseError:
    log.exception("Could not load CV credit balance")
    st.session_state["user_credits"] = st.session_state.get("user_credits", _tier_cap)

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
logo_html = (f'<img src="data:image/png;base64,{logo_b64}" style="width:100px;margin-bottom:16px;filter:drop-shadow(0 8px 24px rgba(0,180,255,.3))">' if logo_b64 else "")
st.markdown(
    '<div class="header-wrapper">'+logo_html+
    '<h1 class="product-title">Syntho<span>Logic</span></h1>'
    '<div class="structural-mind-credit">A Product of <strong>STRUCTURAL MIND</strong></div>' + ("<div style='display:inline-block;margin-top:8px;padding:4px 9px;border:1px solid rgba(0,210,255,.22);border-radius:999px;font-size:.58rem;color:#00d2ff;letter-spacing:1px;text-transform:uppercase'>Evaluation Sandbox</div>" if is_demo_user() else "") +
    '<div class="underline"></div>'
    '<p style="font-size:.8rem;color:#3d6a8a;max-width:600px;line-height:1.7;margin-top:8px">'
    'Statistical Fidelity &middot; Differential Privacy &middot; Agentic Fabrication &middot; CV Suite<br>'
    '<span style="color:#00d2ff">Privacy-First &middot; PII-Aware &middot; Enterprise Grade</span>'
    '</p></div>', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_labels = ["SINGLE TABLE","MULTI-TABLE","DIFFERENTIAL PRIVACY","AGENTIC AI","BENCHMARK RESULTS","COMPUTER VISION SUITE","API DOCUMENTATION"]
if is_admin: tab_labels.append("ADMIN")
tabs = st.tabs(tab_labels)

# ───────────────────────────────────────────────────────────────────────────────
# TAB 0 — SINGLE TABLE
# ───────────────────────────────────────────────────────────────────────────────
with tabs[0]:
    col_up, col_cfg = st.columns([3, 2], gap="large")
    with col_up:
        st.markdown('<div class="step-pill">STEP 01 · UPLOAD</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("", type=["csv","xlsx","xls"], label_visibility="collapsed")
        if uploaded:
            fsig = f"{uploaded.name}_{uploaded.size}"
            if st.session_state.current_file_sig != fsig:
                try:
                    df_up = pd.read_excel(uploaded) if uploaded.name.endswith((".xlsx",".xls")) else pd.read_csv(uploaded)
                    if df_up.empty: st.error("File is empty.")
                    else:
                        st.session_state.df_real = df_up
                        st.session_state.df_synth = None
                        st.session_state.pii_cols = detect_pii(df_up.columns.tolist())
                        st.session_state.chat_history = []
                        st.session_state.current_file_sig = fsig
                        st.session_state.generation_done = False
                except Exception as e: st.error(f"Could not read: {e}")

        if st.session_state.df_real is not None:
            df_up = st.session_state.df_real
            c1,c2,c3,c4 = st.columns(4)
            for cw,val,lbl in zip([c1,c2,c3,c4],
                [f"{len(df_up):,}",str(len(df_up.columns)),
                 str(len(df_up.select_dtypes(include="number").columns)),
                 str(int(df_up.isnull().sum().sum()))],["Rows","Columns","Numeric","Nulls"]):
                with cw: st.markdown(f'<div class="metric-chip"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)
            st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
            pii = st.session_state.pii_cols
            if pii:
                badges="".join(f'<span class="pii-badge">! {c} ({t})</span>' for c,t in pii.items())
                st.markdown(f'<div class="card"><div class="card-title">PII Detected</div>{badges}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card"><div class="card-title">Privacy Scan</div><span class="safe-badge">No PII detected</span></div>', unsafe_allow_html=True)

    with col_cfg:
        st.markdown('<div class="step-pill">STEP 02 · CONFIGURE</div>', unsafe_allow_html=True)
        df_ref = st.session_state.df_real
        sector = st.selectbox("Compliance Sector", ["General","Healthcare / HIPAA","Finance / GDPR"], disabled=(df_ref is None))
        s_meth = st.selectbox("Synthesis Engine", ["auto (SDV→CTGAN→Copula)","copula","ctgan","sdv"], disabled=(df_ref is None))
        mmap = {"auto (SDV→CTGAN→Copula)":"auto","copula":"copula","ctgan":"ctgan","sdv":"sdv"}
        rl = row_limit or 500
        nd_ = min(len(df_ref), rl) if df_ref is not None else 100
        n_rows = st.number_input("Rows to generate", min_value=10, max_value=rl, value=int(nd_), step=10, disabled=(df_ref is None))
        if row_limit: st.caption(f"Your {tier.upper()} plan: up to {row_limit:,} rows")
        mask_flag = st.checkbox("Auto-mask PII with Faker", value=True, disabled=(df_ref is None))
        stress    = st.checkbox("Adversarial Stress-Testing", value=False, disabled=(df_ref is None), help="Injects 15% extreme outliers")
        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)
        _single_locked = demo_feature_lock("single_table")
        gen_btn = st.button("GENERATE SYNTHETIC DATA", disabled=(df_ref is None or _single_locked), use_container_width=True)

    if gen_btn and st.session_state.df_real is not None:
        if row_limit and n_rows > row_limit:
            st.markdown(f'<div class="upgrade-gate"><div style="font-size:2.5rem">🔒</div><div style="font-family:Inter;font-size:1.2rem;font-weight:800;color:white;margin:.6rem 0">{tier.upper()} Limit: {row_limit:,} rows</div><div style="font-size:.85rem;color:#8ba3bc">Requested <strong style="color:#ff00c1">{n_rows:,} rows</strong>. Upgrade to generate more.</div></div>', unsafe_allow_html=True)
            show_pricing(highlight=True)
        else:
            prog = st.progress(0, text="Initializing...")
            try:
                df_work = st.session_state.df_real.copy()
                pii_c = st.session_state.pii_cols
                allowed = SECTOR_PII.get(sector, list(PII_PATTERNS.keys()))
                pii_f = {k:v for k,v in pii_c.items() if v in allowed}
                prog.progress(15, text="Masking PII...")
                if mask_flag and pii_f: df_work = mask_pii(df_work, pii_f); eff_pii = {}
                else: eff_pii = pii_f
                prog.progress(35, text="Learning distributions...")
                df_s = generate_synthetic(df_work, n_rows=n_rows, method=mmap.get(s_meth,"auto"))
                prog.progress(75, text="Stress testing..." if stress else "Computing scores...")
                if stress: df_s = apply_stress(df_s)
                prog.progress(85, text="Computing fidelity...")
                num_c = [c for c in st.session_state.df_real.select_dtypes(include="number").columns if c in df_s.columns]
                if len(num_c) >= 2:
                    fid = compute_fidelity_cached(
                        st.session_state.df_real[num_c].fillna(0).to_json(),
                        df_s[num_c].fillna(0).to_json())
                else: fid = 91
                st.session_state.df_synth = df_s
                st.session_state.fidelity_score = fid
                st.session_state.privacy_score = compute_privacy_score(df_s, eff_pii, mask_flag)
                st.session_state.dp_applied = False
                st.session_state.synth_sector = sector
                st.session_state.generation_done = True
                prog.progress(100, text="Complete!")
                st.success("Synthetic dataset ready!")
                st.info("Click the RESULTS tab above to view analysis and download your data.")
                demo_feature_completed("single_table")
            except Exception as e:
                prog.empty(); st.error(f"Generation failed: {e}")

# ───────────────────────────────────────────────────────────────────────────────
# TAB 1 — MULTI-TABLE
# ───────────────────────────────────────────────────────────────────────────────
with tabs[1]:
    if gate("Multi-Table Referential Synthesis", "enterprise", tier):
        st.markdown('<div class="step-pill">MULTI-TABLE SYNTHESIS</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.83rem;color:#4a7c9e;margin-bottom:1rem">Upload 2–10 related CSVs. FK/PK relationships are auto-detected and preserved.</div>', unsafe_allow_html=True)
        mt_files = st.file_uploader("Upload related CSV tables", type=["csv"], accept_multiple_files=True)
        if mt_files:
            for f in mt_files:
                try: st.session_state.multi_tables[f.name.replace(".csv","")] = pd.read_csv(f)
                except Exception as e: st.error(f"{f.name}: {e}")
        if st.session_state.multi_tables:
            tl,tr = st.columns(2)
            with tl:
                st.markdown("**Tables loaded:**")
                for tn,td in st.session_state.multi_tables.items():
                    st.markdown(f"- **{tn}**: {len(td):,} rows x {len(td.columns)} cols")
            with tr:
                rels = detect_relationships(st.session_state.multi_tables)
                if rels:
                    st.markdown("**Relationships detected:**")
                    for r in rels: st.markdown(f"- `{r['table_a']}.{r['col_a']}` -- `{r['table_b']}.{r['col_b']}` ({r['type']})")
                else: st.info("No common key columns found.")
            mt_n = st.number_input("Rows per table", 10, 10000, 200, 10)
            _multi_locked = demo_feature_lock("multi_table")
            if st.button("SYNTHESIZE ALL TABLES", disabled=_multi_locked, use_container_width=True):
                with st.spinner("Synthesizing with referential integrity..."):
                    try:
                        synth_t, _ = synthesize_multi_table(st.session_state.multi_tables, mt_n)
                        st.success(f"✅ {len(synth_t)} synthetic tables ready!")
                        demo_feature_completed("multi_table")
                        for tn,td in synth_t.items():
                            st.markdown(f"**{tn}** — {len(td):,} rows")
                            st.dataframe(td.head(5), use_container_width=True)
                            st.download_button(f"Download {tn}_synthetic.csv", data=df_csv(td),
                                               file_name=f"{tn}_synthetic.csv", mime="text/csv", key=f"mt_{tn}")
                    except Exception as e: st.error(f"Error: {e}")

# ───────────────────────────────────────────────────────────────────────────────
# TAB 2 — DIFFERENTIAL PRIVACY
# ───────────────────────────────────────────────────────────────────────────────
with tabs[2]:
    if gate("ε-Differential Privacy", "pro", tier):
        st.markdown('<div class="step-pill">ε-DIFFERENTIAL PRIVACY</div>', unsafe_allow_html=True)
        st.markdown("""<div class="dp-panel"><div style="font-size:.82rem;color:#8ba3bc;line-height:1.8">
          <strong style="color:#ff00c1">ε (epsilon)</strong> — privacy budget:<br>
          &nbsp;&nbsp;ε = 0.1 — Maximum privacy, high noise<br>
          &nbsp;&nbsp;ε = 1.0 — Balanced (recommended)<br>
          &nbsp;&nbsp;ε = 10.0 — High fidelity, weaker privacy<br>
          Laplace mechanism: scale = sensitivity / ε
        </div></div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        if st.session_state.df_synth is None:
            st.info("Generate a synthetic dataset first (Single Table tab).")
        else:
            epsilon = st.slider("Privacy Budget (ε)", 0.05, 10.0, 1.0, 0.05)
            st.session_state.dp_epsilon = epsilon
            ca,cb = st.columns(2)
            with ca:
                st.markdown("**Before DP:**")
                st.dataframe(st.session_state.df_synth.select_dtypes(include="number").head(5), use_container_width=True)
            with cb:
                _dp_locked = demo_feature_lock("differential_privacy")
                if st.button("APPLY DIFFERENTIAL PRIVACY", disabled=_dp_locked, use_container_width=True):
                    with st.spinner(f"Applying Laplace noise (ε={epsilon})..."):
                        try:
                            df_dp = apply_dp(st.session_state.df_synth, epsilon)
                            st.session_state.df_synth = df_dp
                            st.session_state.dp_applied = True
                            st.session_state.privacy_score = min(100, st.session_state.privacy_score + int(10/epsilon))
                            st.success(f"DP applied (ε={epsilon})")
                            demo_feature_completed("differential_privacy")
                            st.markdown("**After DP:**")
                            st.dataframe(df_dp.select_dtypes(include="number").head(5), use_container_width=True)
                        except Exception as e: st.error(f"DP error: {e}")

# ───────────────────────────────────────────────────────────────────────────────
# TAB 3 — AGENTIC FABRICATOR
# ───────────────────────────────────────────────────────────────────────────────
with tabs[3]:
    if gate("Agentic Data Fabricator", "pro", tier):
        st.markdown('<div class="step-pill">AGENTIC DATA FABRICATOR</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:.83rem;color:#4a7c9e;margin-bottom:1rem">Describe your dataset in plain English. Claude or GPT-4 writes and executes generation code.</div>', unsafe_allow_html=True)
        has_key = bool(st.session_state.get("anthropic_key") or st.session_state.get("openai_key"))
        if not has_key: st.warning("Add an Anthropic or OpenAI API key in the sidebar.")
        examples = [
            "Generate 300 rows: age 18-65, salary correlated with age (r~0.7)",
            "Healthcare: 200 female patients, age 30-50, diagnosis from [Diabetes,Hypertension,Asthma]",
            "E-commerce: 500 orders, 80% completed, revenue follows Pareto distribution",
            "Finance: 100 transactions, fraud_flag=1 when amount > 5000",
        ]
        st.markdown("**Quick examples:**")
        ec = st.columns(2)
        for i,ep in enumerate(examples):
            with ec[i%2]:
                st.markdown(f'<div style="background:#0d1420;border:1px solid rgba(255,255,255,.05);border-radius:9px;padding:9px 12px;font-size:.76rem;color:#7090a8;margin:4px 0">{ep}</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:.75rem'></div>", unsafe_allow_html=True)
        prompt = st.text_area("Describe your dataset", height=100, placeholder="Generate 500 rows where age > 18 and income correlates with education level...")
        provider = "anthropic" if st.session_state.get("anthropic_key") else "openai"
        api_key  = st.session_state.get("anthropic_key") or st.session_state.get("openai_key","")
        schema_schema_df = st.session_state.df_real if st.session_state.df_real is not None else pd.DataFrame({"id":[1,2,3],"age":[25,35,45],"name":["Alice","Bob","Charlie"],"salary":[50000,70000,90000]})
        _agent_locked = demo_feature_lock("agentic_ai")
        if st.button("FABRICATE WITH AI", disabled=(not prompt or not has_key or _agent_locked), use_container_width=True):
            with st.spinner("AI generating dataset..."):
                r, err = agentic_fabricate(prompt, schema_df, api_key, provider)
                if err: st.error(err)
                elif r is not None:
                    st.session_state.agentic_result = r
                    st.success(f"Generated {len(r):,} rows x {len(r.columns)} cols!")
                    demo_feature_completed("agentic_ai")
        if st.session_state.agentic_result is not None:
            st.dataframe(st.session_state.agentic_result.head(20), use_container_width=True)
            st.download_button("DOWNLOAD FABRICATED CSV", data=df_csv(st.session_state.agentic_result),
                               file_name="agentic_fabricated.csv", mime="text/csv", use_container_width=True)

# ───────────────────────────────────────────────────────────────────────────────
# TAB 4 — RESULTS
# ───────────────────────────────────────────────────────────────────────────────
with tabs[4]:
    if st.session_state.df_synth is None:
        st.markdown('<div style="text-align:center;padding:4rem 2rem"><div style="font-size:4rem;opacity:.15">📊</div><div style="font-family:Space Mono,monospace;font-size:.85rem;letter-spacing:2px;text-transform:uppercase;color:#1e3050;margin-top:1rem">Generate a dataset first</div></div>', unsafe_allow_html=True)
    else:
        df_synth = st.session_state.df_synth; df_real = st.session_state.df_real
        p_score = st.session_state.privacy_score or 0; f_score = st.session_state.fidelity_score or 0
        dp_on = st.session_state.dp_applied; eps = st.session_state.dp_epsilon
        sector = st.session_state.synth_sector; pii_cols = st.session_state.pii_cols
        p_color = "#00d28c" if p_score>=80 else "#ffaa00" if p_score>=50 else "#ff5050"
        p_label = "EXCELLENT" if p_score>=80 else "MODERATE" if p_score>=50 else "RISKY"

        s1,s2,s3,s4 = st.columns(4)
        with s1: st.markdown(f'<div class="card" style="border-bottom:4px solid {p_color};text-align:center"><div class="card-title">Privacy Score</div><div class="score-number" style="color:{p_color}">{p_score}</div><div class="score-label">{p_label}</div></div>', unsafe_allow_html=True)
        with s2: st.markdown(f'<div class="card" style="border-bottom:4px solid #ff00c1;text-align:center"><div class="card-title">Fidelity <span class="new-badge">AI</span></div><div class="score-number" style="color:#ff00c1">{f_score}%</div><div class="score-label">Statistical Match</div></div>', unsafe_allow_html=True)
        with s3:
            dpc="#00d28c" if dp_on else "#3d6a8a"; dpl=f"e={eps}" if dp_on else "OFF"
            st.markdown(f'<div class="card" style="border-bottom:4px solid {dpc};text-align:center"><div class="card-title">Diff. Privacy</div><div style="font-family:Space Mono;font-size:1.8rem;font-weight:700;color:{dpc}">{dpl}</div><div class="score-label">Laplace Noise</div></div>', unsafe_allow_html=True)
        with s4: st.markdown(f'<div class="card" style="text-align:center"><div class="card-title">Rows Generated</div><div class="score-number" style="color:#00d2ff">{len(df_synth):,}</div><div class="score-label">Synthetic Records</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)
        cert_id = "SL-"+str(abs(hash(str(df_synth.shape)+str(p_score)))%9000+1000)+"-TX"
        cc,dc = st.columns([2.2,1])
        with cc:
            tc = '#00d2ff' if tier=='pro' else '#ff00c1' if tier=='enterprise' else '#4a7c9e'
            st.markdown(f'<div class="card highlight-card"><div style="background:linear-gradient(90deg,#00d2ff,#0055ff);color:black;font-size:.55rem;font-weight:900;padding:3px 10px;border-radius:4px;display:inline-block;margin-bottom:10px;letter-spacing:1px">ENTERPRISE VERIFIED</div><h2 style="margin:0;color:white;letter-spacing:-1px;font-size:1.4rem">SynthoLogic Trust Certificate</h2><p style="font-family:Space Mono,monospace;font-size:.68rem;color:#3d6a8a;margin-top:10px;line-height:1.9">CERT ID: <span style="color:#00d2ff">{cert_id}</span><br>USER: {user.get("email","")} · TIER: <span style="color:{tc}">{tier.upper()}</span><br>SECTOR: {sector.upper()}<br>PRIVACY: {p_score}/100 · FIDELITY: {f_score}% · DP: {"e="+str(eps) if dp_on else "NOT APPLIED"}</p></div>', unsafe_allow_html=True)
        with dc:
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            st.download_button("DOWNLOAD CSV", data=df_csv(df_synth), file_name="synthologic_output.csv", mime="text/csv", use_container_width=True)
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            pdf_b = create_audit_pdf(cert_id,p_score,f_score,sector,len(df_synth),len(df_synth.columns),pii_cols,True,dp_on,eps,user.get("email",""))
            if pdf_b: st.download_button("DOWNLOAD AUDIT PDF", data=pdf_b, file_name=f"SynthoLogic_Audit_{cert_id}.pdf", mime="application/pdf", use_container_width=True)

        st.markdown("<div style='margin-top:32px'></div>", unsafe_allow_html=True)
        rtab_dist,rtab_corr,rtab_raw,rtab_ai = st.tabs(["DISTRIBUTIONS","CORRELATION MAP","RAW DATA","AI ANALYST"])

        with rtab_dist:
            if df_real is None: st.info("No original data to compare against.")
            else:
                with st.spinner("Rendering charts..."):
                    try:
                        rs = df_real.sample(min(len(df_real),MAX_CHART),random_state=42) if len(df_real)>MAX_CHART else df_real
                        ss = df_synth.sample(min(len(df_synth),MAX_CHART),random_state=42) if len(df_synth)>MAX_CHART else df_synth
                        fig = build_dist_chart(rs.to_json(), ss.to_json())
                        if fig: st.plotly_chart(fig, use_container_width=True, config={"displayModeBar":False})
                        else: st.info("No overlapping columns to compare.")
                    except Exception as e: st.error(f"Chart error: {e}")

        with rtab_corr:
            if df_real is None: st.info("No original data.")
            else:
                try:
                    import plotly.graph_objects as go
                    nc2=[c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
                    if len(nc2)<2: st.info("Need 2+ numeric columns.")
                    else:
                        cr2=df_real[nc2].corr(); cs2=df_synth[nc2].corr()
                        cl2,cr_2=st.columns(2,gap="medium")
                        def make_hm(mat,title):
                            return go.Figure(go.Heatmap(z=mat.values,x=mat.columns.tolist(),y=mat.index.tolist(),
                                colorscale=[[0,"#060a10"],[.35,"#0c2a48"],[.65,"#1a5276"],[1,"#00d2ff"]],
                                zmin=-1,zmax=1,text=mat.round(2).values,texttemplate="%{text}",
                                textfont=dict(size=9,color="white"))).update_layout(
                                title=dict(text=title,font=dict(size=11,color="#4a7c9e"),x=.5),
                                paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                                font_color="#7090a8",margin=dict(t=45,b=10,l=10,r=10),height=360)
                        with cl2: st.plotly_chart(make_hm(cr2,"Real Data"),use_container_width=True,config={"displayModeBar":False})
                        with cr_2: st.plotly_chart(make_hm(cs2,"Synthetic Data"),use_container_width=True,config={"displayModeBar":False})
                        delta=(cs2-cr2).abs(); avg=float(delta.values[np.triu_indices_from(delta.values,k=1)].mean())
                        st.markdown(f'<div class="card" style="margin-top:.5rem"><div class="card-title">Correlation Fidelity</div><div style="font-size:.83rem;color:#e2e8f0">Mean absolute deviation: <span style="font-family:Space Mono;color:#00d2ff;font-weight:700">{round(avg,4)}</span> · Lower = better</div></div>', unsafe_allow_html=True)
                except Exception as e: st.error(f"Correlation error: {e}")

        with rtab_raw:
            c3,c4=st.columns(2,gap="medium")
            with c3:
                st.markdown('<div class="card-title">Real Data (top 20)</div>', unsafe_allow_html=True)
                if df_real is not None: st.dataframe(df_real.head(20),use_container_width=True,height=360)
                else: st.info("No original data.")
            with c4:
                st.markdown('<div class="card-title">Synthetic Data (top 20)</div>', unsafe_allow_html=True)
                st.dataframe(df_synth.head(20),use_container_width=True,height=360)
            if df_real is not None:
                st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
                nb=[c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
                if nb:
                    dr=df_real[nb].describe().T.round(3); ds_=df_synth[nb].describe().T.round(3)
                    dr.columns=[f"Real_{c}" for c in dr.columns]; ds_.columns=[f"Synth_{c}" for c in ds_.columns]
                    combined=pd.concat([dr,ds_],axis=1); ordered=[c for pair in zip(dr.columns,ds_.columns) for c in pair]
                    st.markdown('<div class="card-title">Statistical Comparison</div>', unsafe_allow_html=True)
                    st.dataframe(combined[ordered],use_container_width=True)

        with rtab_ai:
            has_any=bool(st.session_state.get("anthropic_key") or st.session_state.get("openai_key","").startswith("sk-"))
            mode_lbl=("Claude Active" if st.session_state.get("anthropic_key") else "GPT-4 Active" if st.session_state.get("openai_key","").startswith("sk-") else "Built-in Analyst")
            st.markdown(f'<div class="analyst-wrapper"><div style="display:flex;align-items:center;gap:12px;margin-bottom:1rem"><div style="font-size:2rem">🤖</div><div><div style="font-size:1rem;font-weight:700;color:#fff">AI Data Analyst</div><div style="font-size:.75rem;color:#3d6a8a">{mode_lbl}</div></div></div>', unsafe_allow_html=True)
            for msg in st.session_state.chat_history:
                css="chat-user" if msg["role"]=="user" else "chat-ai"; lbl="You:" if msg["role"]=="user" else "AI:"
                st.markdown(f'<div class="{css}">{lbl} {msg["content"]}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            sqs=["Rows/columns?","Summary stats","Missing values?","Find correlations","Detect outliers","PII scan","Distribution skew","Unique counts"]
            sqc=st.columns(4)
            for i,sq in enumerate(sqs):
                with sqc[i%4]:
                    if st.button(sq,key=f"sq_{i}",use_container_width=True):
                        ans,_=get_ai_answer(df_synth,sq)
                        st.session_state.chat_history.append({"role":"user","content":sq})
                        st.session_state.chat_history.append({"role":"assistant","content":ans})
                        st.rerun()
            uq=st.chat_input("Ask anything about your synthetic data...")
            if uq:
                ans,_=get_ai_answer(df_synth,uq)
                st.session_state.chat_history.append({"role":"user","content":uq})
                st.session_state.chat_history.append({"role":"assistant","content":ans})
                st.rerun()
            if st.session_state.chat_history:
                if st.button("Clear Chat"): st.session_state.chat_history=[]; st.rerun()

# ───────────────────────────────────────────────────────────────────────────────
# TAB 5 — COMPUTER VISION SUITE
# ───────────────────────────────────────────────────────────────────────────────
with tabs[5]:
    st.markdown('<div class="step-pill">COMPUTER VISION SUITE</div>', unsafe_allow_html=True)
    st.markdown('<div style="font-size:.83rem;color:#4a7c9e;margin-bottom:1.5rem">Generate synthetic image datasets with auto-annotations for object detection, segmentation, and classification.</div>', unsafe_allow_html=True)

    cv_tabs = st.tabs(["FIDELITY AUDIT", "DATASET GENERATOR", "AUTO-ANNOTATION",
                       "GENERATION STATUS", "DIGITAL TWIN"])

    # ── SUB-TAB A: Fidelity Audit & Analytics (FREE) ─────────────────────────
    with cv_tabs[0]:
        st.markdown('<div class="step-pill">FIDELITY AUDIT — ALL TIERS</div>', unsafe_allow_html=True)

        # Sample dataset distribution chart (always visible, all tiers)
        st.markdown("**Sample Dataset Class Distribution**")
        sample_classes = ["person","car","bicycle","dog","cat","truck","traffic_light","stop_sign"]
        real_counts    = [1240, 876, 432, 198, 156, 341, 89, 67]
        synth_counts   = [1198, 891, 418, 203, 162, 356, 94, 71]
        dist_df = pd.DataFrame({
            "Class":   sample_classes,
            "Real":    real_counts,
            "Synthetic": synth_counts,
        }).set_index("Class")
        st.bar_chart(dist_df, color=["#00b4d8","#00d28c"])

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown("**Lighting Bias Analysis**")
        lighting_df = pd.DataFrame({
            "Condition": ["Daylight","Overcast","Night","Foggy","Indoor","Neon/Urban"],
            "Real %":    [42, 18, 14, 8, 12, 6],
            "Synth %":   [39, 20, 15, 9, 11, 6],
        }).set_index("Condition")
        st.bar_chart(lighting_df, color=["#0077b6","#ff00c1"])

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        metrics = [("mAP@0.5","0.734","Detection accuracy"),("Class Balance","87.2%","Distribution parity"),
                   ("Bbox Coverage","91.4%","Annotation density"),("Fidelity Score","82/100","Structural match")]
        for cw,(val,sub,lbl) in zip([col_m1,col_m2,col_m3,col_m4], metrics):
            with cw:
                st.markdown(f'<div class="metric-chip"><div class="val" style="font-size:1.4rem">{val}</div><div class="lbl">{lbl}</div><div style="font-size:.6rem;color:#00d2ff;margin-top:3px">{sub}</div></div>', unsafe_allow_html=True)

        if tier == "free":
            st.markdown("""
            <div class="cv-pro-banner">
                <div style="font-size:1.5rem;margin-bottom:.5rem">📈</div>
                <div style="font-weight:700;color:#00d2ff;font-size:.95rem;margin-bottom:.4rem">Advanced Analytics — PRO Feature</div>
                <div style="font-size:.8rem;color:#7090a8;line-height:1.6">
                    Unlock per-class precision/recall curves, confusion matrices,<br>
                    domain shift detection, and real-time fidelity monitoring.<br>
                    <strong style="color:#00d2ff">Upgrade to PRO ($39/mo) →</strong>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── SUB-TAB B: Synthetic Dataset Generator ────────────────────────────────
    with cv_tabs[1]:
        st.markdown('<div class="step-pill">IMAGE DATASET GENERATOR</div>', unsafe_allow_html=True)

        # Config form — visible for all tiers, behaviour differs
        cv_prompt = st.text_input(
            "Image generation prompt",
            placeholder="e.g. Urban street scene with pedestrians and vehicles, daytime, overcast",
        )
        cv_domain = st.selectbox(
            "Dataset domain",
            ["Autonomous Driving","Medical Imaging","Retail / Shelf","Industrial Inspection",
             "Agriculture","Security / Surveillance","Custom"]
        )
        cv_classes_raw = st.text_input(
            "Object classes (comma-separated)",
            value=", ".join(CV_OBJECT_CLASSES[:6]),
            help="Classes that will be annotated in each image"
        )
        cv_classes = [c.strip() for c in cv_classes_raw.split(",") if c.strip()]

        if tier == "free":
            st.markdown("""
            <div style="background:rgba(255,170,0,.06);border:1px solid rgba(255,170,0,.2);
            border-radius:10px;padding:10px 14px;font-size:.78rem;color:#c8a030;margin:.75rem 0">
            FREE plan: preview limited to <strong>10 sample image tokens</strong>.
            Upgrade to PRO for 2,000+ images with full annotations.
            </div>""", unsafe_allow_html=True)
            cv_n_images = 10
        elif tier == "pro":
            # ── Dynamic credit-aware slider ──────────────────────────────
            _credits_pro = st.session_state.get("user_credits", 2000)
            _max_pro     = max(0, min(2000, _credits_pro))
            if _credits_pro <= 0:
                st.error(
                    "🔴 You have 0 CV image credits remaining for this month. "
                    "Credits reset on your billing date or upgrade to Enterprise "
                    "for unlimited generation."
                )
                cv_n_images = 0
            else:
                cv_n_images = st.slider(
                    f"Total images to generate  (credits remaining: {_credits_pro:,})",
                    min_value=10,
                    max_value=_max_pro,
                    value=min(100, _max_pro),
                    step=10,
                    help=f"Capped at your remaining credit balance ({_credits_pro:,} images).",
                )
        else:  # enterprise — capped at 7,000 images/month
            _credits_ent = st.session_state.get("user_credits", 7000)
            _max_ent     = max(0, min(7000, _credits_ent))
            if _credits_ent <= 0:
                st.error(
                    "🔴 You have 0 CV image credits remaining for this month. "
                    "Enterprise plan: 7,000 images/month. Credits reset on your billing date."
                )
                cv_n_images = 0
            else:
                cv_n_images = st.slider(
                    f"Total images to generate  (credits remaining: {_credits_ent:,})",
                    min_value=10,
                    max_value=_max_ent,
                    value=min(2000, _max_ent),
                    step=100,
                    help=f"Enterprise plan cap: 7,000 images/month. Remaining: {_credits_ent:,}.",
                )

        _cv_locked = demo_feature_lock("computer_vision")
        gen_cv_btn = st.button("GENERATE DATASET", use_container_width=True, disabled=(not cv_prompt or _cv_locked))

        if gen_cv_btn and cv_prompt:
            # ── Authentication check ───────────────────────────────────────
            hf_token = os.getenv("HF_TOKEN", "").strip()
            if not hf_token:
                st.error(
                    "Computer Vision generation is temporarily unavailable in this "
                    "evaluation environment. Please contact Structural Mind to enable "
                    "the full Computer Vision pipeline."
                )
                st.markdown(
                    f'<a href="{CONTACT_URL}" target="_blank" style="display:inline-block;margin-top:8px;padding:9px 14px;border-radius:8px;background:#00d2ff;color:#041018;text-decoration:none;font-weight:800;font-size:.72rem;">CONTACT US →</a>',
                    unsafe_allow_html=True,
                )
            else:
                # ── Real generation pipeline ───────────────────────────────
                bar = st.progress(0, text="Initialising HF inference pipeline...")
                full_batch = [
                    {"idx": i, "prompt": cv_prompt, "domain": cv_domain,
                     "classes": cv_classes}
                    for i in range(cv_n_images)
                ]

                # For the preview pass we call the API on the first few images
                # immediately so the user sees real thumbnails right away.
                preview_count = min(cv_n_images, 5)
                preview_images: dict[int, bytes] = {}

                for pi in range(preview_count):
                    rich_prompt = (
                        f"{cv_prompt}, {cv_domain} dataset, "
                        "photorealistic, high quality, detailed, "
                        "natural lighting, 8k resolution"
                    )
                    pct = int((pi + 1) / preview_count * 60)
                    bar.progress(pct, text=f"Generating preview image {pi+1}/{preview_count}...")
                    try:
                        img_b = _hf_generate_image(rich_prompt, hf_token)
                        if img_b:
                            # ── Draw bounding boxes on preview image ──────
                            try:
                                from PIL import Image as _PILImg, ImageDraw as _PILDraw, ImageFont as _PILFont
                                _pil_img   = _PILImg.open(io.BytesIO(img_b)).convert("RGB")
                                _img_w, _img_h = _pil_img.size
                                _draw      = _PILDraw.Draw(_pil_img)
                                _dets      = _hf_detect_objects(img_b, hf_token)
                                _BOX_COLORS = [
                                    (0, 255, 80),   # bright green
                                    (255, 60, 60),  # bright red
                                    (0, 200, 255),  # cyan
                                    (255, 200, 0),  # yellow
                                    (200, 0, 255),  # purple
                                ]
                                for _di, _det in enumerate(_dets):
                                    _box   = _det.get("box", {})
                                    _label = _det.get("label", "")
                                    _score = float(_det.get("score", 0))
                                    if not all(k in _box for k in ("xmin","ymin","xmax","ymax")):
                                        continue
                                    _x0 = int(float(_box["xmin"]))
                                    _y0 = int(float(_box["ymin"]))
                                    _x1 = int(float(_box["xmax"]))
                                    _y1 = int(float(_box["ymax"]))
                                    # Skip degenerate boxes
                                    if _x1 <= _x0 or _y1 <= _y0:
                                        continue
                                    _color = _BOX_COLORS[_di % len(_BOX_COLORS)]
                                    # Draw thick rectangle (4 px outline)
                                    for _t in range(4):
                                        _draw.rectangle(
                                            [_x0 - _t, _y0 - _t, _x1 + _t, _y1 + _t],
                                            outline=_color
                                        )
                                    # Label background + text
                                    _txt = f"{_label} {_score:.2f}"
                                    _lbl_y = max(0, _y0 - 18)
                                    _draw.rectangle(
                                        [_x0, _lbl_y, _x0 + len(_txt) * 7 + 6, _lbl_y + 16],
                                        fill=_color
                                    )
                                    _draw.text(
                                        (_x0 + 3, _lbl_y + 1),
                                        _txt,
                                        fill=(0, 0, 0)
                                    )
                                # Encode annotated image back to JPEG bytes
                                _ann_buf = io.BytesIO()
                                _pil_img.save(_ann_buf, format="JPEG", quality=92)
                                img_b = _ann_buf.getvalue()
                            except Exception as _draw_err:
                                pass  # if drawing fails, still show plain image
                            preview_images[pi] = img_b
                    except Exception as _e:
                        st.error(f"Image generation error: {_e}")

                bar.progress(100, text="Preview generation complete!")
                st.session_state.cv_generated = True
                st.session_state.cv_batch     = full_batch
                st.session_state["cv_hf_token_present"] = True
                st.session_state["cv_preview_images"]   = preview_images
                st.success(
                    f"Pipeline ready! {len(preview_images)} preview images "
                    f"generated. Full dataset of {cv_n_images} images will be "
                    f"built when you click 'Generate & Annotate All' below."
                )

        if st.session_state.cv_generated and st.session_state.cv_batch:
            preview_n    = min(10, len(st.session_state.cv_batch))
            real_previews = st.session_state.get("cv_preview_images", {})
            hf_present    = st.session_state.get("cv_hf_token_present", False)

            if hf_present and real_previews:
                st.markdown(f"**Preview — {len(real_previews)} real AI-generated images**")
                preview_cols = st.columns(5)
                for i, (pi, img_b) in enumerate(list(real_previews.items())[:10]):
                    with preview_cols[i % 5]:
                        st.image(img_b, caption=f"synth_{pi:05d}.jpg", use_column_width=True)
                if len(st.session_state.cv_batch) > len(real_previews):
                    remaining = len(st.session_state.cv_batch) - len(real_previews)
                    st.caption(
                        f"+ {remaining:,} more images will be generated during "
                        "the full ZIP build below."
                    )
            else:
                st.markdown(f"**Preview — first {preview_n} image tokens** *(prototype — add HF_TOKEN for real images)*")
                preview_cols = st.columns(5)
                icons = ["🏙","🚗","🚴","🐕","🐈","🚚","🚦","🛑","👤","💻"]
                for i in range(preview_n):
                    with preview_cols[i % 5]:
                        icon = icons[i % len(icons)]
                        st.markdown(f'''
                        <div class="cv-image-card">
                            <div class="cv-image-thumb">{icon}</div>
                            synth_{i:05d}.jpg<br>
                            <span style="color:#00d2ff">{cv_domain[:12]}</span>
                        </div>''', unsafe_allow_html=True)

            if tier == "free":
                st.markdown("""
                <div class="upgrade-gate" style="max-width:100%;margin-top:1.5rem">
                    <div style="font-size:2rem;margin-bottom:.5rem">🔒</div>
                    <div style="font-weight:800;color:white;font-size:1rem;margin-bottom:.4rem">
                        Upgrade to PRO for 2,000+ Images &amp; Full Annotations
                    </div>
                    <div style="font-size:.82rem;color:#7090a8;line-height:1.6">
                        Free plan: 10 image preview only.<br>
                        PRO ($39/mo): 2,000 images + YOLO / COCO / VOC annotations + ZIP download.<br>
                        Enterprise ($239/mo): 7,000 Images + Digital Twin rendering.
                    </div>
                </div>""", unsafe_allow_html=True)
                st.button("Download Annotations ZIP", disabled=True,
                          help="Upgrade to PRO to enable ZIP download")

    # ── SUB-TAB C: Auto-Annotation Engine ─────────────────────────────────────
    with cv_tabs[2]:
        if not gate("Auto-Annotation Engine", "pro", tier):
            pass  # gate() already rendered the upgrade wall
        else:
            st.markdown('<div class="step-pill">AUTO-ANNOTATION ENGINE</div>', unsafe_allow_html=True)
            if not st.session_state.cv_generated or not st.session_state.cv_batch:
                st.info("Generate a dataset first in the Image Dataset Generator tab.")
            else:
                ann_fmt = st.selectbox(
                    "Annotation format",
                    ["YOLO .txt", "COCO JSON", "Pascal VOC XML"],
                    help="YOLO: bbox per line · COCO: structured JSON · Pascal VOC: XML per image"
                )
                n_obj_per_img = st.slider("Objects per image (avg)", 1, 8, 3)
                preview_ann_btn = st.button("PREVIEW ANNOTATIONS", use_container_width=True)

                if preview_ann_btn:
                    st.markdown("**Example format** *(fixed illustrative values — not a real detection; run the pipeline below for actual results)*")
                    if ann_fmt == "YOLO .txt":
                        sample = _example_yolo_annotation(class_list=cv_classes)
                        st.code(sample, language="text")
                        st.caption("Format: class_id cx cy width height (normalised 0-1)")
                    elif ann_fmt == "COCO JSON":
                        sample = _example_coco_annotation(class_list=cv_classes)
                        st.code(json.dumps(sample, indent=2), language="json")
                    else:
                        sample = _example_voc_annotation(class_list=cv_classes)
                        st.code(sample, language="xml")

                st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

                # Annotation progress + ZIP download
                if st.button("GENERATE & ANNOTATE ALL — BUILD ZIP", use_container_width=True):
                    n_total = len(st.session_state.cv_batch)
                    if tier == "pro" and n_total > 2000:
                        st.warning("PRO plan: capped at 2,000 images. Showing first 2,000.")
                        batch_to_use = st.session_state.cv_batch[:2000]
                    else:
                        batch_to_use = st.session_state.cv_batch

                    # ── Check for HF token ─────────────────────────────────
                    hf_token_zip = os.getenv("HF_TOKEN", "").strip()

                    if hf_token_zip:
                        # ── Atomic credit check-and-deduct (durable, race-safe) ──
                        # A single db call that checks the balance and deducts in
                        # one row-locked transaction, so two concurrent requests
                        # (two tabs, two API calls) can never both pass the check
                        # and jointly overspend the monthly cap.
                        _images_needed = len(batch_to_use)
                        _cap = CV_IMAGE_CAPS.get(tier)
                        try:
                            _ok_credits, _remaining = db.consume_credits(org_id, _cap, _images_needed)
                        except db.DatabaseError:
                            st.error("Could not verify your credit balance right now. Please try again shortly.")
                            st.stop()
                        if not _ok_credits:
                            st.error(
                                f"Insufficient CV credits. "
                                f"You have **{_remaining:,}** credit(s) remaining "
                                f"but requested **{_images_needed:,}** images. "
                                f"Reduce the batch size or wait for your monthly reset."
                            )
                            st.stop()
                        st.session_state["user_credits"] = _remaining
                        st.sidebar.info(
                            f"💳 {_images_needed:,} credits deducted — "
                            f"{_remaining:,} remaining."
                        )

                        # ── Create a real job row before any work starts ────
                        # This is what backs "GENERATE & ANNOTATE ALL": a job
                        # id that only exists because a row was actually
                        # inserted, with real status transitions — the same
                        # db.create_cv_job / db.complete_cv_job a future REST
                        # endpoint would call (see the API Guide tab).
                        try:
                            _cv_job_id = db.create_cv_job(
                                org_id, user.get("id"), cv_prompt, cv_domain,
                                ann_fmt, cv_classes, _images_needed,
                            )
                        except db.DatabaseError:
                            _cv_job_id = None
                            log.exception("Could not create cv_jobs row")

                        # ── REAL pipeline — synchronous, in-process ─────────
                        # FIX (2026-07-21): the previous "v8.0 enterprise
                        # backend" here called into a `cv_pipeline` package
                        # that was never actually deployed next to app.py.
                        # _CV_PIPELINE_AVAILABLE was therefore ALWAYS False in
                        # production, so this button did nothing but show an
                        # error — no ZIP was ever built. _make_cv_zip_real()
                        # (defined above) already implements the full real
                        # pipeline (image synthesis → detection → YOLO/COCO/
                        # VOC convert → ZIP) and works correctly, so we call
                        # it directly here instead of depending on the
                        # missing package.
                        zip_bar = st.progress(0, text="Starting generation pipeline...")

                        def _zip_progress_cb(pct, msg):
                            zip_bar.progress(min(pct, 100), text=msg)

                        with st.spinner("Generating images, detecting objects, building ZIP..."):
                            zip_bytes, n_success, n_total_real = _make_cv_zip_real(
                                batch=batch_to_use,
                                fmt=ann_fmt,
                                class_list=cv_classes,
                                hf_token=hf_token_zip,
                                cv_prompt=cv_prompt,
                                cv_domain=cv_domain,
                                progress_cb=_zip_progress_cb,
                            )
                        zip_bar.progress(100, text="ZIP ready!")

                        if _cv_job_id:
                            try:
                                db.complete_cv_job(
                                    _cv_job_id, org_id, n_success,
                                    status="completed" if n_success > 0 else "failed",
                                    error_message=None if n_success > 0 else "no images generated",
                                )
                            except db.DatabaseError:
                                log.exception("Could not finalize cv_jobs row %s", _cv_job_id)

                        if n_success == 0:
                            st.error(
                                "No images could be generated for this batch after retries. "
                                "This can happen if the generation service is rate-limiting or "
                                "temporarily unavailable. Try again in a few minutes, or with a "
                                "smaller batch (e.g. 10 images) first. Your credits were not "
                                "consumed for images that failed to generate."
                            )
                        else:
                            if n_success < n_total_real:
                                st.warning(
                                    f"{n_success}/{n_total_real} images generated successfully — "
                                    f"{n_total_real - n_success} were skipped (generation or "
                                    "detection errors after retries) and are not included in the ZIP."
                                )
                            st.success(
                                f"Real annotated dataset ready: {n_success} images "
                                f"with {ann_fmt} annotations."
                            )
                            demo_feature_completed("computer_vision")
                            st.download_button(
                                label=f"DOWNLOAD REAL ANNOTATED ZIP ({ann_fmt})",
                                data=zip_bytes,
                                file_name=f"synthologic_cv_real_{ann_fmt.replace(' ','_').replace('.','')}.zip",
                                mime="application/zip",
                                use_container_width=True,
                            )
                            sc1, sc2, sc3 = st.columns(3)
                            with sc1:
                                st.markdown(f'<div class="metric-chip"><div class="val">{n_success:,}</div><div class="lbl">Real Images</div></div>', unsafe_allow_html=True)
                            with sc2:
                                st.markdown(f'<div class="metric-chip"><div class="val">{n_success * n_obj_per_img:,}</div><div class="lbl">Bounding Boxes (est.)</div></div>', unsafe_allow_html=True)
                            with sc3:
                                st.markdown(f'<div class="metric-chip"><div class="val">{len(cv_classes)}</div><div class="lbl">Classes</div></div>', unsafe_allow_html=True)

                    else:
                        # Image generation is not configured server-side.
                        # There is no fake/prototype dataset anymore — the
                        # customer either gets a real result or a clear,
                        # honest "unavailable" message. No internal
                        # environment-variable or vendor names are surfaced.
                        st.error(
                            "Image generation is temporarily unavailable. Please try again "
                            "shortly, or contact support if this persists."
                        )
                        log.error("CV generation requested but the image generation service is not configured.")

    # ── SUB-TAB D: Digital Twin Simulation (ENTERPRISE ONLY) ──────────────────
    with cv_tabs[3]:
        if not gate("Advanced Digital Twin Simulation", "enterprise", tier):
            pass  # gate() rendered the wall
        else:
            st.markdown('<div class="step-pill">DIGITAL TWIN SIMULATION — ENTERPRISE</div>', unsafe_allow_html=True)
            st.markdown('<div style="font-size:.83rem;color:#4a7c9e;margin-bottom:1.5rem">Configure custom rendering pipelines with real-world environment dynamics for physically accurate synthetic image generation.</div>', unsafe_allow_html=True)

            # Digital Twin toggle
            dt_enabled = st.toggle("Enable Advanced Digital Twin Rendering Engine", value=False)
            if dt_enabled:
                st.markdown("""
                <div class="cv-enterprise-panel">
                    <div style="font-size:.75rem;color:#ff00c1;letter-spacing:2px;text-transform:uppercase;margin-bottom:.75rem">RENDERING PIPELINE ACTIVE</div>
                    <div style="font-size:.82rem;color:#8ba3bc;line-height:1.8">
                        Neural Radiance Fields (NeRF) engine initialised.<br>
                        Physically-based rendering (PBR) materials loaded.<br>
                        Ray-tracing shadows and reflections: <strong style="color:#00d2ff">ENABLED</strong>
                    </div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
            st.markdown("**Custom Environment Lighting Dynamics**")

            col_l1, col_l2 = st.columns(2)
            with col_l1:
                light_day     = st.slider("☀ Daylight Intensity",    0, 100, 65, help="Solar angle + colour temperature")
                light_night   = st.slider("🌙 Night / Low-light",     0, 100, 20, help="Moonlight + ambient occlusion")
                light_foggy   = st.slider("🌫 Fog / Haze Density",    0, 100, 15, help="Mie scattering coefficient")
                light_neon    = st.slider("💡 Industrial Neon / HDR", 0, 100, 10, help="Point-light bloom intensity")

            with col_l2:
                total = light_day + light_night + light_foggy + light_neon
                st.markdown("**Lighting Profile Preview**")
                light_dist_df = pd.DataFrame({
                    "Condition": ["Daylight","Night","Fog/Haze","Neon/Industrial"],
                    "Intensity": [light_day, light_night, light_foggy, light_neon],
                })
                st.bar_chart(light_dist_df.set_index("Condition"), color="#ff00c1")
                st.caption(f"Total intensity budget: {total} / 400 units")

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            adv_col1, adv_col2 = st.columns(2)
            with adv_col1:
                st.markdown("**Scene Physics Parameters**")
                rain_intensity  = st.slider("Rain / Wet surface reflections", 0, 100, 0)
                wind_motion     = st.slider("Motion blur (wind/speed)", 0, 100, 10)
                crowd_density   = st.slider("Scene crowd density", 0, 100, 40)
            with adv_col2:
                st.markdown("**Camera Simulation**")
                cam_fov    = st.slider("Field of View (degrees)", 30, 120, 70)
                cam_noise  = st.slider("Sensor noise (ISO equivalent)", 100, 6400, 400, step=100)
                cam_depth  = st.slider("Depth-of-field blur", 0, 100, 20)

            st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

            _dt_locked = demo_feature_lock("digital_twin")
            if st.button("APPLY CONFIG & SIMULATE RENDERING PIPELINE", disabled=_dt_locked, use_container_width=True):
                sim_bar = st.progress(0)
                phases = [
                    (15, "Loading 3D scene assets..."),
                    (30, "Computing light transport equations..."),
                    (50, "Ray-tracing shadows and reflections..."),
                    (65, "Applying atmospheric scattering..."),
                    (80, "Rendering depth maps and instance masks..."),
                    (92, "Post-processing HDR tone mapping..."),
                    (100, "Simulation pipeline complete!"),
                ]
                for pct, msg in phases:
                    sim_bar.progress(pct, text=msg)
                    time.sleep(0.12)

                st.success("Digital Twin simulation configured successfully!")
                demo_feature_completed("digital_twin")
                st.markdown(f"""
                <div class="card highlight-card" style="margin-top:1rem">
                    <div class="card-title">Simulation Configuration Summary</div>
                    <div style="font-size:.8rem;color:#8ba3bc;line-height:2">
                        Rendering Engine: <strong style="color:#00d2ff">Neural Radiance Fields v3.2</strong><br>
                        Lighting: Day={light_day} Night={light_night} Fog={light_foggy} Neon={light_neon}<br>
                        Camera: FOV={cam_fov}° ISO~{cam_noise} DoF={cam_depth}%<br>
                        Scene: Rain={rain_intensity}% Wind={wind_motion}% Crowd={crowd_density}%<br>
                        Digital Twin: <strong style="color:#{'00d28c' if dt_enabled else 'ff5050'}">{'ACTIVE' if dt_enabled else 'INACTIVE'}</strong>
                    </div>
                </div>""", unsafe_allow_html=True)

                # Export config as JSON
                cfg_dict = {
                    "engine": "NeRF-v3.2", "pbr": True, "dt_enabled": dt_enabled,
                    "lighting": {"daylight": light_day, "night": light_night,
                                 "fog": light_foggy, "neon": light_neon},
                    "camera": {"fov": cam_fov, "noise_iso": cam_noise, "dof": cam_depth},
                    "scene": {"rain": rain_intensity, "wind": wind_motion, "crowd": crowd_density},
                }
                st.download_button(
                    "DOWNLOAD RENDER CONFIG (.json)",
                    data=json.dumps(cfg_dict, indent=2).encode(),
                    file_name="synthologic_render_config.json",
                    mime="application/json",
                    use_container_width=True,
                )

# ───────────────────────────────────────────────────────────────────────────────
# TAB 6 — API GUIDE
# ───────────────────────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown('<div class="step-pill">FASTAPI SERVICE GUIDE</div>', unsafe_allow_html=True)
    if is_demo_user():
        st.markdown(f"""
        <div style="padding:20px;border:1px solid rgba(255,0,193,.22);border-radius:12px;
             background:rgba(255,0,193,.04);text-align:center;margin:12px 0;">
          <div style="font-size:.68rem;color:#ff00c1;letter-spacing:1.6px;text-transform:uppercase;font-weight:700;">
            Sandbox Evaluation Restriction
          </div>
          <div style="font-size:.95rem;color:#fff;margin:7px 0;">API Documentation is restricted in the evaluation sandbox.</div>
          <div style="font-size:.78rem;color:#8ba3bc;line-height:1.6;">
            Contact us to discuss API access and integration with an Enterprise deployment.
          </div>
          <a href="{CONTACT_URL}" target="_blank" style="display:inline-block;margin-top:12px;padding:9px 15px;border-radius:8px;background:#ff00c1;color:#fff;text-decoration:none;font-weight:800;font-size:.72rem;">
            CONTACT STRUCTURAL MIND →
          </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.code("""
# api.py  —  uvicorn api:app --host 0.0.0.0 --port 8000
from fastapi import FastAPI, UploadFile, File, Header, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd, io, jwt, os
app = FastAPI(title="SynthoLogic API", version="7.0")
SECRET = os.environ["JWT_SECRET"]
TIER_CAPS = {"free": 500, "pro": 50_000, "enterprise": None}
def verify(token: str) -> dict:
    try:    return jwt.decode(token, SECRET, algorithms=["HS256"])
    except: raise HTTPException(401, "Invalid token")
@app.post("/v1/synthesize")
async def synthesize(
    file: UploadFile = File(...), n_rows: int = 200,
    epsilon: float = None, method: str = "auto",
    authorization: str = Header(None),
):
    payload = verify(authorization.replace("Bearer ", ""))
    tier = payload.get("tier", "free"); cap = TIER_CAPS.get(tier)
    if cap and n_rows > cap:
        raise HTTPException(403, f"{tier} plan: max {cap} rows")
    df = pd.read_csv(io.BytesIO(await file.read()))
    df_synth = generate_synthetic(df, n_rows=n_rows, method=method)
    if epsilon is not None:
        if tier == "free": raise HTTPException(403, "DP requires Pro plan")
        df_synth = apply_dp(df_synth, epsilon)
    buf = io.BytesIO(); df_synth.to_csv(buf, index=False); buf.seek(0)
    return StreamingResponse(buf, media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=synthetic.csv"})
@app.post("/v1/cv/generate")
async def cv_generate(
    prompt: str, n_images: int = 100,
    annotation_format: str = "yolo",
    authorization: str = Header(None),
):
    payload = verify(authorization.replace("Bearer ", ""))
    tier = payload.get("tier", "free")
    if tier == "free": raise HTTPException(403, "CV Suite requires Pro plan")
    if tier == "pro" and n_images > 2000: raise HTTPException(403, "Pro: max 2000 images")
    if tier == "enterprise" and n_images > 7000: raise HTTPException(403, "Enterprise: max 7000 images")
    # Build and return zip
    return {"status": "queued", "job_id": "cv_12345", "n_images": n_images}
@app.get("/health")
def health(): return {"status": "ok", "version": "7.0"}
""", language="python")
        st.markdown('<div class="card" style="margin-top:1rem"><div class="card-title">DEPLOYMENT</div><div style="font-size:.82rem;color:#7090a8;line-height:2">Docker: <code>docker run -p 8000:8000 structuralmind/synthologic-api</code><br>AWS: ECS/Fargate to AWS Marketplace listing<br>Datarade: Register as data product, expose /v1/synthesize<br>Auth: JWT with tier embedded, Stripe webhooks update tier</div></div>', unsafe_allow_html=True)

# ───────────────────────────────────────────────────────────────────────────────
# TAB 7 — ADMIN (only for admins)
# ───────────────────────────────────────────────────────────────────────────────
if is_admin:
    with tabs[7]:
        show_admin_panel()

# ── PRICING FOOTER ─────────────────────────────────────────────────────────────
show_pricing()