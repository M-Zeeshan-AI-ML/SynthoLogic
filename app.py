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

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SynthoLogic | Structural Mind",
    page_icon="favicon.png" ,
    layout="wide"
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

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

/* Hero header */
.hero {
    background: linear-gradient(135deg, #080c14 0%, #0d1a2e 50%, #080c14 100%);
    border-bottom: 1px solid rgba(0,210,255,0.12);
    padding: 2.5rem 3rem 2rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -60px; right: -60px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(0,210,255,0.07) 0%, transparent 70%);
    pointer-events: none;
}
.hero-logo {
    font-family: 'Space Mono', monospace;
    font-size: 1.85rem;
    font-weight: 700;
    color: #00d2ff;
    letter-spacing: -0.5px;
}
.hero-logo span { color: #e2e8f0; }
.hero-tagline {
    font-size: 0.8rem;
    color: #4a7c9e;
    font-family: 'Space Mono', monospace;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 0.25rem;
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

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #080c14; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Utility functions ─────────────────────────────────────────────────────────

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


def detect_pii(columns: list[str]) -> dict[str, str]:
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
    # Penalise if any column could act as quasi-identifier
    quasi = [c for c in df.columns if df[c].nunique() == len(df)]
    score -= min(20, len(quasi) * 10)
    # Reward high cardinality variance (harder to re-identify)
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


def generate_synthetic(df: pd.DataFrame, n_rows: int | None = None) -> pd.DataFrame:
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
    """
    Correlation-preserving synthetic generator:
    1. Encode categoricals ordinally.
    2. Transform marginals via rank-based normal scores.
    3. Sample from multivariate normal using the correlation matrix.
    4. Back-transform each column to its empirical marginal.
    5. Restore categoricals by rounding to nearest valid category.
    """
    rng = np.random.default_rng(42)
    df = df.copy()

    num_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = df.select_dtypes(exclude="number").columns.tolist()

    # Fill missing values
    for c in num_cols:
        df[c] = df[c].fillna(df[c].median())
    for c in cat_cols:
        df[c] = df[c].fillna(df[c].mode().iloc[0] if len(df[c].mode()) else "Unknown")

    work = pd.DataFrame(index=df.index)

    # Encode categoricals as integers
    cat_maps = {}
    for c in cat_cols:
        cats = df[c].astype("category")
        cat_maps[c] = dict(enumerate(cats.cat.categories))
        work[c] = cats.cat.codes.astype(float)

    for c in num_cols:
        work[c] = df[c].astype(float)

    if work.shape[1] == 0:
        return df.sample(n=n, replace=True).reset_index(drop=True)

    # Rank-based normal scores (van der Waerden transformation)
    def to_normal(col: pd.Series) -> np.ndarray:
        from scipy.stats import norm
        ranks = col.rank() / (len(col) + 1)
        return norm.ppf(ranks.clip(1e-6, 1 - 1e-6))

    try:
        from scipy.stats import norm
        normal_matrix = np.column_stack([to_normal(work[c]) for c in work.columns])
    except ImportError:
        # Simpler fallback without scipy
        normal_matrix = np.column_stack([
            (work[c].rank() / (len(work[c]) + 1)).values for c in work.columns
        ])

    # Correlation matrix with regularisation
    corr = np.corrcoef(normal_matrix.T)
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1.0)
    # Nearest positive-definite
    eigvals, eigvecs = np.linalg.eigh(corr)
    eigvals = np.maximum(eigvals, 1e-8)
    corr_pd = eigvecs @ np.diag(eigvals) @ eigvecs.T

    # Sample
    samples = rng.multivariate_normal(
        mean=np.zeros(corr_pd.shape[0]),
        cov=corr_pd,
        size=n
    )

    # Back-transform: for each column, use the empirical quantile function
    result = {}
    for i, c in enumerate(work.columns):
        u = _norm_cdf(samples[:, i])          # probabilities ∈ (0,1)
        empirical = np.sort(work[c].values)
        idx = (u * (len(empirical) - 1)).astype(int).clip(0, len(empirical) - 1)
        vals = empirical[idx]

        if c in cat_cols:
            int_vals = np.round(vals).astype(int).clip(0, len(cat_maps[c]) - 1)
            result[c] = [cat_maps[c][v] for v in int_vals]
        else:
            # Add tiny noise to avoid exact duplicates
            noise = rng.normal(0, (np.std(vals) + 1e-9) * 0.01, size=n)
            result[c] = vals + noise

    synthetic = pd.DataFrame(result)

    # Restore original dtypes for numerics
    for c in num_cols:
        if pd.api.types.is_integer_dtype(df[c]):
            synthetic[c] = synthetic[c].round().astype(df[c].dtype, errors="ignore")

    return synthetic


def _norm_cdf(x: np.ndarray) -> np.ndarray:
    """Approximation of standard normal CDF."""
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
# ── Ultra-Modern Minimalist Header ──────────────────────────────────────────
import base64

def get_image_base64(path):
    try:
        with open(path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except:
        return None

logo_base_64 = get_image_base64("logo.png")

# Clean & Sophisticated CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

    .header-wrapper {
        display: flex;
        flex-direction: column;
        align-items: center; /* Center align for a premium look */
        justify-content: center;
        padding: 40px 0;
        text-align: center;
        font-family: 'Inter', sans-serif;
    }

    .brand-logo-img {
        width: 130px; /* Bigger logo */
        height: auto;
        margin-bottom: 20px;
        /* Clean shadow for depth */
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

    /* Subtle Animated Line under the credit */
    .underline {
        width: 50px;
        height: 3px;
        background: #00d4ff;
        margin: 15px auto;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Constructing the Minimalist Header
logo_img_html = f'<img src="data:image/png;base64,{logo_base_64}" class="brand-logo-img">' if logo_base_64 else ""

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


# ── Step 1 · Upload ───────────────────────────────────────────────────────────
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

        # PII report
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
    n_rows_default = len(df_ref) if df_ref is not None else 100

    n_rows = st.number_input(
        "Synthetic rows to generate",
        min_value=10,
        max_value=100_000,
        value=n_rows_default,
        step=10,
        disabled=(df_ref is None),
    )

    mask_pii_flag = st.checkbox(
        "Auto-mask PII columns with Faker",
        value=True,
        disabled=(df_ref is None),
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

        # Mask PII before feeding to synthesizer if requested
        if mask_pii_flag and pii_cols:
            df_work = mask_pii(df_work, pii_cols)
            effective_pii = {}
        else:
            effective_pii = pii_cols

        df_synth = generate_synthetic(df_work, n_rows=n_rows)

        st.session_state.df_synth = df_synth
        st.session_state.privacy_score = compute_privacy_score(
            df_synth, effective_pii, masked=mask_pii_flag
        )
    st.success("Synthetic dataset ready!", icon="✅")


# ── Results ───────────────────────────────────────────────────────────────────
if st.session_state.df_synth is not None:
    df_real = st.session_state.df_real
    df_synth = st.session_state.df_synth
    score = st.session_state.privacy_score

    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    st.markdown('<div class="step-pill">STEP 03 · RESULTS & EXPORT</div>', unsafe_allow_html=True)

    # ── Privacy Score + Download ──────────────────────────────────────────────
    col_score, col_dl = st.columns([1, 2], gap="large")

    with col_score:
        score_color = (
            "#00d28c" if score >= 80
            else "#f5a623" if score >= 50
            else "#ff5050"
        )
        label = "EXCELLENT" if score >= 80 else "MODERATE" if score >= 50 else "RISKY"
        st.markdown(f"""
        <div class="card" style="text-align:center">
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

        all_cols = num_cols[:6] + cat_cols[:4]   # max 10 panels

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

            # Delta heatmap
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

        # Statistical summary comparison
        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">Statistical Summary Comparison</div>', unsafe_allow_html=True)
        num_cols_both = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
        if num_cols_both:
            desc_r = df_real[num_cols_both].describe().T.round(3)
            desc_s = df_synth[num_cols_both].describe().T.round(3)
            desc_r.columns = ["Real · " + c for c in desc_r.columns]
            desc_s.columns = ["Synth · " + c for c in desc_s.columns]
            combined = pd.concat([desc_r, desc_s], axis=1)
            # Interleave columns: real mean, synth mean, real std, synth std …
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
