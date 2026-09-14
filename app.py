import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Quiz Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

    /* ---------- Main page ---------- */

    .stApp {
        background-color: #f5f7fa;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }


    /* ---------- Header ---------- */

    .dashboard-header {
        background: white;
        padding: 25px 30px;
        border-radius: 16px;
        margin-bottom: 20px;
        border: 1px solid #e8ebef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }

    .dashboard-title {
        font-size: 32px;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 4px;
    }

    .dashboard-subtitle {
        font-size: 15px;
        color: #6b7280;
    }


    /* ---------- Section titles ---------- */

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #1f2937;
        margin-top: 25px;
        margin-bottom: 12px;
    }


    /* ---------- KPI cards ---------- */

    .kpi-card {
        background: white;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #e8ebef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        min-height: 125px;
    }

    .kpi-label {
        font-size: 14px;
        color: #6b7280;
        margin-bottom: 8px;
        font-weight: 500;
    }

    .kpi-value {
        font-size: 30px;
        font-weight: 700;
        color: #111827;
    }

    .kpi-small {
        font-size: 13px;
        color: #6b7280;
        margin-top: 4px;
    }


    /* ---------- Leader cards ---------- */

    .leader-card {
        background: white;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #e8ebef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        min-height: 145px;
    }

    .leader-title {
        font-size: 13px;
        color: #6b7280;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .leader-name {
        font-size: 19px;
        font-weight: 700;
        color: #111827;
        margin-bottom: 5px;
    }

    .leader-value {
        font-size: 14px;
        color: #4b5563;
    }


    /* ---------- General cards ---------- */

    .dash-card {
        background: white;
        padding: 20px;
        border-radius: 14px;
        border: 1px solid #e8ebef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }


    /* ---------- Alert cards ---------- */

    .attention-card {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        padding: 18px;
        border-radius: 12px;
        margin-bottom: 10px;
    }

    .success-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 18px;
        border-radius: 12px;
    }


    /* ---------- File uploader ---------- */

    [data-testid="stFileUploader"] {
        background: white;
        border-radius: 14px;
        padding: 10px;
    }


    /* ---------- Dataframe ---------- */

    [data-testid="stDataFrame"] {
        border-radius: 12px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_duration(value):
    """
    Convert duration values such as:
    17:25
    01:17:25
    9:19
    into seconds.
    """

    if pd.isna(value):
        return np.nan

    value = str(value).strip()

    if value == "":
        return np.nan

    # Already numeric
    if isinstance(value, (int, float)):
        return float(value)

    parts = value.split(":")

    try:
        if len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds

        elif len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds

    except ValueError:
        return np.nan

    return np.nan


def seconds_to_time(seconds):
    """Convert seconds into MM:SS or HH:MM:SS."""

    if pd.isna(seconds):
        return "N/A"

    seconds = int(round(seconds))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    return f"{minutes:02d}:{secs:02d}"


def get_participant_name(row):
    """Create participant display name."""

    first = str(row.get("First name", "")).strip()
    last = str(row.get("Last name", "")).strip()

    name = f"{first} {last}".strip()

    if name:
        return name

    if "Email" in row:
        return str(row["Email"])

    return "Unknown"


def load_file(uploaded_file):
    """Read CSV or Excel file."""

    if uploaded_file.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded_file)

    elif uploaded_file.name.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)

    return None


def find_score_column(df):
    """Find the score column automatically."""

    possible_columns = [
        "Grade/15.00",
        "Grade",
        "Score",
        "Marks",
        "Total Score"
    ]

    for col in possible_columns:
        if col in df.columns:
            return col

    return None


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="dashboard-header">

    <div class="dashboard-title">
        📊 Quiz Performance Dashboard
    </div>

    <div class="dashboard-subtitle">
        Participant performance, score, time and question-level analytics
    </div>

</div>
""", unsafe_allow_html=True)


# ============================================================
# FILE UPLOAD
# ============================================================

uploaded_file = st.file_uploader(
    "Upload Quiz Worksheet",
    type=["csv", "xlsx", "xls"],
    help="Upload the latest quiz result CSV or Excel worksheet."
)


if uploaded_file is None:

    st.markdown("""
    <div class="dash-card">

    <h3>📁 Upload your quiz results</h3>

    <p>
    Upload the CSV or Excel worksheet containing participant attempts.
    The dashboard will automatically calculate all statistics from the
    uploaded file.
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

