import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Student Improvement Analysis",
    page_icon="📈",
    layout="wide"
)

st.title("📊 Student Performance Dashboard")
st.header("📈 Student Improvement Analysis")
st.write("Upload the assessment CSV file to analyse student performance.")

# --------------------------------------------------
# FILE UPLOAD
# --------------------------------------------------

st.sidebar.header("📂 Upload CSV")

uploaded_file = st.sidebar.file_uploader(
    "Choose your CSV file",
    type=["csv"]
)

if uploaded_file is None: st.info("Please upload your CSV file from the sidebar."); st.stop()

# --------------------------------------------------
# READ CSV
# --------------------------------------------------

df = pd.read_csv(uploaded_file)

df.columns = df.columns.astype(str).str.strip()

st.success("✅ CSV uploaded successfully.")

# --------------------------------------------------
# SHOW ORIGINAL DATA
# --------------------------------------------------

st.subheader("📋 Uploaded Data")

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# FIND SCORE COLUMN
# --------------------------------------------------

possible_score_columns = [
    "Grade/15.00",
    "Grade",
    "Score",
    "Marks",
    "Total",
    "Final Score"
]

numeric_columns = df.select_dtypes(
    include="number"
).columns.tolist()

score_column = next(
    (column for column in possible_score_columns if column in df.columns),
    numeric_columns[0] if numeric_columns else None
)

score_column is None and st.error("❌ No score column was found.")
score_column is None and st.write("Available columns:", list(df.columns))
score_column is None and st.stop()

# --------------------------------------------------
# CONVERT SCORE
# --------------------------------------------------

df[score_column] = pd.to_numeric(
    df[score_column],
    errors="coerce"
)

df = df.dropna(
    subset=[score_column]
).copy()

# --------------------------------------------------
# STUDENT NAME
# --------------------------------------------------

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

# --------------------------------------------------
# BASIC STATISTICS
# --------------------------------------------------

max_score = 15.0

student_count = len(df)

average_score = df[score_column].mean()

highest_score = df[score_column].max()

lowest_score = df[score_column].min()

median_score = df[score_column].median()

# --------------------------------------------------
# PERCENTAGE
# --------------------------------------------------

df["Percentage"] = (
    df[score_column] / max_score
) * 100

df["Percentage"] = df["Percentage"].clip(
    0,
    100
)

# --------------------------------------------------
# IMPROVEMENT
# --------------------------------------------------

df["Improvement"] = (
    df[score_column] - average_score
)

# --------------------------------------------------
# PERFORMANCE CATEGORY
# --------------------------------------------------

df["Performance"] = pd.cut(
    df["Percentage"],
    bins=[-1, 40, 60, 80, 101],
    labels=[
        "Needs Improvement",
        "Average",
        "Good",
        "Excellent"
    ],
    right=False
)

# --------------------------------------------------
# IMPROVEMENT STATUS
# --------------------------------------------------

df["Improvement Status"] = pd.cut(
    df["Improvement"],
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

# --------------------------------------------------
# MAIN METRICS
# --------------------------------------------------

st.subheader("📌 Overall Performance")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "👨‍🎓 Students",
    student_count
)

col2.metric(
    "📊 Class Average",
    f"{average_score:.2f}/15"
)

col3.metric(
    "🏆 Highest",
    f"{highest_score:.2f}"
)

col4.metric(
    "📉 Lowest",
    f"{lowest_score:.2f}"
)

col5.metric(
    "📍 Median",
    f"{median_score:.2f}"
)

# --------------------------------------------------
# PERFORMANCE COUNTS
# --------------------------------------------------

