import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# PAGE SETTINGS
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

    /* Main background */
    .stApp {
        background-color: #f5f7fa;
    }

    .block-container {
        max-width: 1500px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    /* Header */
    .header-card {
        background-color: white;
        padding: 28px 32px;
        border-radius: 18px;
        border: 1px solid #e5e7eb;
        margin-bottom: 20px;
        box-shadow: 0px 3px 12px rgba(0,0,0,0.05);
    }

    .header-title {
        font-size: 32px;
        font-weight: 700;
        color: #1f2937;
        margin: 0;
    }

    .header-subtitle {
        color: #6b7280;
        font-size: 15px;
        margin-top: 5px;
    }

    /* Section */
    .section-title {
        font-size: 22px;
        font-weight: 700;
        color: #1f2937;
        margin-top: 28px;
        margin-bottom: 14px;
    }

    /* KPI cards */
    .kpi {
        background: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        min-height: 125px;
        box-shadow: 0px 3px 12px rgba(0,0,0,0.04);
    }

    .kpi-label {
        color: #6b7280;
        font-size: 14px;
        font-weight: 600;
    }

    .kpi-value {
        color: #111827;
        font-size: 30px;
        font-weight: 700;
        margin-top: 7px;
    }

    .kpi-description {
        color: #9ca3af;
        font-size: 12px;
        margin-top: 4px;
    }

    /* Leader cards */
    .leader {
        background: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        min-height: 135px;
        box-shadow: 0px 3px 12px rgba(0,0,0,0.04);
    }

    .leader-label {
        color: #6b7280;
        font-size: 13px;
        font-weight: 600;
        text-transform: uppercase;
    }

    .leader-name {
        color: #111827;
        font-size: 19px;
        font-weight: 700;
        margin-top: 8px;
    }

    .leader-value {
        color: #4b5563;
        font-size: 14px;
        margin-top: 5px;
    }

    /* Information card */
    .info-card {
        background: white;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0px 3px 12px rgba(0,0,0,0.04);
    }

    /* Success */
    .success-card {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 18px;
        border-radius: 14px;
    }

    /* Warning */
    .warning-card {
        background: #fff7ed;
        border: 1px solid #fed7aa;
        padding: 18px;
        border-radius: 14px;
    }

</style>
""", unsafe_allow_html=True)


# ============================================================
# HEADER
# ============================================================

st.markdown("""
<div class="header-card">

    <div class="header-title">
        📊 Quiz Performance Dashboard
    </div>

    <div class="header-subtitle">
        Participant performance, attempts, scores, time and question analysis
    </div>

</div>
""", unsafe_allow_html=True)


# ============================================================
# FILE UPLOADER
# ============================================================

uploaded_file = st.file_uploader(
    "📁 Upload Quiz Results",
    type=["csv", "xlsx", "xls"],
    help="Upload the quiz result CSV or Excel worksheet."
)


# ============================================================
# NO FILE YET
# ============================================================

if uploaded_file is None:

    st.markdown("""
    <div class="info-card">

    <h3>📁 Upload your quiz worksheet</h3>

    <p>
    Upload the CSV or Excel file containing the quiz attempts.
    The dashboard will automatically calculate the results.
    </p>

    <p>
    <b>Supported:</b> CSV, XLSX, XLS
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ============================================================
# READ FILE
# ============================================================

try:

    if uploaded_file.name.lower().endswith(".csv"):

        df = pd.read_csv(uploaded_file)

    else:

        df = pd.read_excel(uploaded_file)

except Exception as error:

    st.error(f"Unable to read the file: {error}")
    st.stop()


# ============================================================
# BASIC CLEANING
# ============================================================

if df.empty:

    st.error("The uploaded worksheet is empty.")
    st.stop()


# Remove spaces around column names
df.columns = df.columns.astype(str).str.strip()


# ============================================================
# DISPLAY FILE INFORMATION
# ============================================================

st.caption(
    f"Loaded file: **{uploaded_file.name}**  |  "
    f"{len(df)} attempt(s) | {len(df.columns)} column(s)"
)


# ============================================================
# CREATE PARTICIPANT NAME
# ============================================================

if "First name" in df.columns and "Last name" in df.columns:

    df["Participant"] = (
        df["First name"].fillna("").astype(str).str.strip()
        + " "
        + df["Last name"].fillna("").astype(str).str.strip()
    ).str.strip()

elif "Name" in df.columns:

    df["Participant"] = (
        df["Name"].fillna("Unknown").astype(str)
    )

elif "Email" in df.columns:

    df["Participant"] = (
        df["Email"].fillna("Unknown").astype(str)
    )

else:

    df["Participant"] = [
        f"Participant {i+1}" for i in range(len(df))
    ]


# Replace empty names
df.loc[
    df["Participant"].isin(["", "nan", "None"]),
    "Participant"
] = "Unknown"


# ============================================================
# PARTICIPANT ID
# ============================================================

# Email is better for identifying the same person
# when multiple attempts exist.

if "Email" in df.columns:

    df["Participant_ID"] = (
        df["Email"]
        .fillna(df["Participant"])
        .astype(str)
        .str.strip()
    )

else:

    df["Participant_ID"] = df["Participant"]


# ============================================================
# FIND SCORE COLUMN
# ============================================================

score_column = None

possible_score_columns = [
    "Grade/15.00",
    "Grade",
    "Score",
    "Marks",
    "Total Score"
]

for column in possible_score_columns:

    if column in df.columns:

        score_column = column
        break


if score_column is None:

    st.error(
        "I could not find the score column."
    )

    st.write("Columns found in your worksheet:")

    st.write(list(df.columns))

    st.stop()


# ============================================================
# CONVERT SCORE TO NUMBER
# ============================================================

df["Score"] = pd.to_numeric(
    df[score_column],
    errors="coerce"
)


# Remove rows where score cannot be read
df = df.dropna(subset=["Score"]).copy()


# Keep scores between 0 and 15
df["Score"] = df["Score"].clip(0, 15)


# ============================================================
# PERFECT ATTEMPTS
# ============================================================

df["Perfect"] = df["Score"] == 15


# ============================================================
# DURATION CONVERSION
# ============================================================

def duration_to_seconds(value):

    if pd.isna(value):
        return None

    text = str(value).strip()

    if text == "":
        return None

    try:

        parts = text.split(":")

        if len(parts) == 2:

            minutes = int(parts[0])
            seconds = int(parts[1])

            return minutes * 60 + seconds

        elif len(parts) == 3:

            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])

            return (
                hours * 3600
                + minutes * 60
                + seconds
            )

    except:

        return None

    return None