try:

    df = load_file(uploaded_file)

except Exception as e:

    st.error(f"Could not read the file: {e}")
    st.stop()


if df is None or df.empty:

    st.error("The uploaded file is empty.")
    st.stop()


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = df.columns.astype(str).str.strip()


# ============================================================
# FIND SCORE COLUMN
# ============================================================

score_column = find_score_column(df)

if score_column is None:

    st.error(
        "Could not find the score column. "
        "Expected something like 'Grade/15.00', 'Grade' or 'Score'."
    )

    st.write("Columns found in your file:")
    st.write(list(df.columns))

    st.stop()


# ============================================================
# CREATE PARTICIPANT NAME
# ============================================================

if "First name" in df.columns and "Last name" in df.columns:

    df["Participant"] = df.apply(get_participant_name, axis=1)

elif "Name" in df.columns:

    df["Participant"] = df["Name"].astype(str)

elif "Email" in df.columns:

    df["Participant"] = df["Email"].astype(str)

else:

    df["Participant"] = "Participant " + (
        df.index + 1
    ).astype(str)


# ============================================================
# SCORE
# ============================================================

df["Score"] = pd.to_numeric(
    df[score_column],
    errors="coerce"
)

df = df.dropna(subset=["Score"]).copy()

df["Score"] = df["Score"].clip(lower=0, upper=15)


# ============================================================
# DURATION
# ============================================================

if "Duration" in df.columns:

    df["Duration_Seconds"] = df["Duration"].apply(parse_duration)

else:

    df["Duration_Seconds"] = np.nan


# ============================================================
# PERFECT ATTEMPT
# ============================================================

df["Perfect"] = df["Score"].eq(15)


# ============================================================
# UNIQUE PARTICIPANT IDENTIFIER
# ============================================================

if "Email" in df.columns:

    df["Participant_ID"] = df["Email"].fillna(
        df["Participant"]
    ).astype(str)

else:

    df["Participant_ID"] = df["Participant"].astype(str)


# ============================================================
# KPI CALCULATIONS
# ============================================================

total_attempts = len(df)

total_participants = df["Participant_ID"].nunique()

average_score = df["Score"].mean()

highest_score = df["Score"].max()

lowest_score = df["Score"].min()

perfect_attempts = int(df["Perfect"].sum())


# ============================================================
# KPI SECTION
# ============================================================

st.markdown(
    '<div class="section-title">📌 Overview</div>',
    unsafe_allow_html=True
)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)


with kpi1:

    st.markdown(f"""
    <div class="kpi-card">

        <div class="kpi-label">👥 Participants</div>

        <div class="kpi-value">
            {total_participants}
        </div>

        <div class="kpi-small">
            Unique participants
        </div>

    </div>
    """, unsafe_allow_html=True)


with kpi2:

    st.markdown(f"""
    <div class="kpi-card">

        <div class="kpi-label">📝 Total Attempts</div>

        <div class="kpi-value">
            {total_attempts}
        </div>

        <div class="kpi-small">
            Quiz attempts recorded
        </div>

    </div>
    """, unsafe_allow_html=True)


with kpi3:

    st.markdown(f"""
    <div class="kpi-card">

        <div class="kpi-label">📊 Average Score</div>

        <div class="kpi-value">
            {average_score:.2f}/15
        </div>

        <div class="kpi-small">
            Across all attempts
        </div>

    </div>
    """, unsafe_allow_html=True)


with kpi4:

    st.markdown(f"""
    <div class="kpi-card">

        <div class="kpi-label">🏆 Highest Score</div>

        <div class="kpi-value">
            {highest_score:.0f}/15
        </div>

        <div class="kpi-small">
            Best single attempt
        </div>

    </div>
    """, unsafe_allow_html=True)


with kpi5:

    st.markdown(f"""
    <div class="kpi-card">

        <div class="kpi-label">🎯 Perfect Attempts</div>

        <div class="kpi-value">
            {perfect_attempts}
        </div>

        <div class="kpi-small">
            Attempts scoring 15/15
        </div>

    </div>
    """, unsafe_allow_html=True)


