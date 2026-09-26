
import io
import re

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# ==========================================================================
# PAGE SETTINGS
# ==========================================================================

st.set_page_config(
    page_title="Quiz Results Dashboard",
    page_icon="📝",
    layout="wide"
)


# ==========================================================================
# PARSING HELPERS
# ==========================================================================

def norm(text: str) -> str:
    return re.sub(
        r"\s+",
        "",
        str(text)
        .replace("\ufeff", "")
    ).strip().lower()


def detect_columns(columns) -> dict:
    """Map the columns in the uploaded file to standard names."""

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
    """
    Convert different duration formats into seconds.

    Examples:
        12 mins 30 secs
        1 hour 5 mins
        00:12:30
        12:30
        plain seconds
    """

    if value is None or pd.isna(value):
        return np.nan

    s = str(value).strip()

    if not s or s == "-":
        return np.nan

    # HH:MM:SS or MM:SS
    m = re.fullmatch(r"(\d+):(\d{2})(?::(\d{2}))?", s)

    if m:
        a, b, c = int(m.group(1)), int(m.group(2)), m.group(3)

        if c is not None:
            return a * 3600 + b * 60 + int(c)

        return a * 60 + b

    # Text duration
    total = 0.0
    found = False

    for num, unit in re.findall(
        r"(\d+(?:\.\d+)?)\s*"
        r"(days?|hours?|hrs?|minutes?|mins?|seconds?|secs?)",
        s,
        re.I
    ):
        found = True

        u = unit[0].lower()

        factor = {
            "d": 86400,
            "h": 3600,
            "m": 60,
            "s": 1
        }[u]

        total += float(num) * factor

    if found:
        return total

    try:
        return float(s)
    except ValueError:
        return np.nan


def parse_dates(series: pd.Series) -> pd.Series:

    cleaned = (
        series
        .astype(str)
        .str.strip()
        .replace({
            "-": None,
            "nan": None,
            "": None
        })
    )

    parsed = pd.to_datetime(
        cleaned,
        format="%d %B %Y %I:%M %p",
        errors="coerce"
    )

    missing = parsed.isna() & cleaned.notna()

    if missing.any():
        parsed.loc[missing] = pd.to_datetime(
            cleaned.loc[missing],
            errors="coerce"
        )

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

    suffix = (
        "th"
        if 10 <= n % 100 <= 20
        else {
            1: "st",
            2: "nd",
            3: "rd"
        }.get(n % 10, "th")
    )

    return f"{n}{suffix}"


# ==========================================================================
# TEAM ASSIGNMENT
# ==========================================================================

# ==========================================================================
# TEAM ASSIGNMENT
# ==========================================================================

# ==========================================================================
# TEAM ASSIGNMENT
# ==========================================================================

TEAM_MAP = {

    # Apple Team
    "aparna": "Apple",
    "jayalakshmi": "Apple",
    "ganga": "Apple",
    "jintu": "Apple",

    # Orange Team
    "sreelakhsmiAnilkumar": "Orange",
    "aiswarya": "Orange",
    "nandana": "Orange",
}

def assign_team(student_name):

    name = norm(student_name)

    for member, team in TEAM_MAP.items():

        if member in name:
            return team

    return "Unassigned"
# ==========================================================================
# DATA PREPARATION
# ==========================================================================

