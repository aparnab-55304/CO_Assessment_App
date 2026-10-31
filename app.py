import re
import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# ============================================================
# PAGE CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="Quiz Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Quiz Performance Dashboard")
st.caption(
    "A clear summary of student scores, improvement, time usage, "
    "team performance and question-wise results."
)

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def find_column(df, possible_names):
    """Return the first matching column, ignoring case and spaces."""
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for name in possible_names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None


def parse_duration(value):
    """Convert values such as '17 mins 25 secs' to minutes."""
    if pd.isna(value):
        return np.nan

    # Numeric durations are assumed to be seconds.
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value) / 60

    text = str(value).strip().lower()
    if not text or text in {"-", "nan", "none"}:
        return np.nan

    hours = re.search(r"(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|h)\b", text)
    minutes = re.search(r"(\d+(?:\.\d+)?)\s*(?:minutes?|mins?|m)\b", text)
    seconds = re.search(r"(\d+(?:\.\d+)?)\s*(?:seconds?|secs?|s)\b", text)

    # Handle a plain number as minutes.
    if not hours and not minutes and not seconds:
        try:
            return float(text)
        except ValueError:
            return np.nan

    total = 0.0
    if hours:
        total += float(hours.group(1)) * 60
    if minutes:
        total += float(minutes.group(1))
    if seconds:
        total += float(seconds.group(1)) / 60
    return total


def format_minutes(value):
    if pd.isna(value):
        return "N/A"
    total_seconds = int(round(abs(float(value)) * 60))
    mins, secs = divmod(total_seconds, 60)
    sign = "-" if float(value) < 0 else ""
    return f"{sign}{mins} min {secs:02d} sec"


def format_score(value):
    return "N/A" if pd.isna(value) else f"{value:.2f}/15"


def prepare_data(raw):
    """Clean the uploaded Moodle-style quiz export."""
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    first_col = find_column(df, ["First name", "First Name"])
    last_col = find_column(df, ["Last name", "Last Name"])
    email_col = find_column(df, ["Email address", "Email"])
    status_col = find_column(df, ["Status"])
    started_col = find_column(df, ["Started", "Start time"])
    completed_col = find_column(df, ["Completed", "Completion time"])
    duration_col = find_column(df, ["Duration", "Time taken"])
    grade_col = find_column(df, ["Grade/15.00", "Grade/15", "Grade"])

    if first_col is None:
        raise ValueError("The dataset must contain a 'First name' column.")
    if grade_col is None:
        raise ValueError("Could not find the quiz grade column (for example, Grade/15.00).")

    # Remove Moodle's overall-average/footer row and blank rows.
    df = df[df[first_col].notna()].copy()
    df = df[~df[first_col].astype(str).str.strip().str.lower().isin(
        ["overall average", "overallaverage", "average"]
    )].copy()

    # Keep submitted/completed attempts only when a status column exists.
    if status_col is not None:
        status = df[status_col].astype(str).str.strip().str.lower()
        finished = status.str.contains(r"finish|complete|submit", regex=True, na=False)
        df = df[finished].copy()

    # Construct readable student names. The new file uses values such as
    # "MeeraKrishnan" in First name and "Dummy@2026" in Last name.
    first_values = df[first_col].fillna("").astype(str).str.strip()
    if last_col is not None:
        last_values = df[last_col].fillna("").astype(str).str.strip()
        use_last = (
            last_values.ne("")
            & ~last_values.str.lower().str.startswith("dummy")
            & ~last_values.str.lower().isin(["nan", "none"])
        )
        df["Student"] = np.where(
            use_last,
            first_values + " " + last_values,
            first_values
        )
    else:
        df["Student"] = first_values

    df["Student"] = df["Student"].str.replace(r"\s+", " ", regex=True).str.strip()

    # Stable identifier: email if available, otherwise student name.
    if email_col is not None:
        df["_student_id"] = df[email_col].fillna(df["Student"]).astype(str).str.strip().str.lower()
    else:
        df["_student_id"] = df["Student"].str.lower()

    df["Score"] = pd.to_numeric(
        df[grade_col].astype(str).str.replace(",", "", regex=False),
        errors="coerce"
    )

    # Identify question columns in formats such as Q1, Q. 1 /1.00.
    question_map = {}
    for col in df.columns:
        match = re.search(r"q\.?\s*(\d+)", str(col), flags=re.IGNORECASE)
        if match:
            question_map[col] = f"Q{int(match.group(1))}"

    question_cols = list(question_map.keys())
    for old_col, new_col in question_map.items():
        df[new_col] = pd.to_numeric(
            df[old_col].astype(str).str.replace(",", "", regex=False),
            errors="coerce"
        )

    question_cols_clean = [question_map[c] for c in question_cols]
    question_cols_clean = sorted(
        set(question_cols_clean),
        key=lambda x: int(re.search(r"\d+", x).group())
    )

    # Parse dates and durations.
    df["Started_dt"] = pd.to_datetime(
        df[started_col], errors="coerce", dayfirst=True
    ) if started_col is not None else pd.NaT

    df["Completed_dt"] = pd.to_datetime(
        df[completed_col], errors="coerce", dayfirst=True
    ) if completed_col is not None else pd.NaT

    df["Time_min"] = df[duration_col].apply(parse_duration) if duration_col is not None else np.nan

    # If duration is absent, calculate it from start and completion timestamps.
    if duration_col is None and started_col is not None and completed_col is not None:
        df["Time_min"] = (
            (df["Completed_dt"] - df["Started_dt"]).dt.total_seconds() / 60
        )

    df = df[df["Score"].notna()].copy()
    df = df[df["Student"].ne("")].copy()
    df = df.sort_values(
        ["_student_id", "Started_dt"],
        na_position="last"
    ).reset_index(drop=True)

    df["Attempt"] = df.groupby("_student_id").cumcount() + 1
    df["Attempt_Label"] = "Attempt " + df["Attempt"].astype(str)

    # Keep scores within the quiz's possible range.
    df["Score"] = df["Score"].clip(lower=0, upper=15)
    return df, question_cols_clean


