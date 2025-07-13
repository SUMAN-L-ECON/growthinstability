import streamlit as st
import pandas as pd
import numpy as np
import io
from sklearn.linear_model import LinearRegression
import base64
import matplotlib.pyplot as plt
from fpdf import FPDF

# Set page config
st.set_page_config(page_title="Growth & Instability Analyser — SumanEcon-UAS(B)", layout="centered")
st.title("📊 Growth & Instability Analyser — SumanEcon-UAS(B)")

st.markdown("""
This app computes **Compound Annual Growth Rate (CAGR)** and **Cuddy-Della Valle Instability Index (CDVI)** for selected numeric variables.
Upload your dataset and follow the guided steps below.
""")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV, XLS, or XLSX file", type=["csv", "xls", "xlsx"])

if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)

        st.success("File uploaded successfully!")
        st.subheader("Data Preview")
        st.dataframe(df.head())

        # Convert object columns to numeric/date if possible
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    try:
                        df[col] = pd.to_numeric(df[col])
                    except:
                        pass

        # Select time column
        time_col = st.selectbox("Select Year/Date/Time Column (Independent Variable)", df.columns)

        # Convert time column to numeric index if datetime or year
        if np.issubdtype(df[time_col].dtype, np.datetime64):
            df = df.sort_values(by=time_col)
            df['TimeIndex'] = range(1, len(df)+1)
        else:
            try:
                df[time_col] = pd.to_numeric(df[time_col])
                df = df.sort_values(by=time_col)
                df['TimeIndex'] = df[time_col] - df[time_col].min() + 1
            except:
                st.error("Selected time column could not be converted to numeric or datetime.")

        numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col != 'TimeIndex']

        selected_cols = st.multiselect("Select numeric columns for analysis", options=numeric_cols, default=numeric_cols)

        if selected_cols:
            # Handle missing values
            df[selected_cols] = df[selected_cols].interpolate(method='linear')
            df = df.dropna(subset=['TimeIndex'] + selected_cols)

            results = []
            for col in selected_cols:
                y = df[col]
                t = df['TimeIndex']
                X = t.values.reshape(-1, 1)

                # CAGR
                begin = y.iloc[0]
                end = y.iloc[-1]
                n = len(y) - 1
                cagr = ((end / begin) ** (1 / n) - 1) * 100 if begin > 0 and end > 0 else np.nan

                # CDVI
                model = LinearRegression().fit(X, np.log(y + 1e-9))
                r_squared = model.score(X, np.log(y + 1e-9))
                cv = np.std(y) / np.mean(y) * 100 if np.mean(y) != 0 else np.nan
                cdvi = cv * np.sqrt(1 - r_squared)

                results.append({
                    'Variable': col,
                    'CAGR (%)': round(cagr, 2),
                    'CV (%)': round(cv, 2),
                    'R-squared': round(r_squared, 4),
                    'CDVI (%)': round(cdvi, 2)
                })

            results_df = pd.DataFrame(results)
            st.subheader("Analysis Results")
            st.dataframe(results_df)

            # Download as Excel
            def to_excel(df):
                output = io.BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                df.to_excel(writer, index=False, sheet_name='Results')
                writer.close()
                processed_data = output.getvalue()
                return processed_data

            excel_data = to_excel(results_df)
            st.download_button(label='📥 Download Results as Excel',
                               data=excel_data,
                               file_name='Growth_Instability_Results.xlsx')

            # Download as PDF
            class PDF(FPDF):
                def header(self):
                    self.set_font('Arial', 'B', 12)
                    self.cell(0, 10, 'Growth & Instability Analysis Results', ln=True, align='C')
                    self.ln(10)

                def footer(self):
                    self.set_y(-15)
                    self.set_font('Arial', 'I', 8)
                    self.cell(0, 10, 'For more, collaborate with sumanecon.uas@outlook.in', 0, 0, 'C')

                def table(self, data):
                    self.set_font("Arial", size=10)
                    col_width = self.epw / len(data.columns)
                    for col in data.columns:
                        self.cell(col_width, 10, str(col), border=1)
                    self.ln()
                    for i in range(len(data)):
                        for val in data.iloc[i]:
                            self.cell(col_width, 10, str(val), border=1)
                        self.ln()

            pdf = PDF()
            pdf.add_page()
            pdf.table(results_df)
            pdf_output = io.BytesIO()
            pdf.output(pdf_output)
            st.download_button(label="📄 Download Results as PDF", data=pdf_output.getvalue(), file_name="Growth_Instability_Results.pdf")

    except Exception as e:
        st.error(f"❌ Error: {e}")

# Footer
st.markdown("---")
st.markdown("<center><small>For more, collaborate with sumanecon.uas@outlook.in</small></center>", unsafe_allow_html=True)
