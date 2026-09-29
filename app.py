import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Student Improvement Analysis",
    page_icon="📈",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("📊 Student Performance Dashboard")
st.header("📈 Student Improvement Analysis")

st.markdown(
    """
    This dashboard analyses student assessment performance,
    identifies improvement, and presents the results using
    tables and charts.
    """
)


# ============================================================
# FILE UPLOAD
# ============================================================

st.sidebar.header("📂 Upload Data")

uploaded_file = st.sidebar.file_uploader(
    "Upload Student CSV File",
    type=["csv"]
)


# ============================================================
# SAMPLE DATA
# ============================================================

def create_sample_data():

    data = {
        "Last name": [
            "Anu", "Binu", "Cathy", "Deepa", "Eva",
            "Fathima", "Gopika", "Hema", "Isha", "Jiya"
        ],

        "First name": [
            "A", "B", "C", "D", "E",
            "F", "G", "H", "I", "J"
        ],

        "Email address": [
            "anu@gmail.com",
            "binu@gmail.com",
            "cathy@gmail.com",
            "deepa@gmail.com",
            "eva@gmail.com",
            "fathima@gmail.com",
            "gopika@gmail.com",
            "hema@gmail.com",
            "isha@gmail.com",
            "jiya@gmail.com"
        ],

        "Grade/15.00": [
            13, 11, 9, 14, 8,
            12, 7, 10, 15, 6
        ]
    }

    return pd.DataFrame(data)


# ============================================================
# READ DATA
# ============================================================

if uploaded_file is not None:

    try:
        df = pd.read_csv(uploaded_file)

        st.success("✅ CSV file uploaded successfully.")

    except Exception as e:

        st.error(f"❌ Error reading CSV file: {e}")
        st.stop()

else:

    df = create_sample_data()

    st.info(
        "ℹ️ No CSV file uploaded. Sample data is being displayed."
    )


# ============================================================
# CLEAN COLUMN NAMES
# ============================================================

df.columns = df.columns.astype(str).str.strip()


# ============================================================
# DISPLAY RAW DATA
# ============================================================

with st.expander("📋 View Uploaded Data"):

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# IDENTIFY SCORE COLUMN
# ============================================================

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


# ============================================================
# IF SCORE COLUMN NOT FOUND
# ============================================================

if score_column is None:

    st.error(
        """
        ❌ Score column not found.

        Your CSV should contain a score column such as:

        - Grade/15.00
        - Grade
        - Score
        - Marks
        - Total
        """
    )

    st.write("Available columns:")

    st.write(list(df.columns))

    st.stop()


# ============================================================
# CONVERT SCORE TO NUMERIC
# ============================================================

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

if "First name" in df.columns and "Last name" in df.columns:

    df["Student Name"] = (
        df["First name"].fillna("").astype(str)
        + " "
        + df["Last name"].fillna("").astype(str)
    ).str.strip()

elif "First name" in df.columns:

    df["Student Name"] = (
        df["First name"].fillna("").astype(str)
    )

elif "Last name" in df.columns:

    df["Student Name"] = (
        df["Last name"].fillna("").astype(str)
    )

else:

    df["Student Name"] = [
        f"Student {i + 1}"
        for i in range(len(df))
    ]


# ============================================================
# BASIC STATISTICS
# ============================================================

max_score = 15

average_score = df[score_column].mean()

highest_score = df[score_column].max()

lowest_score = df[score_column].min()

median_score = df[score_column].median()

std_score = df[score_column].std()

number_students = len(df)


# ============================================================
# IMPROVEMENT CALCULATION
# ============================================================

# Improvement is calculated relative to the class average.

df["Improvement"] = (
    df[score_column] - average_score
)

df["Percentage"] = (
    df[score_column] / max_score
) * 100


# ============================================================
# PERFORMANCE CATEGORY
# ============================================================

def performance_category(score):

    percentage = (score / max_score) * 100

    if percentage >= 80:
        return "Excellent"

    elif percentage >= 60:
        return "Good"

    elif percentage >= 40:
        return "Average"

    else:
        return "Needs Improvement"


df["Performance"] = df[score_column].apply(
    performance_category
)


# ============================================================
# DASHBOARD METRICS
# ============================================================

st.subheader("📌 Overall Performance")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:

    st.metric(
        "👨‍🎓 Students",
        number_students
    )

with col2:

    st.metric(
        "📊 Average",
        f"{average_score:.2f}/{max_score}"
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
        "📈 Median",
        f"{median_score:.2f}"
    )


# ============================================================
# PERFORMANCE SUMMARY
# ============================================================

st.subheader("📊 Performance Summary")

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


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌟 Excellent", excellent)

with col2:
    st.metric("👍 Good", good)

with col3:
    st.metric("📘 Average", average)

with col4:
    st.metric("⚠️ Needs Improvement", needs_improvement)


# ============================================================
# STUDENT SCORE CHART
# ============================================================

st.subheader("📈 Student Score Analysis")

chart_df = df[
    ["Student Name", score_column]
].copy()

chart_df = chart_df.sort_values(
    by=score_column,
    ascending=False
)


fig, ax = plt.subplots(
    figsize=(12, 6)
)

bars = ax.bar(
    chart_df["Student Name"],
    chart_df[score_column]
)

ax.axhline(
    average_score,
    linestyle="--",
    linewidth=2,
    label=f"Class Average = {average_score:.2f}"
)

ax.set_title(
    "Student Scores"
)

ax.set_xlabel(
    "Student"
)

ax.set_ylabel(
    "Score"
)

ax.set_ylim(
    0,
    max_score + 2
)

ax.legend()

plt.xticks(
    rotation=45,
    ha="right"
)

