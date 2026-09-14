import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import re
from io import BytesIO


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Quiz Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    /* ---------------- GENERAL ---------------- */

    .stApp {
        background-color: #F6F8FC;
    }

    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1450px;
    }

    h1, h2, h3, h4 {
        color: #202124 !important;
    }

    p, label, span, div {
        font-family: Arial, sans-serif;
    }

    /* ---------------- SIDEBAR ---------------- */

    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #EEF0F5;
    }

    section[data-testid="stSidebar"] .block-container {
        padding-top: 2rem;
    }

    /* ---------------- SIDEBAR TITLE ---------------- */

    .sidebar-logo {
        font-size: 25px;
        font-weight: 700;
        color: #6842F5;
        margin-bottom: 5px;
    }

    .sidebar-subtitle {
        font-size: 13px;
        color: #9AA0A6;
        margin-bottom: 25px;
    }

    /* ---------------- HEADER ---------------- */

    .dashboard-title {
        font-size: 32px;
        font-weight: 700;
        color: #202124;
        margin-bottom: 2px;
    }

    .dashboard-subtitle {
        font-size: 15px;
        color: #777B82;
        margin-bottom: 25px;
    }

    /* ---------------- CARDS ---------------- */

    .metric-card {
        background: #FFFFFF;
        border: 1px solid #EEF0F5;
        border-radius: 16px;
        padding: 22px;
        min-height: 145px;
        box-shadow: 0 2px 8px rgba(20, 20, 40, 0.03);
    }

    .metric-label {
        font-size: 14px;
        color: #777B82;
        font-weight: 500;
        margin-bottom: 10px;
    }

    .metric-value {
        font-size: 30px;
        font-weight: 700;
        color: #202124;
        margin-bottom: 5px;
    }

    .metric-description {
        font-size: 12px;
        color: #9AA0A6;
    }

    /* ---------------- SECTION ---------------- */

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #202124;
        margin-top: 20px;
        margin-bottom: 12px;
    }

    .section-description {
        font-size: 13px;
        color: #777B82;
        margin-bottom: 15px;
    }

    /* ---------------- HIGHLIGHT CARDS ---------------- */

    .highlight-card {
        background: #FFFFFF;
        border: 1px solid #EEF0F5;
        border-radius: 15px;
        padding: 18px;
        min-height: 125px;
        box-shadow: 0 2px 8px rgba(20, 20, 40, 0.03);
    }

    .highlight-title {
        font-size: 13px;
        color: #777B82;
        margin-bottom: 8px;
    }

    .highlight-value {
        font-size: 21px;
        font-weight: 700;
        color: #202124;
    }

    .highlight-detail {
        font-size: 12px;
        color: #9AA0A6;
        margin-top: 5px;
    }

    /* ---------------- INFO BOX ---------------- */

    .info-box {
        background: #FFFFFF;
        border: 1px solid #EEF0F5;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
    }

    /* ---------------- TABLE ---------------- */

    .table-title {
        font-size: 20px;
        font-weight: 700;
        color: #202124;
        margin-bottom: 10px;
    }

    /* ---------------- FILE UPLOADER ---------------- */

    [data-testid="stFileUploader"] {
        background-color: #FFFFFF;
        border-radius: 15px;
    }

    /* ---------------- BUTTON ---------------- */

    .stButton > button {
        border-radius: 10px;
        border: 1px solid #E5E7EB;
        font-weight: 600;
    }

    /* ---------------- SELECTBOX ---------------- */

    div[data-baseweb="select"] > div {
        border-radius: 10px;
    }

    /* ---------------- TABS ---------------- */

    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def parse_score(value):
    """
    Converts values such as:
    15
    14.00
    15/15
    14.5/15.00
    into a numeric score.
    """

    if pd.isna(value):
        return np.nan

    text = str(value).strip()

    # Try to find the first numeric value
    match = re.search(r"-?\d+(?:\.\d+)?", text)

    if match:
        try:
            return float(match.group())
        except ValueError:
            return np.nan

    return np.nan


def parse_duration(value):
    """
    Converts duration into seconds.

    Supports:
    MM:SS
    HH:MM:SS
    numeric seconds
    """

    if pd.isna(value):
        return np.nan

    # Already numeric
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip()

    if not text:
        return np.nan

    # HH:MM:SS or MM:SS
    if ":" in text:
        parts = text.split(":")

        try:
            parts = [float(x) for x in parts]

            if len(parts) == 2:
                minutes, seconds = parts
                return minutes * 60 + seconds

            if len(parts) == 3:
                hours, minutes, seconds = parts
                return hours * 3600 + minutes * 60 + seconds

        except ValueError:
            return np.nan

    # Try numeric value
    match = re.search(r"\d+(?:\.\d+)?", text)

    if match:
        try:
            return float(match.group())
        except ValueError:
            return np.nan

    return np.nan