if "Duration" in df.columns:

    df["Duration_Seconds"] = (
        df["Duration"].apply(duration_to_seconds)
    )

else:

    df["Duration_Seconds"] = None


# ============================================================
# FORMAT TIME
# ============================================================

def format_time(seconds):

    if pd.isna(seconds) or seconds is None:

        return "N/A"

    seconds = int(seconds)

    minutes = seconds // 60
    remaining_seconds = seconds % 60

    if minutes >= 60:

        hours = minutes // 60
        minutes = minutes % 60

        return f"{hours:02d}:{minutes:02d}:{remaining_seconds:02d}"

    return f"{minutes:02d}:{remaining_seconds:02d}"


# ============================================================
# OVERALL KPIs
# ============================================================

total_attempts = len(df)

total_participants = df["Participant_ID"].nunique()

average_score = df["Score"].mean()

highest_score = df["Score"].max()

perfect_count = int(df["Perfect"].sum())


# ============================================================
# OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">📌 Overview</div>',
    unsafe_allow_html=True
)


col1, col2, col3, col4, col5 = st.columns(5)


with col1:

    st.markdown(f"""
    <div class="kpi">

        <div class="kpi-label">
            👥 PARTICIPANTS
        </div>

        <div class="kpi-value">
            {total_participants}
        </div>

        <div class="kpi-description">
            Unique participants
        </div>

    </div>
    """, unsafe_allow_html=True)


