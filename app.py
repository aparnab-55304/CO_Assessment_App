import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, time


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
# COLORS
# ============================================================

PURPLE = "#6842F5"
PURPLE_LIGHT = "#F3F0FF"
GREEN = "#22C55E"
GREEN_LIGHT = "#ECFDF3"
RED = "#EF4444"
RED_LIGHT = "#FEF2F2"

BG = "#F6F8FC"
WHITE = "#FFFFFF"
TEXT = "#202124"
MUTED = "#6B7280"
BORDER = "#E7E9EF"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    f"""
    <style>

    /* ==============================
       GENERAL PAGE
       ============================== */

    .stApp {{
        background-color: {BG};
    }}

    .block-container {{
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1500px;
    }}

    /* ==============================
       SIDEBAR
       ============================== */

    section[data-testid="stSidebar"] {{
        background-color: {WHITE};
        border-right: 1px solid {BORDER};
    }}

    section[data-testid="stSidebar"] .block-container {{
        padding-top: 2rem;
    }}

    section[data-testid="stSidebar"] h3 {{
        color: {TEXT} !important;
    }}

    section[data-testid="stSidebar"] p {{
        color: {TEXT} !important;
    }}

    /* Sidebar radio */
    section[data-testid="stSidebar"] div[role="radiogroup"] label {{
        background-color: white;
        border-radius: 10px;
        padding: 9px 12px;
        margin-bottom: 5px;
        color: {TEXT} !important;
    }}

    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
        background-color: {PURPLE_LIGHT};
    }}

    /* ==============================
       HEADINGS
       ============================== */

    h1, h2, h3, h4 {{
        color: {TEXT} !important;
    }}

    p {{
        color: {TEXT};
    }}

    /* ==============================
       METRIC CARDS
       ============================== */

    div[data-testid="stMetric"] {{
        background-color: {WHITE};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 8px rgba(40, 40, 60, 0.04);
        min-height: 120px;
    }}

    div[data-testid="stMetricLabel"] {{
        color: {MUTED} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: {TEXT} !important;
        font-size: 26px !important;
        font-weight: 700 !important;
    }}

    div[data-testid="stMetricDelta"] {{
        font-size: 12px !important;
    }}

    /* ==============================
       DATAFRAME
       ============================== */

    div[data-testid="stDataFrame"] {{
        border: 1px solid {BORDER};
        border-radius: 12px;
        overflow: hidden;
    }}

    /* ==============================
       FILE UPLOADER
       ============================== */

    section[data-testid="stFileUploaderDropzone"] {{
        background-color: #FAF9FF;
        border: 1px dashed #C9C0FF;
        border-radius: 12px;
    }}

    /* ==============================
       SELECT BOX
       ============================== */

    div[data-baseweb="select"] > div {{
        background-color: white;
        border-radius: 10px;
        border-color: {BORDER};
    }}

    /* ==============================
       DIVIDER
       ============================== */

    hr {{
        border-color: {BORDER};
    }}

    /* ==============================
       CUSTOM CARDS
       ============================== */

    .info-card {{
        background-color: white;
        border: 1px solid #E7E9EF;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 10px;
    }}

    .info-title {{
        color: #6B7280;
        font-size: 13px;
        font-weight: 500;
        margin-bottom: 8px;
    }}

    .info-value {{
        color: #202124;
        font-size: 22px;
        font-weight: 700;
    }}

    .info-description {{
        color: #6B7280;
        font-size: 12px;
        margin-top: 5px;
    }}

    .section-heading {{
        color: #202124;
        font-size: 21px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 2px;
    }}

    .section-description {{
        color: #6B7280;
        font-size: 13px;
        margin-bottom: 15px;
    }}

    .welcome-box {{
        background-color: white;
        border: 1px solid #E7E9EF;
        border-radius: 15px;
        padding: 22px 25px;
        margin-bottom: 20px;
    }}

    .welcome-title {{
        color: #202124;
        font-size: 26px;
        font-weight: 700;
    }}

    .welcome-text {{
        color: #6B7280;
        font-size: 14px;
        margin-top: 5px;
    }}

    .highlight-box {{
        background-color: white;
        border: 1px solid #E7E9EF;
        border-radius: 14px;
        padding: 18px;
        min-height: 135px;
    }}

    .highlight-label {{
        color: #6B7280;
        font-size: 12px;
        font-weight: 500;
    }}

    .highlight-name {{
        color: #202124;
        font-size: 18px;
        font-weight: 700;
        margin-top: 8px;
    }}

    .highlight-value {{
        color: #6842F5;
        font-size: 13px;
        margin-top: 5px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def duration_to_seconds(value):

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

    if value == "":
        return None

    try:

        parts = value.split(":")

        if len(parts) == 2:

            minutes = float(parts[0])
            seconds = float(parts[1])

            return minutes * 60 + seconds

        elif len(parts) == 3:

            hours = float(parts[0])
            minutes = float(parts[1])
            seconds = float(parts[2])

            return (
                hours * 3600
                + minutes * 60
                + seconds
            )

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


def get_participant_name(row):

    first = str(
        row.get("First name", "")
    ).strip()

    last = str(
        row.get("Last name", "")
    ).strip()

    name = f"{first} {last}".strip()

    if name:
        return name

    email = str(
        row.get("Email", "")
    ).strip()

    if email:
        return email

    return "Unknown Participant"


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        "### 📊 Quiz Analytics"
    )

    st.caption(
        "Performance Dashboard"
    )

    st.divider()

    st.markdown(
        "**DASHBOARD**"
    )

    page = st.radio(
        "Dashboard sections",
        [
            "Overview",
            "Participants",
            "Performance",
            "Perfect Scores"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown(
        "**UPLOAD DATA**"
    )

    uploaded_file = st.file_uploader(
        "Choose your quiz worksheet",
        type=["csv", "xlsx"],
        help="Upload a CSV or Excel worksheet containing quiz attempts."
    )

    st.divider()

    st.caption(
        "The dashboard updates automatically when a new worksheet is uploaded."
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    """
    <div class="welcome-box">
        <div class="welcome-title">
            Quiz Performance Dashboard
        </div>
        <div class="welcome-text">
            A clear overview of participant scores, attempts,
            completion time and performance highlights.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ============================================================
