import streamlit as st
import pandas as pd

# App title
st.title("CO Assessment App")

st.write("Upload your assessment data file and analyze it.")

# File uploader
uploaded_file = st.file_uploader(
    "Choose a CSV or Excel file",
    type=["csv", "xlsx"]
)

if uploaded_file is not None:

    # Read file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)

    else:
        df = pd.read_excel(uploaded_file)

    st.success("File uploaded successfully!")

    # Display data
    st.subheader("Data Preview")
    st.dataframe(df)

    # Dataset information
    st.subheader("Dataset Information")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Number of Rows",
            df.shape[0]
        )

    with col2:
        st.metric(
            "Number of Columns",
            df.shape[1]
        )

    # Summary statistics
    st.subheader("Summary Statistics")

    st.write(df.describe())