with col2:

    st.markdown(f"""
    <div class="kpi">

        <div class="kpi-label">
            📝 ATTEMPTS
        </div>

        <div class="kpi-value">
            {total_attempts}
        </div>

        <div class="kpi-description">
            Total quiz attempts
        </div>

    </div>
    """, unsafe_allow_html=True)


with col3:

    st.markdown(f"""
    <div class="kpi">

        <div class="kpi-label">
            📊 AVERAGE SCORE
        </div>

        <div class="kpi-value">
            {average_score:.2f}/15
        </div>

        <div class="kpi-description">
            Across all attempts
        </div>

    </div>
    """, unsafe_allow_html=True)


with col4:

    st.markdown(f"""
    <div class="kpi">

        <div class="kpi-label">
            🏆 HIGHEST SCORE
        </div>

        <div class="kpi-value">
            {highest_score:.0f}/15
        </div>

        <div class="kpi-description">
            Best single attempt
        </div>

    </div>
    """, unsafe_allow_html=True)


with col5:

    st.markdown(f"""
    <div class="kpi">

        <div class="kpi-label">
            🎯 PERFECT ATTEMPTS
        </div>

        <div class="kpi-value">
            {perfect_count}
        </div>

        <div class="kpi-description">
            Attempts scoring 15/15
        </div>

    </div>
    """, unsafe_allow_html=True)


# ============================================================
# PARTICIPANT SUMMARY
# ============================================================

summary = (
    df.groupby(
        ["Participant_ID", "Participant"],
        dropna=False
    )
    .agg(
        Attempts=("Score", "count"),
        Average_Score=("Score", "mean"),
        Highest_Score=("Score", "max"),
        Lowest_Score=("Score", "min"),
        Perfect_15=("Perfect", "sum"),
        Average_Duration=("Duration_Seconds", "mean"),
        Fastest_Duration=("Duration_Seconds", "min")
    )
    .reset_index()
)


# ============================================================
# SCORE AT FASTEST ATTEMPT
# ============================================================

fastest_score_list = []


for participant_id, group in df.groupby("Participant_ID"):

    timed = group.dropna(
        subset=["Duration_Seconds"]
    )

    if not timed.empty:

        fastest_row = timed.loc[
            timed["Duration_Seconds"].idxmin()
        ]

        fastest_score_list.append({
            "Participant_ID": participant_id,
            "Score_at_Fastest": fastest_row["Score"]
        })


fastest_score_df = pd.DataFrame(
    fastest_score_list
)


if not fastest_score_df.empty:

    summary = summary.merge(
        fastest_score_df,
        on="Participant_ID",
        how="left"
    )

else:

    summary["Score_at_Fastest"] = None


# ============================================================
# PERFORMANCE LEADERS
# ============================================================

st.markdown(
    '<div class="section-title">🏅 Performance Leaders</div>',
    unsafe_allow_html=True
)


# Highest average
highest_average = summary.loc[
    summary["Average_Score"].idxmax()
]


# Highest single score
highest_single = df.loc[
    df["Score"].idxmax()
]


# Most 15/15
most_15 = summary.loc[
    summary["Perfect_15"].idxmax()
]


# Fastest perfect attempt
perfect_timed = df[
    (df["Score"] == 15)
    & (df["Duration_Seconds"].notna())
]


if not perfect_timed.empty:

    fastest_perfect = perfect_timed.loc[
        perfect_timed["Duration_Seconds"].idxmin()
    ]

else:

    fastest_perfect = None


l1, l2, l3, l4 = st.columns(4)


with l1:

    st.markdown(f"""
    <div class="leader">

        <div class="leader-label">
            🥇 Highest Average
        </div>

        <div class="leader-name">
            {highest_average["Participant"]}
        </div>

        <div class="leader-value">
            {highest_average["Average_Score"]:.2f}/15 average
        </div>

    </div>
    """, unsafe_allow_html=True)


