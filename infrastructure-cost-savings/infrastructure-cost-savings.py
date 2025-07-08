import boto3, os, requests, json
import datetime
from datetime import timezone
from dotenv import load_dotenv
import gspread

load_dotenv()

gc = gspread.service_account()


# Use the path from environment variable or default to service_account.json in current directory
# service_account_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'service_account.json')
# gc = gspread.service_account(filename=service_account_path)

NR_API_KEY = os.getenv("NEW_RELIC_API_KEY")
ACCOUNT_ID = int(os.getenv("ACCOUNT_ID"))

# New Relic GraphQL API endpoint (EU region)
# Change to https://api.newrelic.com/graphql for US region
url = f"https://api.eu.newrelic.com/graphql"

# Set up request headers with authentication
headers = {
    "X-Api-Key": NR_API_KEY,
    "Content-Type": "application/json",  # Required for GraphQL requests
}

# start_time = datetime.datetime(2025, 6, 1, 0, 0, 0, tzinfo=timezone.utc)
# end_time = datetime.datetime(2025, 7, 1, 0, 0, 0, tzinfo=timezone.utc)

# Function to get AWS monthly cost using Cost Explorer API
def get_monthly_cost():

    client = boto3.client('ce',)

    # Calculate start and end dates for the previous full month
    today = datetime.datetime.now(timezone.utc)
    first_day_this_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_end = first_day_this_month
    last_month_start = (first_day_this_month - datetime.timedelta(days=1)).replace(day=1)
    print(f"Last month start: {last_month_start}, Last month end: {last_month_end}")
    response = client.get_cost_and_usage(
        TimePeriod={
            'Start': last_month_start.strftime('%Y-%m-%d'),
            'End': last_month_end.strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Metrics=['UnblendedCost']
    )

    results = response['ResultsByTime'][0]
    amount = float(results['Total']['UnblendedCost']['Amount'])
    unit = results['Total']['UnblendedCost']['Unit']
    return amount

def get_transactions_count():
    # Define NRQL query to get average transaction duration in milliseconds
    nrql = (
        "SELECT "
        "  filter(count(*), WHERE message LIKE '%event.payment.initiated%') "
        "  + filter(count(*), WHERE name = 'payout.initiated') "
        "  + filter(count(*), WHERE event = 'event.collection.initiated') "
        "AS 'Total Transactions' "
        "FROM Log "
        "SINCE 1 month ago"
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
    response.raise_for_status()  # Raise exception for HTTP errors
    
    # Parse the response JSON
    data = response.json()
    results = data["data"]["actor"]["account"]["nrql"]["results"]
    total_transactions = float(results[0]["Total Transactions"])
    print(f"Total transactions for the month: {total_transactions}")
    return total_transactions

def cost_per_transaction():
    # Get the total AWS cost for the month
    total_cost = get_monthly_cost()
    # Get the total transactions count
    total_transactions = get_transactions_count()
    if total_transactions > 0:
        cost_per_transaction = total_cost / total_transactions
        print(cost_per_transaction)
        return cost_per_transaction
    else:
        print("No transactions found for the month.")
        return None


def get_month():
    last_month = datetime.datetime.now().replace(day=1) - datetime.timedelta(days=1)
    formatted_month = last_month.strftime("%B %Y")
    return formatted_month

if __name__ == "__main__":
    month = get_month()
    total_infra_cost = get_monthly_cost()
    cost_per_transact = cost_per_transaction()
    total_transactions = get_transactions_count()
    row = [month, total_transactions, total_infra_cost, cost_per_transact]

     # Open the Google Sheet and append the data
    print("Updating Google Sheet...")
    sh = gc.open("Production Reliability Workbook")
    worksheet = sh.worksheet(" Infrastructure Cost Efficiency")
   
    # Add the uptime row
    worksheet.append_rows([row], value_input_option="USER_ENTERED")

    print(f"Successfully updated infrastructure cost savings data for the month: {month}")


