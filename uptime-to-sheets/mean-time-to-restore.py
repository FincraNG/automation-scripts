import requests, yaml
import gspread
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
"""
    This script calculates the Mean Time Between Failures (MTBF) for uptime monitoring
    and updates a Google Sheet with the results.

"""


# Load environment variables from .env file (for local development)
# In GitHub Actions, these will be provided as environment variables
load_dotenv()

# Initialize Google Sheets client using service account credentials
# This requires a service_account.json file in the project directory
# In GitHub Actions, this file is created from a base64-encoded secret
# gc = gspread.service_account()


# Use the path from environment variable or default to service_account.json in current directory
service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
gc = gspread.service_account(filename=service_account_path)


# Load Infrastructure repos from yaml file
internal_services = yaml.safe_load(open('monitors.yml'))['internal-services']


url = "https://api.uptimerobot.com/v2/getMonitors"

# UNIX timestamp for the last 30 days
now = datetime.now(timezone.utc)
# For the year
# start_of_year = datetime(now.year, 1, 1, tzinfo=timezone.utc)
# For the month
# Calculate the start of the previous month
if now.month == 1:
    start_of_month = datetime(now.year - 1, 12, 1, tzinfo=timezone.utc)
else:
    start_of_month = datetime(now.year, now.month - 1, 1, tzinfo=timezone.utc)
# For the past 7 days
# seven_days_ago = now - timedelta(days=7)
# For the day
# start_of_day = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
# Custom range 
# start_time = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
# end_time = datetime(2025, 6, 30, 23, 59, 59, tzinfo=timezone.utc)


def get_logs_data():

    payload = {
        'api_key': os.getenv('UPTIME_ROBOT_API_KEY'),
        'format': 'json',
        'logs': 1,
        'logs_type': 1,  # 1 for all logs
        'logs_limit': 1000,  # Limit to 1000 logs 
        'show_tags': 1, 
    }
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    
    response = requests.post(url, data=payload, headers=headers)
    response.raise_for_status()  # Raise exception for HTTP errors
    
    # Parse the response JSON
    data = response.json()
    return data



def get_mean_time_to_restore():
    data = get_logs_data()
    # print(data['monitors'][0])
    if 'monitors' not in data:
        raise Exception(f"UptimeRobot API error or invalid response: {data}")

    down_times = None
    recovery_durations = []


    for monitor in data['monitors']:
        #Skip external services
        if monitor['friendly_name'] not in internal_services:
            continue
        status = monitor.get("status")
        if status == 0:
        # Skip paused monitors
            continue

        events = sorted(monitor['logs'], key=lambda x: x['datetime'])

        for event in events:
            event_timestamp = datetime.fromtimestamp(event['datetime'], tz=timezone.utc)

            # if log['type'] == 1 and start_time <= log_time < end_time and log['duration'] > 120:  #Custom range
            if event['type'] == 1 and event_timestamp >= start_of_month:  # For the month
                # Type 1 indicates a downtime log
                # print(log)
                down_times = event_timestamp
                # print(f"Downtime detected at {down_times} for monitor {monitor['friendly_name']}")
            elif event['type'] == 2 and down_times is not None and event_timestamp >= start_of_month:
                # Type 2 indicates a recovery log
                up_times = event_timestamp
                # print(f"Recovery detected at {up_times} for monitor {monitor['friendly_name']}")
                # Calculate the duration of downtime
                downtime_time = (up_times - down_times).total_seconds() / 3600
                recovery_durations.append(downtime_time)
                down_times = None  # Reset down_times after processing recovery

    # 5. Calculate MTTR
    if recovery_durations:
        mttr = sum(recovery_durations) / len(recovery_durations)
    else:
        mttr = 0

    return mttr

def get_month():
    last_month = datetime.now().replace(day=1) - timedelta(days=1)
    formatted_month = last_month.strftime("%B %Y")
    return formatted_month

# Main execution block
if __name__ == "__main__":
    
    month = get_month()
    mttr = get_mean_time_to_restore()
    row = [month, mttr]

    # Open the Google Sheet and append the data
    print("Updating Google Sheet...")
    sh = gc.open("Production Reliability Workbook")
    worksheet = sh.worksheet("Mean Time To Restore")
    
    # Add the uptime row
    worksheet.append_rows([row], value_input_option="USER_ENTERED")

    print(f"Successfully updated Mean Time To Restore (MTTR) data for the month: {month}")
