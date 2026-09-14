import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Quiz Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# COLORS
# ============================================================

PURPLE = "#6842F5"
GREEN = "#22C55E"
RED = "#EF4444"
TEXT = "#202124"
MUTED = "#8A8F9C"
BG = "#F6F8FC"
CARD = "#FFFFFF"
BORDER = "#EEF0F5"

# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* Main background */
    .stApp {
        background-color: #F6F8FC;
    }

    /* Remove top padding */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1500px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #EEF0F5;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* Sidebar text */
    section[data-testid="stSidebar"] p {
        color: #202124;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid #EEF0F5;
        background-color: white;
        color: #202124;
    }

    .stButton > button:hover {
        border-color: #6842F5;
        color: #6842F5;
    }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #EEF0F5;
        border-radius: 14px;
        padding: 18px;
        box-shadow: 0 2px 8px rgba(30, 30, 50, 0.03);
    }

    div[data-testid="stMetricLabel"] {
        color: #8A8F9C;
        font-size: 13px;
    }

    div[data-testid="stMetricValue"] {
        color: #202124;
        font-size: 26px;
        font-weight: 700;
    }

    /* Dataframe */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
    }

    /* Selectbox */
    div[data-baseweb="select"] > div {
        border-radius: 10px;
        border-color: #EEF0F5;
    }

    /* File uploader */
    section[data-testid="stFileUploaderDropzone"] {
        border-radius: 12px;
        border: 1px dashed #CFC9FF;
        background-color: #FAF9FF;
    }

    /* Horizontal line */
    hr {
        border-color: #EEF0F5;
    }

    /* Section headings */
    .section-title {
        font-size: 20px;
        font-weight: 700;
        color: #202124;
        margin-bottom: 2px;
    }

    .section-subtitle {
        font-size: 13px;
        color: #8A8F9C;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def duration_to_seconds(value):
    """
    Convert quiz duration into seconds.

    Handles:
    MM:SS
    HH:MM:SS
    pandas Timedelta
    datetime.time
    """

    if pd.isna(value):
        return None

    if isinstance(value, pd.Timedelta):
        return value.total_seconds()

    if isinstance(value, time):
        return (
            value.hour * 3600
            + value.minute * 60
            + value.second
        )

    if isinstance(value, datetime):
        return (
            value.hour * 3600
            + value.minute * 60
            + value.second
        )

    value = str(value).strip()

    if not value:
        return None

    try:
        parts = value.split(":")

        if len(parts) == 2:
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds

        if len(parts) == 3:
            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])

            return hours * 3600 + minutes * 60 + seconds

    except Exception:
        return None

    return None


def seconds_to_display(seconds):

    if pd.isna(seconds):
        return "-"

    seconds = int(round(seconds))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"

    return f"{minutes}m {secs}s"


def convert_question(value):

    if pd.isna(value):
        return None

    # Numeric values
    try:
        number = float(value)

        if number == 1:
            return 1

        if number == 0:
            return 0

    except Exception:
        pass

    # Text values
    text = str(value).strip().lower()

    correct_values = {
        "correct",
        "yes",
        "true",
        "right",
        "1"
    }

    incorrect_values = {
        "incorrect",
        "wrong",
        "no",
        "false",
        "0"
    }

    if text in correct_values:
        return 1

    if text in incorrect_values:
        return 0

    return None


def get_participant_name(row):

    first = str(row.get("First name", "")).strip()
    last = str(row.get("Last name", "")).strip()

    name = f"{first} {last}".strip()

    if name:
        return name

    email = str(row.get("Email", "")).strip()

    if email:
        return email

    return "Unknown Participant"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### ◉ Quiz Analytics"
    )

    st.caption("Performance Dashboard")

    st.divider()

    st.markdown("**NAVIGATION**")

    page = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Participants",
            "Performance",
            "Questions",
            "15/15 Analysis"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("**DATA**")

    st.info(
        "Upload your quiz worksheet to update the dashboard."
    )

    uploaded_file = st.file_uploader(
        "Upload Worksheet",
        type=["csv", "xlsx"],
        label_visibility="collapsed"
    )

    st.divider()

    st.caption("Quiz Analytics Dashboard")
    st.caption("Built with Streamlit")

