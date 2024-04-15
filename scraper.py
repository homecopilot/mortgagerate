import pandas as pd
import re
import requests
import html2text
import os
import telebot

from datetime import datetime

# Create bot
bot = telebot.TeleBot(token=os.environ.get('TELEGRAM_TOKEN'))
chat_id = os.environ.get('TELEGRAM_CHAT_ID')

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
    
def send_telegram_message(message):
    # Define the URL for the API
    url = "https://api.telegram.org/bot{}/sendMessage".format(TELEGRAM_TOKEN)

    
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

    telegram_message = f"New mortgage rates scraped at {date}:\n"
    send_message = False

    MORGAGE_RATE_FILE = "data/mortgage_rates.csv"
    curr_rates = data[['Product', 'Term', 'Rate', 'APR']].sort_values(by=['Product', 'Term'])

    if os.path.exists(MORGAGE_RATE_FILE):
        old_data = pd.read_csv(MORGAGE_RATE_FILE)
        existing_dates = set(pd.to_datetime(old_data['date']))
        # calculate the differences since last available date
        last_date = old_data.date.max()

        if old_data is not None and date not in existing_dates:
            data = pd.concat([old_data, data], ignore_index=True)
            data.to_csv(MORGAGE_RATE_FILE, index=False)
            rate_diff = curr_rates.merge(old_data[old_data.date == last_date], on=['Product', 'Term'], how='left')
            rate_diff['Rate_Diff'] = rate_diff['Rate_x'].astype(float) - rate_diff['Rate_y'].astype(float)
            rate_diff['APR_Diff'] = rate_diff['APR_x'].astype(float) - rate_diff['APR_y'].astype(float)

            rate_diff = rate_diff[['Product', 'Term', 'Rate_Diff', 'APR_Diff', 'Rate_x', 'APR_x']]
            emojify = lambda x: f"📈{x:.3f}" if x > 0 else (f"📉{x:.3f}" if x < 0 else f"🟰{x:.3f}")
            pad_name = lambda x: x.replace("-Rate", "").replace("Rate","").ljust(30)
            telegram_message += "".join(rate_diff.apply(
                lambda x: pad_name(x['Product'] + ' '+ x['Term']) +\
                    f"{x['Rate_x']:.3f} ({emojify(x['Rate_Diff'])}), APR {x['APR_x']:.3f} ({emojify(x['APR_Diff'])})\n"
                , axis=1))
            send_message = True
    else:
        data.to_csv(MORGAGE_RATE_FILE, index=False)
        telegram_message += curr_rates.to_string(index=False)
        send_message = True
    
    if send_message:
        bot.send_message(chat_id, "```"+telegram_message+"```", parse_mode='Markdown')
