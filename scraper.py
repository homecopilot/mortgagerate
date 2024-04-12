import pandas as pd
import re
import requests
import html2text
import os

from datetime import datetime

def parse_mortgage_string(mortgage_string):
    # Define the pattern for matching the string
    pattern = r"\[(.*?)\]\((.*?)\) \| ([\d\.]+)% \| ([\d\.]+)%"

    # Use regular expression to find matches
    match = re.match(pattern, mortgage_string)
    if match:
        name = match.group(1)
        url = match.group(2)
        rate = float(match.group(3))
        apr = float(match.group(4))
        return {
            "Term": name,
            "URL": url,
            "Rate": rate,
            "APR": apr
        }
    else:
        return None

def parse_date(mortgage_string):
    pattern = r"(\d{1,2}/\d{1,2}/\d{4} \d{1,2}:\d{1,2} [APap][Mm])"
    # pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
    # pattern = r"(\d{1,2}:\d{1,2} [APap][Mm])"
    match = re.search(pattern, mortgage_string)
    
    if match:
        # Extract the matched date and time
        date_time_str = match.group(1)

        # Parse the date and time
        date_time_obj = datetime.strptime(date_time_str, "%m/%d/%Y %I:%M %p")
        return date_time_obj
    else:
        return None
    
if __name__ == "__main__":
    response = requests.get("https://www.wellsfargo.com/mortgage/rates/")
    data = html2text.html2text(response.text)

    # remove tracking pixels /assets/images/global/s.gif?
    data = "\n".join([lines for lines in data.split("\n") if r"/assets/images/global/s.gif" not in lines])

    # save a copy of the data to a file
    with open("data/all_rates.txt", "w") as file:
        file.write(data)

    # generate current data
    Product = None
    results = []
    date = None
    for d in data.split("\n"):
        if "purchase rates" in d.lower():
            Product = "Purchase"
        if "refinance rates" in d.lower():
            Product = "Refinance"
        if Product:
            m = parse_mortgage_string(d)
            if m:
                m.update({"Product": Product})
                results.append(m)
            else:
                date = date if date else parse_date(d)
    data = pd.DataFrame.from_records(results)
    data['date'] = date

    MORGAGE_RATE_FILE = "data/mortgage_rates.csv"
    if os.path.exists(MORGAGE_RATE_FILE):
        old_data = pd.read_csv(MORGAGE_RATE_FILE)
        existing_dates = set(pd.to_datetime(old_data['date']))
        if old_data is not None and date not in existing_dates:
            data = pd.concat([old_data, data], ignore_index=True)
            data.to_csv(MORGAGE_RATE_FILE, index=False)
    else:
        data.to_csv(MORGAGE_RATE_FILE, index=False)