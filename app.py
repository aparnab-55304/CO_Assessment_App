import streamlit as st
import pandas as pd

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(
    page_title="Quiz Dashboard",
    page_icon="🏆",
    layout="wide"
)

st.title("🏆 Quiz Performance Dashboard")
st.write("Simple summary of participant scores and time.")

# -----------------------------
# LOAD DATA
# -----------------------------
uploaded_file = st.file_uploader(
    "Upload your quiz CSV file",
    type=["csv"]
)

if uploaded_file is not None:

    df = pd.read_csv(uploaded_file)

    st.success("Data loaded successfully!")

    # -----------------------------
    # SHOW COLUMN NAMES
    # -----------------------------
    st.write("Columns found in your data:")
    st.write(list(df.columns))

    # ------------------------------------------------
    # CHANGE THESE IF YOUR COLUMN NAMES ARE DIFFERENT
    # ------------------------------------------------
    name_col = "name"
    score_col = "grade"
    time_col = "time"

    # -----------------------------
    # CHECK COLUMNS
    # -----------------------------
    missing = []

    for col in [name_col, score_col, time_col]:
        if col not in df.columns:
            missing.append(col)

    if missing:
        st.error(
            f"These columns were not found: {missing}. "
            "Change the column names near the top of the code."
        )
        st.stop()

    # -----------------------------
    # CLEAN DATA
    # -----------------------------
    df[score_col] = pd.to_numeric(
        df[score_col], errors="coerce"
    )

    # Convert time to seconds if possible
    def convert_time(x):

        if pd.isna(x):
            return None

        x = str(x)

        try:
            # HH:MM:SS
            parts = x.split(":")

            if len(parts) == 3:
                h, m, s = map(float, parts)
                return h * 3600 + m * 60 + s

            # MM:SS
            elif len(parts) == 2:
                m, s = map(float, parts)
                return m * 60 + s

            # Already numeric
            else:
                return float(x)

        except:
            return None

    df["Time_Seconds"] = df[time_col].apply(convert_time)

    # -----------------------------
    # BASIC STATISTICS
    # -----------------------------
    total_participants = len(df)

    highest_score = df[score_col].max()

    full_score = df[df[score_col] == 15]

    fastest = df.sort_values(
        "Time_Seconds"
    ).head(5)

    winners = df.sort_values(
        by=[score_col, "Time_Seconds"],
        ascending=[False, True]
    ).head(5)

    # -----------------------------
    # METRICS
    # -----------------------------
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "👥 Participants",
        total_participants
    )

    col2.metric(
        "🏆 Highest Score",
        f"{highest_score:.0f}/15"
    )

    col3.metric(
        "🎯 Full Scores",
        len(full_score)
    )

    if df["Time_Seconds"].notna().any():
        fastest_time = df["Time_Seconds"].min()

        minutes = int(fastest_time // 60)
        seconds = int(fastest_time % 60)

        col4.metric(
            "⚡ Fastest Time",
            f"{minutes}:{seconds:02d}"
        )

    # -----------------------------
    # WINNERS
    # -----------------------------
    st.header("🏆 Top Participants")

    winners_display = winners[
        [name_col, score_col, time_col]
    ].copy()

    winners_display.columns = [
        "Name",
        "Score",
        "Time"
    ]

    winners_display.insert(
        0,
        "Rank",
        range(1, len(winners_display) + 1)
    )

    st.dataframe(
        winners_display,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------
    # FASTEST PARTICIPANTS
    # -----------------------------
    st.header("⚡ Fastest Participants")

    fastest_display = fastest[
        [name_col, score_col, time_col]
    ].copy()

    fastest_display.columns = [
        "Name",
        "Score",
        "Time"
    ]

    fastest_display.insert(
        0,
        "Rank",
        range(1, len(fastest_display) + 1)
    )

    st.dataframe(
        fastest_display,
        use_container_width=True,
        hide_index=True
    )

    # -----------------------------
    # FULL SCORE
    # -----------------------------
    st.header("🎯 Participants with 15/15")

    if len(full_score) > 0:

        full_display = full_score[
            [name_col, score_col, time_col]
        ].copy()

        full_display.columns = [
            "Name",
            "Score",
            "Time"
        ]

        st.dataframe(
            full_display,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info("No participant scored 15/15.")

    # -----------------------------
    # ALL PARTICIPANTS
    # -----------------------------
    st.header("📋 All Participants")

    all_display = df[
        [name_col, score_col, time_col]
    ].copy()

    all_display.columns = [
        "Name",
        "Score",
        "Time"
    ]

    st.dataframe(
        all_display,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("⬆️ Upload your quiz CSV file to open the dashboard.")
