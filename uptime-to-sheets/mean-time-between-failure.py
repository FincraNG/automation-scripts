import requests, yaml
import gspread
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import pytz
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

def get_month():
    now = datetime.now(timezone.utc)
    # Get the first day of the current month
    first_day_current_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    # Last day of previous month is one day before first day of current month
    window_end = first_day_current_month - timedelta(days=1)
    # First day of previous month
    window_start = datetime(window_end.year, window_end.month, 1, tzinfo=timezone.utc)
    month = window_start.strftime('%B %Y')
    return window_start, window_end, month

window_start, window_end, month = get_month()

# Custom range
# window_start = datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
# window_end = datetime(2025, 6, 30, 23, 59, 59, tzinfo=timezone.utc)
# month = window_start.strftime('%B %Y')
    

def get_mean_time_between_failures():
    """Get Mean Time Between Failures (MTBF) for the past month"""
    print(f"Analyzing downtime events from {window_start.strftime('%Y-%m-%d')} to {window_end.strftime('%Y-%m-%d')}")
    data = get_logs_data()
    # print(data['monitors'][0])
    if 'monitors' not in data:
        raise Exception(f"UptimeRobot API error or invalid response: {data}")
    
    # Create a list of downtimes with their associated monitor names
    named_down_times = []
    for monitor in data['monitors']:
        if monitor['friendly_name'] not in internal_services:
            continue
        status = monitor.get("status")
        if status == 0:
            continue
        
        for log in monitor.get('logs', []):
            log_time = datetime.fromtimestamp(log['datetime'], tz=timezone.utc)
            if log['type'] == 1 and log['duration'] > 120 and window_start <= log_time < window_end:
                named_down_times.append((monitor['friendly_name'], log_time))

    # Group downtimes into incidents
    incidents = define_incidents(named_down_times, threshold_seconds=1800)
    # Extract just the times for MTBF calculation
    incident_downtimes = [named_down_times[incident[0]][1] for incident in incidents]
    # Generate incident summaries
    incident_summaries = incidents_report(incidents, named_down_times)
    # Update Google Sheet with incident summaries
    incident_sheet_url = update_incident_report(incident_summaries)
  

    # print("\nAll incident summaries:")
    # for incident in incident_summaries:
    #     print(incident)
    

    # Print for debugging
    # for name, dt in named_down_times:
    #     print(f"{name}: {dt.isoformat()}")
    
    # # Extract just the times for MTBF calculation
    # down_times = [dt for _, dt in named_down_times]
    num_failures = len(incident_downtimes)
    print(f"Number of failures: {num_failures}")
    intervals = []

    # Calculate intervals between downtimes
    for i in range(1, len(incident_downtimes)):
        interval = (incident_downtimes[i] - incident_downtimes[i - 1]).total_seconds()/3600  # Convert to hours
        if interval > 0:  # Only consider positive intervals
            intervals.append(interval)

    # 5. Calculate MTBF
    if intervals:
        mtbf = sum(intervals) / len(intervals)
    else:
        mtbf = 0
    print(num_failures, mtbf)
    return num_failures, mtbf, incident_sheet_url


def define_incidents(named_down_times, threshold_seconds=1800):
    """
    Groups downtime events into incidents.
    Each incident is a sequence of events where the gap between any two consecutive events is ≤ threshold_seconds.
    Returns a list of lists, each inner list contains the indexes of events in that incident.
    """
    # Sort the downtime events by their timestamp (the second item in each tuple)
    named_down_times.sort(key=lambda x: x[1])
    # Prepare to group events into incidents
    incidents = []      # This will store lists of event indexes for each incident
    current = [0]       # Start with the first event index

    # Walk through each event, starting from the second one
    for i in range(1, len(named_down_times)):
        gap = (named_down_times[i][1] - named_down_times[i-1][1]).total_seconds()
        # print(f"Step 4: Comparing event {i-1} and {i}: gap = {gap} seconds")

        # If the gap is within the threshold, it's part of the current incident
        if gap <= threshold_seconds:
            current.append(i)
        else:
            # Otherwise, close the current incident and start a new one
            incidents.append(current)
            current = [i]

    # After the loop, add the last incident to the list
    if current:
        incidents.append(current)
    return incidents  # List of lists of indexes

def incidents_report(incidents, named_down_times):
    """
    Builds a summary report for each incident.
    Returns a list of incident summary dictionaries.
    """
    lagos = pytz.timezone('Africa/Lagos')

    # Build a summary dictionary for each incident
    inc_rows = []

    # Build a summary dictionary for each incident
    for iid, idxs in enumerate(incidents, start=1): # Start incident IDs from 1
        # Get the UTC time of the first and last event in the incident
        start_utc = named_down_times[idxs[0]][1]
        end_utc = named_down_times[idxs[-1]][1]
        # Convert to Lagos time for reporting
        start_lagos = start_utc.astimezone(lagos)
        end_lagos = end_utc.astimezone(lagos)
        # Get the list of services involved in this incident
        services = [named_down_times[i][0] for i in idxs]
        unique_services = set(services)
        inc_rows.append({
            'incident_id': f"INC-{iid:03d}",
            'start_time': start_lagos.strftime('%Y-%m-%d %H:%M:%S%z'),
            'end_time': end_lagos.strftime('%Y-%m-%d %H:%M:%S%z'),
            'size_events': len(idxs),
            'unique_services': len(unique_services),
            'services_list': "; ".join(unique_services),
            'span_seconds': int((end_utc - start_utc).total_seconds())
        })
    return inc_rows



def update_incident_report(incident_summaries):
    """Update Google Sheet with incident summaries"""
    if not incident_summaries:
        print("No incidents to report.")
        return
    incident_sheet_name = f"Incident Summaries {month}"

    # Open (or create) the incident summary sheet
    incident_sheet_name = f"Incident Summaries {month}"
    try:
        incident_sh = gc.open("Failures Summary Report")
        try:
            incident_ws = incident_sh.worksheet(incident_sheet_name)
        except gspread.exceptions.WorksheetNotFound:
            incident_ws = incident_sh.add_worksheet(title=incident_sheet_name, rows="100", cols="10")
    except gspread.exceptions.SpreadsheetNotFound:
        # If the workbook doesn't exist, create it
        incident_sh = gc.create("Failures Summary Report")
        incident_ws = incident_sh.add_worksheet(title=incident_sheet_name, rows="100", cols="10")

    # Prepare data for upload
    header = list(incident_summaries[0].keys())
    rows = [header] + [list(inc.values()) for inc in incident_summaries]

    # Clear and update the worksheet
    incident_ws.clear()
    incident_ws.append_rows(rows, value_input_option="USER_ENTERED")

    # Get the sheet URL
    incident_sheet_url = f"https://docs.google.com/spreadsheets/d/{incident_sh.id}/edit#gid={incident_ws.id}"
    print("Incident summary sheet URL:", incident_sheet_url)

    print(f"Successfully updated Incident Reports with {len(incident_summaries)} incidents.")
    return incident_sheet_url

# Main execution block
if __name__ == "__main__":
    

    num_failures, mtbf, incident_sheet_url = get_mean_time_between_failures()
    row = [month, num_failures, mtbf, incident_sheet_url]



    # Open the Google Sheet and append the data
    print("Updating Google Sheet...")
    sh = gc.open("Production Reliability Workbook")
    worksheet = sh.worksheet("Mean Time Between Failures")
    
    # Add the uptime row
    worksheet.append_rows([row], value_input_option="USER_ENTERED")

    print(f"Successfully updated Mean Time Between Failures (MTBF) data for the month: {month}")
