from collections import defaultdict
from bs4 import BeautifulSoup

# Sample input data
pf_filing_details = [
    {
        "total_amount": 5328983,
        "employees_count": 1368,
        "wage_month": "AUG-24"
    },
    {
        "total_amount": 5145010,
        "employees_count": 1333,
        "wage_month": "JUL-24"
    },
    {
        "total_amount": 4886753,
        "employees_count": 1258,
        "wage_month": "JUN-24"
    },
    {
        "total_amount": 4646113,
        "employees_count": 1184,
        "wage_month": "MAY-24"
    },
    {
        "total_amount": 4552916,
        "employees_count": 1161,
        "wage_month": "APR-24"
    }
]

# Initialize a dictionary to store the aggregated results
aggregated_data = defaultdict(lambda: {"total_amount": 0, "employees_count": 0})

# Aggregate the data
for entry in pf_filing_details:
    month = entry["wage_month"]
    aggregated_data[month]["total_amount"] += entry["total_amount"]
    aggregated_data[month]["employees_count"] += entry["employees_count"]

# Convert the aggregated data back to the required list format
result = []
for month, data in aggregated_data.items():
    result.append({
        "total_amount": data["total_amount"],
        "employees_count": data["employees_count"],
        "wage_month": month
    })

# Display the result
print(result)

from datetime import datetime
import calendar

# Get the current month and year
current_month = datetime.now().month-1
current_year = datetime.now().year

# Create a list of month abbreviations in the format 'MON-YY'
month_names = [
    f"{calendar.month_abbr[(current_month - i) % 12 or 12].upper()}-{(current_year if (current_month - i) > 0 else current_year - 1) % 100:02d}"
    for i in range(3)
]

print(month_names)

from datetime import datetime

# Original date string
date_of_credit = '09-SEP-2024 20:05:34'

# Parse the date string into a datetime object
date_obj = datetime.strptime(date_of_credit, '%d-%b-%Y %H:%M:%S')

# Format it as 'MON-YY'
formatted_date = date_obj.strftime('%b-%y').upper()

print(formatted_date)