def build_student_summary(data):
    summary = data.groupby(["_student_id", "Student"], as_index=False).agg(
        Attempts=("Score", "count"),
        Average_Score=("Score", "mean"),
        Best_Score=("Score", "max"),
        Latest_Score=("Score", "last"),
        First_Score=("Score", "first"),
        Average_Time=("Time_min", "mean"),
        Total_Time=("Time_min", "sum"),
        Score_SD=("Score", "std")
    )
    summary["Improvement"] = summary["Latest_Score"] - summary["First_Score"]
    summary["Improvement_Pct"] = np.where(
        summary["First_Score"] > 0,
        summary["Improvement"] / summary["First_Score"] * 100,
        np.nan
    )
    summary["Score_SD"] = summary["Score_SD"].fillna(0)
    return summary.sort_values("Average_Score", ascending=False)


def safe_mean(series):
    return float(series.mean()) if series.notna().any() else np.nan


# ============================================================
# DATA UPLOAD
# ============================================================
with st.sidebar:
    st.header("📁 Dataset")
    uploaded_file = st.file_uploader(
        "Upload your quiz results",
        type=["csv", "xlsx", "xls"],
        help="Upload the latest quiz export. The dashboard updates automatically."
    )

    st.divider()
    st.header("⚙️ Display settings")
    show_raw_data = st.checkbox("Show cleaned data preview", value=False)

if uploaded_file is not None:
    try:
        if uploaded_file.name.lower().endswith(".csv"):
            raw_data = pd.read_csv(uploaded_file)
        else:
            raw_data = pd.read_excel(uploaded_file)
    except Exception as e:
        st.error(f"Could not read the uploaded file: {e}")
        st.stop()
else:
    st.info("Upload **Quiz_Results_Dummy.csv** (or your latest quiz export) from the sidebar to begin.")
    st.stop()