performance_counts = (
    df["Performance"]
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

# --------------------------------------------------
# SCORE CHART
# --------------------------------------------------

st.subheader("📈 Student Score Comparison")

score_chart = (
    df[
        ["Student Name", score_column]
    ]
    .sort_values(
        score_column,
        ascending=False
    )
    .set_index("Student Name")
)

st.bar_chart(
    score_chart,
    height=450
)

# --------------------------------------------------
# SCORE DATA LABELS
# --------------------------------------------------

st.markdown("### 🔢 Score Details")

score_details = df[
    [
        "Student Name",
        score_column,
        "Percentage",
        "Performance"
    ]
].copy()

score_details["Score"] = (
    score_details[score_column]
    .round(2)
    .astype(str)
    + " / 15"
)

score_details["Percentage"] = (
    score_details["Percentage"]
    .round(2)
    .astype(str)
    + "%"
)

score_details = score_details.sort_values(
    score_column,
    ascending=False
)

st.dataframe(
    score_details[
        [
            "Student Name",
            "Score",
            "Percentage",
            "Performance"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# IMPROVEMENT CHART
# --------------------------------------------------

st.subheader("📈 Improvement Relative to Class Average")

improvement_chart = (
    df[
        ["Student Name", "Improvement"]
    ]
    .sort_values(
        "Improvement",
        ascending=False
    )
    .set_index("Student Name")
)

st.bar_chart(
    improvement_chart,
    height=450
)

# --------------------------------------------------
# IMPROVEMENT DETAILS
# --------------------------------------------------

st.markdown("### 🔎 Improvement Details")

improvement_details = df[
    [
        "Student Name",
        score_column,
        "Improvement",
        "Improvement Status"
    ]
].copy()

improvement_details["Improvement"] = (
    improvement_details["Improvement"]
    .round(2)
)

improvement_details = improvement_details.sort_values(
    "Improvement",
    ascending=False
)

st.dataframe(
    improvement_details,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# PERCENTAGE CHART
# --------------------------------------------------

st.subheader("📊 Student Percentage")

percentage_chart = (
    df[
        ["Student Name", "Percentage"]
    ]
    .sort_values(
        "Percentage",
        ascending=False
    )
    .set_index("Student Name")
)

st.bar_chart(
    percentage_chart,
    height=450
)

# --------------------------------------------------
# TOP STUDENTS
# --------------------------------------------------

st.subheader("🏆 Top Performing Students")

top_students = df.nlargest(
    min(5, len(df)),
    score_column
)[
    [
        "Student Name",
        score_column,
        "Percentage",
        "Performance"
    ]
].copy()

top_students["Percentage"] = (
    top_students["Percentage"]
    .round(2)
)

st.dataframe(
    top_students,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# STUDENTS BELOW AVERAGE
# --------------------------------------------------

st.subheader("⚠️ Students Below Class Average")

below_average = df[
    df[score_column] < average_score
][
    [
        "Student Name",
        score_column,
        "Percentage",
        "Improvement"
    ]
].copy()

below_average["Percentage"] = (
    below_average["Percentage"]
    .round(2)
)

below_average["Improvement"] = (
    below_average["Improvement"]
    .round(2)
)

st.dataframe(
    below_average,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# DURATION
# --------------------------------------------------

st.subheader("⏱️ Assessment Duration")

duration_data = pd.DataFrame()

duration_data["Student Name"] = df["Student Name"]

duration_data["Duration"] = df.get(
    "Duration",
    pd.Series("Not available", index=df.index)
)

st.dataframe(
    duration_data,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# STATUS
# --------------------------------------------------

st.subheader("📌 Student Status")

status_data = pd.DataFrame()

status_data["Student Name"] = df["Student Name"]

status_data["Status"] = df.get(
    "Status",
    pd.Series("Not available", index=df.index)
)

st.dataframe(
    status_data,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# QUESTION-WISE ANALYSIS
# --------------------------------------------------

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

    question_results.append(
        {
            "Question": question,
            "Average": values.mean(),
            "Attempted": values.notna().sum()
        }
    )

question_summary = pd.DataFrame(
    question_results
)

st.subheader("📝 Question-wise Analysis")

st.dataframe(
    question_summary,
    use_container_width=True,
    hide_index=True
)

question_columns and st.bar_chart(
    question_summary.set_index("Question")["Average"],
    height=400
)

# --------------------------------------------------
# COMPLETE ANALYSIS
# --------------------------------------------------

st.subheader("📋 Complete Student Analysis")

complete_columns = [
    "Student Name",
    score_column,
    "Percentage",
    "Improvement",
    "Performance",
    "Improvement Status"
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
    if column in df.columns
]

complete_df = df[
    complete_columns
].copy()

complete_df["Percentage"] = (
    complete_df["Percentage"]
    .round(2)
)

complete_df["Improvement"] = (
    complete_df["Improvement"]
    .round(2)
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

# --------------------------------------------------
# DOWNLOAD
# --------------------------------------------------

st.subheader("⬇️ Download Analysis")

csv_output = complete_df.to_csv(
    index=False
)

st.download_button(
    label="📥 Download Complete Analysis CSV",
    data=csv_output,
    file_name="student_improvement_analysis.csv",
    mime="text/csv"
)

st.markdown("---")

st.caption(
    "📊 Student Improvement Analysis Dashboard"
)