def format_duration(seconds):
    """
    Converts seconds into readable duration.
    """

    if pd.isna(seconds):
        return "N/A"

    seconds = int(round(seconds))

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"

    if minutes > 0:
        return f"{minutes}m {secs}s"

    return f"{secs}s"


def format_score(score):
    if pd.isna(score):
        return "N/A"

    if float(score).is_integer():
        return f"{int(score)}/15"

    return f"{score:.2f}/15"


def clean_name(value):
    if pd.isna(value):
        return ""

    return str(value).strip()


def create_participant_name(row):
    """
    Creates participant name using First name + Last name.
    """

    first = clean_name(row.get("First name", ""))
    last = clean_name(row.get("Last name", ""))

    name = f"{first} {last}".strip()

    if name:
        return name

    email = clean_name(row.get("Email", ""))

    if email:
        return email

    return "Unknown Participant"


def style_plot(fig, height=370):
    """
    Applies consistent readable styling to every Plotly chart.
    This specifically fixes white/invisible axis labels.
    """

    fig.update_layout(
        paper_bgcolor="white",
        plot_bgcolor="white",

        font=dict(
            family="Arial",
            color="#202124",
            size=12
        ),

        title_font=dict(
            family="Arial",
            color="#202124",
            size=17
        ),

        legend=dict(
            font=dict(
                family="Arial",
                color="#202124",
                size=11
            )
        ),

        margin=dict(
            l=55,
            r=25,
            t=55,
            b=65
        ),

        height=height
    )

    fig.update_xaxes(
        title_font=dict(
            family="Arial",
            color="#202124",
            size=13
        ),

        tickfont=dict(
            family="Arial",
            color="#202124",
            size=11
        ),

        showline=True,
        linecolor="#D1D5DB",
        linewidth=1,

        gridcolor="#E5E7EB",
        zeroline=False
    )

    fig.update_yaxes(
        title_font=dict(
            family="Arial",
            color="#202124",
            size=13
        ),

        tickfont=dict(
            family="Arial",
            color="#202124",
            size=11
        ),

        showline=True,
        linecolor="#D1D5DB",
        linewidth=1,

        gridcolor="#E5E7EB",
        zeroline=False
    )

    return fig