with l2:

    st.markdown(f"""
    <div class="leader">

        <div class="leader-label">
            🏆 Highest Single Score
        </div>

        <div class="leader-name">
            {highest_single["Participant"]}
        </div>

        <div class="leader-value">
            {highest_single["Score"]:.0f}/15
        </div>

    </div>
    """, unsafe_allow_html=True)


with l3:

    st.markdown(f"""
    <div class="leader">

        <div class="leader-label">
            🎯 Most 15/15 Attempts
        </div>

        <div class="leader-name">
            {most_15["Participant"]}
        </div>

        <div class="leader-value">
            {int(most_15["Perfect_15"])} perfect attempt(s)
        </div>

    </div>
    """, unsafe_allow_html=True)


with l4:

    if fastest_perfect is not None:

        st.markdown(f"""
        <div class="leader">

            <div class="leader-label">
                ⚡ Fastest 15/15
            </div>

            <div class="leader-name">
                {fastest_perfect["Participant"]}
            </div>

            <div class="leader-value">
                {format_time(fastest_perfect["Duration_Seconds"])}
            </div>

        </div>
        """, unsafe_allow_html=True)

    else:

        st.markdown("""
        <div class="leader">

            <div class="leader-label">
                ⚡ Fastest 15/15
            </div>

            <div class="leader-name">
                No perfect attempt
            </div>

            <div class="leader-value">
                No timed 15/15 available
            </div>

        </div>
        """, unsafe_allow_html=True)


# ============================================================
# TIME ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">⏱️ Time Performance</div>',
    unsafe_allow_html=True
)


timed_df = df.dropna(
    subset=["Duration_Seconds"]
).copy()


if not timed_df.empty:

    fastest_attempt = timed_df.loc[
        timed_df["Duration_Seconds"].idxmin()
    ]

else:

    fastest_attempt = None


# High score = 13/15 or higher
high_score_df = timed_df[
    timed_df["Score"] >= 13
]


if not high_score_df.empty:

    fastest_high_score = high_score_df.loc[
        high_score_df["Duration_Seconds"].idxmin()
    ]

else:

    fastest_high_score = None


time1, time2, time3 = st.columns(3)


with time1:

    if fastest_attempt is not None:

        st.markdown(f"""
        <div class="info-card">

        <b>⚡ Fastest Overall Attempt</b>

        <h2>
        {format_time(fastest_attempt["Duration_Seconds"])}
        </h2>

        <p>
        <b>{fastest_attempt["Participant"]}</b><br>
        Score: {fastest_attempt["Score"]:.0f}/15
        </p>

        </div>
        """, unsafe_allow_html=True)

    else:

        st.info("No duration information available.")


with time2:

    if fastest_high_score is not None:

        st.markdown(f"""
        <div class="info-card">

        <b>🚀 Fastest High-Score Attempt</b>

        <h2>
        {format_time(fastest_high_score["Duration_Seconds"])}
        </h2>

        <p>
        <b>{fastest_high_score["Participant"]}</b><br>
        Score: {fastest_high_score["Score"]:.0f}/15
        </p>

        </div>
        """, unsafe_allow_html=True)

    else:

        st.info("No attempt scoring 13/15 or above.")


with time3:

    person_15 = df[
        (df["Participant_ID"] == most_15["Participant_ID"])
        & (df["Score"] == 15)
        & (df["Duration_Seconds"].notna())
    ]

    if not person_15.empty:

        shortest_15 = person_15.loc[
            person_15["Duration_Seconds"].idxmin()
        ]

        st.markdown(f"""
        <div class="info-card">

        <b>🎯 Shortest 15/15 of Top Performer</b>

        <h2>
        {format_time(shortest_15["Duration_Seconds"])}
        </h2>

        <p>
        <b>{most_15["Participant"]}</b><br>
        {int(most_15["Perfect_15"])} perfect attempt(s)
        </p>

        </div>
        """, unsafe_allow_html=True)

    else:

        st.info(
            "The top 15/15 performer has no timed perfect attempt."
        )


# ============================================================
# CHARTS
# ============================================================

st.markdown(
    '<div class="section-title">📈 Performance Overview</div>',
    unsafe_allow_html=True
)