def prepare(raw: pd.DataFrame):

    cols = detect_columns(raw.columns)

    missing = [
        k
        for k in ("grade",)
        if k not in cols
    ]

    if not any(
        k in cols
        for k in ("first", "last", "email")
    ):
        missing.append(
            "First name / Last name / Email address"
        )

    if missing:

        raise ValueError(
            "Could not find these columns: "
            + ", ".join(missing)
            + ". Columns in your file: "
            + ", ".join(map(str, raw.columns))
        )

    max_match = re.search(
        r"/\s*([\d.,]+)",
        str(cols["grade"])
    )

    max_grade = (
        float(
            max_match.group(1).replace(",", ".")
        )
        if max_match
        else 15.0
    )

    def col(key):

        if key in cols:
            return raw[cols[key]]

        return pd.Series(
            [""] * len(raw),
            index=raw.index
        )

    df = pd.DataFrame(
        {
            "Last name":
                col("last")
                .fillna("")
                .astype(str)
                .str.strip(),

            "First name":
                col("first")
                .fillna("")
                .astype(str)
                .str.strip(),

            "Email":
                col("email")
                .fillna("")
                .astype(str)
                .str.strip(),

            "Status":
                col("status")
                .fillna("")
                .astype(str)
                .str.strip(),

            "Started":
                parse_dates(col("started")),

            "Completed":
                parse_dates(col("completed")),

            "dur_s":
                col("duration")
                .map(parse_duration),

            "Grade":
                pd.to_numeric(
                    col("grade")
                    .astype(str)
                    .str.replace(
                        ",",
                        ".",
                        regex=False
                    ),
                    errors="coerce"
                )
        }
    )

    # --------------------------------------------------------------
    # Remove footer and empty rows
    # --------------------------------------------------------------

    footer = (
        df["Last name"]
        .str.contains(
            "overall average",
            case=False
        )
        |
        df["First name"]
        .str.contains(
            "overall average",
            case=False
        )
    )

    empty = (
        (df["Last name"] == "")
        &
        (df["First name"] == "")
        &
        (df["Email"] == "")
    )

    df = df[
        ~footer & ~empty
    ].copy()

    df["_row"] = range(len(df))

    # --------------------------------------------------------------
    # Student name
    # --------------------------------------------------------------

    df["Student"] = (
        df["First name"]
        + " "
        + df["Last name"]
    ).str.strip()

    df.loc[
        df["Student"] == "",
        "Student"
    ] = df["Email"]

    # --------------------------------------------------------------
    # Student key
    # --------------------------------------------------------------

    df["key"] = np.where(
        df["Email"] != "",
        df["Email"].str.lower(),
        df["Student"].str.lower()
    )

    # --------------------------------------------------------------
    # TEAM ASSIGNMENT
    # --------------------------------------------------------------

    df["Team"] = df["Student"].apply(
        assign_team
    )

    # --------------------------------------------------------------
    # Fill missing duration from Started/Completed
    # --------------------------------------------------------------

    calc = (
        df["Completed"]
        - df["Started"]
    ).dt.total_seconds()

    df["dur_s"] = (
        df["dur_s"]
        .fillna(calc)
    )

    # --------------------------------------------------------------
    # Finished status
    # --------------------------------------------------------------

    finished_status = (
        df["Status"]
        .str.contains(
            "finish",
            case=False
        )
    )

    in_progress = (
        df["Status"]
        .str.contains(
            "progress|never",
            case=False
        )
    )

    df["Finished"] = (
        finished_status
        |
        (
            df["Completed"].notna()
            & ~in_progress
        )
    )

    # --------------------------------------------------------------
    # Attempt number
    # --------------------------------------------------------------

    df = df.sort_values(
        [
            "key",
            "Started",
            "_row"
        ],
        kind="stable"
    )

    df["Attempt"] = (
        df.groupby("key")
        .cumcount()
        + 1
    )

    df["Time (min)"] = (
        df["dur_s"] / 60
    ).round(2)

    return (
        df.reset_index(drop=True),
        max_grade
    )


# ==========================================================================
# STUDENT SUMMARY
# ==========================================================================

