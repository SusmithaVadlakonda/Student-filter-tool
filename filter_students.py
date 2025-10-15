import streamlit as st
import pandas as pd
from io import BytesIO
import os

st.set_page_config(page_title="Student Filter Tool v3", page_icon="🎓", layout="centered")
st.title("🎓 Student Filter Tool — Upload or Paste Search Data")

st.write("""
Upload your **main student dataset**, then either **upload a search file** *or* **paste IDs/emails manually**.
You can match on one or more columns such as *Banner ID*, *Email*, or *Name*.
""")

# ---------- Helper to load Excel/CSV ----------
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

# ---------- Main file upload ----------
main_file = st.file_uploader("📘 Upload main student file", type=["xlsx", "xls", "csv"])

if main_file:
    df_main = load_file(main_file)
    df_main.columns = df_main.columns.str.strip()
    st.success(f"✅ Main file loaded successfully. ({len(df_main)} rows)")
    st.dataframe(df_main.head(10))

    # ---------- Choose matching columns ----------
    st.subheader("🔗 Select matching column(s) from main file")
    main_cols = st.multiselect("Select one or more columns to match against", df_main.columns)

    # ---------- Choose search method ----------
    st.subheader("🔍 Provide search data")
    search_option = st.radio(
        "How do you want to provide search data?",
        ["Upload a file", "Paste manually"],
        horizontal=True
    )

    if search_option == "Upload a file":
        search_file = st.file_uploader("📗 Upload file with students to search for", type=["xlsx", "xls", "csv"])
        if search_file:
            df_search = load_file(search_file)
            df_search.columns = df_search.columns.str.strip()

            search_cols = st.multiselect(
                "Select corresponding column(s) from search file",
                df_search.columns,
                help="Select the same number of columns as chosen from main file."
            )

            if main_cols and search_cols:
                if len(main_cols) != len(search_cols):
                    st.error("⚠️ The number of selected columns must match.")
                else:
                    if st.button("Filter Records"):
                        # normalize text for fair matching
                        for m, s in zip(main_cols, search_cols):
                            df_main[m] = df_main[m].astype(str).str.strip().str.lower()
                            df_search[s] = df_search[s].astype(str).str.strip().str.lower()

                        merged = pd.merge(df_main, df_search, left_on=main_cols, right_on=search_cols, how="inner")

                        mask = pd.Series(True, index=df_search.index)
                        for m, s in zip(main_cols, search_cols):
                            mask &= df_search[s].isin(df_main[m])
                        missing = df_search[~mask]

                        st.success(f"✅ Found {len(merged)} matching records.")
                        st.dataframe(merged.head(20))

                        if not missing.empty:
                            st.warning(f"⚠️ {len(missing)} entries from search file not found in main file.")
                            st.dataframe(missing.head(10))

                        # download buttons
                        csv_merged = merged.to_csv(index=False).encode("utf-8")
                        csv_missing = missing.to_csv(index=False).encode("utf-8")

                        st.download_button("⬇️ Download matched records (CSV)",
                                           data=csv_merged,
                                           file_name="matched_records.csv",
                                           mime="text/csv")
                        if not missing.empty:
                            st.download_button("⚠️ Download missing entries (CSV)",
                                               data=csv_missing,
                                               file_name="missing_records.csv",
                                               mime="text/csv")

    elif search_option == "Paste manually":
        st.write("Paste IDs or emails below (comma, space, or newline separated):")
        id_input = st.text_area("Student identifiers", placeholder="A05214278, a05214279, john@txstate.edu")

        if main_cols and id_input.strip():
            ids = [x.strip().lower() for x in id_input.replace(",", "\n").splitlines() if x.strip()]
            if st.button("Filter Records"):
                # match any selected column that contains the pasted IDs
                combined_mask = pd.Series(False, index=df_main.index)
                for col in main_cols:
                    df_main[col] = df_main[col].astype(str).str.strip().str.lower()
                    combined_mask |= df_main[col].isin(ids)

                filtered = df_main[combined_mask]
                missing = [i for i in ids if i not in df_main[main_cols].astype(str).stack().values]

                st.success(f"✅ Found {len(filtered)} matching records.")
                st.dataframe(filtered.head(20))

                if missing:
                    st.warning(f"⚠️ {len(missing)} entries not found in main file.")
                    st.text(", ".join(missing[:10]) + ("..." if len(missing) > 10 else ""))

                csv_filtered = filtered.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download filtered CSV",
                                   data=csv_filtered,
                                   file_name="filtered_students.csv",
                                   mime="text/csv")