try:
    data, question_cols = prepare_data(raw_data)
except Exception as e:
    st.error(str(e))
    st.stop()

if data.empty:
    st.warning("No completed attempts with valid scores were found in this dataset.")
    st.stop()

students = sorted(data["Student"].dropna().unique().tolist())
student_summary = build_student_summary(data)

# ============================================================
# TEAM CONFIGURATION
# ============================================================
with st.sidebar:
    st.divider()
    st.header("👥 Team configuration")
    st.caption(
        "This dataset has no Team column. Assign students here. "
        "The team comparison will use these selections."
    )

    team1_name = st.text_input("Team 1 name", value="Team 1")
    team2_name = st.text_input("Team 2 name", value="Team 2")

    team1_members = st.multiselect(
        f"Students in {team1_name or 'Team 1'}",
        options=students,
        default=[]
    )
    remaining_students = [s for s in students if s not in team1_members]
    team2_members = st.multiselect(
        f"Students in {team2_name or 'Team 2'}",
        options=remaining_students,
        default=[]
    )

    unassigned = [
        s for s in students
        if s not in team1_members and s not in team2_members
    ]

team1_name = team1_name.strip() or "Team 1"
team2_name = team2_name.strip() or "Team 2"

team_lookup = {s: team1_name for s in team1_members}
team_lookup.update({s: team2_name for s in team2_members})
data["Team"] = data["Student"].map(team_lookup).fillna("Unassigned")
student_summary["Team"] = student_summary["Student"].map(team_lookup).fillna("Unassigned")

# Add a student filter to the sidebar.
with st.sidebar:
    st.divider()
    selected_students = st.multiselect(
        "Filter students",
        options=students,
        default=students
    )

filtered = data[data["Student"].isin(selected_students)].copy()
filtered_summary = build_student_summary(filtered) if not filtered.empty else student_summary.iloc[0:0].copy()

# Reattach team labels after rebuilding the filtered student summary.
# build_student_summary() calculates performance measures but does not
# create the Team column itself.
if not filtered_summary.empty:
    filtered_summary["Team"] = (
        filtered_summary["Student"].map(team_lookup).fillna("Unassigned")
    )
else:
    filtered_summary["Team"] = pd.Series(dtype="object")

if filtered.empty:
    st.warning("Select at least one student from the sidebar.")
    st.stop()

# ============================================================
# OVERVIEW METRICS
# ============================================================
total_students = filtered["Student"].nunique()
total_attempts = len(filtered)
class_average = filtered["Score"].mean()
average_improvement = filtered_summary["Improvement"].mean() if not filtered_summary.empty else np.nan
average_time = filtered["Time_min"].mean()
perfect_attempts = int((filtered["Score"] == 15).sum())

st.subheader("Class at a glance")
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Students", f"{total_students}")
k2.metric("Completed attempts", f"{total_attempts}")
k3.metric("Average score", f"{class_average:.2f}/15")
k4.metric(
    "Average improvement",
    f"{average_improvement:+.2f}" if pd.notna(average_improvement) else "N/A"
)
k5.metric(
    "Average time",
    format_minutes(average_time)
)

top_student = (
    filtered_summary.sort_values("Average_Score", ascending=False).iloc[0]
    if not filtered_summary.empty else None
)
most_improved = (
    filtered_summary.sort_values("Improvement", ascending=False).iloc[0]
    if not filtered_summary.empty else None
)

with st.expander("Important findings", expanded=True):
    c1, c2, c3 = st.columns(3)
    if top_student is not None:
        c1.metric(
            "Highest average score",
            top_student["Student"],
            f'{top_student["Average_Score"]:.2f}/15'
        )
    if most_improved is not None:
        c2.metric(
            "Highest first-to-last improvement",
            most_improved["Student"],
            f'{most_improved["Improvement"]:+.2f} marks'
        )
    c3.metric("Perfect-score attempts", perfect_attempts)

