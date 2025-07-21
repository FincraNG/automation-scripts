
import os
from dotenv import load_dotenv
import gspread
import datetime
import argparse


load_dotenv()

# Initialize Google Sheets client using service account credentials
# This requires a service_account.json file in the project directory
# In GitHub Actions, this file is created from a base64-encoded secret
# gc = gspread.service_account()

# Use the path from environment variable or default to service_account.json in current directory
service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
gc = gspread.service_account(filename=service_account_path)

# Function to get story points details from command line arguments from the workflow file
def story_points_details():
    parser = argparse.ArgumentParser()
    parser.add_argument('--sprint-name', required=True)
    parser.add_argument('--project-name', required=True)
    parser.add_argument('--story-points-sum', required=True)
    args = parser.parse_args()

    total_points = args.story_points_sum
    sprint_name = args.sprint_name
    project_name = args.project_name
    print(f"Sprint {sprint_name} | Project {project_name} -> {total_points} story points")

    return {
        "sprint_name": sprint_name,
        "project_name": project_name,
        "story_points_sum": total_points
    }


def timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main():
    timestamp = timestamp()
    data = story_points_details()

    rows = []
    row = [timestamp, data["sprint_name"], data["project_name"], data["story_points_sum"]]
    # Append the row to the list of rows
    rows.append(row)
    
    # Open the Google Sheet and append the data
    print("Updating Google Sheet...")
    sh = gc.open("Production Reliability Workbook")
    worksheet = sh.worksheet("Story Points Closed")

    # Add the story points row
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")

    print(f"Successfully uploaded story points data for the sprint: {data['sprint_name']} and project: {data['project_name']} at {timestamp}.")


if __name__ == '__main__':
    main()







# #Instantiate with Credentials
# jira = requests.Session()
# jira.auth = (JIRA_USERNAME, JIRA_API_TOKEN) 
# # Set JIRA API URL
# jira_api_url = f"{JIRA_URL}/rest/api/3/search"
# # Define JQL query to get issues moved to Done in the last 7 days

# def get_issue_changelog(issue_key):
#     start_at = 0
#     all_histories = []
#     while True:
#         changelog_url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}"
#         params = {'startAt': start_at, 'maxResults': 100}
#         response = jira.get(changelog_url, params=params)
#         if response.status_code != 200:
#             print(f"Failed to fetch changelog for {issue_key}")
#             break
        
#         data = response.json()
#         # print(json.dumps(data, indent=4, sort_keys=True, ensure_ascii=False))
#         story_points = data.get('fields', {}).get('customfield_10016', None)  # Adjust the field ID as needed
#         print(f"Story Points for {issue_key}: {story_points}")  # Debugging line
#         histories = data.get('changelog', {}).get('histories', [])
#         all_histories.extend(histories)

#         if len(histories) < 100:  # No more pages
#             break
            
#         start_at += 100
#     return all_histories  

# def find_deployment_timestamps(histories):
#     entry_time = None
#     exit_time = None
    
#     for history in histories:
#         created = parse(history['created'])
#         for item in history.get('items', []):
#             if item['field'] == 'status':
#                 # print(f"{item}")   # Debugging line
#                 if item['toString'] == 'To Do':
#                     entry_time = created
#                 elif item['toString'] == 'DONE' and team == 'HQ':
#                     exit_time = created
#                 elif item['toString'] == 'Done' and team != 'HQ':
#                     exit_time = created
#     # print(f"Entry Time: {entry_time}, Exit Time: {exit_time}")  # Debugging line
#     return entry_time, exit_time    

# def get_jql_query_for_team(team):
#  # jql_query = 'project = "{team}" AND status CHANGED TO "READY TO DEPLOY" AND status CHANGED FROM "READY TO DEPLOY" DURING ("2025-04-01","2025-04-31")'
#     # if team == 'Cross Border Product Development':
#     #     return f'project = "{team}" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
#     # elif team == 'HQ':
#     #     return f'project = "{team}" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
#     # elif team == 'Kele Mobile App':
#     #     return f'project = "{team}" AND status CHANGED TO "READY TO DEPLOY" AND status CHANGED FROM "READY TO DEPLOY" DURING (-30d, now())'
#     # elif team == 'Stablecoin VS':
#     #     return f'project = "{team}" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
#     # elif team == 'Global Collection':
#     #     return f'project = "{team}" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
#     # else:
#     #     return None
#     return f'project = "Global Collection" AND status CHANGED TO "DONE" DURING (-14d, now())'  # Default query for all teams, can be customized per team if needed
# #  jql_query = 'project = "Cross Border Product Development" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING (-30d, now())'
#     # jql_query = 'project = "Cross Border Product Development" AND status CHANGED TO "READY FOR DEPLOYMENT" AND status CHANGED FROM "READY FOR DEPLOYMENT" DURING ("2025-04-01","2025-04-31")'
     
 
# def calculate_deployment_to_resolution_lead_time(team, jql_query=None):
   
#     # Set parameters for the API request
#     params = {
#         'jql': jql_query,
#         'fields': 'created, status, issuetype, resolutiondate, customDocField, summary, reporter',
#         'startAt': 0,
#         'maxResults': 1000,  # Adjust as needed
#     }
#     # Make the API request to get issues
#     response = jira.get(jira_api_url, params=params)
#     data = response.json()
#     if response.status_code == 200:
#         issues = data.get('issues', [])
#         if not issues:
#             print("No issues found in the last 7 days.")
#             return
            
#         total_lead_time = 0
#         total_issues = len(issues)

#         for issue in issues:                                                                         
#             created_time = parse(issue['fields']['created'])
#             issue_key = issue['key']
#             # Get changelog for each issue
#             histories = get_issue_changelog(issue_key)
#             # Find deployment timestamps
#             entry_time, exit_time = find_deployment_timestamps(histories)
#             # print(f" - team: {team}, Created: {created_time}, Exit: {exit_time}")  # Debugging line
#             if created_time and exit_time:
#                 # Calculate lead time in hours
#                 lead_time = (exit_time - created_time).total_seconds() / 3600
#                 total_lead_time += lead_time

#         # Calculate average lead time
#         if total_issues > 0:
#             avg_lead_time = total_lead_time / total_issues
#             # print(f"Average lead time for {team}: {avg_lead_time:.2f} hours") # Debugging line
#             return team, total_issues, avg_lead_time

#     # Get today's date for the date label row
# def get_month():
#     last_month = datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)
#     formatted_month = last_month.strftime("%B %Y")
#     # Return the formatted date row
#     return [f"▶ {formatted_month} ◀"] + [""] * 6

# def timestamp():
#     return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# if __name__ == "__main__":
#     month = get_month()
#     timestamp = timestamp()
#     rows = []
#     for team in teams:
#         jql_query = get_jql_query_for_team(team)
#         if not jql_query:
#             continue
        
#         result = calculate_deployment_to_resolution_lead_time(team, jql_query=jql_query)
#         if result:
#             team, total_issues, avg_lead_time = result
#             row = [timestamp, team, avg_lead_time]
#         else:
#             row = [timestamp, team, 'N/A']
#         # Append the row to the list of rows
#         rows.append(row)
    # Open the Google Sheet and append the data
    # print("Updating Google Sheet...")
    # sh = gc.open("Production Reliability Workbook")
    # worksheet = sh.worksheet("Lead Time")

    #  # Add the date separator row
    # worksheet.append_rows([month], value_input_option="USER_ENTERED")
   
    # # Add the uptime row
    # worksheet.append_rows(rows, value_input_option="USER_ENTERED")

    # print(f"Successfully updated lead time data for the month: {month}")