def metric_card(label, value, description=""):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-description">{description}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def highlight_card(title, value, detail=""):
    st.markdown(
        f"""
        <div class="highlight-card">
            <div class="highlight-title">{title}</div>
            <div class="highlight-value">{value}</div>
            <div class="highlight-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DATA PROCESSING
# ============================================================

def process_data(df):

    df = df.copy()

    # Remove completely empty columns
    df = df.dropna(axis=1, how="all")

    # Remove completely empty rows
    df = df.dropna(axis=0, how="all")

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    score_column = None

    possible_score_columns = [
        "Grade/15.00",
        "Grade /15.00",
        "Grade",
        "Score",
        "Marks",
        "Total Score"
    ]

    for col in possible_score_columns:
        if col in df.columns:
            score_column = col
            break

    if score_column is None:
        st.error(
            "Could not find the score column. "
            "Expected a column such as 'Grade/15.00' or 'Score'."
        )
        st.stop()

    df["Score"] = df[score_column].apply(parse_score)

    # --------------------------------------------------------
    # Duration
    # --------------------------------------------------------

    duration_column = None

    possible_duration_columns = [
        "Duration",
        "Time",
        "Completion Time",
        "Time Taken"
    ]

    for col in possible_duration_columns:
        if col in df.columns:
            duration_column = col
            break

    if duration_column is not None:
        df["Duration Seconds"] = df[duration_column].apply(parse_duration)
    else:
        df["Duration Seconds"] = np.nan

    # --------------------------------------------------------
    # Participant name
    # --------------------------------------------------------

    df["Participant"] = df.apply(create_participant_name, axis=1)

    # --------------------------------------------------------
    # Email
    # --------------------------------------------------------

    if "Email" in df.columns:
        df["Participant ID"] = (
            df["Email"]
            .fillna("")
            .astype(str)
            .str.strip()
            .replace("", np.nan)
        )
    else:
        df["Participant ID"] = np.nan

    df["Participant ID"] = df["Participant ID"].fillna(
        df["Participant"]
    )

    # --------------------------------------------------------
    # Dates
    # --------------------------------------------------------

    if "Started" in df.columns:
        df["Started Date"] = pd.to_datetime(
            df["Started"],
            errors="coerce"
        )
    else:
        df["Started Date"] = pd.NaT

    if "Completed" in df.columns:
        df["Completed Date"] = pd.to_datetime(
            df["Completed"],
            errors="coerce"
        )
    else:
        df["Completed Date"] = pd.NaT

    # --------------------------------------------------------
    # Attempt number
    # --------------------------------------------------------

    df["Attempt Number"] = (
        df.groupby("Participant ID")
        .cumcount() + 1
    )

    # --------------------------------------------------------
    # Perfect score
    # --------------------------------------------------------

    df["Perfect Score"] = np.isclose(
        df["Score"],
        15,
        equal_nan=False
    )

    return df


def create_participant_summary(df):

    records = []

    for participant_id, group in df.groupby("Participant ID"):

        group = group.copy()

        participant = group["Participant"].iloc[0]

        valid_scores = group["Score"].dropna()
        valid_durations = group["Duration Seconds"].dropna()

        attempts = len(group)

        average_score = (
            valid_scores.mean()
            if len(valid_scores) > 0
            else np.nan
        )

        highest_score = (
            valid_scores.max()
            if len(valid_scores) > 0
            else np.nan
        )

        lowest_score = (
            valid_scores.min()
            if len(valid_scores) > 0
            else np.nan
        )

        average_duration = (
            valid_durations.mean()
            if len(valid_durations) > 0
            else np.nan
        )

        fastest_duration = (
            valid_durations.min()
            if len(valid_durations) > 0
            else np.nan
        )

        # Score on fastest attempt
        fastest_score = np.nan

        if len(valid_durations) > 0:

            fastest_row = group.loc[
                group["Duration Seconds"].idxmin()
            ]

            fastest_score = fastest_row["Score"]

        # Fastest high-score attempt >= 13
        high_score_group = group[
            group["Score"] >= 13
        ]

        if not high_score_group.empty:

            high_score_row = high_score_group.loc[
                high_score_group["Duration Seconds"].idxmin()
            ] if high_score_group["Duration Seconds"].notna().any() else None

            if high_score_row is not None:
                fastest_high_score_duration = (
                    high_score_row["Duration Seconds"]
                )
                fastest_high_score = high_score_row["Score"]
            else:
                fastest_high_score_duration = np.nan
                fastest_high_score = np.nan

        else:
            fastest_high_score_duration = np.nan
            fastest_high_score = np.nan

        perfect_attempts = int(
            group["Perfect Score"].sum()
        )

        records.append(
            {
                "Participant ID": participant_id,
                "Participant": participant,
                "Attempts": attempts,
                "Average Score": average_score,
                "Highest Score": highest_score,
                "Lowest Score": lowest_score,
                "Average Duration": average_duration,
                "Fastest Duration": fastest_duration,
                "Score at Fastest Attempt": fastest_score,
                "Fastest High Score Duration": fastest_high_score_duration,
                "Fastest High Score": fastest_high_score,
                "Perfect Attempts": perfect_attempts
            }
        )

    summary = pd.DataFrame(records)

    return summary


# ============================================================
# SESSION STATE
# ============================================================

if "data" not in st.session_state:
    st.session_state.data = None

if "participant_summary" not in st.session_state:
    st.session_state.participant_summary = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-logo">
            Quiz Analytics
        </div>

        <div class="sidebar-subtitle">
            Participant Performance Dashboard
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    page = st.radio(
        "Navigation",
        [
            "Overview",
            "Participants",
            "Performance",
            "Perfect Scores",
            "Upload Data"
        ],
        label_visibility="visible"
    )

    st.markdown("---")

    if st.session_state.data is not None:

        data_sidebar = st.session_state.data

        st.markdown(
            "**Current Dataset**"
        )

        st.caption(
            f"{len(data_sidebar)} attempts"
        )

        st.caption(
            f"{data_sidebar['Participant'].nunique()} participants"
        )

    else:

        st.caption(
            "No dataset uploaded yet."
        )


# ============================================================
# UPLOAD DATA PAGE / UPLOADER
# ============================================================

def upload_section():

    st.markdown(
        '<div class="dashboard-title">Upload Assessment Data</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="dashboard-subtitle">
            Upload a CSV or Excel worksheet to analyse quiz attempts automatically.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="info-box">
            <b>Supported data</b><br><br>
            Upload a worksheet containing participant information,
            quiz scores, and optionally completion duration.
            The dashboard will automatically calculate participant
            performance and 15/15 results.
        </div>
        """,
        unsafe_allow_html=True
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xlsx", "xls"]
    )

    if uploaded_file is not None:

        try:

            file_name = uploaded_file.name.lower()

            if file_name.endswith(".csv"):

                df = pd.read_csv(uploaded_file)

            else:

                excel_file = pd.ExcelFile(uploaded_file)

                sheet_names = excel_file.sheet_names

                if len(sheet_names) > 1:

                    selected_sheet = st.selectbox(
                        "Select worksheet",
                        sheet_names
                    )

                else:

                    selected_sheet = sheet_names[0]

                df = pd.read_excel(
                    uploaded_file,
                    sheet_name=selected_sheet
                )

            processed_df = process_data(df)

            summary_df = create_participant_summary(
                processed_df
            )

            st.session_state.data = processed_df
            st.session_state.participant_summary = summary_df

            st.success(
                f"Successfully loaded {len(processed_df)} attempts."
            )

            st.rerun()

        except Exception as e:

            st.error(
                f"Could not process the file: {e}"
            )


