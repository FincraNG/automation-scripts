"""
This script calculates time-to-market time KPIs from Jira issues and updates a Google Sheet for reporting.

Main tasks:
- Connects to Jira to fetch issue data related to time-to-market time.
- Calculates time-to-market time metrics for completed issues over a specified period.
- Updates a Google Sheet ("Production Reliability Workbook" > "time-to-market Time") with the calculated KPIs.

Environment variables required:
- JIRA_API_TOKEN: Jira API token for authentication.
- JIRA_EMAIL: Jira user email for authentication.
- GOOGLE_APPLICATION_CREDENTIALS (optional): Path to Google service account credentials.

Dependencies:
- requests
- python-dotenv
- gspread
"""

import requests
import json
import yaml
import os
from dotenv import load_dotenv
import gspread
import datetime
from dateutil.parser import parse
from datetime import datetime, timezone, timedelta


load_dotenv()

# Initialize Google Sheets client using service account credentials
# This requires a service_account.json file in the project directory
# In GitHub Actions, this file is created from a base64-encoded secret
# gc = gspread.service_account()


# Use the path from environment variable or default to service_account.json in current directory
service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
gc = gspread.service_account(filename=service_account_path)

# Load teams from YAML file
# This file contains a list of the teams 
teams = yaml.safe_load(open('teams.yml'))['teams']

# Get JIRA credentials from environment variables
JIRA_URL = os.getenv("JIRA_URL")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

#Instantiate with Credentials
jira = requests.Session()
jira.auth = (JIRA_USERNAME, JIRA_API_TOKEN) 
# Set JIRA API URL
jira_api_url = f"{JIRA_URL}/rest/api/3/search"
# Define JQL query to get issues moved to Done in the last 7 days

def get_issue_changelog(issue_key):
    start_at = 0
    all_histories = []
    while True:
        changelog_url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}/changelog"
        params = {'startAt': start_at, 'maxResults': 100}
        response = jira.get(changelog_url, params=params)
        if response.status_code != 200:
            print(f"Failed to fetch changelog for {issue_key}")
            break
        
        data = response.json()
        
        
        histories = data.get('values', [])
        all_histories.extend(histories)
        
        if len(histories) < 100:  # No more pages
            break
            
        start_at += 100
    return all_histories  

def find_timestamps(histories):
    entry_time = None
    exit_time = None
    
    for history in histories:
        created = parse(history['created'])
        for item in history.get('items', []):
            if item['field'] == 'status':
                # print(f"Item: {item}")   # Debugging line
                # print(f"{item}")   # Debugging line
                # Only consider entry when transitioning from BACKLOG to To Do
                if item['toString'] == 'To Do' and item['fromString'] == 'BACKLOG':
                    print(f"Item: {item} timestamp: {created}")   # Debugging line
                    entry_time = created
                elif (item['toString'] == 'Done' or item['toString'] == 'DONE') and entry_time:
                    exit_time = created
    print(f"Entry Time: {entry_time}, Exit Time: {exit_time}")  # Debugging line

    return entry_time, exit_time    

window_start = datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc).strftime('%Y-%m-%d')
window_end = datetime(2025, 7, 31, 23, 59, 59, tzinfo=timezone.utc).strftime('%Y-%m-%d')

def get_jql_query_for_team(team, window_start=window_start, window_end=window_end):
 # jql_query = 'project = "{team}" AND status CHANGED TO "READY TO DEPLOY" AND status CHANGED FROM "READY TO DEPLOY" DURING ("2025-04-01","2025-04-31")'
    # if team == 'Cross Border Product Development':
    #     return f'project = "{team}" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
    # elif team == 'HQ':
    #     return f'project = "{team}" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
    # elif team == 'Kele Mobile App':
    #     return f'project = "{team}" AND status CHANGED TO "READY TO DEPLOY" AND status CHANGED FROM "READY TO DEPLOY" DURING (-30d, now())'
    # elif team == 'Stablecoin VS':
    #     return f'project = "{team}" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
    # elif team == 'Global Collection':
    #     return f'project = "{team}" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
    # else:   # For Custom Time   DURING ("2025-06-01 00:00", "2025-06-07 23:59")
    #     return None
    # return f'project = "{team}" AND status CHANGED TO "DONE" DURING (-30d, now())'  # Default query for all teams, can be customized per team if needed
    return f'project = "{team}" AND status CHANGED TO "DONE" DURING ("{window_start}", "{window_end}")'  # Default query for all teams, can be customized per team if needed


