
import pandas as pd
import numpy as np
import plotly.express as px

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Student Performance Dashboard")
st.write(
    "Upload the assessment CSV file to analyse student scores, improvement, "
    "attempts, time efficiency, and Apple vs Orange team performance."
)

# ============================================================
# FILE UPLOAD
# ============================================================

st.sidebar.header("📂 Upload CSV")

uploaded_file = st.sidebar.file_uploader(
    "Choose your CSV file",
    type=["csv"]
)

if uploaded_file is None:
    st.info("Please upload your CSV file from the sidebar.")
    st.stop()

# ============================================================
# READ CSV
# ============================================================

df_original = pd.read_csv(uploaded_file)

df_original.columns = (
    df_original.columns.astype(str)
    .str.strip()
)

st.success("✅ CSV uploaded successfully.")

# Keep an untouched copy for displaying original data.
df = df_original.copy()

# ============================================================
# SHOW ORIGINAL DATA
# ============================================================

st.subheader("📋 Uploaded Data")

st.dataframe(
    df_original,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# FIND SCORE COLUMN
# ============================================================

possible_score_columns = [
    "Grade/15.00",
    "Grade",
    "Score",
    "Marks",
    "Total",
    "Final Score"
]

numeric_columns = (
    df.select_dtypes(include="number")
    .columns
    .tolist()
)

score_column = next(
    (
        column
        for column in possible_score_columns
        if column in df.columns
    ),
    numeric_columns[0] if numeric_columns else None
)

if score_column is None:
    st.error("❌ No score column was found.")
    st.write("Available columns:", list(df.columns))
    st.stop()

df[score_column] = pd.to_numeric(
    df[score_column],
    errors="coerce"
)

df = df.dropna(
    subset=[score_column]
).copy()

# ============================================================
# STUDENT NAME
# ============================================================

first_name = df.get(
    "First name",
    pd.Series("", index=df.index)
)

last_name = df.get(
    "Last name",
    pd.Series("", index=df.index)
)

email = df.get(
    "Email address",
    pd.Series("", index=df.index)
)

df["Student Name"] = (
    first_name.fillna("").astype(str).str.strip()
    + " "
    + last_name.fillna("").astype(str).str.strip()
).str.strip()

df["Student Name"] = df["Student Name"].where(
    df["Student Name"].ne(""),
    email.fillna("").astype(str).str.strip()
)

# ============================================================
# CLEAN STUDENT NAME FOR TEAM MATCHING
# ============================================================

def normalize_name(name):
    return (
        str(name)
        .lower()
        .replace(" ", "")
        .replace(".", "")
        .replace(",", "")
        .replace("-", "")
        .replace("_", "")
    )

df["Name Key"] = df["Student Name"].apply(normalize_name)

# ============================================================
# APPLE / ORANGE TEAM ASSIGNMENT
# ============================================================

# Your team assignment
apple_members = [
    "Aparna",
    "Jayalakshmi",
    "Ganga",
    "Jintu"
]

orange_members = [
    "Sreelakshmi",
    "Aiswarya",
    "Nandana"
]

apple_keys = [normalize_name(x) for x in apple_members]
orange_keys = [normalize_name(x) for x in orange_members]

def assign_team(name_key):
    # Exact or partial matching makes the mapping robust
    # to names such as "SreelakshmiAnilkumar".
    for member in apple_keys:
        if member in name_key or name_key in member:
            return "Apple"

    for member in orange_keys:
        if member in name_key or name_key in member:
            return "Orange"

    return "Unassigned"

df["Team"] = df["Name Key"].apply(assign_team)

# ============================================================
# BASIC STATISTICS
# ============================================================

max_score = 15.0

student_count = df["Student Name"].nunique()

average_score = df[score_column].mean()

highest_score = df[score_column].max()

lowest_score = df[score_column].min()

median_score = df[score_column].median()

std_score = df[score_column].std()

cv_score = (
    (std_score / average_score) * 100
    if average_score != 0
    else np.nan
)

# ============================================================
# PERCENTAGE
# ============================================================

df["Percentage"] = (
    df[score_column] / max_score
) * 100

df["Percentage"] = df["Percentage"].clip(0, 100)

# ============================================================
# IQR OUTLIER DETECTION
# ============================================================

Q1 = df[score_column].quantile(0.25)
Q3 = df[score_column].quantile(0.75)

IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

df["Outlier"] = (
    (df[score_column] < lower_bound)
    | (df[score_column] > upper_bound)
)

outliers = df[df["Outlier"]].copy()

# Clean data is used for statistical analysis.
clean_df = df[~df["Outlier"]].copy()

# ============================================================
# PERFORMANCE CATEGORY
# ============================================================

clean_df["Performance"] = pd.cut(
    clean_df["Percentage"],
    bins=[-1, 40, 60, 80, 101],
    labels=[
        "Needs Improvement",
        "Average",
        "Good",
        "Excellent"
    ],
    right=False
)

# ============================================================
# CLASS AVERAGE AND RELATIVE PERFORMANCE
# ============================================================

clean_average = clean_df[score_column].mean()

clean_df["Difference from Class Average"] = (
    clean_df[score_column] - clean_average
)

clean_df["Improvement Status"] = pd.cut(
    clean_df["Difference from Class Average"],
    bins=[
        float("-inf"),
        -0.000001,
        0.000001,
        float("inf")
    ],
    labels=[
        "Below Class Average",
        "At Class Average",
        "Above Class Average"
    ]
)

# ============================================================
# DURATION CONVERSION
# ============================================================

def duration_to_minutes(value):
    """
    Convert common Duration formats to minutes.
    Supports:
    - numeric minutes
    - seconds as numeric values
    - HH:MM:SS
    - MM:SS
    - text containing a number
    """
    if pd.isna(value):
        return np.nan

    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)

    text = str(value).strip()

    if text == "" or text.lower() in [
        "nan",
        "none",
        "not available"
    ]:
        return np.nan

    # Time format HH:MM:SS
    parts = text.split(":")

    try:
        if len(parts) == 3:
            h, m, s = map(float, parts)
            return h * 60 + m + s / 60

        if len(parts) == 2:
            m, s = map(float, parts)
            return m + s / 60

        return float(text)
    except ValueError:
        return np.nan