# ============================================================
# CHECK DATA
# ============================================================

if page == "Upload Data":

    upload_section()

    st.stop()


if st.session_state.data is None:

    st.markdown(
        '<div class="dashboard-title">Quiz Analytics Dashboard</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="dashboard-subtitle">
            Analyse participant performance, attempts, completion times,
            and perfect scores.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "Please upload your assessment CSV or Excel file from the sidebar."
    )

    upload_section()

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

df = st.session_state.data.copy()
participant_summary = (
    st.session_state.participant_summary.copy()
)


# ============================================================
# GLOBAL HEADER
# ============================================================

st.markdown(
    '<div class="dashboard-title">Quiz Performance Dashboard</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="dashboard-subtitle">
        A clear overview of participant attempts, scores, completion times,
        and perfect-score performance.
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# OVERVIEW PAGE
# ============================================================

if page == "Overview":

    total_attempts = len(df)

    total_participants = df["Participant"].nunique()

    valid_scores = df["Score"].dropna()

    average_score = (
        valid_scores.mean()
        if not valid_scores.empty
        else np.nan
    )

    highest_score = (
        valid_scores.max()
        if not valid_scores.empty
        else np.nan
    )

    perfect_attempts = int(
        df["Perfect Score"].sum()
    )

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        metric_card(
            "Total Participants",
            total_participants,
            "Unique participants"
        )

    with c2:
        metric_card(
            "Total Attempts",
            total_attempts,
            "All recorded quiz attempts"
        )

    with c3:
        metric_card(
            "Average Score",
            format_score(average_score),
            "Average across all attempts"
        )

    with c4:
        metric_card(
            "Perfect Attempts",
            perfect_attempts,
            "Attempts with exactly 15/15"
        )

    st.markdown(
        '<div class="section-title">Performance Highlights</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # HIGHLIGHTS
    # --------------------------------------------------------

    fastest_overall_duration = np.nan
    fastest_overall_score = np.nan
    fastest_overall_person = "N/A"

    if df["Duration Seconds"].notna().any():

        fastest_row = df.loc[
            df["Duration Seconds"].idxmin()
        ]

        fastest_overall_duration = (
            fastest_row["Duration Seconds"]
        )

        fastest_overall_score = fastest_row["Score"]

        fastest_overall_person = (
            fastest_row["Participant"]
        )

    fastest_high_score_person = "N/A"
    fastest_high_score_duration = np.nan
    fastest_high_score_value = np.nan

    high_score_df = df[
        df["Score"] >= 13
    ].copy()

    high_score_df = high_score_df[
        high_score_df["Duration Seconds"].notna()
    ]

    if not high_score_df.empty:

        row = high_score_df.loc[
            high_score_df["Duration Seconds"].idxmin()
        ]

        fastest_high_score_person = row["Participant"]
        fastest_high_score_duration = row["Duration Seconds"]
        fastest_high_score_value = row["Score"]

    best_average_person = "N/A"
    best_average_score = np.nan

    if not participant_summary.empty:

        best_average_row = participant_summary.loc[
            participant_summary["Average Score"].idxmax()
        ]

        best_average_person = (
            best_average_row["Participant"]
        )

        best_average_score = (
            best_average_row["Average Score"]
        )

    most_perfect_person = "N/A"
    most_perfect_count = 0

    if not participant_summary.empty:

        perfect_row = participant_summary.loc[
            participant_summary["Perfect Attempts"].idxmax()
        ]

        if perfect_row["Perfect Attempts"] > 0:

            most_perfect_person = (
                perfect_row["Participant"]
            )

            most_perfect_count = int(
                perfect_row["Perfect Attempts"]
            )

    h1, h2, h3, h4 = st.columns(4)

    with h1:

        highlight_card(
            "Highest Average Score",
            format_score(best_average_score),
            best_average_person
        )

    with h2:

        highlight_card(
            "Fastest Completed Attempt",
            format_duration(fastest_overall_duration),
            f"{fastest_overall_person} • {format_score(fastest_overall_score)}"
        )

    with h3:

        highlight_card(
            "Fastest High-Score Attempt",
            format_duration(fastest_high_score_duration),
            f"{fastest_high_score_person} • {format_score(fastest_high_score_value)}"
        )

    with h4:

        highlight_card(
            "Most Perfect Scores",
            str(most_perfect_count),
            most_perfect_person
        )

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Score Overview</div>',
        unsafe_allow_html=True
    )

    chart_left, chart_right = st.columns(2)

    # IMPORTANT:
    # chart_left and chart_right are at exactly the same indentation.
    # This prevents the previous IndentationError.

    with chart_left:

        score_distribution = (
            df["Score"]
            .dropna()
            .round(2)
            .value_counts()
            .sort_index()
            .reset_index()
        )

        score_distribution.columns = [
            "Score",
            "Attempts"
        ]

        fig = px.bar(
            score_distribution,
            x="Score",
            y="Attempts",
            title="Score Distribution",
            labels={
                "Score": "Quiz Score (out of 15)",
                "Attempts": "Number of Attempts"
            }
        )

        fig.update_traces(
            hovertemplate=(
                "Score: %{x}<br>"
                "Attempts: %{y}<extra></extra>"
            )
        )

        style_plot(fig)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    with chart_right:

        average_chart = (
            participant_summary[
                [
                    "Participant",
                    "Average Score"
                ]
            ]
            .dropna()
            .sort_values(
                "Average Score",
                ascending=False
            )
            .head(10)
        )

        fig = px.bar(
            average_chart.sort_values("Average Score"),
            x="Average Score",
            y="Participant",
            orientation="h",
            title="Top Participants by Average Score",
            labels={
                "Average Score": "Average Score (out of 15)",
                "Participant": "Participant"
            }
        )

        fig.update_traces(
            hovertemplate=(
                "Participant: %{y}<br>"
                "Average Score: %{x:.2f}<extra></extra>"
            )
        )

        style_plot(fig)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # SCORE VS TIME
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Score and Completion Time</div>',
        unsafe_allow_html=True
    )

    scatter_df = df[
        [
            "Participant",
            "Score",
            "Duration Seconds"
        ]
    ].dropna()

    if not scatter_df.empty:

        fig = px.scatter(
            scatter_df,
            x="Duration Seconds",
            y="Score",
            hover_name="Participant",
            title="Quiz Score vs Completion Time",
            labels={
                "Duration Seconds": "Completion Time (seconds)",
                "Score": "Quiz Score (out of 15)"
            }
        )

        fig.update_traces(
            hovertemplate=(
                "Participant: %{hovertext}<br>"
                "Time: %{x:.0f} seconds<br>"
                "Score: %{y:.2f}/15<extra></extra>"
            )
        )

        style_plot(fig, height=400)

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# PARTICIPANTS PAGE
# ============================================================

