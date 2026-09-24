"""
Quiz Results Dashboard (Streamlit)
 
Upload a quiz export CSV with these columns:
    Last name, First name, Email address, Status, Started, Completed,
    Duration, Grade/15.00
 
Run locally:
    pip install -r requirements.txt
    streamlit run app.py
"""
 
import io
import re
 
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
 
st.set_page_config(page_title="Quiz Results Dashboard", page_icon="📝", layout="wide")
 
 
# --------------------------------------------------------------------------
# Parsing helpers
# --------------------------------------------------------------------------
def norm(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).replace("\ufeff", "")).strip().lower()
 
 
def detect_columns(columns) -> dict:
    """Map the columns in the file to standard names."""
    found = {}
    for col in columns:
        n = norm(col)
        if n.startswith("last name") or n == "surname":
            found.setdefault("last", col)
        elif n.startswith("first name"):
            found.setdefault("first", col)
        elif n.startswith("email"):
            found.setdefault("email", col)
        elif n in ("status", "state"):
            found.setdefault("status", col)
        elif n.startswith("started"):
            found.setdefault("started", col)
        elif n.startswith("completed"):
            found.setdefault("completed", col)
        elif n in ("duration", "time taken"):
            found.setdefault("duration", col)
        elif n.startswith("grade"):
            found.setdefault("grade", col)
    return found
 
 
def parse_duration(value):
    """'12 mins 30 secs', '1 hour 5 mins', '00:12:30' or plain seconds -> seconds."""
    if value is None or pd.isna(value):
        return np.nan
    s = str(value).strip()
    if not s or s == "-":
        return np.nan
    m = re.fullmatch(r"(\d+):(\d{2})(?::(\d{2}))?", s)
    if m:
        a, b, c = int(m.group(1)), int(m.group(2)), m.group(3)
        return a * 3600 + b * 60 + int(c) if c is not None else a * 60 + b
    total, found = 0.0, False
    for num, unit in re.findall(
        r"(\d+(?:\.\d+)?)\s*(days?|hours?|hrs?|minutes?|mins?|seconds?|secs?)", s, re.I
    ):
        found = True
        u = unit[0].lower()
        factor = {"d": 86400, "h": 3600, "m": 60, "s": 1}[u]
        total += float(num) * factor
    if found:
        return total
    try:
        return float(s)
    except ValueError:
        return np.nan
 
 