if "Duration" in df.columns:
    df["Time (minutes)"] = df["Duration"].apply(
        duration_to_minutes
    )
else:
    df["Time (minutes)"] = np.nan

clean_df["Time (minutes)"] = df.loc[
    clean_df.index,
    "Time (minutes)"
]

# ============================================================
# ATTEMPT NUMBER
# ============================================================

# One CSV row = one assessment attempt.
df["Attempt Number"] = (
    df.groupby("Student Name")
    .cumcount()
    + 1
)

clean_df["Attempt Number"] = df.loc[
    clean_df.index,
    "Attempt Number"
]

# ============================================================
# TRUE IMPROVEMENT: FIRST ATTEMPT TO LATEST ATTEMPT
# ============================================================

# Use original rows so that an outlier does not change
# the student's actual attempt history.

df_ordered = df.copy()

if "Started" in df_ordered.columns:
    df_ordered["_Started_dt"] = pd.to_datetime(
        df_ordered["Started"],
        errors="coerce"
    )

    if df_ordered["_Started_dt"].notna().any():
        df_ordered = df_ordered.sort_values(
            ["Student Name", "_Started_dt"]
        )

else:
    df_ordered = df_ordered.sort_index()

first_attempt = (
    df_ordered
    .groupby("Student Name", sort=False)[score_column]
    .first()
)

latest_attempt = (
    df_ordered
    .groupby("Student Name", sort=False)[score_column]
    .last()
)

attempt_counts = (
    df_ordered
    .groupby("Student Name")
    .size()
)

