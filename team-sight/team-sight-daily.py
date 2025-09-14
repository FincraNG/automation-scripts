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




def get_daily_window():
    """Returns the start and end dates for a daily window (past 24 hours)"""
    end_date = datetime.datetime.now().strftime('%Y/%m/%d')
    start_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y/%m/%d')
    return start_date, end_date


# Default to daily window
window_start, window_end = get_daily_window()

# To change window type, uncomment one of these:
# window_start, window_end = get_daily_window()
# window_start, window_end = get_monthly_window()

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

def find_in_progress_and_done_timestamps(histories):
    first_entered_in_progress_at = None
    left_in_progress_at = None
    done_at = None
    in_progress_duration_hours = 0
    
    for history in histories:
        created = parse(history['created'])
        for item in history.get('items', []):
            if item['field'] == 'status':
                if item['toString'] == 'In Progress' and not first_entered_in_progress_at:
                    # Capture the first time it entered "In Progress"
                    first_entered_in_progress_at = created
                if item.get('fromString') == 'In Progress':
                    # Always update to get the last time it left "In Progress"
                    left_in_progress_at = created
                if item['toString'] == 'Done':
                    done_at = created
    in_progress_duration_hours = (
        (left_in_progress_at - first_entered_in_progress_at).total_seconds() / 3600
        if first_entered_in_progress_at and left_in_progress_at else 0
    )
    return first_entered_in_progress_at, left_in_progress_at, in_progress_duration_hours, done_at

def get_jql_query_for_team(team, window_start=window_start, window_end=window_end):
    return f'project = "{team}" AND (status WAS "In Progress" DURING ("{window_start}","{window_end}") OR status = "In Progress" OR status CHANGED TO "DONE" DURING ("{window_start}","{window_end}"))'  # Default query for all teams, can be customized per team if needed
    # return f'project IN ({", ".join([f'"{team}"' for team in teams])}) AND status WAS "In Progress" DURING ("{window_start}","{window_end}") OR status = "In Progress" OR status CHANGED TO "DONE" DURING (-10d, now())'  # Default query for all teams, can be customized per team if needed

def get_issues_for_team(team, jql_query=None):

    # Use customfield_10027 for Cross Border team, customfield_10016 for other teams
    if team == 'Cross Border Product Development':
        params = {
            'jql': jql_query,
            'fields': 'created, status, issuetype, resolutiondate, assignee, summary, reporter, project, customfield_10027',
            'startAt': 0,
            'maxResults': 1000,
        }
    else:
        params = {
            'jql': jql_query,
            'fields': 'created, status, issuetype, resolutiondate, assignee, summary, reporter, project, customfield_10016',
            'startAt': 0,
            'maxResults': 1000,
        }
    
    response = jira.get(jira_api_url, params=params)
    data = response.json()
    
    if response.status_code == 200:
        issues = data.get('issues', [])
        
        if not issues:
            print(f"No issues found for {team}.")
            return None
            
        print(f"Found {len(issues)} issues for {team}")
        
        # Process all issues and return a list
        all_issues = []
        for issue in issues:
            created_time = parse(issue['fields']['created'])
            issue_key = issue['key']
            team_name = issue['fields']['project']['name']
            issue_type = issue['fields']['issuetype']['name']
            summary = issue['fields']['summary']
            reporter = issue['fields']['reporter']['displayName'] if issue['fields']['reporter'] else 'Unassigned'
            assignee = issue['fields']['assignee']['displayName'] if issue['fields']['assignee'] else reporter
            resolution_date = parse(issue['fields']['resolutiondate']) if issue['fields']['resolutiondate'] else None
            last_status = issue['fields']['status']['name']
            story_points = issue['fields'].get('customfield_10027') or issue['fields'].get('customfield_10016')
            
            histories = get_issue_changelog(issue_key)
            first_entered_in_progress_at, left_in_progress_at, in_progress_duration_hours, done_at = find_in_progress_and_done_timestamps(histories)
            
            # If the ticket is still "In Progress", recalculate duration
            if last_status == 'In Progress' and first_entered_in_progress_at:
                # Fix: Use timezone-aware datetime.now()
                now = datetime.datetime.now(first_entered_in_progress_at.tzinfo)
                in_progress_duration_hours = (now - first_entered_in_progress_at).total_seconds() / 3600
                left_in_progress_at = None
                done_at = None

            issue_data = (team, issue_key, summary, issue_type, created_time, first_entered_in_progress_at, 
                         left_in_progress_at, in_progress_duration_hours, done_at, resolution_date, 
                         last_status, assignee, reporter, story_points)
            all_issues.append(issue_data)
            
        return all_issues
    else:
        print(f"Error fetching issues for {team}: {response.status_code}")
        return None

