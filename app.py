import streamlit as st
from azure.storage.blob import BlobServiceClient
import pandas as pd
from datetime import datetime

st.set_page_config(page_title= "Upload Portal", page_icon= '⬆️', layout = "centered")

st.title("🛍️ Meesho Business Upload Portal")
st.header("Upload Daily Reports")


#Validation Function
def validate_files(df, required_cols, file_name):
    validation_passed = True

    #Check empty file
    if df.empty:
        st.error(f"❌ {file_name.name} File is empty")   
        validation_passed = False

    #Check Required Columns
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        st.error(f"❌ {file_name.name}: Missing Columns: {missing_cols}")
        validation_passed = False


    #Check duplicates
    duplicates = df.duplicated().sum()
    if duplicates > 0:
        st.warning(f"⚠️ {file_name.name}: {duplicates} duplicate rows found")
        validation_passed = False


    #Check null columns
    null_cols = df.isnull().sum()
    null_cols = null_cols[null_cols > 0]
    null_df = null_cols.reset_index()
    null_df.columns = ["Column Name", "Null count"]
    null_count = df.isnull().sum().sum()

    if not null_cols.empty:
        st.warning(f"⚠️ {file_name.name} Columns containing null values: {null_count}")
        st.write(null_df)

    return validation_passed

with st.form("update_form"):
    #Orders CSV
    orders = st.file_uploader("Upload Order CSV: ", type = 'csv')

    #Payment Outstanding CSV
    payment_outstanding = st.file_uploader("Upload Payment_Outstanding CSV: ", type = 'csv')

    #Payment Previous Pay CSV
    payment_previous_pay = st.file_uploader("Upload Payment_Previous_Pay CSV: ", type = 'csv')

    submit = st.form_submit_button("Submit")

if submit:
    file_uploaded = True

    if orders is None:
        st.error("❌ Order File is empty")
        file_uploaded = False

    if payment_outstanding is None:
        st.error("❌ Payment Outstanding File is empty")
        file_uploaded = False

    if payment_previous_pay is None:
        st.error("❌ Payment Previous Pay File is empty")
        file_uploaded = False

    if file_uploaded:
        #Read Files
        o_df = pd.read_csv(orders)
        pot_df = pd.read_csv(payment_outstanding)
        ppp_df = pd.read_csv(payment_previous_pay)


        #Required columns 
        o_required_cols = [
            "Reason for Credit Entry",
            "Sub Order No",
            "Order Date",
            "Customer State",
            "Product Name",
            "SKU",
            "Size",
            "Quantity",
            "Supplier Listed Price (Incl. GST + Commission)",
            "Supplier Discounted Price (Incl GST and Commision)",
            "Packet Id"
        ]

        pot_required_cols = ["Sub Order No",
                             "Order Date",
                             "Dispatch Date",
                             "Product Name",
                             "Supplier SKU",
                             "Live Order Status",
                             "Product GST %",
                             "Listing Price (Incl. taxes)",
                             "Quantity",
                             "Transaction ID",
                             "Payment Date",
                             "Final Settlement Amount",
                             "Price Type",
                             "Total Sale Amount (Incl. Shipping & GST)",
                             "Total Sale Return Amount (Incl. Shipping & GST)",
                             "Fixed Fee (Incl. GST)",
                             "Warehousing fee (inc Gst)",
                             "Return premium (incl GST)",
                             "Return premium (incl GST) of Return",
                             "Meesho Commission Percentage",
                             "Meesho Commission (Incl. GST)",
                             "Meesho gold platform fee (Incl. GST)",
                             "Meesho mall platform fee (Incl. GST)",
                             "Fixed Fee (Incl. GST)",
                             "Warehousing fee (Incl. GST)",
                             "Return Shipping Charge (Incl. GST)",
                             "GST Compensation (PRP Shipping)",
                             "Shipping Charge (Incl. GST)",
                             "Other Support Service Charges (Excl. GST)",
                             "Waivers (Excl. GST)",
                             "Net Other Support Service Charges (Excl. GST)",
                             "GST on Net Other Support Service Charges",
                             "TCS",
                             "TDS Rate %",
                             "TDS",
                             "Compensation",
                             "Claims",
                             "Recovery",
                             "Compensation Reason",
                             "Claims Reason",
                             "Recovery Reason"]

        ppp_required_cols = ["Sub Order No",
                             "Order Date",
                             "Dispatch Date",
                             "Product Name",
                             "Supplier SKU",
                             "Live Order Status",
                             "Product GST %",
                             "Listing Price (Incl. taxes)",
                             "Quantity",
                             "Transaction ID",
                             "Payment Date",
                             "Final Settlement Amount",
                             "Price Type",
                             "Total Sale Amount (Incl. Shipping & GST)",
                             "Total Sale Return Amount (Incl. Shipping & GST)",
                             "Fixed Fee (Incl. GST)",
                             "Warehousing fee (inc Gst)",
                             "Return premium (incl GST)",
                             "Return premium (incl GST) of Return",
                             "Meesho Commission Percentage",
                             "Meesho Commission (Incl. GST)",
                             "Meesho gold platform fee (Incl. GST)",
                             "Meesho mall platform fee (Incl. GST)",
                             "Fixed Fee (Incl. GST)",
                             "Warehousing fee (Incl. GST)",
                             "Return Shipping Charge (Incl. GST)",
                             "GST Compensation (PRP Shipping)",
                             "Shipping Charge (Incl. GST)",
                             "Other Support Service Charges (Excl. GST)",
                             "Waivers (Excl. GST)",
                             "Net Other Support Service Charges (Excl. GST)",
                             "GST on Net Other Support Service Charges",
                             "TCS",
                             "TDS Rate %",
                             "TDS",
                             "Compensation",
                             "Claims",
                             "Recovery",
                             "Compensation Reason",
                             "Claims Reason",
                             "Recovery Reason"]

        #Validate Files
        o_valid = validate_files(o_df, o_required_cols, orders)
        pot_valid = validate_files(pot_df, pot_required_cols, payment_outstanding)
        ppp_valid = validate_files(ppp_df, ppp_required_cols, payment_previous_pay)

        all_valid= (o_valid and pot_valid and ppp_valid)

        st.write("Validation Summary")

        if all_valid:
            st.success("✅ All files passed validation")

            #Save files
            today = datetime.today()

            year = str(today.year)
            month = f"{today.month:02d}"
            day = f"{today.day:02d}"
            
            # Connect to Azure Storage
            blob_service_client = BlobServiceClient.from_connection_string(st.secrets["CONNECTION_STRING"])

            # Connect to Container
            container_client = blob_service_client.get_container_client(st.secrets["CONTAINER_NAME"])

            #Path
            orders_blob = f"{year}/{month}/{day}/orders.csv"
            payment_outstanding_blob = f"{year}/{month}/{day}/payment_outstanding.csv"
            payment_previous_pay_blob = f"{year}/{month}/{day}/payment_previous_pay.csv"

            #Upload orders
            container_client.upload_blob(name= orders_blob, data =orders, overwrite=True)

            #Upload payment_outstanding
            container_client.upload_blob(name= payment_outstanding_blob, data =payment_outstanding, overwrite=True)

            #Upload payment_previous_pay
            container_client.upload_blob(name= payment_previous_pay_blob, data =payment_previous_pay, overwrite=True)

            st.success("✅ All files uploaded successfully to Azure Blob Storage")

        else:
            st.error("❌ One or more files failed validation")
        


