import pandas as pd
import re
from datetime import datetime
import streamlit as st
import altair as alt

# -----------------------------------------------------------------------------
# 1. Load the Excel file and transform the data
# -----------------------------------------------------------------------------
file_path = "Statement_manual.xlsx"  # Update path if needed
df = pd.read_excel(file_path)

# --- Date Conversion ---
def convert_date(date_str, year=2025):
    date_str = str(date_str).strip()
    try:
        dt = datetime.strptime(date_str + " " + str(year), "%d %b %Y")
    except Exception:
        try:
            dt = datetime.strptime(date_str + " " + str(year), "%d%b %Y")
        except Exception:
            dt = None
    return dt

df["Date_converted"] = df["Date"].apply(lambda x: convert_date(x, year=2025))
df["Date_formatted"] = df["Date_converted"].apply(lambda dt: dt.strftime("%Y%m%d") if dt is not None else None)

# --- Ensure text columns ---
df["Description1"] = df["Description1"].astype(str)
df["Description2"] = df["Description2"].astype(str)

# --- Clean Balance ---
def clean_balance(balance_str):
    balance_str = str(balance_str).strip()
    if balance_str.lower().endswith("c"):
        balance_str = balance_str[:-1]
    balance_str = balance_str.replace(",", "").strip()
    try:
        return float(balance_str)
    except Exception:
        return None

df["Balance_clean"] = df["Balance"].apply(clean_balance)

# --- Clean Amount & record trans_type ---
def clean_amount(amount_str):
    amount_str = str(amount_str).strip()
    if amount_str and amount_str[-1].lower() == "c":
        trans_type = "Credit"
        amount_str = amount_str[:-1]  # Remove trailing 'c'
    else:
        trans_type = "Debit"
    amount_str = amount_str.replace(",", "").strip()
    try:
        value = float(amount_str)
    except Exception:
        value = None
    return value, trans_type

amounts = df["Amount"].apply(clean_amount)
df["Amount_clean"] = amounts.apply(lambda x: x[0])
df["trans_type"] = amounts.apply(lambda x: x[1])

# --- Clean Accrued Bank Charges ---
def clean_accrued(accrued_str):
    accrued_str = str(accrued_str).replace(",", "").strip()
    try:
        return float(accrued_str)
    except Exception:
        return None

df["Accrued_Bank_Charges_clean"] = df["Accrued Bank Charges"].apply(clean_accrued)