student_summary = pd.DataFrame({
    "Student Name": first_attempt.index,
    "First Attempt Score": first_attempt.values,
    "Latest Attempt Score": latest_attempt.values,
    "Assessment Attempts": attempt_counts.values
})

student_summary["True Improvement"] = (
    student_summary["Latest Attempt Score"]
    - student_summary["First Attempt Score"]
)

student_summary["Improvement %"] = np.where(
    student_summary["First Attempt Score"] != 0,
    (
        student_summary["True Improvement"]
        / student_summary["First Attempt Score"]
    ) * 100,
    np.nan
)

student_summary["Team"] = (
    student_summary["Student Name"]
    .apply(normalize_name)
    .apply(assign_team)
)

# ============================================================
# QUESTION-WISE ATTEMPT COUNTS
# ============================================================

question_columns = [
    column
    for column in df.columns
    if str(column).upper().startswith("Q")
]

question_results = []

for question in question_columns:
    values = pd.to_numeric(
        df[question],
        errors="coerce"
    )

    question_results.append({
        "Question": question,
        "Average": values.mean(),
        "Attempted": values.notna().sum(),
        "Not Attempted": values.isna().sum()
    })

question_summary = pd.DataFrame(question_results)

# ============================================================
# MAIN METRICS
# ============================================================

st.subheader("📌 Overall Performance")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric(
    "👨‍🎓 Students",
    student_count
)

col2.metric(
    "📊 Average",
    f"{average_score:.2f}/15"
)

col3.metric(
    "🏆 Highest",
    f"{highest_score:.2f}/15"
)

col4.metric(
    "📉 Lowest",
    f"{lowest_score:.2f}/15"
)

col5.metric(
    "📍 Median",
    f"{median_score:.2f}"
)

col6.metric(
    "🔄 Total Attempts",
    len(df)
)

# ============================================================
# OUTLIER INFORMATION
# ============================================================

st.subheader("🔍 Outlier Analysis")

outlier_col1, outlier_col2, outlier_col3, outlier_col4 = st.columns(4)

outlier_col1.metric("Q1", f"{Q1:.2f}")
outlier_col2.metric("Q3", f"{Q3:.2f}")
outlier_col3.metric("IQR", f"{IQR:.2f}")
outlier_col4.metric("Outliers", len(outliers))

st.caption(
    "IQR rule: values below Q1 − 1.5×IQR or above Q3 + 1.5×IQR "
    "are treated as outliers. Outliers are excluded from the cleaned "
    "statistical analysis but are not deleted from the original data."
)

if len(outliers) > 0:
    st.dataframe(
        outliers[
            [
                "Student Name",
                score_column,
                "Percentage",
                "Team"
            ]
        ].sort_values(
            score_column,
            ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )
else:
    st.success("✅ No score outliers were detected.")

# ============================================================
# PERFORMANCE CATEGORIES
# ============================================================

performance_counts = (
    clean_df["Performance"]
    .value_counts()
    .reindex(
        [
            "Excellent",
            "Good",
            "Average",
            "Needs Improvement"
        ],
        fill_value=0
    )
)

st.subheader("📊 Performance Categories")

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "🌟 Excellent",
    int(performance_counts["Excellent"])
)

c2.metric(
    "👍 Good",
    int(performance_counts["Good"])
)

c3.metric(
    "📘 Average",
    int(performance_counts["Average"])
)

c4.metric(
    "⚠️ Needs Improvement",
    int(performance_counts["Needs Improvement"])
)

# ============================================================
# ACHIEVEMENT / WINNER SECTION
# ============================================================

st.subheader("🏆 Student Achievement Highlights")

# ---------- Highest score ----------

highest_rows = clean_df[
    clean_df[score_column] == clean_df[score_column].max()
].copy()

highest_names = ", ".join(
    highest_rows["Student Name"].astype(str)
)

# ---------- Most improvement ----------

improved_rows = student_summary[
    student_summary["True Improvement"]
    == student_summary["True Improvement"].max()
].copy()

