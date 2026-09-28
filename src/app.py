import streamlit as st
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
import plotly.express as px
import textwrap
import sqlite3
from datetime import datetime


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Customer Churn Prediction",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# STEP 7 - LOGIN & ROLE-BASED ACCESS
# ============================================================

# Demo credentials. Change these before using the application
# in a real production environment.
USERS = {
    "admin": {
        "password": "admin123",
        "role": "Admin"
    },
    "user": {
        "password": "user123",
        "role": "User"
    }
}


def logout():
    """Clear the current login session."""
    for key in ["authenticated", "username", "role"]:
        st.session_state.pop(key, None)
    st.rerun()


def show_login_page():
    """Display the Step 7 login screen."""

    st.markdown(
        """
        <div style="max-width:620px;margin:70px auto 20px auto;text-align:center;">
            <div style="font-size:64px;">🔐</div>
            <h1 style="font-size:42px;margin-bottom:8px;">Customer Churn AI</h1>
            <p style="color:#a8b0c2;font-size:17px;">
                Secure login · Role-based dashboard access
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    login_col1, login_col2, login_col3 = st.columns([1, 2, 1])

    with login_col2:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("### 🔑 Sign in")

            username = st.text_input(
                "Username",
                placeholder="Enter username"
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter password"
            )

            submitted = st.form_submit_button(
                "🚀 Login",
                type="primary",
                width="stretch"
            )

        if submitted:
            account = USERS.get(username.strip().lower())

            if account and password == account["password"]:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username.strip().lower()
                st.session_state["role"] = account["role"]
                st.success(f"Welcome, {username.strip()}!")
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")



if not st.session_state.get("authenticated", False):
    show_login_page()
    st.stop()

CURRENT_USERNAME = st.session_state.get("username", "user")
CURRENT_ROLE = st.session_state.get("role", "User")
IS_ADMIN = CURRENT_ROLE == "Admin"


# ============================================================
# HELPER FOR HTML
# ============================================================

def render_html(html_code):
    """
    Render custom HTML reliably.

    Newer Streamlit versions provide st.html(), which is more reliable
    for custom HTML than st.markdown(..., unsafe_allow_html=True).
    A fallback is kept for older Streamlit versions.
    """
    html_code = textwrap.dedent(str(html_code)).strip()

    if hasattr(st, "html"):
        st.html(html_code)
    else:
        st.markdown(html_code, unsafe_allow_html=True)


# ============================================================
# STEP 5 - PREDICTION HISTORY DATABASE
# ============================================================

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "customer_churn_history.db"
)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def init_history_database():
    """Create the local SQLite database used by prediction history."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_time TEXT NOT NULL,
                customer_id TEXT,
                customer_name TEXT,
                age INTEGER,
                location TEXT,
                customer_since TEXT,
                tenure INTEGER,
                gender TEXT,
                contract TEXT,
                internet_service TEXT,
                payment_method TEXT,
                online_security TEXT,
                tech_support TEXT,
                monthly_charges REAL,
                total_charges REAL,
                prediction TEXT,
                churn_probability REAL,
                no_churn_probability REAL,
                risk_level TEXT
            )
            """
        )
        conn.commit()


def save_prediction_history(
    customer_id,
    customer_name,
    age,
    location,
    customer_since,
    tenure,
    gender,
    contract,
    internet_service,
    payment_method,
    online_security,
    tech_support,
    monthly_charges,
    total_charges,
    prediction,
    churn_probability,
    no_churn_probability,
    risk_level
):
    """Save one completed prediction to SQLite."""
    prediction_label = (
        "Customer Will Churn"
        if str(prediction).lower() in {
            "1", "true", "yes", "churn", "churned"
        }
        else "Customer Will Not Churn"
    )

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO prediction_history (
                prediction_time, customer_id, customer_name, age, location,
                customer_since, tenure, gender, contract, internet_service,
                payment_method, online_security, tech_support,
                monthly_charges, total_charges, prediction,
                churn_probability, no_churn_probability, risk_level
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                customer_id,
                customer_name,
                int(age),
                location,
                customer_since,
                int(tenure),
                gender,
                contract,
                internet_service,
                payment_method,
                online_security,
                tech_support,
                float(monthly_charges),
                float(total_charges),
                prediction_label,
                float(churn_probability),
                float(no_churn_probability),
                risk_level
            )
        )
        conn.commit()


def load_prediction_history():
    """Load saved predictions from newest to oldest."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(
            """
            SELECT
                id AS ID,
                prediction_time AS Time,
                customer_id AS "Customer ID",
                customer_name AS "Customer Name",
                age AS Age,
                location AS Location,
                customer_since AS "Customer Since",
                tenure AS "Tenure (Months)",
                gender AS Gender,
                contract AS Contract,
                internet_service AS "Internet Service",
                payment_method AS "Payment Method",
                online_security AS "Online Security",
                tech_support AS "Tech Support",
                monthly_charges AS "Monthly Charges",
                total_charges AS "Total Charges",
                prediction AS Prediction,
                churn_probability AS "Churn Probability (%)",
                no_churn_probability AS "No Churn Probability (%)",
                risk_level AS "Risk Level"
            FROM prediction_history
            ORDER BY id DESC
            """,
            conn
        )


def delete_prediction_history():
    """Delete all saved prediction records."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM prediction_history")
        conn.commit()


init_history_database()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
<style>

@keyframes gradientShift {
    0% {
        background-position: 0% 50%;
    }

    50% {
        background-position: 100% 50%;
    }

    100% {
        background-position: 0% 50%;
    }
}

@keyframes fadeUp {
    from {
        opacity: 0;
        transform: translateY(18px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes glowPulse {
    0%, 100% {
        box-shadow: 0 0 0 rgba(99,102,241,0);
    }

    50% {
        box-shadow: 0 0 28px rgba(99,102,241,.22);
    }
}

@keyframes shimmer {
    0% {
        background-position: -200% center;
    }

    100% {
        background-position: 200% center;
    }
}

@keyframes floatCard {
    0%, 100% {
        transform: translateY(0);
    }

    50% {
        transform: translateY(-4px);
    }
}


/* ============================================================
   MAIN APP
   ============================================================ */

.stApp {
    background:
        radial-gradient(
            circle at 8% 8%,
            rgba(99,102,241,.16),
            transparent 25%
        ),
        radial-gradient(
            circle at 92% 12%,
            rgba(14,165,233,.13),
            transparent 24%
        ),
        linear-gradient(
            135deg,
            #070b14 0%,
            #0d1322 48%,
            #080d18 100%
        );

    background-size: 140% 140%;
    animation: gradientShift 16s ease infinite;
    color: #f8fafc;
}


/* ============================================================
   HEADER
   ============================================================ */

[data-testid="stHeader"] {
    background: rgba(0,0,0,0);
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
    animation: fadeUp .7s ease both;
}


/* ============================================================
   PROFILE CARD
   ============================================================ */

.profile-card {
    padding: 18px;
    border-radius: 18px;
    border: 1px solid rgba(148,163,184,.18);
    background: linear-gradient(135deg, rgba(99,102,241,.16), rgba(14,165,233,.08));
    margin: 12px 0 20px 0;
    box-shadow: 0 12px 30px rgba(0,0,0,.16);
}

.profile-avatar {
    width: 58px;
    height: 58px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    font-weight: 800;
    background: linear-gradient(135deg, #6366f1, #0ea5e9);
    color: white;
    margin-bottom: 12px;
}

.profile-name {
    font-size: 22px;
    font-weight: 800;
    color: white;
}

.profile-meta {
    color: #a8b0c2;
    font-size: 13px;
    margin-top: 4px;
}

.profile-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-top: 15px;
}

.profile-item {
    padding: 10px 12px;
    border-radius: 12px;
    background: rgba(255,255,255,.045);
}

.profile-label {
    color: #94a3b8;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .06em;
}

.profile-value {
    color: white;
    font-weight: 700;
    margin-top: 3px;
}

.section-caption {
    color: #94a3b8;
    font-size: 13px;
    margin-bottom: 10px;
}

/* ============================================================
   SIDEBAR
   ============================================================ */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            rgba(25,29,46,.98),
            rgba(9,13,25,.99)
        );

    border-right: 1px solid rgba(148,163,184,.14);
}

section[data-testid="stSidebar"] > div {
    padding-top: 1.5rem;
}


/* ============================================================
   HERO
   ============================================================ */

.main-title {
    font-size: clamp(34px, 4vw, 52px);
    font-weight: 800;
    letter-spacing: -1.5px;

    background:
        linear-gradient(
            90deg,
            #ffffff,
            #93c5fd,
            #c4b5fd,
            #ffffff
        );

    background-size: 250% auto;

    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    animation: shimmer 6s linear infinite;
}

.hero-title {
    display: flex;
    align-items: center;
    gap: 18px;
    animation: fadeUp .8s ease both;
}

.hero-icon {
    width: 64px;
    height: 64px;

    border-radius: 18px;

    display: inline-flex;
    align-items: center;
    justify-content: center;

    font-size: 18px;
    font-weight: 900;
    letter-spacing: 1px;

    color: #ffffff;

    background:
        linear-gradient(
            135deg,
            #6366f1,
            #38bdf8,
            #8b5cf6
        );

    background-size: 200% 200%;

    box-shadow:
        0 0 25px rgba(99,102,241,.35),
        inset 0 0 18px rgba(255,255,255,.12);

    animation:
        gradientShift 5s ease infinite,
        floatCard 3s ease-in-out infinite;

    flex-shrink: 0;
}

.subtitle {
    font-size: 18px;
    color: #a8b0c2;
    margin-top: 5px;
    margin-bottom: 25px;
}

.ai-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;

    padding: 7px 14px;

    border-radius: 999px;

    background: rgba(99,102,241,.13);

    border: 1px solid rgba(129,140,248,.28);

    color: #c7d2fe;

    font-size: 13px;
    font-weight: 600;

    animation: glowPulse 3s ease-in-out infinite;
}

.ai-dot {
    width: 8px;
    height: 8px;

    border-radius: 50%;

    background: #34d399;

    box-shadow: 0 0 12px #34d399;
}


/* ============================================================
   METRIC CARDS
   ============================================================ */

[data-testid="stMetric"] {
    background: rgba(255,255,255,.045);

    border: 1px solid rgba(255,255,255,.08);

    border-radius: 18px;

    padding: 18px;

    backdrop-filter: blur(14px);

    box-shadow: 0 10px 30px rgba(0,0,0,.16);

    animation: fadeUp .7s ease both;

    transition:
        transform .25s ease,
        border-color .25s ease,
        box-shadow .25s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-5px);

    border-color: rgba(129,140,248,.45);

    box-shadow:
        0 15px 35px rgba(99,102,241,.16);
}

[data-testid="stMetricLabel"] {
    color: #cbd5e1 !important;
}

[data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-weight: 800;
}

.custom-metric-card {
    min-height: 104px;

    padding: 18px;

    border-radius: 18px;

    background: rgba(255,255,255,.045);

    border: 1px solid rgba(255,255,255,.08);

    box-shadow: 0 10px 30px rgba(0,0,0,.16);

    backdrop-filter: blur(14px);

    animation: fadeUp .7s ease both;

    transition:
        transform .25s ease,
        border-color .25s ease,
        box-shadow .25s ease;

    overflow: hidden;
}

.custom-metric-card:hover {
    transform: translateY(-5px);

    border-color: rgba(129,140,248,.45);

    box-shadow:
        0 14px 35px rgba(99,102,241,.14);
}

.custom-metric-label {
    color: #d8deea;

    font-size: 14px;

    font-weight: 600;

    margin-bottom: 8px;
}

.custom-metric-value {
    color: #ffffff;

    font-size: 26px;

    line-height: 1.2;

    font-weight: 800;

    white-space: normal;

    word-break: normal;
}

.model-status {
    margin-top: 8px;

    font-size: 13px;

    color: #34d399;

    font-weight: 700;
}


/* ============================================================
   BUTTONS
   ============================================================ */

.stButton > button {
    border: 0;

    border-radius: 14px;

    min-height: 52px;

    font-weight: 700;

    letter-spacing: .2px;

    transition:
        transform .2s ease,
        box-shadow .2s ease;

    color: #ffffff !important;

    background:
        linear-gradient(
            135deg,
            #4f46e5,
            #7c3aed
        ) !important;
}

.stButton > button:hover {
    transform: translateY(-3px) scale(1.01);

    box-shadow:
        0 12px 30px rgba(99,102,241,.28);
}

.stButton > button:active {
    transform: scale(.98);
}


/* ============================================================
   INPUTS
   ============================================================ */

[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input {
    border-radius: 12px !important;

    background: rgba(8,12,22,.88) !important;

    color: #f8fafc !important;

    border: 1px solid rgba(148,163,184,.18) !important;
}

[data-testid="stNumberInput"] button {
    color: #c4b5fd !important;
}


/* ============================================================
   ALERTS
   ============================================================ */

[data-testid="stAlert"] {
    border-radius: 16px;

    animation: fadeUp .55s ease both;

    backdrop-filter: blur(10px);

    transition:
        transform .25s ease,
        box-shadow .25s ease;
}

[data-testid="stAlert"]:hover {
    transform: translateY(-3px);

    box-shadow:
        0 12px 30px rgba(99,102,241,.12);
}


/* ============================================================
   TEXT
   ============================================================ */

h1,
h2,
h3,
h4,
h5,
h6,
p,
label,
[data-testid="stMarkdownContainer"],
[data-testid="stWidgetLabel"] {
    color: #f8fafc;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: #f1f5f9 !important;
}

hr {
    border-color: rgba(148,163,184,.16) !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid rgba(148,163,184,.16);

    border-radius: 14px;
}


/* ============================================================
   RISK
   ============================================================ */

.risk-pill {
    display: inline-block;

    padding: 8px 18px;

    border-radius: 999px;

    font-weight: 800;

    letter-spacing: .5px;

    animation: floatCard 3s ease-in-out infinite;
}

.risk-high {
    background: rgba(239,68,68,.15);

    color: #fca5a5;

    border: 1px solid rgba(239,68,68,.35);
}

.risk-medium {
    background: rgba(245,158,11,.15);

    color: #fcd34d;

    border: 1px solid rgba(245,158,11,.35);
}

.risk-low {
    background: rgba(16,185,129,.15);

    color: #6ee7b7;

    border: 1px solid rgba(16,185,129,.35);
}


/* ============================================================
   FOOTER
   ============================================================ */

.footer {
    text-align: center;

    color: #64748b;

    padding: 15px;

    font-size: 13px;
}

</style>

<style>
/* ===== FINAL UI POLISH ===== */
.block-container { max-width: 1500px; padding-top: 1.25rem; }
section[data-testid="stSidebar"] { min-width: 330px; max-width: 360px; }
section[data-testid="stSidebar"] .stMarkdown p { color: #aeb8ca; }
section[data-testid="stSidebar"] label { font-weight: 650 !important; color: #e7ebf5 !important; }
section[data-testid="stSidebar"] [data-testid="stNumberInput"],
section[data-testid="stSidebar"] [data-testid="stSelectbox"] { margin-bottom: .35rem; }

[data-testid="stMetric"] { min-height: 122px; display:flex; flex-direction:column; justify-content:center; }
[data-testid="stMetricLabel"] { font-size: .92rem !important; }
[data-testid="stMetricValue"] { font-size: 2rem !important; }

.stButton > button[kind="primary"] {
    min-height: 58px;
    border-radius: 16px;
    font-size: 1.05rem;
    box-shadow: 0 12px 30px rgba(79,70,229,.25);
}
.stButton > button[kind="primary"]:hover { transform: translateY(-2px); }
[data-testid="stAlert"] { border-radius: 14px; }

@media (max-width: 900px) {
    section[data-testid="stSidebar"] { min-width: 280px; max-width: 300px; }
    .main-title { font-size: 34px; }
}
</style>
""",
    unsafe_allow_html=True
)




# ============================================================
# STEP 8 - PROFESSIONAL PAGE NAVIGATION
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MODEL_PATH = DATA_DIR / "random_forest_model.pkl"
FEATURE_NAMES_PATH = DATA_DIR / "feature_names.pkl"
MODEL_COLUMNS_PATH = DATA_DIR / "model_columns.pkl"
CUSTOMER_DATA_PATH = DATA_DIR / "customer_churn.csv"