chart1, chart2 = st.columns(2)


# ------------------------------------------------------------
# SCORE DISTRIBUTION
# ------------------------------------------------------------

with chart1:

    score_distribution = (
        df["Score"]
        .value_counts()
        .sort_index()
        .reset_index()
    )

    score_distribution.columns = [
        "Score",
        "Attempts"
    ]

    fig_score = px.bar(
        score_distribution,
        x="Score",
        y="Attempts",
        text="Attempts",
        title="Score Distribution"
    )

    fig_score.update_traces(
        textposition="outside"
    )

    fig_score.update_layout(
        template="plotly_white",
        height=420,
        xaxis_title="Score",
        yaxis_title="Number of Attempts",
        margin=dict(
            l=20,
            r=20,
            t=60,
            b=20
        )
    )

    st.plotly_chart(
        fig_score,
        use_container_width=True
    )


# ------------------------------------------------------------
# AVERAGE SCORE BY PARTICIPANT
# ------------------------------------------------------------

with chart2:

    chart_summary = summary.sort_values(
        "Average_Score",
        ascending=True
    )

    fig_participant = px.bar(
        chart_summary,
        x="Average_Score",
        y="Participant",
        orientation="h",
        text="Average_Score",
        title="Average Score by Participant"
    )

    fig_participant.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    fig_participant.update_layout(
        template="plotly_white",
        height=420,
        xaxis_title="Average Score",
        yaxis_title="",
        xaxis=dict(range=[0, 15]),
        margin=dict(
            l=20,
            r=60,
            t=60,
            b=20
        )
    )

    st.plotly_chart(
        fig_participant,
        use_container_width=True
    )


# ============================================================
# PARTICIPANT ANALYSIS TABLE
# ============================================================

st.markdown(
    '<div class="section-title">👤 Individual Performance</div>',
    unsafe_allow_html=True
)


table = summary.copy()


table["Average Score"] = (
    table["Average_Score"].round(2)
)


table["Highest Score"] = (
    table["Highest_Score"].round(0).astype(int)
)


table["Lowest Score"] = (
    table["Lowest_Score"].round(0).astype(int)
)


table["Average Time"] = (
    table["Average_Duration"]
    .apply(format_time)
)


table["Fastest Time"] = (
    table["Fastest_Duration"]
    .apply(format_time)
)


table["Score at Fastest Time"] = (
    table["Score_at_Fastest"]
    .apply(
        lambda x:
        f"{x:.0f}/15"
        if pd.notna(x)
        else "N/A"
    )
)


table = table[
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
]


table = table.rename(
    columns={
        "Perfect_15": "15/15 Attempts"
    }
)


table = table.sort_values(
    "Average Score",
    ascending=False
)


st.dataframe(
    table,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# 15/15 ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">🎯 15/15 Analysis</div>',
    unsafe_allow_html=True
)


if perfect_count == 0:

    st.markdown("""
    <div class="warning-card">

    <b>No 15/15 attempts found.</b>

    <p>
    There are currently no attempts with a score of exactly 15/15.
    </p>

    </div>
    """, unsafe_allow_html=True)

