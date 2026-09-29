# ==========================================================================
# IMPROVEMENT CHART
# ==========================================================================

st.header("📈 Student Improvement Analysis")

st.caption(
    "Comparison of each student's first and latest scored attempt. "
    "Improvement is calculated directly from the uploaded CSV."
)

# --------------------------------------------------------------------------
# Prepare improvement data
# --------------------------------------------------------------------------

improvement_df = students[
    [
        "Team",
        "Student",
        "Attempts",
        "1st score",
        "Latest score",
        "Change",
        "Best score",
        "Average",
        "Time for best (min)"
    ]
].copy()

# Keep only students having at least a first and latest score
improvement_df = improvement_df[
    improvement_df["1st score"].notna()
    & improvement_df["Latest score"].notna()
].copy()

# Remove students where improvement cannot be calculated
improvement_df = improvement_df[
    improvement_df["Change"].notna()
].copy()

# Sort by improvement
improvement_df = improvement_df.sort_values(
    "Change",
    ascending=False
).reset_index(drop=True)


# ==========================================================================
# MAIN IMPROVEMENT CHART
# ==========================================================================

if not improvement_df.empty:

    fig = px.bar(
        improvement_df,
        x="Student",
        y=["1st score", "Latest score"],
        barmode="group",
        text_auto=".2f",
        title="First Score vs Latest Score",
        labels={
            "value": f"Score / {max_grade:g}",
            "variable": "Score Type",
            "Student": "Student"
        },
        hover_data={
            "Team": True,
            "Attempts": True,
            "1st score": ":.2f",
            "Latest score": ":.2f",
            "Change": ":.2f",
            "Best score": ":.2f",
            "Average": ":.2f",
            "Time for best (min)": ":.2f"
        }
    )

    fig.update_traces(
        textposition="outside",
        cliponaxis=False
    )

    fig.update_layout(
        height=600,
        xaxis_title="Student",
        yaxis_title=f"Score / {max_grade:g}",
        legend_title="Score",
        hovermode="x unified",
        margin=dict(
            t=80,
            b=100,
            l=60,
            r=40
        )
    )

    fig.update_yaxes(
        range=[
            0,
            max(
                max_grade,
                float(
                    improvement_df[
                        ["1st score", "Latest score"]
                    ].max().max()
                )
            ) * 1.15
        ]
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    # ----------------------------------------------------------------------
    # Improvement labels
    # ----------------------------------------------------------------------

    st.subheader("📊 Improvement by Student")

    # Create a readable improvement label
    improvement_df["Improvement"] = improvement_df["Change"].apply(
        lambda x: f"+{x:.2f}" if x > 0
        else f"{x:.2f}"
    )

    # Add percentage improvement
    improvement_df["Improvement %"] = np.where(
        improvement_df["1st score"] != 0,
        (
            improvement_df["Change"]
            / improvement_df["1st score"]
            * 100
        ),
        np.nan
    )

    improvement_df["Improvement %"] = (
        improvement_df["Improvement %"].round(2)
    )


    # ----------------------------------------------------------------------
    # Detailed improvement table
    # ----------------------------------------------------------------------

    display_improvement = improvement_df[
        [
            "Team",
            "Student",
            "Attempts",
            "1st score",
            "Latest score",
            "Improvement",
            "Improvement %",
            "Best score",
            "Average",
            "Time for best (min)"
        ]
    ].copy()

    display_improvement = display_improvement.rename(
        columns={
            "1st score": "First Score",
            "Latest score": "Latest Score",
            "Improvement": "Improvement",
            "Improvement %": "Improvement (%)",
            "Best score": "Best Score",
            "Time for best (min)": "Time for Best (min)"
        }
    )

    st.dataframe(
        display_improvement,
        hide_index=True,
        width="stretch"
    )


    # ----------------------------------------------------------------------
    # Improvement summary metrics
    # ----------------------------------------------------------------------

    st.subheader("📌 Improvement Summary")

    positive = improvement_df[
        improvement_df["Change"] > 0
    ]

    unchanged = improvement_df[
        improvement_df["Change"] == 0
    ]

    decreased = improvement_df[
        improvement_df["Change"] < 0
    ]

    total_improvement = improvement_df["Change"].sum()

    average_improvement = improvement_df["Change"].mean()

    highest_improvement = improvement_df["Change"].max()

    lowest_improvement = improvement_df["Change"].min()

    summary_cols = st.columns(5)

    summary_cols[0].metric(
        "Students Improved",
        len(positive)
    )

    summary_cols[1].metric(
        "No Change",
        len(unchanged)
    )

    summary_cols[2].metric(
        "Score Decreased",
        len(decreased)
    )

    summary_cols[3].metric(
        "Average Improvement",
        f"{average_improvement:+.2f}"
    )

    summary_cols[4].metric(
        "Total Improvement",
        f"{total_improvement:+.2f}"
    )


    # ----------------------------------------------------------------------
    # Most improved student
    # ----------------------------------------------------------------------

    if not positive.empty:

        most_improved = positive.iloc[0]

        st.success(
            f"📈 **Most improved student:** "
            f"{most_improved['Student']} — "
            f"improved by **+{most_improved['Change']:.2f} marks** "
            f"from {most_improved['1st score']:.2f} "
            f"to {most_improved['Latest score']:.2f}."
        )


else:

    st.info(
        "Improvement cannot be calculated yet. "
        "Students need at least two scored attempts."
    )
    # ==========================================================================
# DIRECT IMPROVEMENT CHART
# ==========================================================================

if not improvement_df.empty:

    improvement_chart = px.bar(
        improvement_df.sort_values(
            "Change",
            ascending=True
        ),
        x="Change",
        y="Student",
        orientation="h",
        text="Change",
        title="📈 Improvement from First Attempt to Latest Attempt",
        labels={
            "Change": "Change in Score (marks)",
            "Student": "Student"
        },
        hover_data={
            "Team": True,
            "Attempts": True,
            "1st score": ":.2f",
            "Latest score": ":.2f",
            "Best score": ":.2f",
            "Average": ":.2f",
            "Time for best (min)": ":.2f"
        }
    )

    improvement_chart.update_traces(
        texttemplate="%{text:+.2f}",
        textposition="outside",
        cliponaxis=False
    )

    improvement_chart.update_layout(
        height=max(
            450,
            len(improvement_df) * 45
        ),
        xaxis_title="Improvement in Marks",
        yaxis_title="Student",
        hovermode="y unified",
        margin=dict(
            l=120,
            r=80,
            t=80,
            b=60
        )
    )

    st.plotly_chart(
        improvement_chart,
        use_container_width=True
    )
