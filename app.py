import io
import re
import difflib
import inspect

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ============================================================
# PAGE SETTINGS AND STYLING
# ============================================================

st.set_page_config(
    page_title="Assessment Performance Report",
    layout="wide",
)

st.markdown(
    """
    <style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    }
    .report-header {
        background: #14284B; color: #FFFFFF;
        padding: 1.5rem 2rem; border-radius: 4px; margin-bottom: 1.2rem;
    }
    .report-header h1 {
        color: #FFFFFF; font-size: 1.7rem; font-weight: 600;
        margin: 0; padding: 0; letter-spacing: 0.2px;
    }
    .report-header p { color: #C9D3E6; margin: 0.4rem 0 0 0; font-size: 0.95rem; }
    .section-title {
        font-size: 1.15rem; font-weight: 600;
        border-bottom: 2px solid #14284B;
        padding-bottom: 0.3rem; margin: 1.6rem 0 0.8rem 0;
    }
    .kpi, .finding {
        background: #FFFFFF; border: 1px solid #D9DEE7;
        border-left: 4px solid #14284B; border-radius: 3px;
        padding: 0.8rem 1rem; margin-bottom: 0.7rem; min-height: 5.2rem;
    }
    .finding { border-left-color: #8A6D1D; min-height: 6.4rem; }
    .kpi .label, .finding .label {
        font-size: 0.7rem; text-transform: uppercase;
        letter-spacing: 0.06em; color: #5B6678; font-weight: 600;
    }
    .kpi .value { font-size: 1.55rem; font-weight: 600; color: #14284B; line-height: 1.3; }
    .finding .headline { font-size: 1.05rem; font-weight: 600; color: #14284B; line-height: 1.35; margin-top: 0.15rem; }
    .kpi .sub, .finding .detail { font-size: 0.8rem; color: #5B6678; }
    </style>
    """,
    unsafe_allow_html=True,
)

TOTAL_MARKS = 15.0

# Works on both older and newer Streamlit versions.
if "width" in inspect.signature(st.plotly_chart).parameters:
    STRETCH = {"width": "stretch"}
else:
    STRETCH = {"use_container_width": True}
TEAM_COLORS = {"Apple": "#9B2D30", "Orange": "#D9822B", "Unassigned": "#7F8C8D"}
STUDENT_COLORS = px.colors.qualitative.Safe

# Spelling variants that appear in the CSV but differ from the team lists.
KNOWN_VARIANTS = {"sreelakhsmi": "sreelakshmi"}

# ============================================================
# HELPER FUNCTIONS
# ============================================================


def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)


def kpi(label, value, sub=""):
    st.markdown(
        f'<div class="kpi"><div class="label">{label}</div>'
        f'<div class="value">{value}</div><div class="sub">{sub}</div></div>',
        unsafe_allow_html=True,
    )


def finding(title, headline, detail=""):
    st.markdown(
        f'<div class="finding"><div class="label">{title}</div>'
        f'<div class="headline">{headline}</div><div class="detail">{detail}</div></div>',
        unsafe_allow_html=True,
    )


def fmt_min(x):
    """Minutes (float) -> '4 min 05 s'."""
    if pd.isna(x):
        return "N/A"
    total = int(round(float(x) * 60))
    m, s = divmod(total, 60)
    return f"{m} min {s:02d} s"


def split_camel(text):
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", str(text)).strip()


def norm(text):
    return re.sub(r"[^a-z]", "", str(text).lower())


def duration_to_minutes(value):
    """Parses '17 mins 25 secs', '19 mins 1 sec', '4 mins', 'HH:MM:SS', 'MM:SS'."""
    if pd.isna(value):
        return np.nan
    t = str(value).strip().lower()
    h = re.search(r"(\d+(?:\.\d+)?)\s*hour", t)
    m = re.search(r"(\d+(?:\.\d+)?)\s*min", t)
    s = re.search(r"(\d+(?:\.\d+)?)\s*sec", t)
    if h or m or s:
        return (
            (float(h.group(1)) * 60 if h else 0.0)
            + (float(m.group(1)) if m else 0.0)
            + (float(s.group(1)) / 60 if s else 0.0)
        )
    if ":" in t:
        try:
            parts = [float(p) for p in t.split(":")]
            if len(parts) == 3:
                return parts[0] * 60 + parts[1] + parts[2] / 60
            if len(parts) == 2:
                return parts[0] + parts[1] / 60
        except ValueError:
            return np.nan
    try:
        return float(t)
    except ValueError:
        return np.nan


def parse_datetime(series):
    s = series.astype(str).str.replace(r"\s+", " ", regex=True).str.strip()
    dt = pd.to_datetime(s, format="%d %B %Y %I:%M %p", errors="coerce")
    if dt.isna().any():
        fallback = pd.to_datetime(s, errors="coerce")
        dt = dt.fillna(fallback)
    return dt


def match_member(raw_name, members):
    """Match a CSV name to a team member (tolerates spelling mistakes)."""
    key = norm(raw_name)
    for wrong, right in KNOWN_VARIANTS.items():
        key = key.replace(wrong, right)

    best, best_ratio = None, 0.0
    for display, team in members:
        member_key = norm(display)
        if not member_key:
            continue
        if key.startswith(member_key):
            return display, team
        ratio = difflib.SequenceMatcher(None, key[: len(member_key)], member_key).ratio()
        if ratio > best_ratio:
            best, best_ratio = (display, team), ratio

    if best is not None and best_ratio >= 0.80:
        return best
    return None, "Unassigned"


def names_at(series, value):
    """Names of every student whose value equals `value` (ties handled)."""
    names = list(series[np.isclose(series.astype(float), float(value))].index)
    if len(names) == len(series) and len(series) > 1:
        return f"All {len(series)} students"
    return ", ".join(names)