else:

    perfect_counts = (
        df[df["Perfect"]]
        .groupby("Participant")
        .size()
        .reset_index(name="Perfect Attempts")
        .sort_values(
            "Perfect Attempts",
            ascending=False
        )
    )


    pc1, pc2 = st.columns(2)


    with pc1:

        fig_perfect = px.bar(
            perfect_counts,
            x="Participant",
            y="Perfect Attempts",
            text="Perfect Attempts",
            title="15/15 Attempts by Participant"
        )

        fig_perfect.update_traces(
            textposition="outside"
        )

        fig_perfect.update_layout(
            template="plotly_white",
            height=400,
            xaxis_title="Participant",
            yaxis_title="Number of 15/15 Attempts",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=80
            )
        )

        st.plotly_chart(
            fig_perfect,
            use_container_width=True
        )


    with pc2:

        perfect_table = df[
            df["Perfect"]
        ][
            [
                "Participant",
                "Score"
            ]
        ].copy()


        if "Duration" in df.columns:

            perfect_table["Duration"] = (
                df.loc[
                    df["Perfect"],
                    "Duration"
                ].values
            )


        st.markdown(
            '<div class="info-card"><b>Perfect Attempt Details</b></div>',
            unsafe_allow_html=True
        )

        st.dataframe(
            perfect_table,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# QUESTION ANALYSIS
# ============================================================

question_columns = [
    f"Q{i}"
    for i in range(1, 16)
    if f"Q{i}" in df.columns
]


if len(question_columns) > 0:

    st.markdown(
        '<div class="section-title">❓ Question Analysis</div>',
        unsafe_allow_html=True
    )


    question_results = []


    for question in question_columns:

        values = pd.to_numeric(
            df[question],
            errors="coerce"
        )

        values = values.dropna()


        if len(values) > 0:

            correct_percentage = (
                (values == 1).mean() * 100
            )

            question_results.append({
                "Question": question,
                "Correct %": correct_percentage
            })


    question_df = pd.DataFrame(
        question_results
    )


    if not question_df.empty:

        easiest = question_df.loc[
            question_df["Correct %"].idxmax()
        ]

        difficult = question_df.loc[
            question_df["Correct %"].idxmin()
        ]


        q1, q2 = st.columns(2)


        with q1:

            st.markdown(f"""
            <div class="success-card">

            <b>🟢 Easiest Question</b>

            <h2>
            {easiest["Question"]}
            </h2>

            <p>
            Correct response:
            <b>{easiest["Correct %"]:.1f}%</b>
            </p>

            </div>
            """, unsafe_allow_html=True)


        with q2:

            st.markdown(f"""
            <div class="warning-card">

            <b>🔴 Most Difficult Question</b>

            <h2>
            {difficult["Question"]}
            </h2>

            <p>
            Correct response:
            <b>{difficult["Correct %"]:.1f}%</b>
            </p>

            </div>
            """, unsafe_allow_html=True)


        fig_questions = px.bar(
            question_df,
            x="Question",
            y="Correct %",
            text="Correct %",
            title="Question-wise Correct Percentage"
        )


        fig_questions.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )


        fig_questions.update_layout(
            template="plotly_white",
            height=430,
            yaxis=dict(
                range=[0, 110]
            ),
            xaxis_title="Question",
            yaxis_title="Correct Percentage (%)",
            margin=dict(
                l=20,
                r=20,
                t=60,
                b=20
            )
        )


        st.plotly_chart(
            fig_questions,
            use_container_width=True
        )


else:

    st.info(
        "Q1–Q15 columns were not found in this worksheet."
    )


# ============================================================
# ATTENTION SECTION
# ============================================================

st.markdown(
    '<div class="section-title">⚠️ Performance Attention</div>',
    unsafe_allow_html=True
)


# Participants with average below 10
attention = summary[
    summary["Average_Score"] < 10
].copy()


if attention.empty:

    st.markdown("""
    <div class="success-card">

    <b>✅ No Immediate Performance Concern</b>

    <p>
    No participant currently has an average score below 10/15.
    </p>

    </div>
    """, unsafe_allow_html=True)


else:

    attention_table = attention[
        [
            "Participant",
            "Attempts",
            "Average_Score",
            "Highest_Score",
            "Lowest_Score"
        ]
    ].copy()


    attention_table = attention_table.rename(
        columns={
            "Average_Score": "Average Score",
            "Highest_Score": "Highest Score",
            "Lowest_Score": "Lowest Score"
        }
    )


    attention_table["Average Score"] = (
        attention_table["Average Score"].round(2)
    )


    st.dataframe(
        attention_table,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.markdown("""
<div style="
    text-align:center;
    color:#6b7280;
    font-size:13px;
    padding:10px;
">

    📊 Quiz Performance Analytics Dashboard
    <br>
    Dynamic analysis based on uploaded quiz results

</div>
""", unsafe_allow_html=True)