elif page == "Participants":

    st.markdown(
        '<div class="section-title">Participant Analysis</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="section-description">
            Compare participants using attempts, average score,
            highest score, lowest score, and completion time.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    search = st.text_input(
        "Search participant",
        placeholder="Type a participant name or email..."
    )

    display_df = participant_summary.copy()

    if search:

        display_df = display_df[
            display_df["Participant"]
            .str.contains(
                search,
                case=False,
                na=False
            )
        ]

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    sort_option = st.selectbox(
        "Sort participants by",
        [
            "Average Score",
            "Highest Score",
            "Lowest Score",
            "Attempts",
            "Fastest Duration",
            "Perfect Attempts"
        ]
    )

    ascending = sort_option == "Lowest Score"

    display_df = display_df.sort_values(
        sort_option,
        ascending=ascending,
        na_position="last"
    )

    # --------------------------------------------------------
    # TABLE
    # --------------------------------------------------------

    table_df = display_df.copy()

    table_df["Average Score"] = (
        table_df["Average Score"]
        .round(2)
    )

    table_df["Highest Score"] = (
        table_df["Highest Score"]
        .round(2)
    )

    table_df["Lowest Score"] = (
        table_df["Lowest Score"]
        .round(2)
    )

    table_df["Average Duration"] = (
        table_df["Average Duration"]
        .apply(format_duration)
    )

    table_df["Fastest Duration"] = (
        table_df["Fastest Duration"]
        .apply(format_duration)
    )

    table_df["Score at Fastest Attempt"] = (
        table_df["Score at Fastest Attempt"]
        .apply(format_score)
    )

    table_df["Fastest High Score Duration"] = (
        table_df["Fastest High Score Duration"]
        .apply(format_duration)
    )

    table_df["Fastest High Score"] = (
        table_df["Fastest High Score"]
        .apply(format_score)
    )

    table_df = table_df[
        [
            "Participant",
            "Attempts",
            "Average Score",
            "Highest Score",
            "Lowest Score",
            "Average Duration",
            "Fastest Duration",
            "Score at Fastest Attempt",
            "Perfect Attempts"
        ]
    ]

    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Participant": st.column_config.TextColumn(
                "Participant"
            ),
            "Attempts": st.column_config.NumberColumn(
                "Attempts"
            ),
            "Average Score": st.column_config.NumberColumn(
                "Average Score",
                format="%.2f / 15"
            ),
            "Highest Score": st.column_config.NumberColumn(
                "Highest Score",
                format="%.2f / 15"
            ),
            "Lowest Score": st.column_config.NumberColumn(
                "Lowest Score",
                format="%.2f / 15"
            ),
            "Perfect Attempts": st.column_config.NumberColumn(
                "Perfect Attempts"
            )
        }
    )

    # --------------------------------------------------------
    # PARTICIPANT DETAIL
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Individual Participant Details</div>',
        unsafe_allow_html=True
    )

    participants = sorted(
        participant_summary["Participant"].unique()
    )

    selected_participant = st.selectbox(
        "Select participant",
        participants
    )

    selected_df = df[
        df["Participant"] == selected_participant
    ].copy()

    selected_summary = participant_summary[
        participant_summary["Participant"]
        == selected_participant
    ].iloc[0]

    # --------------------------------------------------------
    # DETAIL KPIs
    # --------------------------------------------------------

    d1, d2, d3, d4, d5 = st.columns(5)

    with d1:

        metric_card(
            "Attempts",
            int(selected_summary["Attempts"]),
            "Total attempts"
        )

    with d2:

        metric_card(
            "Average Score",
            format_score(
                selected_summary["Average Score"]
            ),
            "Average performance"
        )

    with d3:

        metric_card(
            "Highest Score",
            format_score(
                selected_summary["Highest Score"]
            ),
            "Best single attempt"
        )

    with d4:

        metric_card(
            "Lowest Score",
            format_score(
                selected_summary["Lowest Score"]
            ),
            "Lowest single attempt"
        )

    with d5:

        metric_card(
            "Perfect Attempts",
            int(
                selected_summary["Perfect Attempts"]
            ),
            "15/15 attempts"
        )

    # --------------------------------------------------------
    # INDIVIDUAL ATTEMPTS
    # --------------------------------------------------------

    detail_columns = [
        "Attempt Number",
        "Score",
        "Duration Seconds",
        "Perfect Score"
    ]

    detail_available = [
        col
        for col in detail_columns
        if col in selected_df.columns
    ]

    detail_table = selected_df[
        detail_available
    ].copy()

    if "Duration Seconds" in detail_table.columns:

        detail_table["Duration"] = (
            detail_table["Duration Seconds"]
            .apply(format_duration)
        )

        detail_table = detail_table.drop(
            columns=["Duration Seconds"]
        )

    detail_table["Score"] = (
        detail_table["Score"]
        .apply(format_score)
    )

    detail_table = detail_table.rename(
        columns={
            "Attempt Number": "Attempt",
            "Perfect Score": "Perfect (15/15)"
        }
    )

    st.dataframe(
        detail_table,
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
        """
        <div class="section-description">
            Identify the strongest scores, fastest attempts,
            and high-performing participants.
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # PERFORMANCE KPIs
    # --------------------------------------------------------

    valid_scores = df["Score"].dropna()

    median_score = (
        valid_scores.median()
        if not valid_scores.empty
        else np.nan
    )

    score_std = (
        valid_scores.std()
        if len(valid_scores) > 1
        else np.nan
    )

    high_score_attempts = int(
        (df["Score"] >= 13).sum()
    )

    excellent_percentage = (
        high_score_attempts / len(valid_scores) * 100
        if len(valid_scores) > 0
        else 0
    )

    p1, p2, p3, p4 = st.columns(4)

    with p1:

        metric_card(
            "Highest Score",
            format_score(
                valid_scores.max()
                if not valid_scores.empty
                else np.nan
            ),
            "Best recorded attempt"
        )

    with p2:

        metric_card(
            "Median Score",
            format_score(median_score),
            "Middle score"
        )

    with p3:

        metric_card(
            "High-Score Attempts",
            high_score_attempts,
            "Scores of 13/15 or higher"
        )

    with p4:

        metric_card(
            "High-Score Rate",
            f"{excellent_percentage:.1f}%",
            "Attempts scoring 13 or higher"
        )

    # --------------------------------------------------------
    # PARTICIPANT PERFORMANCE CHART
    # --------------------------------------------------------

    chart_data = (
        participant_summary[
            [
                "Participant",
                "Average Score",
                "Highest Score"
            ]
        ]
        .dropna(subset=["Average Score"])
        .sort_values(
            "Average Score",
            ascending=False
        )
    )

    fig = px.bar(
        chart_data,
        x="Participant",
        y="Average Score",
        title="Average Score by Participant",
        labels={
            "Participant": "Participant",
            "Average Score": "Average Score (out of 15)"
        }
    )

    fig.update_traces(
        hovertemplate=(
            "Participant: %{x}<br>"
            "Average Score: %{y:.2f}/15<extra></extra>"
        )
    )

    style_plot(fig, height=430)

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    # --------------------------------------------------------
    # TIME ANALYSIS
    # --------------------------------------------------------

    time_df = participant_summary[
        [
            "Participant",
            "Fastest Duration",
            "Average Duration"
        ]
    ].dropna(
        subset=["Fastest Duration"]
    )

    if not time_df.empty:

        fig = px.bar(
            time_df.sort_values("Fastest Duration"),
            x="Participant",
            y="Fastest Duration",
            title="Fastest Completion Time by Participant",
            labels={
                "Participant": "Participant",
                "Fastest Duration": "Fastest Completion Time (seconds)"
            }
        )

        fig.update_traces(
            hovertemplate=(
                "Participant: %{x}<br>"
                "Fastest Time: %{y:.0f} seconds<extra></extra>"
            )
        )

        style_plot(fig, height=430)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    # --------------------------------------------------------
    # BEST ATTEMPTS TABLE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">Best Attempts</div>',
        unsafe_allow_html=True
    )

    best_attempts = df[
        [
            "Participant",
            "Score",
            "Duration Seconds",
            "Perfect Score"
        ]
    ].copy()

    best_attempts = best_attempts.sort_values(
        ["Score", "Duration Seconds"],
        ascending=[False, True]
    )

    best_attempts["Score"] = (
        best_attempts["Score"]
        .apply(format_score)
    )

    best_attempts["Duration"] = (
        best_attempts["Duration Seconds"]
        .apply(format_duration)
    )

    best_attempts = best_attempts[
        [
            "Participant",
            "Score",
            "Duration",
            "Perfect Score"
        ]
    ]

    best_attempts = best_attempts.rename(
        columns={
            "Perfect Score": "Perfect (15/15)"
        }
    )

    st.dataframe(
        best_attempts.head(20),
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PERFECT SCORES PAGE
# ============================================================

elif page == "Perfect Scores":

    st.markdown(
        '<div class="section-title">Perfect Score Analysis</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="section-description">
            Analyse every attempt that achieved exactly 15/15.
        </div>
        """,
        unsafe_allow_html=True
    )

    perfect_df = df[
        df["Perfect Score"]
    ].copy()

    total_perfect = len(perfect_df)

    participants_with_perfect = (
        perfect_df["Participant"].nunique()
        if not perfect_df.empty
        else 0
    )

    # --------------------------------------------------------
    # PERFECT SCORE KPIs
    # --------------------------------------------------------

    q1, q2, q3, q4 = st.columns(4)

    with q1:

        metric_card(
            "15/15 Attempts",
            total_perfect,
            "Total perfect-score attempts"
        )

    with q2:

        metric_card(
            "Participants with 15/15",
            participants_with_perfect,
            "Unique participants"
        )

    fastest_perfect_duration = np.nan
    fastest_perfect_person = "N/A"

    if not perfect_df.empty:

        duration_available = perfect_df[
            perfect_df["Duration Seconds"].notna()
        ]

        if not duration_available.empty:

            row = duration_available.loc[
                duration_available["Duration Seconds"].idxmin()
            ]

            fastest_perfect_duration = (
                row["Duration Seconds"]
            )

            fastest_perfect_person = (
                row["Participant"]
            )

    with q3:

        metric_card(
            "Fastest 15/15",
            format_duration(
                fastest_perfect_duration
            ),
            fastest_perfect_person
        )

    most_perfect_count = 0
    most_perfect_person = "N/A"

    if not perfect_df.empty:

        counts = (
            perfect_df["Participant"]
            .value_counts()
        )

        if not counts.empty:

            most_perfect_person = counts.index[0]
            most_perfect_count = int(
                counts.iloc[0]
            )

    with q4:

        metric_card(
            "Most 15/15 Scores",
            most_perfect_count,
            most_perfect_person
        )

    # --------------------------------------------------------
    # IF NO PERFECT SCORES
    # --------------------------------------------------------

    if perfect_df.empty:

        st.warning(
            "No participant has achieved exactly 15/15 in the uploaded data."
        )

    else:

        # ----------------------------------------------------
        # PERFECT SCORE RANKING
        # ----------------------------------------------------

        perfect_counts = (
            perfect_df["Participant"]
            .value_counts()
            .reset_index()
        )

        perfect_counts.columns = [
            "Participant",
            "Perfect Attempts"
        ]

        fig = px.bar(
            perfect_counts,
            x="Participant",
            y="Perfect Attempts",
            title="Number of 15/15 Attempts by Participant",
            labels={
                "Participant": "Participant",
                "Perfect Attempts": "Number of 15/15 Attempts"
            }
        )

        fig.update_traces(
            hovertemplate=(
                "Participant: %{x}<br>"
                "15/15 Attempts: %{y}<extra></extra>"
            )
        )

        style_plot(fig, height=430)

        st.plotly_chart(
            fig,
            use_container_width=True
        )

        # ----------------------------------------------------
        # PERFECT ATTEMPTS TABLE
        # ----------------------------------------------------

        st.markdown(
            '<div class="section-title">All Perfect Attempts</div>',
            unsafe_allow_html=True
        )

        perfect_table = perfect_df[
            [
                "Participant",
                "Attempt Number",
                "Score",
                "Duration Seconds",
                "Started",
                "Completed"
            ]
        ].copy()

        perfect_table["Score"] = (
            perfect_table["Score"]
            .apply(format_score)
        )

        perfect_table["Duration"] = (
            perfect_table["Duration Seconds"]
            .apply(format_duration)
        )

        columns_to_show = [
            "Participant",
            "Attempt Number",
            "Score",
            "Duration"
        ]

        if "Started" in perfect_table.columns:
            columns_to_show.append("Started")

        if "Completed" in perfect_table.columns:
            columns_to_show.append("Completed")

        perfect_table = perfect_table[
            columns_to_show
        ]

        perfect_table = perfect_table.rename(
            columns={
                "Attempt Number": "Attempt"
            }
        )

        st.dataframe(
            perfect_table,
            use_container_width=True,
            hide_index=True
        )

        # ----------------------------------------------------
        # FASTEST PERFECT ATTEMPT
        # ----------------------------------------------------

        if not perfect_df[
            "Duration Seconds"
        ].dropna().empty:

            fastest_perfect = perfect_df.loc[
                perfect_df["Duration Seconds"].idxmin()
            ]

            st.markdown(
                '<div class="section-title">Fastest Perfect Attempt</div>',
                unsafe_allow_html=True
            )

            f1, f2, f3 = st.columns(3)

            with f1:

                highlight_card(
                    "Participant",
                    fastest_perfect["Participant"],
                    "Fastest person to complete a 15/15"
                )

            with f2:

                highlight_card(
                    "Completion Time",
                    format_duration(
                        fastest_perfect[
                            "Duration Seconds"
                        ]
                    ),
                    "Shortest time among all 15/15 attempts"
                )

            with f3:

                highlight_card(
                    "Score",
                    format_score(
                        fastest_perfect["Score"]
                    ),
                    "Perfect score"
                )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <br><br>
    <div style="
        text-align:center;
        color:#9AA0A6;
        font-size:12px;
        padding:20px;
    ">
        Quiz Analytics Dashboard • Automatically calculated from uploaded data
    </div>
    """,
    unsafe_allow_html=True
)