# NO FILE UPLOADED
# ============================================================

if uploaded_file is None:

    st.info(
        "Please upload your quiz worksheet using the Upload Data section in the left sidebar."
    )

    st.markdown(
        "### What you can see here"
    )

    a, b, c = st.columns(3)

    with a:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">
                    PARTICIPANT ANALYSIS
                </div>
                <div class="info-value">
                    Individual Results
                </div>
                <div class="info-description">
                    Compare attempts, average scores,
                    highest scores and completion time.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with b:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">
                    PERFORMANCE ANALYSIS
                </div>
                <div class="info-value">
                    Score & Time
                </div>
                <div class="info-description">
                    Identify high-performing and
                    time-efficient attempts.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with c:

        st.markdown(
            """
            <div class="info-card">
                <div class="info-title">
                    PERFECT SCORES
                </div>
                <div class="info-value">
                    15 / 15 Results
                </div>
                <div class="info-description">
                    Find participants with perfect scores
                    and the fastest perfect attempt.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.stop()


# ============================================================
# READ UPLOADED FILE
# ============================================================

try:

    if uploaded_file.name.lower().endswith(".csv"):

        df = pd.read_csv(uploaded_file)

    else:

        df = pd.read_excel(uploaded_file)

except Exception as e:

    st.error(
        f"Unable to read the uploaded worksheet: {e}"
    )

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
# FIND SCORE COLUMN
# ============================================================

score_column = "Grade/15.00"

if score_column not in df.columns:

    possible_columns = [
        col
        for col in df.columns
        if "grade" in col.lower()
        or "score" in col.lower()
    ]

    if possible_columns:

        score_column = possible_columns[0]

    else:

        st.error(
            "The worksheet does not contain a recognizable score column."
        )

        st.write(
            "Columns found:"
        )

        st.write(
            list(df.columns)
        )

        st.stop()


# ============================================================
# CLEAN SCORE
# ============================================================

df["Score"] = (
    df[score_column]
    .astype(str)
    .str.extract(
        r"(\d+(?:\.\d+)?)"
    )[0]
)

df["Score"] = pd.to_numeric(
    df["Score"],
    errors="coerce"
)

df = df.dropna(
    subset=["Score"]
).copy()


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

    df["Participant_ID"] = (
        df["Email"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

else:

    df["Participant_ID"] = ""


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
# BASIC STATISTICS
# ============================================================

total_attempts = len(df)

total_participants = (
    df["Participant_ID"]
    .nunique()
)

average_score = df["Score"].mean()

highest_score = df["Score"].max()

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
        Perfect_Attempts=(
            "Score",
            lambda x: (x == 15).sum()
        )
    )
    .reset_index()
)


# ============================================================
# TIME SUMMARY
# ============================================================

average_time = (
    df.groupby("Participant_ID")
    ["Duration_seconds"]
    .mean()
    .reset_index(
        name="Average_Time"
    )
)

fastest_time = (
    df.groupby("Participant_ID")
    ["Duration_seconds"]
    .min()
    .reset_index(
        name="Fastest_Time"
    )
)

participant_summary = participant_summary.merge(
    average_time,
    on="Participant_ID",
    how="left"
)

participant_summary = participant_summary.merge(
    fastest_time,
    on="Participant_ID",
    how="left"
)


# ============================================================
# SCORE AT FASTEST ATTEMPT
# ============================================================

valid_duration = df.dropna(
    subset=["Duration_seconds"]
)

if len(valid_duration) > 0:

    fastest_attempts = (
        valid_duration
        .sort_values("Duration_seconds")
        .drop_duplicates(
            "Participant_ID"
        )
    )

    fastest_scores = fastest_attempts[
        [
            "Participant_ID",
            "Score"
        ]
    ].rename(
        columns={
            "Score": "Score_at_Fastest"
        }
    )

    participant_summary = (
        participant_summary.merge(
            fastest_scores,
            on="Participant_ID",
            how="left"
        )
    )

else:

    participant_summary[
        "Score_at_Fastest"
    ] = None


participant_summary[
    "Average_Score"
] = participant_summary[
    "Average_Score"
].round(2)


# ============================================================
# LEADERS
# ============================================================

highest_average = participant_summary.loc[
    participant_summary[
        "Average_Score"
    ].idxmax()
]

highest_single = df.loc[
    df["Score"].idxmax()
]

most_perfect = participant_summary.loc[
    participant_summary[
        "Perfect_Attempts"
    ].idxmax()
]


# ============================================================
# FASTEST OVERALL
# ============================================================

if len(valid_duration) > 0:

    fastest_overall = valid_duration.loc[
        valid_duration[
            "Duration_seconds"
        ].idxmin()
    ]

else:

    fastest_overall = None


# ============================================================
# FASTEST PERFECT SCORE
# ============================================================

perfect_df = df[
    df["Score"] == 15
].dropna(
    subset=["Duration_seconds"]
)

if len(perfect_df) > 0:

    fastest_perfect = perfect_df.loc[
        perfect_df[
            "Duration_seconds"
        ].idxmin()
    ]

else:

    fastest_perfect = None


# ============================================================
# FASTEST HIGH-SCORE ATTEMPT
# Score >= 13
# ============================================================

high_score_df = df[
    df["Score"] >= 13
].dropna(
    subset=["Duration_seconds"]
)

if len(high_score_df) > 0:

    fastest_high_score = high_score_df.loc[
        high_score_df[
            "Duration_seconds"
        ].idxmin()
    ]

else:

    fastest_high_score = None


# ============================================================
# OVERVIEW PAGE
# ============================================================

if page == "Overview":

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">Quiz Overview</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'A quick summary of the uploaded quiz data.'
        '</div>',
        unsafe_allow_html=True
    )

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:

        st.metric(
            "Total Participants",
            total_participants
        )

    with k2:

        st.metric(
            "Total Attempts",
            total_attempts
        )

    with k3:

        st.metric(
            "Average Score",
            f"{average_score:.2f} / 15"
        )

    with k4:

        st.metric(
            "Highest Score",
            f"{highest_score:g} / 15"
        )

    with k5:

        st.metric(
            "Perfect Scores",
            perfect_attempts
        )

    st.divider()

    # --------------------------------------------------------
    # PARTICIPANT TABLE
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">'
        'Participant Performance'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Each participant is summarized across all of their quiz attempts.'
        '</div>',
        unsafe_allow_html=True
    )

    table = participant_summary.copy()

    table = table[
        [
            "Participant",
            "Attempts",
            "Average_Score",
            "Highest_Score",
            "Lowest_Score",
            "Perfect_Attempts",
            "Average_Time",
            "Fastest_Time",
            "Score_at_Fastest"
        ]
    ]

    table.columns = [
        "Participant",
        "Attempts",
        "Average Score",
        "Highest Score",
        "Lowest Score",
        "Perfect Scores",
        "Average Time",
        "Fastest Time",
        "Score at Fastest"
    ]

    table["Average Score"] = (
        table["Average Score"]
        .map(
            lambda x:
            f"{x:.2f} / 15"
        )
    )

    table["Highest Score"] = (
        table["Highest Score"]
        .map(
            lambda x:
            f"{x:g} / 15"
        )
    )

    table["Lowest Score"] = (
        table["Lowest Score"]
        .map(
            lambda x:
            f"{x:g} / 15"
        )
    )

    table["Average Time"] = (
        table["Average Time"]
        .apply(seconds_to_display)
    )

    table["Fastest Time"] = (
        table["Fastest Time"]
        .apply(seconds_to_display)
    )

    table["Score at Fastest"] = (
        table["Score at Fastest"]
        .apply(
            lambda x:
            "-"
            if pd.isna(x)
            else f"{x:g} / 15"
        )
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------------
    # CHARTS
    # --------------------------------------------------------

    chart_left, chart_right = st.columns(2)

    with chart_left:

        st.markdown(
            '<div class="section-heading">'
            'Score Distribution'
            '</div>',
            unsafe_allow_html=True
        )

        st.caption(
            "Number of attempts at each score level."
        )

        score_counts = (
    df["Score"]
    .value_counts()
    .sort_index()
    .reset_index()
)

score_counts.columns = [
    "Score",
    "Attempts"
]

fig = px.bar(
    score_counts,
    x="Score",
    y="Attempts",
    text="Attempts",
    labels={
        "Score": "Quiz Score (out of 15)",
        "Attempts": "Number of Attempts"
    }
)

fig.update_traces(
    textposition="outside",
    textfont=dict(
        color="#202124",
        size=12
    )
)

fig.update_layout(
    height=360,
    paper_bgcolor="white",
    plot_bgcolor="white",

    font=dict(
        color="#202124",
        family="Arial"
    ),

    xaxis=dict(
        title="Quiz Score (out of 15)",
        title_font=dict(
            color="#202124",
            size=13
        ),
        tickfont=dict(
            color="#202124",
            size=11
        ),
        showline=True,
        linecolor="#D1D5DB",
        gridcolor="#E5E7EB"
    ),

    yaxis=dict(
        title="Number of Attempts",
        title_font=dict(
            color="#202124",
            size=13
        ),
        tickfont=dict(
            color="#202124",
            size=11
        ),
        showline=True,
        linecolor="#D1D5DB",
        gridcolor="#E5E7EB"
    ),

    margin=dict(
        l=50,
        r=25,
        t=25,
        b=55
    )
)

st.plotly_chart(
    fig,
    use_container_width=True

        )

    with chart_right:

        st.markdown(
            '<div class="section-heading">'
            'Average Score by Participant'
            '</div>',
            unsafe_allow_html=True
        )

        st.caption(
            "Average quiz score across all attempts."
        )

        chart_data = participant_summary.sort_values(
            "Average_Score"
        )

        fig = px.bar(
            chart_data,
            x="Average_Score",
            y="Participant",
            orientation="h"
        )

        fig.update_xaxes(
            range=[0, 15]
        )

        fig.update_layout(
            height=360,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # --------------------------------------------------------
    # PERFORMANCE HIGHLIGHTS
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-heading">'
        'Performance Highlights'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'The strongest results identified from the uploaded attempts.'
        '</div>',
        unsafe_allow_html=True
    )

    h1, h2, h3, h4 = st.columns(4)

    with h1:

        st.markdown(
            f"""
            <div class="highlight-box">
                <div class="highlight-label">
                    HIGHEST AVERAGE SCORE
                </div>
                <div class="highlight-name">
                    {highest_average["Participant"]}
                </div>
                <div class="highlight-value">
                    {highest_average["Average_Score"]:.2f} / 15 average
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with h2:

        st.markdown(
            f"""
            <div class="highlight-box">
                <div class="highlight-label">
                    HIGHEST SINGLE SCORE
                </div>
                <div class="highlight-name">
                    {highest_single["Participant"]}
                </div>
                <div class="highlight-value">
                    {highest_single["Score"]:g} / 15
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with h3:

        st.markdown(
            f"""
            <div class="highlight-box">
                <div class="highlight-label">
                    MOST PERFECT SCORES
                </div>
                <div class="highlight-name">
                    {most_perfect["Participant"]}
                </div>
                <div class="highlight-value">
                    {int(most_perfect["Perfect_Attempts"])} perfect attempts
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with h4:

        if fastest_perfect is not None:

            st.markdown(
                f"""
                <div class="highlight-box">
                    <div class="highlight-label">
                        FASTEST PERFECT SCORE
                    </div>
                    <div class="highlight-name">
                        {fastest_perfect["Participant"]}
                    </div>
                    <div class="highlight-value">
                        {seconds_to_display(
                            fastest_perfect["Duration_seconds"]
                        )}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                """
                <div class="highlight-box">
                    <div class="highlight-label">
                        FASTEST PERFECT SCORE
                    </div>
                    <div class="highlight-name">
                        No perfect attempt
                    </div>
                    <div class="highlight-value">
                        Not available
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# PARTICIPANTS PAGE
# ============================================================

elif page == "Participants":

    st.markdown(
        '<div class="section-heading">'
        'Participant Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Select a participant to view their complete quiz performance.'
        '</div>',
        unsafe_allow_html=True
    )

    participants = sorted(
        participant_summary[
            "Participant"
        ].unique()
    )

    selected_participant = st.selectbox(
        "Select Participant",
        participants
    )

    selected_summary = participant_summary[
        participant_summary[
            "Participant"
        ] == selected_participant
    ].iloc[0]

    st.divider()

    # --------------------------------------------------------
    # SELECTED PARTICIPANT KPIs
    # --------------------------------------------------------

    a1, a2, a3, a4 = st.columns(4)

    with a1:

        st.metric(
            "Number of Attempts",
            int(
                selected_summary[
                    "Attempts"
                ]
            )
        )

    with a2:

        st.metric(
            "Average Score",
            f"{selected_summary['Average_Score']:.2f} / 15"
        )

    with a3:

        st.metric(
            "Highest Score",
            f"{selected_summary['Highest_Score']:g} / 15"
        )

    with a4:

        st.metric(
            "Perfect Scores",
            int(
                selected_summary[
                    "Perfect_Attempts"
                ]
            )
        )

    st.divider()

    b1, b2, b3 = st.columns(3)

    with b1:

        st.metric(
            "Lowest Score",
            f"{selected_summary['Lowest_Score']:g} / 15"
        )

    with b2:

        st.metric(
            "Fastest Attempt",
            seconds_to_display(
                selected_summary[
                    "Fastest_Time"
                ]
            )
        )

    with b3:

        score_fast = selected_summary[
            "Score_at_Fastest"
        ]

        if pd.isna(score_fast):
            score_fast_text = "-"
        else:
            score_fast_text = f"{score_fast:g} / 15"

        st.metric(
            "Score at Fastest Attempt",
            score_fast_text
        )

    st.divider()

    # --------------------------------------------------------
    # ATTEMPT HISTORY
    # --------------------------------------------------------

    participant_id = participant_summary[
        participant_summary[
            "Participant"
        ] == selected_participant
    ]["Participant_ID"].iloc[0]

    person_df = df[
        df["Participant_ID"] == participant_id
    ].copy()

    person_df = person_df.reset_index(
        drop=True
    )

    person_df["Attempt Number"] = (
        range(
            1,
            len(person_df) + 1
        )
    )

    st.markdown(
        "### Score Across Attempts"
    )

    st.caption(
        "This chart shows how the participant performed in each attempt."
    )

    fig = px.line(
        person_df,
        x="Attempt Number",
        y="Score",
        markers=True
    )

    fig.update_yaxes(
        range=[0, 15]
    )

    fig.update_layout(
        height=380,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20
        )
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

    st.markdown(
        "### Attempt Details"
    )

    attempt_columns = [
        col
        for col in [
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
            .apply(
                lambda x:
                f"{x:g} / 15"
            )
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
        '<div class="section-heading">'
        'Performance Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'Identify strong scores achieved efficiently within a short completion time.'
        '</div>',
        unsafe_allow_html=True
    )

    if fastest_overall is not None:

        fastest_name = fastest_overall[
            "Participant"
        ]

        fastest_time = seconds_to_display(
            fastest_overall[
                "Duration_seconds"
            ]
        )

        fastest_score = fastest_overall[
            "Score"
        ]

    else:

        fastest_name = "Not available"
        fastest_time = "-"
        fastest_score = 0

    if fastest_high_score is not None:

        high_name = fastest_high_score[
            "Participant"
        ]

        high_time = seconds_to_display(
            fastest_high_score[
                "Duration_seconds"
            ]
        )

        high_score = fastest_high_score[
            "Score"
        ]

    else:

        high_name = "Not available"
        high_time = "-"
        high_score = 0

    p1, p2, p3 = st.columns(3)

    with p1:

        st.markdown(
            f"""
            <div class="highlight-box">
                <div class="highlight-label">
                    FASTEST COMPLETED ATTEMPT
                </div>
                <div class="highlight-name">
                    {fastest_name}
                </div>
                <div class="highlight-value">
                    {fastest_time} • Score: {fastest_score:g} / 15
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p2:

        st.markdown(
            f"""
            <div class="highlight-box">
                <div class="highlight-label">
                    FASTEST ATTEMPT WITH SCORE ≥ 13
                </div>
                <div class="highlight-name">
                    {high_name}
                </div>
                <div class="highlight-value">
                    {high_time} • Score: {high_score:g} / 15
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with p3:

        st.markdown(
            f"""
            <div class="highlight-box">
                <div class="highlight-label">
                    HIGHEST SCORE
                </div>
                <div class="highlight-name">
                    {highest_single["Participant"]}
                </div>
                <div class="highlight-value">
                    {highest_single["Score"]:g} / 15
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    # --------------------------------------------------------
    # SCORE VS TIME
    # --------------------------------------------------------

    if len(valid_duration) > 0:

        st.markdown(
            "### Score Compared with Completion Time"
        )

        st.caption(
            "Each point represents one quiz attempt."
        )

        fig = px.scatter(
            valid_duration,
            x="Duration_seconds",
            y="Score",
            hover_name="Participant",
            labels={
                "Duration_seconds":
                    "Completion Time (seconds)",
                "Score":
                    "Score / 15"
            }
        )

        fig.update_yaxes(
            range=[0, 15]
        )

        fig.update_layout(
            height=450,
            paper_bgcolor="white",
            plot_bgcolor="white",
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20
            )
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )

    st.divider()

    # --------------------------------------------------------
    # TIME SUMMARY
    # --------------------------------------------------------

    st.markdown(
        "### Completion Time Summary"
    )

    time_table = participant_summary[
        [
            "Participant",
            "Attempts",
            "Average_Time",
            "Fastest_Time",
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
        time_table[
            "Score at Fastest"
        ]
        .apply(
            lambda x:
            "-"
            if pd.isna(x)
            else f"{x:g} / 15"
        )
    )

    st.dataframe(
        time_table,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# PERFECT SCORES PAGE
# ============================================================

elif page == "Perfect Scores":

    st.markdown(
        '<div class="section-heading">'
        'Perfect Score Analysis'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-description">'
        'A perfect score means the participant achieved exactly 15 out of 15.'
        '</div>',
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # NO PERFECT SCORES
    # --------------------------------------------------------

    if perfect_attempts == 0:

        st.info(
            "No participant has achieved a perfect score of 15/15 yet."
        )

        st.stop()

    # --------------------------------------------------------
    # PERFECT SCORE KPIs
    # --------------------------------------------------------

    x1, x2, x3 = st.columns(3)

    with x1:

        st.metric(
            "Total Perfect Attempts",
            perfect_attempts
        )

    with x2:

        st.metric(
            "Participant with Most Perfect Scores",
            most_perfect["Participant"],
            f"{int(most_perfect['Perfect_Attempts'])} times"
        )

    with x3:

        if fastest_perfect is not None:

            st.metric(
                "Fastest Perfect Attempt",
                fastest_perfect["Participant"],
                seconds_to_display(
                    fastest_perfect[
                        "Duration_seconds"
                    ]
                )
            )

        else:

            st.metric(
                "Fastest Perfect Attempt",
                "Time unavailable"
            )

    st.divider()

    # --------------------------------------------------------
    # ALL PERFECT ATTEMPTS
    # --------------------------------------------------------

    st.markdown(
        "### All 15/15 Attempts"
    )

    st.caption(
        "Every attempt in which the participant scored 15 out of 15."
    )

    perfect_display = df[
        df["Score"] == 15
    ].copy()

    columns_to_show = [
        col
        for col in [
            "Participant",
            "Email",
            "Started",
            "Completed",
            "Duration"
        ]
        if col in perfect_display.columns
    ]

    perfect_table = perfect_display[
        columns_to_show
    ].copy()

    perfect_table.insert(
        len(perfect_table.columns),
        "Score",
        "15 / 15"
    )

    st.dataframe(
        perfect_table,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # --------------------------------------------------------
    # PERFECT SCORE LEADERBOARD
    # --------------------------------------------------------

    st.markdown(
        "### Perfect Score Leaderboard"
    )

    leaderboard = participant_summary[
        participant_summary[
            "Perfect_Attempts"
        ] > 0
    ][
        [
            "Participant",
            "Perfect_Attempts",
            "Fastest_Time"
        ]
    ].copy()

    leaderboard = leaderboard.sort_values(
        [
            "Perfect_Attempts",
            "Fastest_Time"
        ],
        ascending=[
            False,
            True
        ]
    )

    leaderboard["Fastest_Time"] = (
        leaderboard["Fastest_Time"]
        .apply(seconds_to_display)
    )

    leaderboard.columns = [
        "Participant",
        "Number of 15/15 Scores",
        "Fastest Perfect Attempt"
    ]

    st.dataframe(
        leaderboard,
        use_container_width=True,
        hide_index=True
    )
