import streamlit as st
import pandas as pd
from io import BytesIO
import os

st.set_page_config(page_title="Student Filter Tool v2", page_icon="🎓", layout="centered")
st.title("🎓 Student Filter Tool — Multi-Column Matching")

st.write("""
Upload your **main student dataset** (large file) and a **search file** (event signup, attendance, etc.).
You can match on one or more columns, such as *Banner ID*, *Email*, or *Name*.
""")

# ---------- Helper: load Excel/CSV safely ----------
def load_file(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext == ".csv":
        return pd.read_csv(file)
    elif ext in [".xlsx", ".xls"]:
        try:
            return pd.read_excel(file, engine="openpyxl")
        except Exception:
            return pd.read_excel(file, engine="xlrd")
    else:
        st.error(f"❌ Unsupported file format: {ext}")
        st.stop()

# ---------- File uploads ----------
main_file = st.file_uploader("📘 Upload main student file", type=["xlsx", "xls", "csv"])
search_file = st.file_uploader("📗 Upload file with students to search for", type=["xlsx", "xls", "csv"])

if main_file and search_file:
    df_main = load_file(main_file)
    df_search = load_file(search_file)

    df_main.columns = df_main.columns.str.strip()
    df_search.columns = df_search.columns.str.strip()

    st.success(f"✅ Files loaded successfully.")
    st.write(f"Main file: {len(df_main)} rows | Search file: {len(df_search)} rows")

    # ---------- Select matching columns ----------
    st.subheader("🔗 Select columns to match")

    col1, col2 = st.columns(2)
    with col1:
        main_cols = st.multiselect("Select matching column(s) from main file", df_main.columns)
    with col2:
        search_cols = st.multiselect("Select corresponding column(s) from search file", df_search.columns)

    if main_cols and search_cols:
        if len(main_cols) != len(search_cols):
            st.error("⚠️ The number of selected columns must be equal on both sides.")
        else:
            if st.button("Filter Records"):
                # ---------- Normalize types ----------
                for m, s in zip(main_cols, search_cols):
                    df_main[m] = df_main[m].astype(str).str.strip().str.lower()
                    df_search[s] = df_search[s].astype(str).str.strip().str.lower()

                # ---------- Perform merge ----------
                merged = pd.merge(
                    df_main,
                    df_search,
                    left_on=main_cols,
                    right_on=search_cols,
                    how="inner",
                )

                # ---------- Identify missing entries ----------
                mask = pd.Series([True] * len(df_search))
                for m, s in zip(main_cols, search_cols):
                    mask &= df_search[s].isin(df_main[m])
                missing = df_search[~mask]

                # ---------- Display results ----------
                st.success(f"✅ Found {len(merged)} matching records.")
                st.dataframe(merged.head(20))

                if not missing.empty:
                    st.warning(f"⚠️ {len(missing)} entries from search file not found in main file.")
                    st.dataframe(missing.head(10))

                # ---------- Download buttons ----------
                csv_merged = merged.to_csv(index=False).encode("utf-8")
                csv_missing = missing.to_csv(index=False).encode("utf-8")

                st.download_button(
                    "⬇️ Download matched records (CSV)",
                    data=csv_merged,
                    file_name="matched_records.csv",
                    mime="text/csv",
                )

                st.download_button(
                    "⚠️ Download missing entries (CSV)",
                    data=csv_missing,
                    file_name="missing_records.csv",
                    mime="text/csv",
                )

else:
    st.info("⬆️ Please upload both files to begin.")