# ============================================================
# HEADER
# ============================================================

st.title("Hello, Quiz Dashboard 👋")

st.caption(
    "Participant performance, attempts, scores, time and question analysis"
)

# ============================================================
# UPLOAD MESSAGE
# ============================================================

if uploaded_file is None:

    st.divider()

    st.info(
        "👈 Upload your CSV or Excel worksheet from the sidebar to begin."
    )

    st.markdown("### What this dashboard analyzes")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("👤 Participants", "—")

    with col2:
        st.metric("📝 Attempts", "—")

    with col3:
        st.metric("📊 Average Score", "—")

    with col4:
        st.metric("🏆 Perfect Attempts", "—")

    st.divider()

    st.markdown(
        """
        **Your worksheet should contain:**

        `Last name`, `First name`, `Email`, `Status`,
        `Started`, `Completed`, `Duration`, `Grade/15.00`,
        and `Q1` through `Q15`.
        """
    )

    st.stop()

# ============================================================
# READ FILE
# ============================================================

try:

    if uploaded_file.name.lower().endswith(".csv"):

        df = pd.read_csv(uploaded_file)

    else:

        df = pd.read_excel(uploaded_file)

except Exception as e:

    st.error(f"Could not read the file: {e}")
    st.stop()

# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .astype(str)
    .str.strip()
)

# ============================================================
# CHECK SCORE COLUMN
# ============================================================

score_column = "Grade/15.00"

if score_column not in df.columns:

    possible_score_columns = [
        col for col in df.columns
        if "grade" in col.lower()
        or "score" in col.lower()
    ]

    if possible_score_columns:

        score_column = possible_score_columns[0]

    else:

        st.error(
            "I could not find the quiz score column."
        )

        st.write("Columns found in your worksheet:")

        st.write(list(df.columns))

        st.stop()

# ============================================================
# SCORE CLEANING
# ============================================================

df["Score"] = (
    df[score_column]
    .astype(str)
    .str.extract(r"(\d+(?:\.\d+)?)")[0]
)

df["Score"] = pd.to_numeric(
    df["Score"],
    errors="coerce"
)

df = df.dropna(subset=["Score"]).copy()

# ============================================================
# PARTICIPANT NAME
# ============================================================

df["Participant"] = df.apply(
    get_participant_name,
    axis=1
)

# ============================================================
# PARTICIPANT ID
# ============================================================

