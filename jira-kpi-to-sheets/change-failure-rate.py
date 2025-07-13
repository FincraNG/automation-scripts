"""
This script calculates lead time KPIs from Jira issues and updates a Google Sheet for reporting.

Main tasks:
- Connects to Jira to fetch issue data related to lead time.
- Calculates lead time metrics for completed issues over a specified period.
- Updates a Google Sheet ("Production Reliability Workbook" > "Lead Time") with the calculated KPIs.

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


load_dotenv()

# Initialize Google Sheets client using service account credentials
# This requires a service_account.json file in the project directory
# In GitHub Actions, this file is created from a base64-encoded secret
gc = gspread.service_account()



# Use the path from environment variable or default to service_account.json in current directory
# service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
# gc = gspread.service_account(filename=service_account_path)

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

def get_jql_query_for_total_deployments(team):
    # jql_query = f'project = "{team}" AND status CHANGED FROM "DEPLOYED TO PROD" DURING ("2025-06-01 00:00", "2025-06-31 23:59")' # For looking for specific date ranges
    if team == 'Cross Border Product Development':
        return f'project = "{team}" AND status CHANGED TO "POST-DEPLOYMENT QA" DURING (-7d, now())'
    elif team == 'HQ':
        return f'project = "HQ" AND status CHANGED TO "POST DEPLOYMENT CHECKS" DURING (-7d, now())'
    elif team == 'Kele Mobile App':
        return f'project = "{team}" AND status CHANGED TO "POST DEPLOYMENT TEST" DURING (-7d, now())'
    elif team == 'Stablecoin VS':
        return f'project = "{team}" AND status CHANGED TO "POST DEPLOYMENT QA" DURING (-7d, now())'
    elif team == 'Global Collection':
        return f'project = "{team}" AND status CHANGED TO "POST DEPLOYMENT QA" DURING (-7d, now())'
    else:
        return None

def get_jql_query_for_failed_deployments(team):
    if team == 'Cross Border Product Development':
        return f'project = "{team}" AND status changed TO "Post-Deployment QA" DURING (-7d, now()) AND NOT status changed TO Done DURING (-7d, now())'
    elif team == 'HQ':
        return f'project = "{team}" AND status changed TO "POST DEPLOYMENT CHECKS" DURING (-7d, now()) AND NOT status changed TO Done DURING (-7d, now())'
    elif team == 'Kele Mobile App':
        return f'project = "{team}" AND status changed TO "POST DEPLOYMENT TEST" DURING (-7d, now()) AND NOT status changed TO Done DURING (-7d, now())'
    elif team == 'Stablecoin VS':
        return f'project = "{team}" AND status changed TO "POST DEPLOYMENT QA" DURING (-7d, now()) AND NOT status changed TO Done DURING (-7d, now())'
    elif team == 'Global Collection':
        return f'project = "{team}" AND status changed TO "POST DEPLOYMENT QA" DURING (-7d, now()) AND NOT status changed TO Done DURING (-7d, now())'
    else:
        return None

def get_total_deployments(jql_query):
    """
    Fetch the total number of deployments for a given JQL query.
    """
    params = {
        'jql': jql_query,
        'fields': 'status',
        'startAt': 0,
        'maxResults': 1000,
    }
    response = jira.get(jira_api_url, params=params)
    data = response.json()
    if response.status_code == 200:
        issues = data.get('issues', [])
        return len(issues)
    return 0

    # Get today's date for the date label row
def get_month():
    last_month = datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)
    formatted_month = last_month.strftime("%B %Y")
    # Return the formatted date row
    return [f"▶ {formatted_month} ◀"] + [""] * 6

def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_weekly_date_range():
    # Get today's date
    today = datetime.datetime.now().date()
    
    # Calculate the start of the week (previous Sunday)
    start_of_week = today - datetime.timedelta(days=today.weekday() + 1)
    
    # Calculate the end of the week (next Saturday)
    end_of_week = start_of_week + datetime.timedelta(days=6)
    
    # Function to add ordinal suffix to day
    def add_ordinal_suffix(day):
        if 4 <= day <= 20 or 24 <= day <= 30:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        return f"{day}{suffix}"
    
    # Format start date as "Sunday, May 14th 2025"
    start_day_with_suffix = add_ordinal_suffix(start_of_week.day)
    start_date_formatted = start_of_week.strftime(f"%A, %B {start_day_with_suffix} %Y")
    
    # Format end date as "Saturday, May 20th 2025"
    end_day_with_suffix = add_ordinal_suffix(end_of_week.day)
    end_date_formatted = end_of_week.strftime(f"%A, %B {end_day_with_suffix} %Y")
    
    # Combine into a range string
    date_range = f"{start_date_formatted} - {end_date_formatted}"
    
    # Return the formatted date row
    return [f"▶ {date_range} ◀"] + [""] * 6


if __name__ == "__main__":
    weekly_range = get_weekly_date_range()
    timestamp = timestamp()
    rows = []
    for team in teams:

        jql_query_total = get_jql_query_for_total_deployments(team)
        if not jql_query_total:
            continue

        total_deployments = get_total_deployments(jql_query_total)

        jql_query_failed = get_jql_query_for_failed_deployments(team)
        if not jql_query_failed:
            continue
        failed_deployments = get_total_deployments(jql_query_failed)

        # Calculate change failure rate
        if total_deployments > 0:
            change_failure_rate = (failed_deployments / total_deployments) * 100
        else:
            change_failure_rate = 0

        # Append the data to the rows
        rows.append(["", team, total_deployments, failed_deployments, change_failure_rate])

    # Open the Google Sheet and append the data
    print("Updating Google Sheet...")
    sh = gc.open("Production Reliability Workbook")
    worksheet = sh.worksheet("Change Failure Rate")

     # Add the date separator row
    worksheet.append_rows([weekly_range], value_input_option="USER_ENTERED")

    # Add the uptime row
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")

    print(f"Successfully updated lead time data for the week: {weekly_range[0]}")



 # for issue in issues:
#     issue_key = issue['key']
#     # Get changelog for each issue
#     histories = get_issue_changelog(issue_key)
#     # Find deployment timestamps
#     entry_time, exit_time = find_deployment_timestamps(histories)
    
#     if entry_time and exit_time:
#         # Calculate lead time in hours
#         lead_time = (exit_time - entry_time).total_seconds() / 3600
#         total_lead_time += lead_time
        
# # Calculate average lead time
# if total_issues > 0:
#     avg_lead_time = total_lead_time / total_issues
#     return team, total_issues, avg_lead_time