def student_table(df: pd.DataFrame) -> pd.DataFrame:

    rows = []

    for key, g in df.groupby(
        "key",
        sort=False
    ):

        scored = g[
            g["Grade"].notna()
        ]

        best = None

        if not scored.empty:

            best = (
                scored
                .sort_values(
                    ["Grade", "dur_s"],
                    ascending=[
                        False,
                        True
                    ]
                )
                .iloc[0]
            )

        first = (
            scored.iloc[0]
            if not scored.empty
            else None
        )

        last = (
            scored.iloc[-1]
            if not scored.empty
            else None
        )

        rows.append(
            {
                "Student":
                    g["Student"].iloc[0],

                "Email":
                    g["Email"].iloc[0],

                "Team":
                    g["Team"].iloc[0],

                "Attempts":
                    len(g),

                "Best score":
                    best["Grade"]
                    if best is not None
                    else np.nan,

                "Time for best (min)":
                    round(
                        best["dur_s"] / 60,
                        2
                    )
                    if (
                        best is not None
                        and pd.notna(
                            best["dur_s"]
                        )
                    )
                    else np.nan,

                "Best on attempt":
                    int(best["Attempt"])
                    if best is not None
                    else np.nan,

                "1st score":
                    first["Grade"]
                    if first is not None
                    else np.nan,

                "Latest score":
                    last["Grade"]
                    if last is not None
                    else np.nan,

                "Change":
                    (
                        last["Grade"]
                        - first["Grade"]
                    )
                    if len(scored) > 1
                    else np.nan,

                "Average":
                    scored["Grade"].mean()
                    if not scored.empty
                    else np.nan,

                "Total time (min)":
                    round(
                        g["dur_s"].sum() / 60,
                        2
                    )
                    if g["dur_s"].notna().any()
                    else np.nan
            }
        )

    out = pd.DataFrame(rows)

    out = out.sort_values(
        [
            "Best score",
            "Time for best (min)"
        ],
        ascending=[
            False,
            True
        ],
        na_position="last"
    )

    out.insert(
        0,
        "Rank",
        range(1, len(out) + 1)
    )

    return out.reset_index(
        drop=True
    )


# ==========================================================================
# TEAM SUMMARY
# ==========================================================================

def team_summary(
    students: pd.DataFrame,
    df: pd.DataFrame
) -> pd.DataFrame:

    rows = []

    for team in [
        "Apple",
        "Orange"
    ]:

        team_students = students[
            students["Team"] == team
        ]

        team_attempts = df[
            df["Team"] == team
        ]

        scored = team_attempts[
            team_attempts["Grade"].notna()
        ]

        if team_students.empty:
            continue

        # ----------------------------------------------------------
        # Average best score per member
        # ----------------------------------------------------------

        avg_best_score = (
            team_students["Best score"]
            .mean()
        )

        # ----------------------------------------------------------
        # Highest individual score
        # ----------------------------------------------------------

        highest_score = (
            scored["Grade"].max()
            if not scored.empty
            else np.nan
        )

        # ----------------------------------------------------------
        # Average score across all attempts
        # ----------------------------------------------------------

        avg_score = (
            scored["Grade"].mean()
            if not scored.empty
            else np.nan
        )

        # ----------------------------------------------------------
        # Average time per attempt
        # ----------------------------------------------------------

        avg_time = (
            team_attempts["dur_s"].mean()
            if team_attempts["dur_s"].notna().any()
            else np.nan
        )

        # ----------------------------------------------------------
        # Average time for best score
        # ----------------------------------------------------------

        avg_best_time = (
            team_students[
                "Time for best (min)"
            ].mean()
        )

        # ----------------------------------------------------------
        # Improvement
        # ----------------------------------------------------------

        improvements = (
            team_students["Change"]
            .dropna()
        )

        total_improvement = (
            improvements.sum()
            if len(improvements)
            else 0
        )

        avg_improvement = (
            improvements.mean()
            if len(improvements)
            else 0
        )

        rows.append(
            {
                "Team": team,

                "Members":
                    len(team_students),

                "Average best score":
                    round(
                        avg_best_score,
                        2
                    ),

                "Highest score":
                    highest_score,

                "Average score":
                    round(
                        avg_score,
                        2
                    )
                    if pd.notna(avg_score)
                    else np.nan,

                "Average time (min)":
                    round(
                        avg_time / 60,
                        2
                    )
                    if pd.notna(avg_time)
                    else np.nan,

                "Average time for best (min)":
                    round(
                        avg_best_time,
                        2
                    )
                    if pd.notna(avg_best_time)
                    else np.nan,

                "Total improvement":
                    round(
                        total_improvement,
                        2
                    ),

                "Average improvement":
                    round(
                        avg_improvement,
                        2
                    )
            }
        )

    return pd.DataFrame(rows)


# ==========================================================================
# TOP ROWS / TIES
# ==========================================================================