most_improved_names = ", ".join(
    improved_rows["Student Name"].astype(str)
)

# ---------- Maximum attempts ----------

max_attempts = student_summary["Assessment Attempts"].max()

max_attempt_rows = student_summary[
    student_summary["Assessment Attempts"]
    == max_attempts
].copy()

max_attempt_names = ", ".join(
    max_attempt_rows["Student Name"].astype(str)
)

# ---------- Highest score with least time ----------

score_time_df = clean_df.dropna(
    subset=["Time (minutes)"]
).copy()

if len(score_time_df) > 0:
    highest_clean_score = score_time_df[score_column].max()

    high_score_fast_rows = score_time_df[
        score_time_df[score_column]
        == highest_clean_score
    ].sort_values(
        "Time (minutes)",
        ascending=True
    )

    fastest_high_score = high_score_fast_rows.iloc[0]

    fastest_high_score_name = fastest_high_score["Student Name"]
    fastest_high_score_value = fastest_high_score[score_column]
    fastest_high_score_time = fastest_high_score["Time (minutes)"]

else:
    fastest_high_score_name = "Duration not available"
    fastest_high_score_value = np.nan
    fastest_high_score_time = np.nan

# ---------- Best score per minute ----------

efficiency_df = clean_df.dropna(
    subset=["Time (minutes)"]
).copy()

efficiency_df = efficiency_df[
    efficiency_df["Time (minutes)"] > 0
].copy()

if len(efficiency_df) > 0:
    efficiency_df["Score per Minute"] = (
        efficiency_df[score_column]
        / efficiency_df["Time (minutes)"]
    )

    best_efficiency_row = efficiency_df.loc[
        efficiency_df["Score per Minute"].idxmax()
    ]

    best_efficiency_name = best_efficiency_row["Student Name"]
    best_efficiency_score = best_efficiency_row[score_column]
    best_efficiency_time = best_efficiency_row["Time (minutes)"]
    best_efficiency_value = best_efficiency_row["Score per Minute"]

else:
    best_efficiency_name = "Duration not available"
    best_efficiency_score = np.nan
    best_efficiency_time = np.nan
    best_efficiency_value = np.nan

a1, a2, a3 = st.columns(3)

a1.metric(
    "🏆 Highest Score",
    f"{highest_score:.2f}/15"
)
st.write(f"**Student:** {highest_names}")

a2.metric(
    "📈 Most Improvement",
    f"{student_summary['True Improvement'].max():.2f} marks"
)
st.write(f"**Student:** {most_improved_names}")

a3.metric(
    "🔄 Maximum Attempts",
    int(max_attempts)
)
st.write(f"**Student:** {max_attempt_names}")

b1, b2 = st.columns(2)

with b1:
    st.markdown("### ⚡ Highest Score in Least Time")

    if not pd.isna(fastest_high_score_time):
        st.write(
            f"**Student:** {fastest_high_score_name}"
        )
        st.write(
            f"**Score:** {fastest_high_score_value:.2f}/15"
        )
        st.write(
            f"**Time:** {fastest_high_score_time:.2f} minutes"
        )
    else:
        st.info("Duration information is not available.")

with b2:
    st.markdown("### 🎯 Best Score-Time Efficiency")

    if not pd.isna(best_efficiency_value):
        st.write(
            f"**Student:** {best_efficiency_name}"
        )
        st.write(
            f"**Score:** {best_efficiency_score:.2f}/15"
        )
        st.write(
            f"**Time:** {best_efficiency_time:.2f} minutes"
        )
        st.write(
            f"**Score per minute:** {best_efficiency_value:.3f}"
        )
    else:
        st.info("Duration information is not available.")

# ============================================================
# TRUE IMPROVEMENT TABLE
# ============================================================

st.subheader("📈 True Student Improvement")

improvement_display = student_summary.copy()

improvement_display["First Attempt Score"] = (
    improvement_display["First Attempt Score"].round(2)
)

