import streamlit as st
import pandas as pd

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="Quiz Performance Dashboard",
    page_icon="📊",
    layout="wide"
)

# -----------------------------
# Title
# -----------------------------
st.title("📊 Quiz Performance Dashboard")

st.write(
    "Upload a CSV or Excel worksheet to analyze quiz performance "
    "across multiple attempts."
)

# -----------------------------
# File upload
# -----------------------------
uploaded_file = st.file_uploader(
    "📁 Upload your quiz worksheet",
    type=["csv", "xlsx"]
)

# -----------------------------
# Read uploaded file
# -----------------------------
if uploaded_file is not None:

    try:

        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)

        else:
            df = pd.read_excel(uploaded_file)

        st.success("✅ File uploaded successfully!")

        # -----------------------------
        # Basic information
        # -----------------------------
        st.subheader("📋 Dataset Overview")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Total Attempts",
                len(df)
            )

        with col2:
            st.metric(
                "Total Columns",
                len(df.columns)
            )

        # Find name column
        if "First name" in df.columns and "Last name" in df.columns:

            df["Participant"] = (
                df["First name"].fillna("").astype(str)
                + " "
                + df["Last name"].fillna("").astype(str)
            ).str.strip()

            number_of_people = df["Participant"].nunique()

        elif "First name" in df.columns:

            df["Participant"] = df["First name"].fillna("").astype(str)

            number_of_people = df["Participant"].nunique()

        else:
            number_of_people = 0

        with col3:
            st.metric(
                "Participants",
                number_of_people
            )

        # -----------------------------
        # Data preview
        # -----------------------------
        st.subheader("🔎 Data Preview")

        st.dataframe(
            df,
            use_container_width=True
        )

        # -----------------------------
        # Score analysis
        # -----------------------------
        if "Grade/15.00" in df.columns:

            # Convert score to numeric
            df["Score"] = pd.to_numeric(
                df["Grade/15.00"],
                errors="coerce"
            )

            st.subheader("🏆 Overall Performance")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Highest Score",
                    f"{df['Score'].max():.0f}/15"
                )

            with col2:
                st.metric(
                    "Lowest Score",
                    f"{df['Score'].min():.0f}/15"
                )

            with col3:
                st.metric(
                    "Average Score",
                    f"{df['Score'].mean():.2f}/15"
                )

            with col4:
                perfect_scores = (df["Score"] == 15).sum()

                st.metric(
                    "15/15 Attempts",
                    perfect_scores
                )

        # -----------------------------
        # Participant summary
        # -----------------------------
        if "Participant" in df.columns and "Score" in df.columns:

            st.subheader("👤 Participant Performance")

            participant_summary = (
                df.groupby("Participant")
                .agg(
                    Attempts=("Score", "count"),
                    Average_Score=("Score", "mean"),
                    Highest_Score=("Score", "max"),
                    Lowest_Score=("Score", "min"),
                    Perfect_15=("Score", lambda x: (x == 15).sum())
                )
                .reset_index()
            )

            participant_summary["Average_Score"] = (
                participant_summary["Average_Score"].round(2)
            )

            participant_summary = participant_summary.sort_values(
                "Average_Score",
                ascending=False
            )

            st.dataframe(
                participant_summary,
                use_container_width=True
            )

        # -----------------------------
        # Top performer
        # -----------------------------
        if "Participant" in df.columns and "Score" in df.columns:

            st.subheader("🥇 Top Performer")

            highest_average = participant_summary.iloc[0]

            st.success(
                f"**{highest_average['Participant']}** "
                f"has the highest average score of "
                f"**{highest_average['Average_Score']}/15** "
                f"across {highest_average['Attempts']} attempt(s)."
            )

        # -----------------------------
        # Most frequent 15/15
        # -----------------------------
        if "Participant" in df.columns and "Score" in df.columns:

            perfect_summary = participant_summary[
                participant_summary["Perfect_15"] > 0
            ].sort_values(
                "Perfect_15",
                ascending=False
            )

            st.subheader("🏆 Most Frequent 15/15 Performer")

            if len(perfect_summary) > 0:

                top_15 = perfect_summary.iloc[0]

                st.success(
                    f"**{top_15['Participant']}** obtained "
                    f"**15/15 {int(top_15['Perfect_15'])} time(s)**."
                )

                st.dataframe(
                    perfect_summary,
                    use_container_width=True
                )

            else:

                st.info("No participant has obtained 15/15 yet.")

    except Exception as e:

        st.error(
            f"❌ There was an error reading the file: {e}"
        )

else:

    st.info(
        "👆 Upload your CSV or Excel worksheet above to begin."
    )