@st.cache_resource
def load_model_step8():
    model = joblib.load(MODEL_PATH)
    feature_names = joblib.load(FEATURE_NAMES_PATH)
    model_columns = joblib.load(MODEL_COLUMNS_PATH)
    return model, feature_names, model_columns

try:
    model, feature_names, model_columns = load_model_step8()
except Exception as e:
    st.error("Unable to load the trained model.")
    st.code(str(e))
    st.stop()

@st.cache_data
def load_customer_data_step8():
    if not CUSTOMER_DATA_PATH.exists():
        return None
    return pd.read_csv(CUSTOMER_DATA_PATH)

customer_data = load_customer_data_step8()
churn_column = None
if customer_data is not None:
    churn_column = next((col for col in customer_data.columns if str(col).strip().lower() in {"churn", "exited", "customer_status"}), None)

st.sidebar.markdown(
    f"<div style='padding:8px 4px 14px 4px;'>"
    f"<div style='font-size:12px;color:#94a3b8;'>SIGNED IN AS</div>"
    f"<div style='font-size:20px;font-weight:800;color:white;'>👤 {CURRENT_USERNAME.title()}</div>"
    f"<div style='font-size:13px;color:#a5b4fc;'>Role: {CURRENT_ROLE}</div></div>",
    unsafe_allow_html=True
)
if st.sidebar.button("🚪 Logout", width="stretch"):
    logout()
st.sidebar.divider()
st.sidebar.markdown("### 🧭 Navigation")
page_options = ["🏠 Dashboard", "👤 Customer Profile", "🌐 Customer 360", "🎯 Customer Segmentation", "📈 Business Intelligence", "🔮 Churn Prediction", "🧪 Model Evaluation"]
if IS_ADMIN:
    page_options += ["🗃️ Prediction History", "📊 Customer Analytics"]
selected_page = st.sidebar.radio("Go to", page_options, label_visibility="collapsed", key="step8_page")
st.sidebar.divider()
st.sidebar.caption("Customer Churn AI · Step 8")

def page_header(title, subtitle):
    render_html(f"""
    <div style='padding:8px 0 22px 0;'>
        <div style='font-size:38px;font-weight:800;letter-spacing:-1px;'>{title}</div>
        <div style='font-size:16px;color:#94a3b8;margin-top:6px;'>{subtitle}</div>
    </div>
    """)


