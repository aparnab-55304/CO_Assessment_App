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