improvement_display["Latest Attempt Score"] = (
    improvement_display["Latest Attempt Score"].round(2)
)

improvement_display["True Improvement"] = (
    improvement_display["True Improvement"].round(2)
)

improvement_display["Improvement %"] = (
    improvement_display["Improvement %"].round(2)
)

improvement_display = improvement_display.sort_values(
    "True Improvement",
    ascending=False
)

st.dataframe(
    improvement_display[
        [
            "Student Name",
            "Team",
            "First Attempt Score",
            "Latest Attempt Score",
            "True Improvement",
            "Improvement %",
            "Assessment Attempts"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

# ============================================================
# SCORE CHART
# ============================================================

st.subheader("📊 Student Score Comparison")

score_chart_df = clean_df[
    [
        "Student Name",
        score_column,
        "Team"
    ]
].sort_values(
    score_column,
    ascending=False
)

fig_score = px.bar(
    score_chart_df,
    x="Student Name",
    y=score_column,
    color="Team",
    text=score_column,
    title="Student Score Comparison",
    labels={
        "Student Name": "Student",
        score_column: "Score"
    }
)

fig_score.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)

fig_score.update_layout(
    xaxis_tickangle=-45,
    yaxis_title="Score out of 15",
    xaxis_title="Student",
    height=550
)

st.plotly_chart(
    fig_score,
    use_container_width=True
)

# ============================================================
# TRUE IMPROVEMENT CHART
# ============================================================

st.subheader("📈 Student Improvement: First Attempt → Latest Attempt")

fig_improvement = px.bar(
    improvement_display,
    x="Student Name",
    y="True Improvement",
    color="Team",
    text="True Improvement",
    title="Improvement from First Attempt to Latest Attempt",
    labels={
        "Student Name": "Student",
        "True Improvement": "Improvement in Marks"
    }
)

fig_improvement.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)

fig_improvement.update_layout(
    xaxis_tickangle=-45,
    xaxis_title="Student",
    yaxis_title="Improvement in Marks",
    height=550
)

st.plotly_chart(
    fig_improvement,
    use_container_width=True
)

# ============================================================
# SCORE VS TIME
# ============================================================

st.subheader("⏱️ Score vs Time")

if len(efficiency_df) > 0:

    fig_scatter = px.scatter(
        efficiency_df,
        x="Time (minutes)",
        y=score_column,
        color="Team",
        text="Student Name",
        size="Percentage",
        hover_data=[
            "Student Name",
            "Team",
            score_column,
            "Percentage",
            "Time (minutes)"
        ],
        title="Score vs Assessment Time",
        labels={
            "Time (minutes)": "Time (minutes)",
            score_column: "Score"
        }
    )

    fig_scatter.update_traces(
        textposition="top center"
    )

    fig_scatter.update_layout(
        xaxis_title="Assessment Time (minutes)",
        yaxis_title="Score out of 15",
        height=550
    )

    st.plotly_chart(
        fig_scatter,
        use_container_width=True
    )

else:
    st.info("Duration information is not available for the score-time chart.")

# ============================================================
# ATTEMPT COUNT CHART
# ============================================================

st.subheader("🔄 Assessment Attempts by Student")

attempt_chart = student_summary.sort_values(
    "Assessment Attempts",
    ascending=False
)

fig_attempts = px.bar(
    attempt_chart,
    x="Student Name",
    y="Assessment Attempts",
    color="Team",
    text="Assessment Attempts",
    title="Number of Assessment Attempts",
    labels={
        "Student Name": "Student",
        "Assessment Attempts": "Number of Attempts"
    }
)

fig_attempts.update_traces(
    textposition="outside"
)

fig_attempts.update_layout(
    xaxis_tickangle=-45,
    xaxis_title="Student",
    yaxis_title="Number of Attempts",
    height=550
)

st.plotly_chart(
    fig_attempts,
    use_container_width=True
)

# ============================================================
# DURATION TABLE
# ============================================================

st.subheader("⏱️ Student Duration and Efficiency")

duration_display = clean_df[
    [
        "Student Name",
        "Team",
        score_column,
        "Percentage",
        "Time (minutes)"
    ]
].copy()

duration_display["Score per Minute"] = np.where(
    duration_display["Time (minutes)"] > 0,
    duration_display[score_column]
    / duration_display["Time (minutes)"],
    np.nan
)

duration_display = duration_display.sort_values(
    "Score per Minute",
    ascending=False
)

duration_display["Percentage"] = (
    duration_display["Percentage"].round(2)
)

duration_display[score_column] = (
    duration_display[score_column].round(2)
)

duration_display["Time (minutes)"] = (
    duration_display["Time (minutes)"].round(2)
)

duration_display["Score per Minute"] = (
    duration_display["Score per Minute"].round(3)
)

st.dataframe(
    duration_display,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# APPLE VS ORANGE TEAM COMPARISON
# ============================================================

st.subheader("🍎 Apple vs 🟠 Orange — Complete Team Comparison")

team_df = clean_df[
    clean_df["Team"].isin(["Apple", "Orange"])
].copy()

team_summary_rows = []

for team in ["Apple", "Orange"]:

    team_clean = clean_df[
        clean_df["Team"] == team
    ].copy()

    team_original = df[
        df["Team"] == team
    ].copy()

    team_students = student_summary[
        student_summary["Team"] == team
    ].copy()

    team_summary_rows.append({
        "Team": team,
        "Students": team_students["Student Name"].nunique(),
        "Assessment Attempts": len(team_original),
        "Average Score": team_clean[score_column].mean(),
        "Highest Score": team_clean[score_column].max(),
        "Lowest Score": team_clean[score_column].min(),
        "Average Percentage": team_clean["Percentage"].mean(),
        "Average Time (min)": team_clean["Time (minutes)"].mean(),
        "Average Attempts / Student": team_students[
            "Assessment Attempts"
        ].mean(),
        "Total Improvement": team_students[
            "True Improvement"
        ].sum(),
        "Average Improvement": team_students[
            "True Improvement"
        ].mean()
    })

team_summary = pd.DataFrame(
    team_summary_rows
)

team_summary_display = team_summary.copy()

for column in [
    "Average Score",
    "Highest Score",
    "Lowest Score",
    "Average Percentage",
    "Average Time (min)",
    "Average Attempts / Student",
    "Total Improvement",
    "Average Improvement"
]:
    team_summary_display[column] = (
        team_summary_display[column].round(2)
    )

st.dataframe(
    team_summary_display,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# TEAM WINNER: MORE SCORE + LESS TIME
# ============================================================

st.markdown("### 🏆 Which Team Scores More in Less Time?")

valid_team_summary = team_summary.dropna(
    subset=[
        "Average Score",
        "Average Time (min)"
    ]
).copy()

if len(valid_team_summary) == 2:

    higher_score_team = valid_team_summary.loc[
        valid_team_summary["Average Score"].idxmax(),
        "Team"
    ]

    lower_time_team = valid_team_summary.loc[
        valid_team_summary["Average Time (min)"].idxmin(),
        "Team"
    ]

    if higher_score_team == lower_time_team:

        st.success(
            f"🏆 **{higher_score_team} is the stronger score-time team**: "
            f"it has the higher average score and the lower average time."
        )

    else:

        score_team = higher_score_team
        time_team = lower_time_team

        st.warning(
            f"📊 The results are mixed: **{score_team}** has the higher "
            f"average score, while **{time_team}** has the lower average time."
        )

        st.write(
            "Therefore, there is no single winner based on both criteria."
        )

else:
    st.info(
        "Both teams need usable score and duration data for this comparison."
    )

# ============================================================
# TEAM AVERAGE SCORE CHART
# ============================================================

st.subheader("🍎🟠 Average Score: Apple vs Orange")

fig_team_score = px.bar(
    team_summary,
    x="Team",
    y="Average Score",
    color="Team",
    text="Average Score",
    title="Average Score by Team",
    labels={
        "Team": "Team",
        "Average Score": "Average Score"
    }
)

fig_team_score.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)

fig_team_score.update_layout(
    xaxis_title="Team",
    yaxis_title="Average Score out of 15",
    height=450
)

st.plotly_chart(
    fig_team_score,
    use_container_width=True
)

# ============================================================
# TEAM TIME CHART
# ============================================================

st.subheader("⏱️ Average Time: Apple vs Orange")

fig_team_time = px.bar(
    team_summary,
    x="Team",
    y="Average Time (min)",
    color="Team",
    text="Average Time (min)",
    title="Average Assessment Time by Team",
    labels={
        "Team": "Team",
        "Average Time (min)": "Average Time (minutes)"
    }
)

fig_team_time.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)

fig_team_time.update_layout(
    xaxis_title="Team",
    yaxis_title="Average Time (minutes)",
    height=450
)

st.plotly_chart(
    fig_team_time,
    use_container_width=True
)

# ============================================================
# TEAM PERCENTAGE CHART
# ============================================================

st.subheader("📊 Average Percentage: Apple vs Orange")

fig_team_percentage = px.bar(
    team_summary,
    x="Team",
    y="Average Percentage",
    color="Team",
    text="Average Percentage",
    title="Average Percentage by Team",
    labels={
        "Team": "Team",
        "Average Percentage": "Average Percentage"
    }
)

fig_team_percentage.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside"
)