# ============================================================
# PARTICIPANT SUMMARY
# ============================================================

summary = (
    df.groupby(["Participant_ID", "Participant"])
    .agg(
        Attempts=("Score", "count"),
        Average_Score=("Score", "mean"),
        Highest_Score=("Score", "max"),
        Lowest_Score=("Score", "min"),
        Perfect_15=("Perfect", "sum"),
        Average_Duration=("Duration_Seconds", "mean"),
        Shortest_Duration=("Duration_Seconds", "min")
    )
    .reset_index()
)


# ============================================================
# FIND SCORE AT SHORTEST ATTEMPT
# ============================================================

shortest_scores = []

for participant_id, group in df.groupby("Participant_ID"):

    valid = group.dropna(subset=["Duration_Seconds"])

    if len(valid) > 0:

        row = valid.loc[
            valid["Duration_Seconds"].idxmin()
        ]

        shortest_scores.append({
            "Participant_ID": participant_id,
            "Score_at_Shortest": row["Score"]
        })


shortest_scores_df = pd.DataFrame(shortest_scores)


if not shortest_scores_df.empty:

    summary = summary.merge(
        shortest_scores_df,
        on="Participant_ID",
        how="left"
    )

else:

    summary["Score_at_Shortest"] = np.nan


# ============================================================
# LEADERS
# ============================================================

highest_average_row = summary.loc[
    summary["Average_Score"].idxmax()
]

highest_single_row = df.loc[
    df["Score"].idxmax()
]


most_perfect_row = summary.loc[
    summary["Perfect_15"].idxmax()
]


# ============================================================
# PERFORMANCE LEADERS
# ============================================================

st.markdown(
    '<div class="section-title">🏅 Performance Leaders</div>',
    unsafe_allow_html=True
)

l1, l2, l3, l4 = st.columns(4)


with l1:

    st.markdown(f"""
    <div class="leader-card">

        <div class="leader-title">
            🥇 HIGHEST AVERAGE
        </div>

        <div class="leader-name">
            {highest_average_row["Participant"]}
        </div>

        <div class="leader-value">
            Average: {highest_average_row["Average_Score"]:.2f}/15
        </div>

    </div>
    """, unsafe_allow_html=True)


with l2:

    st.markdown(f"""
    <div class="leader-card">

        <div class="leader-title">
            🏆 HIGHEST SINGLE SCORE
        </div>

        <div class="leader-name">
            {highest_single_row["Participant"]}
        </div>

        <div class="leader-value">
            Score: {highest_single_row["Score"]:.0f}/15
        </div>

    </div>
    """, unsafe_allow_html=True)


with l3:

    st.markdown(f"""
    <div class="leader-card">

        <div class="leader-title">
            🎯 MOST 15/15 ATTEMPTS
        </div>

        <div class="leader-name">
            {most_perfect_row["Participant"]}
        </div>

        <div class="leader-value">
            {int(most_perfect_row["Perfect_15"])} perfect attempt(s)
        </div>

    </div>
    """, unsafe_allow_html=True)


# ============================================================
# FASTEST PERFECT ATTEMPT
# ============================================================

perfect_df = df[
    (df["Score"] == 15) &
    (df["Duration_Seconds"].notna())
].copy()