# ============================================================
# TABS
# ============================================================
tabs = st.tabs([
    "Overview",
    "Student Performance",
    "Improvement",
    "First 20% vs Last 20%",
    "Time and Efficiency",
    "Attempts and Activity",
    "Team Comparison",
    "Question Analysis",
    "Data and Downloads"
])

# ------------------------------------------------------------
# TAB 1: OVERVIEW
# ------------------------------------------------------------
with tabs[0]:
    st.subheader("Score distribution")
    left, right = st.columns(2)

    with left:
        fig = px.histogram(
            filtered,
            x="Score",
            nbins=15,
            title="Distribution of all attempt scores",
            labels={"Score": "Score out of 15", "count": "Number of attempts"}
        )
        fig.update_layout(bargap=0.12)
        st.plotly_chart(fig, use_container_width=True)

    with right:
        bands = pd.cut(
            filtered["Score"],
            bins=[-0.01, 5, 10, 12, 15],
            labels=["0–5", "Above 5–10", "Above 10–12", "Above 12–15"]
        )
        band_counts = bands.value_counts().reindex(
            ["0–5", "Above 5–10", "Above 10–12", "Above 12–15"],
            fill_value=0
        ).reset_index()
        band_counts.columns = ["Score range", "Attempts"]
        fig = px.bar(
            band_counts,
            x="Score range",
            y="Attempts",
            title="Performance bands",
            text="Attempts"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Average score by student")
    avg_plot = filtered_summary.sort_values("Average_Score", ascending=True)
    fig = px.bar(
        avg_plot,
        x="Average_Score",
        y="Student",
        orientation="h",
        text=avg_plot["Average_Score"].round(2),
        labels={"Average_Score": "Average score out of 15"}
    )
    fig.update_xaxes(range=[0, 15])
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------
# TAB 2: STUDENT PERFORMANCE
# ------------------------------------------------------------
with tabs[1]:
    st.subheader("Student-wise performance")
    display = filtered_summary.copy()
    display = display.rename(columns={
        "Attempts": "Attempts",
        "Average_Score": "Average score",
        "Best_Score": "Best score",
        "Latest_Score": "Latest score",
        "First_Score": "First score",
        "Improvement": "Improvement",
        "Average_Time": "Average time (min)",
        "Score_SD": "Score SD",
        "Team": "Team"
    })
    columns_to_show = [
        "Student", "Team", "Attempts", "Average score", "Best score",
        "First score", "Latest score", "Improvement",
        "Average time (min)", "Score SD"
    ]
    st.dataframe(
        display[columns_to_show].round(2),
        use_container_width=True,
        hide_index=True
    )

    chosen_student = st.selectbox(
        "Select a student for detailed analysis",
        options=students
    )
    one = filtered[filtered["Student"] == chosen_student].sort_values(
        ["Started_dt", "Attempt"], na_position="last"
    )
    if not one.empty:
        a, b, c = st.columns(3)
        a.metric("Attempts", len(one))
        a.metric("Average score", f'{one["Score"].mean():.2f}/15')
        a.metric("Best score", f'{one["Score"].max():.2f}/15')

        fig = px.line(
            one,
            x="Attempt",
            y="Score",
            markers=True,
            title=f"Score progression: {chosen_student}",
            labels={"Score": "Score out of 15", "Attempt": "Attempt number"}
        )
        fig.update_yaxes(range=[0, 15])
        st.plotly_chart(fig, use_container_width=True)

        detail_cols = ["Attempt", "Started_dt", "Score", "Time_min"]
        st.dataframe(
            one[detail_cols].rename(columns={
                "Started_dt": "Started",
                "Time_min": "Time (minutes)"
            }).round(2),
            use_container_width=True,
            hide_index=True
        )

# ------------------------------------------------------------
# TAB 3: IMPROVEMENT
# ------------------------------------------------------------
with tabs[2]:
    st.subheader("Improvement from first attempt to latest attempt")
    imp = filtered_summary.sort_values("Improvement", ascending=False)
    fig = px.bar(
        imp,
        x="Student",
        y="Improvement",
        color="Improvement",
        title="First-to-latest score change",
        labels={"Improvement": "Change in marks"}
    )
    fig.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        imp[[
            "Student", "Attempts", "First_Score", "Latest_Score",
            "Improvement", "Improvement_Pct"
        ]].rename(columns={
            "First_Score": "First score",
            "Latest_Score": "Latest score",
            "Improvement": "Improvement (marks)",
            "Improvement_Pct": "Improvement (%)"
        }).round(2),
        use_container_width=True,
        hide_index=True
    )

    improved = int((filtered_summary["Improvement"] > 0).sum())
    unchanged = int((filtered_summary["Improvement"] == 0).sum())
    declined = int((filtered_summary["Improvement"] < 0).sum())
    x1, x2, x3 = st.columns(3)
    x1.metric("Students improved", improved)
    x2.metric("No change", unchanged)
    x3.metric("Students declined", declined)