fig_team_percentage.update_layout(
    xaxis_title="Team",
    yaxis_title="Average Percentage",
    height=450
)

st.plotly_chart(
    fig_team_percentage,
    use_container_width=True
)

# ============================================================
# TEAM ATTEMPTS CHART
# ============================================================

st.subheader("🔄 Assessment Attempts: Apple vs Orange")

fig_team_attempts = px.bar(
    team_summary,
    x="Team",
    y="Assessment Attempts",
    color="Team",
    text="Assessment Attempts",
    title="Total Assessment Attempts by Team",
    labels={
        "Team": "Team",
        "Assessment Attempts": "Total Attempts"
    }
)

fig_team_attempts.update_traces(
    textposition="outside"
)

fig_team_attempts.update_layout(
    xaxis_title="Team",
    yaxis_title="Total Assessment Attempts",
    height=450
)

st.plotly_chart(
    fig_team_attempts,
    use_container_width=True
)

# ============================================================
# TEAM IMPROVEMENT CHART
# ============================================================

st.subheader("📈 Average Improvement: Apple vs Orange")

fig_team_improvement = px.bar(
    team_summary,
    x="Team",
    y="Average Improvement",
    color="Team",
    text="Average Improvement",
    title="Average Improvement by Team",
    labels={
        "Team": "Team",
        "Average Improvement": "Average Improvement (marks)"
    }
)