# --- Classify Transactions based on Description1 ---
def assign_class(desc):
    desc_lower = str(desc).lower()
    
    ## ---Expansion 
    
                # If it has "pmtto" and "building" -> Expansion
    if "pmtto" in desc_lower and "building" in desc_lower:
        return "Expansion"

    elif "cjcronje" in desc_lower:
        return "Expansion"
    
    elif "healthcertificate" in desc_lower:
        return "Expansion"
        
        # If it has "pmtto" and "waterdrilling" -> Expansion
    elif "pmtto" in desc_lower and "waterdrilling" in desc_lower:
        return "Expansion"
    
    
    ## ---Rent 
    
    elif "magtapedebit" in desc_lower and "ophrental" in desc_lower:
        return "Rent"
    elif "apppaymenttobraammedi&dental" in desc_lower:
        return "Rent"
    
    ## ---WAGES   
    
    # If it has "pmtto" and "drmmotla" -> wages
    elif "pmtto" in desc_lower and "drmmotla" in desc_lower:
        return "wages"

    # If it has "pmtto" and "nursing" -> wages
    elif "pmtto" in desc_lower and "nursing" in desc_lower:
        return "wages"

    # If it has "pmtto" and "receptionist" -> wages
    elif "pmtto" in desc_lower and "receptionist" in desc_lower:
        return "wages"
    
    # If it has "pmtto" and "security" -> wages
    elif "pmtto" in desc_lower and "security" in desc_lower:
        return "wages"

    # If it has "pmtto" and "cleaner" -> wages
    elif "pmtto" in desc_lower and "cleaner" in desc_lower:
        return "wages"
    
    elif "fnbapppaymentfrom" in desc_lower:
        return "wages"
    
    elif "paymentto" in desc_lower and "advance" in desc_lower:
        return "wages"

    # If it has "pmtto" and "creditcheck" -> (decide what category you want)
    #elif "pmtto" in desc_lower and "creditcheck" in desc_lower:
     #   return "wages"  # or "other" or "Service Provider"? It's up to you
  
    ## ---Stock 
    elif "stock" in desc_lower:
        return "Stock"
    elif "transpharm" in desc_lower:
        return "Stock"
    
    ## ---Bursary 
    
    elif "apppaymenttoeducationfees" in desc_lower:
        return "Bursary"
    elif "tuitionfees" in desc_lower:
        return "Bursary"
    
    ## ---Service Provider
    
    elif "wastemanagement" in desc_lower:
        return "Service Provider"
    elif "fnbobcoll" in desc_lower:
        return "Service Provider"
    elif "tdbmconnect" in desc_lower:
        return "Service Provider"
    elif "wix.com11597" in desc_lower:
        return "Service Provider"
    elif "paymentto" in desc_lower and "accountingservices" in desc_lower:
        return "Service Provider"
    
    
    
    ## ---- Bank Fees
    elif "fee" in desc_lower:
        return "Bank fees"
    
    
    ## ---Transport
    
    elif "uber" in desc_lower:
        return "Transport"
    elif "bolt" in desc_lower:
        return "Transport"
    elif "fuel" in desc_lower:
        return "Transport"
    
    ## ---Policy
    
    elif "internaldebitorder" in desc_lower:
        return "Policy"
    elif "bycdebit" in desc_lower:
        return "Policy"
    elif "magtapedebit" in desc_lower:
        return "Policy"
    
    #elif "credit" in desc_lower and "pps" in desc_lower:
    #    return "policy"
    
    ## ---Working Capital
    
    elif "sendmoney" in desc_lower:
        return "Working Capital"
    elif "prepaidairtime" in desc_lower:
        return "Working Capital"
    
    ## ---Marketing

    elif "google" in desc_lower:
        return "Marketing"
    
    ## ---Union
    elif "samasubs" in desc_lower:
        return "Union"
    
     ## ---Cash Deposit
    elif "cashdeposit" in desc_lower:
        return "Cash Deposit"
    
    ## ---Speed point
    elif "paymentcrikhokha" in desc_lower:
        return "Speed point"
    elif "paymentcrspeedpoint" in desc_lower:
        return "Speed point"

    ## ---Annual Subscribtion
    elif "healthprofessions" in desc_lower:
        return "Annual Subscribtion"

    ## ---Medical Aid
    elif ("magtapecredit" in desc_lower or "realtimecredit" in desc_lower) and "980102" in desc_lower:
        return "Medical Aid"
    elif "magtapecredit" in desc_lower and "dhflexcar" in desc_lower:
        return "Medical Aid"
    
    else:
        return "other"

df["class"] = df["Description1"].apply(assign_class)

# --- Final Output Columns ---
output_columns = [
    "Date",
    "Description1",
    "Date_converted",
    "Date_formatted",
    "Balance_clean",
    "Amount_clean",
    "Accrued_Bank_Charges_clean",
    "trans_type",
    "class"
]
final_df = df[output_columns]

# Save the transformed data to an Excel file
output_file = "final_transformed.xlsx"
final_df.to_excel(output_file, index=False)
#st.write(f"Data successfully saved to {output_file}")

# -----------------------------------------------------------------------------
# 2. Build the Streamlit Dashboard using the transformed data
# -----------------------------------------------------------------------------

@st.cache_data
def load_transformed_data():
    # Load the transformed Excel file
    df = pd.read_excel(output_file)
    # Convert Date_formatted (YYYYMMDD) to datetime for plotting
    df['Date_plot'] = pd.to_datetime(df['Date_formatted'], format="%Y%m%d", errors='coerce')
    return df

df_dash = load_transformed_data()

# Sidebar: Date Range Filter
st.sidebar.header("Filter by Date")
min_date = df_dash['Date_plot'].min().date()
max_date = df_dash['Date_plot'].max().date()

start_date = st.sidebar.date_input("Start Date", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("End Date", value=max_date, min_value=min_date, max_value=max_date)

# Filter data by selected date range
filtered_df = df_dash[(df_dash['Date_plot'].dt.date >= start_date) & (df_dash['Date_plot'].dt.date <= end_date)]

# Dashboard Title and Description
st.title("Medical Business Financial Dashboard")
st.write("This dashboard displays your financial performance over time based on your bank statement data.")

# Metrics: Total Income, Total Expenses, Net Income
total_income = filtered_df.loc[filtered_df['trans_type'] == 'Credit', 'Amount_clean'].sum()
total_expenses = filtered_df.loc[filtered_df['trans_type'] == 'Debit', 'Amount_clean'].sum()
net_income = total_income - total_expenses

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"R{total_income:,.2f}")
col2.metric("Total Expenses", f"R{total_expenses:,.2f}")
col3.metric("Net Income", f"R{net_income:,.2f}")