# ------------------------------------------------------------
# TAB 4: FIRST 20% VS LAST 20%
# ------------------------------------------------------------
with tabs[3]:
    st.subheader("Compare the first 20% and last 20% of attempts")
    st.caption(
        "For each student, attempts are ordered by the Started timestamp. "
        "At least one attempt is included in each group."
    )

    comparison_rows = []
    for sid, group in filtered.sort_values(
        ["_student_id", "Started_dt"], na_position="last"
    ).groupby("_student_id"):
        group = group.sort_values("Started_dt", na_position="last")
        n = len(group)
        count = max(1, int(np.ceil(n * 0.20)))
        first_group = group.head(count)
        last_group = group.tail(count)

        first_score = first_group["Score"].mean()
        last_score = last_group["Score"].mean()
        first_time = first_group["Time_min"].mean()
        last_time = last_group["Time_min"].mean()

        comparison_rows.append({
            "Student": group["Student"].iloc[0],
            "Attempts": n,
            "First 20% average score": first_score,
            "Last 20% average score": last_score,
            "Score change": last_score - first_score,
            "First 20% average time": first_time,
            "Last 20% average time": last_time,
            "Time saved (minutes)": first_time - last_time
        })

    comparison = pd.DataFrame(comparison_rows)
    comparison = comparison.sort_values("Score change", ascending=False)

    m1, m2 = st.columns(2)
    m1.metric(
        "Average score change",
        f'{comparison["Score change"].mean():+.2f} marks'
    )
    m2.metric(
        "Average time saved",
        format_minutes(comparison["Time saved (minutes)"].mean())
    )

    fig = px.bar(
        comparison,
        x="Student",
        y=["First 20% average score", "Last 20% average score"],
        barmode="group",
        title="Score comparison: first 20% vs last 20%"
    )
    st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        comparison,
        x="Student",
        y="Score change",
        title="Change in average score",
        color="Score change"
    )
    fig.add_hline(y=0, line_dash="dash")
    st.plotly_chart(fig, use_container_width=True)

    time_display = comparison.copy()
    time_display["First 20% average time"] = time_display["First 20% average time"].apply(format_minutes)
    time_display["Last 20% average time"] = time_display["Last 20% average time"].apply(format_minutes)
    time_display["Time saved"] = time_display["Time saved (minutes)"].apply(format_minutes)
    st.dataframe(
        time_display[[
            "Student", "Attempts", "First 20% average score",
            "Last 20% average score", "Score change",
            "First 20% average time", "Last 20% average time", "Time saved"
        ]].round(2),
        use_container_width=True,
        hide_index=True
    )