fig_team_improvement.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside"
)

fig_team_improvement.update_layout(
    xaxis_title="Team",
    yaxis_title="Average Improvement (marks)",
    height=450
)

st.plotly_chart(
    fig_team_improvement,
    use_container_width=True
)

# ============================================================
# TEAM MEMBER COMPARISON
# ============================================================

st.subheader("👥 Student-wise Apple vs Orange Comparison")

team_member_display = student_summary.copy()

# Add average score and average time per student
student_avg_score = (
    clean_df
    .groupby("Student Name")[score_column]
    .mean()
    .rename("Average Score")
)

student_avg_percentage = (
    clean_df
    .groupby("Student Name")["Percentage"]
    .mean()
    .rename("Average Percentage")
)

student_avg_time = (
    clean_df
    .groupby("Student Name")["Time (minutes)"]
    .mean()
    .rename("Average Time (min)")
)

team_member_display = (
    team_member_display
    .set_index("Student Name")
    .join(student_avg_score)
    .join(student_avg_percentage)
    .join(student_avg_time)
    .reset_index()
)

team_member_display = team_member_display[
    team_member_display["Team"].isin(
        ["Apple", "Orange"]
    )
].copy()

for column in [
    "Average Score",
    "Average Percentage",
    "Average Time (min)",
    "First Attempt Score",
    "Latest Attempt Score",
    "True Improvement"
]:
    team_member_display[column] = (
        team_member_display[column].round(2)
    )

