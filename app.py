import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="📊",
    layout="wide"
)


# ============================================================
# TITLE
# ============================================================

st.title("📊 Student Performance Dashboard")
st.header("📈 Student Improvement & Assessment Analysis")

st.write(
    "Upload the assessment CSV file to analyse student performance, "
    "scores, improvement, duration, question-wise performance and outliers."
)


# ============================================================
# SIDEBAR
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
    df_original.columns
    .astype(str)
    .str.strip()
)


st.success("✅ CSV uploaded successfully.")


# ============================================================
# ORIGINAL DATA
# ============================================================

st.subheader("📋 Complete Uploaded CSV Data")

st.caption(
    f"Original dataset: {len(df_original)} rows × "
    f"{len(df_original.columns)} columns"
)

st.dataframe(
    df_original,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# SCORE COLUMN
# ============================================================

possible_score_columns = [
    "Grade/15.00",
    "Grade",
    "Score",
    "Marks",
    "Total",
    "Final Score"
]


numeric_columns = df_original.select_dtypes(
    include="number"
).columns.tolist()


score_column = next(
    (
        column
        for column in possible_score_columns
        if column in df_original.columns
    ),
    numeric_columns[0] if numeric_columns else None
)


if score_column is None:

    st.error("❌ No score column was found.")

    st.write(
        "Available columns:",
        list(df_original.columns)
    )

    st.stop()


# ============================================================
# WORKING COPY
# ============================================================

df = df_original.copy()


df[score_column] = pd.to_numeric(
    df[score_column],
    errors="coerce"
)


# Remove rows where score is missing
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
# OUTLIER DETECTION USING IQR
# ============================================================

Q1 = df[score_column].quantile(0.25)

Q3 = df[score_column].quantile(0.75)

IQR = Q3 - Q1

lower_bound = Q1 - 1.5 * IQR

upper_bound = Q3 + 1.5 * IQR


df["Outlier"] = (
    (df[score_column] < lower_bound)
    |
    (df[score_column] > upper_bound)
)


outliers = df[
    df["Outlier"]
].copy()


clean_df = df[
    ~df["Outlier"]
].copy()


# ============================================================
# OUTLIER SUMMARY
# ============================================================

st.subheader("🚨 Outlier Detection")

o1, o2, o3, o4 = st.columns(4)

o1.metric(
    "Q1",
    f"{Q1:.2f}"
)

o2.metric(
    "Q3",
    f"{Q3:.2f}"
)

o3.metric(
    "IQR",
    f"{IQR:.2f}"
)

o4.metric(
    "Outliers Removed",
    len(outliers)
)


st.info(
    f"IQR lower limit = {lower_bound:.2f} | "
    f"IQR upper limit = {upper_bound:.2f}"
)


if len(outliers) > 0:

    st.warning(
        f"⚠️ {len(outliers)} observation(s) were identified "
        f"as score outliers."
    )

    st.dataframe(
        outliers,
        use_container_width=True,
        hide_index=True
    )

else:

    st.success(
        "✅ No score outliers were detected using the IQR method."
    )


# ============================================================
# USE CLEAN DATA FOR ANALYSIS
# ============================================================

df = clean_df.copy()


# ============================================================
# BASIC STATISTICS
# ============================================================

max_score = 15.0

student_count = len(df)

average_score = df[score_column].mean()

highest_score = df[score_column].max()

lowest_score = df[score_column].min()

median_score = df[score_column].median()

std_score = df[score_column].std()

cv = (
    std_score / average_score * 100
    if average_score != 0
    else np.nan
)


# ============================================================
# PERCENTAGE
# ============================================================

df["Percentage"] = (
    df[score_column] / max_score
) * 100


df["Percentage"] = df["Percentage"].clip(
    0,
    100
)


# ============================================================
# IMPROVEMENT
# ============================================================

df["Improvement"] = (
    df[score_column] - average_score
)


# ============================================================
# PERFORMANCE CATEGORY
# ============================================================

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


# ============================================================
# IMPROVEMENT STATUS
# ============================================================

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


# ============================================================
# MAIN METRICS
# ============================================================

st.subheader("📌 Overall Performance After Outlier Removal")

col1, col2, col3, col4, col5, col6 = st.columns(6)

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

col6.metric(
    "📐 CV",
    f"{cv:.2f}%"
)


# ============================================================
# PERFORMANCE COUNTS
# ============================================================

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


# ============================================================
# 1. STUDENT SCORE COMPARISON
# ============================================================

st.subheader("📈 Student Score Comparison")

score_chart = (
    df[
        ["Student Name", score_column]
    ]
    .sort_values(
        score_column,
        ascending=False
    )
)


fig_score = px.bar(
    score_chart,
    x="Student Name",
    y=score_column,
    title="Student Score Comparison",
    labels={
        "Student Name": "Student",
        score_column: "Score"
    },
    text=score_column
)


fig_score.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Score: %{y:.2f}/15"
        "<extra></extra>"
    )
)