# ------------------------------------------------------------
# TAB 5: TIME AND EFFICIENCY
# ------------------------------------------------------------
with tabs[4]:
    st.subheader("Time usage and score efficiency")
    timed = filtered.dropna(subset=["Time_min"]).copy()

    if timed.empty:
        st.info("No usable duration values were found in the uploaded data.")
    else:
        t1, t2, t3 = st.columns(3)
        t1.metric("Average completion time", format_minutes(timed["Time_min"].mean()))
        t2.metric("Fastest attempt", format_minutes(timed["Time_min"].min()))
        t3.metric("Longest attempt", format_minutes(timed["Time_min"].max()))

        fig = px.scatter(
            timed,
            x="Time_min",
            y="Score",
            color="Student",
            hover_data=["Attempt"],
            title="Relationship between time taken and score",
            labels={"Time_min": "Time taken (minutes)", "Score": "Score out of 15"}
        )
        fig.update_yaxes(range=[0, 15])
        st.plotly_chart(fig, use_container_width=True)

        student_time = timed.groupby("Student", as_index=False).agg(
            Average_Time=("Time_min", "mean"),
            Average_Score=("Score", "mean")
        )
        fig = px.bar(
            student_time.sort_values("Average_Time"),
            x="Student",
            y="Average_Time",
            title="Average time taken by student",
            labels={"Average_Time": "Average time (minutes)"}
        )
        st.plotly_chart(fig, use_container_width=True)

        timed["Score_per_Minute"] = np.where(
            timed["Time_min"] > 0,
            timed["Score"] / timed["Time_min"],
            np.nan
        )
        efficiency = timed.groupby("Student", as_index=False)["Score_per_Minute"].mean()
        efficiency = efficiency.sort_values("Score_per_Minute", ascending=False)
        st.markdown("**Average score per minute**")
        st.dataframe(efficiency.round(3), use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# TAB 6: ATTEMPTS AND ACTIVITY
# ------------------------------------------------------------
with tabs[5]:
    st.subheader("Attempt activity")
    attempt_counts = filtered.groupby("Student", as_index=False).agg(
        Attempts=("Score", "count"),
        Average_Score=("Score", "mean")
    ).sort_values("Attempts", ascending=False)

    fig = px.bar(
        attempt_counts,
        x="Student",
        y="Attempts",
        color="Attempts",
        title="Number of completed attempts per student"
    )
    st.plotly_chart(fig, use_container_width=True)

    if filtered["Started_dt"].notna().any():
        daily = (
            filtered.dropna(subset=["Started_dt"])
            .assign(Date=lambda x: x["Started_dt"].dt.date)
            .groupby("Date")
            .size()
            .reset_index(name="Attempts")
        )
        fig = px.line(
            daily,
            x="Date",
            y="Attempts",
            markers=True,
            title="Attempts over time"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(attempt_counts, use_container_width=True, hide_index=True)

# ------------------------------------------------------------
# TAB 7: TEAM COMPARISON
# ------------------------------------------------------------
with tabs[6]:
    st.subheader("Team comparison")
    assigned_data = filtered[filtered["Team"].ne("Unassigned")].copy()

    if assigned_data.empty:
        st.info(
            "No team members have been assigned yet. Use the Team configuration "
            "section in the sidebar to create teams and assign students."
        )
    else:
        team_summary = assigned_data.groupby("Team", as_index=False).agg(
            Students=("Student", "nunique"),
            Attempts=("Score", "count"),
            Average_Score=("Score", "mean"),
            Best_Score=("Score", "max"),
            Average_Time=("Time_min", "mean")
        )

        team_improvement = (
            student_summary[student_summary["Team"].ne("Unassigned")]
            .groupby("Team", as_index=False)["Improvement"].mean()
            .rename(columns={"Improvement": "Average improvement"})
        )
        team_summary = team_summary.merge(team_improvement, on="Team", how="left")

        st.dataframe(team_summary.round(2), use_container_width=True, hide_index=True)

        fig = px.bar(
            team_summary,
            x="Team",
            y="Average_Score",
            color="Team",
            text=team_summary["Average_Score"].round(2),
            title="Average score by team",
            labels={"Average_Score": "Average score out of 15"}
        )
        fig.update_yaxes(range=[0, 15])
        st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(
            team_summary,
            x="Team",
            y="Average improvement",
            color="Team",
            title="Average first-to-latest improvement by team"
        )
        fig.add_hline(y=0, line_dash="dash")
        st.plotly_chart(fig, use_container_width=True)

        team_scores = assigned_data.groupby(["Team", "Student"], as_index=False)["Score"].mean()
        fig = px.bar(
            team_scores,
            x="Student",
            y="Score",
            color="Team",
            title="Student average scores within teams"
        )
        fig.update_yaxes(range=[0, 15])
        st.plotly_chart(fig, use_container_width=True)

    if unassigned:
        st.caption("Not assigned to a team: " + ", ".join(unassigned))

# ------------------------------------------------------------
# TAB 8: QUESTION ANALYSIS
# ------------------------------------------------------------
with tabs[7]:
    st.subheader("Question-wise analysis")
    if not question_cols:
        st.warning("No question columns were detected. Expected columns such as 'Q. 1 /1.00'.")
    else:
        question_summary = []
        for q in question_cols:
            values = pd.to_numeric(filtered[q], errors="coerce")
            question_summary.append({
                "Question": q,
                "Correct responses": int((values == 1).sum()),
                "Incorrect responses": int((values == 0).sum()),
                "Responses": int(values.notna().sum()),
                "Accuracy (%)": values.mean() * 100 if values.notna().any() else np.nan
            })

        q_summary = pd.DataFrame(question_summary).sort_values("Question")
        fig = px.bar(
            q_summary,
            x="Question",
            y="Accuracy (%)",
            color="Accuracy (%)",
            text=q_summary["Accuracy (%)"].round(1),
            title="Question-wise accuracy",
            labels={"Accuracy (%)": "Correct responses (%)"}
        )
        fig.update_yaxes(range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)

        valid_q = q_summary.dropna(subset=["Accuracy (%)"])
        if not valid_q.empty:
            easiest = valid_q.loc[valid_q["Accuracy (%)"].idxmax()]
            hardest = valid_q.loc[valid_q["Accuracy (%)"].idxmin()]
            e1, e2 = st.columns(2)
            e1.metric("Highest accuracy", easiest["Question"], f'{easiest["Accuracy (%)"]:.1f}%')
            e2.metric("Lowest accuracy", hardest["Question"], f'{hardest["Accuracy (%)"]:.1f}%')

        st.dataframe(q_summary.round(2), use_container_width=True, hide_index=True)

        st.markdown("**Question response matrix**")
        q_matrix = filtered.groupby("Student")[question_cols].mean() * 100
        st.dataframe(q_matrix.round(1), use_container_width=True)

# ------------------------------------------------------------
# TAB 9: DATA AND DOWNLOADS
# ------------------------------------------------------------
with tabs[8]:
    st.subheader("Cleaned dataset and downloads")
    st.write(f"Original rows in uploaded file: **{len(raw_data)}**")
    st.write(f"Valid completed attempts used: **{len(data)}**")
    st.write(f"Students identified: **{data['Student'].nunique()}**")

    if show_raw_data:
        st.markdown("**Cleaned attempt-level data**")
        display_cols = [
            "Student", "Team", "Attempt", "Started_dt",
            "Score", "Time_min"
        ] + question_cols
        display_cols = [c for c in display_cols if c in data.columns]
        st.dataframe(data[display_cols], use_container_width=True, hide_index=True)

    csv_attempts = data.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Download cleaned attempt data (CSV)",
        data=csv_attempts,
        file_name="cleaned_quiz_attempts.csv",
        mime="text/csv"
    )

    csv_summary = student_summary.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ Download student summary (CSV)",
        data=csv_summary,
        file_name="student_performance_summary.csv",
        mime="text/csv"
    )

    if question_cols:
        q_csv = q_summary.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "⬇️ Download question analysis (CSV)",
            data=q_csv,
            file_name="question_analysis.csv",
            mime="text/csv"
        )

    st.caption(
        "Team assignments are selected in the sidebar for the current app session. "
        "The uploaded CSV itself is not modified."
    )

st.divider()
st.caption("Quiz Performance Dashboard | Data is recalculated from the uploaded file.")