def show_dashboard():
    # ============================================================
    # PATHS
    # ============================================================

    BASE_DIR = Path(__file__).resolve().parent.parent

    DATA_DIR = BASE_DIR / "data"

    MODEL_PATH = DATA_DIR / "random_forest_model.pkl"
    FEATURE_NAMES_PATH = DATA_DIR / "feature_names.pkl"
    MODEL_COLUMNS_PATH = DATA_DIR / "model_columns.pkl"

    CUSTOMER_DATA_PATH = DATA_DIR / "customer_churn.csv"


    # ============================================================
    # LOAD MODEL
    # ============================================================

    @st.cache_resource
    def load_model():

        model = joblib.load(MODEL_PATH)

        feature_names = joblib.load(FEATURE_NAMES_PATH)

        model_columns = joblib.load(MODEL_COLUMNS_PATH)

        return model, feature_names, model_columns


    try:

        model, feature_names, model_columns = load_model()

    except Exception as e:

        st.error("Unable to load the trained model.")

        st.code(str(e))

        st.stop()


    # ============================================================
    # HEADER
    # ============================================================

    render_html(
        """
        <div class="hero-title">
            <span class="hero-icon">AI</span>
            <span class="main-title">Customer Churn Prediction</span>
        </div>
        """
    )

    render_html(
        """
        <div class="subtitle">
            Machine Learning Dashboard powered by Random Forest
        </div>
        """
    )

    render_html(
        """
        <div class="ai-badge">
            <span class="ai-dot"></span>
            AI MODEL ONLINE · RANDOM FOREST
        </div>
        """
    )

    st.divider()



    # ============================================================
    # MODEL PERFORMANCE
    # ============================================================

    st.subheader("📈 Model Performance")

    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:

        st.metric(
            "Accuracy",
            "75.20%"
        )

    with metric2:

        st.metric(
            "ROC-AUC",
            "83.79%"
        )

    with metric3:

        st.metric(
            "F1 Score",
            "62.99%"
        )

    with metric4:

        render_html(
            """
            <div class="custom-metric-card">

                <div class="custom-metric-label">
                    🤖 Model
                </div>

                <div class="custom-metric-value">
                    Random Forest
                </div>

                <div class="model-status">
                    ● Active
                </div>

            </div>
            """
        )


    st.divider()


    # ============================================================
    # LOAD CUSTOMER DATA
    # ============================================================

    @st.cache_data
    def load_customer_data():

        if not CUSTOMER_DATA_PATH.exists():
            return None

        return pd.read_csv(CUSTOMER_DATA_PATH)


    customer_data = load_customer_data()


    # ============================================================
    # CHURN COLUMN
    # ============================================================

    churn_column = None

    if customer_data is not None:

        churn_column = next(
            (
                col
                for col in customer_data.columns
                if str(col).strip().lower()
                in {
                    "churn",
                    "exited",
                    "customer_status"
                }
            ),
            None
        )


    # ============================================================
    # DATASET ANALYTICS
    # ============================================================

    st.subheader("📊 Customer Churn Analytics")

    st.caption(
        "Overview of the customer dataset used for the churn prediction project."
    )


    if customer_data is None:

        st.info(
            "Dataset analytics are unavailable because "
            "customer_churn.csv was not found in the data folder."
        )

    elif churn_column is None:

        st.info(
            "The dataset was loaded, but a supported churn column "
            "was not found. Expected a column such as 'Churn'."
        )

    else:

        total_customers = len(customer_data)

        churn_values = (
            customer_data[churn_column]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        churn_yes = churn_values.isin(
            {
                "yes",
                "1",
                "true",
                "churned",
                "exited"
            }
        ).sum()

        churn_no = total_customers - churn_yes

        churn_rate = (
            churn_yes / total_customers * 100
            if total_customers > 0
            else 0
        )

        analytics_col1, analytics_col2, analytics_col3, analytics_col4 = st.columns(4)

        with analytics_col1:

            st.metric(
                "Total Customers",
                f"{total_customers:,}"
            )

        with analytics_col2:

            st.metric(
                "Churned Customers",
                f"{churn_yes:,}"
            )

        with analytics_col3:

            st.metric(
                "Retained Customers",
                f"{churn_no:,}"
            )

        with analytics_col4:

            st.metric(
                "Dataset Churn Rate",
                f"{churn_rate:.2f}%"
            )


        # ========================================================
        # CHURN DISTRIBUTION
        # ========================================================

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:

            churn_chart_data = pd.DataFrame(
                {
                    "Customer Status": [
                        "Retained",
                        "Churned"
                    ],

                    "Customers": [
                        churn_no,
                        churn_yes
                    ]
                }
            )

            fig_churn_distribution = px.pie(
                churn_chart_data,

                names="Customer Status",

                values="Customers",

                hole=0.55,

                title="Customer Churn Distribution"
            )

            fig_churn_distribution.update_layout(
                height=430,

                plot_bgcolor="rgba(0,0,0,0)",

                paper_bgcolor="rgba(0,0,0,0)",

                font=dict(
                    color="#f8fafc"
                ),

                legend=dict(
                    font=dict(
                        color="#f8fafc"
                    )
                )
            )

            st.plotly_chart(
                fig_churn_distribution,
                width="stretch"
            )


        with chart_col2:

            status_counts = (
                churn_values
                .value_counts()
                .reset_index()
            )

            status_counts.columns = [
                "Status",
                "Customers"
            ]

            status_counts["Status"] = (
                status_counts["Status"]
                .str.title()
            )

            fig_status = px.bar(
                status_counts,

                x="Status",

                y="Customers",

                text="Customers",

                title="Customer Status Count"
            )

            fig_status.update_traces(
                textposition="outside"
            )

            fig_status.update_layout(
                height=430,

                plot_bgcolor="rgba(0,0,0,0)",

                paper_bgcolor="rgba(0,0,0,0)",

                font=dict(
                    color="#f8fafc"
                ),

                xaxis_title="",

                yaxis_title="Customers",

                showlegend=False,

                margin=dict(
                    l=50,
                    r=30,
                    t=70,
                    b=60
                )
            )

            st.plotly_chart(
                fig_status,
                width="stretch"
            )


        # ========================================================
        # CONTRACT ANALYSIS
        # ========================================================

        contract_column = next(
            (
                col
                for col in customer_data.columns
                if str(col).strip().lower() == "contract"
            ),
            None
        )

        if contract_column is not None:

            st.markdown("### 📋 Churn by Contract")

            contract_analysis = customer_data.copy()

            contract_analysis["_churn_flag"] = (
                churn_values
                .isin(
                    {
                        "yes",
                        "1",
                        "true",
                        "churned",
                        "exited"
                    }
                )
                .astype(int)
            )

            contract_summary = (
                contract_analysis
                .groupby(
                    contract_column,
                    dropna=False
                )
                .agg(
                    Customers=(
                        contract_column,
                        "size"
                    ),

                    Churned=(
                        "_churn_flag",
                        "sum"
                    )
                )
                .reset_index()
            )

            contract_summary["Churn Rate (%)"] = (
                contract_summary["Churned"]
                /
                contract_summary["Customers"]
                * 100
            ).round(2)

            contract_summary = contract_summary.rename(
                columns={
                    contract_column: "Contract"
                }
            )

            contract_chart = px.bar(
                contract_summary,

                x="Contract",

                y="Churn Rate (%)",

                text="Churn Rate (%)",

                title="Churn Rate by Contract Type"
            )

            contract_chart.update_traces(
                texttemplate="%{text:.2f}%",

                textposition="outside"
            )

            contract_chart.update_layout(
                height=430,

                plot_bgcolor="rgba(0,0,0,0)",

                paper_bgcolor="rgba(0,0,0,0)",

                font=dict(
                    color="#f8fafc"
                ),

                yaxis=dict(
                    title="Churn Rate (%)",

                    range=[0, 100]
                ),

                xaxis_title="Contract",

                showlegend=False
            )

            st.plotly_chart(
                contract_chart,
                width="stretch"
            )

            st.dataframe(
                contract_summary,

                width="stretch",

                hide_index=True
            )


    st.divider()



def show_prediction():
    page_header("🔮 Churn Prediction", "Enter customer details and generate a Random Forest churn prediction.")
    st.sidebar.title("👤 Customer Profile")
    st.sidebar.markdown("Create a customer profile before entering prediction details.")
    customer_id = st.sidebar.text_input(
        "Customer ID",
        value="CUS-1001",
        max_chars=30
    )

    customer_name = st.sidebar.text_input(
        "Customer Name",
        value="Rahul Kumar",
        max_chars=60
    )

    profile_age = st.sidebar.number_input(
        "Age",
        min_value=18,
        max_value=100,
        value=28
    )

    profile_location = st.sidebar.text_input(
        "Location",
        value="Bengaluru",
        max_chars=60
    )

    customer_since = st.sidebar.selectbox(
        "Customer Since",
        ["2026", "2025", "2024", "2023", "2022", "2021", "2020"]
    )

    st.sidebar.divider()
    st.sidebar.subheader("📋 Customer Details")
    st.sidebar.markdown(
        "Enter account and service information below."
    )


    # ============================================================
    # NUMERICAL INPUTS
    # ============================================================

    tenure = st.sidebar.number_input(
        "Tenure (months)",

        min_value=0,

        max_value=100,

        value=5
    )


    monthly_charges = st.sidebar.number_input(
        "Monthly Charges",

        min_value=0.0,

        max_value=200.0,

        value=70.0
    )


    total_charges = st.sidebar.number_input(
        "Total Charges",

        min_value=0.0,

        max_value=10000.0,

        value=350.0
    )


    # ============================================================
    # CUSTOMER INFORMATION
    # ============================================================

    gender = st.sidebar.selectbox(
        "Gender",

        [
            "Male",
            "Female"
        ]
    )


    contract = st.sidebar.selectbox(
        "Contract",

        [
            "Month-to-month",
            "One year",
            "Two year"
        ]
    )


    internet_service = st.sidebar.selectbox(
        "Internet Service",

        [
            "DSL",
            "Fiber optic",
            "No internet service"
        ]
    )


    payment_method = st.sidebar.selectbox(
        "Payment Method",

        [
            "Electronic check",
            "Mailed check",
            "Bank transfer (automatic)",
            "Credit card (automatic)"
        ]
    )


    online_security = st.sidebar.selectbox(
        "Online Security",

        [
            "Yes",
            "No",
            "No internet service"
        ]
    )


    tech_support = st.sidebar.selectbox(
        "Tech Support",

        [
            "Yes",
            "No",
            "No internet service"
        ]
    )


    # ============================================================
    # CUSTOMER PROFILE PREVIEW
    # ============================================================

    profile_initial = (customer_name.strip()[:1] or "C").upper()

    render_html(
        f"""
        <div class="profile-card">
            <div class="profile-avatar">{profile_initial}</div>
            <div class="profile-name">{customer_name}</div>
            <div class="profile-meta">Customer ID · {customer_id} &nbsp;•&nbsp; {profile_location}</div>
            <div class="profile-grid">
                <div class="profile-item">
                    <div class="profile-label">Age</div>
                    <div class="profile-value">{profile_age} years</div>
                </div>
                <div class="profile-item">
                    <div class="profile-label">Customer Since</div>
                    <div class="profile-value">{customer_since}</div>
                </div>
                <div class="profile-item">
                    <div class="profile-label">Tenure</div>
                    <div class="profile-value">{tenure} months</div>
                </div>
                <div class="profile-item">
                    <div class="profile-label">Contract</div>
                    <div class="profile-value">{contract}</div>
                </div>
            </div>
        </div>
        """
    )


    # ============================================================
    # CREATE INPUT DATAFRAME
    # ============================================================

    def create_input_dataframe():

        input_data = pd.DataFrame(
            np.zeros(
                (
                    1,
                    len(model_columns)
                )
            ),

            columns=model_columns
        )


        # --------------------------------------------------------
        # Numerical features
        # --------------------------------------------------------

        if "tenure" in input_data.columns:

            input_data["tenure"] = tenure

        if "MonthlyCharges" in input_data.columns:

            input_data["MonthlyCharges"] = monthly_charges

        if "TotalCharges" in input_data.columns:

            input_data["TotalCharges"] = total_charges


        # --------------------------------------------------------
        # Gender
        # --------------------------------------------------------

        if gender == "Male":

            if "gender_Male" in input_data.columns:

                input_data["gender_Male"] = 1


        # --------------------------------------------------------
        # Contract
        # --------------------------------------------------------

        if contract == "One year":

            if "Contract_One year" in input_data.columns:

                input_data["Contract_One year"] = 1

        elif contract == "Two year":

            if "Contract_Two year" in input_data.columns:

                input_data["Contract_Two year"] = 1


        # --------------------------------------------------------
        # Internet Service
        # --------------------------------------------------------

        if internet_service == "Fiber optic":

            if "InternetService_Fiber optic" in input_data.columns:

                input_data["InternetService_Fiber optic"] = 1

        elif internet_service == "No internet service":

            if "InternetService_No internet service" in input_data.columns:

                input_data["InternetService_No internet service"] = 1


        # --------------------------------------------------------
        # Payment Method
        # --------------------------------------------------------

        if payment_method == "Electronic check":

            if "PaymentMethod_Electronic check" in input_data.columns:

                input_data["PaymentMethod_Electronic check"] = 1

        elif payment_method == "Mailed check":

            if "PaymentMethod_Mailed check" in input_data.columns:

                input_data["PaymentMethod_Mailed check"] = 1

        elif payment_method == "Credit card (automatic)":

            if "PaymentMethod_Credit card (automatic)" in input_data.columns:

                input_data[
                    "PaymentMethod_Credit card (automatic)"
                ] = 1

        elif payment_method == "Bank transfer (automatic)":

            if "PaymentMethod_Bank transfer (automatic)" in input_data.columns:

                input_data[
                    "PaymentMethod_Bank transfer (automatic)"
                ] = 1


        # --------------------------------------------------------
        # Online Security
        # --------------------------------------------------------

        if online_security == "Yes":

            if "OnlineSecurity_Yes" in input_data.columns:

                input_data["OnlineSecurity_Yes"] = 1

        elif online_security == "No internet service":

            if "OnlineSecurity_No internet service" in input_data.columns:

                input_data[
                    "OnlineSecurity_No internet service"
                ] = 1


        # --------------------------------------------------------
        # Tech Support
        # --------------------------------------------------------

        if tech_support == "Yes":

            if "TechSupport_Yes" in input_data.columns:

                input_data["TechSupport_Yes"] = 1

        elif tech_support == "No internet service":

            if "TechSupport_No internet service" in input_data.columns:

                input_data[
                    "TechSupport_No internet service"
                ] = 1


        return input_data


    # ============================================================
    # EXPLAINABLE AI - LOCAL WHAT-IF ANALYSIS
    # ============================================================

    def get_churn_probability(dataframe):
        """Return the model's probability for the positive/churn class."""

        probabilities = model.predict_proba(dataframe)[0]
        classes = list(model.classes_) if hasattr(model, "classes_") else [0, 1]

        if 1 in classes:
            churn_index = classes.index(1)
        elif "1" in classes:
            churn_index = classes.index("1")
        else:
            churn_index = min(1, len(probabilities) - 1)

        return float(probabilities[churn_index] * 100)


    def create_local_explanation(input_df):
        """Create a local what-if explanation; this is model sensitivity, not causality."""

        original_probability = get_churn_probability(input_df)
        explanations = []

        numeric_baselines = {
            "tenure": 24,
            "MonthlyCharges": 70.0,
            "TotalCharges": 1500.0
        }

        numeric_labels = {
            "tenure": "Tenure",
            "MonthlyCharges": "Monthly Charges",
            "TotalCharges": "Total Charges"
        }

        for feature, baseline_value in numeric_baselines.items():
            if feature not in input_df.columns:
                continue

            current_value = input_df.iloc[0][feature]
            changed_df = input_df.copy()
            changed_df.loc[changed_df.index[0], feature] = baseline_value
            changed_probability = get_churn_probability(changed_df)

            explanations.append({
                "Feature": numeric_labels[feature],
                "Current Value": current_value,
                "Baseline Value": baseline_value,
                "Probability Change": original_probability - changed_probability
            })

        categorical_groups = {
            "Gender": [c for c in model_columns if str(c).startswith("gender_")],
            "Contract": [c for c in model_columns if str(c).startswith("Contract_")],
            "Internet Service": [c for c in model_columns if str(c).startswith("InternetService_")],
            "Payment Method": [c for c in model_columns if str(c).startswith("PaymentMethod_")],
            "Online Security": [c for c in model_columns if str(c).startswith("OnlineSecurity_")],
            "Tech Support": [c for c in model_columns if str(c).startswith("TechSupport_")]
        }

        for group_name, group_columns in categorical_groups.items():
            if not group_columns:
                continue

            active_columns = []
            for column in group_columns:
                try:
                    if float(input_df.iloc[0][column]) == 1:
                        active_columns.append(column)
                except (TypeError, ValueError, KeyError):
                    pass

            if not active_columns:
                continue

            changed_df = input_df.copy()
            for column in group_columns:
                changed_df.loc[changed_df.index[0], column] = 0

            changed_probability = get_churn_probability(changed_df)
            active_name = active_columns[0]
            active_value = active_name.split("_", 1)[1] if "_" in active_name else active_name

            explanations.append({
                "Feature": group_name,
                "Current Value": active_value,
                "Baseline Value": "Encoded baseline",
                "Probability Change": original_probability - changed_probability
            })

        explanation_df = pd.DataFrame(explanations)

        if explanation_df.empty:
            return explanation_df

        # Streamlit/PyArrow requires a consistent dtype for each dataframe column.
        # "Current Value" contains both numbers and strings because this table
        # combines numeric features with categorical features.
        explanation_df["Current Value"] = explanation_df["Current Value"].astype(str)
        explanation_df["Baseline Value"] = explanation_df["Baseline Value"].astype(str)
        explanation_df["Probability Change"] = pd.to_numeric(
            explanation_df["Probability Change"], errors="coerce"
        ).fillna(0.0)

        explanation_df["Absolute Impact"] = explanation_df["Probability Change"].abs()
        explanation_df = (
            explanation_df
            .sort_values("Absolute Impact", ascending=False)
            .drop(columns=["Absolute Impact"])
            .head(8)
        )

        return explanation_df


    # ============================================================
    # PREDICT BUTTON
    # ============================================================

    st.subheader("🔮 Customer Prediction")

    predict_button = st.button(
        "🚀 Predict Customer Churn",

        type="primary",

        width="stretch"
    )


    # ============================================================
    # PREDICTION
    # ============================================================

    if predict_button:

        try:

            input_df = create_input_dataframe()


            # ====================================================
            # PREDICTION
            # ====================================================

            prediction = model.predict(
                input_df
            )[0]


            # ====================================================
            # PROBABILITY
            # ====================================================

            probabilities = model.predict_proba(
                input_df
            )[0]


            # Safely find probability for class 1
            if hasattr(model, "classes_"):

                classes = list(model.classes_)

                if 1 in classes:

                    churn_index = classes.index(1)

                elif "1" in classes:

                    churn_index = classes.index("1")

                else:

                    churn_index = 1

            else:

                churn_index = 1


            churn_probability = (
                probabilities[churn_index] * 100
            )

            no_churn_probability = (
                100 - churn_probability
            )


            # ====================================================
            # RISK LEVEL
            # ====================================================

            if churn_probability >= 70:

                risk_level = "HIGH"

            elif churn_probability >= 40:

                risk_level = "MEDIUM"

            else:

                risk_level = "LOW"


            st.divider()


            # ====================================================
            # RESULT
            # ====================================================

            st.subheader("📋 Prediction Result")

            prediction_value = str(prediction).lower()

            if prediction_value in {
                "1",
                "true",
                "yes",
                "churn",
                "churned"
            }:

                st.error(
                    "🔴 CUSTOMER WILL CHURN",

                    icon="⚠️"
                )

            else:

                st.success(
                    "🟢 CUSTOMER WILL NOT CHURN",

                    icon="✅"
                )


            # ====================================================
            # PROBABILITY CARDS
            # ====================================================

            col1, col2 = st.columns(2)

            with col1:

                st.metric(
                    "No Churn Probability",

                    f"{no_churn_probability:.2f}%"
                )

            with col2:

                st.metric(
                    "Churn Probability",

                    f"{churn_probability:.2f}%"
                )


            # ====================================================
            # RISK LEVEL
            # ====================================================

            st.subheader("🎯 Churn Risk Level")

            risk_col1, risk_col2 = st.columns(2)

            with risk_col1:

                st.metric(
                    "Risk Level",

                    risk_level
                )

            with risk_col2:

                st.metric(
                    "Churn Probability",

                    f"{churn_probability:.2f}%"
                )


            risk_class = (
                "risk-high"
                if risk_level == "HIGH"
                else
                "risk-medium"
                if risk_level == "MEDIUM"
                else
                "risk-low"
            )


            render_html(
                f"""
                <div class="risk-pill {risk_class}">
                    🎯 {risk_level} RISK ·
                    {churn_probability:.2f}% CHURN PROBABILITY
                </div>
                """
            )


            # ====================================================
            # RISK MESSAGE
            # ====================================================

            if risk_level == "HIGH":

                st.error(
                    "⚠️ High churn risk. Customer may be likely to leave."
                )

            elif risk_level == "MEDIUM":

                st.warning(
                    "⚠️ Medium churn risk. Customer should be monitored."
                )

            else:

                st.success(
                    "✅ Low churn risk. Customer has a lower predicted probability of leaving."
                )


            # ====================================================
            # CHURN RISK ANALYSIS
            # ====================================================

            st.subheader("🎯 Churn Risk Analysis")


            if risk_level == "HIGH":

                risk_color = "#ef4444"

                risk_icon = "🔴"

                risk_message = (
                    "Customer has a high predicted probability of churn."
                )

                recommendations = [
                    "Contact the customer proactively",
                    "Offer a suitable retention plan",
                    "Review contract and pricing",
                    "Check customer support issues"
                ]


            elif risk_level == "MEDIUM":

                risk_color = "#f59e0b"

                risk_icon = "🟠"

                risk_message = (
                    "Customer has a moderate predicted probability of churn."
                )

                recommendations = [
                    "Monitor customer activity",
                    "Review contract details",
                    "Consider a loyalty offer",
                    "Improve customer engagement"
                ]


            else:

                risk_color = "#22c55e"

                risk_icon = "🟢"

                risk_message = (
                    "Customer has a lower predicted probability of churn."
                )

                recommendations = [
                    "Maintain good customer service",
                    "Continue customer engagement",
                    "Consider loyalty benefits",
                    "Monitor future customer activity"
                ]


            # ====================================================
            # RISK CARD
            # ====================================================

            render_html(
                f"""
                <div style="
                    padding: 28px;
                    border-radius: 20px;
                    border: 1px solid {risk_color};
                    background:
                        linear-gradient(
                            135deg,
                            rgba(255,255,255,0.06),
                            rgba(255,255,255,0.02)
                        );
                    box-shadow:
                        0 0 25px {risk_color}22;
                    text-align: center;
                    margin: 10px 0 25px 0;
                ">

                    <div style="
                        font-size: 22px;
                        margin-bottom: 8px;
                        color: white;
                    ">
                        {risk_icon} CHURN RISK
                    </div>

                    <div style="
                        font-size: 38px;
                        font-weight: 800;
                        color: {risk_color};
                        margin-bottom: 8px;
                    ">
                        {risk_level}
                    </div>

                    <div style="
                        font-size: 26px;
                        font-weight: 700;
                        color: white;
                    ">
                        {churn_probability:.2f}%
                    </div>

                    <div style="
                        color: #a8b0c2;
                        margin-top: 8px;
                    ">
                        Predicted probability of customer churn
                    </div>

                </div>
                """
            )


            st.markdown("**Risk Probability**")

            st.progress(
                min(
                    int(churn_probability),
                    100
                )
            )

            st.write(
                risk_message
            )


            # ====================================================
            # SUGGESTED ACTIONS
            # ====================================================

            st.markdown("### 💡 Suggested Actions")

            action_col1, action_col2 = st.columns(2)

            with action_col1:

                for action in recommendations[:2]:

                    st.markdown(
                        f"• {action}"
                    )

            with action_col2:

                for action in recommendations[2:]:

                    st.markdown(
                        f"• {action}"
                    )


            # ====================================================
            # STEP 5 - SAVE PREDICTION
            # ====================================================

            save_prediction_history(
                customer_id=customer_id,
                customer_name=customer_name,
                age=profile_age,
                location=profile_location,
                customer_since=customer_since,
                tenure=tenure,
                gender=gender,
                contract=contract,
                internet_service=internet_service,
                payment_method=payment_method,
                online_security=online_security,
                tech_support=tech_support,
                monthly_charges=monthly_charges,
                total_charges=total_charges,
                prediction=prediction,
                churn_probability=churn_probability,
                no_churn_probability=no_churn_probability,
                risk_level=risk_level
            )

            st.success(
                "💾 Prediction saved to Prediction History."
            )


            # ====================================================
            # PROBABILITY CHART
            # ====================================================

            st.subheader("📊 Prediction Probability")

            probability_data = pd.DataFrame(
                {
                    "Result": [
                        "Will Not Churn",
                        "Will Churn"
                    ],

                    "Probability": [
                        no_churn_probability,
                        churn_probability
                    ]
                }
            )


            fig_probability = px.bar(
                probability_data,

                x="Result",

                y="Probability",

                text="Probability",

                title="Customer Churn Probability"
            )


            fig_probability.update_yaxes(
                range=[0, 100],

                dtick=20,

                title="Probability (%)",

                fixedrange=True
            )


            fig_probability.update_traces(
                texttemplate="%{text:.2f}%",

                textposition="outside",

                textfont=dict(
                    size=16,
                    color="white"
                ),

                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Probability: %{y:.2f}%"
                    "<extra></extra>"
                )
            )


            fig_probability.update_layout(
                height=470,

                title=dict(
                    text="Customer Churn Probability",

                    font=dict(
                        size=22,
                        color="#ffffff"
                    ),

                    x=0.02
                ),

                xaxis=dict(
                    title="",

                    tickfont=dict(
                        size=14,
                        color="#d1d5db"
                    )
                ),

                yaxis=dict(
                    title="Probability (%)",

                    range=[0, 100],

                    dtick=20,

                    tickfont=dict(
                        size=13,
                        color="#d1d5db"
                    ),

                    gridcolor="rgba(255,255,255,0.12)"
                ),

                plot_bgcolor="rgba(0,0,0,0)",

                paper_bgcolor="rgba(0,0,0,0)",

                showlegend=False,

                margin=dict(
                    l=70,
                    r=30,
                    t=80,
                    b=70
                )
            )


            st.plotly_chart(
                fig_probability,

                width="stretch"
            )


            # ====================================================
            # EXPLAINABLE AI
            # ====================================================

            st.divider()
            st.subheader("🧠 Why Did the Model Make This Prediction?")
            st.caption(
                "Local what-if explanation: each feature/group is compared with a baseline. "
                "These values describe model behavior and are not causal effects."
            )

            try:
                explanation_df = create_local_explanation(input_df)

                if not explanation_df.empty:
                    explanation_display = explanation_df.copy()
                    explanation_display["Probability Change"] = explanation_display["Probability Change"].round(2)
                    explanation_display = explanation_display.rename(
                        columns={"Probability Change": "Model Impact (%)"}
                    )

                    chart_explanation = explanation_df.sort_values(
                        "Probability Change", ascending=True
                    )

                    fig_explanation = px.bar(
                        chart_explanation,
                        x="Probability Change",
                        y="Feature",
                        orientation="h",
                        text="Probability Change",
                        title="Local Feature Impact on Churn Probability"
                    )

                    fig_explanation.update_traces(
                        texttemplate="%{text:.2f}%",
                        textposition="outside"
                    )

                    fig_explanation.update_layout(
                        height=480,
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)",
                        font=dict(color="#f8fafc"),
                        xaxis_title="Change in Churn Probability (%)",
                        yaxis_title="",
                        showlegend=False,
                        margin=dict(l=30, r=90, t=80, b=50)
                    )

                    st.plotly_chart(
                        fig_explanation,
                        width="stretch"
                    )

                    st.markdown("### 📋 Prediction Explanation Details")
                    st.dataframe(
                        explanation_display,
                        width="stretch",
                        hide_index=True
                    )

                    strongest = explanation_df.iloc[0]
                    strongest_feature = strongest["Feature"]
                    strongest_impact = float(strongest["Probability Change"])

                    st.info(
                        f"🔎 Strongest local factor: **{strongest_feature}**. "
                        f"Replacing it with the baseline changes the model's predicted "
                        f"churn probability by **{strongest_impact:+.2f} percentage points**."
                    )
                else:
                    st.info("No local explanation could be generated for this customer.")

            except Exception as explanation_error:
                st.warning("Local explanation is currently unavailable.")
                st.caption(str(explanation_error))


            # ====================================================
            # CUSTOMER PROFILE + SUMMARY
            # ====================================================

            st.subheader("👤 Customer Profile")

            render_html(
                f"""
                <div class="profile-card">
                    <div class="profile-avatar">{profile_initial}</div>
                    <div class="profile-name">{customer_name}</div>
                    <div class="profile-meta">{customer_id} · {profile_location}</div>
                    <div class="profile-grid">
                        <div class="profile-item">
                            <div class="profile-label">Age</div>
                            <div class="profile-value">{profile_age} years</div>
                        </div>
                        <div class="profile-item">
                            <div class="profile-label">Since</div>
                            <div class="profile-value">{customer_since}</div>
                        </div>
                        <div class="profile-item">
                            <div class="profile-label">Gender</div>
                            <div class="profile-value">{gender}</div>
                        </div>
                        <div class="profile-item">
                            <div class="profile-label">Contract</div>
                            <div class="profile-value">{contract}</div>
                        </div>
                    </div>
                </div>
                """
            )

            st.subheader("📋 Account Summary")

            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

            with summary_col1:
                st.metric("Tenure", f"{tenure} months")

            with summary_col2:
                st.metric("Monthly Charges", f"${monthly_charges:.2f}")

            with summary_col3:
                st.metric("Total Charges", f"${total_charges:.2f}")

            with summary_col4:
                st.metric("Internet", internet_service)

            summary_col1, summary_col2, summary_col3 = st.columns(3)

            with summary_col1:
                st.write("**Payment Method**")
                st.write(payment_method)

            with summary_col2:
                st.write("**Online Security**")
                st.write(online_security)

            with summary_col3:
                st.write("**Tech Support**")
                st.write(tech_support)


            # ====================================================
            # DOWNLOAD REPORT
            # ====================================================

            st.divider()

            st.subheader("📥 Download Prediction Report")


            report_text = f"""
    CUSTOMER CHURN PREDICTION REPORT
    ========================================

    PREDICTION RESULT
    -----------------
    Prediction: {
        "Customer Will Churn"
        if prediction_value in {
            "1",
            "true",
            "yes",
            "churn",
            "churned"
        }
        else
        "Customer Will Not Churn"
    }

    Churn Probability: {churn_probability:.2f}%
    No-Churn Probability: {no_churn_probability:.2f}%
    Risk Level: {risk_level}


    CUSTOMER PROFILE
    ----------------
    Customer ID: {customer_id}
    Customer Name: {customer_name}
    Age: {profile_age}
    Location: {profile_location}
    Customer Since: {customer_since}

    CUSTOMER DETAILS
    ----------------
    Tenure: {tenure} months
    Gender: {gender}
    Contract: {contract}
    Monthly Charges: ${monthly_charges:.2f}
    Total Charges: ${total_charges:.2f}
    Internet Service: {internet_service}
    Payment Method: {payment_method}
    Online Security: {online_security}
    Tech Support: {tech_support}


    SUGGESTED ACTIONS
    -----------------
    """


            for number, action in enumerate(
                recommendations,
                start=1
            ):

                report_text += (
                    f"{number}. {action}\n"
                )


            report_text += """

    NOTE
    ----
    This report contains the Random Forest model prediction
    for the customer information entered in the dashboard.

    Model predictions are probabilistic and should be considered
    together with business context and customer information.
    """


            download_col1, download_col2 = st.columns(
                [1, 2]
            )


            with download_col1:

                st.download_button(
                    label="📄 Download Report",

                    data=report_text,

                    file_name=(
                        "customer_churn_prediction_report.txt"
                    ),

                    mime="text/plain",

                    width="stretch"
                )


            with download_col2:

                st.info(
                    "Download a text report containing the prediction, "
                    "churn probability, risk level, customer details, "
                    "and suggested actions."
                )


            # ====================================================
            # FEATURE IMPORTANCE
            # ====================================================

            st.divider()

            st.subheader("🧠 Important Features")


            try:

                importances = model.feature_importances_

                if len(importances) != len(model_columns):

                    st.warning(
                        "Feature importance cannot be displayed because "
                        "the number of model features does not match "
                        "the saved model columns."
                    )

                else:

                    feature_importance_df = pd.DataFrame(
                        {
                            "Feature": model_columns,

                            "Importance": importances
                        }
                    )


                    feature_importance_df = (
                        feature_importance_df
                        .sort_values(
                            by="Importance",

                            ascending=False
                        )
                    )


                    top_features = (
                        feature_importance_df
                        .head(10)
                        .copy()
                    )


                    chart_data = (
                        top_features
                        .sort_values(
                            by="Importance",

                            ascending=True
                        )
                    )


                    fig_features = px.bar(
                        chart_data,

                        x="Importance",

                        y="Feature",

                        orientation="h",

                        text="Importance",

                        title=(
                            "Top 10 Features "
                            "Influencing Customer Churn"
                        )
                    )


                    fig_features.update_traces(
                        texttemplate="%{text:.3f}",

                        textposition="outside"
                    )


                    fig_features.update_layout(
                        plot_bgcolor="rgba(0,0,0,0)",

                        paper_bgcolor="rgba(0,0,0,0)",

                        font=dict(
                            color="#f8fafc"
                        ),

                        height=520,

                        xaxis_title="Feature Importance",

                        yaxis_title="",

                        showlegend=False,

                        margin=dict(
                            l=20,
                            r=80,
                            t=70,
                            b=20
                        )
                    )


                    st.plotly_chart(
                        fig_features,

                        width="stretch"
                    )


                    display_features = (
                        top_features
                        .copy()
                    )


                    display_features["Importance"] = (
                        display_features["Importance"] * 100
                    ).round(2)


                    display_features = (
                        display_features
                        .rename(
                            columns={
                                "Importance":
                                "Importance (%)"
                            }
                        )
                    )


                    st.markdown(
                        "### 📋 Feature Importance Details"
                    )


                    st.dataframe(
                        display_features,

                        width="stretch",

                        hide_index=True
                    )

            except Exception as feature_error:

                st.info(
                    "Feature importance is not available."
                )


        except Exception as e:

            st.error(
                "Prediction failed."
            )

            st.exception(e)


    # ============================================================