fig_score.update_layout(
    xaxis_title="Student",
    yaxis_title="Score",
    xaxis_tickangle=-45,
    height=600,
    showlegend=False
)


fig_score.update_yaxes(
    range=[
        0,
        max(15, highest_score + 1)
    ]
)


st.plotly_chart(
    fig_score,
    use_container_width=True
)


# ============================================================
# 2. PERCENTAGE CHART
# ============================================================

st.subheader("📊 Student Percentage")

percentage_chart = (
    df[
        ["Student Name", "Percentage"]
    ]
    .sort_values(
        "Percentage",
        ascending=False
    )
)


fig_percentage = px.bar(
    percentage_chart,
    x="Student Name",
    y="Percentage",
    title="Student Percentage Comparison",
    labels={
        "Student Name": "Student",
        "Percentage": "Percentage (%)"
    },
    text="Percentage"
)


fig_percentage.update_traces(
    texttemplate="%{text:.1f}%",
    textposition="outside",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Percentage: %{y:.2f}%"
        "<extra></extra>"
    )
)


fig_percentage.update_layout(
    xaxis_title="Student",
    yaxis_title="Percentage (%)",
    xaxis_tickangle=-45,
    height=600,
    showlegend=False
)


fig_percentage.update_yaxes(
    range=[0, 105]
)


st.plotly_chart(
    fig_percentage,
    use_container_width=True
)


# ============================================================
# 3. IMPROVEMENT CHART
# ============================================================

st.subheader(
    "📈 Improvement Relative to Class Average"
)


improvement_chart = (
    df[
        ["Student Name", "Improvement"]
    ]
    .sort_values(
        "Improvement",
        ascending=False
    )
)


fig_improvement = px.bar(
    improvement_chart,
    x="Student Name",
    y="Improvement",
    title="Student Improvement Relative to Class Average",
    labels={
        "Student Name": "Student",
        "Improvement": "Difference from Class Average"
    },
    text="Improvement"
)


fig_improvement.update_traces(
    texttemplate="%{text:.2f}",
    textposition="outside",
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Difference: %{y:.2f}<br>"
        "<extra></extra>"
    )
)


fig_improvement.add_hline(
    y=0,
    line_width=2,
    line_dash="dash"
)


fig_improvement.update_layout(
    xaxis_title="Student",
    yaxis_title="Score Difference from Class Average",
    xaxis_tickangle=-45,
    height=600,
    showlegend=False
)


st.plotly_chart(
    fig_improvement,
    use_container_width=True
)


# ============================================================
# 4. SCORE DISTRIBUTION
# ============================================================

st.subheader("📊 Score Distribution")


fig_distribution = px.histogram(
    df,
    x=score_column,
    nbins=10,
    title="Distribution of Student Scores",
    labels={
        score_column: "Score",
        "count": "Number of Students"
    },
    text_auto=True
)


fig_distribution.update_layout(
    xaxis_title="Score",
    yaxis_title="Number of Students",
    height=500,
    showlegend=False
)


st.plotly_chart(
    fig_distribution,
    use_container_width=True
)


# ============================================================
# 5. BOX PLOT
# ============================================================

st.subheader("📦 Score Box Plot")


fig_box = px.box(
    df,
    y=score_column,
    points="all",
    title="Score Distribution and Remaining Observations",
    labels={
        score_column: "Score"
    }
)


fig_box.update_layout(
    yaxis_title="Score",
    height=500,
    showlegend=False
)


st.plotly_chart(
    fig_box,
    use_container_width=True
)


# ============================================================
# 6. TOP STUDENTS
# ============================================================

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


# ============================================================
# 7. BELOW AVERAGE STUDENTS
# ============================================================

st.subheader(
    "⚠️ Students Below Class Average"
)


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


# ============================================================
# 8. DURATION ANALYSIS
# ============================================================

if "Duration" in df.columns:

    st.subheader("⏱️ Assessment Duration")

    duration_df = df[
        [
            "Student Name",
            "Duration"
        ]
    ].copy()

    st.dataframe(
        duration_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# 9. SCORE VS DURATION
# ============================================================

if "Duration" in df.columns:

    duration_numeric = pd.to_numeric(
        df["Duration"],
        errors="coerce"
    )

    if duration_numeric.notna().sum() > 1:

        chart_duration = df.copy()

        chart_duration["Duration Numeric"] = (
            duration_numeric
        )

        chart_duration = chart_duration.dropna(
            subset=["Duration Numeric"]
        )

        st.subheader(
            "⏱️ Score vs Assessment Duration"
        )

        fig_duration = px.scatter(
            chart_duration,
            x="Duration Numeric",
            y=score_column,
            hover_name="Student Name",
            title="Relationship Between Assessment Duration and Score",
            labels={
                "Duration Numeric": "Assessment Duration",
                score_column: "Score"
            },
            text="Student Name"
        )

        fig_duration.update_traces(
            marker=dict(size=12),
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Duration: %{x}<br>"
                "Score: %{y:.2f}<br>"
                "<extra></extra>"
            )
        )

        fig_duration.update_layout(
            xaxis_title="Assessment Duration",
            yaxis_title="Score",
            height=600
        )

        st.plotly_chart(
            fig_duration,
            use_container_width=True
        )


