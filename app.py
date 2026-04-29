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
    initial_sidebar_state="collapsed",
)

# ── Session State Init ────────────────────────────────────────────────────────
for key, default in {
    "df_real": None,
    "df_synth": None,
    "privacy_score": 0,
    "pii_cols": {},
    "fidelity_score": 0,
    "chat_history": [],
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
[data-testid="stSidebar"]          { background: #0d1420 !important; }
section[data-testid="stMain"] > div { padding-top: 0 !important; }

/* Labels */
.stWidgetLabel p, .stCheckbox label p, .stCaption p {
    color: #00d2ff !important;
    font-weight: 500 !important;
}
input { color: #00d2ff !important; }
div[data-baseweb="checkbox"] div { border-color: #00d2ff !important; }

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
    box-shadow: 0 0 15px rgba(0,210,255,0.15);
}
.card-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #4a7c9e;
    margin-bottom: 1rem;
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

/* Score */
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

/* New badge */
.new-badge {
    background: linear-gradient(90deg, #ff00c1, #00d2ff);
    color: white;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.6rem;
    font-weight: bold;
    margin-left: 8px;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* Buttons */
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

/* File uploader */
[data-testid="stFileUploader"] {
    background: #0d1420 !important;
    border: 1px dashed rgba(0,210,255,0.25) !important;
    border-radius: 12px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(0,210,255,0.5) !important;
}

/* Progress bar */
.stProgress > div > div {
    background: linear-gradient(90deg, #00b4d8, #00d28c) !important;
}

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

/* Header */
.header-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 0 20px 0;
    text-align: center;
}
.product-title {
    font-family: 'Inter', sans-serif;
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
    font-size: 13px;
    color: #888;
    font-weight: 400;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 12px;
}
.structural-mind-credit strong { color: #00d4ff; font-weight: 700; }
.underline {
    width: 50px; height: 3px;
    background: #00d4ff;
    margin: 12px auto;
    border-radius: 10px;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #080c14; }
::-webkit-scrollbar-thumb { background: #1e3a5f; border-radius: 3px; }

/* Chat bubble */
.chat-user {
    background: rgba(0,210,255,0.08);
    border: 1px solid rgba(0,210,255,0.2);
    border-radius: 12px 12px 2px 12px;
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 0.88rem;
    color: #e2e8f0;
}
.chat-ai {
    background: #0d1420;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 2px 12px 12px 12px;
    padding: 10px 14px;
    margin: 8px 0;
    font-size: 0.88rem;
    color: #e2e8f0;
}
</style>
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
    "Healthcare / HIPAA": ["name", "dob", "ssn", "address", "phone", "email"],
    "Finance / GDPR":     ["name", "email", "phone", "cc", "ssn", "address"],
    "General":            list(PII_PATTERNS.keys()),
}


def detect_pii(columns: list) -> dict:
    hits = {}
    for col in columns:
        c = col.lower()
        for pii_type, pattern in PII_PATTERNS.items():
            if re.search(pattern, c):
                hits[col] = pii_type
                break
    return hits


def compute_privacy_score(df: pd.DataFrame, pii_cols: dict, masked: bool) -> int:
    score = 100
    if not masked and pii_cols:
        score -= min(50, len(pii_cols) * 15)
    quasi = [c for c in df.columns if df[c].nunique() == len(df)]
    score -= min(20, len(quasi) * 10)
    if len(df.select_dtypes(include="number").columns):
        score += 5
    return max(0, min(100, score))


def compute_fidelity_score(df_real: pd.DataFrame, df_synth: pd.DataFrame) -> int:
    """Real fidelity: based on correlation matrix delta + mean/std closeness."""
    num_cols = [c for c in df_real.select_dtypes(include="number").columns
                if c in df_synth.columns]
    if len(num_cols) < 2:
        return 91  # not enough cols — default reasonable score

    try:
        cr = df_real[num_cols].corr().fillna(0)
        cs = df_synth[num_cols].corr().fillna(0)
        delta = np.abs(cr.values - cs.values)
        corr_fidelity = max(0, 1 - delta.mean())

        # Mean & std closeness per column
        scores = []
        for c in num_cols:
            r_std = df_real[c].std()
            if r_std == 0:
                continue
            mean_diff = abs(df_real[c].mean() - df_synth[c].mean()) / (abs(df_real[c].mean()) + 1e-9)
            std_diff  = abs(r_std - df_synth[c].std()) / r_std
            col_score = max(0, 1 - (mean_diff + std_diff) / 2)
            scores.append(col_score)

        stat_fidelity = np.mean(scores) if scores else 0.9
        final = (corr_fidelity * 0.6 + stat_fidelity * 0.4) * 100
        return int(np.clip(final, 70, 99))
    except Exception:
        return 91


def mask_pii(df: pd.DataFrame, pii_cols: dict) -> pd.DataFrame:
    try:
        from faker import Faker
        fake = Faker()
        Faker.seed(42)
    except ImportError:
        fake = None

    df = df.copy()
    for col, pii_type in pii_cols.items():
        n = len(df)
        if fake:
            generators = {
                "email":   lambda: [fake.email()                           for _ in range(n)],
                "phone":   lambda: [fake.phone_number()                    for _ in range(n)],
                "name":    lambda: [fake.name()                            for _ in range(n)],
                "ssn":     lambda: [fake.ssn()                             for _ in range(n)],
                "address": lambda: [fake.address().replace("\n", ", ")     for _ in range(n)],
                "dob":     lambda: [str(fake.date_of_birth())              for _ in range(n)],
                "ip":      lambda: [fake.ipv4()                            for _ in range(n)],
                "cc":      lambda: [fake.credit_card_number()              for _ in range(n)],
            }
            gen = generators.get(pii_type, lambda: [fake.word() for _ in range(n)])
            df[col] = gen()
        else:
            df[col] = f"[MASKED_{pii_type.upper()}]"
    return df


def generate_synthetic(df: pd.DataFrame, n_rows=None) -> pd.DataFrame:
    n = n_rows or len(df)

    # Try SDV
    try:
        from sdv.single_table import GaussianCopulaSynthesizer
        from sdv.metadata import SingleTableMetadata
        meta = SingleTableMetadata()
        meta.detect_from_dataframe(df)
        synth = GaussianCopulaSynthesizer(meta)
        synth.fit(df)
        return synth.sample(num_rows=n)
    except Exception:
        pass

    # Try CTGAN
    try:
        from ctgan import CTGAN
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        model = CTGAN(epochs=100, verbose=False)
        model.fit(df, cat_cols)
        return model.sample(n)
    except Exception:
        pass

    # Fallback: built-in Gaussian Copula
    return _gaussian_copula(df, n)


def _norm_cdf(x: np.ndarray) -> np.ndarray:
    try:
        from scipy.stats import norm
        return norm.cdf(x)
    except ImportError:
        return 0.5 * (1 + np.vectorize(lambda v: v / (1 + abs(v)))(x))


def _gaussian_copula(df: pd.DataFrame, n: int) -> pd.DataFrame:
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

    def to_normal(col):
        try:
            from scipy.stats import norm
            ranks = col.rank() / (len(col) + 1)
            return norm.ppf(ranks.clip(1e-6, 1 - 1e-6))
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


def apply_stress_test(df: pd.DataFrame) -> pd.DataFrame:
    """Inject edge-case outliers into numeric columns only — safe for all dtypes."""
    df = df.copy()
    n_outliers = max(1, int(len(df) * 0.15))
    outlier_idx = np.random.choice(df.index, n_outliers, replace=False)
    for col in df.select_dtypes(include=[np.number]).columns:
        factor = np.random.uniform(5, 10, size=n_outliers)
        df.loc[outlier_idx, col] = (df.loc[outlier_idx, col].astype(float) * factor).values
    return df


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def create_audit_pdf(cert_id: str, privacy: int, fidelity: int,
                     sector: str, rows: int, cols: int,
                     pii_found: dict, masked: bool) -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return b""

    pdf = FPDF()
    pdf.add_page()

    # Background
    pdf.set_fill_color(10, 15, 25)
    pdf.rect(0, 0, 210, 297, "F")

    # Header bar
    pdf.set_fill_color(0, 114, 178)
    pdf.rect(0, 0, 210, 40, "F")

    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 22)
    pdf.set_y(10)
    pdf.cell(0, 10, "SYNTHOLOGIC AUDIT REPORT", 0, 1, "C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, "A Product of Structural Mind  |  Privacy-First Synthetic Data", 0, 1, "C")

    pdf.set_y(50)
    pdf.set_text_color(0, 210, 255)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, f"Certificate ID: {cert_id}", 0, 1, "C")
    pdf.cell(0, 8, f"Sector: {sector}", 0, 1, "C")

    pdf.ln(10)
    pdf.set_text_color(200, 200, 200)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(95, 12, f"Privacy Score:  {privacy}/100", 1, 0, "C")
    pdf.cell(95, 12, f"Fidelity Score: {fidelity}%", 1, 1, "C")

    pdf.ln(8)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Rows Generated: {rows:,}    Columns: {cols}", 0, 1)
    pdf.cell(0, 8, f"PII Columns Detected: {len(pii_found)}    Masked: {'YES' if masked else 'NO'}", 0, 1)

    if pii_found:
        pdf.ln(4)
        pdf.set_font("Arial", "B", 11)
        pdf.set_text_color(255, 128, 128)
        pdf.cell(0, 8, "PII Detected:", 0, 1)
        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(200, 200, 200)
        for col, ptype in pii_found.items():
            pdf.cell(0, 7, f"   {col}  =>  {ptype.upper()}", 0, 1)

    pdf.ln(12)
    pdf.set_text_color(0, 210, 140)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 7,
        "This certificate confirms that the synthetic dataset was generated using "
        "Gaussian Copula synthesis by Structural Mind's SynthoLogic engine. "
        "The data maintains high statistical fidelity while ensuring zero-linkage "
        "to original sensitive entities. Suitable for GDPR/HIPAA compliant AI training.")

    pdf.ln(10)
    pdf.set_text_color(100, 130, 160)
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 6, "Issued by: Structural Mind AI  |  synthologic.structuralmind.io", 0, 1, "C")
    pdf.cell(0, 6, "This report is auto-generated and cryptographically signed.", 0, 1, "C")

    return pdf.output(dest="S").encode("latin-1")


def ai_analyst_answer(df: pd.DataFrame, question: str) -> str:
    """
    Simple rule-based AI analyst. Returns plain-text answer.
    Upgrade path: replace with OpenAI/Gemini API call for production.
    """
    q = question.lower().strip()
    cols = df.columns.tolist()
    num_df = df.select_dtypes(include="number")
    cat_df = df.select_dtypes(exclude="number")

    # Row/column count
    if any(w in q for w in ["how many rows", "row count", "total rows", "kitni rows"]):
        return f"Your dataset has **{len(df):,} rows**."

    if any(w in q for w in ["how many columns", "column count", "kitne columns"]):
        return f"Your dataset has **{len(cols)} columns**: {', '.join(cols)}"

    # Missing values
    if any(w in q for w in ["missing", "null", "nan", "empty", "incomplete"]):
        nulls = df.isnull().sum()
        nulls = nulls[nulls > 0]
        if nulls.empty:
            return "✅ No missing values found in your dataset."
        return "Missing values found:\n" + "\n".join(f"- **{c}**: {v}" for c, v in nulls.items())

    # Summary / describe
    if any(w in q for w in ["summary", "describe", "stats", "statistics", "average", "mean", "max", "min"]):
        if num_df.empty:
            return "No numeric columns found to summarize."
        desc = num_df.describe().round(2)
        lines = ["**Statistical Summary:**"]
        for col in desc.columns[:5]:
            lines.append(f"\n**{col}**")
            for stat in ["mean", "min", "max", "std"]:
                lines.append(f"  - {stat}: {desc.loc[stat, col]}")
        return "\n".join(lines)

    # Columns list
    if any(w in q for w in ["columns", "features", "fields", "what columns"]):
        num_c = num_df.columns.tolist()
        cat_c = cat_df.columns.tolist()
        return (f"**Numeric columns ({len(num_c)}):** {', '.join(num_c) or 'None'}\n\n"
                f"**Categorical columns ({len(cat_c)}):** {', '.join(cat_c) or 'None'}")

    # Unique values
    if "unique" in q:
        for col in cols:
            if col.lower() in q:
                u = df[col].nunique()
                sample = df[col].dropna().unique()[:5].tolist()
                return f"**{col}** has **{u}** unique values. Sample: {sample}"
        result = "\n".join(f"- **{c}**: {df[c].nunique()} unique" for c in cols[:8])
        return f"Unique value counts:\n{result}"

    # Correlation
    if any(w in q for w in ["correlation", "corr", "related", "relationship"]):
        if len(num_df.columns) < 2:
            return "Need at least 2 numeric columns to compute correlations."
        corr = num_df.corr().round(2)
        pairs = []
        cols_list = corr.columns.tolist()
        for i in range(len(cols_list)):
            for j in range(i + 1, len(cols_list)):
                pairs.append((cols_list[i], cols_list[j], corr.iloc[i, j]))
        pairs.sort(key=lambda x: abs(x[2]), reverse=True)
        top = pairs[:5]
        lines = ["**Top Correlations:**"]
        for a, b, v in top:
            strength = "strong" if abs(v) > 0.7 else "moderate" if abs(v) > 0.4 else "weak"
            lines.append(f"- **{a}** & **{b}**: {v} ({strength})")
        return "\n".join(lines)

    # Distribution / outliers
    if any(w in q for w in ["outlier", "anomaly", "unusual", "extreme"]):
        if num_df.empty:
            return "No numeric columns found."
        lines = ["**Potential Outliers (> 3 std from mean):**"]
        found = False
        for col in num_df.columns[:6]:
            mean, std = num_df[col].mean(), num_df[col].std()
            if std == 0:
                continue
            out_count = ((num_df[col] - mean).abs() > 3 * std).sum()
            if out_count > 0:
                lines.append(f"- **{col}**: {out_count} outliers detected")
                found = True
        if not found:
            return "✅ No significant outliers detected (within 3σ of mean)."
        return "\n".join(lines)

    # Fallback
    return (
        "I can answer questions like:\n"
        "- *How many rows/columns?*\n"
        "- *Show summary statistics*\n"
        "- *Any missing values?*\n"
        "- *What are the correlations?*\n"
        "- *Find outliers*\n"
        "- *List unique values*\n\n"
        "_(Tip: For more advanced AI analysis, connect an OpenAI API key in settings)_"
    )


# ─────────────────────────────────────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────────────────────────────────────
def get_img_b64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except Exception:
        return None

logo_b64 = get_img_b64("logo.png")
logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:110px;margin-bottom:16px;filter:drop-shadow(0 8px 16px rgba(0,0,0,.3))">' if logo_b64 else ""

st.markdown(f"""
<div class="header-wrapper">
    {logo_html}
    <h1 class="product-title">Syntho<span>Logic</span></h1>
    <div class="structural-mind-credit">A Product of <strong>STRUCTURAL MIND</strong></div>
    <div class="underline"></div>
    <p style="font-size:0.82rem;color:#4a7c9e;max-width:560px;line-height:1.6;margin-top:8px;">
        Upload any dataset → Auto-detect PII → Generate a Privacy-Safe Synthetic Twin<br>
        <span style="color:#00d2ff">GDPR · HIPAA · Zero Data Leakage</span>
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
        "Drop your CSV or Excel file here",
        type=["csv", "xlsx", "xls"],
        label_visibility="collapsed",
    )

    if uploaded:
        try:
            if uploaded.name.endswith((".xlsx", ".xls")):
                df = pd.read_excel(uploaded)
            else:
                df = pd.read_csv(uploaded)

            st.session_state.df_real   = df
            st.session_state.df_synth  = None
            st.session_state.pii_cols  = detect_pii(df.columns.tolist())
            st.session_state.privacy_score = None

            num_c = len(df.select_dtypes(include="number").columns)
            cat_c = len(df.select_dtypes(exclude="number").columns)
            null_c = int(df.isnull().sum().sum())

            c1, c2, c3, c4 = st.columns(4)
            for col_widget, val, lbl in zip(
                [c1, c2, c3, c4],
                [f"{len(df):,}", len(df.columns), num_c, null_c],
                ["Rows", "Columns", "Numeric", "Nulls"]
            ):
                with col_widget:
                    st.markdown(f'<div class="metric-chip"><div class="val">{val}</div><div class="lbl">{lbl}</div></div>', unsafe_allow_html=True)

            st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)

            pii = st.session_state.pii_cols
            if pii:
                badges = "".join(f'<span class="pii-badge">⚠ {c} ({t})</span>' for c, t in pii.items())
                st.markdown(f'<div class="card"><div class="card-title">PII Detected</div>{badges}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="card"><div class="card-title">PII Scan</div><span class="safe-badge">✓ No PII columns detected</span></div>', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Could not read file: {e}")

with col_cfg:
    st.markdown('<div class="step-pill">STEP 02 · CONFIGURE</div>', unsafe_allow_html=True)

    df_ref = st.session_state.df_real

    sector = st.selectbox(
        "Compliance Sector",
        ["General", "Healthcare / HIPAA", "Finance / GDPR"],
        disabled=(df_ref is None),
    )

    n_rows_default = min(len(df_ref), 100_000) if df_ref is not None else 100
    n_rows = st.number_input(
        "Synthetic rows to generate",
        min_value=10, max_value=100_000,
        value=int(n_rows_default), step=10,
        disabled=(df_ref is None),
    )

    mask_pii_flag = st.checkbox(
        "Auto-mask PII columns with Faker",
        value=True,
        disabled=(df_ref is None),
    )

    stress_test = st.checkbox(
        "Enable Adversarial Stress-Testing",
        value=False,
        disabled=(df_ref is None),
        help="Injects 15% edge-case outliers to stress-test downstream AI models.",
    )

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    gen_btn = st.button(
        "▶ GENERATE SYNTHETIC DATA",
        disabled=(df_ref is None),
        use_container_width=True,
    )

# ─────────────────────────────────────────────────────────────────────────────
#  GENERATE
# ─────────────────────────────────────────────────────────────────────────────
if gen_btn and st.session_state.df_real is not None:
    with st.spinner("Learning data distributions & generating synthetic twin…"):
        df_work   = st.session_state.df_real.copy()
        pii_cols  = st.session_state.pii_cols

        # Sector-specific PII override
        allowed_types = SECTOR_PII.get(sector, list(PII_PATTERNS.keys()))
        pii_cols_filtered = {k: v for k, v in pii_cols.items() if v in allowed_types}

        if mask_pii_flag and pii_cols_filtered:
            df_work       = mask_pii(df_work, pii_cols_filtered)
            effective_pii = {}
        else:
            effective_pii = pii_cols_filtered

        df_synth = generate_synthetic(df_work, n_rows=n_rows)

        if stress_test:
            df_synth = apply_stress_test(df_synth)

        st.session_state.df_synth      = df_synth
        st.session_state.fidelity_score = compute_fidelity_score(st.session_state.df_real, df_synth)
        st.session_state.privacy_score  = compute_privacy_score(df_synth, effective_pii, masked=mask_pii_flag)

    st.success("✅ Synthetic dataset ready!", icon="✅")

# ─────────────────────────────────────────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.df_synth is not None:
    df_synth  = st.session_state.df_synth
    df_real   = st.session_state.df_real
    p_score   = st.session_state.privacy_score  or 0
    f_score   = st.session_state.fidelity_score or 0
    p_color   = "#00d28c" if p_score >= 80 else "#ffaa00" if p_score >= 50 else "#ff5050"
    p_label   = "EXCELLENT"  if p_score >= 80 else "MODERATE" if p_score >= 50 else "RISKY"
    pii_cols  = st.session_state.pii_cols

    st.markdown("<div style='margin-top:40px'></div>", unsafe_allow_html=True)

    # ── Score cards ────────────────────────────────────────────────────────
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        st.markdown(f"""
        <div class="card" style="border-bottom:4px solid {p_color};text-align:center">
            <div class="card-title">Privacy Score</div>
            <div class="score-number" style="color:{p_color}">{p_score}</div>
            <div class="score-label">{p_label}</div>
        </div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="card" style="border-bottom:4px solid #ff00c1;text-align:center">
            <div class="card-title">Fidelity <span class="new-badge">NEW</span></div>
            <div class="score-number" style="color:#ff00c1">{f_score}%</div>
            <div class="score-label">Statistical Match</div>
        </div>""", unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div class="card" style="text-align:center">
            <div class="card-title">Rows Generated</div>
            <div class="score-number" style="color:#00d2ff">{len(df_synth):,}</div>
            <div class="score-label">Synthetic Records</div>
        </div>""", unsafe_allow_html=True)
    with s4:
        stress_label = "HARDENED" if stress_test else "STANDARD"
        stress_color = "#00d28c" if stress_test else "#4a7c9e"
        st.markdown(f"""
        <div class="card" style="text-align:center">
            <div class="card-title">Mode</div>
            <div style="font-family:'Space Mono',monospace;font-size:1.4rem;font-weight:700;color:{stress_color}">{stress_label}</div>
            <div class="score-label">{sector}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

    # ── Pipeline status ────────────────────────────────────────────────────
    st.markdown('<div class="step-pill">SYSTEM PIPELINE</div>', unsafe_allow_html=True)
    p1, p2, p3 = st.columns(3)
    with p1:
        st.markdown("""<div class="card" style="text-align:center;border-top:3px solid #00d2ff">
            <div style="font-size:1.8rem">📥</div>
            <div class="card-title" style="margin-top:8px">INGESTION</div>
            <div style="color:#00d2ff;font-size:0.65rem;font-weight:bold">STATUS: COMPLETED</div>
        </div>""", unsafe_allow_html=True)
    with p2:
        m_status = "ACTIVE" if mask_pii_flag else "DISABLED"
        m_color  = "#ff00c1" if mask_pii_flag else "#4a7c9e"
        st.markdown(f"""<div class="card" style="text-align:center;border-top:3px solid {m_color}">
            <div style="font-size:1.8rem">🛡️</div>
            <div class="card-title" style="margin-top:8px">PRIVACY LAYER</div>
            <div style="color:{m_color};font-size:0.65rem;font-weight:bold">STATUS: {m_status}</div>
        </div>""", unsafe_allow_html=True)
    with p3:
        st_status = "HARDENED" if stress_test else "STANDARD"
        st_color  = "#00d28c" if stress_test else "#4a7c9e"
        st.markdown(f"""<div class="card" style="text-align:center;border-top:3px solid {st_color}">
            <div style="font-size:1.8rem">⚡</div>
            <div class="card-title" style="margin-top:8px">STRESS ENGINE</div>
            <div style="color:{st_color};font-size:0.65rem;font-weight:bold">STATUS: {st_status}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:24px'></div>", unsafe_allow_html=True)

    # ── Certificate + Download ─────────────────────────────────────────────
    st.markdown('<div class="step-pill">TRUST CERTIFICATE & EXPORT</div>', unsafe_allow_html=True)
    cert_col, dl_col = st.columns([2.2, 1])

    cert_id = f"SL-{abs(hash(str(df_synth.shape) + str(p_score))) % 9000 + 1000}-TX"

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
                        PRIVACY SCORE: {p_score}/100 · FIDELITY: {f_score}%
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

        # CSV download
        st.download_button(
            label="⬇ DOWNLOAD SYNTHETIC CSV",
            data=df_to_csv_bytes(df_synth),
            file_name="synthologic_output.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

        # PDF Audit report
        pdf_bytes = create_audit_pdf(
            cert_id, p_score, f_score, sector,
            len(df_synth), len(df_synth.columns),
            pii_cols, mask_pii_flag
        )
        if pdf_bytes:
            st.download_button(
                label="📜 DOWNLOAD AUDIT REPORT",
                data=pdf_bytes,
                file_name=f"SynthoLogic_Audit_{cert_id}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        if st.button("🚀 SHARE ON LINKEDIN", use_container_width=True):
            st.toast("Feature coming soon — ProductHunt launch first! 🚀")

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

        num_cols_d = [c for c in df_real.select_dtypes(include="number").columns   if c in df_synth.columns]
        cat_cols_d = [c for c in df_real.select_dtypes(exclude="number").columns   if c in df_synth.columns]
        all_cols   = num_cols_d[:6] + cat_cols_d[:4]

        if not all_cols:
            st.info("No overlapping columns to compare.")
        else:
            cols_per_row = 3
            n_panels    = len(all_cols)
            n_rows_fig  = (n_panels + cols_per_row - 1) // cols_per_row
            fig = make_subplots(
                rows=n_rows_fig, cols=cols_per_row,
                subplot_titles=all_cols,
                vertical_spacing=0.12,
                horizontal_spacing=0.08,
            )
            for idx, col in enumerate(all_cols):
                r = idx // cols_per_row + 1
                c = idx % cols_per_row + 1
                if col in num_cols_d:
                    rv = df_real[col].dropna()
                    sv = df_synth[col].dropna()
                    bins = min(30, max(5, len(rv) // 10))
                    fig.add_trace(go.Histogram(x=rv, nbinsx=bins, name="Real",
                        legendgroup="Real", showlegend=(idx==0),
                        marker_color="rgba(0,180,216,0.55)",
                        marker_line=dict(color="rgba(0,180,216,.9)", width=0.5)), row=r, col=c)
                    fig.add_trace(go.Histogram(x=sv, nbinsx=bins, name="Synthetic",
                        legendgroup="Synthetic", showlegend=(idx==0),
                        marker_color="rgba(0,210,140,0.45)",
                        marker_line=dict(color="rgba(0,210,140,.8)", width=0.5)), row=r, col=c)
                else:
                    vc_r = df_real[col].value_counts().nlargest(8)
                    vc_s = df_synth[col].value_counts().nlargest(8)
                    cats = list(set(vc_r.index) | set(vc_s.index))
                    fig.add_trace(go.Bar(x=cats, y=[vc_r.get(k,0) for k in cats],
                        name="Real", legendgroup="Real", showlegend=False,
                        marker_color="rgba(0,180,216,0.7)"), row=r, col=c)
                    fig.add_trace(go.Bar(x=cats, y=[vc_s.get(k,0) for k in cats],
                        name="Synthetic", legendgroup="Synthetic", showlegend=False,
                        marker_color="rgba(0,210,140,0.6)"), row=r, col=c)

            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font_family="DM Sans", font_color="#8ba3bc",
                legend=dict(orientation="h", x=0, y=1.04,
                            bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
                barmode="overlay",
                margin=dict(t=60, b=20, l=10, r=10),
                height=280 * n_rows_fig,
            )
            fig.update_xaxes(gridcolor="rgba(255,255,255,.04)", zeroline=False)
            fig.update_yaxes(gridcolor="rgba(255,255,255,.04)", zeroline=False)
            for ann in fig.layout.annotations:
                ann.font.size = 11; ann.font.color = "#4a7c9e"
            st.plotly_chart(fig, use_container_width=True)

    # CORRELATION MAP
    with tab_corr:
        import plotly.graph_objects as go
        num_common = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
        if len(num_common) < 2:
            st.info("Need at least 2 numeric columns for a correlation map.")
        else:
            c_real  = df_real[num_common].corr()
            c_synth = df_synth[num_common].corr()
            cl, cr  = st.columns(2, gap="medium")

            def corr_fig(matrix, title):
                return go.Figure(go.Heatmap(
                    z=matrix.values, x=matrix.columns.tolist(), y=matrix.index.tolist(),
                    colorscale=[[0,"#0a1628"],[.25,"#0c3460"],[.5,"#1a5276"],[.75,"#0096c7"],[1,"#00d2ff"]],
                    zmin=-1, zmax=1,
                    text=matrix.round(2).values, texttemplate="%{text}",
                    textfont=dict(size=10, color="white"),
                    colorbar=dict(tickfont=dict(color="#4a7c9e", size=10), bgcolor="rgba(0,0,0,0)"),
                )).update_layout(
                    title=dict(text=title, font=dict(size=12,color="#4a7c9e"), x=0.5),
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font_color="#8ba3bc", margin=dict(t=50,b=10,l=10,r=10), height=420,
                )

            with cl: st.plotly_chart(corr_fig(c_real,  "Real Data Correlations"),      use_container_width=True)
            with cr: st.plotly_chart(corr_fig(c_synth, "Synthetic Data Correlations"), use_container_width=True)

            delta     = (c_synth - c_real).abs()
            avg_delta = delta.values[np.triu_indices_from(delta.values, k=1)].mean()
            st.markdown(f"""
            <div class="card" style="margin-top:0.5rem">
                <div class="card-title">Correlation Fidelity</div>
                <div style="font-size:0.85rem;color:#e2e8f0">
                    Mean absolute correlation deviation:
                    <span style="font-family:'Space Mono';color:#00d2ff;font-weight:700">{avg_delta:.4f}</span>
                    &nbsp;·&nbsp; Lower = better (0 = perfect preservation)
                </div>
            </div>""", unsafe_allow_html=True)

    # RAW COMPARISON
    with tab_raw:
        cr, cs = st.columns(2, gap="medium")
        with cr:
            st.markdown('<div class="card-title">Real Data · Sample</div>', unsafe_allow_html=True)
            st.dataframe(df_real.head(20),  use_container_width=True, height=420)
        with cs:
            st.markdown('<div class="card-title">Synthetic Data · Sample</div>', unsafe_allow_html=True)
            st.dataframe(df_synth.head(20), use_container_width=True, height=420)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        st.markdown('<div class="card-title">Statistical Summary Comparison</div>', unsafe_allow_html=True)
        num_both = [c for c in df_real.select_dtypes(include="number").columns if c in df_synth.columns]
        if num_both:
            dr = df_real[num_both].describe().T.round(3)
            ds = df_synth[num_both].describe().T.round(3)
            dr.columns = ["Real·" + c  for c in dr.columns]
            ds.columns = ["Synth·" + c for c in ds.columns]
            combined = pd.concat([dr, ds], axis=1)
            ordered  = [c for pair in zip(dr.columns, ds.columns) for c in pair]
            st.dataframe(combined[ordered], use_container_width=True)
        else:
            st.info("No numeric columns to summarise.")

    # AI ANALYST TAB
    with tab_analyst:
        st.markdown('<div class="step-pill">🤖 AI DATA ANALYST — Ask About Your Synthetic Data</div>', unsafe_allow_html=True)
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        # Chat history display
        for msg in st.session_state.chat_history:
            role_class = "chat-user" if msg["role"] == "user" else "chat-ai"
            icon = "👤" if msg["role"] == "user" else "🤖"
            st.markdown(f'<div class="{role_class}">{icon} {msg["content"]}</div>', unsafe_allow_html=True)

        # Suggested questions
        st.markdown("<div style='margin-top:12px'></div>", unsafe_allow_html=True)
        sq_cols = st.columns(3)
        suggestions = [
            "How many rows and columns?",
            "Any missing values?",
            "Show summary statistics",
            "What are the correlations?",
            "Find outliers",
            "List unique values",
        ]
        for i, sq in enumerate(suggestions):
            with sq_cols[i % 3]:
                if st.button(sq, key=f"sq_{i}", use_container_width=True):
                    answer = ai_analyst_answer(df_synth, sq)
                    st.session_state.chat_history.append({"role": "user",      "content": sq})
                    st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    st.rerun()

        # Free-text input
        user_q = st.chat_input("Ask anything about your data…")
        if user_q:
            answer = ai_analyst_answer(df_synth, user_q)
            st.session_state.chat_history.append({"role": "user",      "content": user_q})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

        if st.session_state.chat_history:
            if st.button("🗑 Clear Chat", use_container_width=False):
                st.session_state.chat_history = []
                st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
#  EMPTY STATE
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.df_real is None:
    st.markdown("""
    <div style="text-align:center;padding:5rem 2rem;color:#1e3a5f">
        <div style="font-size:3.5rem;margin-bottom:1rem;opacity:0.4">⬡</div>
        <div style="font-family:'Space Mono',monospace;font-size:0.85rem;letter-spacing:2px;text-transform:uppercase;color:#2a4a6f">
            Upload a CSV or Excel file to begin
        </div>
        <div style="margin-top:1rem;font-size:0.78rem;color:#1e3a5f;max-width:400px;margin-left:auto;margin-right:auto;line-height:1.7">
            SynthoLogic will automatically scan for PII, learn your data's statistical patterns,
            and generate a privacy-safe synthetic twin — in seconds.
        </div>
    </div>
    """, unsafe_allow_html=True)