def show_evaluation():
    page_header("🧪 Model Evaluation", "Review classification performance, confusion matrix, and ROC-AUC analysis.")
    # MODEL EVALUATION
    # ============================================================

    st.divider()

    st.subheader("🧪 Model Evaluation")

    st.caption(
        "Evaluation results from the Random Forest test-set assessment."
    )


    # ============================================================
    # CONFUSION MATRIX
    # ============================================================

    confusion_matrix = np.array(
        [
            [761, 272],
            [77, 297]
        ]
    )

    actual_labels = [
        "No Churn",
        "Churn"
    ]

    predicted_labels = [
        "No Churn",
        "Churn"
    ]


    cm_col1, cm_col2 = st.columns(
        [1.15, 1]
    )


    with cm_col1:

        fig_cm = px.imshow(
            confusion_matrix,

            x=predicted_labels,

            y=actual_labels,

            text_auto=True,

            aspect="auto",

            title="Confusion Matrix"
        )


        fig_cm.update_layout(
            height=430,

            plot_bgcolor="rgba(0,0,0,0)",

            paper_bgcolor="rgba(0,0,0,0)",

            font=dict(
                color="#f8fafc"
            ),

            xaxis_title="Predicted",

            yaxis_title="Actual",

            margin=dict(
                l=40,
                r=30,
                t=70,
                b=40
            )
        )


        st.plotly_chart(
            fig_cm,

            width="stretch"
        )


    with cm_col2:

        tn, fp, fn, tp = (
            confusion_matrix.ravel()
        )


        evaluation_accuracy = (
            (tn + tp)
            /
            confusion_matrix.sum()
            * 100
        )


        precision = (
            tp
            /
            (tp + fp)
            * 100
            if (tp + fp)
            else 0
        )


        recall = (
            tp
            /
            (tp + fn)
            * 100
            if (tp + fn)
            else 0
        )


        f1_score = (
            2
            *
            precision
            *
            recall
            /
            (precision + recall)

            if (precision + recall)

            else 0
        )


        st.markdown(
            "### 📋 Classification Metrics"
        )


        eval_col1, eval_col2 = st.columns(2)


        with eval_col1:

            st.metric(
                "Accuracy",

                f"{evaluation_accuracy:.2f}%"
            )

            st.metric(
                "Precision",

                f"{precision:.2f}%"
            )


        with eval_col2:

            st.metric(
                "Recall",

                f"{recall:.2f}%"
            )

            st.metric(
                "F1 Score",

                f"{f1_score:.2f}%"
            )


        st.markdown("### 🔎 Confusion Matrix Details")

        cm1, cm2 = st.columns(2)
        with cm1:
            render_html(
                f"""
                <div class="custom-metric-card">
                    <div class="custom-metric-label">True Negative</div>
                    <div class="custom-metric-value">{tn:,}</div>
                </div>
                """
            )
            render_html(
                f"""
                <div class="custom-metric-card" style="margin-top:12px;">
                    <div class="custom-metric-label">False Negative</div>
                    <div class="custom-metric-value">{fn:,}</div>
                </div>
                """
            )

        with cm2:
            render_html(
                f"""
                <div class="custom-metric-card">
                    <div class="custom-metric-label">False Positive</div>
                    <div class="custom-metric-value">{fp:,}</div>
                </div>
                """
            )
            render_html(
                f"""
                <div class="custom-metric-card" style="margin-top:12px;">
                    <div class="custom-metric-label">True Positive</div>
                    <div class="custom-metric-value">{tp:,}</div>
                </div>
                """
            )


    st.info(
        "The confusion matrix shows how the model classified "
        "the evaluation samples. The positive class represents "
        "customers who churned."
    )


    # ============================================================
    # ROC CURVE & AUC
    # ============================================================

    st.divider()

    st.subheader("📈 ROC Curve & AUC Analysis")

    st.caption(
        "ROC-AUC visualization based on the customer churn dataset "
        "and the trained Random Forest model."
    )


    try:

        from sklearn.metrics import (
            roc_curve,
            roc_auc_score
        )


        if (
            customer_data is None
            or churn_column is None
        ):

            st.info(
                "ROC curve is unavailable because the customer "
                "dataset or churn column was not found."
            )

        else:

            roc_data = customer_data.copy()


            # ----------------------------------------------------
            # Convert numeric columns
            # ----------------------------------------------------

            for numeric_column in [
                "tenure",
                "MonthlyCharges",
                "TotalCharges"
            ]:

                if numeric_column in roc_data.columns:

                    roc_data[numeric_column] = pd.to_numeric(
                        roc_data[numeric_column],

                        errors="coerce"
                    )


            # ----------------------------------------------------
            # Remove missing target
            # ----------------------------------------------------

            roc_data = roc_data.dropna(
                subset=[churn_column]
            )


            # ----------------------------------------------------
            # Target encoding
            # ----------------------------------------------------

            target_values = (
                roc_data[churn_column]
                .astype(str)
                .str.strip()
                .str.lower()
            )


            y_true = (
                target_values
                .isin(
                    {
                        "yes",
                        "1",
                        "true",
                        "churned",
                        "exited"
                    }
                )
                .astype(int)
            )


            # ----------------------------------------------------
            # Feature data
            # ----------------------------------------------------

            X_roc = roc_data.drop(
                columns=[churn_column]
            )


            # ----------------------------------------------------
            # Convert object columns to numeric
            # ----------------------------------------------------

            X_roc = pd.get_dummies(
                X_roc,

                drop_first=True
            )


            # ----------------------------------------------------
            # Match exact model columns
            # ----------------------------------------------------

            X_roc = X_roc.reindex(
                columns=model_columns,

                fill_value=0
            )


            # ----------------------------------------------------
            # Convert everything to numeric
            # ----------------------------------------------------

            X_roc = X_roc.apply(
                pd.to_numeric,

                errors="coerce"
            )


            # ----------------------------------------------------
            # Remove invalid rows
            # ----------------------------------------------------

            valid_rows = (
                X_roc.notna().all(axis=1)
            )


            X_roc = X_roc.loc[
                valid_rows
            ]

            y_true = y_true.loc[
                valid_rows
            ]


            # ----------------------------------------------------
            # ROC
            # ----------------------------------------------------

            if (
                len(X_roc) > 1
                and y_true.nunique() == 2
            ):

                roc_classes = list(model.classes_) if hasattr(model, "classes_") else [0, 1]
                if 1 in roc_classes:
                    roc_churn_index = roc_classes.index(1)
                elif "1" in roc_classes:
                    roc_churn_index = roc_classes.index("1")
                else:
                    roc_churn_index = min(1, len(roc_classes) - 1)

                y_score = model.predict_proba(
                    X_roc
                )[:, roc_churn_index]


                fpr, tpr, _ = roc_curve(
                    y_true,

                    y_score
                )


                roc_auc = roc_auc_score(
                    y_true,

                    y_score
                )


                roc_col1, roc_col2 = st.columns(
                    [1.5, 1]
                )


                with roc_col1:

                    roc_df = pd.DataFrame(
                        {
                            "False Positive Rate": fpr,

                            "True Positive Rate": tpr
                        }
                    )


                    fig_roc = px.line(
                        roc_df,

                        x="False Positive Rate",

                        y="True Positive Rate",

                        title=(
                            "Receiver Operating "
                            "Characteristic (ROC) Curve"
                        )
                    )


                    fig_roc.update_traces(
                        line=dict(
                            width=4
                        ),

                        hovertemplate=(
                            "False Positive Rate: %{x:.3f}<br>"
                            "True Positive Rate: %{y:.3f}"
                            "<extra></extra>"
                        )
                    )


                    # Random classifier
                    fig_roc.add_scatter(
                        x=[
                            0,
                            1
                        ],

                        y=[
                            0,
                            1
                        ],

                        mode="lines",

                        name="Random Classifier",

                        line=dict(
                            dash="dash",

                            width=2
                        )
                    )


                    fig_roc.update_layout(
                        height=470,

                        xaxis=dict(
                            range=[0, 1],

                            title="False Positive Rate"
                        ),

                        yaxis=dict(
                            range=[0, 1],

                            title="True Positive Rate"
                        ),

                        plot_bgcolor="rgba(0,0,0,0)",

                        paper_bgcolor="rgba(0,0,0,0)",

                        font=dict(
                            color="#f8fafc"
                        ),

                        margin=dict(
                            l=60,
                            r=30,
                            t=80,
                            b=60
                        ),

                        legend=dict(
                            orientation="h",

                            y=-0.18
                        )
                    )


                    st.plotly_chart(
                        fig_roc,

                        width="stretch"
                    )


                with roc_col2:

                    st.markdown(
                        "### 🎯 ROC-AUC Score"
                    )


                    st.metric(
                        "AUC",

                        f"{roc_auc * 100:.2f}%"
                    )


                    render_html(
                        f"""
                        <div class="custom-metric-card">

                            <div class="custom-metric-label">
                                Evaluation Samples
                            </div>

                            <div class="custom-metric-value">
                                {len(X_roc):,}
                            </div>

                        </div>
                        """
                    )


                    render_html(
                        """
                        <div class="custom-metric-card"
                             style="margin-top:12px;">

                            <div class="custom-metric-label">
                                Positive Class
                            </div>

                            <div class="custom-metric-value">
                                Customer Churn
                            </div>

                        </div>
                        """
                    )


                    st.info(
                        "AUC summarizes how well the model separates "
                        "churned and non-churned customers across "
                        "different classification thresholds."
                    )


            else:

                st.info(
                    "ROC curve could not be calculated because "
                    "both target classes were not available after preprocessing."
                )


    except Exception as roc_error:

        st.warning(
            "ROC curve could not be generated from the "
            "available dataset/model format."
        )

        # Uncomment for debugging:
        # st.exception(roc_error)


    # ============================================================


def show_history():
    page_header("🗃️ Prediction History", "Search, review, download, or clear saved customer predictions.")
    # ADMIN - PREDICTION HISTORY
    # ============================================================

    st.subheader("🗃️ Prediction History")
    st.markdown(
        "Every completed prediction is stored locally in a SQLite database "
        "so you can review previous customer assessments."
    )

    history_df = load_prediction_history()

    if history_df.empty:
        st.info(
            "No prediction history yet. Run a customer prediction and it "
            "will appear here automatically."
        )
    else:
        history_top1, history_top2, history_top3 = st.columns(3)

        with history_top1:
            st.metric(
                "Total Predictions",
                f"{len(history_df):,}"
            )

        with history_top2:
            churn_count = int(
                (history_df["Prediction"] == "Customer Will Churn").sum()
            )
            st.metric(
                "Predicted Churn",
                f"{churn_count:,}"
            )

        with history_top3:
            high_risk_count = int(
                (history_df["Risk Level"] == "HIGH").sum()
            )
            st.metric(
                "High Risk",
                f"{high_risk_count:,}"
            )

        st.markdown("### 🔎 Search Customer History")

        search_text = st.text_input(
            "Search by Customer ID, Name, or Location",
            placeholder="Example: CUS-1001 or Rahul",
            key="history_search"
        )

        filtered_history = history_df.copy()

        if search_text.strip():
            search_value = search_text.strip().lower()
            search_columns = [
                "Customer ID",
                "Customer Name",
                "Location"
            ]

            mask = pd.Series(False, index=filtered_history.index)

            for column in search_columns:
                mask = mask | filtered_history[column].astype(str).str.lower().str.contains(
                    search_value,
                    na=False
                )

            filtered_history = filtered_history[mask]

        display_history = filtered_history.copy()

        if not display_history.empty:
            display_history["Churn Probability (%)"] = display_history[
                "Churn Probability (%)"
            ].round(2)

            display_history["Monthly Charges"] = display_history[
                "Monthly Charges"
            ].round(2)

            display_history["Total Charges"] = display_history[
                "Total Charges"
            ].round(2)

            st.dataframe(
                display_history,
                width="stretch",
                hide_index=True
            )

            csv_history = display_history.to_csv(index=False).encode("utf-8")

            history_col1, history_col2 = st.columns(2)

            with history_col1:
                st.download_button(
                    "📥 Download History CSV",
                    data=csv_history,
                    file_name="customer_churn_prediction_history.csv",
                    mime="text/csv",
                    width="stretch"
                )

            with history_col2:
                if st.button(
                    "🗑️ Clear All History",
                    width="stretch",
                    type="secondary"
                ):
                    delete_prediction_history()
                    st.success("Prediction history cleared.")
                    st.rerun()
        else:
            st.warning(
                "No customer records match your search."
            )



    # ============================================================