def main(window_start=window_start, window_end=window_end):
    rows = []
    print(f"Window Start: {window_start}, Window End: {window_end}")

    for team in teams:
        print(f"Processing team: {team}...")
        jql_query = get_jql_query_for_team(team)
        
        if not jql_query:
            print(f"Skipping {team} - no JQL query generated")
            continue
            
        results = get_issues_for_team(team, jql_query=jql_query)
        
        if results:  # Check if results is not None and not empty
            for result in results:  # Process each issue
                (team_name, issue_key, summary, issue_type, created_time, first_entered_in_progress_at, 
                 left_in_progress_at, in_progress_duration_hours, done_at, resolution_date, 
                 last_status, assignee, reporter, story_points) = result
                
                # Convert datetime objects to strings
                created_time_str = created_time.strftime('%Y-%m-%d %H:%M:%S') if created_time else ''
                first_in_progress_str = first_entered_in_progress_at.strftime('%Y-%m-%d %H:%M:%S') if first_entered_in_progress_at else ''
                left_in_progress_str = left_in_progress_at.strftime('%Y-%m-%d %H:%M:%S') if left_in_progress_at else ''
                done_at_str = done_at.strftime('%Y-%m-%d %H:%M:%S') if done_at else ''
                resolution_date_str = resolution_date.strftime('%Y-%m-%d %H:%M:%S') if resolution_date else ''

                row = [window_start, window_end, team_name, issue_key, summary, issue_type, story_points, assignee, 
                       created_time_str, first_in_progress_str, left_in_progress_str, 
                       in_progress_duration_hours, done_at_str, resolution_date_str, last_status]
                rows.append(row)
        else:
            print(f"No data to process for {team}")

    # Open the Google Sheet and append the data
    print("Updating Google Sheet...")
    sh = gc.open("TeamSight Workbook Daily")
    
    # Create a new worksheet with today's date
    sheet_title = f'TeamSight Daily {datetime.datetime.now().strftime("%Y-%m-%d")}'

    # Check if worksheet with this name already exists
    try:
        worksheet = sh.worksheet(sheet_title)
        print(f"Worksheet {sheet_title} already exists, using it.")
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=sheet_title, rows=100, cols=20)
        print(f"Created new worksheet: {sheet_title}")
        
        # Add headers
        headers = [
            "Window Start", "Window End", "Team", "Issue Key", "Summary", "Issue Type", "Story Points",
            "Assignee", "Created Date", "Started Progress", "Left Progress", 
            "Time in Progress (hours)", "Done Date", "Resolution Date", "Current Status"
        ]
        
        # Create data including headers
        table_data = [headers]
        if rows:
            table_data.extend(rows)
            
        # Use batch_update to create a formatted table
        worksheet.batch_update([{
            'range': f'A1:O{len(table_data)}',
            'values': table_data
        }])
        
        # Format as table with headers
        worksheet.format('A1:O1', {'textFormat': {'bold': True}})
        worksheet.freeze(rows=1)
        
        # Auto-resize columns for better readability
        worksheet.columns_auto_resize(1, 15)
    else:
        # If worksheet exists and we have data, append it
        if rows:
            worksheet.append_rows(rows, value_input_option="USER_ENTERED")
            print(f"Updated Google Sheet with {len(rows)} rows.")
        else:
            print("No data to update in Google Sheet.")

if __name__ == "__main__":
    main()


