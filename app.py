import streamlit as st
import pandas as pd

# ------------------------------------------------------------

# PAGE SETTINGS

# ------------------------------------------------------------

st.set_page_config(
page_title="Student Improvement Analysis",
page_icon="📈",
layout="wide"
)

# ------------------------------------------------------------

# TITLE

# ------------------------------------------------------------

st.title("📊 Student Performance Dashboard")
st.header("📈 Student Improvement Analysis")

st.write(
"Upload the assessment CSV file to analyse student scores, "
"percentages, improvement and question-wise performance."
)

# ------------------------------------------------------------

# SIDEBAR - FILE UPLOAD

# ------------------------------------------------------------

st.sidebar.header("📂 Upload CSV")

uploaded_file = st.sidebar.file_uploader(
"Choose your CSV file",
type=["csv"]
)

# ------------------------------------------------------------

# STOP UNTIL FILE IS UPLOADED

# ------------------------------------------------------------

if uploaded_file is None:
st.info("Please upload your CSV file from the sidebar.")
st.stop()

# ------------------------------------------------------------

# READ CSV

# ------------------------------------------------------------

try:
df = pd.read_csv(uploaded_file)
except Exception as e:
st.error(f"Error reading CSV file: {e}")
st.stop()

# ------------------------------------------------------------

# CLEAN COLUMN NAMES

# ------------------------------------------------------------

df.columns = df.columns.astype(str).str.strip()

# ------------------------------------------------------------

# SHOW ORIGINAL DATA

# ------------------------------------------------------------

st.subheader("📋 Uploaded Data")

st.dataframe(
df,
use_container_width=True,
hide_index=True
)

# ------------------------------------------------------------

# FIND SCORE COLUMN

# ------------------------------------------------------------

score_column = None

possible_score_columns = [
"Grade/15.00",
"Grade",
"Score",
"Marks",
"Total",
"Final Score"
]

for column in possible_score_columns:
if column in df.columns:
score_column = column
break

# ------------------------------------------------------------

# AUTOMATIC SCORE COLUMN DETECTION

# ------------------------------------------------------------

if score_column is None:

```
for column in df.columns:

    numeric_values = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    if numeric_values.notna().sum() > 0:
        score_column = column
        break
```

# ------------------------------------------------------------

# SCORE COLUMN CHECK

# ------------------------------------------------------------

if score_column is None:

```
st.error("❌ Could not find a numerical score column.")

st.write("Columns detected in your CSV:")

st.write(list(df.columns))

st.stop()
```

# ------------------------------------------------------------

# CONVERT SCORE TO NUMBER

# ------------------------------------------------------------

df[score_column] = pd.to_numeric(
df[score_column],
errors="coerce"
)

df = df.dropna(
subset=[score_column]
).copy()

# ------------------------------------------------------------

# DETERMINE STUDENT NAME

# ------------------------------------------------------------

if "First name" in df.columns and "Last name" in df.columns:

```
df["Student Name"] = (
    df["First name"].fillna("").astype(str).str.strip()
    + " "
    + df["Last name"].fillna("").astype(str).str.strip()
).str.strip()
```

elif "First name" in df.columns:

```
df["Student Name"] = (
    df["First name"]
    .fillna("")
    .astype(str)
    .str.strip()
)
```

elif "Last name" in df.columns:

```
df["Student Name"] = (
    df["Last name"]
    .fillna("")
    .astype(str)
    .str.strip()
)
```

elif "Email address" in df.columns:

```
df["Student Name"] = (
    df["Email address"]
    .fillna("")
    .astype(str)
    .str.strip()
)
```

else:

```
df["Student Name"] = [
    f"Student {i + 1}"
    for i in range(len(df))
]
```

# ------------------------------------------------------------

# MAXIMUM MARK

# ------------------------------------------------------------

max_score = 15.0

if df[score_column].max() > 15:
max_score = float(df[score_column].max())

# ------------------------------------------------------------

# BASIC STATISTICS

# ------------------------------------------------------------

student_count = len(df)

average_score = df[score_column].mean()

highest_score = df[score_column].max()

lowest_score = df[score_column].min()

median_score = df[score_column].median()

# ------------------------------------------------------------

# PERCENTAGE

# ------------------------------------------------------------

df["Percentage"] = (
df[score_column] / max_score
) * 100

df["Percentage"] = df["Percentage"].clip(0, 100)

# ------------------------------------------------------------

# IMPROVEMENT

# ------------------------------------------------------------

# Positive = above class average

# Negative = below class average

df["Improvement"] = (
df[score_column] - average_score
)

# ------------------------------------------------------------

# PERFORMANCE CATEGORY

# ------------------------------------------------------------

def performance_category(score):

```
percentage = (
    score / max_score
) * 100

if percentage >= 80:
    return "Excellent"

elif percentage >= 60:
    return "Good"

elif percentage >= 40:
    return "Average"

else:
    return "Needs Improvement"
```

df["Performance"] = df[score_column].apply(
performance_category
)

# ------------------------------------------------------------

# OVERALL METRICS

# ------------------------------------------------------------

st.subheader("📌 Overall Performance")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
st.metric(
"👨‍🎓 Students",
student_count
)

with col2:
st.metric(
"📊 Class Average",
f"{average_score:.2f}"
)

with col3:
st.metric(
"🏆 Highest",
f"{highest_score:.2f}"
)

with col4:
st.metric(
"📉 Lowest",
f"{lowest_score:.2f}"
)