def show_analytics():
    page_header("📊 Customer Analytics", "Explore trends and patterns in stored churn predictions.")

    # ============================================================
    # STEP 10 - COMPLETE CUSTOMER CHURN EDA
    # ============================================================
    # This section uses the original customer_churn.csv dataset and
    # safely creates churn-analysis charts when the expected columns
    # are available. It is independent of the prediction-history table.

    st.divider()
    st.subheader("🔍 Exploratory Data Analysis (EDA)")
    st.caption(
        "Churn patterns across Internet Service, Payment Method, Senior Citizen status, "
        "Tech Support, and Online Security."
    )

    if customer_data is None or customer_data.empty:
        st.info(
            "EDA is unavailable because customer_churn.csv was not found or contains no records."
        )
    else:
        eda_df = customer_data.copy()

        eda_churn_column = next(
            (
                col for col in eda_df.columns
                if str(col).strip().lower() in {
                    "churn", "exited", "customer_status"
                }
            ),
            None
        )

        def find_eda_column(*names):
            """Find a dataset column without depending on capitalization."""
            lookup = {
                str(col).strip().lower(): col
                for col in eda_df.columns
            }
            for name in names:
                if name.strip().lower() in lookup:
                    return lookup[name.strip().lower()]
            return None

        if eda_churn_column is None:
            st.warning(
                "EDA could not be generated because a churn column such as 'Churn' was not found."
            )
        else:
            # Convert churn target into a consistent Yes/No label.
            eda_df["_Churn Label"] = (
                eda_df[eda_churn_column]
                .astype(str)
                .str.strip()
                .str.lower()
                .map(
                    lambda value: "Churned"
                    if value in {"yes", "1", "true", "churned", "exited"}
                    else "Retained"
                )
            )

            def make_churn_rate_table(category_column):
                """Return customer count and churn rate for one category."""
                if category_column is None or category_column not in eda_df.columns:
                    return None

                temp = eda_df[[category_column, "_Churn Label"]].copy()
                temp[category_column] = temp[category_column].fillna("Unknown").astype(str).str.strip()
                temp.loc[temp[category_column] == "", category_column] = "Unknown"

                result = (
                    temp.groupby(category_column, dropna=False)
                    .agg(
                        Customers=("_Churn Label", "size"),
                        Churned=(
                            "_Churn Label",
                            lambda values: (values == "Churned").sum()
                        )
                    )
                    .reset_index()
                )

                result["Churn Rate (%)"] = (
                    result["Churned"] / result["Customers"] * 100
                ).round(2)

                result = result.rename(columns={category_column: "Category"})
                return result

            def show_eda_chart(category_column, title, key_suffix, x_title=None):
                """Render one EDA churn-rate chart safely."""
                result = make_churn_rate_table(category_column)

                if result is None or result.empty:
                    st.info(f"{title} is unavailable for the current dataset.")
                    return

                fig = px.bar(
                    result,
                    x="Category",
                    y="Churn Rate (%)",
                    text="Churn Rate (%)",
                    title=title,
                    hover_data=["Customers", "Churned"]
                )

                fig.update_traces(
                    texttemplate="%{text:.2f}%",
                    textposition="outside",
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        "Churn Rate: %{y:.2f}%<br>"
                        "Customers: %{customdata[0]}<br>"
                        "Churned: %{customdata[1]}<extra></extra>"
                    )
                )

                fig.update_layout(
                    height=430,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc"),
                    yaxis=dict(
                        title="Churn Rate (%)",
                        range=[0, 100]
                    ),
                    xaxis=dict(
                        title=x_title or "",
                        tickangle=-20 if len(result) > 4 else 0
                    ),
                    showlegend=False,
                    margin=dict(l=50, r=30, t=75, b=80)
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                    key=f"eda_{key_suffix}"
                )

                with st.expander(f"📋 View {title} data"):
                    display_result = result.copy()
                    st.dataframe(
                        display_result,
                        width="stretch",
                        hide_index=True
                    )

            # --------------------------------------------------------
            # Overall churn distribution
            # --------------------------------------------------------
            eda_count_col1, eda_count_col2, eda_count_col3 = st.columns(3)

            total_eda_customers = len(eda_df)
            total_eda_churned = int((eda_df["_Churn Label"] == "Churned").sum())
            total_eda_retained = total_eda_customers - total_eda_churned
            eda_rate = (
                total_eda_churned / total_eda_customers * 100
                if total_eda_customers
                else 0
            )

            with eda_count_col1:
                st.metric("EDA Customers", f"{total_eda_customers:,}")
            with eda_count_col2:
                st.metric("EDA Churned", f"{total_eda_churned:,}")
            with eda_count_col3:
                st.metric("EDA Churn Rate", f"{eda_rate:.2f}%")

            # --------------------------------------------------------
            # 1. Churn by Internet Service
            # --------------------------------------------------------
            internet_col = find_eda_column("InternetService", "Internet Service")
            payment_col = find_eda_column("PaymentMethod", "Payment Method")
            senior_col = find_eda_column("SeniorCitizen", "Senior Citizen")
            support_col = find_eda_column("TechSupport", "Tech Support")
            security_col = find_eda_column("OnlineSecurity", "Online Security")

            eda_col1, eda_col2 = st.columns(2)

            with eda_col1:
                show_eda_chart(
                    internet_col,
                    "🌐 Churn Rate by Internet Service",
                    "internet_service",
                    "Internet Service"
                )

            with eda_col2:
                show_eda_chart(
                    payment_col,
                    "💳 Churn Rate by Payment Method",
                    "payment_method",
                    "Payment Method"
                )

            # --------------------------------------------------------
            # 2. Churn by Senior Citizen status
            # --------------------------------------------------------
            senior_result = make_churn_rate_table(senior_col)
            if senior_result is not None and not senior_result.empty:
                senior_result["Category"] = senior_result["Category"].replace({
                    "0": "Non-Senior Citizen",
                    "1": "Senior Citizen",
                    "0.0": "Non-Senior Citizen",
                    "1.0": "Senior Citizen"
                })

                fig_senior = px.bar(
                    senior_result,
                    x="Category",
                    y="Churn Rate (%)",
                    text="Churn Rate (%)",
                    title="👴 Churn Rate by Senior Citizen Status",
                    hover_data=["Customers", "Churned"]
                )
                fig_senior.update_traces(
                    texttemplate="%{text:.2f}%",
                    textposition="outside"
                )
                fig_senior.update_layout(
                    height=430,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc"),
                    yaxis=dict(title="Churn Rate (%)", range=[0, 100]),
                    xaxis_title="Senior Citizen Status",
                    showlegend=False
                )
                st.plotly_chart(fig_senior, width="stretch", key="eda_senior_citizen")
            else:
                st.info("👴 Churn Rate by Senior Citizen Status is unavailable for the current dataset.")

            # --------------------------------------------------------
            # 3. Churn by Tech Support and Online Security
            # --------------------------------------------------------
            support_security_col1, support_security_col2 = st.columns(2)

            with support_security_col1:
                show_eda_chart(
                    support_col,
                    "🛠️ Churn Rate by Tech Support",
                    "tech_support",
                    "Tech Support"
                )

            with support_security_col2:
                show_eda_chart(
                    security_col,
                    "🔐 Churn Rate by Online Security",
                    "online_security",
                    "Online Security"
                )

            st.success(
                "✅ Step 10 EDA completed: Internet Service, Payment Method, "
                "Senior Citizen, Tech Support, and Online Security churn analysis are now available."
            )

    # ============================================================
    # STEP 6 - CUSTOMER ANALYTICS DASHBOARD
    # ============================================================
    # ============================================================

    st.divider()
    st.subheader("📊 Customer Analytics Dashboard")
    st.caption(
        "Interactive analytics based on the prediction history stored in the local SQLite database."
    )

    analytics_history = load_prediction_history()

    if analytics_history.empty:
        st.info(
            "Analytics will appear after you make at least one customer prediction."
        )
    else:
        analytics_df = analytics_history.copy()

        # Convert fields to numeric/date types safely.
        for numeric_col in [
            "Tenure (Months)",
            "Monthly Charges",
            "Total Charges",
            "Churn Probability (%)"
        ]:
            if numeric_col in analytics_df.columns:
                analytics_df[numeric_col] = pd.to_numeric(
                    analytics_df[numeric_col], errors="coerce"
                )

        analytics_df["Time"] = pd.to_datetime(
            analytics_df["Time"], errors="coerce"
        )

        # ------------------------------------------------------------
        # Analytics filters
        # ------------------------------------------------------------

        st.markdown("### 🔎 Analytics Filters")

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            risk_options = ["All"] + sorted(
                analytics_df["Risk Level"].dropna().astype(str).unique().tolist()
            )
            selected_risk = st.selectbox(
                "Risk Level",
                risk_options,
                key="analytics_risk_filter"
            )

        with filter_col2:
            contract_options = ["All"] + sorted(
                analytics_df["Contract"].dropna().astype(str).unique().tolist()
            )
            selected_contract = st.selectbox(
                "Contract",
                contract_options,
                key="analytics_contract_filter"
            )

        with filter_col3:
            prediction_options = ["All"] + sorted(
                analytics_df["Prediction"].dropna().astype(str).unique().tolist()
            )
            selected_prediction = st.selectbox(
                "Prediction",
                prediction_options,
                key="analytics_prediction_filter"
            )

        filtered_analytics = analytics_df.copy()

        if selected_risk != "All":
            filtered_analytics = filtered_analytics[
                filtered_analytics["Risk Level"] == selected_risk
            ]

        if selected_contract != "All":
            filtered_analytics = filtered_analytics[
                filtered_analytics["Contract"] == selected_contract
            ]

        if selected_prediction != "All":
            filtered_analytics = filtered_analytics[
                filtered_analytics["Prediction"] == selected_prediction
            ]

        if filtered_analytics.empty:
            st.warning("No prediction records match the selected filters.")
        else:
            # --------------------------------------------------------
            # KPI cards
            # --------------------------------------------------------

            total_predictions = len(filtered_analytics)
            churn_predictions = int(
                (
                    filtered_analytics["Prediction"]
                    == "Customer Will Churn"
                ).sum()
            )
            high_risk_predictions = int(
                (filtered_analytics["Risk Level"] == "HIGH").sum()
            )
            avg_churn_probability = filtered_analytics[
                "Churn Probability (%)"
            ].mean()

            analytics_metric1, analytics_metric2 = st.columns(4)[:2]
            analytics_metric3, analytics_metric4 = st.columns(4)[2:]

            with analytics_metric1:
                st.metric(
                    "Filtered Predictions",
                    f"{total_predictions:,}"
                )

            with analytics_metric2:
                st.metric(
                    "Predicted Churn",
                    f"{churn_predictions:,}"
                )

            with analytics_metric3:
                st.metric(
                    "High Risk Customers",
                    f"{high_risk_predictions:,}"
                )

            with analytics_metric4:
                st.metric(
                    "Average Churn Probability",
                    f"{avg_churn_probability:.2f}%"
                )

            # --------------------------------------------------------
            # Risk distribution + prediction distribution
            # --------------------------------------------------------

            chart_col1, chart_col2 = st.columns(2)

            with chart_col1:
                risk_counts = (
                    filtered_analytics["Risk Level"]
                    .value_counts()
                    .rename_axis("Risk Level")
                    .reset_index(name="Customers")
                )

                fig_risk = px.pie(
                    risk_counts,
                    names="Risk Level",
                    values="Customers",
                    hole=0.55,
                    title="Risk Level Distribution"
                )

                fig_risk.update_layout(
                    height=420,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc")
                )

                st.plotly_chart(fig_risk, width="stretch")

            with chart_col2:
                prediction_counts = (
                    filtered_analytics["Prediction"]
                    .value_counts()
                    .rename_axis("Prediction")
                    .reset_index(name="Customers")
                )

                fig_prediction = px.bar(
                    prediction_counts,
                    x="Prediction",
                    y="Customers",
                    text="Customers",
                    title="Prediction Distribution"
                )

                fig_prediction.update_traces(textposition="outside")
                fig_prediction.update_layout(
                    height=420,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc"),
                    xaxis_title="",
                    yaxis_title="Customers",
                    showlegend=False
                )

                st.plotly_chart(fig_prediction, width="stretch")

            # --------------------------------------------------------
            # Contract analysis
            # --------------------------------------------------------

            st.markdown("### 📋 Churn Analysis by Contract")

            contract_analysis = (
                filtered_analytics
                .assign(
                    Churn_Flag=(
                        filtered_analytics["Prediction"]
                        == "Customer Will Churn"
                    ).astype(int)
                )
                .groupby("Contract", dropna=False)
                .agg(
                    Customers=("Prediction", "size"),
                    Churned=("Churn_Flag", "sum"),
                    Avg_Churn_Probability=(
                        "Churn Probability (%)", "mean"
                    )
                )
                .reset_index()
            )

            contract_analysis["Churn Rate (%)"] = (
                contract_analysis["Churned"]
                / contract_analysis["Customers"]
                * 100
            ).round(2)

            contract_analysis["Avg Churn Probability (%)"] = (
                contract_analysis["Avg_Churn_Probability"]
                .round(2)
            )

            contract_display = contract_analysis[
                [
                    "Contract",
                    "Customers",
                    "Churned",
                    "Churn Rate (%)",
                    "Avg Churn Probability (%)"
                ]
            ]

            st.dataframe(
                contract_display,
                width="stretch",
                hide_index=True
            )

            fig_contract = px.bar(
                contract_analysis,
                x="Contract",
                y="Churn Rate (%)",
                text="Churn Rate (%)",
                title="Predicted Churn Rate by Contract"
            )

            fig_contract.update_traces(
                texttemplate="%{text:.2f}%",
                textposition="outside"
            )

            fig_contract.update_layout(
                height=420,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f8fafc"),
                yaxis=dict(
                    title="Churn Rate (%)",
                    range=[0, 100]
                ),
                xaxis_title="Contract",
                showlegend=False
            )

            st.plotly_chart(fig_contract, width="stretch")

            # --------------------------------------------------------
            # Tenure analysis
            # --------------------------------------------------------

            st.markdown("### ⏳ Churn Analysis by Tenure")

            tenure_df = filtered_analytics.dropna(
                subset=["Tenure (Months)"]
            ).copy()

            if not tenure_df.empty:
                tenure_bins = [-1, 6, 12, 24, 48, float("inf")]
                tenure_labels = [
                    "0–6 months",
                    "7–12 months",
                    "13–24 months",
                    "25–48 months",
                    "49+ months"
                ]

                tenure_df["Tenure Group"] = pd.cut(
                    tenure_df["Tenure (Months)"],
                    bins=tenure_bins,
                    labels=tenure_labels
                )

                tenure_analysis = (
                    tenure_df
                    .assign(
                        Churn_Flag=(
                            tenure_df["Prediction"]
                            == "Customer Will Churn"
                        ).astype(int)
                    )
                    .groupby("Tenure Group", observed=False)
                    .agg(
                        Customers=("Prediction", "size"),
                        Churned=("Churn_Flag", "sum"),
                        Avg_Churn_Probability=(
                            "Churn Probability (%)", "mean"
                        )
                    )
                    .reset_index()
                )

                tenure_analysis["Churn Rate (%)"] = (
                    tenure_analysis["Churned"]
                    / tenure_analysis["Customers"]
                    * 100
                ).round(2)

                fig_tenure = px.bar(
                    tenure_analysis,
                    x="Tenure Group",
                    y="Churn Rate (%)",
                    text="Churn Rate (%)",
                    title="Predicted Churn Rate by Tenure"
                )

                fig_tenure.update_traces(
                    texttemplate="%{text:.2f}%",
                    textposition="outside"
                )

                fig_tenure.update_layout(
                    height=420,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc"),
                    yaxis=dict(
                        title="Churn Rate (%)",
                        range=[0, 100]
                    ),
                    xaxis_title="Tenure",
                    showlegend=False
                )

                st.plotly_chart(fig_tenure, width="stretch")
            else:
                st.info("Tenure analytics are unavailable for the selected records.")

            # --------------------------------------------------------
            # Charges vs churn probability
            # --------------------------------------------------------

            st.markdown("### 💰 Charges vs Churn Probability")

            scatter_df = filtered_analytics.dropna(
                subset=[
                    "Monthly Charges",
                    "Churn Probability (%)"
                ]
            ).copy()

            if not scatter_df.empty:
                fig_scatter = px.scatter(
                    scatter_df,
                    x="Monthly Charges",
                    y="Churn Probability (%)",
                    size="Tenure (Months)",
                    hover_data=[
                        "Customer ID",
                        "Customer Name",
                        "Contract",
                        "Risk Level"
                    ],
                    title="Monthly Charges vs Churn Probability"
                )

                fig_scatter.update_layout(
                    height=470,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc"),
                    xaxis_title="Monthly Charges",
                    yaxis=dict(
                        title="Churn Probability (%)",
                        range=[0, 100]
                    )
                )

                st.plotly_chart(fig_scatter, width="stretch")
            else:
                st.info("Charge analytics are unavailable for the selected records.")

            # --------------------------------------------------------
            # Prediction trend over time
            # --------------------------------------------------------

            st.markdown("### 📅 Prediction Trend")

            trend_df = filtered_analytics.dropna(subset=["Time"]).copy()

            if not trend_df.empty:
                trend_df["Date"] = trend_df["Time"].dt.date

                daily_predictions = (
                    trend_df
                    .groupby("Date")
                    .size()
                    .reset_index(name="Predictions")
                )

                fig_trend = px.line(
                    daily_predictions,
                    x="Date",
                    y="Predictions",
                    markers=True,
                    title="Predictions Over Time"
                )

                fig_trend.update_layout(
                    height=420,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#f8fafc"),
                    xaxis_title="Date",
                    yaxis_title="Predictions"
                )

                st.plotly_chart(fig_trend, width="stretch")
            else:
                st.info("Prediction trend is unavailable because timestamps could not be read.")

            # --------------------------------------------------------
            # High-risk customer table
            # --------------------------------------------------------

            st.markdown("### 🚨 High-Risk Customer List")

            high_risk_df = filtered_analytics[
                filtered_analytics["Risk Level"] == "HIGH"
            ].copy()

            if high_risk_df.empty:
                st.success("No HIGH-risk customers are present in the selected records.")
            else:
                high_risk_display = high_risk_df[
                    [
                        "Customer ID",
                        "Customer Name",
                        "Contract",
                        "Tenure (Months)",
                        "Monthly Charges",
                        "Churn Probability (%)",
                        "Risk Level"
                    ]
                ].sort_values(
                    by="Churn Probability (%)",
                    ascending=False
                )

                st.dataframe(
                    high_risk_display,
                    width="stretch",
                    hide_index=True
                )

                high_risk_csv = high_risk_display.to_csv(
                    index=False
                ).encode("utf-8")

                st.download_button(
                    "📥 Download High-Risk Customers",
                    data=high_risk_csv,
                    file_name="high_risk_customers.csv",
                    mime="text/csv",
                    width="stretch"
                )

    # ============================================================
    # STEP 11 - CUSTOMER RETENTION ACTION CENTER
    # ============================================================
    # Converts prediction-history analytics into an actionable
    # retention list. This section is based only on stored
    # predictions and does not change the trained model.

    st.divider()
    st.subheader("🎯 Customer Retention Action Center")
    st.caption(
        "Use predicted churn risk to identify customers that may need follow-up. "
        "The suggested actions are business-support guidance, not model predictions."
    )

    retention_df = filtered_analytics.copy() if 'filtered_analytics' in locals() else pd.DataFrame()

    if retention_df.empty:
        st.info("Retention recommendations will appear when matching prediction records are available.")
    else:
        retention_df = retention_df.copy()

        # Safely calculate an action category from the existing risk level.
        def retention_action(risk):
            risk = str(risk).upper()
            if risk == "HIGH":
                return "Immediate follow-up"
            if risk == "MEDIUM":
                return "Monitor and engage"
            return "Maintain engagement"

        retention_df["Recommended Action"] = retention_df["Risk Level"].apply(retention_action)

        action_counts = (
            retention_df["Recommended Action"]
            .value_counts()
            .rename_axis("Recommended Action")
            .reset_index(name="Customers")
        )

        retention_col1, retention_col2, retention_col3, retention_col4 = st.columns(4)

        high_count = int((retention_df["Risk Level"].astype(str).str.upper() == "HIGH").sum())
        medium_count = int((retention_df["Risk Level"].astype(str).str.upper() == "MEDIUM").sum())
        low_count = int((retention_df["Risk Level"].astype(str).str.upper() == "LOW").sum())

        with retention_col1:
            st.metric("Customers in View", f"{len(retention_df):,}")
        with retention_col2:
            st.metric("Immediate Follow-up", f"{high_count:,}")
        with retention_col3:
            st.metric("Monitor & Engage", f"{medium_count:,}")
        with retention_col4:
            st.metric("Maintain Engagement", f"{low_count:,}")

        action_chart_col1, action_chart_col2 = st.columns(2)

        with action_chart_col1:
            fig_actions = px.bar(
                action_counts,
                x="Recommended Action",
                y="Customers",
                text="Customers",
                title="Retention Action Distribution"
            )
            fig_actions.update_traces(textposition="outside")
            fig_actions.update_layout(
                height=420,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f8fafc"),
                xaxis_title="",
                yaxis_title="Customers",
                showlegend=False,
                margin=dict(l=50, r=30, t=70, b=80)
            )
            st.plotly_chart(fig_actions, width="stretch")

        with action_chart_col2:
            action_probability = (
                retention_df.groupby("Recommended Action", dropna=False)["Churn Probability (%)"]
                .mean()
                .reset_index(name="Average Churn Probability (%)")
            )
            action_probability["Average Churn Probability (%)"] = action_probability["Average Churn Probability (%)"].round(2)

            fig_action_probability = px.bar(
                action_probability,
                x="Recommended Action",
                y="Average Churn Probability (%)",
                text="Average Churn Probability (%)",
                title="Average Churn Probability by Action"
            )
            fig_action_probability.update_traces(
                texttemplate="%{text:.2f}%",
                textposition="outside"
            )
            fig_action_probability.update_layout(
                height=420,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f8fafc"),
                yaxis=dict(title="Average Churn Probability (%)", range=[0, 100]),
                xaxis_title="",
                showlegend=False,
                margin=dict(l=50, r=30, t=70, b=80)
            )
            st.plotly_chart(fig_action_probability, width="stretch")

        st.markdown("### 📋 Retention Priority List")

        retention_columns = [
            "Customer ID",
            "Customer Name",
            "Contract",
            "Tenure (Months)",
            "Monthly Charges",
            "Churn Probability (%)",
            "Risk Level",
            "Recommended Action"
        ]
        retention_columns = [col for col in retention_columns if col in retention_df.columns]

        priority_df = retention_df[retention_columns].copy()

        if "Risk Level" in priority_df.columns:
            risk_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
            priority_df["_risk_order"] = priority_df["Risk Level"].astype(str).str.upper().map(risk_order).fillna(3)
        else:
            priority_df["_risk_order"] = 3

        if "Churn Probability (%)" in priority_df.columns:
            priority_df = priority_df.sort_values(
                by=["_risk_order", "Churn Probability (%)"],
                ascending=[True, False]
            )
        else:
            priority_df = priority_df.sort_values(by=["_risk_order"], ascending=True)

        priority_df = priority_df.drop(columns=["_risk_order"], errors="ignore")

        st.dataframe(
            priority_df,
            width="stretch",
            hide_index=True
        )

        retention_csv = priority_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download Retention Action List",
            data=retention_csv,
            file_name="customer_retention_action_list.csv",
            mime="text/csv",
            width="stretch"
        )

        st.success(
            "✅ Step 11 completed: the Customer Retention Action Center is now available in Customer Analytics."
        )

    # ============================================================
    # FOOTER
    # ============================================================

    st.divider()

    render_html(
        f"""
        <div class="footer">
            📊 Customer Churn Prediction ·
            Random Forest Machine Learning ·
            Streamlit ·
            Logged in as {CURRENT_USERNAME.title()} ({CURRENT_ROLE})
        </div>
        """
    )


