import pandas as pd
import os

# Define the list of CSV files (ensuring "Canada" appears first)
files = [
    'Canada.CPI.1810000401.csv',  
    'AB.CPI.1810000401.csv',
    'BC.CPI.1810000401.csv',
    'MB.CPI.1810000401.csv',
    'NB.CPI.1810000401.csv',
    'NL.CPI.1810000401.csv',
    'NS.CPI.1810000401.csv',
    'ON.CPI.1810000401.csv',
    'PEI.CPI.1810000401.csv',
    'QC.CPI.1810000401.csv',
    'SK.CPI.1810000401.csv'
]

all_rows = []

#-----------------------------------------------------------------------------------------------------------
# Read each CSV and process data
for f in files:
    df = pd.read_csv(f)

    # Remove extra spaces from column names
    df.columns = [col.strip() for col in df.columns]

    # Extract jurisdiction from filename
    juris = os.path.basename(f).split('.')[0]

    # Convert from wide to long format manually
    for index, row in df.iterrows():
        item = row["Item"]  
        for col in df.columns:
            if col != "Item":
                new_row = {
                    "Item": item,
                    "Month": col,
                    "Jurisdiction": juris,
                    "CPI": row[col],
                    "Month_dt": pd.to_datetime(col, format="%y-%b", errors='coerce')  # Convert to date
                }
                all_rows.append(new_row)

# Create DataFrame
combined_df = pd.DataFrame(all_rows)

# Sort by Month first, then by Jurisdiction 
combined_df = combined_df.sort_values(["Month_dt", "Jurisdiction"])
combined_df = pd.concat([combined_df[combined_df["Jurisdiction"] == "Canada"], 
                         combined_df[combined_df["Jurisdiction"] != "Canada"]])

# Format Month as "Jan 24"
combined_df["Month"] = combined_df["Month_dt"].dt.strftime("%b %y")

# Remove Month_dt from final output
combined_df = combined_df.drop(columns=["Month_dt"])

# Print first 12 rows
print("First 12 rows of the combined DataFrame:")
print(combined_df.head(12).to_string(index=False))
print()
#-----------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------
#Calculate month-to-month percentage change in CPI for each (Jurisdiction, Item) group.
combined_df["Pct_change"] = combined_df.groupby(["Jurisdiction", "Item"])["CPI"].pct_change() * 100

# Get a list of unique jurisdictions from the data
jurisdictions = combined_df["Jurisdiction"].unique()

# Compute average month-to-month percentage change for selected categories.
categories = ["Food", "Shelter", "All-items excluding food and energy"]
avg_changes = {}

for juris in jurisdictions:
    avg_changes[juris] = {}
    for cat in categories:
        subset = combined_df[(combined_df["Jurisdiction"] == juris) & (combined_df["Item"] == cat)]
        if not subset.empty:
            avg = subset["Pct_change"].mean()
            avg_changes[juris][cat] = round(avg, 1)
        else:
            avg_changes[juris][cat] = "No data"
print("Average Month-to-Month Percentage Changes (in %):")
for juris in jurisdictions:
    print(f"{juris}:")
    for cat in categories:
        print(f"  {cat}: {avg_changes[juris][cat]}")
    print()

annual_change_services = {}
for juris in combined_df["Jurisdiction"].unique():
    # Get the Services data for this jurisdiction and convert Month to a datetime column.
    subset = combined_df[(combined_df["Jurisdiction"] == juris) & (combined_df["Item"] == "Services")].copy()
    subset["Month_dt"] = pd.to_datetime(subset["Month"], format="%b %y", errors='coerce')
    subset = subset.sort_values("Month_dt")
    if not subset.empty:
        start = subset.iloc[0]["CPI"]
        end = subset.iloc[-1]["CPI"]
        annual_change_services[juris] = round((end - start) / start * 100, 1)
    else:
        annual_change_services[juris] = "No data"
print("Annual Change in CPI for Services (in %):")
for juris, change in annual_change_services.items():
    print(f"{juris}: {change}")
#-----------------------------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------------------------
#Find the province with the highest average month-to-month percentage change 

highest_avg = None
highest_avg_province = None

# Loop through each jurisdiction
for juris in jurisdictions:
    # Skip the Canada
    if juris == "Canada":
        continue
    
    total = 0
    count = 0
    # Loop through the three selected categories
    for cat in categories:
        value = avg_changes[juris][cat]
        # Only add if the value is a number
        if isinstance(value, (int, float)):
            total += value
            count += 1
    
    # Calculate the average if we have valid numbers
    if count > 0:
        average = total / count
        if highest_avg is None or average > highest_avg:
            highest_avg = average
            highest_avg_province = juris

if highest_avg_province:
    print(f"\nProvince with highest average month-to-month percentage change: {highest_avg_province}")
#-----------------------------------------------------------------------------------------------------------


#-----------------------------------------------------------------------------------------------------------
#Find the province with the highest inflation in services 

highest_services = None
highest_services_province = None

# Loop through each jurisdiction (excluding "Canada")
for juris in jurisdictions:
    if juris == "Canada":
        continue
    change = annual_change_services[juris]
    # Only consider valid numeric values
    if isinstance(change, (int, float)):
        if highest_services is None or change > highest_services:
            highest_services = change
            highest_services_province = juris

if highest_services_province:
    print(f"Province with highest inflation in services: {highest_services_province} with {highest_services:.1f}%")
else:
    print("No data to determine the highest inflation in services.")
#-----------------------------------------------------------------------------------------------------------
