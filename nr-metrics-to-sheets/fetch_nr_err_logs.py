import os, requests, yaml, json
from dotenv import load_dotenv
import gspread
import datetime

# Load environment variables from .env file (for local development)
# In GitHub Actions, these will be provided as environment variables
load_dotenv()

# gc = gspread.service_account()

# Initialize Google Sheets client using service account credentials
# Use the path from environment variable or default to service_account.json in current directory
service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
gc = gspread.service_account(filename=service_account_path)

# Get New Relic credentials from environment variables
# These are set in .env file locally or in GitHub Secrets for Actions
NR_API_KEY = os.getenv("NEW_RELIC_API_KEY")
ACCOUNT_ID = int(os.getenv("ACCOUNT_ID"))

# Load services from YAML file
# This file contains a list of New Relic application names to monitor
services = yaml.safe_load(open('services.yml'))['services']


# New Relic GraphQL API endpoint (EU region)
url = f"https://api.eu.newrelic.com/graphql"

# Set up request headers with authentication
headers = {
    "X-Api-Key": NR_API_KEY,
    "Content-Type": "application/json",  # Required for GraphQL requests
}

def fetch_error_logs(service_name):
    # Define NRQL query to get error logs
    if service_name == 'checkout-core-prod':
        # Special case for checkout-core-prod to use Log API
        nrql = (
            f"FROM Log "
            f"SELECT count(*) AS `count`, "
            f"max(timestamp) AS `lastSeen`, "
            f"latest( IF(error.httpCode IS NOT NULL AND error.httpCode != '', error.httpCode, "
            f"             IF(newrelic.ERROR_CODE IS NOT NULL AND newrelic.ERROR_CODE != '', newrelic.ERROR_CODE, "
            f"                IF(newrelicHttpCode IS NOT NULL AND newrelicHttpCode != '', newrelicHttpCode, "
            f"                   IF(httpCode IS NOT NULL AND httpCode != '', httpCode, "
            f"                      IF(response IS NOT NULL AND response != '', response, 'unknown')))))) AS `httpCode` "
            f"WHERE entity.guids = 'NDMwMTE1NHxJTkZSQXxOQXwxODI2OTMyNTk5MDAwOTgyNjQ2' "
            f"WHERE message LIKE '%error%' "
            f"SINCE 1 week ago UNTIL now "
            f"FACET message "
            f"LIMIT 5"
        )
    else:
        # General case for other services
        nrql = (
            f"FROM Log "
            f"SELECT count(*) AS `count`, "
        f"max(timestamp) AS `lastSeen`, "
        f"latest( IF(error.httpCode IS NOT NULL AND error.httpCode != '', error.httpCode, "
        f"             IF(newrelic.ERROR_CODE IS NOT NULL AND newrelic.ERROR_CODE != '', newrelic.ERROR_CODE, "
        f"                IF(newrelicHttpCode IS NOT NULL AND newrelicHttpCode != '', newrelicHttpCode, "
        f"                   IF(httpCode IS NOT NULL AND httpCode != '', httpCode, "
        f"                      IF(response IS NOT NULL AND response != '', response, 'unknown')))))) AS `httpCode` "
        f"WHERE entity.name = '{service_name}' "
        f"  AND level = 'error' "
        f"SINCE 1 week ago UNTIL now "
        f"FACET message "
        f"LIMIT 5"
    )

    # Construct the GraphQL query with variables
    payload = {
            "query": """
            query($accountId: Int!, $nrql: Nrql!) {
                actor {
                account(id: $accountId) {
                    nrql(query: $nrql) {
                    results
                    }
                }
                }
            }
            """,
            "variables": {
                "accountId": ACCOUNT_ID,
                "nrql": nrql
            }
        }
    
    # Make the API request to New Relic
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    #Parse the response JSON      
    data = response.json()
    results = data["data"]["actor"]["account"]["nrql"]["results"]
    return results

# Fetch error logs for checkout-core-prod

# Fetch total count of errors for a service
def fetch_error_count(service_name):
    # Define NRQL query to get error count
    if service_name == 'checkout-core-prod':
        nrql = (
                f"FROM Log "
                f"SELECT Count(*) AS `count` "
                f"WHERE entity.guids = 'NDMwMTE1NHxJTkZSQXxOQXwxODI2OTMyNTk5MDAwOTgyNjQ2' "
                f"AND message LIKE '%error%' "
                f"SINCE 1 week ago "
                f"UNTIL now "
                )
    else:
        nrql = (
            f"FROM Log "
            f"SELECT Count(*) AS `count` "
            f"WHERE entity.name = '{service_name}' "
            f"AND level = 'error' "
            f"SINCE 1 week ago "
            f"UNTIL now "
            )

    # Construct the GraphQL query with variables
    payload = {
            "query": """
            query($accountId: Int!, $nrql: Nrql!) {
                actor {
                account(id: $accountId) {
                    nrql(query: $nrql) {
                    results
                    }
                }
                }
            }
            """,
            "variables": {
                "accountId": ACCOUNT_ID,
                "nrql": nrql
            }
        }
    
    # Make the API request to New Relic
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    
    # Parse the response JSON
    data = response.json()
    results = data["data"]["actor"]["account"]["nrql"]["results"]
    error_count = results[0]["count"]
    return error_count

# Convert lastseen to human-redable string
def convert_lastseen(lastseen):
    return datetime.datetime.fromtimestamp(lastseen/1000).strftime("%Y-%m-%d %H:%M:%S")

# Function to get current timestamp
def get_current_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Function to create a date label row
def get_date_row():
    today = datetime.datetime.now().date()
    
    # Get day with ordinal suffix (1st, 2nd, 3rd, etc.)
    day = today.day
    if 4 <= day <= 20 or 24 <= day <= 30:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    
    # Format as "Friday, May 14th 2025"
    formatted_date = today.strftime(f"%A, %B {day}{suffix} %Y")
    
    # Return the formatted date row
    return [f"▶ {formatted_date} ◀"] + [""] * 6

# Main execution block
if __name__ == "__main__":
    rows = []
    for svc in services:
        print(f"Fetching logs for {svc}...")
        error_logs = fetch_error_logs(svc)
        total_errors = fetch_error_count(svc)
        timestamp = get_current_timestamp()
        date_row = get_date_row()   
                    
        # If no errors found, add a row with a message and continue to next service
        if not error_logs:
            rows.append([timestamp,svc, "No errors found", "N/A", "N/A", "N/A", "N/A"])
            print(f"No errors found for {svc}")
            continue

        for entry in error_logs:
            message= entry["facet"]
            # error_code = "N/A" if code_str is None else int(code_str)
            count = entry["count"]
            error_code = "N/A" if entry["httpCode"] == "unknown" else int(entry["httpCode"])
            last_seen = convert_lastseen(entry["lastSeen"])
            pct_of_total_errors = count / total_errors * 100

            # Create a row with all metrics for this service
            rows.append([
                timestamp,
                svc,
                message,
                error_code,
                count,
                f"{pct_of_total_errors:.2f}%",
                last_seen
            ])

    # Open the Google Sheet and append the data
    print("Updating Google Sheet...")
    sh = gc.open("Production Reliability Workbook")
    worksheet = sh.worksheet("Error Logs Daily")
        
    # Add the date separator row
    worksheet.append_rows([date_row], value_input_option="USER_ENTERED")
        
    # Add the logs rows
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")
        
    print(f"Successfully updated error logs for {len(services)} services.")

