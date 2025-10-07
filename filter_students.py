
import streamlit as st
import pandas as pd
from io import BytesIO


st.set_page_config(page_title="Student Filter Tool", page_icon="🎓", layout="centered")
st.title("🎓 Student Filter Tool")

st.write("Upload your main student Excel/CSV file and paste the list of Student IDs you want to extract.")

# Upload main student data
main_file = st.file_uploader("Upload the main student data file", type=["xlsx", "csv"])


if main_file:
    import os
    ext = os.path.splitext(main_file.name)[1].lower()

    if ext == '.csv':
        df = pd.read_csv(main_file)
    elif ext == '.xlsx':
        df = pd.read_excel(main_file, engine='openpyxl')
    elif ext == '.xls':
        df = pd.read_excel(main_file, engine='xlrd')
    else:
        st.error(f"❌ Unsupported file format: {ext}")
        st.stop()
    st.write("Preview:")
    st.dataframe(df.head(10))

    # Select the student ID column
    student_col = st.selectbox("Select the Student ID column", df.columns)

    # Paste IDs
    st.subheader("Paste your Student IDs below")
    id_input = st.text_area(
        "Enter IDs separated by commas, spaces, or newlines",
        placeholder="Example: 12345, 67890, 11223"
    )

    if st.button("Filter Records"):
        if not id_input.strip():
            st.warning("Please enter at least one Student ID.")
        else:
            # Split and clean the IDs
            ids = [x.strip() for x in id_input.replace(",", "\n").splitlines() if x.strip()]

            # Convert to appropriate type
            df[student_col] = df[student_col].astype(str)
            ids = [str(x) for x in ids]

            filtered = df[df[student_col].isin(ids)]

            st.success(f"✅ Found {len(filtered)} matching records.")
            st.dataframe(filtered.head(20))

            # Download options
            csv_data = filtered.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="⬇️ Download as CSV",
                data=csv_data,
                file_name="filtered_students.csv",
                mime="text/csv",
            )

            # Optional Excel download
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                filtered.to_excel(writer, index=False, sheet_name="Filtered_Students")
            st.download_button(
                label="📘 Download as Excel",
                data=output.getvalue(),
                file_name="filtered_students.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