if "Email" in df.columns:

    email_clean = (
        df["Email"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

else:

    email_clean = pd.Series(
        [""] * len(df),
        index=df.index
    )

df["Participant_ID"] = email_clean

# If email is missing, use name
df.loc[
    df["Participant_ID"] == "",
    "Participant_ID"
] = (
    df.loc[
        df["Participant_ID"] == "",
        "Participant"
    ]
    .str.lower()
    .str.strip()
)

# ============================================================
# DURATION
# ============================================================

if "Duration" in df.columns:

    df["Duration_seconds"] = (
        df["Duration"]
        .apply(duration_to_seconds)
    )

else:

    df["Duration_seconds"] = None

# ============================================================
# QUESTION COLUMNS
# ============================================================

question_columns = [
    f"Q{i}"
    for i in range(1, 16)
    if f"Q{i}" in df.columns
]

for question in question_columns:

    df[question + "_correct"] = (
        df[question]
        .apply(convert_question)
    )

# ============================================================
# BASIC CALCULATIONS
# ============================================================

total_attempts = len(df)

unique_participants = (
    df["Participant_ID"]
    .nunique()
)

average_score = df["Score"].mean()

highest_score = df["Score"].max()

lowest_score = df["Score"].min()

perfect_attempts = int(
    (df["Score"] == 15).sum()
)

# ============================================================
# PARTICIPANT SUMMARY
# ============================================================

participant_summary = (
    df.groupby("Participant_ID")
    .agg(
        Participant=("Participant", "first"),
        Attempts=("Score", "count"),
        Average_Score=("Score", "mean"),
        Highest_Score=("Score", "max"),
        Lowest_Score=("Score", "min"),
        Perfect_Attempts=("Score", lambda x: (x == 15).sum())
    )
    .reset_index()
)

# Average duration
average_duration = (
    df.groupby("Participant_ID")["Duration_seconds"]
    .mean()
    .reset_index(name="Average_Duration")
)

fastest_duration = (
    df.groupby("Participant_ID")["Duration_seconds"]
    .min()
    .reset_index(name="Fastest_Duration")
)

participant_summary = participant_summary.merge(
    average_duration,
    on="Participant_ID",
    how="left"
)

participant_summary = participant_summary.merge(
    fastest_duration,
    on="Participant_ID",
    how="left"
)

# ============================================================
# SCORE AT FASTEST ATTEMPT
# ============================================================

fastest_rows = (
    df.sort_values("Duration_seconds")
    .dropna(subset=["Duration_seconds"])
    .drop_duplicates("Participant_ID")
)

fastest_scores = fastest_rows[
    ["Participant_ID", "Score"]
].rename(
    columns={
        "Score": "Score_at_Fastest"
    }
)

participant_summary = participant_summary.merge(
    fastest_scores,
    on="Participant_ID",
    how="left"
)

# ============================================================
# ROUND VALUES
# ============================================================

participant_summary["Average_Score"] = (
    participant_summary["Average_Score"].round(2)
)

# ============================================================
# PERFORMANCE LEADERS
# ============================================================

highest_average_row = participant_summary.loc[
    participant_summary["Average_Score"].idxmax()
]

highest_single_row = df.loc[
    df["Score"].idxmax()
]

most_perfect_row = participant_summary.loc[
    participant_summary["Perfect_Attempts"].idxmax()
]

# Fastest overall attempt
valid_time_df = df.dropna(
    subset=["Duration_seconds"]
)

if len(valid_time_df) > 0:

    fastest_overall = valid_time_df.loc[
        valid_time_df["Duration_seconds"].idxmin()
    ]

else:

    fastest_overall = None

# Fastest perfect attempt
perfect_df = df[
    df["Score"] == 15
].dropna(
    subset=["Duration_seconds"]
)

if len(perfect_df) > 0:

    fastest_perfect = perfect_df.loc[
        perfect_df["Duration_seconds"].idxmin()
    ]

else:

    fastest_perfect = None

# Fastest high score >= 13
high_score_df = df[
    df["Score"] >= 13
].dropna(
    subset=["Duration_seconds"]
)

if len(high_score_df) > 0:

    fastest_high_score = high_score_df.loc[
        high_score_df["Duration_seconds"].idxmin()
    ]

else:

    fastest_high_score = None

# ============================================================
# DASHBOARD PAGE
# ============================================================

if page == "Dashboard":

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Overview</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">Quick summary of the uploaded quiz data</div>',
        unsafe_allow_html=True
    )

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.metric(
            "👤 Participants",
            unique_participants
        )

    with k2:
        st.metric(
            "📝 Total Attempts",
            total_attempts
        )

    with k3:
        st.metric(
            "📊 Average Score",
            f"{average_score:.2f}/15"
        )

    with k4:
        st.metric(
            "🏆 Highest Score",
            f"{highest_score:g}/15"
        )

    with k5:
        st.metric(
            "🎯 Perfect Attempts",
            perfect_attempts
        )

    st.divider()

    # --------------------------------------------------------
    # PARTICIPANT TABLE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Participant Performance</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">Overall performance across all attempts</div>',
        unsafe_allow_html=True
    )

    display_table = participant_summary[
        [
            "Participant",
            "Attempts",
            "Average_Score",
            "Highest_Score",
            "Lowest_Score",
            "Perfect_Attempts",
            "Average_Duration",
            "Fastest_Duration",
            "Score_at_Fastest"
        ]
    ].copy()

    display_table.columns = [
        "Participant",
        "Attempts",
        "Avg Score",
        "Highest",
        "Lowest",
        "15/15",
        "Avg Time",
        "Fastest Time",
        "Score at Fastest"
    ]

    display_table["Avg Score"] = (
        display_table["Avg Score"]
        .map(lambda x: f"{x:.2f}/15")
    )

    display_table["Highest"] = (
        display_table["Highest"]
        .map(lambda x: f"{x:g}/15")
    )

    display_table["Lowest"] = (
        display_table["Lowest"]
        .map(lambda x: f"{x:g}/15")
    )

    display_table["Avg Time"] = (
        display_table["Avg Time"]
        .apply(seconds_to_display)
    )

    display_table["Fastest Time"] = (
        display_table["Fastest Time"]
        .apply(seconds_to_display)
    )

    display_table["Score at Fastest"] = (
        display_table["Score at Fastest"]
        .apply(
            lambda x: "-"
            if pd.isna(x)
            else f"{x:g}/15"
        )
    )

    display_table = display_table.sort_values(
        "Avg Score",
        ascending=False
    )

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    chart1, chart2 = st.columns(2)

    with chart1:

        st.markdown(
            '<div class="section-title">Score Distribution</div>',
            unsafe_allow_html=True
        )

        fig = px.histogram(
            df,
            x="Score",
            nbins=16,
            labels={
                "Score": "Score"
            }
        )

        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="white",
            plot_bgcolor="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with chart2:

        st.markdown(
            '<div class="section-title">Average Score by Participant</div>',
            unsafe_allow_html=True
        )

        chart_data = participant_summary.sort_values(
            "Average_Score",
            ascending=True
        )

        fig = px.bar(
            chart_data,
            x="Average_Score",
            y="Participant",
            orientation="h",
            labels={
                "Average_Score": "Average Score",
                "Participant": ""
            }
        )

        fig.update_layout(
            height=350,
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="white",
            plot_bgcolor="white"
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # --------------------------------------------------------
    # PERFORMANCE LEADERS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Performance Leaders</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">Highlights from the quiz attempts</div>',
        unsafe_allow_html=True
    )

    l1, l2, l3, l4 = st.columns(4)

    with l1:

        st.metric(
            "🏆 Highest Average",
            highest_average_row["Participant"],
            f"{highest_average_row['Average_Score']:.2f}/15"
        )

    with l2:

        st.metric(
            "⭐ Highest Single Score",
            highest_single_row["Participant"],
            f"{highest_single_row['Score']:g}/15"
        )

    with l3:

        st.metric(
            "🎯 Most 15/15",
            most_perfect_row["Participant"],
            f"{int(most_perfect_row['Perfect_Attempts'])} perfect attempts"
        )

    with l4:

        if fastest_perfect is not None:

            st.metric(
                "⚡ Fastest 15/15",
                fastest_perfect["Participant"],
                seconds_to_display(
                    fastest_perfect["Duration_seconds"]
                )
            )

        else:

            st.metric(
                "⚡ Fastest 15/15",
                "None",
                "No perfect attempt"
            )