def parse_dates(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.strip().replace({"-": None, "nan": None, "": None})
    parsed = pd.to_datetime(cleaned, format="%d %B %Y %I:%M %p", errors="coerce")
    missing = parsed.isna() & cleaned.notna()
    if missing.any():
        parsed[missing] = pd.to_datetime(cleaned[missing], errors="coerce")
    return parsed
 
 
def fmt_dur(seconds) -> str:
    if seconds is None or pd.isna(seconds):
        return "—"
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"
 
 
def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"
 
 
# --------------------------------------------------------------------------
# Data preparation
# --------------------------------------------------------------------------
def prepare(raw: pd.DataFrame):
    cols = detect_columns(raw.columns)
    missing = [k for k in ("grade",) if k not in cols]
    if not any(k in cols for k in ("first", "last", "email")):
        missing.append("First name / Last name / Email address")
    if missing:
        raise ValueError(
            "Could not find these columns: "
            + ", ".join(missing)
            + ". Columns in your file: "
            + ", ".join(map(str, raw.columns))
        )
 
    max_match = re.search(r"/\s*([\d.,]+)", str(cols["grade"]))
    max_grade = float(max_match.group(1).replace(",", ".")) if max_match else 15.0
 
    def col(key):
        return raw[cols[key]] if key in cols else pd.Series([""] * len(raw), index=raw.index)
 
    df = pd.DataFrame(
        {
            "Last name": col("last").fillna("").astype(str).str.strip(),
            "First name": col("first").fillna("").astype(str).str.strip(),
            "Email": col("email").fillna("").astype(str).str.strip(),
            "Status": col("status").fillna("").astype(str).str.strip(),
            "Started": parse_dates(col("started")),
            "Completed": parse_dates(col("completed")),
            "dur_s": col("duration").map(parse_duration),
            "Grade": pd.to_numeric(
                col("grade").astype(str).str.replace(",", ".", regex=False), errors="coerce"
            ),
        }
    )
 
    # Drop the "Overall average" footer row and empty rows
    footer = df["Last name"].str.contains("overall average", case=False) | df[
        "First name"
    ].str.contains("overall average", case=False)
    empty = (df["Last name"] == "") & (df["First name"] == "") & (df["Email"] == "")
    df = df[~footer & ~empty].copy()
    df["_row"] = range(len(df))
 
    df["Student"] = (df["First name"] + " " + df["Last name"]).str.strip()
    df.loc[df["Student"] == "", "Student"] = df["Email"]
    df["key"] = np.where(df["Email"] != "", df["Email"].str.lower(), df["Student"].str.lower())
 
    # Fill missing durations from Started/Completed
    calc = (df["Completed"] - df["Started"]).dt.total_seconds()
    df["dur_s"] = df["dur_s"].fillna(calc)
 
    finished_status = df["Status"].str.contains("finish", case=False)
    in_progress = df["Status"].str.contains("progress|never", case=False)
    df["Finished"] = finished_status | (df["Completed"].notna() & ~in_progress)
 
    # Attempt number per student, in the order the attempts were started
    df = df.sort_values(["key", "Started", "_row"], kind="stable")
    df["Attempt"] = df.groupby("key").cumcount() + 1
    df["Time (min)"] = (df["dur_s"] / 60).round(2)
    return df.reset_index(drop=True), max_grade
 
 
def student_table(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key, g in df.groupby("key", sort=False):
        scored = g[g["Grade"].notna()]
        best = None
        if not scored.empty:
            best = scored.sort_values(["Grade", "dur_s"], ascending=[False, True]).iloc[0]
        first = scored.iloc[0] if not scored.empty else None
        last = scored.iloc[-1] if not scored.empty else None
        rows.append(
            {
                "Student": g["Student"].iloc[0],
                "Email": g["Email"].iloc[0],
                "Attempts": len(g),
                "Best score": best["Grade"] if best is not None else np.nan,
                "Time for best (min)": round(best["dur_s"] / 60, 2) if best is not None and pd.notna(best["dur_s"]) else np.nan,
                "Best on attempt": int(best["Attempt"]) if best is not None else np.nan,
                "1st score": first["Grade"] if first is not None else np.nan,
                "Latest score": last["Grade"] if last is not None else np.nan,
                "Change": (last["Grade"] - first["Grade"]) if len(scored) > 1 else np.nan,
                "Average": scored["Grade"].mean() if not scored.empty else np.nan,
                "Total time (min)": round(g["dur_s"].sum() / 60, 2) if g["dur_s"].notna().any() else np.nan,
            }
        )
    out = pd.DataFrame(rows)
    out = out.sort_values(["Best score", "Time for best (min)"], ascending=[False, True], na_position="last")
    out.insert(0, "Rank", range(1, len(out) + 1))
    return out.reset_index(drop=True)
 
 
def top_rows(df: pd.DataFrame, sort_cols, ascending):
    """Best row(s) by sort order. Returns every row tied with the winner."""
    if df.empty:
        return df
    ordered = df.sort_values(sort_cols, ascending=ascending)
    first = ordered.iloc[0]
    same = (ordered[sort_cols].fillna(-1) == first[sort_cols].fillna(-1)).all(axis=1)
    return ordered[same]
 
 
def ties_text(tied: pd.DataFrame, name_col="Student") -> str:
    names = list(dict.fromkeys(tied[name_col].tolist()))[1:]
    if not names:
        return ""
    shown = ", ".join(names[:3])
    extra = f" and {len(names) - 3} more" if len(names) > 3 else ""
    return f"Also tied: {shown}{extra}"
 
 
def highlight(container, label, name, detail, note=""):
    with container.container(border=True):
        st.caption(label)
        st.subheader(name)
        st.write(detail)
        if note:
            st.caption(note)
 
 
# --------------------------------------------------------------------------
# Sample data (same layout as a Moodle quiz export)
# --------------------------------------------------------------------------
def sample_csv() -> str:
    rng = np.random.default_rng(11)
    first_names = ["Aarav", "Diya", "Kiran", "Meera", "Rahul", "Anjali", "Vishnu", "Neha", "Arjun", "Sneha"]
    last_names = ["Nair", "Menon", "Pillai", "Thomas", "Kurian", "Varma", "Das", "Iyer"]
    rows = []
    for i in range(36):
        first, last = first_names[i % 10], last_names[(i // 4) % 8]
        email = f"{first}.{last}{i}@example.com".lower()
        skill = 5 + rng.random() * 8
        attempts = 1 + int(rng.random() * rng.random() * 4.2)
        t0 = pd.Timestamp(2025, 3, 10 + int(rng.integers(0, 5)), 9 + int(rng.integers(0, 7)), int(rng.integers(0, 60)))
        for a in range(attempts):
            started = t0 + pd.Timedelta(days=a, minutes=int(rng.integers(0, 60)))
            secs = int(rng.integers(240, 1740))
            grade = float(np.clip(round((skill + a * rng.random() * 2.2 + (rng.random() - 0.5) * 3) * 2) / 2, 0, 15))
            started_s = started.strftime("%d %B %Y %I:%M %p").lstrip("0")
            done_s = (started + pd.Timedelta(seconds=secs)).strftime("%d %B %Y %I:%M %p").lstrip("0")
            dur_s = f"{secs // 60} mins {secs % 60} secs"
            rows.append([last, first, email, "Finished", started_s, done_s, dur_s, f"{grade:.2f}"])
    cols = ["Last name", "First name", "Email address", "Status", "Started", "Completed", "Duration", "Grade/15.00"]
    df = pd.DataFrame(rows, columns=cols)
    avg = df["Grade/15.00"].astype(float).mean()
    df.loc[len(df)] = ["Overall average", "", "", "", "", "", "", f"{avg:.2f}"]
    return df.to_csv(index=False)
 
 
# --------------------------------------------------------------------------
# App
# --------------------------------------------------------------------------
st.title("Quiz results dashboard")
st.write("Upload your quiz export to see who scored highest, who was fastest, and who tried the most.")
 
with st.sidebar:
    st.header("Data")
    uploaded = st.file_uploader("Quiz results CSV", type=["csv"])
    use_sample = st.checkbox("Use sample data", value=False)
    pass_pct = st.number_input("Pass mark (%)", min_value=0, max_value=100, value=50, step=5)
 
if uploaded is not None:
    raw = pd.read_csv(uploaded, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    source = uploaded.name
elif use_sample:
    raw = pd.read_csv(io.StringIO(sample_csv()), dtype=str, keep_default_na=False)
    source = "sample data"
else:
    st.info("Upload a CSV in the sidebar, or tick “Use sample data”.")
    st.stop()
 
try:
    df, max_grade = prepare(raw)
except ValueError as err:
    st.error(str(err))
    st.stop()
 
if df.empty:
    st.error("The file has no student rows.")
    st.stop()
 
scored = df[df["Grade"].notna()]
students = student_table(df)
st.caption(f"Showing {source}")
 
# ---- Top result --------------------------------------------------------
candidates = scored[scored["Finished"] | scored["dur_s"].notna()]
best_overall = top_rows(candidates if not candidates.empty else scored, ["Grade", "dur_s"], [False, True])
if not best_overall.empty:
    w = best_overall.iloc[0]
    with st.container(border=True):
        c1, c2 = st.columns([1, 3])
        c1.metric("Top score", f"{w['Grade']:g} / {max_grade:g}")
        c2.caption("Highest score in the least time")
        c2.subheader(w["Student"])
        c2.write(f"**{fmt_dur(w['dur_s'])}** on attempt **{int(w['Attempt'])}**  ·  {w['Email']}")
        if ties_text(best_overall):
            c2.caption(ties_text(best_overall))
 
# ---- KPIs --------------------------------------------------------------
with_score = students[students["Best score"].notna()]
passed = (with_score["Best score"] / max_grade * 100 >= pass_pct).sum() if len(with_score) else 0
k = st.columns(6)
k[0].metric("Students", len(students))
k[1].metric("Attempts", len(df))
k[2].metric(f"Average score (of {max_grade:g})", f"{scored['Grade'].mean():.2f}" if len(scored) else "—")
k[3].metric("Average time", fmt_dur(df.loc[df["Finished"], "dur_s"].mean()))
k[4].metric(f"Passed (≥ {pass_pct}%)", f"{passed / len(with_score) * 100:.0f}%" if len(with_score) else "—")
k[5].metric("Unfinished attempts", int((~df["Finished"]).sum()))
 
# ---- Highlights --------------------------------------------------------
st.header("Highlights")
st.caption("Ties are broken by the shorter time taken.")
 
row1 = st.columns(3)
row2 = st.columns(3)
 
best = top_rows(scored, ["Grade", "dur_s"], [False, True])
if not best.empty:
    b = best.iloc[0]
    highlight(row1[0], "Highest score in least time", b["Student"],
              f"**{b['Grade']:g}** in {fmt_dur(b['dur_s'])} (attempt {int(b['Attempt'])})", ties_text(best))
 
fast = top_rows(scored[scored["Finished"] & (scored["dur_s"] > 0)], ["dur_s"], [True])
if not fast.empty:
    f = fast.iloc[0]
    highlight(row1[1], "Fastest to finish", f["Student"],
              f"**{fmt_dur(f['dur_s'])}** with a score of {f['Grade']:g}", ties_text(fast))
 
most = top_rows(students, ["Attempts"], [False])
if not most.empty:
    m = most.iloc[0]
    highlight(row1[2], "Most attempts", m["Student"],
              f"**{int(m['Attempts'])}** attempts, best score {m['Best score']:g}", ties_text(most))
 
first_top = top_rows(scored[scored["Attempt"] == 1], ["Grade", "dur_s"], [False, True])
if not first_top.empty:
    t = first_top.iloc[0]
    highlight(row2[0], "Highest score in the 1st attempt", t["Student"],
              f"**{t['Grade']:g}** in {fmt_dur(t['dur_s'])}", ties_text(first_top))
 
improved = students[students["Change"].notna()]
imp = top_rows(improved, ["Change"], [False])
if not imp.empty and imp.iloc[0]["Change"] > 0:
    i = imp.iloc[0]
    highlight(row2[1], "Most improved", i["Student"],
              f"**+{i['Change']:.2f}** from first to last attempt ({i['1st score']:g} to {i['Latest score']:g})",
              ties_text(imp))
 
full = students[students["Best score"] >= max_grade]
names = ", ".join(full["Student"].head(4)) + (f" and {len(full) - 4} more" if len(full) > 4 else "")
highlight(row2[2], "Full marks", f"{len(full)} student{'s' if len(full) != 1 else ''}",
          names if len(full) else f"Nobody reached {max_grade:g} yet")
 
# ---- Best result in each attempt --------------------------------------
st.header("Best result in each attempt")
st.caption("Attempts are numbered per student in the order they were started.")
rows = []
for n in sorted(scored["Attempt"].unique()):
    sub = scored[scored["Attempt"] == n]
    tw = top_rows(sub, ["Grade", "dur_s"], [False, True])
    w = tw.iloc[0]
    rows.append({
        "Attempt": ordinal(int(n)),
        "Submitted": len(sub),
        "Average": round(sub["Grade"].mean(), 2),
        "Lowest": sub["Grade"].min(),
        "Top scorer": w["Student"] + (f" (+{len(tw) - 1} tied)" if len(tw) > 1 else ""),
        "Score": w["Grade"],
        "Time": fmt_dur(w["dur_s"]),
    })
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
 
# ---- Charts ------------------------------------------------------------
st.header("Charts")
c1, c2 = st.columns(2)
with c1:
    fig = px.histogram(with_score, x="Best score", nbins=int(np.ceil(max_grade)) + 1,
                       title="Score distribution (best score per student)")
    fig.update_layout(yaxis_title="Students", bargap=0.05)
    st.plotly_chart(fig, width="stretch")
with c2:
    counts = students["Attempts"].value_counts().sort_index().reset_index()
    counts.columns = ["Attempts", "Students"]
    fig = px.bar(counts, x="Attempts", y="Students", title="Students by number of attempts")
    fig.update_xaxes(type="category")
    st.plotly_chart(fig, width="stretch")
 
c3, c4 = st.columns(2)
with c3:
    by_attempt = scored.groupby("Attempt", as_index=False)["Grade"].mean()
    fig = px.line(by_attempt, x="Attempt", y="Grade", markers=True, title="Average score by attempt number")
    fig.update_xaxes(dtick=1)
    fig.update_yaxes(rangemode="tozero")
    st.plotly_chart(fig, width="stretch")
with c4:
    fig = px.scatter(scored.dropna(subset=["Time (min)"]), x="Time (min)", y="Grade",
                     hover_name="Student", title="Score vs time taken")
    st.plotly_chart(fig, width="stretch")
 
# ---- Detail tables -----------------------------------------------------
st.header("Details")
query = st.text_input("Search name or email")
tab1, tab2 = st.tabs(["Students", "All attempts"])
 
with tab1:
    view = students
    if query:
        mask = view["Student"].str.contains(query, case=False, na=False) | view["Email"].str.contains(query, case=False, na=False)
        view = view[mask]
    st.dataframe(view, hide_index=True, width="stretch")
    st.download_button("Download student summary (CSV)", students.to_csv(index=False),
                       file_name="student_summary.csv", mime="text/csv")
 
with tab2:
    view = df[["Student", "Email", "Attempt", "Status", "Started", "Completed", "Time (min)", "Grade"]]
    if query:
        mask = view["Student"].str.contains(query, case=False, na=False) | view["Email"].str.contains(query, case=False, na=False)
        view = view[mask]
    st.dataframe(view, hide_index=True, width="stretch")
 