def style_fig(fig, height=450):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=40, r=20, t=60, b=40),
        font=dict(family="Segoe UI, Helvetica Neue, Arial, sans-serif", size=13),
        title_font=dict(size=16),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title_text=""),
    )
    return fig


def show_table(df, **kwargs):
    st.dataframe(df, hide_index=True, **STRETCH, **kwargs)


# ============================================================
# DATA LOADING AND PREPARATION
# ============================================================


@st.cache_data(show_spinner=False)
def load_data(raw_bytes, apple_members, orange_members):
    raw = pd.read_csv(io.BytesIO(raw_bytes))
    raw.columns = raw.columns.astype(str).str.strip()

    def find(predicate):
        return next((c for c in raw.columns if predicate(c.lower())), None)

    grade_col = find(lambda c: c.startswith("grade"))
    if grade_col is None:
        return None
    email_col = find(lambda c: "email" in c)
    first_col = find(lambda c: c.startswith("first"))
    last_col = find(lambda c: c.startswith("last"))
    status_col = find(lambda c: c == "status")
    started_col = find(lambda c: c == "started")
    completed_col = find(lambda c: c == "completed")
    duration_col = find(lambda c: c == "duration")
    q_raw = [c for c in raw.columns if re.match(r"^Q\.?\s*\d+", c, re.I)]

    # --- Remove summary rows such as "Overall average" (not students) ---
    summary_mask = pd.Series(False, index=raw.index)
    for col in (first_col, last_col):
        if col:
            summary_mask |= raw[col].astype(str).str.contains(
                r"overall|average", case=False, na=False
            )
    if email_col:
        summary_mask |= raw[email_col].isna() | ~raw[email_col].astype(str).str.contains("@")
    data = raw[~summary_mask].copy()

    # --- Keep completed attempts that have a numeric grade ---
    grade = pd.to_numeric(data[grade_col], errors="coerce")
    if status_col:
        finished = data[status_col].astype(str).str.strip().str.lower().eq("finished")
    else:
        finished = pd.Series(True, index=data.index)
    valid = finished & grade.notna()
    incomplete = data[~valid].copy()
    att = data[valid].copy()
    att["Score"] = grade[valid]

    # --- Student identity (e-mail is the most reliable key) ---
    if email_col:
        att["_key"] = att[email_col].astype(str).str.strip().str.lower()
    else:
        att["_key"] = att[first_col].astype(str).str.strip().str.lower()

    def raw_name(row):
        name = str(row[first_col]).strip() if first_col and pd.notna(row[first_col]) else ""
        if not name and email_col:
            name = str(row[email_col]).split("@")[0]
        return name

    att["_raw_name"] = att.apply(raw_name, axis=1)

    members = [(n.strip(), "Apple") for n in apple_members if n.strip()] + [
        (n.strip(), "Orange") for n in orange_members if n.strip()
    ]
    matched = att["_raw_name"].apply(lambda n: match_member(n, members))
    att["Team"] = matched.apply(lambda x: x[1])
    att["Student"] = [
        m[0] if m[0] else split_camel(n) for m, n in zip(matched, att["_raw_name"])
    ]
    att["Full Name (as in CSV)"] = att["_raw_name"].apply(split_camel)

    # --- Dates, durations, attempt order ---
    att["Started"] = parse_datetime(att[started_col]) if started_col else pd.NaT
    att["Completed"] = parse_datetime(att[completed_col]) if completed_col else pd.NaT
    att["Duration"] = att[duration_col] if duration_col else np.nan
    att["Time (min)"] = att["Duration"].apply(duration_to_minutes)

    att = att.sort_values(["_key", "Started"], kind="stable").reset_index(drop=True)
    att["Attempt"] = att.groupby("_key").cumcount() + 1
    att["Percentage"] = att["Score"] / TOTAL_MARKS * 100
    att["Perfect"] = att["Score"] >= TOTAL_MARKS
    att["Score per Minute"] = np.where(att["Time (min)"] > 0, att["Score"] / att["Time (min)"], np.nan)
    att["Date"] = att["Started"].dt.strftime("%d %b %Y")

    # --- Question columns -> Q1, Q2, ... ---
    q_map = {}
    for c in q_raw:
        q_map[c] = f"Q{int(re.search(r'\d+', c).group())}"
    q_cols = sorted(q_map.values(), key=lambda x: int(x[1:]))
    for old, new in q_map.items():
        att[new] = pd.to_numeric(att[old], errors="coerce")

    # --- Student summary ---
    g = att.groupby("_key", sort=False)
    summary = g.agg(
        Student=("Student", "first"),
        Team=("Team", "first"),
        Attempts=("Score", "size"),
        First=("Score", "first"),
        Latest=("Score", "last"),
        Best=("Score", "max"),
        Lowest=("Score", "min"),
        Average=("Score", "mean"),
        Median=("Score", "median"),
        StdDev=("Score", "std"),
        AvgTime=("Time (min)", "mean"),
        FastestTime=("Time (min)", "min"),
        Perfect=("Perfect", "sum"),
    ).reset_index(drop=True)

    perfect_att = att[att["Perfect"]]
    fastest_perfect = perfect_att.groupby("Student")["Time (min)"].min()
    first_perfect_attempt = perfect_att.groupby("Student")["Attempt"].min()
    summary["FastestPerfect"] = summary["Student"].map(fastest_perfect)
    summary["FirstPerfectAt"] = summary["Student"].map(first_perfect_attempt)
    summary["Improvement"] = summary["Latest"] - summary["First"]
    summary["BestGain"] = summary["Best"] - summary["First"]
    summary["ImprovementPct"] = np.where(
        summary["First"] > 0, summary["Improvement"] / summary["First"] * 100, np.nan
    )
    summary["AvgPct"] = summary["Average"] / TOTAL_MARKS * 100

    return {
        "attempts": att,
        "summary": summary,
        "q_cols": q_cols,
        "incomplete": incomplete,
        "summary_rows_removed": int(summary_mask.sum()),
        "raw_rows": len(raw),
    }