# ============================================================
# 10. STATUS ANALYSIS
# ============================================================

if "Status" in df.columns:

    st.subheader("📌 Student Status")

    status_counts = (
        df["Status"]
        .fillna("Unknown")
        .astype(str)
        .value_counts()
        .reset_index()
    )

    status_counts.columns = [
        "Status",
        "Students"
    ]

    fig_status = px.bar(
        status_counts,
        x="Status",
        y="Students",
        title="Student Status Distribution",
        labels={
            "Status": "Student Status",
            "Students": "Number of Students"
        },
        text="Students"
    )

    fig_status.update_traces(
        textposition="outside"
    )

    fig_status.update_layout(
        xaxis_title="Student Status",
        yaxis_title="Number of Students",
        height=500,
        showlegend=False
    )

    st.plotly_chart(
        fig_status,
        use_container_width=True
    )


# ============================================================
# 11. QUESTION-WISE ANALYSIS
# ============================================================

question_columns = [
    column
    for column in df.columns
    if str(column).upper().startswith("Q")
]


if question_columns:

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
                "Attempted": values.notna().sum(),
                "Not Attempted": values.isna().sum()
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


    # Question average chart

    fig_question = px.bar(
        question_summary,
        x="Question",
        y="Average",
        title="Average Performance by Question",
        labels={
            "Question": "Question",
            "Average": "Average Score"
        },
        text="Average"
    )


    fig_question.update_traces(
        texttemplate="%{text:.2f}",
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Average: %{y:.2f}<br>"
            "<extra></extra>"
        )
    )


    fig_question.update_layout(
        xaxis_title="Question",
        yaxis_title="Average Score",
        height=500,
        showlegend=False
    )


    st.plotly_chart(
        fig_question,
        use_container_width=True
    )


    # Attempted vs not attempted

    question_attempt = question_summary.melt(
        id_vars="Question",
        value_vars=[
            "Attempted",
            "Not Attempted"
        ],
        var_name="Attempt Status",
        value_name="Students"
    )


    fig_attempt = px.bar(
        question_attempt,
        x="Question",
        y="Students",
        color="Attempt Status",
        barmode="group",
        title="Question-wise Attempt Status",
        labels={
            "Question": "Question",
            "Students": "Number of Students",
            "Attempt Status": "Attempt Status"
        },
        text="Students"
    )


    fig_attempt.update_traces(
        textposition="outside"
    )


    fig_attempt.update_layout(
        xaxis_title="Question",
        yaxis_title="Number of Students",
        height=550
    )


    st.plotly_chart(
        fig_attempt,
        use_container_width=True
    )


# ============================================================
# 12. COMPLETE STUDENT ANALYSIS
# ============================================================

st.subheader("📋 Complete Student Analysis")


complete_columns = [
    column
    for column in df_original.columns
    if column in df.columns
]


# Add calculated columns

calculated_columns = [
    "Student Name",
    "Percentage",
    "Improvement",
    "Performance",
    "Improvement Status",
    "Outlier"
]


for column in calculated_columns:

    if column in df.columns and column not in complete_columns:

        complete_columns.append(column)


complete_df = df[
    complete_columns
].copy()


if "Percentage" in complete_df.columns:

    complete_df["Percentage"] = (
        complete_df["Percentage"]
        .round(2)
    )


if "Improvement" in complete_df.columns:

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


# ============================================================
# 13. ORIGINAL DATA vs CLEANED DATA
# ============================================================

st.subheader("🔍 Original vs Cleaned Dataset")


comparison_col1, comparison_col2 = st.columns(2)


with comparison_col1:

    st.metric(
        "Original Rows",
        len(df_original)
    )


with comparison_col2:

    st.metric(
        "Rows After Outlier Removal",
        len(df)
    )


st.caption(
    f"Rows removed as outliers: "
    f"{len(df_original) - len(df)}"
)


# ============================================================
# 14. DOWNLOAD CLEANED DATA
# ============================================================

st.subheader("⬇️ Download Analysis")


cleaned_csv = complete_df.to_csv(
    index=False
)


st.download_button(
    label="📥 Download Cleaned Analysis CSV",
    data=cleaned_csv,
    file_name="cleaned_student_analysis.csv",
    mime="text/csv"
)


# ============================================================
# DOWNLOAD OUTLIERS
# ============================================================

if len(outliers) > 0:

    outlier_csv = outliers.to_csv(
        index=False
    )

    st.download_button(
        label="📥 Download Removed Outliers",
        data=outlier_csv,
        file_name="removed_outliers.csv",
        mime="text/csv"
    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "📊 Student Performance & Improvement Analysis Dashboard"
)