def top_rows(
    df,
    sort_cols,
    ascending
):

    if df.empty:
        return df

    ordered = df.sort_values(
        sort_cols,
        ascending=ascending
    )

    first = ordered.iloc[0]

    same = (
        ordered[sort_cols]
        .fillna(-1)
        == first[sort_cols]
        .fillna(-1)
    ).all(axis=1)

    return ordered[same]


def ties_text(
    tied: pd.DataFrame,
    name_col="Student"
) -> str:

    names = list(
        dict.fromkeys(
            tied[name_col].tolist()
        )
    )[1:]

    if not names:
        return ""

    shown = ", ".join(
        names[:3]
    )

    extra = (
        f" and {len(names) - 3} more"
        if len(names) > 3
        else ""
    )

    return (
        f"Also tied: {shown}{extra}"
    )


def highlight(
    container,
    label,
    name,
    detail,
    note=""
):

    with container.container(
        border=True
    ):

        st.caption(label)

        st.subheader(name)

        st.write(detail)

        if note:
            st.caption(note)


# ==========================================================================
# SAMPLE DATA
# ==========================================================================

def sample_csv() -> str:

    rng = np.random.default_rng(11)

    first_names = [
        "Aparna",
        "Jayalakshmi",
        "Ganga",
        "Jintu",
        "Sreelakshmi",
        "Aiswarya",
        "Nandana",
        "Meera",
        "Rahul",
        "Anjali"
    ]

    last_names = [
        "Nair",
        "Menon",
        "Pillai",
        "Thomas",
        "Kurian",
        "Varma",
        "Das",
        "Iyer"
    ]

    rows = []

    for i in range(36):

        first = first_names[i % 10]

        last = last_names[
            (i // 4) % 8
        ]

        email = (
            f"{first}.{last}{i}@example.com"
            .lower()
        )

        skill = (
            5
            + rng.random() * 8
        )

        attempts = (
            1
            + int(
                rng.random()
                * rng.random()
                * 4.2
            )
        )

        t0 = pd.Timestamp(
            2025,
            3,
            10
            + int(
                rng.integers(0, 5)
            ),
            9
            + int(
                rng.integers(0, 7)
            ),
            int(
                rng.integers(0, 60)
            )
        )

        for a in range(attempts):

            started = (
                t0
                + pd.Timedelta(
                    days=a,
                    minutes=int(
                        rng.integers(
                            0,
                            60
                        )
                    )
                )
            )

            secs = int(
                rng.integers(
                    240,
                    1740
                )
            )

            grade = float(
                np.clip(
                    round(
                        (
                            skill
                            + a
                            * rng.random()
                            * 2.2
                            + (
                                rng.random()
                                - 0.5
                            )
                            * 3
                        )
                        * 2
                    )
                    / 2,
                    0,
                    15
                )
            )

            started_s = (
                started
                .strftime(
                    "%d %B %Y %I:%M %p"
                )
                .lstrip("0")
            )

            done_s = (
                (
                    started
                    + pd.Timedelta(
                        seconds=secs
                    )
                )
                .strftime(
                    "%d %B %Y %I:%M %p"
                )
                .lstrip("0")
            )

            dur_s = (
                f"{secs // 60} mins "
                f"{secs % 60} secs"
            )

            rows.append(
                [
                    last,
                    first,
                    email,
                    "Finished",
                    started_s,
                    done_s,
                    dur_s,
                    f"{grade:.2f}"
                ]
            )

    cols = [
        "Last name",
        "First name",
        "Email address",
        "Status",
        "Started",
        "Completed",
        "Duration",
        "Grade/15.00"
    ]

    df = pd.DataFrame(
        rows,
        columns=cols
    )

    avg = (
        df["Grade/15.00"]
        .astype(float)
        .mean()
    )

    df.loc[len(df)] = [
        "Overall average",
        "",
        "",
        "",
        "",
        "",
        "",
        f"{avg:.2f}"
    ]

    return df.to_csv(
        index=False
    )


# ==========================================================================
# APP
# ==========================================================================

st.title(
    "📝 Quiz Results Dashboard"
)

st.write(
    "Upload your quiz export to see "
    "individual and team performance."
)


# ==========================================================================
# SIDEBAR
# ==========================================================================

with st.sidebar:

    st.header("Data")

    uploaded = st.file_uploader(
        "Quiz results CSV",
        type=["csv"]
    )

    use_sample = st.checkbox(
        "Use sample data",
        value=False
    )

    pass_pct = st.number_input(
        "Pass mark (%)",
        min_value=0,
        max_value=100,
        value=50,
        step=5
    )


# ==========================================================================
# LOAD DATA
# ==========================================================================

if uploaded is not None:

    raw = pd.read_csv(
        uploaded,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig"
    )

    source = uploaded.name

elif use_sample:

    raw = pd.read_csv(
        io.StringIO(
            sample_csv()
        ),
        dtype=str,
        keep_default_na=False
    )

    source = "sample data"

else:

    st.info(
        "Upload a CSV in the sidebar, "
        "or tick 'Use sample data'."
    )

    st.stop()


# ==========================================================================
# PREPARE
# ==========================================================================

try:

    df, max_grade = prepare(raw)

except ValueError as err:

    st.error(str(err))

    st.stop()


if df.empty:

    st.error(
        "The file has no student rows."
    )

    st.stop()


# ==========================================================================
# MAIN DATA
# ==========================================================================

scored = df[
    df["Grade"].notna()
]

students = student_table(
    df
)

team_df = team_summary(
    students,
    df
)

st.caption(
    f"Showing {source}"
)


# ==========================================================================
# TOP RESULT
# ==========================================================================

candidates = scored[
    scored["Finished"]
    |
    scored["dur_s"].notna()
]

best_overall = top_rows(
    candidates
    if not candidates.empty
    else scored,
    ["Grade", "dur_s"],
    [False, True]
)


if not best_overall.empty:

    w = best_overall.iloc[0]

    with st.container(
        border=True
    ):

        c1, c2 = st.columns(
            [1, 3]
        )

        c1.metric(
            "Top score",
            f"{w['Grade']:g} / {max_grade:g}"
        )

        c2.caption(
            "Highest score in the least time"
        )

        c2.subheader(
            w["Student"]
        )

        c2.write(
            f"**{fmt_dur(w['dur_s'])}** "
            f"on attempt **{int(w['Attempt'])}**"
            f" · {w['Email']}"
        )

        if ties_text(best_overall):

            c2.caption(
                ties_text(
                    best_overall
                )
            )


# ==========================================================================
# KPIs
# ==========================================================================

with_score = students[
    students["Best score"].notna()
]

passed = (
    (
        with_score["Best score"]
        / max_grade
        * 100
        >= pass_pct
    ).sum()
    if len(with_score)
    else 0
)

k = st.columns(6)

k[0].metric(
    "Students",
    len(students)
)

k[1].metric(
    "Attempts",
    len(df)
)

k[2].metric(
    f"Average score (of {max_grade:g})",
    (
        f"{scored['Grade'].mean():.2f}"
        if len(scored)
        else "—"
    )
)

k[3].metric(
    "Average time",
    fmt_dur(
        df.loc[
            df["Finished"],
            "dur_s"
        ].mean()
    )
)

k[4].metric(
    f"Passed (≥ {pass_pct}%)",
    (
        f"{passed / len(with_score) * 100:.0f}%"
        if len(with_score)
        else "—"
    )
)

k[5].metric(
    "Unfinished attempts",
    int(
        (~df["Finished"]).sum()
    )
)


# ==========================================================================
# INDIVIDUAL HIGHLIGHTS
# ==========================================================================

st.header(
    "Individual Highlights"
)

st.caption(
    "Ties are broken by the shorter time taken."
)

row1 = st.columns(3)
row2 = st.columns(3)


# Highest score in least time
best = top_rows(
    scored,
    ["Grade", "dur_s"],
    [False, True]
)

if not best.empty:

    b = best.iloc[0]

    highlight(
        row1[0],
        "Highest score in least time",
        b["Student"],
        (
            f"**{b['Grade']:g}** "
            f"in {fmt_dur(b['dur_s'])} "
            f"(attempt {int(b['Attempt'])})"
        ),
        ties_text(best)
    )


# Fastest
fast = top_rows(
    scored[
        scored["Finished"]
        &
        (scored["dur_s"] > 0)
    ],
    ["dur_s"],
    [True]
)

if not fast.empty:

    f = fast.iloc[0]

    highlight(
        row1[1],
        "Fastest to finish",
        f["Student"],
        (
            f"**{fmt_dur(f['dur_s'])}** "
            f"with a score of "
            f"{f['Grade']:g}"
        ),
        ties_text(fast)
    )


# Most attempts
most = top_rows(
    students,
    ["Attempts"],
    [False]
)

if not most.empty:

    m = most.iloc[0]

    highlight(
        row1[2],
        "Most attempts",
        m["Student"],
        (
            f"**{int(m['Attempts'])}** attempts, "
            f"best score "
            f"{m['Best score']:g}"
        ),
        ties_text(most)
    )


# Highest first attempt
first_top = top_rows(
    scored[
        scored["Attempt"] == 1
    ],
    ["Grade", "dur_s"],
    [False, True]
)

if not first_top.empty:

    t = first_top.iloc[0]

    highlight(
        row2[0],
        "Highest score in 1st attempt",
        t["Student"],
        (
            f"**{t['Grade']:g}** "
            f"in {fmt_dur(t['dur_s'])}"
        ),
        ties_text(first_top)
    )


# Most improved individual
improved = students[
    students["Change"].notna()
]

imp = top_rows(
    improved,
    ["Change"],
    [False]
)

if (
    not imp.empty
    and imp.iloc[0]["Change"] > 0
):

    i = imp.iloc[0]

    highlight(
        row2[1],
        "Most improved",
        i["Student"],
        (
            f"**+{i['Change']:.2f}** "
            f"from first to last attempt "
            f"({i['1st score']:g} "
            f"to {i['Latest score']:g})"
        ),
        ties_text(imp)
    )


# Full marks
full = students[
    students["Best score"] >= max_grade
]

names = (
    ", ".join(
        full["Student"].head(4)
    )
    +
    (
        f" and {len(full) - 4} more"
        if len(full) > 4
        else ""
    )
)

highlight(
    row2[2],
    "Full marks",
    (
        f"{len(full)} student"
        f"{'s' if len(full) != 1 else ''}"
    ),
    (
        names
        if len(full)
        else f"Nobody reached {max_grade:g} yet"
    )
)


# ==========================================================================
# TEAM PERFORMANCE
# ==========================================================================

st.header(
    "🍎 Apple vs 🍊 Orange"
)

st.caption(
    "Teams are assigned automatically from the "
    "predefined member list. Team comparison uses "
    "averages because Apple has 4 members and "
    "Orange has 3."
)


# --------------------------------------------------------------------------
# Team Summary Table
# --------------------------------------------------------------------------

st.subheader(
    "Team Summary"
)

display_team_df = team_df.copy()

display_team_df = display_team_df[
    [
        "Team",
        "Members",
        "Average best score",
        "Highest score",
        "Average score",
        "Average time (min)",
        "Average time for best (min)",
        "Average improvement"
    ]
]

st.dataframe(
    display_team_df,
    hide_index=True,
    width="stretch"
)


# ==========================================================================
# TEAM METRICS
# ==========================================================================

team_cols = st.columns(2)

for idx, team in enumerate(
    ["Apple", "Orange"]
):

    team_row = team_df[
        team_df["Team"] == team
    ]

    if team_row.empty:
        continue

    r = team_row.iloc[0]

    icon = (
        "🍎"
        if team == "Apple"
        else "🍊"
    )

    with team_cols[idx]:

        with st.container(
            border=True
        ):

            st.subheader(
                f"{icon} {team} Team"
            )

            st.metric(
                "Members",
                int(r["Members"])
            )

            st.metric(
                "Average best score",
                (
                    f"{r['Average best score']:.2f}"
                    f" / {max_grade:g}"
                )
            )

            st.metric(
                "Average time",
                (
                    f"{r['Average time (min)']:.2f}"
                    " min"
                )
            )

            st.metric(
                "Average improvement",
                (
                    f"+{r['Average improvement']:.2f}"
                )
            )


# ==========================================================================
# SCORE + TIME COMPARISON
# ==========================================================================

st.subheader(
    "🏆 Score + Time Comparison"
)

if len(team_df) == 2:

    apple = team_df[
        team_df["Team"] == "Apple"
    ].iloc[0]

    orange = team_df[
        team_df["Team"] == "Orange"
    ].iloc[0]

    apple_score = (
        apple["Average best score"]
    )

    orange_score = (
        orange["Average best score"]
    )

    apple_time = (
        apple["Average time (min)"]
    )

    orange_time = (
        orange["Average time (min)"]
    )

    # --------------------------------------------------------------
    # Higher score AND less time
    # --------------------------------------------------------------

    if (
        apple_score > orange_score
        and apple_time < orange_time
    ):

        st.success(
            f"🍎 Apple achieved the higher "
            f"average best score "
            f"({apple_score:.2f}) "
            f"and did so in less average time "
            f"({apple_time:.2f} min)."
        )

    elif (
        orange_score > apple_score
        and orange_time < apple_time
    ):

        st.success(
            f"🍊 Orange achieved the higher "
            f"average best score "
            f"({orange_score:.2f}) "
            f"and did so in less average time "
            f"({orange_time:.2f} min)."
        )

    else:

        st.info(
            "There is no single team that has both "
            "a higher average best score and a "
            "lower average time. The two measures "
            "should therefore be considered separately."
        )

        comparison_cols = st.columns(2)

        with comparison_cols[0]:

            if apple_score > orange_score:

                st.write(
                    f"🍎 Apple has the higher "
                    f"average best score: "
                    f"**{apple_score:.2f}**"
                )

            elif orange_score > apple_score:

                st.write(
                    f"🍊 Orange has the higher "
                    f"average best score: "
                    f"**{orange_score:.2f}**"
                )

            else:

                st.write(
                    "Both teams have the same "
                    "average best score."
                )

        with comparison_cols[1]:

            if apple_time < orange_time:

                st.write(
                    f"🍎 Apple has the lower "
                    f"average time: "
                    f"**{apple_time:.2f} min**"
                )

            elif orange_time < apple_time:

                st.write(
                    f"🍊 Orange has the lower "
                    f"average time: "
                    f"**{orange_time:.2f} min**"
                )

            else:

                st.write(
                    "Both teams have the same "
                    "average time."
                )


# ==========================================================================
# TEAM IMPROVEMENT
# ==========================================================================

st.subheader(
    "📈 Team Improvement"
)

if len(team_df) == 2:

    apple_imp = team_df.loc[
        team_df["Team"] == "Apple",
        "Average improvement"
    ].iloc[0]

    orange_imp = team_df.loc[
        team_df["Team"] == "Orange",
        "Average improvement"
    ].iloc[0]

    c1, c2 = st.columns(2)

    with c1:

        st.metric(
            "🍎 Apple average improvement",
            f"+{apple_imp:.2f}"
        )

    with c2:

        st.metric(
            "🍊 Orange average improvement",
            f"+{orange_imp:.2f}"
        )

    if apple_imp > orange_imp:

        st.success(
            f"🍎 Apple had the larger average "
            f"improvement: +{apple_imp:.2f} marks."
        )

    elif orange_imp > apple_imp:

        st.success(
            f"🍊 Orange had the larger average "
            f"improvement: +{orange_imp:.2f} marks."
        )

    else:

        st.info(
            "Both teams had the same "
            "average improvement."
        )


# ==========================================================================
# TEAM PERFORMANCE CHART
# ==========================================================================


# ==========================================================================
# TEAM MEMBERS
# ==========================================================================

st.subheader(
    "👥 Team Members"
)

team_view = students[
    [
        "Team",
        "Student",
        "Attempts",
        "Best score",
        "Time for best (min)",
        "1st score",
        "Latest score",
        "Change"
    ]
].copy()

team_view = team_view.sort_values(
    [
        "Team",
        "Best score"
    ],
    ascending=[
        True,
        False
    ]
)

st.dataframe(
    team_view,
    hide_index=True,
    width="stretch"
)


# ==========================================================================
# TEAM MEMBER LIST
# ==========================================================================

st.subheader(
    "👥 Team Composition"
)

apple_members = [
    "Aparna",
    "Jayalakshmi",
    "Ganga",
    "Jintu"
]

orange_members = [
    "SreelakshmiAnilkumar",
    "Aiswarya",
    "Nandana"
]

c1, c2 = st.columns(2)

with c1:

    st.markdown(
        "### 🍎 Apple"
    )

    for member in apple_members:

        st.write(
            f"• {member}"
        )

with c2:

    st.markdown(
        "### 🍊 Orange"
    )

    for member in orange_members:

        st.write(
            f"• {member}"
        )


# ==========================================================================
# UNASSIGNED STUDENTS
# ==========================================================================

unassigned = students[
    students["Team"] == "Unassigned"
]

if not unassigned.empty:

    st.subheader(
        "⚠️ Unassigned Students"
    )

    st.caption(
        "These names were not found in the "
        "Apple/Orange team list."
    )

    st.dataframe(
        unassigned[
            [
                "Student",
                "Email",
                "Best score",
                "Attempts"
            ]
        ],
        hide_index=True,
        width="stretch"
    )


# ==========================================================================
# BEST RESULT IN EACH ATTEMPT
# ==========================================================================

st.header(
    "Best Result in Each Attempt"
)

st.caption(
    "Attempts are numbered per student "
    "in the order they were started."
)

rows = []

for n in sorted(
    scored["Attempt"].unique()
):

    sub = scored[
        scored["Attempt"] == n
    ]

    tw = top_rows(
        sub,
        ["Grade", "dur_s"],
        [False, True]
    )

    w = tw.iloc[0]

    rows.append(
        {
            "Attempt":
                ordinal(int(n)),

            "Submitted":
                len(sub),

            "Average":
                round(
                    sub["Grade"].mean(),
                    2
                ),

            "Lowest":
                sub["Grade"].min(),

            "Top scorer":
                w["Student"]
                +
                (
                    f" (+{len(tw) - 1} tied)"
                    if len(tw) > 1
                    else ""
                ),

            "Score":
                w["Grade"],

            "Time":
                fmt_dur(
                    w["dur_s"]
                )
        }
    )

st.dataframe(
    pd.DataFrame(rows),
    hide_index=True,
    width="stretch"
)


# ==========================================================================
# DETAILS
# ==========================================================================

st.header(
    "Details"
)

query = st.text_input(
    "Search name or email"
)

tab1, tab2 = st.tabs(
    [
        "Students",
        "All attempts"
    ]
)


# --------------------------------------------------------------------------
# STUDENT TAB
# --------------------------------------------------------------------------

with tab1:

    view = students

    if query:

        mask = (
            view["Student"]
            .str.contains(
                query,
                case=False,
                na=False
            )
            |
            view["Email"]
            .str.contains(
                query,
                case=False,
                na=False
            )
        )

        view = view[mask]

    st.dataframe(
        view,
        hide_index=True,
        width="stretch"
    )

    st.download_button(
        "Download student summary (CSV)",
        students.to_csv(
            index=False
        ),
        file_name="student_summary.csv",
        mime="text/csv"
    )


# --------------------------------------------------------------------------
# ALL ATTEMPTS TAB
# --------------------------------------------------------------------------

with tab2:

    view = df[
        [
            "Team",
            "Student",
            "Email",
            "Attempt",
            "Status",
            "Started",
            "Completed",
            "Time (min)",
            "Grade"
        ]
    ]

    if query:

        mask = (
            view["Student"]
            .str.contains(
                query,
                case=False,
                na=False
            )
            |
            view["Email"]
            .str.contains(
                query,
                case=False,
                na=False
            )
        )

        view = view[mask]

    st.dataframe(
        view,
        hide_index=True,
        width="stretch"
    )


# ==========================================================================
# TEAM SUMMARY DOWNLOAD
# ==========================================================================

st.subheader(
    "📥 Downloads"
)

st.download_button(
    "Download team summary (CSV)",
    team_df.to_csv(
        index=False
    ),
    file_name="team_summary.csv",
    mime="text/csv"
)