# ============================================================
# HEADER AND UPLOAD
# ============================================================

st.markdown(
    """
    <div class="report-header">
        <h1>Assessment Performance Report</h1>
        <p>ST500304 &nbsp;|&nbsp; Questions Based on AR Models &nbsp;|&nbsp;
        Individual, improvement, time-efficiency and team (Apple vs Orange) analysis</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.header("Data Source")
uploaded_file = st.sidebar.file_uploader("Upload the assessment CSV file", type=["csv"])

st.sidebar.header("Team Configuration")
apple_text = st.sidebar.text_area(
    "Team Apple (comma-separated first names)", "Aparna, Jayalakshmi, Ganga, Jintu"
)
orange_text = st.sidebar.text_area(
    "Team Orange (comma-separated first names)", "Sreelakshmi, Aiswarya, Nandana"
)

if uploaded_file is None:
    st.info("Please upload the assessment CSV file using the sidebar to generate the report.")
    st.stop()

apple_members = tuple(x.strip() for x in apple_text.split(",") if x.strip())
orange_members = tuple(x.strip() for x in orange_text.split(",") if x.strip())

result = load_data(uploaded_file.getvalue(), apple_members, orange_members)
if result is None:
    st.error("No grade column was found in the uploaded file.")
    st.stop()

A = result["attempts"]
S = result["summary"]
q_cols = result["q_cols"]
incomplete = result["incomplete"]

if A.empty:
    st.error("The file contains no completed attempts with a numeric grade.")
    st.stop()

unassigned = S.loc[S["Team"] == "Unassigned", "Student"].tolist()
if unassigned:
    st.sidebar.warning("Not matched to any team: " + ", ".join(unassigned))

n_students = len(S)

with st.expander("Data notes and methodology"):
    st.markdown(
        f"""
- The file has **{result['raw_rows']} rows**. **{result['summary_rows_removed']}** summary row(s)
  (for example *Overall average*) were removed because they are not students.
- **{len(incomplete)}** unfinished attempt(s) (status *Never submitted* or no grade) were excluded from all scores.
- **{len(A)} completed attempts** by **{n_students} students** are analysed. Students are identified by e-mail address.
- Attempts are ordered by start time. **Improvement** = latest-attempt score minus first-attempt score.
  **Best gain** = best score minus first-attempt score.
- **Time** is converted from text such as "17 mins 25 secs" to minutes. **Score per minute** = score divided by time.
- Team names are matched to the CSV tolerantly, so spelling variants such as *Sreelakhsmi* are assigned correctly.
- No attempt is treated as an outlier or discarded; the lowest and highest scores are reported exactly as recorded.
        """
    )

# ============================================================
# TABS
# ============================================================

team_export = pd.DataFrame()

tabs = st.tabs(
    [
        "Overview",
        "Student Performance",
        "Improvement",
        "Time and Efficiency",
        "Attempts and Activity",
        "Team Comparison",
        "Question Analysis",
        "Data and Downloads",
    ]
)

# ------------------------------------------------------------
# 1. OVERVIEW
# ------------------------------------------------------------
with tabs[0]:
    section("Overall Performance Summary")

    scores = A["Score"]
    c = st.columns(6)
    with c[0]:
        kpi("Students", n_students, "with completed attempts")
    with c[1]:
        kpi("Completed Attempts", len(A), f"{len(incomplete)} unfinished excluded")
    with c[2]:
        kpi("Class Average", f"{scores.mean():.2f} / 15", f"{scores.mean() / TOTAL_MARKS * 100:.1f}%")
    with c[3]:
        kpi("Highest Score", f"{scores.max():.0f} / 15", f"{int(A['Perfect'].sum())} perfect attempts")
    with c[4]:
        kpi("Lowest Score", f"{scores.min():.0f} / 15", f"{scores.min() / TOTAL_MARKS * 100:.1f}%")
    with c[5]:
        kpi("Median Score", f"{scores.median():.1f} / 15", f"Std. deviation {scores.std():.2f}")

    c = st.columns(6)
    with c[0]:
        kpi("Average of Best Scores", f"{S['Best'].mean():.2f} / 15", "per student")
    with c[1]:
        kpi("Average First Attempt", f"{S['First'].mean():.2f} / 15", "per student")
    with c[2]:
        kpi("Average Latest Attempt", f"{S['Latest'].mean():.2f} / 15", "per student")
    with c[3]:
        kpi("Average Improvement", f"{S['Improvement'].mean():+.2f} marks", "latest minus first")
    with c[4]:
        kpi("Average Time", fmt_min(A["Time (min)"].mean()), "per attempt")
    with c[5]:
        kpi("Fastest Attempt", fmt_min(A["Time (min)"].min()), "any score")

    # ---------------- Key findings ----------------
    section("Key Findings")

    s_idx = S.set_index("Student")

    # Highest score
    top = scores.max()
    top_students = A.loc[np.isclose(A["Score"], top), "Student"].nunique()
    f_high = (f"{top:.0f} / 15", f"Achieved by {top_students} of {n_students} students; "
              f"{int(A['Perfect'].sum()) if top == TOTAL_MARKS else int((A['Score'] == top).sum())} attempts at this score")

    # Lowest score
    low = scores.min()
    low_rows = A[np.isclose(A["Score"], low)]
    f_low = (
        f"{', '.join(low_rows['Student'].unique())}: {low:.0f} / 15",
        f"Attempt {int(low_rows.iloc[0]['Attempt'])} on {low_rows.iloc[0]['Date']}",
    )

    # Most / least improved
    imp_max = s_idx["Improvement"].max()
    imp_min = s_idx["Improvement"].min()
    f_imp = (
        names_at(s_idx["Improvement"], imp_max),
        f"{imp_max:+.0f} marks: {s_idx['First'][s_idx['Improvement'] == imp_max].iloc[0]:.0f} → "
        f"{s_idx['Latest'][s_idx['Improvement'] == imp_max].iloc[0]:.0f}",
    )
    f_least = (
        names_at(s_idx["Improvement"], imp_min),
        f"{imp_min:+.0f} marks: {s_idx['First'][s_idx['Improvement'] == imp_min].iloc[0]:.0f} → "
        f"{s_idx['Latest'][s_idx['Improvement'] == imp_min].iloc[0]:.0f}",
    )

    # Most attempts
    att_max = s_idx["Attempts"].max()
    f_att = (names_at(s_idx["Attempts"], att_max), f"{int(att_max)} attempts")

    # Highest average
    avg_max = s_idx["Average"].max()
    f_avg = (names_at(s_idx["Average"].round(6), round(avg_max, 6)), f"Average {avg_max:.2f} / 15 across all attempts")

    # Most perfect scores
    pf_max = s_idx["Perfect"].max()
    f_perf = (names_at(s_idx["Perfect"], pf_max), f"{int(pf_max)} attempts scored 15 / 15")

    # Highest first attempt
    fa_max = s_idx["First"].max()
    f_first = (names_at(s_idx["First"], fa_max), f"First-attempt score {fa_max:.0f} / 15")

    # Fastest perfect score
    perfect_t = A[A["Perfect"]].dropna(subset=["Time (min)"])
    if not perfect_t.empty:
        r = perfect_t.sort_values(["Time (min)", "Started"]).iloc[0]
        f_fast = (r["Student"], f"{r['Score']:.0f} / 15 in {fmt_min(r['Time (min)'])} (attempt {int(r['Attempt'])})")
    else:
        f_fast = ("Not available", "No perfect score with a recorded duration")

    # Best score per minute
    eff = A.dropna(subset=["Score per Minute"])
    if not eff.empty:
        r = eff.loc[eff["Score per Minute"].idxmax()]
        f_eff = (r["Student"], f"{r['Score per Minute']:.2f} marks per minute "
                 f"({r['Score']:.0f} / 15 in {fmt_min(r['Time (min)'])})")
    else:
        f_eff = ("Not available", "")

    # Most consistent (lowest standard deviation, at least 3 attempts)
    cons = s_idx[s_idx["Attempts"] >= 3]["StdDev"].dropna()
    if not cons.empty:
        cmin = cons.min()
        f_cons = (cons.idxmin(), f"Standard deviation {cmin:.2f} marks across {int(s_idx.loc[cons.idxmin(), 'Attempts'])} attempts")
    else:
        f_cons = ("Not available", "")

    cards = [
        ("Highest Score", *f_high),
        ("Lowest Score", *f_low),
        ("Most Improved (First → Latest)", *f_imp),
        ("Least Improved (First → Latest)", *f_least),
        ("Most Attempts", *f_att),
        ("Highest Average Score", *f_avg),
        ("Most Perfect Scores", *f_perf),
        ("Highest First-Attempt Score", *f_first),
        ("Fastest Perfect Score", *f_fast),
        ("Best Score-per-Minute Efficiency", *f_eff),
        ("Most Consistent Student", *f_cons),
    ]
    for i in range(0, len(cards), 3):
        cols = st.columns(3)
        for col, card in zip(cols, cards[i:i + 3]):
            with col:
                finding(*card)

    # ---------------- Distribution ----------------
    section("Score Distribution")
    left, right = st.columns(2)

    with left:
        dist = (
            A["Score"].round().astype(int).value_counts()
            .reindex(range(0, int(TOTAL_MARKS) + 1), fill_value=0)
            .rename_axis("Score").reset_index(name="Attempts")
        )
        fig = px.bar(dist, x="Score", y="Attempts", text="Attempts",
                     title="Number of Attempts at Each Score",
                     color_discrete_sequence=["#14284B"])
        fig.update_traces(textposition="outside")
        fig.update_xaxes(dtick=1)
        st.plotly_chart(style_fig(fig), **STRETCH)

    with right:
        bands = pd.cut(
            A["Percentage"], bins=[-1, 40, 60, 80, 101], right=False,
            labels=["Needs Improvement (<40%)", "Average (40–59%)", "Good (60–79%)", "Excellent (80%+)"],
        )
        band_df = bands.value_counts().reindex(bands.cat.categories).rename_axis("Band").reset_index(name="Attempts")
        band_df["Share"] = (band_df["Attempts"] / len(A) * 100).round(1)
        fig = px.bar(band_df, x="Band", y="Attempts", text="Attempts",
                     title="Attempts by Performance Band",
                     color_discrete_sequence=["#8A6D1D"])
        fig.update_traces(textposition="outside")
        st.plotly_chart(style_fig(fig), **STRETCH)
        show_table(band_df.rename(columns={"Share": "Share of Attempts (%)"}))

# ------------------------------------------------------------
# 2. STUDENT PERFORMANCE
# ------------------------------------------------------------
with tabs[1]:
    section("Individual Student Summary")

    perf = S.sort_values("Average", ascending=False).copy()
    perf_display = pd.DataFrame({
        "Student": perf["Student"],
        "Team": perf["Team"],
        "Attempts": perf["Attempts"],
        "First Attempt": perf["First"],
        "Latest Attempt": perf["Latest"],
        "Best Score": perf["Best"],
        "Lowest Score": perf["Lowest"],
        "Average Score": perf["Average"].round(2),
        "Median": perf["Median"],
        "Std. Dev.": perf["StdDev"].round(2),
        "Average (%)": perf["AvgPct"].round(1),
        "Perfect Scores (15/15)": perf["Perfect"].astype(int),
        "Average Time": perf["AvgTime"].apply(fmt_min),
        "Fastest Perfect Time": perf["FastestPerfect"].apply(fmt_min),
    })
    show_table(perf_display)

    left, right = st.columns(2)
    with left:
        melt = perf.melt(
            id_vars="Student", value_vars=["First", "Average", "Best", "Lowest"],
            var_name="Measure", value_name="Score",
        )
        melt["Measure"] = melt["Measure"].replace({"First": "First Attempt", "Average": "Average", "Best": "Best", "Lowest": "Lowest"})
        fig = px.bar(melt, x="Student", y="Score", color="Measure", barmode="group",
                     title="First, Average, Best and Lowest Score by Student",
                     color_discrete_sequence=["#7F8FA9", "#14284B", "#2E7D5B", "#9B2D30"])
        fig.update_yaxes(range=[0, TOTAL_MARKS + 1], title="Score out of 15")
        st.plotly_chart(style_fig(fig), **STRETCH)

    with right:
        fig = px.box(A, x="Student", y="Score", color="Team", points="all",
                     title="Score Spread Across All Attempts",
                     color_discrete_map=TEAM_COLORS,
                     category_orders={"Student": perf["Student"].tolist()})
        fig.update_yaxes(range=[0, TOTAL_MARKS + 1], title="Score out of 15")
        st.plotly_chart(style_fig(fig), **STRETCH)

    fig = px.bar(perf, x="Student", y="Average", color="Team", text=perf["Average"].round(2),
                 title="Average Score by Student", color_discrete_map=TEAM_COLORS)
    fig.update_traces(textposition="outside")
    fig.update_yaxes(range=[0, TOTAL_MARKS + 1], title="Average score out of 15")
    st.plotly_chart(style_fig(fig, 420), **STRETCH)

# ------------------------------------------------------------
# 3. IMPROVEMENT
# ------------------------------------------------------------
with tabs[2]:
    section("Improvement from First Attempt to Latest Attempt")

    imp = S.sort_values("Improvement", ascending=False).copy()
    imp_display = pd.DataFrame({
        "Student": imp["Student"],
        "Team": imp["Team"],
        "Attempts": imp["Attempts"],
        "First Attempt": imp["First"],
        "Latest Attempt": imp["Latest"],
        "Best Score": imp["Best"],
        "Improvement (Latest − First)": imp["Improvement"],
        "Improvement (%)": imp["ImprovementPct"].round(1),
        "Best Gain (Best − First)": imp["BestGain"],
        "First Perfect Score at Attempt": imp["FirstPerfectAt"],
    })
    show_table(imp_display)

    top_row = imp.iloc[0]
    st.markdown(
        f"**Most improved student:** {names_at(imp.set_index('Student')['Improvement'], top_row['Improvement'])} "
        f"({top_row['Improvement']:+.0f} marks, from {top_row['First']:.0f} to {top_row['Latest']:.0f})."
    )

    left, right = st.columns(2)
    with left:
        fig = px.bar(imp, x="Student", y="Improvement", color="Team",
                     text=imp["Improvement"].map(lambda v: f"{v:+.0f}"),
                     title="Improvement in Marks (Latest − First)",
                     color_discrete_map=TEAM_COLORS)
        fig.update_traces(textposition="outside")
        fig.update_yaxes(title="Marks")
        st.plotly_chart(style_fig(fig), **STRETCH)

    with right:
        cmp = imp.melt(id_vars="Student", value_vars=["First", "Latest", "Best"],
                       var_name="Attempt", value_name="Score")
        cmp["Attempt"] = cmp["Attempt"].replace({"First": "First", "Latest": "Latest", "Best": "Best"})
        fig = px.bar(cmp, x="Student", y="Score", color="Attempt", barmode="group",
                     title="First, Latest and Best Score",
                     color_discrete_sequence=["#7F8FA9", "#14284B", "#2E7D5B"])
        fig.update_yaxes(range=[0, TOTAL_MARKS + 1], title="Score out of 15")
        st.plotly_chart(style_fig(fig), **STRETCH)

    section("Score Progression Across Attempts")
    chosen = st.multiselect("Students shown", S["Student"].tolist(), default=S["Student"].tolist())
    prog = A[A["Student"].isin(chosen)]
    if not prog.empty:
        fig = px.line(prog, x="Attempt", y="Score", color="Student", markers=True,
                      title="Score by Attempt Number",
                      color_discrete_sequence=STUDENT_COLORS)
        fig.update_yaxes(range=[0, TOTAL_MARKS + 1], title="Score out of 15")
        fig.update_xaxes(title="Attempt number", dtick=2)
        st.plotly_chart(style_fig(fig, 480), **STRETCH)

# ------------------------------------------------------------
# 4. TIME AND EFFICIENCY
# ------------------------------------------------------------
with tabs[3]:
    section("Time Taken and Efficiency")

    tdf = A.dropna(subset=["Time (min)"])
    if tdf.empty:
        st.info("Duration information is not available in this file.")
    else:
        c = st.columns(4)
        with c[0]:
            kpi("Average Time", fmt_min(tdf["Time (min)"].mean()), "per attempt")
        with c[1]:
            kpi("Median Time", fmt_min(tdf["Time (min)"].median()), "per attempt")
        with c[2]:
            fast = tdf.loc[tdf["Time (min)"].idxmin()]
            kpi("Quickest Attempt", fmt_min(fast["Time (min)"]), f"{fast['Student']}, score {fast['Score']:.0f}")
        with c[3]:
            slow = tdf.loc[tdf["Time (min)"].idxmax()]
            kpi("Longest Attempt", fmt_min(slow["Time (min)"]), f"{slow['Student']}, score {slow['Score']:.0f}")

        t_sum = S.sort_values("AvgTime").copy()
        t_display = pd.DataFrame({
            "Student": t_sum["Student"],
            "Team": t_sum["Team"],
            "Average Time": t_sum["AvgTime"].apply(fmt_min),
            "Fastest Attempt": t_sum["FastestTime"].apply(fmt_min),
            "Fastest Perfect Score": t_sum["FastestPerfect"].apply(fmt_min),
            "Average Score per Minute": (
                tdf.groupby("Student")["Score per Minute"].mean().reindex(t_sum["Student"]).round(2).values
            ),
        })
        show_table(t_display)

        left, right = st.columns(2)
        with left:
            fig = px.bar(t_sum, x="Student", y="AvgTime", color="Team",
                         text=t_sum["AvgTime"].round(2),
                         title="Average Time per Attempt (minutes)",
                         color_discrete_map=TEAM_COLORS)
            fig.update_traces(textposition="outside")
            fig.update_yaxes(title="Minutes")
            st.plotly_chart(style_fig(fig), **STRETCH)
        with right:
            fig = px.scatter(tdf, x="Time (min)", y="Score", color="Student",
                             hover_data=["Team", "Attempt", "Date", "Duration"],
                             title="Score versus Time Taken (every attempt)",
                             color_discrete_sequence=STUDENT_COLORS)
            fig.update_yaxes(range=[0, TOTAL_MARKS + 1], title="Score out of 15")
            fig.update_xaxes(title="Time (minutes)")
            st.plotly_chart(style_fig(fig), **STRETCH)

        fig = px.line(tdf, x="Attempt", y="Time (min)", color="Student", markers=True,
                      title="Time Taken by Attempt Number (speed improvement)",
                      color_discrete_sequence=STUDENT_COLORS)
        fig.update_yaxes(title="Minutes")
        fig.update_xaxes(title="Attempt number", dtick=2)
        st.plotly_chart(style_fig(fig, 450), **STRETCH)

        section("Top 10 Perfect Scores in the Shortest Time")
        top_perfect = (
            tdf[tdf["Perfect"]].sort_values(["Time (min)", "Started"]).head(10)
            [["Student", "Team", "Attempt", "Date", "Score", "Duration"]]
        )
        show_table(top_perfect)

# ------------------------------------------------------------
# 5. ATTEMPTS AND ACTIVITY
# ------------------------------------------------------------
with tabs[4]:
    section("Number of Attempts")

    att_sum = S.sort_values("Attempts", ascending=False)
    left, right = st.columns(2)
    with left:
        fig = px.bar(att_sum, x="Student", y="Attempts", color="Team", text="Attempts",
                     title="Completed Attempts by Student", color_discrete_map=TEAM_COLORS)
        fig.update_traces(textposition="outside")
        st.plotly_chart(style_fig(fig), **STRETCH)
    with right:
        daily = A.groupby(["Date", "Student"]).size().reset_index(name="Attempts")
        date_order = A.sort_values("Started")["Date"].drop_duplicates().tolist()
        fig = px.bar(daily, x="Date", y="Attempts", color="Student",
                     title="Attempts per Day",
                     category_orders={"Date": date_order},
                     color_discrete_sequence=STUDENT_COLORS)
        st.plotly_chart(style_fig(fig), **STRETCH)

    act = A.groupby("Student").agg(
        Team=("Team", "first"),
        Attempts=("Score", "size"),
        First_Started=("Started", "min"),
        Last_Started=("Started", "max"),
        Days_Active=("Date", "nunique"),
    ).reset_index().sort_values("Attempts", ascending=False)
    act["First_Started"] = act["First_Started"].dt.strftime("%d %b %Y, %I:%M %p")
    act["Last_Started"] = act["Last_Started"].dt.strftime("%d %b %Y, %I:%M %p")
    act = act.rename(columns={
        "First_Started": "First Attempt Started", "Last_Started": "Latest Attempt Started",
        "Days_Active": "Days Active",
    })
    show_table(act)

    if len(incomplete) > 0:
        section("Unfinished Attempts (excluded from scores)")
        keep = [c for c in incomplete.columns if not re.match(r"^Q\.?\s*\d+", c, re.I)]
        show_table(incomplete[keep])

# ------------------------------------------------------------
# 6. TEAM COMPARISON
# ------------------------------------------------------------
with tabs[5]:
    section("Apple versus Orange")

    def team_metrics(team):
        a = A[A["Team"] == team]
        s = S[S["Team"] == team]
        if a.empty:
            return None
        pf = a[a["Perfect"]]
        return {
            "Students": (len(s), "int"),
            "Completed attempts": (len(a), "int"),
            "Average attempts per student": (s["Attempts"].mean(), "f2"),
            "Average score (all attempts)": (a["Score"].mean(), "f2"),
            "Average percentage": (a["Percentage"].mean(), "pct"),
            "Median score": (a["Score"].median(), "f1"),
            "Highest score": (a["Score"].max(), "f0"),
            "Lowest score": (a["Score"].min(), "f0"),
            "Perfect scores (15/15)": (len(pf), "int"),
            "Average of students' best scores": (s["Best"].mean(), "f2"),
            "Average first-attempt score": (s["First"].mean(), "f2"),
            "Average latest-attempt score": (s["Latest"].mean(), "f2"),
            "Average improvement (latest − first)": (s["Improvement"].mean(), "signed"),
            "Total improvement (latest − first)": (s["Improvement"].sum(), "signed"),
            "Average best gain (best − first)": (s["BestGain"].mean(), "signed"),
            "Average time per attempt": (a["Time (min)"].mean(), "time"),
            "Fastest attempt": (a["Time (min)"].min(), "time"),
            "Fastest perfect score": (pf["Time (min)"].min() if len(pf) else np.nan, "time"),
        }

    def fmt_metric(value, kind):
        if pd.isna(value):
            return "N/A"
        return {
            "int": f"{int(value)}",
            "f0": f"{value:.0f}",
            "f1": f"{value:.1f}",
            "f2": f"{value:.2f}",
            "pct": f"{value:.1f}%",
            "signed": f"{value:+.2f}",
            "time": fmt_min(value),
        }[kind]

    tm = {t: team_metrics(t) for t in ["Apple", "Orange"]}

    if tm["Apple"] is None or tm["Orange"] is None:
        st.warning("Both teams need at least one matched student for a comparison. Check the team names in the sidebar.")
    else:
        rows = []
        for label in tm["Apple"]:
            rows.append({
                "Measure": label,
                "Apple": fmt_metric(*tm["Apple"][label]),
                "Orange": fmt_metric(*tm["Orange"][label]),
            })
        team_table = pd.DataFrame(rows)
        team_export = team_table
        show_table(team_table)

        # ---- Verdict ----
        a_score, o_score = tm["Apple"]["Average score (all attempts)"][0], tm["Orange"]["Average score (all attempts)"][0]
        a_time, o_time = tm["Apple"]["Average time per attempt"][0], tm["Orange"]["Average time per attempt"][0]
        a_best, o_best = tm["Apple"]["Average of students' best scores"][0], tm["Orange"]["Average of students' best scores"][0]
        a_imp, o_imp = tm["Apple"]["Average improvement (latest − first)"][0], tm["Orange"]["Average improvement (latest − first)"][0]

        def leader(a, o, higher=True, tol=1e-9):
            if pd.isna(a) or pd.isna(o) or abs(a - o) < tol:
                return None
            return "Apple" if (a > o) == higher else "Orange"

        score_leader = leader(a_score, o_score, True)
        time_leader = leader(a_time, o_time, False)

        section("Team Verdict")
        if score_leader and score_leader == time_leader:
            st.success(
                f"Team {score_leader} performs better on both criteria: higher average score "
                f"({max(a_score, o_score):.2f} versus {min(a_score, o_score):.2f}) and lower average time per attempt "
                f"({fmt_min(min(a_time, o_time))} versus {fmt_min(max(a_time, o_time))})."
            )
        elif score_leader and time_leader:
            st.info(
                f"Results are mixed. Team {score_leader} has the higher average score "
                f"({max(a_score, o_score):.2f} versus {min(a_score, o_score):.2f}), while Team {time_leader} has the lower "
                f"average time per attempt ({fmt_min(min(a_time, o_time))} versus {fmt_min(max(a_time, o_time))})."
            )
        else:
            st.info("The two teams are level on at least one of the two criteria (average score, average time).")

        verdict_rows = [
            ("Higher average score (all attempts)", leader(a_score, o_score, True)),
            ("Higher average of best scores", leader(a_best, o_best, True)),
            ("Lower average time per attempt", time_leader),
            ("Greater average improvement", leader(a_imp, o_imp, True)),
        ]
        show_table(pd.DataFrame(verdict_rows, columns=["Criterion", "Leading Team"]).fillna("Level"))

        # ---- Charts ----
        tsum = pd.DataFrame({
            "Team": ["Apple", "Orange"],
            "Average Score": [a_score, o_score],
            "Average of Best Scores": [a_best, o_best],
            "Average Time (min)": [a_time, o_time],
            "Average Improvement": [a_imp, o_imp],
            "Average Attempts per Student": [
                tm["Apple"]["Average attempts per student"][0],
                tm["Orange"]["Average attempts per student"][0],
            ],
            "Total Attempts": [tm["Apple"]["Completed attempts"][0], tm["Orange"]["Completed attempts"][0]],
        })

        def team_bar(col, title, ytitle, fmt="%{text:.2f}"):
            fig = px.bar(tsum, x="Team", y=col, color="Team", text=col, title=title,
                         color_discrete_map=TEAM_COLORS)
            fig.update_traces(texttemplate=fmt, textposition="outside")
            fig.update_yaxes(title=ytitle)
            fig.update_layout(showlegend=False)
            return style_fig(fig, 380)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.plotly_chart(team_bar("Average Score", "Average Score", "Score out of 15"), **STRETCH)
        with c2:
            st.plotly_chart(team_bar("Average Time (min)", "Average Time per Attempt", "Minutes"), **STRETCH)
        with c3:
            st.plotly_chart(team_bar("Average Improvement", "Average Improvement (Latest − First)", "Marks"), **STRETCH)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.plotly_chart(team_bar("Average of Best Scores", "Average of Students' Best Scores", "Score out of 15"), **STRETCH)
        with c2:
            st.plotly_chart(team_bar("Average Attempts per Student", "Average Attempts per Student", "Attempts"), **STRETCH)
        with c3:
            st.plotly_chart(team_bar("Total Attempts", "Total Completed Attempts", "Attempts", "%{text:.0f}"), **STRETCH)

        fig = px.box(A[A["Team"].isin(["Apple", "Orange"])], x="Team", y="Score", color="Team",
                     points="all", title="Score Distribution by Team",
                     color_discrete_map=TEAM_COLORS)
        fig.update_yaxes(range=[0, TOTAL_MARKS + 1], title="Score out of 15")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_fig(fig, 420), **STRETCH)

        section("Team Members")
        members_df = S[S["Team"].isin(["Apple", "Orange"])].sort_values(["Team", "Average"], ascending=[True, False])
        show_table(pd.DataFrame({
            "Team": members_df["Team"],
            "Student": members_df["Student"],
            "Attempts": members_df["Attempts"],
            "First": members_df["First"],
            "Latest": members_df["Latest"],
            "Best": members_df["Best"],
            "Lowest": members_df["Lowest"],
            "Average": members_df["Average"].round(2),
            "Improvement": members_df["Improvement"],
            "Average Time": members_df["AvgTime"].apply(fmt_min),
        }))

# ------------------------------------------------------------
# 7. QUESTION ANALYSIS
# ------------------------------------------------------------
with tabs[6]:
    section("Question-wise Analysis")

    if not q_cols:
        st.info("No question columns were found in the file.")
    else:
        q_rows = []
        for q in q_cols:
            vals = A[q].dropna()
            q_rows.append({
                "Question": q,
                "Correct": int((vals > 0).sum()),
                "Attempts": len(vals),
                "Accuracy (%)": vals.mean() * 100 if len(vals) else np.nan,
            })
        qdf = pd.DataFrame(q_rows)
        qdf["Difficulty"] = pd.cut(qdf["Accuracy (%)"], bins=[-1, 80, 90, 101],
                                   labels=["Difficult", "Moderate", "Easy"], right=False)
        qdf["Rank (1 = hardest)"] = qdf["Accuracy (%)"].rank(method="min").astype(int)

        hardest = qdf.loc[qdf["Accuracy (%)"].idxmin()]
        easiest = qdf.loc[qdf["Accuracy (%)"].idxmax()]
        c = st.columns(3)
        with c[0]:
            kpi("Hardest Question", hardest["Question"], f"{hardest['Accuracy (%)']:.1f}% answered correctly")
        with c[1]:
            kpi("Easiest Question", easiest["Question"], f"{easiest['Accuracy (%)']:.1f}% answered correctly")
        with c[2]:
            kpi("Average Accuracy", f"{qdf['Accuracy (%)'].mean():.1f}%", "across all questions")

        left, right = st.columns([1, 1])
        with left:
            show_table(qdf.assign(**{"Accuracy (%)": qdf["Accuracy (%)"].round(1)}))
        with right:
            fig = px.bar(qdf, x="Question", y="Accuracy (%)", text=qdf["Accuracy (%)"].round(1),
                         title="Percentage Answered Correctly, by Question",
                         color_discrete_sequence=["#14284B"])
            fig.update_traces(textposition="outside")
            fig.update_yaxes(range=[0, 108])
            st.plotly_chart(style_fig(fig, 420), **STRETCH)

        section("Accuracy by Team and by Student")
        team_q = (
            A[A["Team"].isin(["Apple", "Orange"])]
            .groupby("Team")[q_cols].mean().mul(100).reset_index()
            .melt(id_vars="Team", var_name="Question", value_name="Accuracy (%)")
        )
        fig = px.bar(team_q, x="Question", y="Accuracy (%)", color="Team", barmode="group",
                     title="Question Accuracy: Apple versus Orange",
                     color_discrete_map=TEAM_COLORS)
        fig.update_yaxes(range=[0, 105])
        st.plotly_chart(style_fig(fig, 420), **STRETCH)

        heat = A.groupby("Student")[q_cols].mean().mul(100).round(0)
        fig = px.imshow(heat, text_auto=".0f", aspect="auto", color_continuous_scale="Blues",
                        zmin=0, zmax=100, title="Percentage Correct by Student and Question")
        fig.update_xaxes(side="top")
        st.plotly_chart(style_fig(fig, 420), **STRETCH)

# ------------------------------------------------------------
# 8. DATA AND DOWNLOADS
# ------------------------------------------------------------
with tabs[7]:
    section("All Completed Attempts")

    pick = st.multiselect("Filter by student", S["Student"].tolist(), default=[])
    base_cols = ["Student", "Team", "Attempt", "Date", "Score", "Percentage", "Duration", "Time (min)",
                 "Score per Minute"] + q_cols
    view = A[A["Student"].isin(pick)] if pick else A
    view = view.sort_values(["Started"])[base_cols].copy()
    view["Percentage"] = view["Percentage"].round(1)
    view["Time (min)"] = view["Time (min)"].round(2)
    view["Score per Minute"] = view["Score per Minute"].round(2)
    show_table(view)

    section("Download Reports")

    student_export = pd.DataFrame({
        "Student": S["Student"], "Team": S["Team"], "Attempts": S["Attempts"],
        "First Attempt": S["First"], "Latest Attempt": S["Latest"], "Best Score": S["Best"],
        "Lowest Score": S["Lowest"], "Average Score": S["Average"].round(2),
        "Improvement (Latest - First)": S["Improvement"], "Improvement (%)": S["ImprovementPct"].round(1),
        "Best Gain (Best - First)": S["BestGain"], "Perfect Scores": S["Perfect"].astype(int),
        "Average Time": S["AvgTime"].apply(fmt_min), "Fastest Perfect Time": S["FastestPerfect"].apply(fmt_min),
    })
    d1, d2, d3 = st.columns(3)
    d1.download_button("Student Summary (CSV)", student_export.to_csv(index=False),
                       "student_summary.csv", "text/csv")
    d2.download_button("All Attempts (CSV)", view.to_csv(index=False),
                       "all_attempts.csv", "text/csv")
    if not team_export.empty:
        d3.download_button("Team Comparison (CSV)", team_export.to_csv(index=False),
                           "apple_orange_comparison.csv", "text/csv")

st.markdown("---")
st.caption("Assessment Performance Report  |  Completed attempts only  |  Improvement measured from first to latest attempt")