# ============================================================
# PARTICIPANTS PAGE
# ============================================================

elif page == "Participants":

    st.markdown(
        '<div class="section-title">Participants</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">Detailed individual performance analysis</div>',
        unsafe_allow_html=True
    )

    participant_names = sorted(
        participant_summary["Participant"].unique()
    )

    selected = st.selectbox(
        "Select Participant",
        participant_names
    )

    selected_row = participant_summary[
        participant_summary["Participant"] == selected
    ].iloc[0]

    st.divider()

    p1, p2, p3, p4 = st.columns(4)

    with p1:
        st.metric(
            "Attempts",
            int(selected_row["Attempts"])
        )

    with p2:
        st.metric(
            "Average Score",
            f"{selected_row['Average_Score']:.2f}/15"
        )

    with p3:
        st.metric(
            "Highest Score",
            f"{selected_row['Highest_Score']:g}/15"
        )

    with p4:
        st.metric(
            "15/15 Attempts",
            int(selected_row["Perfect_Attempts"])
        )

    st.divider()

    p5, p6, p7 = st.columns(3)

    with p5:
        st.metric(
            "Lowest Score",
            f"{selected_row['Lowest_Score']:g}/15"
        )

    with p6:
        st.metric(
            "Fastest Attempt",
            seconds_to_display(
                selected_row["Fastest_Duration"]
            )
        )

    with p7:
        score_fastest = selected_row["Score_at_Fastest"]

        if pd.isna(score_fastest):
            score_fastest_text = "-"
        else:
            score_fastest_text = f"{score_fastest:g}/15"

        st.metric(
            "Score at Fastest",
            score_fastest_text
        )

    st.divider()

    # Attempt history
    participant_id = participant_summary[
        participant_summary["Participant"] == selected
    ]["Participant_ID"].iloc[0]

    person_df = df[
        df["Participant_ID"] == participant_id
    ].copy()

    person_df = person_df.reset_index(drop=True)

    person_df["Attempt"] = range(
        1,
        len(person_df) + 1
    )

    fig = px.line(
        person_df,
        x="Attempt",
        y="Score",
        markers=True,
        labels={
            "Score": "Score / 15"
        }
    )

    fig.update_yaxes(
        range=[0, 15]
    )

    fig.update_layout(
        height=380,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=20, b=20)
    )

    st.markdown("### Score Across Attempts")

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown("### Attempt Details")

    attempt_columns = [
        col for col in [
            "Started",
            "Completed",
            "Duration",
            "Score"
        ]
        if col in person_df.columns
    ]

    attempt_table = person_df[
        attempt_columns
    ].copy()

    if "Score" in attempt_table.columns:

        attempt_table["Score"] = (
            attempt_table["Score"]
            .apply(lambda x: f"{x:g}/15")
        )

    st.dataframe(
        attempt_table,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# PERFORMANCE PAGE
# ============================================================

elif page == "Performance":

    st.markdown(
        '<div class="section-title">Performance Analysis</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">Score and time-based performance indicators</div>',
        unsafe_allow_html=True
    )

    if fastest_overall is not None:

        fastest_name = fastest_overall["Participant"]
        fastest_time = seconds_to_display(
            fastest_overall["Duration_seconds"]
        )
        fastest_score = fastest_overall["Score"]

    else:

        fastest_name = "None"
        fastest_time = "-"
        fastest_score = 0

    if fastest_high_score is not None:

        high_name = fastest_high_score["Participant"]
        high_time = seconds_to_display(
            fastest_high_score["Duration_seconds"]
        )
        high_score = fastest_high_score["Score"]

    else:

        high_name = "None"
        high_time = "-"
        high_score = 0

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "⚡ Fastest Overall",
            fastest_name,
            fastest_time
        )

    with c2:

        st.metric(
            "🚀 Fastest High Score",
            high_name,
            f"{high_score:g}/15 • {high_time}"
        )

    with c3:

        st.metric(
            "🏆 Highest Score",
            highest_single_row["Participant"],
            f"{highest_single_row['Score']:g}/15"
        )

    st.divider()

    # Score vs time
    if len(valid_time_df) > 0:

        st.markdown("### Score vs Completion Time")

        fig = px.scatter(
            valid_time_df,
            x="Duration_seconds",
            y="Score",
            hover_name="Participant",
            labels={
                "Duration_seconds": "Time (seconds)",
                "Score": "Score / 15"
            }
        )

        fig.update_layout(
            height=450,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=20, b=20)
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.markdown("### Participant Time Summary")

    time_table = participant_summary[
        [
            "Participant",
            "Attempts",
            "Average_Duration",
            "Fastest_Duration",
            "Score_at_Fastest"
        ]
    ].copy()

    time_table.columns = [
        "Participant",
        "Attempts",
        "Average Time",
        "Fastest Time",
        "Score at Fastest"
    ]

    time_table["Average Time"] = (
        time_table["Average Time"]
        .apply(seconds_to_display)
    )

    time_table["Fastest Time"] = (
        time_table["Fastest Time"]
        .apply(seconds_to_display)
    )

    time_table["Score at Fastest"] = (
        time_table["Score at Fastest"]
        .apply(
            lambda x: "-"
            if pd.isna(x)
            else f"{x:g}/15"
        )
    )

    st.dataframe(
        time_table,
        use_container_width=True,
        hide_index=True
    )

