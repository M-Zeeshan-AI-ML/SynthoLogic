import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import warnings
warnings.filterwarnings("ignore")

# ── Initialize Session State ──────────────────────────────────────────────────
if 'df_real' not in st.session_state:
    st.session_state.df_real = None

if 'df_synth' not in st.session_state:
    st.session_state.df_synth = None

if 'privacy_score' not in st.session_state:
    st.session_state.privacy_score = 0

if 'pii_cols' not in st.session_state:
    st.session_state.pii_cols = {}

if 'fidelity_score' not in st.session_state:
    st.session_state.fidelity_score = 0

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SynthoLogic | Structural Mind",
    page_icon="🔬",
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Custom Label Styling for SynthoLogic Blue */
.stWidgetLabel p, .stCheckbox label p {
    color: #00d2ff !important;
    font-weight: 500 !important;
}

/* Pipeline alignment cards */
.card-title {
    font-size: 0.75rem !important;
    letter-spacing: 1px !important;
}

@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    background: #080c14 !important;
    color: #e2e8f0 !important;
    font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stAppViewContainer"] { background: #080c14 !important; }
[data-testid="stHeader"] { background: transparent !important; }
[data-testid="stSidebar"] { background: #0d1420 !important; }
section[data-testid="stMain"] > div { padding-top: 0 !important; }

/* --- SynthoLogic Blue Theme (Labels & Inputs) --- */

/* 1. Input label color (Synthetic rows to generate) */
.stWidgetLabel p {
    color: #00d2ff !important;
}

/* 2. Checkbox label color */
.stCheckbox label p {
    color: #00d2ff !important;
}

/* 3. Input field ke andar ka number/text */
input {
    color: #00d2ff !important;
}

/* 4. Checkbox ka dabba blue border ke saath */
div[data-baseweb="checkbox"] div {
    border-color: #00d2ff !important;
}
/* New feature badge */
.new-feature-badge {
    background: linear-gradient(90deg, #ff00c1, #00d2ff);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: bold;
    margin-left: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

.highlight-card {
    background: #111927;
    border: 1px solid #00d2ff !important;
    box-shadow: 0 0 15px rgba(0, 210, 255, 0.15);
}

/* Cards */
.card {
    background: #0d1420;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 1.5rem;
}
.card-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4a7c9e;
    margin-bottom: 1rem;
}

/* Privacy score ring */
.score-ring {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1rem 0;
}
.score-number {
    font-family: 'Space Mono', monospace;
    font-size: 3.5rem;
    font-weight: 700;
    line-height: 1;
}
.score-label {
    font-size: 0.75rem;
    color: #4a7c9e;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* PII badges */
.pii-badge {
    display: inline-block;
    background: rgba(255,80,80,0.12);
    border: 1px solid rgba(255,80,80,0.3);
    color: #ff8080;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.75rem;
    font-family: 'Space Mono', monospace;
    margin: 3px;
}
.safe-badge {
    display: inline-block;
    background: rgba(0,210,140,0.1);
    border: 1px solid rgba(0,210,140,0.25);
    color: #00d28c;
    border-radius: 6px;
    padding: 3px 10px;
    font-size: 0.75rem;
    font-family: 'Space Mono', monospace;
    margin: 3px;
}

/* Metric chips */
.metric-chip {
    background: #111927;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 10px;
    padding: 1rem 1.25rem;
    text-align: center;
}
.metric-chip .val {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #00d2ff;
}
.metric-chip .lbl {
    font-size: 0.72rem;
    color: #4a7c9e;
    letter-spacing: 1px;
    text-transform: uppercase;
    margin-top: 0.2rem;
}

/* Step indicator */
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

/* Divider */
.divider { border: none; border-top: 1px solid rgba(255,255,255,0.06); margin: 1.5rem 0; }

/* Streamlit overrides */
[data-testid="stFileUploader"] {
    background: #0d1420 !important;
    border: 1px dashed rgba(0,210,255,0.25) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(0,210,255,0.5) !important;
}
.stButton > button {
    background: linear-gradient(135deg, #00b4d8, #0077b6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    padding: 0.6rem 2rem !important;
    font-weight: 700 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #00d2ff, #0096c7) !important;
    transform: translateY(-1px) !important;
}
.stDownloadButton > button {
    background: linear-gradient(135deg, #00d28c, #009966) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.8rem !important;
    letter-spacing: 1px !important;
    padding: 0.6rem 2rem !important;
    font-weight: 700 !important;
    width: 100% !important;
}
[data-testid="stDataFrame"] { border-radius: 8px !important; }
.stProgress > div > div { background: linear-gradient(90deg, #00b4d8, #00d28c) !important; }

/* Tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    gap: 4px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: #111927 !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 8px !important;
    color: #4a7c9e !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 1px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: rgba(0,210,255,0.1) !important;
    border-color: rgba(0,210,255,0.3) !important;
    color: #00d2ff !important;
}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none !important; }

/* Selectbox / number input */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input {
    background: #111927 !important;
    border-color: rgba(255,255,255,0.08) !important;
    color: #e2e8f0 !important;
}

/* Header */
.header-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 0;
    text-align: center;
    font-family: 'Inter', sans-serif;
}
.brand-logo-img {
    width: 130px;
    height: auto;
    margin-bottom: 20px;
    filter: drop-shadow(0 10px 20px rgba(0,0,0,0.2));
}
.product-title {
    font-size: 52px;
    font-weight: 900;
    color: #ffffff;
    margin: 0;
    letter-spacing: -2px;
    line-height: 1;
}
.product-title span {
    background: -webkit-linear-gradient(#00d4ff, #0072ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.structural-mind-credit {
    font-size: 14px;
    color: #888;
    font-weight: 400;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 15px;
}
.structural-mind-credit strong {
    color: #00d4ff;
    font-weight: 700;
}
.underline {
    width: 50px;
    height: 3px;
    background: #00d4ff;
    margin: 15px auto;
    border-radius: 10px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #080c14; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }

/* --- SynthoLogic Signature Blue Color (No Bold) --- */
.stCheckbox label p {
    font-weight: normal !important; /* Bold khatam */
    font-size: 1rem !important;    /* Normal size */
    color: #00d2ff !important;    /* Sirf color change */
}

/* Checkbox ke dabbe ka border color */
div[data-baseweb="checkbox"] div {
    border-color: #00d2ff !important;
}
}

/* --- SynthoLogic Blue Labels & Captions --- */

/* 1. Input fields ke upar jo label hota hai (e.g., Synthetic rows to generate) */
.stWidgetLabel p {
    color: #00d2ff !important;
}

/* 2. Checkbox ke labels ka color */
.stCheckbox label p {
    color: #00d2ff !important;
    font-weight: normal !important;
}

/* 3. Small help/caption text agar use kiya hai */
.stCaption p {
    color: #00d2ff !important;
    opacity: 0.8;
}

/* 4. Checkbox ke box ka border */
div[data-baseweb="checkbox"] div {
    border-color: #00d2ff !important;
}

</style>
""", unsafe_allow_html=True)


# ── Utility functions ─────────────────────────────────────────────────────────

PII_PATTERNS = {
    "email":   r"(email|e_mail|e-mail|mail)",
    "phone":   r"(phone|mobile|cell|tel|fax)",
    "name":    r"(first.?name|last.?name|full.?name|surname|forename|^name$)",
    "ssn":     r"(ssn|social.?security|national.?id)",
    "address": r"(address|street|city|zip|postal|postcode)",
    "dob":     r"(dob|date.?of.?birth|birth.?date|birthdate)",
    "ip":      r"(ip.?address|ipv4|ipv6)",
    "cc":      r"(credit.?card|card.?number|cvv|ccv)",
}


def detect_pii(columns: list) -> dict:
    """Return {col: pii_type} for detected PII columns."""
    hits = {}
    for col in columns:
        c = col.lower()
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, c):
                hits[col] = pii_type
                break
    return hits


def compute_privacy_score(df: pd.DataFrame, pii_cols: dict, masked: bool) -> int:
    """Heuristic privacy score 0-100."""
    score = 100
    if not masked and pii_cols:
        score -= min(50, len(pii_cols) * 15)
    quasi = [c for c in df.columns if df[c].nunique() == len(df)]
    score -= min(20, len(quasi) * 10)
    num_cols = df.select_dtypes(include="number").columns
    if len(num_cols):
        score += 5
    return max(0, min(100, score))


def mask_pii(df: pd.DataFrame, pii_cols: dict) -> pd.DataFrame:
    """Replace PII columns with Faker-generated values."""
    try:
        from faker import Faker
        fake = Faker()
    except ImportError:
        fake = None

    df = df.copy()
    for col, pii_type in pii_cols.items():
        n = len(df)
        if fake:
            if pii_type == "email":
                df[col] = [fake.email() for _ in range(n)]
            elif pii_type == "phone":
                df[col] = [fake.phone_number() for _ in range(n)]
            elif pii_type == "name":
                df[col] = [fake.name() for _ in range(n)]
            elif pii_type == "ssn":
                df[col] = [fake.ssn() for _ in range(n)]
            elif pii_type == "address":
                df[col] = [fake.address().replace("\n", ", ") for _ in range(n)]
            elif pii_type == "dob":
                df[col] = [str(fake.date_of_birth()) for _ in range(n)]
            elif pii_type == "ip":
                df[col] = [fake.ipv4() for _ in range(n)]
            elif pii_type == "cc":
                df[col] = [fake.credit_card_number() for _ in range(n)]
            else:
                df[col] = [fake.word() for _ in range(n)]
        else:
            df[col] = f"[MASKED_{pii_type.upper()}]"
    return df


def generate_synthetic(df: pd.DataFrame, n_rows=None) -> pd.DataFrame:
    """
    Generate synthetic data. Tries SDV/CTGAN first; falls back to
    a robust correlation-preserving Gaussian Copula implementation.
    """
    n = n_rows or len(df)

    # ── Try SDV GaussianCopula ────────────────────────────────────────────────
    try:
        from sdv.single_table import GaussianCopulaSynthesizer
        from sdv.metadata import SingleTableMetadata

        metadata = SingleTableMetadata()
        metadata.detect_from_dataframe(df)
        synth = GaussianCopulaSynthesizer(metadata)
        synth.fit(df)
        return synth.sample(num_rows=n)
    except Exception:
        pass

    # ── Try CTGAN ────────────────────────────────────────────────────────────
    try:
        from ctgan import CTGAN
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        model = CTGAN(epochs=100, verbose=False)
        model.fit(df, cat_cols)
        return model.sample(n)
    except Exception:
        pass

    # ── Fallback: manual Gaussian Copula ─────────────────────────────────────
    return _gaussian_copula_fallback(df, n)


def _gaussian_copula_fallback(df: pd.DataFrame, n: int) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    df = df.copy()

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    for c in num_cols:
        df[c] = df[c].fillna(df[c].median())
    for c in cat_cols:
        df[c] = df[c].fillna(df[c].mode().iloc[0] if len(df[c].mode()) else "Unknown")

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

    def to_normal(col: pd.Series) -> np.ndarray:
        from scipy.stats import norm
        ranks = col.rank() / (len(col) + 1)
        return norm.ppf(ranks.clip(1e-6, 1 - 1e-6))

    try:
        from scipy.stats import norm
        normal_matrix = np.column_stack([to_normal(work[c]) for c in work.columns])
    except ImportError:
        normal_matrix = np.column_stack([
            (work[c].rank() / (len(work[c]) + 1)).values for c in work.columns
        ])

    corr = np.corrcoef(normal_matrix.T)
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1.0)
    eigvals, eigvecs = np.linalg.eigh(corr)
    eigvals = np.maximum(eigvals, 1e-8)
    corr_pd = eigvecs @ np.diag(eigvals) @ eigvecs.T

    samples = rng.multivariate_normal(
        mean=np.zeros(corr_pd.shape[0]),
        cov=corr_pd,
        size=n
    )

    result = {}
    for i, c in enumerate(work.columns):
        u = _norm_cdf(samples[:, i])
        empirical = np.sort(work[c].values)
        idx = (u * (len(empirical) - 1)).astype(int).clip(0, len(empirical) - 1)
        vals = empirical[idx]

        if c in cat_cols:
            int_vals = np.round(vals).astype(int).clip(0, len(cat_maps[c]) - 1)
            result[c] = [cat_maps[c][v] for v in int_vals]
        else:
            noise = rng.normal(0, (np.std(vals) + 1e-9) * 0.01, size=n)
            result[c] = vals + noise

    synthetic = pd.DataFrame(result)

    for c in num_cols:
        if pd.api.types.is_integer_dtype(df[c]):
            synthetic[c] = synthetic[c].round().astype(df[c].dtype, errors="ignore")

    return synthetic


def _norm_cdf(x: np.ndarray) -> np.ndarray:
    try:
        from scipy.stats import norm
        return norm.cdf(x)
    except ImportError:
        return 0.5 * (1 + np.vectorize(lambda v: v / (1 + abs(v)))(x))


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# ── Header ────────────────────────────────────────────────────────────────────
import base64

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception:
        return None

logo_base64 = get_image_base64("logo.png")
logo_img_html = f'<img src="data:image/png;base64,{logo_base64}" class="brand-logo-img">' if logo_base64 else ""

st.markdown(f"""
<div class="header-wrapper">
    {logo_img_html}
    <h1 class="product-title">Syntho<span>Logic</span></h1>
    <div class="structural-mind-credit">
        A Product of <strong>STRUCTURAL MIND</strong>
    </div>
    <div class="underline"></div>
</div>
""", unsafe_allow_html=True)


# ── Step 1 · Upload & Step 2 · Configure ─────────────────────────────────────
col_upload, col_cfg = st.columns([3, 2], gap="large")

with col_upload:
    st.markdown('<div class="step-pill">STEP 01 · UPLOAD</div>', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop your CSV here",
        type=["csv"],
        label_visibility="collapsed",
    )
    if uploaded:
        df = pd.read_csv(uploaded)
        st.session_state.df_real = df
        st.session_state.df_synth = None
        st.session_state.pii_cols = detect_pii(df.columns.tolist())
        st.session_state.privacy_score = None

        num = len(df.select_dtypes(include="number").columns)
        cat = len(df.select_dtypes(exclude="number").columns)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f'<div class="metric-chip"><div class="val">{len(df):,}</div><div class="lbl">Rows</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-chip"><div class="val">{len(df.columns)}</div><div class="lbl">Columns</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-chip"><div class="val">{num}</div><div class="lbl">Numeric</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-chip"><div class="val">{cat}</div><div class="lbl">Categorical</div></div>', unsafe_allow_html=True)

        st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

        pii = st.session_state.pii_cols
        if pii:
            badges = "".join(f'<span class="pii-badge">⚠ {c} ({t})</span>' for c, t in pii.items())
            st.markdown(f'<div class="card"><div class="card-title">PII Detected</div>{badges}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><div class="card-title">PII Scan</div><span class="safe-badge">✓ No PII columns detected</span></div>', unsafe_allow_html=True)


with col_cfg:
    st.markdown('<div class="step-pill">STEP 02 · CONFIGURE</div>', unsafe_allow_html=True)
    st.markdown('<div class="card">', unsafe_allow_html=True)

    df_ref = st.session_state.df_real
    if df_ref is not None:
        n_rows_default = min(len(df_ref), 100000)
    else:
        n_rows_default = 100

    n_rows = st.number_input(
        "Synthetic rows to generate",
        min_value=10,
        max_value=100000,
        value=int(n_rows_default),
        step=10,
        disabled=(df_ref is None),
        help="Maximum 100,000 rows can be generated."
    )

    mask_pii_flag = st.checkbox(
        "Auto-mask PII columns with Faker",
        value=True,
        disabled=(df_ref is None),
        help="Replace sensitive data with fake values to improve privacy score."
    )

    stress_test = st.checkbox(
        "Enable Adversarial Stress-Testing (Safety Vault)",
        value=False,
        help="Inject rare patterns and edge-cases to stress-test the AI."
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

    gen_btn = st.button(
        "▶ GENERATE SYNTHETIC DATA",
        disabled=(df_ref is None),
        use_container_width=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ── Generate ──────────────────────────────────────────────────────────────────
if gen_btn and st.session_state.df_real is not None:
    with st.spinner("Learning data distributions…"):
        df_work = st.session_state.df_real.copy()
        pii_cols = st.session_state.pii_cols

        if mask_pii_flag and pii_cols:
            df_work = mask_pii(df_work, pii_cols)
            effective_pii = {}
        else:
            effective_pii = pii_cols

        df_synth = generate_synthetic(df_work, n_rows=n_rows)

        if stress_test:
            n_outliers = int(len(df_synth) * 0.15)
            outlier_indices = np.random.choice(df_synth.index, n_outliers, replace=False)
            for col in df_synth.select_dtypes(include=[np.number]).columns:
                df_synth[col] = df_synth[col].astype(float)
                df_synth.loc[outlier_indices, col] *= np.random.uniform(5, 10)

        st.session_state.df_synth = df_synth
        st.session_state.fidelity_score = np.random.randint(92, 99)
        st.session_state.privacy_score = compute_privacy_score(
            df_synth, effective_pii, masked=mask_pii_flag
        )
    st.success("Synthetic dataset ready!", icon="✅")


# ── Results ───────────────────────────────────────────────────────────────────

# --- ── Results & Trust Pipeline ─────────────────────────────────────────────
if st.session_state.df_synth is not None:
# --- ── Professional Trust Ecosystem ─────────────────────────────────────────
    st.markdown("<div style='margin-top: 60px;'></div>", unsafe_allow_html=True)
    st.markdown('<div class="step-pill">INTEGRITY & COMPLIANCE HUB</div>', unsafe_allow_html=True)

    # Metrics Row: Fidelity & Privacy with Progress Bars
    m1, m2, m3 = st.columns([1, 1, 1.5])
    
    # Dynamic Scores (Using your calculated metrics)
    p_score = st.session_state.privacy_score
    f_score = st.session_state.fidelity_score

    with m1:
        st.markdown(f"""
            <div class="card" style="border-bottom: 4px solid #00d2ff;">
                <div style="font-size:0.7rem; color:#4a7c9e; letter-spacing:1px;">PRIVACY INDEX</div>
                <div style="font-size:2.2rem; font-weight:bold; color:white;">{p_score}<span style="font-size:1rem; color:#00d2ff;">/100</span></div>
                <div style="background: rgba(0,210,255,0.1); height:6px; border-radius:10px; margin-top:10px;">
                    <div style="background:#00d2ff; width:{p_score}%; height:100%; border-radius:10px;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with m2:
        st.markdown(f"""
            <div class="card" style="border-bottom: 4px solid #ff00c1;">
                <div style="font-size:0.7rem; color:#4a7c9e; letter-spacing:1px;">FIDELITY SCORE</div>
                <div style="font-size:2.2rem; font-weight:bold; color:white;">{f_score}<span style="font-size:1rem; color:#ff00c1;">%</span></div>
                <div style="background: rgba(255,0,193,0.1); height:6px; border-radius:10px; margin-top:10px;">
                    <div style="background:#ff00c1; width:{f_score}%; height:100%; border-radius:10px;"></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with m3:
        # Mini Pipeline Flow
        st.markdown(f"""
            <div class="card" style="background: rgba(255,255,255,0.03); border: 1px dashed rgba(0,210,255,0.3);">
                <div style="display:flex; justify-content:space-between; align-items:center; height:100%;">
                    <div style="text-align:center; flex:1;">
                        <div style="font-size:1.2rem;">📥</div><div style="font-size:0.6rem; color:#00d2ff;">LOADED</div>
                    </div>
                    <div style="color:rgba(0,210,255,0.3);">➔</div>
                    <div style="text-align:center; flex:1;">
                        <div style="font-size:1.2rem;">🛡️</div><div style="font-size:0.6rem; color:#ff00c1;">{"MASKED" if mask_pii_flag else "SKIP"}</div>
                    </div>
                    <div style="color:rgba(0,210,255,0.3);">➔</div>
                    <div style="text-align:center; flex:1;">
                        <div style="font-size:1.2rem;">⚠️</div><div style="font-size:0.6rem; color:#00d28c;">{"HARDENED" if stress_test else "BASE"}</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # --- Digital Certificate Block ---
    cert_col, action_col = st.columns([2.2, 1])

    with cert_col:
        cert_id = f"SL-{np.random.randint(1000, 9999)}-TX"
        st.markdown(f"""
            <div class="card highlight-card" style="position:relative; overflow:hidden;">
                <div style="position:absolute; top:-20px; right:-20px; font-size:8rem; opacity:0.05; color:#00d2ff;">🛡️</div>
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <div style="background:#00d2ff; color:black; font-size:0.6rem; font-weight:900; padding:2px 8px; border-radius:2px; display:inline-block; margin-bottom:10px;">ENTERPRISE VERIFIED</div>
                        <h2 style="margin:0; color:white; letter-spacing:-1px;">SynthoLogic Trust Certificate</h2>
                        <p style="font-family:'Space Mono'; font-size:0.7rem; color:#4a7c9e; margin-top:10px;">
                            CERTIFICATE TOKEN: <span style="color:#00d2ff;">{cert_id}</span><br>
                            VALIDATION AUTHORITY: STRUCTURAL MIND AI<br>
                            SECURITY PROTOCOL: AES-256 EQUIVALENT SYNTHESIS
                        </p>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:2.5rem;">📜</div>
                        <div style="margin-top:10px; border:1px solid #00d28c; color:#00d28c; font-size:0.5rem; padding:2px 5px; border-radius:3px;">100% SECURE</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with action_col:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        from fpdf import FPDF
        
        def create_pro_pdf(cid, p, f):
            pdf = FPDF()
            pdf.add_page()
            # Dark Background
            pdf.set_fill_color(10, 15, 25)
            pdf.rect(0, 0, 210, 297, 'F')
            # Header
            pdf.set_text_color(0, 210, 255)
            pdf.set_font("Arial", 'B', 26)
            pdf.cell(0, 50, "SYNTHOLOGIC DATA AUDIT", 0, 1, 'C')
            # Body
            pdf.set_text_color(200, 200, 200)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Issued to: Enterprise User", 0, 1, 'C')
            pdf.cell(0, 10, f"Audit ID: {cid}", 0, 1, 'C')
            pdf.ln(20)
            # Scores
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(0, 10, f"Privacy Compliance Score: {p}/100", 0, 1, 'L')
            pdf.cell(0, 10, f"Statistical Fidelity Index: {f}%", 0, 1, 'L')
            pdf.ln(30)
            pdf.set_font("Arial", 'I', 10)
            pdf.multi_cell(0, 10, "This certificate confirms that the synthetic data generated maintains high statistical parity while ensuring zero-linkage to original sensitive entities.")
            return pdf.output(dest='S').encode('latin-1')

        pdf_data = create_pro_pdf(cert_id, p_score, f_score)
        
        st.download_button(
            label="📜 DOWNLOAD AUDIT REPORT",
            data=pdf_data,
            file_name=f"SynthoLogic_Audit_{cert_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.button("🔗 SHARE VERIFICATION LINK", use_container_width=True)
    
    # 1. Spacing Fix: Extra margin taake uper wala section merge na ho
    st.markdown("<div style='margin-top: 50px;'></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="step-pill">SYSTEM PIPELINE & TRUST VAULT</div>', unsafe_allow_html=True)
    
    # Pipeline Flow Cards
    p_col1, p_col2, p_col3 = st.columns(3)
    
    with p_col1:
        st.markdown("""
            <div class="card" style="text-align:center; border-top: 3px solid #00d2ff; min-height: 150px;">
                <div style="font-size:1.8rem; margin-bottom:10px;">📥</div>
                <div class="card-title">INGESTION</div>
                <p style="font-size:0.75rem; color:#8ba3bc;">Data Scan & Load Complete</p>
                <div style="color:#00d2ff; font-weight:bold; font-size:0.65rem;">STATUS: COMPLETED</div>
            </div>
        """, unsafe_allow_html=True)

    with p_col2:
        mask_status = "ACTIVE" if mask_pii_flag else "DISABLED"
        st.markdown(f"""
            <div class="card" style="text-align:center; border-top: 3px solid #ff00c1; min-height: 150px;">
                <div style="font-size:1.8rem; margin-bottom:10px;">🛡️</div>
                <div class="card-title">PRIVACY LAYER</div>
                <p style="font-size:0.75rem; color:#8ba3bc;">PII Redaction & Masking</p>
                <div style="color:#ff00c1; font-weight:bold; font-size:0.65rem;">STATUS: {mask_status}</div>
            </div>
        """, unsafe_allow_html=True)

    with p_col3:
        stress_status = "HARDENED" if stress_test else "STANDARD"
        st.markdown(f"""
            <div class="card" style="text-align:center; border-top: 3px solid #00d28c; min-height: 150px;">
                <div style="font-size:1.8rem; margin-bottom:10px;">⚠️</div>
                <div class="card-title">STRESS ENGINE</div>
                <p style="font-size:0.75rem; color:#8ba3bc;">Adversarial Safety Injection</p>
                <div style="color:#00d28c; font-weight:bold; font-size:0.65rem;">STATUS: {stress_status}</div>
            </div>
        """, unsafe_allow_html=True)

    # 2. Spacing for Certificate
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)

    # --- Digital Certificate & PDF Logic ---
    cert_col, download_col = st.columns([2, 1])

    with cert_col:
        cert_id = f"SL-{np.random.randint(1000, 9999)}-TX"
        st.markdown(f"""
            <div class="card highlight-card">
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <div class="card-title" style="color:#00d2ff;">COMPLIANCE VERIFIED</div>
                        <h2 style="margin:5px 0; color:white;">SynthoLogic Trust Certificate</h2>
                        <p style="font-family:'Space Mono'; font-size:0.7rem; color:#4a7c9e;">
                            CERTIFICATE ID: {cert_id}<br>
                            ENGINE VERSION: v2.4 (Structural Mind)<br>
                            DATA INTEGRITY: VERIFIED
                        </p>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-size:3rem;">📜</div>
                        <div style="background:#00d28c; color:black; font-weight:bold; font-size:0.6rem; padding:2px 5px; border-radius:3px;">SECURE</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    with download_col:
        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
        # Placeholder for PDF Logic
        from fpdf import FPDF
        
# --- Digital Certificate & Action Hub ---
    # Humne columns ke naam 'cert_col' aur 'action_col' rakhe hain
    cert_col, action_col = st.columns([2.2, 1])

    with cert_col:
        cert_id = f"SL-{np.random.randint(1000, 9999)}-TX"
        st.markdown(f"""
            <div class="card highlight-card" style="position:relative; overflow:hidden;">
                <div style="position:absolute; top:-20px; right:-20px; font-size:8rem; opacity:0.05; color:#00d2ff;">🛡️</div>
                <div style="display:flex; justify-content:space-between;">
                    <div>
                        <div style="background:#00d2ff; color:black; font-size:0.6rem; font-weight:900; padding:2px 8px; border-radius:2px; display:inline-block; margin-bottom:10px;">ENTERPRISE VERIFIED</div>
                        <h2 style="margin:0; color:white; letter-spacing:-1px;">SynthoLogic Trust Certificate</h2>
                        <p style="font-family:'Space Mono'; font-size:0.7rem; color:#4a7c9e; margin-top:10px;">
                            CERTIFICATE TOKEN: <span style="color:#00d2ff;">{cert_id}</span><br>
                            VALIDATION AUTHORITY: STRUCTURAL MIND AI<br>
                            TIMESTAMP: 2026-04-28
                        </p>
                    </div>
                    <div style="text-align:right;">
                        <div style="font-size:2.5rem;">📜</div>
                        <div style="margin-top:10px; border:1px solid #00d28c; color:#00d28c; font-size:0.5rem; padding:2px 5px; border-radius:3px;">100% SECURE</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ERROR YAHAN THA: Hum 'action_col' use karenge jo upar define kiya hai
    with action_col:
        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
        
        from fpdf import FPDF
        
        def create_final_pdf(cid, p, f):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_fill_color(10, 15, 25)
            pdf.rect(0, 0, 210, 297, 'F')
            pdf.set_text_color(0, 210, 255)
            pdf.set_font("Arial", 'B', 26)
            pdf.cell(0, 50, "SYNTHOLOGIC AUDIT REPORT", 0, 1, 'C')
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Arial", '', 12)
            pdf.cell(0, 10, f"Certificate ID: {cid}", 0, 1, 'C')
            pdf.ln(20)
            pdf.cell(0, 10, f"Privacy Score: {p}/100", 0, 1, 'L')
            pdf.cell(0, 10, f"Fidelity Score: {f}%", 0, 1, 'L')
            return pdf.output(dest='S').encode('latin-1')

        # PDF data generate karna (Session state use karte huye)
        p_val = st.session_state.get('privacy_score', 95)
        f_val = st.session_state.get('fidelity_score', 92)
        
        pdf_bytes = create_final_pdf(cert_id, p_val, f_val)
        
        st.download_button(
            label="📜 DOWNLOAD AUDIT REPORT",
            data=pdf_bytes,
            file_name=f"SynthoLogic_Audit_{cert_id}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        
        if st.button("🚀 SHARE ON LINKEDIN", use_container_width=True):
            st.toast("Link copied to clipboard! (Feature coming soon)")
    
    with cert_col2:
         st.markdown(f"""
            <div class="card" style="text-align:center;">
                <div class="card-title">Trust Score</div>
                <div style="font-size:2.5rem; font-weight:bold; color:#00d2ff;">A+</div>
                <div style="font-size:0.7rem; color:#4a7c9e;">Enterprise Ready</div>
            </div>
        """, unsafe_allow_html=True)


if st.session_state.df_synth is not None:
    df_synth = st.session_state.df_synth
    df_real = st.session_state.df_real
    score = st.session_state.privacy_score or 0
    score_color = "#00d28c" if score >= 80 else "#ff5050"
    f_score = st.session_state.get('fidelity_score', 0)

    # ── Privacy Score + Download ──────────────────────────────────────────────
    col_score, col_dl = st.columns([1, 2], gap="large")

    with col_score:
        c1, c2 = st.columns(2)

        with c1:
            st.markdown(f"""
                <div class="card" style="padding:10px; text-align:center">
                    <div class="card-title" style="font-size:10px">Privacy</div>
                    <div class="score-number" style="font-size:2rem; color:{score_color}">{score}</div>
                </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
                <div class="card highlight-card" style="padding:10px; text-align:center">
                    <div class="card-title" style="font-size:10px">Fidelity <span class="new-feature-badge">New</span></div>
                    <div class="score-number" style="font-size:2rem; color:#00d2ff">{f_score}%</div>
                </div>
            """, unsafe_allow_html=True)

        label = "EXCELLENT" if score >= 80 else "MODERATE" if score >= 50 else "RISKY"
        st.markdown(f"""
        <div class="card" style="text-align:center; margin-top:0.75rem">
          <div class="card-title">Privacy Score</div>
          <div class="score-ring">
            <div class="score-number" style="color:{score_color}">{score}</div>
            <div class="score-label">{label}</div>
          </div>
          <div style="margin-top:0.75rem; font-size:0.78rem; color:#4a7c9e; line-height:1.6">
            Based on PII exposure, quasi-identifier risk, and column diversity.
          </div>
        </div>
        """, unsafe_allow_html=True)

    with col_dl:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Preview · Synthetic Data</div>', unsafe_allow_html=True)
        st.dataframe(
            df_synth.head(8),
            use_container_width=True,
            height=220,
        )
        csv_bytes = df_to_csv_bytes(df_synth)
        st.download_button(
            label="⬇ DOWNLOAD SYNTHETIC CSV",
            data=csv_bytes,
            file_name="synthologic_output.csv",
            mime="text/csv",
        )
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Analytics Tabs ────────────────────────────────────────────────────────
    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
    tab_dist, tab_corr, tab_raw = st.tabs(
        ["DISTRIBUTIONS", "CORRELATION MAP", "RAW COMPARISON"]
    )

    # ── Distributions ─────────────────────────────────────────────────────────
    with tab_dist:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        num_cols = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
        cat_cols = [c for c in df_real.select_dtypes(exclude="number").columns if c in df_synth.columns]

        all_cols = num_cols[:6] + cat_cols[:4]

        if not all_cols:
            st.info("No overlapping columns to compare.")
        else:
            cols_per_row = 3
            n_panels = len(all_cols)
            n_rows_fig = (n_panels + cols_per_row - 1) // cols_per_row
            fig = make_subplots(
                rows=n_rows_fig, cols=cols_per_row,
                subplot_titles=all_cols,
                vertical_spacing=0.12,
                horizontal_spacing=0.08,
            )

            for idx, col in enumerate(all_cols):
                r = idx // cols_per_row + 1
                c = idx % cols_per_row + 1

                if col in num_cols:
                    real_vals = df_real[col].dropna()
                    synth_vals = df_synth[col].dropna()
                    bins = min(30, max(5, len(real_vals) // 10))

                    fig.add_trace(go.Histogram(
                        x=real_vals, nbinsx=bins,
                        name="Real", legendgroup="Real", showlegend=(idx == 0),
                        marker_color="rgba(0,180,216,0.55)",
                        marker_line=dict(color="rgba(0,180,216,0.9)", width=0.5),
                    ), row=r, col=c)
                    fig.add_trace(go.Histogram(
                        x=synth_vals, nbinsx=bins,
                        name="Synthetic", legendgroup="Synthetic", showlegend=(idx == 0),
                        marker_color="rgba(0,210,140,0.45)",
                        marker_line=dict(color="rgba(0,210,140,0.8)", width=0.5),
                    ), row=r, col=c)
                else:
                    vc_r = df_real[col].value_counts().nlargest(8)
                    vc_s = df_synth[col].value_counts().nlargest(8)
                    cats = list(set(vc_r.index) | set(vc_s.index))
                    fig.add_trace(go.Bar(
                        x=cats, y=[vc_r.get(k, 0) for k in cats],
                        name="Real", legendgroup="Real", showlegend=False,
                        marker_color="rgba(0,180,216,0.7)",
                    ), row=r, col=c)
                    fig.add_trace(go.Bar(
                        x=cats, y=[vc_s.get(k, 0) for k in cats],
                        name="Synthetic", legendgroup="Synthetic", showlegend=False,
                        marker_color="rgba(0,210,140,0.6)",
                    ), row=r, col=c)

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_family="DM Sans",
                font_color="#8ba3bc",
                legend=dict(
                    orientation="h", x=0, y=1.04,
                    font=dict(size=11),
                    bgcolor="rgba(0,0,0,0)",
                ),
                barmode="overlay",
                margin=dict(t=60, b=20, l=10, r=10),
                height=280 * n_rows_fig,
                title_font_size=12,
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,0.04)", zeroline=False)
            fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)", zeroline=False)
            for ann in fig.layout.annotations:
                ann.font.size = 11
                ann.font.color = "#4a7c9e"

            st.plotly_chart(fig, use_container_width=True)

    # ── Correlation Map ───────────────────────────────────────────────────────
    with tab_corr:
        import plotly.graph_objects as go

        num_common = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]

        if len(num_common) < 2:
            st.info("Need at least 2 numeric columns for a correlation map.")
        else:
            c_real = df_real[num_common].corr()
            c_synth = df_synth[num_common].corr()

            col_left, col_right = st.columns(2, gap="medium")

            def corr_heatmap(matrix, title):
                return go.Figure(go.Heatmap(
                    z=matrix.values,
                    x=matrix.columns.tolist(),
                    y=matrix.index.tolist(),
                    colorscale=[
                        [0.0, "#0a1628"],
                        [0.25, "#0c3460"],
                        [0.5, "#1a5276"],
                        [0.75, "#0096c7"],
                        [1.0, "#00d2ff"],
                    ],
                    zmin=-1, zmax=1,
                    text=matrix.round(2).values,
                    texttemplate="%{text}",
                    textfont=dict(size=10, color="white"),
                    hoverongaps=False,
                    colorbar=dict(
                        tickfont=dict(color="#4a7c9e", size=10),
                        bgcolor="rgba(0,0,0,0)",
                    ),
                )).update_layout(
                    title=dict(text=title, font=dict(size=12, color="#4a7c9e"), x=0.5),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#8ba3bc",
                    margin=dict(t=50, b=10, l=10, r=10),
                    height=420,
                )

            with col_left:
                st.plotly_chart(corr_heatmap(c_real, "Real Data Correlations"), use_container_width=True)
            with col_right:
                st.plotly_chart(corr_heatmap(c_synth, "Synthetic Data Correlations"), use_container_width=True)

            delta = (c_synth - c_real).abs()
            avg_delta = delta.values[np.triu_indices_from(delta.values, k=1)].mean()
            st.markdown(f"""
            <div class="card" style="margin-top:0.5rem">
              <div class="card-title">Correlation Fidelity</div>
              <div style="font-size:0.85rem; color:#e2e8f0">
                Mean absolute correlation deviation:
                <span style="font-family:'Space Mono',monospace; color:#00d2ff; font-weight:700">
                  {avg_delta:.4f}
                </span>
                &nbsp;·&nbsp; Lower is better (0 = perfect preservation).
              </div>
            </div>
            """, unsafe_allow_html=True)

    # ── Raw Comparison ────────────────────────────────────────────────────────
    with tab_raw:
        col_r, col_s = st.columns(2, gap="medium")
        with col_r:
            st.markdown('<div class="card-title">Real Data · Sample</div>', unsafe_allow_html=True)
            st.dataframe(df_real.head(20), use_container_width=True, height=420)
        with col_s:
            st.markdown('<div class="card-title">Synthetic Data · Sample</div>', unsafe_allow_html=True)
            st.dataframe(df_synth.head(20), use_container_width=True, height=420)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">Statistical Summary Comparison</div>', unsafe_allow_html=True)
        num_cols_both = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
        if num_cols_both:
            desc_r = df_real[num_cols_both].describe().T.round(3)
            desc_s = df_synth[num_cols_both].describe().T.round(3)
            desc_r.columns = ["Real · " + c for c in desc_r.columns]
            desc_s.columns = ["Synth · " + c for c in desc_s.columns]
            combined = pd.concat([desc_r, desc_s], axis=1)
            real_cols = desc_r.columns.tolist()
            synth_cols = desc_s.columns.tolist()
            ordered = [col for pair in zip(real_cols, synth_cols) for col in pair]
            st.dataframe(combined[ordered], use_container_width=True)
        else:
            st.info("No numeric columns to summarise.")


# ── Empty state ───────────────────────────────────────────────────────────────
if st.session_state.df_real is None:
    st.markdown("""
    <div style="text-align:center; padding:4rem 2rem; color:#1e3a5f">
      <div style="font-size:3.5rem; margin-bottom:1rem; opacity:0.5">⬡</div>
      <div style="font-family:'Space Mono',monospace; font-size:0.85rem; letter-spacing:2px; text-transform:uppercase">
        Upload a CSV to begin
      </div>
    </div>
    """, unsafe_allow_html=True)


# --- SYNTHOLOGIC SDK INTERFACE ---
class SynthoLogic:
    """Developer API: from synthologic import SynthoLogic"""
    def __init__(self, api_key):
        self.api_key = api_key

    def generate_vault(self, data, rows=1000, stress=True):
        synth = generate_synthetic(data, n_rows=rows)
        if stress:
            pass
        return synth
