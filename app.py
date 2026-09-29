import streamlit as st
import pandas as pd

st.set_page_config(
page_title="Student Improvement Analysis",
page_icon="📈",
layout="wide"
)

st.title("📊 Student Performance Dashboard")
st.header("📈 Student Improvement Analysis")

st.markdown(
"""
This dashboard analyses student assessment performance,
scores, percentages, duration, and improvement relative
to the class average.
"""
)

st.sidebar.title("📂 Data Upload")

uploaded_file = st.sidebar.file_uploader(
"Upload your CSV file",
type=["csv"]
)

if uploaded_file is None:
st.info("Please upload your CSV file from the sidebar.")
st.stop()

try:
df = pd.read_csv(uploaded_file)
except Exception as e:
st.error(f"Unable to read the CSV file: {e}")
st.stop()

df.columns = df.columns.astype(str).str.strip()

with st.expander("📋 View Original CSV Data"):
st.dataframe(
df,
use_container_width=True,
hide_index=True
)

score_column = None

possible_score_columns = [
"Grade/15.00",
"Grade",
"Score",
"Marks",
"Total",
"Final Score"
]

for col in possible_score_columns:
if col in df.columns:
score_column = col
break

if score_column is None:
for col in df.columns:
converted = pd.to_numeric(
df[col],
errors="coerce"
)

```
    if converted.notna().sum() > 0:
        score_column = col
        break
```

if score_column is None:
st.error("❌ No numerical score column was found.")
st.write("Available columns:")
st.write(list(df.columns))
st.stop()

df[score_column] = pd.to_numeric(
df[score_column],
errors="coerce"
)

df = df.dropna(
subset=[score_column]
).copy()

max_score = 15.0

if df[score_column].max() > 15:
max_score = float(df[score_column].max())

if "First name" in df.columns and "Last name" in df.columns:
df["Student Name"] = (
df["First name"].fillna("").astype(str).str.strip()
+ " "
+ df["Last name"].fillna("").astype(str).str.strip()
).str.strip()

elif "First name" in df.columns:
df["Student Name"] = (
df["First name"]
.fillna("")
.astype(str)
.str.strip()
)

elif "Last name" in df.columns:
df["Student Name"] = (
df["Last name"]
.fillna("")
.astype(str)
.str.strip()
)

elif "Email address" in df.columns:
df["Student Name"] = (
df["Email address"]
.fillna("")
.astype(str)
)

else:
df["Student Name"] = [
f"Student {i + 1}"
for i in range(len(df))
]

average_score = df[score_column].mean()
highest_score = df[score_column].max()
lowest_score = df[score_column].min()
median_score = df[score_column].median()
number_students = len(df)

df["Percentage"] = (
df[score_column] / max_score
) * 100

df["Percentage"] = df["Percentage"].clip(0, 100)

df["Improvement"] = (
df[score_column] - average_score
)

def get_category(score):
percentage = (score / max_score) * 100

