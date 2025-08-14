import csv
import requests
from datetime import datetime

PUBMEDCSV = "/path/to/PubMedSearch's/pubmed.csv"
SLACK_WEBHOOK_URL = "INSERT_WEBHOOK_URL"


def count_rows(file):
    with open(file, newline='', encoding='utf-8') as f:
        return sum(1 for _ in csv.reader(f))

def toSlack(message):
    payload = {"text": message}
    response = requests.post(SLACK_WEBHOOK_URL, json=payload)
    if response.status_code!= 200:
        raise ValueError(f"Request failed: {response.status_code}, {response.text}")
    

current_date = datetime.today().strftime('%Y-%m-%d')
    
if __name__ == "__main__":
    try:
        row_count = count_rows(PUBMEDCSV)
        toSlack(f" *{row_count}* total articles as of " + current_date)
        print("Sent to Slack")
    except Exception as e:
         print(f"Failed to process csv: {e}")