# ------------------------------------------------------------
# DATA LABELS
# ------------------------------------------------------------

for bar in bars:

    height = bar.get_height()

    ax.text(
        bar.get_x() + bar.get_width() / 2,
        height + 0.2,
        f"{height:.1f}",
        ha="center",
        va="bottom",
        fontsize=10
    )

plt.tight_layout()

st.pyplot(fig)


# ============================================================
# IMPROVEMENT CHART
# ============================================================

st.subheader("📈 Student Improvement from Class Average")

improvement_df = df[
    ["Student Name", "Improvement"]
].copy()

improvement_df = improvement_df.sort_values(
    by="Improvement",
    ascending=False
)


fig2, ax2 = plt.subplots(
    figsize=(12, 6)
)

bars2 = ax2.bar(
    improvement_df["Student Name"],
    improvement_df["Improvement"]
)

ax2.axhline(
    0,
    linewidth=1
)

ax2.set_title(
    "Student Improvement Relative to Class Average"
)

ax2.set_xlabel(
    "Student"
)

ax2.set_ylabel(
    "Difference from Class Average"
)

plt.xticks(
    rotation=45,
    ha="right"
)


# ------------------------------------------------------------
# IMPROVEMENT DATA LABELS
# ------------------------------------------------------------

for bar in bars2:

    height = bar.get_height()

    if height >= 0:

        y_position = height + 0.15
        vertical_alignment = "bottom"

    else:

        y_position = height - 0.15
        vertical_alignment = "top"

    ax2.text(
        bar.get_x() + bar.get_width() / 2,
        y_position,
        f"{height:+.2f}",
        ha="center",
        va=vertical_alignment,
        fontsize=9
    )


plt.tight_layout()

st.pyplot(fig2)


# ============================================================
# PERCENTAGE PERFORMANCE
# ============================================================

st.subheader("📊 Student Percentage")

percentage_df = df[
    ["Student Name", "Percentage"]
].copy()

percentage_df = percentage_df.sort_values(
    by="Percentage",
    ascending=False
)


fig3, ax3 = plt.subplots(
    figsize=(12, 6)
)

bars3 = ax3.bar(
    percentage_df["Student Name"],
    percentage_df["Percentage"]
)

ax3.axhline(
    60,
    linestyle="--",
    linewidth=2,
    label="60% Reference"
)

ax3.set_title(
    "Student Percentage"
)

ax3.set_xlabel(
    "Student"
)

ax3.set_ylabel(
    "Percentage (%)"
)

ax3.set_ylim(
    0,
    110
)

ax3.legend()

plt.xticks(
    rotation=45,
    ha="right"
)


for bar in bars3:

    height = bar.get_height()

    ax3.text(
        bar.get_x() + bar.get_width() / 2,
        height + 1,
        f"{height:.1f}%",
        ha="center",
        va="bottom",
        fontsize=9
    )


plt.tight_layout()

st.pyplot(fig3)


# ============================================================
# STUDENT PERFORMANCE TABLE
# ============================================================

st.subheader("📋 Detailed Student Performance")

display_df = df[
    [
        "Student Name",
        score_column,
        "Percentage",
        "Improvement",
        "Performance"
    ]
].copy()


display_df["Percentage"] = (
    display_df["Percentage"].round(2)
)

display_df["Improvement"] = (
    display_df["Improvement"].round(2)
)


display_df = display_df.sort_values(
    by=score_column,
    ascending=False
)


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# TOP PERFORMERS
# ============================================================

st.subheader("🏆 Top Performing Students")

top_n = min(
    5,
    len(df)
)

top_students = df.nlargest(
    top_n,
    score_column
)[
    [
        "Student Name",
        score_column,
        "Percentage"
    ]
].copy()


top_students["Percentage"] = (
    top_students["Percentage"].round(2)
)


st.dataframe(
    top_students,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# STUDENTS REQUIRING IMPROVEMENT
# ============================================================

st.subheader("⚠️ Students Requiring Improvement")

weak_students = df[
    df[score_column] < average_score
].copy()


if len(weak_students) > 0:

    weak_students = weak_students[
        [
            "Student Name",
            score_column,
            "Percentage",
            "Improvement"
        ]
    ]

    weak_students["Percentage"] = (
        weak_students["Percentage"].round(2)
    )

    weak_students["Improvement"] = (
        weak_students["Improvement"].round(2)
    )

    weak_students = weak_students.sort_values(
        by=score_column
    )

    st.dataframe(
        weak_students,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "🎉 All students are at or above the class average!"
    )


# ============================================================
# SCORE DISTRIBUTION
# ============================================================

st.subheader("📊 Score Distribution")

fig4, ax4 = plt.subplots(
    figsize=(10, 5)
)

ax4.hist(
    df[score_column],
    bins=8,
    edgecolor="black"
)

ax4.axvline(
    average_score,
    linestyle="--",
    linewidth=2,
    label=f"Mean = {average_score:.2f}"
)

ax4.set_title(
    "Distribution of Student Scores"
)

ax4.set_xlabel(
    "Score"
)

ax4.set_ylabel(
    "Number of Students"
)

ax4.legend()

plt.tight_layout()

st.pyplot(fig4)


# ============================================================
# DOWNLOAD ANALYSIS
# ============================================================

st.subheader("⬇️ Download Analysis")

download_df = df[
    [
        "Student Name",
        score_column,
        "Percentage",
        "Improvement",
        "Performance"
    ]
].copy()


csv_data = download_df.to_csv(
    index=False
)


st.download_button(
    label="📥 Download Student Analysis CSV",
    data=csv_data,
    file_name="student_improvement_analysis.csv",
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "📊 Student Improvement Analysis Dashboard"
)
