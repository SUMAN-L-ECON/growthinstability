import streamlit as st
import pandas as pd
import numpy as np
from scipy.interpolate import interp1d

# Function to calculate CAGR
def calculate_cagr(data, column):
    start_value = data[column].iloc[0]
    end_value = data[column].iloc[-1]
    years = (data.index[-1] - data.index[0]).days / 365.25
    cagr = (end_value / start_value) ** (1 / (years / 1)) - 1
    return cagr

# Function to calculate CDVI (Cuddy Della Valle Index)
def calculate_cdvi(data, column):
    mean_value = data[column].mean()
    std_dev = data[column].std()
    cdvi = (std_dev / mean_value) * 100
    return cdvi

# Function to perform linear interpolation
def linear_interpolation(data, column):
    x = np.arange(len(data))
    y = data[column].values
    mask = ~np.isnan(y)
    f = interp1d(x[mask], y[mask], fill_value="extrapolate")
    interpolated_values = f(x)
    data[column] = interpolated_values
    return data

# Main function
def main():
    st.title("Growth&Instability analyser--SumanEcon-UAS(B)")
    st.markdown("For more collaborate with sumanecon.uas@outlook.in")

    # Upload file
    uploaded_file = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xls", "xlsx"])

    if uploaded_file is not None:
        # Read file
        if uploaded_file.type == "text/csv":
            data = pd.read_csv(uploaded_file)
        else:
            data = pd.read_excel(uploaded_file)

        # Check data types and transform if required
        for column in data.columns:
            if data[column].dtype == "object":
                try:
                    data[column] = pd.to_datetime(data[column])
                except ValueError:
                    try:
                        data[column] = pd.to_numeric(data[column])
                    except ValueError:
                        pass

        # Select numeric columns
        numeric_columns = [column for column in data.columns if data[column].dtype in ["int64", "float64"]]

        # Select Year/Date/Time column
        date_columns = [column for column in data.columns if data[column].dtype == "datetime64[ns]"]
        if date_columns:
            date_column = st.selectbox("Select Year/Date/Time column", date_columns)
            data.set_index(date_column, inplace=True)
        else:
            st.error("No date column found")
            return

        # Select columns for analysis
        columns_to_analyze = st.multiselect("Select columns for analysis", numeric_columns, default=numeric_columns)

        if columns_to_analyze:
            # Handle missing values
            for column in columns_to_analyze:
                if data[column].isnull().any():
                    data = linear_interpolation(data, column)

            # Calculate CAGR and CDVI
            results = []
            for column in columns_to_analyze:
                cagr = calculate_cagr(data, column)
                cdvi = calculate_cdvi(data, column)
                results.append([column, cagr, cdvi])

            # Create results table
            results_df = pd.DataFrame(results, columns=["Column", "CAGR", "CDVI (Instability)"])

            # Display results table
            st.write(results_df)

            # Download results
            col1, col2 = st.columns(2)
            col1.download_button(
                label="Download results as Excel",
                data=results_df.to_excel(index=False),
                file_name="growth_and_instability_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            col2.download_button(
                label="Download results as PDF",
                data=results_df.to_csv(index=False).encode("utf-8"),
                file_name="growth_and_instability_results.pdf",
                mime="application/pdf"
            )

if __name__ == "__main__":
    main()