#  jql_query = 'project = "Cross Border Product Development" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
    # jql_query = 'project = "Cross Border Product Development" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING ("2025-04-01","2025-04-31")'


def calculate_time_to_market(team, jql_query=None):

    # Set parameters for the API request
    print(f"JQL Query for {team}: {jql_query}")  # Debugging line
    params = {
        'jql': jql_query,
        'fields': 'created, status, issuetype, resolutiondate, customDocField, summary, reporter',
        'startAt': 0,
        'maxResults': 1000,  # Adjust as needed
    }
    # Make the API request to get issues
    response = jira.get(jira_api_url, params=params)
    data = response.json()
    if response.status_code == 200:
        issues = data.get('issues', [])
        if not issues:
            print(f"No issues found for {team}.")
            return
            
        total_time_to_market = 0
        total_issues = 0  # Initialize counter for valid issues only
        

        for issue in issues :                                                                         
            # created_time = parse(issue['fields']['created'])
            # Skip bugs
            if issue['fields']['issuetype']['name'].lower() == 'bug':
                continue

            issue_key = issue['key']
            # Get changelog for each issue
            histories = get_issue_changelog(issue_key)
            # Find timestamps
            entry_time, exit_time = find_timestamps(histories)
            print(f" - issue: {issue_key}, entry_time: {entry_time}, exit_time: {exit_time}")  # Debugging line
            if entry_time and exit_time:
                total_issues += 1  # Increment for each valid issue
                # Calculate time-to-market time in hours
                time_to_market = (exit_time - entry_time).total_seconds() / 3600
                total_time_to_market += time_to_market

        print(f"Total issues found for {team}: {total_issues}") 
        # Calculate average lead time
        if total_issues > 0:
            avg_time_to_market = total_time_to_market / total_issues
            # print(f"Average lead time for {team}: {avg_time_to_market:.2f} hours") # Debugging line
            return team, total_issues, avg_time_to_market
        
    # Get today's date for the date label row
def get_month():
    last_month = datetime.now().replace(day=1) - timedelta(days=1)
    formatted_month = last_month.strftime("%B %Y")
    # Return the formatted date row
    return [f"▶ {formatted_month} ◀"] + [""] * 6

def timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    month = get_month()
    timestamp = timestamp()
    rows = []
    for team in teams:
        print(f"Calculating time to market for {team}...")
        jql_query = get_jql_query_for_team(team)
        if not jql_query:
            continue
        
        result = calculate_time_to_market(team, jql_query=jql_query)
        if result:
            team, total_issues, avg_time_to_market = result
            row = [ timestamp, team, total_issues, avg_time_to_market]
        else:
            row = [ timestamp, team, 'N/A']
        # Append the row to the list of rows
        rows.append(row)
    # Open the Google Sheet and append the data
    print("Updating Google Sheet...")
    sh = gc.open("Production Reliability Workbook")
    worksheet = sh.worksheet("Time to Market")

     # Add the date separator row
    worksheet.append_rows([month], value_input_option="USER_ENTERED")

    # Add the lead time row
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")

    print(f"Successfully updated lead time data for the month: {month}")



 # for issue in issues:
#     issue_key = issue['key']
#     # Get changelog for each issue
#     histories = get_issue_changelog(issue_key)
#     # Find deployment timestamps
#     entry_time, exit_time = find_timestamps(histories)
    
#     if entry_time and exit_time:
#         # Calculate time-to-market time in hours
#         time_to_market = (exit_time - entry_time).total_seconds() / 3600
#         total_time_to_market += time_to_market
        
# # Calculate average time-to-market time
# if total_issues > 0:
#     avg_time_to_market = total_time_to_market / total_issues
#     return team, total_issues, avg_time_to_market