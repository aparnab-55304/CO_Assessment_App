import streamlit as st
import pandas as pd

# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Quiz Performance Analytics",
    page_icon="📊",
    layout="wide"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

    /* Main background */
    .stApp {
        background-color: #f5f7fb;
    }

    /* Main title */
    .main-title {
        font-size: 42px;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 17px;
        color: #6b7280;
        margin-bottom: 25px;
    }

    /* Section headings */
    .section-title {
        font-size: 25px;
        font-weight: 650;
        color: #1f2937;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    /* KPI cards */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.05);
        text-align: center;
    }

    .metric-label {
        font-size: 15px;
        color: #6b7280;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 700;
        color: #111827;
    }

    /* Leader cards */
    .leader-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0px 3px 10px rgba(0,0,0,0.05);
        min-height: 130px;
    }

    .leader-title {
        font-size: 15px;
        color: #6b7280;
    }

    .leader-name {
        font-size: 22px;
        font-weight: 700;
        color: #111827;
        margin-top: 8px;
    }

    .leader-value {
        font-size: 18px;
        color: #374151;
        margin-top: 5px;
    }

</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================

st.markdown(
    '<div class="main-title">📊 Quiz Performance Analytics</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Interactive analysis of participant attempts, scores and performance'
    '</div>',
    unsafe_allow_html=True
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("📁 Dashboard Controls")

    uploaded_file = st.file_uploader(
        "Upload Quiz Worksheet",
        type=["csv", "xlsx"]
    )

    st.markdown("---")

    st.info(
        "Upload your latest worksheet to automatically update "
        "the dashboard."
    )


# =========================================================
# NO FILE MESSAGE
# =========================================================

if uploaded_file is None:

    st.markdown(
        """
        <div class="leader-card">
            <h3>👆 Upload your worksheet</h3>
            <p>
            Upload a CSV or Excel file from the sidebar
            to begin analysing quiz performance.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.stop()


# =========================================================
# READ FILE
# =========================================================

try:

    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    else:
        df = pd.read_excel(uploaded_file)

except Exception as e:

    st.error(f"Unable to read the file: {e}")
    st.stop()


# =========================================================
# CREATE PARTICIPANT NAME
# =========================================================

if "First name" in df.columns and "Last name" in df.columns:

    df["Participant"] = (
        df["First name"].fillna("").astype(str)
        + " "
        + df["Last name"].fillna("").astype(str)
    ).str.strip()

elif "First name" in df.columns:

    df["Participant"] = (
        df["First name"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

else:

    st.error(
        "The worksheet must contain a First name column."
    )

    st.stop()


# =========================================================
# SCORE
# =========================================================

if "Grade/15.00" not in df.columns:

    st.error(
        "The worksheet must contain the Grade/15.00 column."
    )

    st.stop()


df["Score"] = pd.to_numeric(
    df["Grade/15.00"],
    errors="coerce"
)


# =========================================================
# KPI CALCULATIONS
# =========================================================

total_attempts = len(df)

total_participants = df["Participant"].nunique()

average_score = df["Score"].mean()

highest_score = df["Score"].max()

perfect_attempts = (df["Score"] == 15).sum()


# =========================================================
# KPI SECTION
# =========================================================

st.markdown(
    '<div class="section-title">📌 Performance Overview</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">👥 Participants</div>
            <div class="metric-value">{total_participants}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col2:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">📝 Attempts</div>
            <div class="metric-value">{total_attempts}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col3:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">⭐ Average Score</div>
            <div class="metric-value">{average_score:.2f}/15</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col4:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">🏆 Highest Score</div>
            <div class="metric-value">{highest_score:.0f}/15</div>
        </div>
        """,
        unsafe_allow_html=True
    )


with col5:

    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">🎯 Perfect Attempts</div>
            <div class="metric-value">{perfect_attempts}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# =========================================================
# PARTICIPANT SUMMARY
# =========================================================

participant_summary = (
    df.groupby("Participant")
    .agg(
        Attempts=("Score", "count"),
        Average_Score=("Score", "mean"),
        Highest_Score=("Score", "max"),
        Lowest_Score=("Score", "min"),
        Perfect_15=("Score", lambda x: (x == 15).sum())
    )
    .reset_index()
)

participant_summary["Average_Score"] = (
    participant_summary["Average_Score"].round(2)
)

participant_summary = participant_summary.sort_values(
    "Average_Score",
    ascending=False
)


# =========================================================
# LEADERS
# =========================================================

st.markdown(
    '<div class="section-title">🏆 Performance Leaders</div>',
    unsafe_allow_html=True
)

leader1, leader2, leader3 = st.columns(3)


# Highest average
top_average = participant_summary.iloc[0]

with leader1:

    st.markdown(
        f"""
        <div class="leader-card">
            <div class="leader-title">🥇 Highest Average Score</div>
            <div class="leader-name">
                {top_average['Participant']}
            </div>
            <div class="leader-value">
                {top_average['Average_Score']}/15
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# Highest single score
highest_row = df.loc[df["Score"].idxmax()]

with leader2:

    st.markdown(
        f"""
        <div class="leader-card">
            <div class="leader-title">⭐ Highest Single Score</div>
            <div class="leader-name">
                {highest_row['Participant']}
            </div>
            <div class="leader-value">
                {highest_row['Score']:.0f}/15
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# Most 15/15
perfect_summary = participant_summary[
    participant_summary["Perfect_15"] > 0
].sort_values(
    "Perfect_15",
    ascending=False
)

with leader3:

    if len(perfect_summary) > 0:

        top_perfect = perfect_summary.iloc[0]

        st.markdown(
            f"""
            <div class="leader-card">
                <div class="leader-title">
                    🎯 Most 15/15 Attempts
                </div>
                <div class="leader-name">
                    {top_perfect['Participant']}
                </div>
                <div class="leader-value">
                    {int(top_perfect['Perfect_15'])} perfect attempt(s)
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(
            """
            <div class="leader-card">
                <div class="leader-title">
                    🎯 Most 15/15 Attempts
                </div>
                <div class="leader-name">
                    None yet
                </div>
                <div class="leader-value">
                    No perfect scores
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )


# =========================================================
# PARTICIPANT TABLE
# =========================================================

st.markdown(
    '<div class="section-title">👤 Participant Performance</div>',
    unsafe_allow_html=True
)

st.dataframe(
    participant_summary,
    use_container_width=True,
    hide_index=True
)