# Prepare data for time series charts (Line Chart)
df_time = filtered_df.groupby("Date_plot").apply(lambda x: pd.Series({
    "Income": x.loc[x["trans_type"] == "Credit", "Amount_clean"].sum(),
    "Expenses": x.loc[x["trans_type"] == "Debit", "Amount_clean"].sum()
})).reset_index()

df_melt = df_time.melt('Date_plot', var_name='Type', value_name='Amount')

# Interactive Line Chart: Income and Expenses Over Time
line_chart = alt.Chart(df_melt).mark_line(point=True).encode(
    x=alt.X('Date_plot:T', title="Date"),
    y=alt.Y('Amount:Q', title="Amount (R)"),
    color=alt.Color('Type:N', title="Transaction Type"),
    tooltip=['Date_plot:T', 'Type', 'Amount']
).interactive().properties(
    title="Income and Expenses Over Time (Line Chart)",
    width=700,
    height=400
)
st.altair_chart(line_chart, use_container_width=True)

# -----------------------------------------------------------------------------
# Clustered Column Chart: Income and Expenses Over Time with Time Granularity
# -----------------------------------------------------------------------------

# Sidebar selectbox for time granularity
time_granularity = st.sidebar.selectbox(
    "Select Time Granularity for Clustered Column Chart",
    options=["Week", "Month", "Year"],
    index=1
)

# Group the filtered data based on the selected time granularity
df_grouped = filtered_df.copy()
if time_granularity == "Week":
    df_grouped['Time'] = df_grouped['Date_plot'].dt.to_period('W').apply(lambda r: r.start_time)
elif time_granularity == "Month":
    df_grouped['Time'] = df_grouped['Date_plot'].dt.to_period('M').dt.to_timestamp()
elif time_granularity == "Year":
    df_grouped['Time'] = df_grouped['Date_plot'].dt.to_period('Y').apply(lambda r: r.start_time)

# Create a string representation of Time based on the selected granularity.
if time_granularity == "Year":
    time_format = '%Y'
elif time_granularity == "Month":
    time_format = '%Y-%m'
else:
    time_format = '%Y-%m-%d'
    
df_grouped['Time_str'] = df_grouped['Time'].dt.strftime(time_format)

# Group the amounts by the new 'Time' column and separate Income and Expenses
df_time_grouped = df_grouped.groupby("Time").apply(lambda x: pd.Series({
    "Income": x.loc[x["trans_type"] == "Credit", "Amount_clean"].sum(),
    "Expenses": x.loc[x["trans_type"] == "Debit", "Amount_clean"].sum()
})).reset_index()

# Merge the Time_str from df_grouped by taking the first occurrence for each Time
time_str_mapping = df_grouped.groupby("Time")['Time_str'].first().reset_index()
df_time_grouped = df_time_grouped.merge(time_str_mapping, on="Time", how="left")

# Melt the grouped data for plotting; include both Time and Time_str in the id_vars.
df_melt_grouped = df_time_grouped.melt(id_vars=['Time', 'Time_str'], var_name='Type', value_name='Amount')

# Create the clustered column chart using xOffset to separate the bars by transaction type.
clustered_chart = alt.Chart(df_melt_grouped).mark_bar().encode(
    x=alt.X('Time_str:N', sort=sorted(df_time_grouped['Time_str'].unique()), title="Time"),
    xOffset=alt.XOffset('Type:N', title="Transaction Type"),
    y=alt.Y('Amount:Q', title="Amount (R)"),
    color=alt.Color('Type:N', title="Transaction Type"),
    tooltip=['Time_str:N', 'Type', 'Amount']
).properties(
    title=f"Income and Expenses Over Time (Clustered Columns - {time_granularity})",
    width=700,
    height=400
)

st.altair_chart(clustered_chart, use_container_width=True)

# -----------------------------------------------------------------------------
# Pie Chart: Transaction Classification Breakdown
# -----------------------------------------------------------------------------

class_data = filtered_df.groupby("class")["Amount_clean"].sum().reset_index()
pie_chart = alt.Chart(class_data).mark_arc().encode(
    theta=alt.Theta(field="Amount_clean", type="quantitative"),
    color=alt.Color(field="class", type="nominal"),
    tooltip=["class", "Amount_clean"]
).properties(
    title="Transaction Classification Breakdown"
)
st.altair_chart(pie_chart, use_container_width=True)

# Option to display raw filtered data
if st.checkbox("Show Raw Data"):
    st.write(filtered_df)