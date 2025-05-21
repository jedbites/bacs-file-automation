import streamlit as st
import pandas as pd
import csv
import io
from datetime import datetime

def process_csv(
        df,
        debtor_name,
        debtor_account,
        batch_id,
        contra_sort_code
):
    """
    Processes the input DataFrame into a Standard 18 BACS file format.

    The resulting file includes the following records:
      - VOL, HDR1, HDR2, UHL1 (headers)
      - One PAY record per row from the input CSV
      - A CONTRA record to sum the total debits/credits
      - EOF/UTL records
    """

    # Check if the required columns are present
    required_cols = {
        "beneficiary_name",
        "beneficiary_sort_code",
        "beneficiary_account",
        "amount",
        "payment_reference",
        "processing_date"
    }
    
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Missing required columns: {', '.join(missing)}")
    
    today = datetime.today().strftime('%Y-%m-%d')
    records = []

    # Header records
    records.append(["VOL", "001", "HSBC", today, "", "", "", ""])
    records.append(["HDR1", debtor_name, debtor_account, "HSBC", today, "", "", ""])
    records.append(["HDR2", f"Payment Batch {batch_id}", batch_id, "", "", "", "", ""])
    records.append(["UHL1", debtor_name, debtor_account, "", "", "", "", ""])

    # Generate one PAY record for each CSV row
    for idx, row in df.iterrows():
        try:
            amount_val = float(row["amount"])
        except Exception:
            amount_valu = 0.0
        records.append([
            "PAY",
            row["beneficiary_name"],
            row["beneficiary_sort_code"],
            row["beneficiary_account"],
            f"{amount_val:.2f}",
            row["payment_reference"],
            row["processing_date"],
            ""
        ])
    
    # Create CONTRA record (summing up the amount column)
    total_ammount = df["amount"].sum()
    records.append(["CONTRA", debtor_name, contra_sort_code, debtor_account, f"{total_ammount:.2f}", "", "", ""])
    records.append(["EOF1", "End of File", "", "", "", "", "", ""])
    records.append(["EOF2", "Checksum", "", "", "", "", "", ""])
    records.append(["UTL1", "Processing Complete", "", "", "", "", "", ""])

    # Write records to in-memory CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(records)
    return output.getvalue()

def main():
    st.title("BACS File Generator")
    st.write("""
    This app converts a CSV file with transaction details
    into a Standard 18 BACS file format compatible with HSBC.
    
    **Input CSV Requirements:**  
    The CSV file must contain the following columns (with exact names):
      - beneficiary_name  
      - beneficiary_sort_code  
      - beneficiary_account  
      - amount  
      - payment_reference  
      - processing_date  
    """)

    # Get debtor and batch details from the user
    debtor_name = st.text_input("Enter Debtor (Your Organization) Name", value="ABC Ltd")
    debtor_account = st.text_input("Enter Debtor Account Number", value="12345678")
    batch_id = st.text_input("Enter Payment Batch ID", value="001")
    contra_sort_code = st.text_input("Enter Contra Sort Code", value="12-34-56")

    # File uploader for the transaction CSV
    uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            # Read and display the input CSV.
            df = pd.read_csv(uploaded_file)
            st.subheader("Input CSV Preview")
            st.dataframe(df)

            # Generate processed file when the button is clicked
            if st.button("Generate BACS File"):
                # Process the dataframe in a BACS file format
                bacs_csv = process_csv(df, debtor_name, debtor_account, batch_id, contra_sort_code)
                st.success("BACS file generated successfully!")
                st.download_button(
                    label="Download BACS File",
                    data=bacs_csv,
                    file_name="bacs_file.csv",
                    mime="text/csv"
                )
        except Exception as e:
            st.error(f"Error processing the file: {e}")

if __name__ == "__main__":
    main()