# ============================================================
# QUESTIONS PAGE
# ============================================================

elif page == "Questions":

    st.markdown(
        '<div class="section-title">Question Analysis</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">Correct response percentage for Q1–Q15</div>',
        unsafe_allow_html=True
    )

    if len(question_columns) == 0:

        st.warning(
            "No Q1–Q15 columns were found in the worksheet."
        )

        st.stop()

    question_results = []

    for question in question_columns:

        correct_column = question + "_correct"

        correct_values = df[
            correct_column
        ].dropna()

        if len(correct_values) > 0:

            percentage = (
                correct_values.mean() * 100
            )

            question_results.append(
                {
                    "Question": question,
                    "Correct %": percentage
                }
            )

    question_df = pd.DataFrame(
        question_results
    )

    if len(question_df) > 0:

        easiest = question_df.loc[
            question_df["Correct %"].idxmax()
        ]

        difficult = question_df.loc[
            question_df["Correct %"].idxmin()
        ]

        q1, q2 = st.columns(2)

        with q1:

            st.metric(
                "🟢 Easiest Question",
                easiest["Question"],
                f"{easiest['Correct %']:.1f}% correct"
            )

        with q2:

            st.metric(
                "🔴 Most Difficult Question",
                difficult["Question"],
                f"{difficult['Correct %']:.1f}% correct"
            )

        st.divider()

        fig = px.bar(
            question_df,
            x="Question",
            y="Correct %",
            text_auto=".1f",
            labels={
                "Correct %": "Correct Response (%)"
            }
        )

        fig.update_yaxes(
            range=[0, 100]
        )

        fig.update_layout(
            height=450,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(l=20, r=20, t=20, b=20)
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        st.markdown("### Question Performance Table")

        question_display = question_df.copy()

        question_display["Correct %"] = (
            question_display["Correct %"]
            .round(2)
            .astype(str)
            + "%"
        )

        st.dataframe(
            question_display,
            use_container_width=True,
            hide_index=True
        )

# ============================================================
# 15/15 ANALYSIS PAGE
# ============================================================

elif page == "15/15 Analysis":

    st.markdown(
        '<div class="section-title">15/15 Analysis</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-subtitle">Detailed analysis of perfect quiz attempts</div>',
        unsafe_allow_html=True
    )

    if perfect_attempts == 0:

        st.warning(
            "No 15/15 attempts were found in this worksheet."
        )

        st.stop()

    perfect_df_display = df[
        df["Score"] == 15
    ].copy()

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    pp1, pp2, pp3 = st.columns(3)

    with pp1:

        st.metric(
            "🎯 Total 15/15 Attempts",
            perfect_attempts
        )

    with pp2:

        st.metric(
            "👤 Most 15/15",
            most_perfect_row["Participant"],
            f"{int(most_perfect_row['Perfect_Attempts'])} times"
        )

    with pp3:

        if fastest_perfect is not None:

            st.metric(
                "⚡ Fastest 15/15",
                fastest_perfect["Participant"],
                seconds_to_display(
                    fastest_perfect["Duration_seconds"]
                )
            )

        else:

            st.metric(
                "⚡ Fastest 15/15",
                "Time unavailable"
            )

    st.divider()

    # --------------------------------------------------------
    # PERFECT ATTEMPTS TABLE
    # --------------------------------------------------------

    st.markdown("### All Perfect Attempts")

    perfect_columns = [
        col for col in [
            "Participant",
            "Email",
            "Started",
            "Completed",
            "Duration",
            "Score"
        ]
        if col in perfect_df_display.columns
    ]

    perfect_table = perfect_df_display[
        perfect_columns
    ].copy()

    if "Score" in perfect_table.columns:

        perfect_table["Score"] = "15/15"

    st.dataframe(
        perfect_table,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------------
    # 15/15 BY PARTICIPANT
    # --------------------------------------------------------

    perfect_summary = participant_summary[
        participant_summary["Perfect_Attempts"] > 0
    ][
        [
            "Participant",
            "Perfect_Attempts",
            "Fastest_Duration"
        ]
    ].copy()

    perfect_summary = perfect_summary.sort_values(
        "Perfect_Attempts",
        ascending=False
    )

    perfect_summary["Fastest_Duration"] = (
        perfect_summary["Fastest_Duration"]
        .apply(seconds_to_display)
    )

    perfect_summary.columns = [
        "Participant",
        "15/15 Attempts",
        "Fastest Attempt"
    ]

    st.markdown("### Perfect Score Leaders")

    st.dataframe(
        perfect_summary,
        use_container_width=True,
        hide_index=True
    )