# ============================================================
# STEP 14 - CUSTOMER SEARCH & EDIT PROFILE
# ============================================================
def update_customer_profile(
    original_customer_id,
    customer_id,
    customer_name,
    age,
    location,
    customer_since,
    tenure,
    gender,
    contract,
    internet_service,
    payment_method,
    online_security,
    tech_support,
    monthly_charges,
    total_charges
):
    """Update profile information for every prediction record belonging to a customer."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute(
            """
            UPDATE prediction_history
            SET customer_id = ?,
                customer_name = ?,
                age = ?,
                location = ?,
                customer_since = ?,
                tenure = ?,
                gender = ?,
                contract = ?,
                internet_service = ?,
                payment_method = ?,
                online_security = ?,
                tech_support = ?,
                monthly_charges = ?,
                total_charges = ?
            WHERE customer_id = ?
            """,
            (
                customer_id.strip(),
                customer_name.strip(),
                int(age),
                location.strip(),
                customer_since.strip(),
                int(tenure),
                gender,
                contract,
                internet_service,
                payment_method,
                online_security,
                tech_support,
                float(monthly_charges),
                float(total_charges),
                original_customer_id
            )
        )
        conn.commit()
        return cursor.rowcount


def show_customer_profile():
    page_header(
        "👤 Customer Profile",
        "Search, view, and edit customer information stored in prediction history."
    )

    history_df = load_prediction_history()

    if history_df.empty:
        st.info("No customer profiles are available yet. Run a churn prediction first to create a customer profile.")
        return

    # Build one row per customer using the newest prediction record.
    profile_df = history_df.copy()
    if "Time" in profile_df.columns:
        profile_df["_sort_time"] = pd.to_datetime(profile_df["Time"], errors="coerce")
        profile_df = profile_df.sort_values("_sort_time", ascending=False)
    profile_df = profile_df.drop_duplicates(subset=["Customer ID"], keep="first")

    st.subheader("🔎 Search Customer")
    search_col, select_col = st.columns([1, 1.5])

    with search_col:
        search_text = st.text_input(
            "Search by Customer ID or Name",
            placeholder="Example: CUS-1001 or Rahul",
            key="step14_customer_search"
        ).strip().lower()

    filtered_profiles = profile_df.copy()
    if search_text:
        mask = (
            filtered_profiles["Customer ID"].astype(str).str.lower().str.contains(search_text, na=False)
            | filtered_profiles["Customer Name"].astype(str).str.lower().str.contains(search_text, na=False)
        )
        filtered_profiles = filtered_profiles.loc[mask]

    if filtered_profiles.empty:
        st.warning("No customer matched your search.")
        return

    customer_ids = filtered_profiles["Customer ID"].astype(str).tolist()

    with select_col:
        selected_customer = st.selectbox(
            "Select Customer",
            customer_ids,
            key="step14_customer_selector"
        )

    customer_rows = history_df[
        history_df["Customer ID"].astype(str) == str(selected_customer)
    ].copy()

    if customer_rows.empty:
        st.warning("Customer profile could not be found.")
        return

    if "Time" in customer_rows.columns:
        customer_rows["_sort_time"] = pd.to_datetime(customer_rows["Time"], errors="coerce")
        customer_rows = customer_rows.sort_values("_sort_time", ascending=False)

    customer = customer_rows.iloc[0]

    def safe_int(value, default=0):
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return default

    def safe_float(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    customer_id = str(customer.get("Customer ID", ""))
    customer_name = str(customer.get("Customer Name", "Customer"))
    age = safe_int(customer.get("Age", 28), 28)
    location = str(customer.get("Location", ""))
    customer_since = str(customer.get("Customer Since", ""))
    tenure = safe_int(customer.get("Tenure (Months)", 0), 0)
    gender = str(customer.get("Gender", "Male"))
    contract = str(customer.get("Contract", "Month-to-month"))
    internet = str(customer.get("Internet Service", "DSL"))
    payment = str(customer.get("Payment Method", "Electronic check"))
    security = str(customer.get("Online Security", "No"))
    support = str(customer.get("Tech Support", "No"))
    monthly = safe_float(customer.get("Monthly Charges", 0), 0.0)
    total = safe_float(customer.get("Total Charges", 0), 0.0)
    prediction = str(customer.get("Prediction", "-"))
    churn_probability = safe_float(customer.get("Churn Probability (%)", 0), 0.0)
    no_churn_probability = safe_float(customer.get("No Churn Probability (%)", 0), 0.0)
    risk = str(customer.get("Risk Level", "LOW")).upper()
    last_prediction = str(customer.get("Time", "-"))

    risk_class = {
        "HIGH": "risk-high",
        "MEDIUM": "risk-medium",
        "LOW": "risk-low"
    }.get(risk, "risk-low")
    initial = (customer_name.strip()[:1] or "C").upper()

    render_html(
        f"""
        <div class="profile-card" style="margin-bottom:20px;">
            <div class="profile-avatar">{initial}</div>
            <div class="profile-name">{customer_name}</div>
            <div class="profile-meta">Customer ID · {customer_id} &nbsp;•&nbsp; {location}</div>
            <div style="margin-top:14px;">
                <span class="risk-pill {risk_class}">🎯 {risk} RISK · {churn_probability:.2f}%</span>
            </div>
        </div>
        """
    )

    # ========================================================
    # STEP 14 - EDIT PROFILE
    # ========================================================
    st.subheader("✏️ Edit Customer Profile")
    st.caption("Changes are saved to the local SQLite prediction-history database. Existing prediction results are not recalculated.")

    with st.form("edit_customer_profile_form", clear_on_submit=False):
        c1, c2, c3 = st.columns(3)
        with c1:
            edit_customer_id = st.text_input("Customer ID", value=customer_id, max_chars=30)
            edit_customer_name = st.text_input("Customer Name", value=customer_name, max_chars=60)
            edit_age = st.number_input("Age", min_value=18, max_value=100, value=max(18, min(age, 100)), step=1)
            edit_gender = st.selectbox("Gender", ["Male", "Female"], index=0 if gender not in ["Male", "Female"] else ["Male", "Female"].index(gender))
            edit_location = st.text_input("Location", value=location, max_chars=100)

        with c2:
            edit_customer_since = st.text_input("Customer Since", value=customer_since, max_chars=30)
            edit_tenure = st.number_input("Tenure (Months)", min_value=0, max_value=100, value=max(0, min(tenure, 100)), step=1)
            contracts = ["Month-to-month", "One year", "Two year"]
            edit_contract = st.selectbox("Contract", contracts, index=contracts.index(contract) if contract in contracts else 0)
            internet_options = ["DSL", "Fiber optic", "No internet service"]
            edit_internet = st.selectbox("Internet Service", internet_options, index=internet_options.index(internet) if internet in internet_options else 0)
            payment_options = ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]
            edit_payment = st.selectbox("Payment Method", payment_options, index=payment_options.index(payment) if payment in payment_options else 0)

        with c3:
            security_options = ["Yes", "No", "No internet service"]
            edit_security = st.selectbox("Online Security", security_options, index=security_options.index(security) if security in security_options else 1)
            support_options = ["Yes", "No", "No internet service"]
            edit_support = st.selectbox("Tech Support", support_options, index=support_options.index(support) if support in support_options else 1)
            edit_monthly = st.number_input("Monthly Charges", min_value=0.0, max_value=10000.0, value=max(0.0, monthly), step=1.0)
            edit_total = st.number_input("Total Charges", min_value=0.0, max_value=100000.0, value=max(0.0, total), step=10.0)

        save_profile = st.form_submit_button("💾 Save Profile Changes", type="primary", width="stretch")

    if save_profile:
        if not edit_customer_id.strip() or not edit_customer_name.strip():
            st.error("Customer ID and Customer Name cannot be empty.")
        else:
            try:
                updated_rows = update_customer_profile(
                    customer_id,
                    edit_customer_id,
                    edit_customer_name,
                    edit_age,
                    edit_location,
                    edit_customer_since,
                    edit_tenure,
                    edit_gender,
                    edit_contract,
                    edit_internet,
                    edit_payment,
                    edit_security,
                    edit_support,
                    edit_monthly,
                    edit_total
                )
                if updated_rows > 0:
                    st.success(f"✅ Customer profile updated successfully. {updated_rows} prediction record(s) were updated.")
                    st.rerun()
                else:
                    st.warning("No matching customer record was updated.")
            except sqlite3.Error as edit_error:
                st.error(f"Unable to update customer profile: {edit_error}")

    st.divider()
    st.subheader("📊 Customer Overview")
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Age", f"{age}")
    with m2:
        st.metric("Tenure", f"{tenure} months")
    with m3:
        st.metric("Monthly Charges", f"${monthly:.2f}")
    with m4:
        st.metric("Total Charges", f"${total:.2f}")

    left, right = st.columns(2)
    with left:
        st.subheader("👤 Personal Information")
        personal = pd.DataFrame({
            "Field": ["Customer ID", "Customer Name", "Age", "Gender", "Location", "Customer Since"],
            "Value": [customer_id, customer_name, age, gender, location, customer_since]
        })
        st.dataframe(personal, width="stretch", hide_index=True)
    with right:
        st.subheader("📋 Service Information")
        service = pd.DataFrame({
            "Field": ["Contract", "Internet Service", "Payment Method", "Online Security", "Tech Support"],
            "Value": [contract, internet, payment, security, support]
        })
        st.dataframe(service, width="stretch", hide_index=True)

    st.divider()
    st.subheader("🔮 Latest Churn Assessment")
    r1, r2, r3 = st.columns(3)
    with r1:
        if prediction == "Customer Will Churn":
            st.error("🔴 CUSTOMER WILL CHURN")
        else:
            st.success("🟢 CUSTOMER WILL NOT CHURN")
    with r2:
        st.metric("Churn Probability", f"{churn_probability:.2f}%")
    with r3:
        st.metric("No-Churn Probability", f"{no_churn_probability:.2f}%")

    st.markdown("**Churn Probability**")
    st.progress(max(0, min(int(round(churn_probability)), 100)))
    st.caption(f"Last prediction: {last_prediction}")

    st.subheader("🕘 Customer Prediction History")
    history_display = customer_rows.drop(columns=["_sort_time"], errors="ignore").copy()
    if "Churn Probability (%)" in history_display.columns:
        history_display["Churn Probability (%)"] = pd.to_numeric(
            history_display["Churn Probability (%)"], errors="coerce"
        ).round(2)
    st.dataframe(history_display, width="stretch", hide_index=True)

    profile_csv = pd.DataFrame({
        "Field": [
            "Customer ID", "Customer Name", "Age", "Gender", "Location",
            "Customer Since", "Tenure (Months)", "Contract", "Internet Service",
            "Payment Method", "Online Security", "Tech Support",
            "Monthly Charges", "Total Charges", "Prediction",
            "Churn Probability (%)", "No-Churn Probability (%)", "Risk Level",
            "Last Prediction"
        ],
        "Value": [
            customer_id, customer_name, age, gender, location, customer_since, tenure,
            contract, internet, payment, security, support, monthly, total,
            prediction, f"{churn_probability:.2f}", f"{no_churn_probability:.2f}",
            risk, last_prediction
        ]
    }).to_csv(index=False).encode("utf-8")

    st.download_button(
        "📥 Download Customer Profile",
        data=profile_csv,
        file_name=f"{customer_id}_profile.csv",
        mime="text/csv",
        width="stretch"
    )


# ============================================================
# STEP 15 - CUSTOMER 360 DASHBOARD
# ============================================================
def show_customer_360():
    page_header(
        "🌐 Customer 360",
        "A complete view of one customer's profile, churn risk, billing, services, and prediction history."
    )

    history_df = load_prediction_history()
    if history_df.empty:
        st.info("No customer data is available yet. Run a churn prediction first.")
        return

    work = history_df.copy()
    work["_sort_time"] = pd.to_datetime(work["Time"], errors="coerce")
    work = work.sort_values("_sort_time", ascending=False)
    latest_profiles = work.drop_duplicates(subset=["Customer ID"], keep="first").copy()

    st.subheader("🔎 Select Customer")
    c1, c2 = st.columns([1, 2])
    with c1:
        search = st.text_input(
            "Search Customer ID or Name",
            placeholder="Example: CUS-1001 or Rahul",
            key="step15_search"
        ).strip().lower()

    filtered = latest_profiles.copy()
    if search:
        mask = (
            filtered["Customer ID"].astype(str).str.lower().str.contains(search, na=False)
            | filtered["Customer Name"].astype(str).str.lower().str.contains(search, na=False)
        )
        filtered = filtered.loc[mask]

    if filtered.empty:
        st.warning("No customer matched your search.")
        return

    options = filtered["Customer ID"].astype(str).tolist()
    with c2:
        selected_id = st.selectbox("Customer", options, key="step15_customer")

    rows = work[work["Customer ID"].astype(str) == str(selected_id)].copy()
    if rows.empty:
        st.warning("Customer record not found.")
        return

    latest = rows.iloc[0]

    def sf(value, default=0.0):
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    name = str(latest.get("Customer Name", "Customer"))
    risk = str(latest.get("Risk Level", "LOW")).upper()
    churn = sf(latest.get("Churn Probability (%)", 0))
    no_churn = sf(latest.get("No Churn Probability (%)", 0))
    risk_class = {"HIGH": "risk-high", "MEDIUM": "risk-medium", "LOW": "risk-low"}.get(risk, "risk-low")
    initial = (name.strip()[:1] or "C").upper()

    render_html(f"""
    <div class="profile-card" style="margin-bottom:20px;">
        <div class="profile-avatar">{initial}</div>
        <div class="profile-name">{name}</div>
        <div class="profile-meta">Customer ID · {selected_id} &nbsp;•&nbsp; {latest.get('Location', '')}</div>
        <div style="margin-top:14px;">
            <span class="risk-pill {risk_class}">🎯 {risk} RISK · {churn:.2f}%</span>
        </div>
    </div>
    """)

    st.subheader("📊 Customer Snapshot")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Age", f"{int(sf(latest.get('Age', 0)))}")
    m2.metric("Tenure", f"{int(sf(latest.get('Tenure (Months)', 0)))} months")
    m3.metric("Monthly Charges", f"${sf(latest.get('Monthly Charges', 0)):.2f}")
    m4.metric("Total Charges", f"${sf(latest.get('Total Charges', 0)):.2f}")
    m5.metric("Predictions", f"{len(rows):,}")

    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("👤 Personal Information")
        personal = pd.DataFrame({
            "Field": ["Customer ID", "Customer Name", "Age", "Gender", "Location", "Customer Since"],
            "Value": [
                latest.get("Customer ID", ""), latest.get("Customer Name", ""), latest.get("Age", ""),
                latest.get("Gender", ""), latest.get("Location", ""), latest.get("Customer Since", "")
            ]
        })
        st.dataframe(personal, width="stretch", hide_index=True)

    with right:
        st.subheader("📡 Service & Billing")
        service = pd.DataFrame({
            "Field": ["Contract", "Internet Service", "Payment Method", "Online Security", "Tech Support", "Monthly Charges", "Total Charges"],
            "Value": [
                latest.get("Contract", ""), latest.get("Internet Service", ""), latest.get("Payment Method", ""),
                latest.get("Online Security", ""), latest.get("Tech Support", ""),
                f"${sf(latest.get('Monthly Charges', 0)):.2f}", f"${sf(latest.get('Total Charges', 0)):.2f}"
            ]
        })
        st.dataframe(service, width="stretch", hide_index=True)

    st.divider()
    st.subheader("🎯 Current Churn Assessment")
    r1, r2, r3 = st.columns(3)
    with r1:
        if str(latest.get("Prediction", "")) == "Customer Will Churn":
            st.error("🔴 CUSTOMER WILL CHURN")
        else:
            st.success("🟢 CUSTOMER WILL NOT CHURN")
    with r2:
        st.metric("Churn Probability", f"{churn:.2f}%")
    with r3:
        st.metric("No-Churn Probability", f"{no_churn:.2f}%")

    st.progress(max(0, min(int(round(churn)), 100)))
    st.caption(f"Risk level: {risk} · Latest prediction: {latest.get('Time', '-')}")

    # Retention guidance based on the existing risk category.
    st.subheader("💡 Retention Action")
    if risk == "HIGH":
        action = "Immediate follow-up"
        message = "Review the customer's recent experience and consider an appropriate retention conversation."
        st.error(f"🔴 {action}: {message}")
    elif risk == "MEDIUM":
        action = "Monitor and engage"
        message = "Keep the customer engaged and review service or contract details during follow-up."
        st.warning(f"🟠 {action}: {message}")
    else:
        action = "Maintain engagement"
        message = "Continue normal customer engagement and monitor future prediction changes."
        st.success(f"🟢 {action}: {message}")

    st.divider()
    st.subheader("📈 Churn Probability Trend")
    trend = rows[["Time", "Churn Probability (%)", "Risk Level", "Prediction"]].copy()
    trend["Time"] = pd.to_datetime(trend["Time"], errors="coerce")
    trend["Churn Probability (%)"] = pd.to_numeric(trend["Churn Probability (%)"], errors="coerce")
    trend = trend.dropna(subset=["Time", "Churn Probability (%)"]).sort_values("Time")

    if len(trend) >= 1:
        fig = px.line(
            trend, x="Time", y="Churn Probability (%)", markers=True,
            title="Customer Churn Probability Over Time"
        )
        fig.update_yaxes(range=[0, 100], title="Churn Probability (%)")
        fig.update_xaxes(title="Prediction Time")
        fig.update_layout(
            height=430, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"), margin=dict(l=60, r=30, t=70, b=60)
        )
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("A churn trend will appear after prediction records are available.")

    st.subheader("🕘 Prediction History")
    history_display = rows.drop(columns=["_sort_time"], errors="ignore").copy()
    if "Churn Probability (%)" in history_display.columns:
        history_display["Churn Probability (%)"] = pd.to_numeric(history_display["Churn Probability (%)"], errors="coerce").round(2)
    if "No Churn Probability (%)" in history_display.columns:
        history_display["No Churn Probability (%)"] = pd.to_numeric(history_display["No Churn Probability (%)"], errors="coerce").round(2)
    st.dataframe(history_display, width="stretch", hide_index=True)

    # Complete customer report.
    report = pd.DataFrame({
        "Field": [
            "Customer ID", "Customer Name", "Age", "Gender", "Location", "Customer Since",
            "Tenure (Months)", "Contract", "Internet Service", "Payment Method",
            "Online Security", "Tech Support", "Monthly Charges", "Total Charges",
            "Prediction", "Churn Probability (%)", "No-Churn Probability (%)", "Risk Level",
            "Recommended Action", "Latest Prediction Time"
        ],
        "Value": [
            latest.get("Customer ID", ""), latest.get("Customer Name", ""), latest.get("Age", ""),
            latest.get("Gender", ""), latest.get("Location", ""), latest.get("Customer Since", ""),
            latest.get("Tenure (Months)", ""), latest.get("Contract", ""), latest.get("Internet Service", ""),
            latest.get("Payment Method", ""), latest.get("Online Security", ""), latest.get("Tech Support", ""),
            f"${sf(latest.get('Monthly Charges', 0)):.2f}", f"${sf(latest.get('Total Charges', 0)):.2f}",
            latest.get("Prediction", ""), f"{churn:.2f}", f"{no_churn:.2f}", risk, action, latest.get("Time", "")
        ]
    })

    st.download_button(
        "📥 Download Complete Customer 360 Report",
        data=report.to_csv(index=False).encode("utf-8"),
        file_name=f"{selected_id}_customer_360.csv",
        mime="text/csv",
        width="stretch"
    )

    st.success("✅ Step 15 completed: Customer 360 Dashboard is available.")


# ============================================================
# STEP 16 - CUSTOMER SEGMENTATION & RETENTION DASHBOARD
# ============================================================
def show_segmentation():
    page_header(
        "🎯 Customer Segmentation",
        "Group customers by churn risk, value, tenure, and engagement indicators."
    )

    history_df = load_prediction_history()

    if history_df.empty:
        st.info("No customer data is available yet. Run at least one prediction first.")
        return

    df = history_df.copy()

    # Use the newest prediction for each customer so the dashboard does not
    # count repeated predictions for the same customer multiple times.
    if "Time" in df.columns:
        df["_sort_time"] = pd.to_datetime(df["Time"], errors="coerce")
        df = df.sort_values("_sort_time", ascending=False)

    df = df.drop_duplicates(subset=["Customer ID"], keep="first").copy()

    def numeric_column(column, default=0.0):
        if column in df.columns:
            return pd.to_numeric(df[column], errors="coerce").fillna(default)
        return pd.Series(default, index=df.index)

    df["Churn Probability (%)"] = numeric_column("Churn Probability (%)")
    df["Monthly Charges"] = numeric_column("Monthly Charges")
    df["Total Charges"] = numeric_column("Total Charges")
    df["Tenure (Months)"] = numeric_column("Tenure (Months)")

    # ------------------------------------------------------------
    # Segment customers using transparent business rules.
    # ------------------------------------------------------------
    def assign_segment(row):
        risk = str(row.get("Risk Level", "LOW")).upper()
        churn = float(row.get("Churn Probability (%)", 0))
        monthly = float(row.get("Monthly Charges", 0))
        tenure = float(row.get("Tenure (Months)", 0))

        if risk == "HIGH" and monthly >= 70:
            return "High-Risk / High-Value"
        if risk == "HIGH":
            return "High-Risk"
        if risk == "MEDIUM" and tenure < 12:
            return "New / At-Risk"
        if risk == "MEDIUM":
            return "Engagement Needed"
        if monthly >= 70 and tenure >= 24:
            return "Loyal / High-Value"
        if tenure < 12:
            return "New Customer"
        return "Stable Customer"

    df["Customer Segment"] = df.apply(assign_segment, axis=1)

    segment_actions = {
        "High-Risk / High-Value": "Priority retention review",
        "High-Risk": "Immediate follow-up",
        "New / At-Risk": "Early engagement",
        "Engagement Needed": "Monitor and engage",
        "Loyal / High-Value": "Maintain loyalty",
        "New Customer": "Onboarding engagement",
        "Stable Customer": "Maintain engagement"
    }
    df["Recommended Action"] = df["Customer Segment"].map(segment_actions).fillna("Review customer")

    # ------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------
    st.subheader("🔎 Segment Filters")
    filter_col1, filter_col2, filter_col3 = st.columns(3)

    segments = sorted(df["Customer Segment"].dropna().astype(str).unique().tolist())
    risks = [r for r in ["HIGH", "MEDIUM", "LOW"] if r in df["Risk Level"].astype(str).str.upper().unique()]

    with filter_col1:
        selected_segments = st.multiselect(
            "Customer Segment",
            segments,
            default=segments,
            key="step16_segments"
        )

    with filter_col2:
        selected_risks = st.multiselect(
            "Risk Level",
            risks,
            default=risks,
            key="step16_risks"
        )

    with filter_col3:
        min_monthly = float(df["Monthly Charges"].min()) if not df.empty else 0.0
        max_monthly = float(df["Monthly Charges"].max()) if not df.empty else 0.0
        if max_monthly > min_monthly:
            monthly_range = st.slider(
                "Monthly Charges",
                min_value=float(np.floor(min_monthly)),
                max_value=float(np.ceil(max_monthly)),
                value=(float(np.floor(min_monthly)), float(np.ceil(max_monthly))),
                key="step16_monthly_range"
            )
        else:
            monthly_range = (min_monthly, max_monthly)
            st.caption(f"Monthly Charges: ${min_monthly:.2f}")

    filtered = df[
        df["Customer Segment"].isin(selected_segments)
        & df["Risk Level"].astype(str).str.upper().isin(selected_risks)
        & df["Monthly Charges"].between(monthly_range[0], monthly_range[1])
    ].copy()

    st.divider()
    st.subheader("📊 Segment Overview")

    total = len(filtered)
    high = int((filtered["Risk Level"].astype(str).str.upper() == "HIGH").sum())
    medium = int((filtered["Risk Level"].astype(str).str.upper() == "MEDIUM").sum())
    avg_churn = float(filtered["Churn Probability (%)"].mean()) if total else 0.0

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Customers in View", f"{total:,}")
    with m2:
        st.metric("High-Risk Customers", f"{high:,}")
    with m3:
        st.metric("Medium-Risk Customers", f"{medium:,}")
    with m4:
        st.metric("Average Churn Probability", f"{avg_churn:.2f}%")

    if filtered.empty:
        st.warning("No customers match the selected filters.")
        return

    # ------------------------------------------------------------
    # Segment charts
    # ------------------------------------------------------------
    chart_col1, chart_col2 = st.columns(2)

    segment_counts = (
        filtered["Customer Segment"]
        .value_counts()
        .rename_axis("Customer Segment")
        .reset_index(name="Customers")
    )

    with chart_col1:
        fig_segments = px.pie(
            segment_counts,
            names="Customer Segment",
            values="Customers",
            hole=0.5,
            title="Customer Segment Distribution"
        )
        fig_segments.update_layout(
            height=430,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc")
        )
        st.plotly_chart(fig_segments, width="stretch")

    with chart_col2:
        segment_risk = (
            filtered.groupby("Customer Segment", dropna=False)["Churn Probability (%)"]
            .mean()
            .reset_index(name="Average Churn Probability (%)")
            .sort_values("Average Churn Probability (%)", ascending=False)
        )
        fig_risk = px.bar(
            segment_risk,
            x="Customer Segment",
            y="Average Churn Probability (%)",
            text="Average Churn Probability (%)",
            title="Average Churn Probability by Segment"
        )
        fig_risk.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
        fig_risk.update_layout(
            height=430,
            yaxis=dict(range=[0, 100], title="Average Churn Probability (%)"),
            xaxis_title="",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"),
            showlegend=False,
            margin=dict(l=50, r=30, t=70, b=100)
        )
        st.plotly_chart(fig_risk, width="stretch")

    st.divider()
    st.subheader("💰 Customer Value vs Churn Risk")

    value_df = filtered.copy()
    value_df["Customer Label"] = value_df["Customer Name"].astype(str)

    fig_value = px.scatter(
        value_df,
        x="Monthly Charges",
        y="Churn Probability (%)",
        size="Total Charges",
        hover_name="Customer Label",
        color="Customer Segment",
        hover_data=["Customer ID", "Contract", "Tenure (Months)", "Risk Level"],
        title="Monthly Charges vs Churn Probability"
    )
    fig_value.update_layout(
        height=520,
        yaxis=dict(range=[0, 100], title="Churn Probability (%)"),
        xaxis_title="Monthly Charges",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f8fafc"),
        legend_title="Segment"
    )
    st.plotly_chart(fig_value, width="stretch")

    # ------------------------------------------------------------
    # Retention action table
    # ------------------------------------------------------------
    st.subheader("🎯 Segment Retention Actions")
    action_summary = (
        filtered.groupby(["Customer Segment", "Recommended Action"], dropna=False)
        .agg(
            Customers=("Customer ID", "count"),
            Average_Churn=("Churn Probability (%)", "mean"),
            Average_Monthly_Charges=("Monthly Charges", "mean")
        )
        .reset_index()
    )
    action_summary["Average_Churn"] = action_summary["Average_Churn"].round(2)
    action_summary["Average_Monthly_Charges"] = action_summary["Average_Monthly_Charges"].round(2)
    action_summary = action_summary.rename(columns={
        "Average_Churn": "Average Churn Probability (%)",
        "Average_Monthly_Charges": "Average Monthly Charges"
    })
    st.dataframe(action_summary, width="stretch", hide_index=True)

    st.subheader("📋 Segmented Customer List")
    display_columns = [
        "Customer ID", "Customer Name", "Customer Segment", "Recommended Action",
        "Risk Level", "Churn Probability (%)", "Tenure (Months)",
        "Monthly Charges", "Contract"
    ]
    display_columns = [c for c in display_columns if c in filtered.columns]

    customer_list = filtered[display_columns].copy()
    customer_list = customer_list.sort_values(
        by=["Churn Probability (%)", "Monthly Charges"],
        ascending=[False, False]
    )

    st.dataframe(customer_list, width="stretch", hide_index=True)

    csv_data = customer_list.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Segmented Customer List",
        data=csv_data,
        file_name="customer_segments_step16.csv",
        mime="text/csv",
        width="stretch"
    )

    st.success("✅ Step 16 completed: Customer Segmentation & Retention Dashboard is now available.")

# ============================================================
# STEP 17 - BUSINESS INTELLIGENCE & CHURN TRENDS
# ============================================================
def show_business_intelligence():
    page_header(
        "📈 Business Intelligence Dashboard",
        "Track churn trends, customer value, revenue at risk, and prediction activity."
    )

    history_df = load_prediction_history()

    if history_df.empty:
        st.info("Business intelligence will appear after you make at least one customer prediction.")
        return

    df = history_df.copy()

    # Safely convert numeric and date fields.
    for col in ["Tenure (Months)", "Monthly Charges", "Total Charges",
                "Churn Probability (%)", "No Churn Probability (%)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Time" in df.columns:
        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
    else:
        df["Time"] = pd.NaT

    df["Risk Level"] = df.get("Risk Level", "LOW").astype(str).str.upper()
    df["Prediction"] = df.get("Prediction", "Customer Will Not Churn").astype(str)

    # Use latest prediction per customer for customer-level KPIs.
    latest_df = df.sort_values("Time", ascending=False).drop_duplicates(
        subset=["Customer ID"], keep="first"
    ).copy() if "Customer ID" in df.columns else df.copy()

    # ------------------------------------------------------------
    # Filters
    # ------------------------------------------------------------
    st.subheader("🔎 Business Filters")
    f1, f2, f3, f4 = st.columns(4)

    with f1:
        risk_options = ["All"] + sorted(df["Risk Level"].dropna().unique().tolist())
        selected_risk = st.selectbox("Risk Level", risk_options, key="step17_risk")

    with f2:
        contract_values = sorted(df["Contract"].dropna().astype(str).unique().tolist()) if "Contract" in df else []
        selected_contract = st.selectbox("Contract", ["All"] + contract_values, key="step17_contract")

    with f3:
        prediction_values = sorted(df["Prediction"].dropna().unique().tolist())
        selected_prediction = st.selectbox("Prediction", ["All"] + prediction_values, key="step17_prediction")

    with f4:
        if df["Time"].notna().any():
            min_date = df["Time"].min().date()
            max_date = df["Time"].max().date()
            date_range = st.date_input(
                "Prediction Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
                key="step17_dates"
            )
        else:
            date_range = None
            st.caption("No valid prediction dates available.")

    filtered = df.copy()

    if selected_risk != "All":
        filtered = filtered[filtered["Risk Level"] == selected_risk]
    if selected_contract != "All" and "Contract" in filtered.columns:
        filtered = filtered[filtered["Contract"].astype(str) == selected_contract]
    if selected_prediction != "All":
        filtered = filtered[filtered["Prediction"] == selected_prediction]

    if date_range is not None and len(date_range) == 2:
        start_date, end_date = date_range
        filtered = filtered[
            filtered["Time"].dt.date.between(start_date, end_date)
        ]

    if filtered.empty:
        st.warning("No records match the selected business filters.")
        return

    # Latest customer records under the selected filters.
    filtered_latest = filtered.sort_values("Time", ascending=False).drop_duplicates(
        subset=["Customer ID"], keep="first"
    ).copy() if "Customer ID" in filtered.columns else filtered.copy()

    # ------------------------------------------------------------
    # KPI cards
    # ------------------------------------------------------------
    customer_count = len(filtered_latest)
    prediction_count = len(filtered)
    churn_count = int((filtered_latest["Prediction"] == "Customer Will Churn").sum())
    high_risk_count = int((filtered_latest["Risk Level"] == "HIGH").sum())
    avg_probability = float(filtered_latest["Churn Probability (%)"].mean())
    monthly_revenue = float(filtered_latest["Monthly Charges"].sum())

    # Revenue at risk is an analytical estimate: monthly charges multiplied
    # by the model's predicted churn probability for each customer.
    revenue_at_risk = float(
        (filtered_latest["Monthly Charges"].fillna(0) *
         filtered_latest["Churn Probability (%)"].fillna(0) / 100).sum()
    )

    st.divider()
    st.subheader("📊 Business KPIs")
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Customers in View", f"{customer_count:,}")
    with k2:
        st.metric("Predicted Churn", f"{churn_count:,}")
    with k3:
        st.metric("High-Risk Customers", f"{high_risk_count:,}")
    with k4:
        st.metric("Avg. Churn Probability", f"{avg_probability:.2f}%")

    k5, k6, k7 = st.columns(3)
    with k5:
        st.metric("Monthly Charges in View", f"${monthly_revenue:,.2f}")
    with k6:
        st.metric("Estimated Revenue at Risk", f"${revenue_at_risk:,.2f}")
    with k7:
        st.metric("Prediction Records", f"{prediction_count:,}")

    st.caption(
        "Estimated revenue at risk is a simple analytical estimate based on monthly charges × predicted churn probability; it is not a forecast of actual lost revenue."
    )

    # ------------------------------------------------------------
    # Trend charts
    # ------------------------------------------------------------
    st.divider()
    st.subheader("📈 Churn & Prediction Trends")

    trend_df = filtered.dropna(subset=["Time"]).copy()
    if not trend_df.empty:
        trend_df["Date"] = trend_df["Time"].dt.date
        daily = trend_df.groupby("Date").agg(
            Predictions=("Prediction", "size"),
            Churned=("Prediction", lambda x: (x == "Customer Will Churn").sum()),
            Average_Churn_Probability=("Churn Probability (%)", "mean")
        ).reset_index()
        daily["Churn Rate (%)"] = np.where(
            daily["Predictions"] > 0,
            daily["Churned"] / daily["Predictions"] * 100,
            0
        )

        trend_col1, trend_col2 = st.columns(2)
        with trend_col1:
            fig_trend = px.line(
                daily,
                x="Date",
                y=["Predictions", "Churned"],
                markers=True,
                title="Prediction Activity Over Time"
            )
            fig_trend.update_layout(
                height=430,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f8fafc"),
                yaxis_title="Customers",
                legend_title=""
            )
            st.plotly_chart(fig_trend, width="stretch")

        with trend_col2:
            fig_probability = px.line(
                daily,
                x="Date",
                y="Average_Churn_Probability",
                markers=True,
                title="Average Churn Probability Trend"
            )
            fig_probability.update_traces(
                hovertemplate="Date: %{x}<br>Average Churn Probability: %{y:.2f}%<extra></extra>"
            )
            fig_probability.update_layout(
                height=430,
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#f8fafc"),
                yaxis=dict(title="Average Churn Probability (%)", range=[0, 100]),
                xaxis_title="Date",
                showlegend=False
            )
            st.plotly_chart(fig_probability, width="stretch")

        fig_rate = px.area(
            daily,
            x="Date",
            y="Churn Rate (%)",
            title="Predicted Churn Rate Over Time"
        )
        fig_rate.update_layout(
            height=400,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"),
            yaxis=dict(title="Predicted Churn Rate (%)", range=[0, 100]),
            xaxis_title="Date"
        )
        st.plotly_chart(fig_rate, width="stretch")
    else:
        st.info("Trend charts require valid prediction timestamps.")

    # ------------------------------------------------------------
    # Risk and value analysis
    # ------------------------------------------------------------
    st.divider()
    st.subheader("💰 Revenue & Risk Analysis")
    analysis_col1, analysis_col2 = st.columns(2)

    risk_summary = (
        filtered_latest.groupby("Risk Level", dropna=False)
        .agg(
            Customers=("Customer ID", "count"),
            Monthly_Charges=("Monthly Charges", "sum"),
            Average_Churn_Probability=("Churn Probability (%)", "mean")
        )
        .reset_index()
    )
    risk_summary["Monthly_Charges"] = risk_summary["Monthly_Charges"].fillna(0)
    risk_summary["Estimated_Revenue_at_Risk"] = (
        risk_summary["Monthly_Charges"] * risk_summary["Average_Churn_Probability"] / 100
    )

    with analysis_col1:
        fig_risk = px.bar(
            risk_summary,
            x="Risk Level",
            y="Customers",
            text="Customers",
            title="Customers by Risk Level"
        )
        fig_risk.update_traces(textposition="outside")
        fig_risk.update_layout(
            height=430,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"),
            yaxis_title="Customers",
            xaxis_title="",
            showlegend=False
        )
        st.plotly_chart(fig_risk, width="stretch")

    with analysis_col2:
        revenue_chart = risk_summary.melt(
            id_vars=["Risk Level"],
            value_vars=["Monthly_Charges", "Estimated_Revenue_at_Risk"],
            var_name="Metric",
            value_name="Amount"
        )
        revenue_chart["Metric"] = revenue_chart["Metric"].replace({
            "Monthly_Charges": "Monthly Charges",
            "Estimated_Revenue_at_Risk": "Estimated Revenue at Risk"
        })
        fig_revenue = px.bar(
            revenue_chart,
            x="Risk Level",
            y="Amount",
            color="Metric",
            barmode="group",
            title="Monthly Charges vs Estimated Revenue at Risk"
        )
        fig_revenue.update_layout(
            height=430,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#f8fafc"),
            yaxis_title="Amount",
            xaxis_title="",
            legend_title=""
        )
        st.plotly_chart(fig_revenue, width="stretch")

    # ------------------------------------------------------------
    # Top accounts requiring attention
    # ------------------------------------------------------------
    st.divider()
    st.subheader("🚨 Customers Requiring Attention")

    attention = filtered_latest.copy()
    attention["Estimated Revenue at Risk"] = (
        attention["Monthly Charges"].fillna(0) *
        attention["Churn Probability (%)"].fillna(0) / 100
    )
    attention = attention.sort_values(
        by=["Churn Probability (%)", "Estimated Revenue at Risk"],
        ascending=[False, False]
    )

    attention_cols = [
        "Customer ID", "Customer Name", "Risk Level", "Churn Probability (%)",
        "Monthly Charges", "Estimated Revenue at Risk", "Contract",
        "Tenure (Months)"
    ]
    attention_cols = [c for c in attention_cols if c in attention.columns]
    attention_display = attention[attention_cols].head(20).copy()

    st.dataframe(attention_display, width="stretch", hide_index=True)

    attention_csv = attention_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Download Business Intelligence Report",
        data=attention_csv,
        file_name="customer_business_intelligence_step17.csv",
        mime="text/csv",
        width="stretch"
    )

    st.success("✅ Step 17 completed: Business Intelligence & Churn Trends Dashboard is now available.")

# ============================================================
# STEP 8 - PAGE ROUTER
# ============================================================
# IMPORTANT:
# Save this file as: <project_folder>/src/app.py
# Run from the project folder:
#     streamlit run src/app.py
if selected_page == "🏠 Dashboard":
    show_dashboard()
elif selected_page == "👤 Customer Profile":
    show_customer_profile()
elif selected_page == "🌐 Customer 360":
    show_customer_360()
elif selected_page == "🎯 Customer Segmentation":
    show_segmentation()
elif selected_page == "📈 Business Intelligence":
    show_business_intelligence()
elif selected_page == "🔮 Churn Prediction":
    show_prediction()
elif selected_page == "🧪 Model Evaluation":
    show_evaluation()
elif selected_page == "🗃️ Prediction History":
    show_history() if IS_ADMIN else st.error("Admin access required.")
elif selected_page == "📊 Customer Analytics":
    show_analytics() if IS_ADMIN else st.error("Admin access required.")

st.divider()
render_html("""
<div class="footer">📊 Customer Churn AI · Random Forest Machine Learning · Streamlit · Step 17</div>
""")
