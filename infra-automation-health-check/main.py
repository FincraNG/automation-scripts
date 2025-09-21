"""
This script monitors the health and status of infrastructure automation workflows in Fincra's infrastructure repositories.

Main tasks:
- Loads a list of infrastructure repositories from a YAML configuration file.
- Fetches the latest workflow run status from GitHub Actions for each repository.
- Aggregates and reports the health status of automation workflows.
- Updates a Google Sheet ("Production Reliability Workbook" > "Infra Automation Health Check") with the health check results.

Environment variables required:
- FINCRA_GITHUB_TOKEN: GitHub token for API authentication.
- GOOGLE_APPLICATION_CREDENTIALS (optional): Path to Google service account credentials.

Dependencies:
- requests
- PyYAML
- python-dotenv
- gspread
"""

import requests, yaml
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import gspread

load_dotenv()

# Initialize Google Sheets client using service account credentials
# This requires a service_account.json file in the project directory
# In GitHub Actions, this file is created from a base64-encoded secret
# gc = gspread.service_account()


# Use the path from environment variable or default to service_account.json in current directory
service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
gc = gspread.service_account(filename=service_account_path)

# Load Infrastructure repos from yaml file
infrastructure_repos = yaml.safe_load(open('infrastructure-repos.yml'))['infrastructure-repos']


org_name = "FincraNG"
repo_name = "fincra-disbursements"
token = os.getenv("FINCRA_GITHUB_TOKEN")

# def get_org_repos():
#     """
#     Fetch all repositories for a GitHub organization.
    
#     Args:
#         org_name (str): Name of the GitHub organization
#         token (str): GitHub personal access token
    
#     Returns:
#         List[dict]: List of repository information
#     """
#     base_url = f"https://api.github.com/orgs/{org_name}/repos"
#     headers = {
#         "Authorization": f"token {token}",
#         "Accept": "application/vnd.github.v3+json"
#     }
    
#     repos_info = []
#     repos = []
#     page = 1
    
#     while True:
#         response = requests.get(
#             f"{base_url}?page={page}&per_page=100",
#             headers=headers
#         )
        
#         if response.status_code != 200:
#             raise Exception(f"Failed to fetch repos: {response.status_code}")
            
#         page_repos = response.json()
#         if not page_repos:
#             break
            
#         repos_info.extend(page_repos)
#         page += 1  

#     print(f"Found {len(repos_info)} repositories:")
#     for repo in repos_info:
#         repos.append(repo['name'])
     
#     return repos

    # For specific date range
    # Set time to start of the day for start_date and end of the day for end_date

# Set time range to cover July, August, and September (until today)
# today = datetime.now()
# start_date_initial = datetime(today.year, 9, 18, 0, 0, 0)  # September 18th of current year
# end_date_final = datetime(today.year, today.month, today.day, 23, 59, 59)  # Today at end of day

# print(f"Analyzing workflow runs from {start_date_initial.strftime('%Y-%m-%d')} to {end_date_final.strftime('%Y-%m-%d')}")

# # Function to process each day individually
# def process_daily_stats():
#     current_date = start_date_initial
    
#     while current_date <= end_date_final:
#         # Set start and end time for the current day
#         start_date = current_date.replace(hour=0, minute=0, second=0)   
#         end_date = current_date.replace(hour=23, minute=59, second=59)
        
#         print(f"Processing data for {start_date.strftime('%Y-%m-%d')}")
        
#         # Get stats for this specific day
#         stats = get_workflow_stats(start_date, end_date)
        
#         # Update Google Sheet with the day's data
#         rows = [[
#             start_date.strftime("%Y-%m-%d"),
#             stats["total_runs"],
#             stats["successful_runs"],
#             stats["failed_runs"],
#         ]]
        
#         # Open the Google Sheet and append the data
#         sh = gc.open("Production Reliability Workbook")
#         worksheet = sh.worksheet("Infra Automation Health Check")
        
#         if rows and rows[0][1] > 0:  # Only add if there were runs that day
#             worksheet.append_rows(rows, value_input_option="USER_ENTERED")
#             print(f"Added data for {start_date.strftime('%Y-%m-%d')}: {stats['total_runs']} runs")
#         else:
#             print(f"No data for {start_date.strftime('%Y-%m-%d')}")
        
#         # Move to the next day
#         current_date += timedelta(days=1)

today = datetime.now()
start_date = today.replace(hour=0, minute=0, second=0)  # Today at start of day
end_date = today.replace(hour=23, minute=59, second=59)  # Today at end of day

def get_workflow_stats(start_date, end_date):
    """Get statistics for workflow runs across all repos"""
    repos = infrastructure_repos
    
    total_runs = 0
    successful_runs = 0
    failed_runs = 0
    failed_actions = []

    for repo_name in repos:
        base_url = f"https://api.github.com/repos/{org_name}/{repo_name}/actions/runs"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        yesterday = datetime.now() - timedelta(days=1)
        
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            continue   
        runs = response.json()["workflow_runs"]
        # Define a default recent_runs using yesterday's date
        recent_runs = [
            run for run in runs 
            if datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ") > yesterday
        ]
        
        recent_runs = [
            run for run in runs 
            if datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ") >= start_date
            and datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ") <= end_date
        ]


        total_runs += len(recent_runs)

        for run in recent_runs:
            if run["conclusion"] == "success":
                successful_runs += 1
            elif run["conclusion"] == "failure":
                failed_runs += 1
                failed_actions.append({
                    "repo": repo_name,
                    "name": run["name"],
                    "url": run["html_url"]
                })
        
        
    return {
        "total_runs": total_runs,
        "successful_runs": successful_runs,
        "failed_runs": failed_runs,
        "failed_actions": failed_actions
    }

# def update_google_sheet(stats):
#     """Update Google Sheet with workflow statistics"""
#     rows = [[
#         datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         stats["total_runs"],
#         stats["successful_runs"],
#         stats["failed_runs"],
#     ]]
    
#     # Open the Google Sheet and append the data
#     print("Updating Google Sheet...")
#     sh = gc.open("Production Reliability Workbook")
#     worksheet = sh.worksheet("Infra Automation Health Check")
    
#     if rows:
#         worksheet.append_rows(rows, value_input_option="USER_ENTERED")
    
#     print(f"Successfully updated sheet with {len(rows)} entries.")

# def main():
#     stats = get_workflow_stats()
#     print(f"Total runs: {stats['total_runs']}")
#     print(f"Successful runs: {stats['successful_runs']}")
#     print(f"Failed runs: {stats['failed_runs']}")
    
#     if stats["failed_actions"]:
#         print("\nFailed actions:")
#         for action in stats["failed_actions"]:
#             print(f"- {action['repo']}: {action['name']} ({action['url']})")
#     update_google_sheet(stats)

if __name__ == "__main__":
    # main()
    process_daily_stats()