```
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
get_category
)

st.subheader("📌 Overall Performance")

c1, c2, c3, c4, c5 = st.columns(5)

with c1:
st.metric(
"👨‍🎓 Students",
number_students
)

with c2:
st.metric(
"📊 Average Score",
f"{average_score:.2f}/{max_score:.0f}"
)

with c3:
st.metric(
"🏆 Highest Score",
f"{highest_score:.2f}"
)

with c4:
st.metric(
"📉 Lowest Score",
f"{lowest_score:.2f}"
)

with c5:
st.metric(
"📍 Median",
f"{median_score:.2f}"
)

excellent_count = (
df["Performance"] == "Excellent"
).sum()

good_count = (
df["Performance"] == "Good"
).sum()

average_count = (
df["Performance"] == "Average"
).sum()

improvement_count = (
df["Performance"] == "Needs Improvement"
).sum()

st.subheader("📊 Performance Categories")

c1, c2, c3, c4 = st.columns(4)

with c1:
st.metric("🌟 Excellent", excellent_count)

with c2:
st.metric("👍 Good", good_count)

with c3:
st.metric("📘 Average", average_count)

with c4:
st.metric(
"⚠️ Needs Improvement",
improvement_count
)

st.subheader("📈 Student Score Comparison")

score_chart = (
df[["Student Name", score_column]]
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

st.subheader("🔢 Student Score Labels")

score_labels = df[
["Student Name", score_column]
].copy()

score_labels["Score Label"] = (
score_labels[score_column]
.round(2)
.astype(str)
+ " / "
+ str(int(max_score))
)

score_labels = score_labels.sort_values(
by=score_column,
ascending=False
)

st.dataframe(
score_labels[
["Student Name", "Score Label"]
],
use_container_width=True,
hide_index=True
)

st.subheader("📈 Improvement Relative to Class Average")

improvement_chart = (
df[["Student Name", "Improvement"]]
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

st.subheader("🔎 Improvement Details")

improvement_details = df[
[
"Student Name",
score_column,
"Improvement",
"Performance"
]
].copy()

improvement_details["Improvement"] = (
improvement_details["Improvement"]
.round(2)
)

improvement_details["Status"] = (
improvement_details["Improvement"]
.apply(
lambda x:
"Above Class Average"
if x > 0
else (
"At Class Average"
if x == 0
else "Below Class Average"
)
)
)

improvement_details = improvement_details.sort_values(
by="Improvement",
ascending=False
)

st.dataframe(
improvement_details,
use_container_width=True,
hide_index=True
)

st.subheader("📊 Student Percentage")

percentage_chart = (
df[["Student Name", "Percentage"]]
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

st.subheader("🏆 Highest Scores")

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

st.subheader("⚠️ Students Below Class Average")

students_below_average = df[
df[score_column] < average_score
][
[
"Student Name",
score_column,
"Percentage",
"Improvement"
]
].copy()

students_below_average["Percentage"] = (
students_below_average["Percentage"]
.round(2)
)

students_below_average["Improvement"] = (
students_below_average["Improvement"]
.round(2)
)

if len(students_below_average) > 0:
st.dataframe(
students_below_average,
use_container_width=True,
hide_index=True
)
else:
st.success(
"✅ No student is below the class average."
)

if "Duration" in df.columns:
st.subheader("⏱️ Assessment Duration")

```
duration_df = df[
    ["Student Name", "Duration"]
].copy()

st.dataframe(
    duration_df,
    use_container_width=True,
    hide_index=True
)
```

if "Status" in df.columns:
st.subheader("📌 Student Status")

```
status_counts = (
    df["Status"]
    .fillna("Unknown")
    .value_counts()
    .rename_axis("Status")
    .reset_index(name="Students")
)

st.dataframe(
    status_counts,
    use_container_width=True,
    hide_index=True
)
```

question_columns = [
col
for col in df.columns
if str(col).upper().startswith("Q")
]

if len(question_columns) > 0:
st.subheader("📝 Question-wise Analysis")

```
question_summary = []

for question in question_columns:
    numeric_values = pd.to_numeric(
        df[question],
        errors="coerce"
    )

    question_summary.append(
        {
            "Question": question,
            "Average": numeric_values.mean(),
            "Attempted": numeric_values.notna().sum()
        }
    )

question_summary = pd.DataFrame(
    question_summary
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

st.subheader("📋 Complete Student Analysis")

complete_columns = [
"Student Name",
score_column,
"Percentage",
"Improvement",
"Performance"
]

for extra_column in [
"Email address",
"Status",
"Started",
"Completed",
"Duration"
]:
if extra_column in df.columns:
complete_columns.append(extra_column)

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

st.subheader("⬇️ Download Analysis")

download_data = complete_df.to_csv(
index=False
)

st.download_button(
label="📥 Download Complete Analysis",
data=download_data,
file_name="student_improvement_analysis.csv",
mime="text/csv"
)

st.markdown("---")

st.caption(
"Student Improvement Analysis Dashboard"
)