with l4:

    if not perfect_df.empty:

        fastest_perfect = perfect_df.loc[
            perfect_df["Duration_Seconds"].idxmin()
        ]

        st.markdown(f"""
        <div class="leader-card">

            <div class="leader-title">
                ⚡ FASTEST 15/15
            </div>

            <div class="leader-name">
                {fastest_perfect["Participant"]}
            </div>

            <div class="leader-value">
                {seconds_to_time(fastest_perfect["Duration_Seconds"])}
            </div>

        </div>
        """, unsafe_allow_html=True)

    else:

        st.markdown("""
        <div class="leader-card">

            <div class="leader-title">
                ⚡ FASTEST 15/15
            </div>

            <div class="leader-name">
                No perfect attempt
            </div>

            <div class="leader-value">
                No 15/15 attempt available
            </div>

        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TIME PERFORMANCE
# ============================================================

st.markdown(
    '<div class="section-title">⏱️ Time & Performance Analysis</div>',
    unsafe_allow_html=True
)


# Fastest overall attempt
valid_duration = df.dropna(
    subset=["Duration_Seconds"]
).copy()


if not valid_duration.empty:

    fastest_overall = valid_duration.loc[
        valid_duration["Duration_Seconds"].idxmin()
    ]

else:

    fastest_overall = None


# Fastest high-score attempt
high_score_df = valid_duration[
    valid_duration["Score"] >= 13
].copy()


if not high_score_df.empty:

    fastest_high_score = high_score_df.loc[
        high_score_df["Duration_Seconds"].idxmin()
    ]

else:

    fastest_high_score = None


t1, t2, t3 = st.columns(3)


with t1:

    if fastest_overall is not None:

        st.markdown(f"""
        <div class="dash-card">

        <b>⚡ Fastest Overall Attempt</b>

        <h2>{seconds_to_time(fastest_overall["Duration_Seconds"])}</h2>

        <p>
        <b>{fastest_overall["Participant"]}</b><br>
        Score: {fastest_overall["Score"]:.0f}/15
        </p>

        </div>
        """, unsafe_allow_html=True)

    else:

        st.info("Duration data unavailable.")


with t2:

    if fastest_high_score is not None:

        st.markdown(f"""
        <div class="dash-card">

        <b>🚀 Fastest High-Score Attempt</b>

        <h2>{seconds_to_time(fastest_high_score["Duration_Seconds"])}</h2>

        <p>
        <b>{fastest_high_score["Participant"]}</b><br>
        Score: {fastest_high_score["Score"]:.0f}/15
        </p>

        </div>
        """, unsafe_allow_html=True)

    else:

        st.info("No attempt scoring 13/15 or above.")


with t3:

    person_perfect = df[
        (df["Participant_ID"] == most_perfect_row["Participant_ID"]) &
        (df["Score"] == 15) &
        (df["Duration_Seconds"].notna())
    ]

    if not person_perfect.empty:

        shortest_person_perfect = person_perfect.loc[
            person_perfect["Duration_Seconds"].idxmin()
        ]

        st.markdown(f"""
        <div class="dash-card">

        <b>🎯 Shortest 15/15 by Top Performer</b>

        <h2>
        {seconds_to_time(shortest_person_perfect["Duration_Seconds"])}
        </h2>

        <p>
        <b>{most_perfect_row["Participant"]}</b><br>
        {int(most_perfect_row["Perfect_15"])} perfect attempt(s)
        </p>

        </div>
        """, unsafe_allow_html=True)

    else:

        st.info("No timed 15/15 attempt available.")


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

st.markdown(
    '<div class="section-title">📈 Score Distribution</div>',
    unsafe_allow_html=True
)

c1, c2 = st.columns(2)


with c1:

    score_counts = (
        df["Score"]
        .value_counts()
        .sort_index()
    )

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=score_counts.index,
            y=score_counts.values,
            text=score_counts.values,
            textposition="outside"
        )
    )

    fig.update_layout(
        title="Number of Attempts by Score",
        xaxis_title="Score",
        yaxis_title="Number of Attempts",
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


with c2:

    participant_chart = summary.sort_values(
        "Average_Score",
        ascending=False
    ).head(15)

    fig2 = go.Figure()

    fig2.add_trace(
        go.Bar(
            x=participant_chart["Average_Score"],
            y=participant_chart["Participant"],
            orientation="h",
            text=participant_chart["Average_Score"].round(2),
            textposition="outside"
        )
    )

    fig2.update_layout(
        title="Average Score by Participant",
        xaxis_title="Average Score",
        yaxis_title="",
        xaxis=dict(range=[0, 15]),
        template="plotly_white",
        height=400,
        margin=dict(l=20, r=60, t=60, b=20)
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


# ============================================================
# PARTICIPANT PERFORMANCE TABLE
# ============================================================

st.markdown(
    '<div class="section-title">👤 Participant Performance</div>',
    unsafe_allow_html=True
)


display_summary = summary.copy()

display_summary["Average Score"] = (
    display_summary["Average_Score"].round(2).astype(str)
    + "/15"
)

display_summary["Highest Score"] = (
    display_summary["Highest_Score"].round(0).astype(int).astype(str)
    + "/15"
)

display_summary["Lowest Score"] = (
    display_summary["Lowest_Score"].round(0).astype(int).astype(str)
    + "/15"
)

display_summary["Average Time"] = (
    display_summary["Average_Duration"]
    .apply(seconds_to_time)
)

display_summary["Fastest Time"] = (
    display_summary["Shortest_Duration"]
    .apply(seconds_to_time)
)

display_summary["Score at Fastest Time"] = (
    display_summary["Score_at_Shortest"]
    .apply(
        lambda x: f"{x:.0f}/15"
        if pd.notna(x)
        else "N/A"
    )
)


display_summary = display_summary[
    [
        "Participant",
        "Attempts",
        "Average Score",
        "Highest Score",
        "Lowest Score",
        "Perfect_15",
        "Average Time",
        "Fastest Time",
        "Score at Fastest Time"
    ]
].copy()


display_summary = display_summary.rename(
    columns={
        "Perfect_15": "15/15 Attempts"
    }
)


display_summary = display_summary.sort_values(
    "Average Score",
    ascending=False
)


st.dataframe(
    display_summary,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 15/15 ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">🎯 15/15 Performance Analysis</div>',
    unsafe_allow_html=True
)


p1, p2 = st.columns(2)


with p1:

    if perfect_df.empty:

        st.markdown("""
        <div class="attention-card">

        <b>No Perfect Attempts</b>

        <p>
        No participant has achieved 15/15 in the uploaded worksheet.
        </p>

        </div>
        """, unsafe_allow_html=True)

    else:

        perfect_counts = (
            perfect_df.groupby("Participant")
            .size()
            .sort_values(ascending=False)
            .reset_index(name="Perfect Attempts")
        )

        fig3 = go.Figure()

        fig3.add_trace(
            go.Bar(
                x=perfect_counts["Participant"],
                y=perfect_counts["Perfect Attempts"],
                text=perfect_counts["Perfect Attempts"],
                textposition="outside"
            )
        )

        fig3.update_layout(
            title="15/15 Attempts by Participant",
            xaxis_title="Participant",
            yaxis_title="Number of 15/15 Attempts",
            template="plotly_white",
            height=400,
            margin=dict(l=20, r=20, t=60, b=80)
        )

        st.plotly_chart(
            fig3,
            use_container_width=True
        )


with p2:

    if not perfect_df.empty:

        perfect_display = perfect_df[
            [
                "Participant",
                "Score",
                "Duration"
            ]
        ].copy()

        perfect_display = perfect_display.sort_values(
            "Participant"
        )

        st.markdown(
            '<div class="dash-card"><b>Perfect Attempt Details</b></div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            perfect_display,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# QUESTION ANALYSIS
# ============================================================

question_columns = [
    f"Q{i}" for i in range(1, 16)
    if f"Q{i}" in df.columns
]


if question_columns:

    st.markdown(
        '<div class="section-title">❓ Question-Level Analysis</div>',
        unsafe_allow_html=True
    )

    question_results = []

    for q in question_columns:

        values = pd.to_numeric(
            df[q],
            errors="coerce"
        )

        valid_values = values.dropna()

        if len(valid_values) > 0:

            # Assumes 1 = correct and 0 = incorrect
            correct_percentage = (
                (valid_values == 1).mean() * 100
            )

            question_results.append({
                "Question": q,
                "Correct %": correct_percentage
            })


    question_df = pd.DataFrame(question_results)


    if not question_df.empty:

        easiest_question = question_df.loc[
            question_df["Correct %"].idxmax()
        ]

        hardest_question = question_df.loc[
            question_df["Correct %"].idxmin()
        ]


        q1, q2 = st.columns(2)


        with q1:

            st.markdown(f"""
            <div class="success-card">

            <b>🟢 Easiest Question</b>

            <h2>{easiest_question["Question"]}</h2>

            <p>
            Correct response rate:
            <b>{easiest_question["Correct %"]:.1f}%</b>
            </p>

            </div>
            """, unsafe_allow_html=True)


        with q2:

            st.markdown(f"""
            <div class="attention-card">

            <b>🔴 Most Difficult Question</b>

            <h2>{hardest_question["Question"]}</h2>

            <p>
            Correct response rate:
            <b>{hardest_question["Correct %"]:.1f}%</b>
            </p>

            </div>
            """, unsafe_allow_html=True)


        fig4 = go.Figure()

        fig4.add_trace(
            go.Bar(
                x=question_df["Question"],
                y=question_df["Correct %"],
                text=question_df["Correct %"].round(1),
                texttemplate="%{text}%",
                textposition="outside"
            )
        )

        fig4.update_layout(
            title="Question Correctness Percentage",
            xaxis_title="Question",
            yaxis_title="Correct (%)",
            yaxis=dict(range=[0, 110]),
            template="plotly_white",
            height=450,
            margin=dict(l=20, r=20, t=60, b=20)
        )

        st.plotly_chart(
            fig4,
            use_container_width=True
        )


# ============================================================
# NEEDS ATTENTION
# ============================================================

st.markdown(
    '<div class="section-title">⚠️ Participants Needing Attention</div>',
    unsafe_allow_html=True
)


attention = summary[
    summary["Average_Score"] < 10
].copy()


if attention.empty:

    st.markdown("""
    <div class="success-card">

    <b>✅ Good Overall Performance</b>

    <p>
    No participant has an average score below 10/15.
    </p>

    </div>
    """, unsafe_allow_html=True)

else:

    attention_display = attention[
        [
            "Participant",
            "Attempts",
            "Average_Score",
            "Highest_Score",
            "Lowest_Score"
        ]
    ].copy()

    attention_display["Average Score"] = (
        attention_display["Average_Score"].round(2)
    )

    attention_display["Highest"] = (
        attention_display["Highest_Score"].astype(int)
    )

    attention_display["Lowest"] = (
        attention_display["Lowest_Score"].astype(int)
    )

    attention_display = attention_display[
        [
            "Participant",
            "Attempts",
            "Average Score",
            "Highest",
            "Lowest"
        ]
    ]

    st.dataframe(
        attention_display,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# TEAM ANALYSIS
# ============================================================

team_column = None

for col in ["Team", "team", "Group", "group", "Team Name", "Team_Name"]:

    if col in df.columns:
        team_column = col
        break


st.markdown(
    '<div class="section-title">👥 Team Analysis</div>',
    unsafe_allow_html=True
)


if team_column is None:

    st.markdown("""
    <div class="dash-card">

    <b>Team information is not available yet.</b>

    <p>
    The current worksheet does not contain a Team or Group column.
    Team analysis will automatically appear when you upload a worksheet
    containing team information.
    </p>

    </div>
    """, unsafe_allow_html=True)


else:

    team_summary = (
        df.groupby(team_column)
        .agg(
            Participants=("Participant_ID", "nunique"),
            Attempts=("Score", "count"),
            Average_Score=("Score", "mean"),
            Highest_Score=("Score", "max"),
            Perfect_Attempts=("Perfect", "sum"),
            Average_Duration=("Duration_Seconds", "mean")
        )
        .reset_index()
    )

    team_summary["Average Time"] = (
        team_summary["Average_Duration"]
        .apply(seconds_to_time)
    )

    team_display = team_summary[
        [
            team_column,
            "Participants",
            "Attempts",
            "Average_Score",
            "Highest_Score",
            "Perfect_Attempts",
            "Average Time"
        ]
    ].copy()

    team_display["Average_Score"] = (
        team_display["Average_Score"].round(2)
    )

    team_display = team_display.rename(
        columns={
            team_column: "Team",
            "Average_Score": "Average Score",
            "Highest_Score": "Highest Score",
            "Perfect_Attempts": "15/15 Attempts"
        }
    )

    st.dataframe(
        team_display,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown("""
<div style="text-align:center; color:#6b7280; font-size:13px;">

    📊 Quiz Performance Analytics Dashboard
    <br>
    Automatically generated from the uploaded worksheet

</div>
""", unsafe_allow_html=True)