with col5:
st.metric(
"📍 Median",
f"{median_score:.2f}"
)

# ------------------------------------------------------------

# PERFORMANCE COUNTS

# ------------------------------------------------------------

excellent = (
df["Performance"] == "Excellent"
).sum()

good = (
df["Performance"] == "Good"
).sum()

average = (
df["Performance"] == "Average"
).sum()

needs_improvement = (
df["Performance"] == "Needs Improvement"
).sum()

st.subheader("📊 Performance Categories")

col1, col2, col3, col4 = st.columns(4)

with col1:
st.metric("🌟 Excellent", excellent)

with col2:
st.metric("👍 Good", good)

with col3:
st.metric("📘 Average", average)

with col4:
st.metric(
"⚠️ Needs Improvement",
needs_improvement
)

# ------------------------------------------------------------

# SCORE CHART

# ------------------------------------------------------------

st.subheader("📈 Student Score Comparison")

score_chart = (
df[
["Student Name", score_column]
]
.sort_values(
by=score_column,
ascending=False
)
.set_index("Student Name")
)

st.bar_chart(
score_chart,
height=450
)

# ------------------------------------------------------------

# SCORE LABEL TABLE

# ------------------------------------------------------------

st.subheader("🔢 Score Details")

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
+ " / "
+ str(int(max_score))
)

score_details["Percentage"] = (
score_details["Percentage"]
.round(2)
)

score_details = score_details.sort_values(
by=score_column,
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

# ------------------------------------------------------------

# IMPROVEMENT CHART

# ------------------------------------------------------------

st.subheader("📈 Improvement Relative to Class Average")

improvement_chart = (
df[
["Student Name", "Improvement"]
]
.sort_values(
by="Improvement",
ascending=False
)
.set_index("Student Name")
)

st.bar_chart(
improvement_chart,
height=450
)

# ------------------------------------------------------------

# IMPROVEMENT TABLE

# ------------------------------------------------------------

st.subheader("🔎 Improvement Details")

improvement_table = df[
[
"Student Name",
score_column,
"Improvement",
"Performance"
]
].copy()

improvement_table["Improvement"] = (
improvement_table["Improvement"]
.round(2)
)

def improvement_status(value):

```
if value > 0:
    return "Above Class Average"

elif value == 0:
    return "At Class Average"

else:
    return "Below Class Average"
```

improvement_table["Status"] = (
improvement_table["Improvement"]
.apply(improvement_status)
)

improvement_table = improvement_table.sort_values(
by="Improvement",
ascending=False
)

st.dataframe(
improvement_table,
use_container_width=True,
hide_index=True
)

# ------------------------------------------------------------

# PERCENTAGE CHART

# ------------------------------------------------------------

st.subheader("📊 Student Percentage")

percentage_chart = (
df[
["Student Name", "Percentage"]
]
.sort_values(
by="Percentage",
ascending=False
)
.set_index("Student Name")
)

st.bar_chart(
percentage_chart,
height=450
)

# ------------------------------------------------------------

# TOP STUDENTS

# ------------------------------------------------------------

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

# ------------------------------------------------------------

# STUDENTS BELOW AVERAGE

# ------------------------------------------------------------

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

if len(below_average) > 0:

```
st.dataframe(
    below_average,
    use_container_width=True,
    hide_index=True
)
```

else:

```
st.success(
    "✅ No student is below the class average."
)
```

# ------------------------------------------------------------

# DURATION

# ------------------------------------------------------------

if "Duration" in df.columns:

```
st.subheader("⏱️ Assessment Duration")

duration_data = df[
    [
        "Student Name",
        "Duration"
    ]
].copy()

st.dataframe(
    duration_data,
    use_container_width=True,
    hide_index=True
)
```

# ------------------------------------------------------------

# STATUS

# ------------------------------------------------------------

if "Status" in df.columns:

```
st.subheader("📌 Student Status")

status_data = (
    df["Status"]
    .fillna("Unknown")
    .value_counts()
    .rename_axis("Status")
    .reset_index(name="Students")
)

st.dataframe(
    status_data,
    use_container_width=True,
    hide_index=True
)
```

# ------------------------------------------------------------

# QUESTION-WISE ANALYSIS

# ------------------------------------------------------------

question_columns = [
column
for column in df.columns
if str(column).upper().startswith("Q")
]

if len(question_columns) > 0:

```
st.subheader("📝 Question-wise Analysis")

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

question_summary["Average"] = (
    question_summary["Average"]
    .round(2)
)

st.dataframe(
    question_summary,
    use_container_width=True,
    hide_index=True
)

question_chart = (
    question_summary[
        ["Question", "Average"]
    ]
    .set_index("Question")
)

st.bar_chart(
    question_chart,
    height=400
)
```

# ------------------------------------------------------------

# COMPLETE ANALYSIS

# ------------------------------------------------------------

st.subheader("📋 Complete Student Analysis")

complete_columns = [
"Student Name",
score_column,
"Percentage",
"Improvement",
"Performance"
]

for column in [
"Email address",
"Status",
"Started",
"Completed",
"Duration"
]:

```
if column in df.columns:
    complete_columns.append(column)
```

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
by=score_column,
ascending=False
)

st.dataframe(
complete_df,
use_container_width=True,
hide_index=True
)

# ------------------------------------------------------------

# DOWNLOAD

# ------------------------------------------------------------

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

# ------------------------------------------------------------

# FOOTER

# ------------------------------------------------------------

st.markdown("---")

st.caption(
"📊 Student Improvement Analysis Dashboard"
)