st.dataframe(
    team_member_display[
        [
            "Student Name",
            "Team",
            "Average Score",
            "Average Percentage",
            "Average Time (min)",
            "Assessment Attempts",
            "First Attempt Score",
            "Latest Attempt Score",
            "True Improvement"
        ]
    ].sort_values(
        ["Team", "Average Score"],
        ascending=[True, False]
    ),
    use_container_width=True,
    hide_index=True
)

# ============================================================
# QUESTION-WISE ANALYSIS
# ============================================================

st.subheader("📝 Question-wise Analysis")

if len(question_summary) > 0:

    question_display = question_summary.copy()

    question_display["Average"] = (
        question_display["Average"].round(2)
    )

    st.dataframe(
        question_display,
        use_container_width=True,
        hide_index=True
    )

    fig_question = px.bar(
        question_summary,
        x="Question",
        y="Average",
        text="Average",
        title="Question-wise Average Score",
        labels={
            "Question": "Question",
            "Average": "Average Score"
        }
    )

    fig_question.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside"
    )

    fig_question.update_layout(
        xaxis_title="Question",
        yaxis_title="Average Score",
        height=500
    )

    st.plotly_chart(
        fig_question,
        use_container_width=True
    )

else:
    st.info("No question columns beginning with Q were found.")

# ============================================================
# COMPLETE CLEANED ANALYSIS
# ============================================================

st.subheader("📋 Complete Cleaned Student Analysis")

complete_columns = [
    "Student Name",
    "Team",
    score_column,
    "Percentage",
    "Difference from Class Average",
    "Improvement Status",
    "Performance",
    "Outlier",
    "Time (minutes)",
    "Attempt Number"
]

extra_columns = [
    "Email address",
    "Status",
    "Started",
    "Completed",
    "Duration"
]

complete_columns += [
    column
    for column in extra_columns
    if column in clean_df.columns
]

complete_df = clean_df[
    complete_columns
].copy()

for column in [
    "Percentage",
    "Difference from Class Average",
    "Time (minutes)"
]:
    if column in complete_df.columns:
        complete_df[column] = (
            complete_df[column].round(2)
        )

complete_df = complete_df.sort_values(
    score_column,
    ascending=False
)

st.dataframe(
    complete_df,
    use_container_width=True,
    hide_index=True
)

# ============================================================
# DOWNLOADS
# ============================================================

st.subheader("⬇️ Download Analysis")

download_col1, download_col2, download_col3 = st.columns(3)

# Complete cleaned analysis
clean_csv = complete_df.to_csv(index=False)

download_col1.download_button(
    label="📥 Cleaned Analysis CSV",
    data=clean_csv,
    file_name="cleaned_student_analysis.csv",
    mime="text/csv"
)

# Student summary
summary_csv = student_summary.to_csv(index=False)

download_col2.download_button(
    label="📥 Student Summary CSV",
    data=summary_csv,
    file_name="student_attempt_summary.csv",
    mime="text/csv"
)

# Team summary
team_csv = team_summary_display.to_csv(index=False)

download_col3.download_button(
    label="📥 Team Comparison CSV",
    data=team_csv,
    file_name="apple_orange_team_comparison.csv",
    mime="text/csv"
)

st.markdown("---")

st.caption(
    "📊 Student Performance Dashboard | "
    "IQR-based outlier detection | "
    "Attempt-based improvement | "
    "Apple vs Orange team analysis"
)
