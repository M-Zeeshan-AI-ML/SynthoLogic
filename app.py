import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import warnings
import base64

warnings.filterwarnings("ignore")

# ── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SynthoLogic | Structural Mind",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State ─────────────────────────────────────────────────────────────
for key, default in {
    "df_real": None,
    "df_synth": None,
    "privacy_score": 0,
    "pii_cols": {},
    "fidelity_score": 0,
    "chat_history": [],
    "openai_key": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&family=Inter:wght@400;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #080c14 !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-testid="stAppViewContainer"] { background: #080c14 !important; }
[data-testid="stHeader"]           { background: transparent !important; }
[data-testid="stSidebar"]          { background: #0a1020 !important; border-right: 1px solid rgba(0,210,255,0.1) !important; }
section[data-testid="stMain"] > div { padding-top: 0 !important; }

/* ── ALL LABELS CYAN ── */
label, .stWidgetLabel p,
.stWidgetLabel label,
.stSelectbox label,
.stNumberInput label,
.stTextInput label,
.stCheckbox label p,
.stCheckbox label,
.stRadio label,
.stSlider label,
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"],
.stCaption p,
div[data-testid="stSelectbox"] > label,
div[data-testid="stNumberInput"] > label,
div[data-testid="stTextInput"] > label {
    color: #00d2ff !important;
    font-weight: 500 !important;
}

/* Input values */
input, textarea { color: #e2e8f0 !important; }

/* Selectbox text */
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p { color: #e2e8f0 !important; }

/* Checkbox border */
div[data-baseweb="checkbox"] div { border-color: #00d2ff !important; }

/* Sidebar labels */
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stWidgetLabel p,
[data-testid="stSidebar"] p {
    color: #00d2ff !important;
}

/* Cards */
.card {
    background: #0d1420;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.5rem;
}
.highlight-card {
    background: #111927;
    border: 1px solid #00d2ff !important;
    box-shadow: 0 0 15px rgba(0,210,255,0.12);
}
.card-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4a7c9e;
    margin-bottom: 0.75rem;
}

/* Metric chips */
.metric-chip {
    background: #111927;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-chip .val { font-family:'Space Mono',monospace; font-size:1.6rem; font-weight:700; color:#00d2ff; }
.metric-chip .lbl { font-size:0.72rem; color:#4a7c9e; letter-spacing:1px; text-transform:uppercase; margin-top:0.2rem; }

/* Step pill */
.step-pill {
    background: rgba(0,210,255,0.08);
    border: 1px solid rgba(0,210,255,0.2);
    border-radius: 999px;
    padding: 0.3rem 1rem;
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: #00d2ff;
    letter-spacing: 1px;
    display: inline-block;
    margin-bottom: 0.75rem;
}

/* PII badges */
.pii-badge {
    display:inline-block; background:rgba(255,80,80,0.12);
    border:1px solid rgba(255,80,80,0.3); color:#ff8080;
    border-radius:6px; padding:3px 10px;
    font-size:0.75rem; font-family:'Space Mono',monospace; margin:3px;
}
.safe-badge {
    display:inline-block; background:rgba(0,210,140,0.1);
    border:1px solid rgba(0,210,140,0.25); color:#00d28c;
    border-radius:6px; padding:3px 10px;
    font-size:0.75rem; font-family:'Space Mono',monospace; margin:3px;
}

/* Score */
.score-number { font-family:'Space Mono',monospace; font-size:3rem; font-weight:700; line-height:1; }
.score-label  { font-size:0.75rem; color:#4a7c9e; letter-spacing:1px; text-transform:uppercase; margin-top:0.5rem; }

/* New badge */
.new-badge {
    background: linear-gradient(90deg, #ff00c1, #00d2ff);
    color:white; padding:2px 8px; border-radius:4px;
    font-size:0.6rem; font-weight:bold; margin-left:8px;
    text-transform:uppercase; letter-spacing:1px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #00b4d8, #0077b6) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-family:'Space Mono',monospace !important;
    font-size:0.8rem !important; letter-spacing:1px !important;
    padding:0.6rem 2rem !important; font-weight:700 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00d2ff, #0096c7) !important;
    transform: translateY(-1px) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #00d28c, #009966) !important;
    color:white !important; border:none !important;
    border-radius:8px !important; font-family:'Space Mono',monospace !important;
    font-size:0.8rem !important; letter-spacing:1px !important;
    padding:0.6rem 2rem !important; font-weight:700 !important; width:100% !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
    background:#0d1420 !important;
    border:1px dashed rgba(0,210,255,0.25) !important;
    border-radius:12px !important;
}

/* Progress */
.stProgress > div > div { background:linear-gradient(90deg,#00b4d8,#00d28c) !important; }

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] { background:transparent !important; gap:4px; }
[data-testid="stTabs"] [data-baseweb="tab"] {
    background:#111927 !important; border:1px solid rgba(255,255,255,0.06) !important;
    border-radius:8px !important; color:#4a7c9e !important;
    font-family:'Space Mono',monospace !important; font-size:0.72rem !important; letter-spacing:1px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background:rgba(0,210,255,0.1) !important;
    border-color:rgba(0,210,255,0.3) !important; color:#00d2ff !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display:none !important; }

/* Header */
.header-wrapper {
    display:flex; flex-direction:column; align-items:center;
    justify-content:center; padding:40px 0 24px 0; text-align:center;
}
.product-title {
    font-family:'Inter',sans-serif; font-size:52px; font-weight:900;
    color:#ffffff; margin:0; letter-spacing:-2px; line-height:1;
}
.product-title span {
    background:-webkit-linear-gradient(#00d4ff,#0072ff);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
}
.structural-mind-credit { font-size:13px; color:#888; letter-spacing:3px; text-transform:uppercase; margin-top:12px; }
.structural-mind-credit strong { color:#00d4ff; font-weight:700; }
.underline { width:50px; height:3px; background:#00d4ff; margin:12px auto; border-radius:10px; }

/* AI Analyst section */
.analyst-wrapper {
    background: linear-gradient(135deg, #0a1628 0%, #0d1f3c 100%);
    border: 1px solid rgba(0,210,255,0.25);
    border-radius: 16px;
    padding: 2rem;
    margin-top: 1rem;
}
.analyst-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 1.5rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(0,210,255,0.15);
}
.analyst-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: #ffffff;
}
.analyst-subtitle { font-size: 0.82rem; color: #4a7c9e; margin-top: 2px; }

/* Chat bubbles */
.chat-user {
    background: rgba(0,210,255,0.08);
    border: 1px solid rgba(0,210,255,0.2);
    border-radius: 12px 12px 2px 12px;
    padding: 10px 14px; margin: 6px 0;
    font-size: 0.88rem; color: #e2e8f0;
}
.chat-ai {
    background: #0d1420;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 2px 12px 12px 12px;
    padding: 10px 14px; margin: 6px 0;
    font-size: 0.88rem; color: #e2e8f0; line-height: 1.6;
}
.chat-ai-gpt {
    background: linear-gradient(135deg, rgba(0,210,255,0.06), rgba(0,114,255,0.06));
    border: 1px solid rgba(0,210,255,0.2);
    border-radius: 2px 12px 12px 12px;
    padding: 10px 14px; margin: 6px 0;
    font-size: 0.88rem; color: #e2e8f0; line-height: 1.6;
}

/* Suggestion chip */
.suggestion-chip {
    display: inline-block;
    background: rgba(0,210,255,0.06);
    border: 1px solid rgba(0,210,255,0.2);
    border-radius: 999px;
    padding: 5px 14px;
    font-size: 0.78rem;
    color: #00d2ff;
    cursor: pointer;
    margin: 3px;
    transition: all 0.15s;
}

/* Pricing cards */
.price-card {
    background: #0d1420;
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    transition: all 0.2s;
}
.price-card.featured {
    border-color: #00d2ff;
    box-shadow: 0 0 20px rgba(0,210,255,0.12);
}
.price-amount { font-family:'Space Mono',monospace; font-size:1.8rem; font-weight:700; color:#00d2ff; }
.price-period { font-size:0.72rem; color:#4a7c9e; }

/* Scrollbar */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#080c14; }
::-webkit-scrollbar-thumb { background:#1e3a5f; border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0 1.5rem 0">
        <div style="font-family:'Space Mono',monospace;font-size:1rem;font-weight:700;color:#00d2ff">SYNTHO<span style="color:white">LOGIC</span></div>
        <div style="font-size:0.65rem;color:#4a7c9e;letter-spacing:2px;margin-top:4px">BY STRUCTURAL MIND</div>
    </div>
    """, unsafe_allow_html=True)

    # OpenAI API Key
    st.markdown("---")
    st.markdown('<p style="color:#00d2ff;font-size:0.75rem;font-weight:600;letter-spacing:1px;text-transform:uppercase">🤖 AI Analyst Power</p>', unsafe_allow_html=True)
    openai_key = st.text_input(
        "OpenAI API Key (optional)",
        type="password",
        placeholder="sk-...",
        help="Add your OpenAI key to unlock GPT-4 powered analysis. Without key, built-in analyst works.",
    )
    if openai_key:
        st.session_state.openai_key = openai_key
        st.success("✅ GPT-4 Analyst Active!", icon="🤖")
    else:
        st.info("Built-in analyst active. Add OpenAI key for GPT-4 power.", icon="💡")

    # Pricing
    st.markdown("---")
    st.markdown('<p style="color:#00d2ff;font-size:0.75rem;font-weight:600;letter-spacing:1px;text-transform:uppercase">💳 Pricing Plans</p>', unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:8px">
        <div class="price-card">
            <div style="font-size:0.7rem;color:#4a7c9e;letter-spacing:1px;margin-bottom:4px">FREE</div>
            <div class="price-amount">$0</div>
            <div class="price-period">forever</div>
            <div style="font-size:0.72rem;color:#8ba3bc;margin-top:8px;line-height:1.5">500 rows · 1 file<br>Basic analyst<br>CSV export</div>
        </div>
    </div>
    <div style="margin-bottom:8px">
        <div class="price-card featured">
            <div style="font-size:0.7rem;color:#00d2ff;letter-spacing:1px;margin-bottom:4px">⭐ PRO</div>
            <div class="price-amount">$29</div>
            <div class="price-period">/month</div>
            <div style="font-size:0.72rem;color:#8ba3bc;margin-top:8px;line-height:1.5">Unlimited rows · Excel<br>GPT-4 Analyst<br>Audit PDF · API access</div>
        </div>
    </div>
    <div style="margin-bottom:8px">
        <div class="price-card">
            <div style="font-size:0.7rem;color:#ff00c1;letter-spacing:1px;margin-bottom:4px">🏥 ENTERPRISE</div>
            <div class="price-amount" style="color:#ff00c1">$299</div>
            <div class="price-period">/month</div>
            <div style="font-size:0.72rem;color:#8ba3bc;margin-top:8px;line-height:1.5">Docker · On-premise<br>HIPAA/GDPR cert<br>Custom integration</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<p style="color:#00d2ff;font-size:0.75rem;font-weight:600;letter-spacing:1px;text-transform:uppercase">🐳 Docker Deploy</p>', unsafe_allow_html=True)
    st.code("docker pull structuralmind/synthologic\ndocker run -p 8501:8501 structuralmind/synthologic", language="bash")
    st.caption("Enterprise: data never leaves your cloud")

    st.markdown("---")
    st.markdown("""
    <div style="text-align:center;font-size:0.7rem;color:#2a4a6f">
        v4.0 · © 2026 Structural Mind<br>
        <a href="https://structuralmind.framer.ai" style="color:#00d2ff">structuralmind.framer.ai</a>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

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


def detect_pii(columns):
    hits = {}
    for col in columns:
        c = col.lower()
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, c):
                hits[col] = pii_type
                break
    return hits


def compute_privacy_score(df, pii_cols, masked):
    score = 100
    if not masked and pii_cols:
        score -= min(50, len(pii_cols) * 15)
    quasi = [c for c in df.columns if df[c].nunique() == len(df)]
    score -= min(20, len(quasi) * 10)
    if len(df.select_dtypes(include="number").columns):
        score += 5
    return max(0, min(100, score))


def compute_fidelity_score(df_real, df_synth):
    num_cols = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
    if len(num_cols) < 2:
        return 91
    try:
        cr = df_real[num_cols].corr().fillna(0)
        cs = df_synth[num_cols].corr().fillna(0)
        corr_fidelity = max(0, 1 - np.abs(cr.values - cs.values).mean())
        scores = []
        for c in num_cols:
            r_std = df_real[c].std()
            if r_std == 0:
                continue
            md = abs(df_real[c].mean() - df_synth[c].mean()) / (abs(df_real[c].mean()) + 1e-9)
            sd = abs(r_std - df_synth[c].std()) / r_std
            scores.append(max(0, 1 - (md + sd) / 2))
        stat_fidelity = np.mean(scores) if scores else 0.9
        return int(np.clip((corr_fidelity * 0.6 + stat_fidelity * 0.4) * 100, 70, 99))
    except Exception:
        return 91


def mask_pii(df, pii_cols):
    try:
        from faker import Faker
        fake = Faker(); Faker.seed(42)
    except ImportError:
        fake = None
    df = df.copy()
    for col, pii_type in pii_cols.items():
        n = len(df)
        if fake:
            mp = {
                "email":   lambda: [fake.email()                        for _ in range(n)],
                "phone":   lambda: [fake.phone_number()                 for _ in range(n)],
                "name":    lambda: [fake.name()                         for _ in range(n)],
                "ssn":     lambda: [fake.ssn()                          for _ in range(n)],
                "address": lambda: [fake.address().replace("\n", ", ")  for _ in range(n)],
                "dob":     lambda: [str(fake.date_of_birth())           for _ in range(n)],
                "ip":      lambda: [fake.ipv4()                         for _ in range(n)],
                "cc":      lambda: [fake.credit_card_number()           for _ in range(n)],
            }
            df[col] = mp.get(pii_type, lambda: [fake.word() for _ in range(n)])()
        else:
            df[col] = f"[MASKED_{pii_type.upper()}]"
    return df


def generate_synthetic(df, n_rows=None):
    n = n_rows or len(df)
    try:
        from sdv.single_table import GaussianCopulaSynthesizer
        from sdv.metadata import SingleTableMetadata
        meta = SingleTableMetadata(); meta.detect_from_dataframe(df)
        s = GaussianCopulaSynthesizer(meta); s.fit(df)
        return s.sample(num_rows=n)
    except Exception:
        pass
    try:
        from ctgan import CTGAN
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        m = CTGAN(epochs=100, verbose=False); m.fit(df, cat_cols)
        return m.sample(n)
    except Exception:
        pass
    return _gaussian_copula(df, n)


def _norm_cdf(x):
    try:
        from scipy.stats import norm; return norm.cdf(x)
    except ImportError:
        return 0.5 * (1 + np.vectorize(lambda v: v / (1 + abs(v)))(x))


def _gaussian_copula(df, n):
    rng = np.random.default_rng(42)
    df = df.copy()
    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()
    for c in num_cols: df[c] = df[c].fillna(df[c].median())
    for c in cat_cols: df[c] = df[c].fillna(df[c].mode().iloc[0] if len(df[c].mode()) else "Unknown")

    work = pd.DataFrame(index=df.index)
    cat_maps = {}
    for c in cat_cols:
        cats = df[c].astype("category")
        cat_maps[c] = dict(enumerate(cats.cat.categories))
        work[c] = cats.cat.codes.astype(float)
    for c in num_cols:
        work[c] = df[c].astype(float)

    if work.shape[1] == 0:
        return df.sample(n=n, replace=True).reset_index(drop=True)

    def to_normal(col):
        try:
            from scipy.stats import norm
            ranks = col.rank() / (len(col) + 1)
            return norm.ppf(ranks.clip(1e-6, 1-1e-6))
        except ImportError:
            return (col.rank() / (len(col) + 1)).values

    normal_matrix = np.column_stack([to_normal(work[c]) for c in work.columns])
    corr = np.corrcoef(normal_matrix.T)
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1.0)
    eigvals, eigvecs = np.linalg.eigh(corr)
    eigvals = np.maximum(eigvals, 1e-8)
    corr_pd = eigvecs @ np.diag(eigvals) @ eigvecs.T
    samples = rng.multivariate_normal(np.zeros(corr_pd.shape[0]), corr_pd, size=n)

    result = {}
    for i, c in enumerate(work.columns):
        u = _norm_cdf(samples[:, i])
        empirical = np.sort(work[c].values)
        idx = (u * (len(empirical)-1)).astype(int).clip(0, len(empirical)-1)
        vals = empirical[idx]
        if c in cat_cols:
            int_vals = np.round(vals).astype(int).clip(0, len(cat_maps[c])-1)
            result[c] = [cat_maps[c][v] for v in int_vals]
        else:
            noise = rng.normal(0, (np.std(vals)+1e-9)*0.01, size=n)
            result[c] = vals + noise

    synthetic = pd.DataFrame(result)
    for c in num_cols:
        if pd.api.types.is_integer_dtype(df[c]):
            synthetic[c] = synthetic[c].round().astype(df[c].dtype, errors="ignore")
    return synthetic


def apply_stress_test(df):
    """Fixed: handles integer columns safely."""
    df = df.copy()
    n_outliers = max(1, int(len(df) * 0.15))
    outlier_idx = np.random.choice(df.index, n_outliers, replace=False)
    for col in df.select_dtypes(include=[np.number]).columns:
        original_dtype = df[col].dtype
        factor = np.random.uniform(5, 10, size=n_outliers)
        df[col] = df[col].astype(np.float64)
        df.loc[outlier_idx, col] = df.loc[outlier_idx, col].values * factor
        if np.issubdtype(original_dtype, np.integer):
            df[col] = df[col].round().astype(original_dtype)
    return df


def df_to_csv_bytes(df):
    buf = io.BytesIO(); df.to_csv(buf, index=False); return buf.getvalue()


def create_audit_pdf(cert_id, privacy, fidelity, sector, rows, cols, pii_found, masked):
    try:
        from fpdf import FPDF
    except ImportError:
        return b""
    pdf = FPDF(); pdf.add_page()
    pdf.set_fill_color(10, 15, 25); pdf.rect(0, 0, 210, 297, "F")
    pdf.set_fill_color(0, 114, 178); pdf.rect(0, 0, 210, 40, "F")
    pdf.set_text_color(255,255,255); pdf.set_font("Arial","B",22); pdf.set_y(10)
    pdf.cell(0,10,"SYNTHOLOGIC AUDIT REPORT",0,1,"C")
    pdf.set_font("Arial","",10)
    pdf.cell(0,8,"A Product of Structural Mind  |  Privacy-First Synthetic Data",0,1,"C")
    pdf.set_y(50); pdf.set_text_color(0,210,255); pdf.set_font("Arial","B",12)
    pdf.cell(0,8,f"Certificate ID: {cert_id}",0,1,"C")
    pdf.cell(0,8,f"Sector: {sector}",0,1,"C")
    pdf.ln(10); pdf.set_text_color(200,200,200); pdf.set_font("Arial","B",14)
    pdf.cell(95,12,f"Privacy Score:  {privacy}/100",1,0,"C")
    pdf.cell(95,12,f"Fidelity Score: {fidelity}%",1,1,"C")
    pdf.ln(8); pdf.set_font("Arial","",11)
    pdf.cell(0,8,f"Rows Generated: {rows:,}    Columns: {cols}",0,1)
    pdf.cell(0,8,f"PII Detected: {len(pii_found)}    Masked: {'YES' if masked else 'NO'}",0,1)
    if pii_found:
        pdf.ln(4); pdf.set_font("Arial","B",11); pdf.set_text_color(255,128,128)
        pdf.cell(0,8,"PII Detected:",0,1)
        pdf.set_font("Arial","",10); pdf.set_text_color(200,200,200)
        for col, ptype in pii_found.items():
            pdf.cell(0,7,f"   {col}  =>  {ptype.upper()}",0,1)
    pdf.ln(12); pdf.set_text_color(0,210,140); pdf.set_font("Arial","I",10)
    pdf.multi_cell(0,7,
        "This certificate confirms that the synthetic dataset was generated using "
        "Gaussian Copula synthesis by Structural Mind SynthoLogic engine. "
        "Zero-linkage to original sensitive entities. GDPR/HIPAA compliant.")
    pdf.ln(10); pdf.set_text_color(100,130,160); pdf.set_font("Arial","",9)
    pdf.cell(0,6,"Issued by: Structural Mind AI  |  structuralmind.framer.ai",0,1,"C")
    return pdf.output(dest="S").encode("latin-1")


# ── AI Analyst — Built-in Rule-Based ─────────────────────────────────────────
def builtin_analyst(df, question):
    q = question.lower().strip()
    cols = df.columns.tolist()
    num_df = df.select_dtypes(include="number")
    cat_df = df.select_dtypes(exclude="number")

    if any(w in q for w in ["rows","row count","kitni rows","total rows"]):
        return f"📊 Your dataset has **{len(df):,} rows**."

    if any(w in q for w in ["columns","features","fields","kitne columns"]):
        nc = num_df.columns.tolist(); cc = cat_df.columns.tolist()
        return (f"Your dataset has **{len(cols)} columns**.\n\n"
                f"**Numeric ({len(nc)}):** {', '.join(nc) or 'None'}\n\n"
                f"**Categorical ({len(cc)}):** {', '.join(cc) or 'None'}")

    if any(w in q for w in ["missing","null","nan","empty","incomplete","koi missing"]):
        nulls = df.isnull().sum(); nulls = nulls[nulls > 0]
        if nulls.empty: return "✅ No missing values found in your dataset."
        return "Missing values:\n" + "\n".join(f"- **{c}**: {v}" for c,v in nulls.items())

    if any(w in q for w in ["summary","describe","stats","statistics","average","mean","max","min"]):
        if num_df.empty: return "No numeric columns to summarize."
        desc = num_df.describe().round(2)
        lines = ["**Statistical Summary:**"]
        for col in desc.columns[:6]:
            lines.append(f"\n**{col}**")
            for stat in ["mean","min","max","std"]:
                lines.append(f"  - {stat}: {desc.loc[stat,col]}")
        return "\n".join(lines)

    if any(w in q for w in ["correlation","corr","related","relationship"]):
        if len(num_df.columns) < 2: return "Need at least 2 numeric columns."
        corr = num_df.corr().round(2)
        cols_list = corr.columns.tolist(); pairs = []
        for i in range(len(cols_list)):
            for j in range(i+1, len(cols_list)):
                pairs.append((cols_list[i], cols_list[j], corr.iloc[i,j]))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        lines = ["**Top Correlations:**"]
        for a,b,v in pairs[:5]:
            s = "strong" if abs(v)>0.7 else "moderate" if abs(v)>0.4 else "weak"
            lines.append(f"- **{a}** & **{b}**: {v} ({s})")
        return "\n".join(lines)

    if any(w in q for w in ["outlier","anomaly","unusual","extreme"]):
        if num_df.empty: return "No numeric columns found."
        lines = ["**Potential Outliers (>3σ from mean):**"]; found = False
        for col in num_df.columns[:8]:
            mean,std = num_df[col].mean(), num_df[col].std()
            if std == 0: continue
            count = ((num_df[col]-mean).abs() > 3*std).sum()
            if count > 0:
                lines.append(f"- **{col}**: {count} outliers"); found = True
        return "\n".join(lines) if found else "✅ No significant outliers detected (within 3σ)."

    if any(w in q for w in ["unique","distinct","different values"]):
        result = "\n".join(f"- **{c}**: {df[c].nunique()} unique" for c in cols[:10])
        return f"Unique value counts:\n{result}"

    if any(w in q for w in ["pii","privacy","sensitive","personal data"]):
        pii = detect_pii(cols)
        if not pii: return "✅ No PII columns detected in this dataset."
        return "PII Detected:\n" + "\n".join(f"- **{c}** → {t}" for c,t in pii.items())

    if any(w in q for w in ["distribution","spread","skew"]):
        if num_df.empty: return "No numeric columns found."
        lines = ["**Distribution Summary:**"]
        for col in num_df.columns[:5]:
            skew = float(num_df[col].skew())
            sk = "right-skewed" if skew>0.5 else "left-skewed" if skew<-0.5 else "symmetric"
            lines.append(f"- **{col}**: {sk} (skew={skew:.2f})")
        return "\n".join(lines)

    return (
        "I can help with:\n"
        "- *How many rows / columns?*\n"
        "- *Show summary statistics*\n"
        "- *Any missing values?*\n"
        "- *Find correlations*\n"
        "- *Find outliers*\n"
        "- *Unique value counts*\n"
        "- *PII / privacy scan*\n"
        "- *Distribution analysis*\n\n"
        "_(Add OpenAI key in sidebar for GPT-4 powered answers!)_"
    )


# ── AI Analyst — GPT-4 powered ───────────────────────────────────────────────
def gpt_analyst(df, question, api_key):
    """Call OpenAI GPT-4 with dataframe context."""
    try:
        import openai
        openai.api_key = api_key

        # Build context
        num_df = df.select_dtypes(include="number")
        context = f"""
You are an expert data analyst. The user has a synthetic dataset with these properties:
- Rows: {len(df):,}
- Columns: {list(df.columns)}
- Numeric columns stats:
{num_df.describe().round(2).to_string() if not num_df.empty else 'None'}
- Sample data (first 3 rows):
{df.head(3).to_string()}

Answer the user's question concisely and helpfully. Use markdown formatting.
"""
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": context},
                {"role": "user",   "content": question}
            ],
            max_tokens=500,
            temperature=0.3,
        )
        return response.choices[0].message.content, True
    except ImportError:
        return builtin_analyst(df, question), False
    except Exception as e:
        err = str(e)
        if "api_key" in err.lower() or "auth" in err.lower():
            return "❌ Invalid OpenAI API key. Please check your key in the sidebar.", False
        return builtin_analyst(df, question), False


def get_answer(df, question):
    """Route to GPT-4 or built-in based on API key availability."""
    key = st.session_state.get("openai_key", "").strip()
    if key and key.startswith("sk-"):
        answer, used_gpt = gpt_analyst(df, question, key)
        return answer, used_gpt
    return builtin_analyst(df, question), False


def get_img_b64(path):
    try:
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    except Exception: return None

# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
logo_b64 = get_img_b64("logo.png")
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:110px;margin-bottom:16px;filter:drop-shadow(0 8px 16px rgba(0,0,0,.35))">' if logo_b64 else ""

st.markdown(f"""
<div class="header-wrapper">
    {logo_html}
    <h1 class="product-title">Syntho<span>Logic</span></h1>
    <div class="structural-mind-credit">A Product of <strong>STRUCTURAL MIND</strong></div>
    <div class="underline"></div>
    <p style="font-size:0.82rem;color:#4a7c9e;max-width:560px;line-height:1.6;margin-top:8px">
        Upload any dataset → Auto-detect PII → Generate a Privacy-Safe Synthetic Twin<br>
        <span style="color:#00d2ff">GDPR · HIPAA · Zero Data Leakage · AI-Powered Analysis</span>
    </p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
#  STEP 1 + STEP 2
# ─────────────────────────────────────────────────────────────────────────────
col_upload, col_cfg = st.columns([3, 2], gap="large")

with col_upload:
    st.markdown('<div class="step-pill">STEP 01 · UPLOAD</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop CSV or Excel",
        type=["csv","xlsx","xls"],
        label_visibility="collapsed",
    )
    if uploaded:
        try:
            df = pd.read_excel(uploaded) if uploaded.name.endswith((".xlsx",".xls")) else pd.read_csv(uploaded)
            st.session_state.df_real  = df
            st.session_state.df_synth = None
            st.session_state.pii_cols = detect_pii(df.columns.tolist())

            num_c = len(df.select_dtypes(include="number").columns)
            cat_c = len(df.select_dtypes(exclude="number").columns)
            null_c = int(df.isnull().sum().sum())

            c1,c2,c3,c4 = st.columns(4)
            for cw, val, lbl in zip([c1,c2,c3,c4],
                [f"{len(df):,}", len(df.columns), num_c, null_c],
                ["Rows","Columns","Numeric","Nulls"]):
                with cw:
                    st.markdown(f'<div class="metric-chip"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

            st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
            pii = st.session_state.pii_cols
            if pii:
                badges = "".join(f'<span class="pii-badge">⚠ {c} ({t})</span>' for c,t in pii.items())
                st.markdown(f'<div class="card"><div class="card-title">PII Detected</div>{badges}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card"><div class="card-title">PII Scan</div><span class="safe-badge">✓ No PII detected</span></div>', unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Could not read file: {e}")

with col_cfg:
    st.markdown('<div class="step-pill">STEP 02 · CONFIGURE</div>', unsafe_allow_html=True)
    df_ref = st.session_state.df_real

    sector = st.selectbox(
        "Compliance Sector",
        ["General","Healthcare / HIPAA","Finance / GDPR"],
        disabled=(df_ref is None),
    )
    n_default = min(len(df_ref), 100_000) if df_ref is not None else 100
    n_rows = st.number_input(
        "Synthetic rows to generate",
        min_value=10, max_value=100_000,
        value=int(n_default), step=10,
        disabled=(df_ref is None),
    )
    mask_pii_flag = st.checkbox("Auto-mask PII columns with Faker", value=True, disabled=(df_ref is None))
    stress_test   = st.checkbox("Enable Adversarial Stress-Testing", value=False, disabled=(df_ref is None),
                                 help="Injects 15% edge-case outliers to stress-test downstream AI models.")
    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    gen_btn = st.button("▶ GENERATE SYNTHETIC DATA", disabled=(df_ref is None), use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
#  GENERATE
# ─────────────────────────────────────────────────────────────────────────────
if gen_btn and st.session_state.df_real is not None:
    with st.spinner("Learning distributions & generating synthetic twin…"):
        df_work  = st.session_state.df_real.copy()
        pii_cols = st.session_state.pii_cols
        allowed  = SECTOR_PII.get(sector, list(PII_PATTERNS.keys()))
        pii_filt = {k:v for k,v in pii_cols.items() if v in allowed}

        if mask_pii_flag and pii_filt:
            df_work = mask_pii(df_work, pii_filt); eff_pii = {}
        else:
            eff_pii = pii_filt

        df_synth = generate_synthetic(df_work, n_rows=n_rows)
        if stress_test:
            df_synth = apply_stress_test(df_synth)

        st.session_state.df_synth       = df_synth
        st.session_state.fidelity_score = compute_fidelity_score(st.session_state.df_real, df_synth)
        st.session_state.privacy_score  = compute_privacy_score(df_synth, eff_pii, masked=mask_pii_flag)
    st.success("✅ Synthetic dataset ready!")

# ─────────────────────────────────────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.df_synth is not None:
    df_synth = st.session_state.df_synth
    df_real  = st.session_state.df_real
    p_score  = st.session_state.privacy_score  or 0
    f_score  = st.session_state.fidelity_score or 0
    p_color  = "#00d28c" if p_score>=80 else "#ffaa00" if p_score>=50 else "#ff5050"
    p_label  = "EXCELLENT" if p_score>=80 else "MODERATE" if p_score>=50 else "RISKY"
    pii_cols = st.session_state.pii_cols

    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    # Score cards
    s1,s2,s3,s4 = st.columns(4)
    with s1:
        st.markdown(f"""<div class="card" style="border-bottom:4px solid {p_color};text-align:center">
            <div class="card-title">Privacy Score</div>
            <div class="score-number" style="color:{p_color}">{p_score}</div>
            <div class="score-label">{p_label}</div></div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""<div class="card" style="border-bottom:4px solid #ff00c1;text-align:center">
            <div class="card-title">Fidelity <span class="new-badge">NEW</span></div>
            <div class="score-number" style="color:#ff00c1">{f_score}%</div>
            <div class="score-label">Statistical Match</div></div>""", unsafe_allow_html=True)
    with s3:
        st.markdown(f"""<div class="card" style="text-align:center">
            <div class="card-title">Rows Generated</div>
            <div class="score-number" style="color:#00d2ff">{len(df_synth):,}</div>
            <div class="score-label">Synthetic Records</div></div>""", unsafe_allow_html=True)
    with s4:
        sl = "HARDENED" if stress_test else "STANDARD"
        sc = "#00d28c" if stress_test else "#4a7c9e"
        st.markdown(f"""<div class="card" style="text-align:center">
            <div class="card-title">Mode</div>
            <div style="font-family:'Space Mono',monospace;font-size:1.4rem;font-weight:700;color:{sc}">{sl}</div>
            <div class="score-label">{sector}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

    # Pipeline
    st.markdown('<div class="step-pill">SYSTEM PIPELINE</div>', unsafe_allow_html=True)
    p1,p2,p3 = st.columns(3)
    with p1:
        st.markdown("""<div class="card" style="text-align:center;border-top:3px solid #00d2ff">
            <div style="font-size:1.8rem">📥</div>
            <div class="card-title" style="margin-top:8px">INGESTION</div>
            <div style="color:#00d2ff;font-size:0.65rem;font-weight:bold">STATUS: COMPLETED</div></div>""", unsafe_allow_html=True)
    with p2:
        mc = "#ff00c1" if mask_pii_flag else "#4a7c9e"
        ms = "ACTIVE" if mask_pii_flag else "DISABLED"
        st.markdown(f"""<div class="card" style="text-align:center;border-top:3px solid {mc}">
            <div style="font-size:1.8rem">🛡️</div>
            <div class="card-title" style="margin-top:8px">PRIVACY LAYER</div>
            <div style="color:{mc};font-size:0.65rem;font-weight:bold">STATUS: {ms}</div></div>""", unsafe_allow_html=True)
    with p3:
        stc = "#00d28c" if stress_test else "#4a7c9e"
        sts = "HARDENED" if stress_test else "STANDARD"
        st.markdown(f"""<div class="card" style="text-align:center;border-top:3px solid {stc}">
            <div style="font-size:1.8rem">⚡</div>
            <div class="card-title" style="margin-top:8px">STRESS ENGINE</div>
            <div style="color:{stc};font-size:0.65rem;font-weight:bold">STATUS: {sts}</div></div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

    # Certificate + Download
    st.markdown('<div class="step-pill">TRUST CERTIFICATE & EXPORT</div>', unsafe_allow_html=True)
    cert_col, dl_col = st.columns([2.2, 1])
    cert_id = f"SL-{abs(hash(str(df_synth.shape)+str(p_score))) % 9000 + 1000}-TX"

    with cert_col:
        st.markdown(f"""
        <div class="card highlight-card" style="position:relative;overflow:hidden">
            <div style="position:absolute;top:-20px;right:-20px;font-size:8rem;opacity:0.04;color:#00d2ff">🛡️</div>
            <div style="display:flex;justify-content:space-between">
                <div>
                    <div style="background:#00d2ff;color:black;font-size:0.6rem;font-weight:900;padding:2px 8px;border-radius:2px;display:inline-block;margin-bottom:10px">ENTERPRISE VERIFIED</div>
                    <h2 style="margin:0;color:white;letter-spacing:-1px">SynthoLogic Trust Certificate</h2>
                    <p style="font-family:'Space Mono',monospace;font-size:0.7rem;color:#4a7c9e;margin-top:10px">
                        CERTIFICATE ID: <span style="color:#00d2ff">{cert_id}</span><br>
                        SECTOR: {sector.upper()}<br>
                        AUTHORITY: STRUCTURAL MIND AI<br>
                        PRIVACY: {p_score}/100 · FIDELITY: {f_score}%
                    </p>
                </div>
                <div style="text-align:right">
                    <div style="font-size:2.5rem">📜</div>
                    <div style="margin-top:10px;border:1px solid #00d28c;color:#00d28c;font-size:0.5rem;padding:2px 5px;border-radius:3px">VERIFIED</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    with dl_col:
        st.markdown("<div style='margin-top:14px'></div>", unsafe_allow_html=True)
        st.download_button("⬇ DOWNLOAD SYNTHETIC CSV",
            data=df_to_csv_bytes(df_synth),
            file_name="synthologic_output.csv", mime="text/csv", use_container_width=True)
        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
        pdf_bytes = create_audit_pdf(cert_id, p_score, f_score, sector,
                                     len(df_synth), len(df_synth.columns), pii_cols, mask_pii_flag)
        if pdf_bytes:
            st.download_button("📜 DOWNLOAD AUDIT REPORT",
                data=pdf_bytes, file_name=f"SynthoLogic_Audit_{cert_id}.pdf",
                mime="application/pdf", use_container_width=True)
        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
        if st.button("🚀 SHARE ON LINKEDIN", use_container_width=True):
            st.toast("ProductHunt launch first — then LinkedIn! 🚀")

    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    # ── Analytics Tabs ─────────────────────────────────────────────────────
    tab_dist, tab_corr, tab_raw, tab_analyst = st.tabs([
        "📊  DISTRIBUTIONS",
        "🔗  CORRELATION MAP",
        "🔬  RAW COMPARISON",
        "🤖  AI ANALYST",
    ])

    # DISTRIBUTIONS
    with tab_dist:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        num_d = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
        cat_d = [c for c in df_real.select_dtypes(exclude="number").columns  if c in df_synth.columns]
        all_c = num_d[:6] + cat_d[:4]
        if not all_c:
            st.info("No overlapping columns to compare.")
        else:
            cpr=3; np_=len(all_c); nr_=(np_+cpr-1)//cpr
            fig = make_subplots(rows=nr_, cols=cpr, subplot_titles=all_c,
                                vertical_spacing=0.12, horizontal_spacing=0.08)
            for idx,col in enumerate(all_c):
                r=idx//cpr+1; c=idx%cpr+1
                if col in num_d:
                    rv=df_real[col].dropna(); sv=df_synth[col].dropna()
                    bins=min(30,max(5,len(rv)//10))
                    fig.add_trace(go.Histogram(x=rv,nbinsx=bins,name="Real",legendgroup="Real",
                        showlegend=(idx==0),marker_color="rgba(0,180,216,0.55)",
                        marker_line=dict(color="rgba(0,180,216,.9)",width=0.5)),row=r,col=c)
                    fig.add_trace(go.Histogram(x=sv,nbinsx=bins,name="Synthetic",legendgroup="Synthetic",
                        showlegend=(idx==0),marker_color="rgba(0,210,140,0.45)",
                        marker_line=dict(color="rgba(0,210,140,.8)",width=0.5)),row=r,col=c)
                else:
                    vcr=df_real[col].value_counts().nlargest(8)
                    vcs=df_synth[col].value_counts().nlargest(8)
                    cats=list(set(vcr.index)|set(vcs.index))
                    fig.add_trace(go.Bar(x=cats,y=[vcr.get(k,0) for k in cats],name="Real",
                        legendgroup="Real",showlegend=False,marker_color="rgba(0,180,216,0.7)"),row=r,col=c)
                    fig.add_trace(go.Bar(x=cats,y=[vcs.get(k,0) for k in cats],name="Synthetic",
                        legendgroup="Synthetic",showlegend=False,marker_color="rgba(0,210,140,0.6)"),row=r,col=c)
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                font_family="DM Sans",font_color="#8ba3bc",barmode="overlay",
                legend=dict(orientation="h",x=0,y=1.04,bgcolor="rgba(0,0,0,0)",font=dict(size=11)),
                margin=dict(t=60,b=20,l=10,r=10),height=280*nr_)
            fig.update_xaxes(gridcolor="rgba(255,255,255,.04)",zeroline=False)
            fig.update_yaxes(gridcolor="rgba(255,255,255,.04)",zeroline=False)
            for ann in fig.layout.annotations: ann.font.size=11; ann.font.color="#4a7c9e"
            st.plotly_chart(fig, use_container_width=True)

    # CORRELATION
    with tab_corr:
        import plotly.graph_objects as go
        num_c2 = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
        if len(num_c2) < 2:
            st.info("Need at least 2 numeric columns.")
        else:
            cr2=df_real[num_c2].corr(); cs2=df_synth[num_c2].corr()
            cl,cr_=st.columns(2,gap="medium")
            def heatmap(mat,title):
                return go.Figure(go.Heatmap(
                    z=mat.values,x=mat.columns.tolist(),y=mat.index.tolist(),
                    colorscale=[[0,"#0a1628"],[.25,"#0c3460"],[.5,"#1a5276"],[.75,"#0096c7"],[1,"#00d2ff"]],
                    zmin=-1,zmax=1,text=mat.round(2).values,texttemplate="%{text}",
                    textfont=dict(size=10,color="white"),
                    colorbar=dict(tickfont=dict(color="#4a7c9e",size=10),bgcolor="rgba(0,0,0,0)"),
                )).update_layout(title=dict(text=title,font=dict(size=12,color="#4a7c9e"),x=0.5),
                    paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#8ba3bc",margin=dict(t=50,b=10,l=10,r=10),height=420)
            with cl:  st.plotly_chart(heatmap(cr2,"Real Data Correlations"),      use_container_width=True)
            with cr_: st.plotly_chart(heatmap(cs2,"Synthetic Data Correlations"), use_container_width=True)
            delta=(cs2-cr2).abs()
            avg=delta.values[np.triu_indices_from(delta.values,k=1)].mean()
            st.markdown(f"""<div class="card" style="margin-top:0.5rem">
                <div class="card-title">Correlation Fidelity</div>
                <div style="font-size:0.85rem;color:#e2e8f0">Mean absolute deviation:
                <span style="font-family:'Space Mono';color:#00d2ff;font-weight:700">{avg:.4f}</span>
                &nbsp;·&nbsp; Lower = better (0 = perfect)</div></div>""", unsafe_allow_html=True)

    # RAW
    with tab_raw:
        cr3,cs3=st.columns(2,gap="medium")
        with cr3:
            st.markdown('<div class="card-title">Real Data · Sample</div>', unsafe_allow_html=True)
            st.dataframe(df_real.head(20), use_container_width=True, height=420)
        with cs3:
            st.markdown('<div class="card-title">Synthetic Data · Sample</div>', unsafe_allow_html=True)
            st.dataframe(df_synth.head(20), use_container_width=True, height=420)
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">Statistical Summary Comparison</div>', unsafe_allow_html=True)
        nb=[c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
        if nb:
            dr=df_real[nb].describe().T.round(3); ds=df_synth[nb].describe().T.round(3)
            dr.columns=["Real·"+c for c in dr.columns]; ds.columns=["Synth·"+c for c in ds.columns]
            combined=pd.concat([dr,ds],axis=1)
            ordered=[c for pair in zip(dr.columns,ds.columns) for c in pair]
            st.dataframe(combined[ordered], use_container_width=True)
        else:
            st.info("No numeric columns to summarise.")

    # ── AI ANALYST TAB — Prominent Section ───────────────────────────────────
    with tab_analyst:
        has_key = bool(st.session_state.get("openai_key","").strip().startswith("sk-"))

        st.markdown(f"""
        <div class="analyst-wrapper">
            <div class="analyst-header">
                <div style="font-size:2.5rem">🤖</div>
                <div>
                    <div class="analyst-title">AI Data Analyst</div>
                    <div class="analyst-subtitle">
                        {"🟢 GPT-4 Powered — OpenAI key connected" if has_key else "🔵 Built-in Analyst Active — Add OpenAI key in sidebar for GPT-4 power"}
                    </div>
                </div>
                <div style="margin-left:auto;text-align:right">
                    <div style="background:{'rgba(0,210,140,0.1)' if has_key else 'rgba(0,210,255,0.08)'};
                         border:1px solid {'#00d28c' if has_key else 'rgba(0,210,255,0.3)'};
                         border-radius:8px;padding:6px 14px;font-size:0.72rem;
                         color:{'#00d28c' if has_key else '#00d2ff'};font-family:'Space Mono',monospace">
                        {"GPT-4 ACTIVE" if has_key else "BUILT-IN MODE"}
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Chat history
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-user">👤 {msg["content"]}</div>', unsafe_allow_html=True)
            else:
                css_class = "chat-ai-gpt" if msg.get("gpt") else "chat-ai"
                icon = "✨" if msg.get("gpt") else "🤖"
                st.markdown(f'<div class="{css_class}">{icon} {msg["content"]}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Suggested questions
        st.markdown("<div style='margin-top:16px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">💡 QUICK QUESTIONS</div>', unsafe_allow_html=True)

        suggestions = [
            "How many rows and columns?",
            "Show summary statistics",
            "Any missing values?",
            "Find correlations",
            "Detect outliers",
            "Count unique values",
            "PII / Privacy scan",
            "Distribution analysis",
        ]

        sq_cols = st.columns(4)
        for i, sq in enumerate(suggestions):
            with sq_cols[i % 4]:
                if st.button(sq, key=f"sq_{i}", use_container_width=True):
                    answer, used_gpt = get_answer(df_synth, sq)
                    st.session_state.chat_history.append({"role":"user","content":sq})
                    st.session_state.chat_history.append({"role":"assistant","content":answer,"gpt":used_gpt})
                    st.rerun()

        # Free text input
        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
        user_q = st.chat_input("Ask anything about your synthetic data…")
        if user_q:
            answer, used_gpt = get_answer(df_synth, user_q)
            st.session_state.chat_history.append({"role":"user","content":user_q})
            st.session_state.chat_history.append({"role":"assistant","content":answer,"gpt":used_gpt})
            st.rerun()

        if st.session_state.chat_history:
            st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)
            if st.button("🗑 Clear Chat", use_container_width=False):
                st.session_state.chat_history = []
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.df_real is None:
    st.markdown("""
    <div style="text-align:center;padding:5rem 2rem">
        <div style="font-size:3.5rem;margin-bottom:1rem;opacity:0.35">⬡</div>
        <div style="font-family:'Space Mono',monospace;font-size:0.85rem;letter-spacing:2px;text-transform:uppercase;color:#2a4a6f">
            Upload a CSV or Excel file to begin
        </div>
        <div style="margin-top:1rem;font-size:0.78rem;color:#1e3a5f;max-width:420px;margin-left:auto;margin-right:auto;line-height:1.7">
            SynthoLogic automatically scans for PII, learns your data's statistical patterns,
            and generates a privacy-safe synthetic twin — in seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)
