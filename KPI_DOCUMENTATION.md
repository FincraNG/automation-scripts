# KPI Documentation

This document provides comprehensive documentation for all Key Performance Indicators (KPIs) being tracked. Each KPI includes its definition, measurement methodology, data sources, and the automation workflows that support it.

## Table of Contents

1. [Infrastructure Automation Health Check](#infrastructure-automation-health-check)
2. [Lead Time](#lead-time)
3. [Story Points Closed](#story-points-closed)
4. [Change Failure Rate](#change-failure-rate)
5. [Deployment Frequency](#deployment-frequency)
6. [Average Deployments per Engineer](#average-deployments-per-engineer)
7. [Mean Time Between Failures (MTBF)](#mean-time-between-failures)
8. [Mean Time To Restore (MTTR)](#mean-time-to-restore)
9. [Customer Impacting Incidents](#customer-impacting-incidents)
10. [Service Uptime](#service-uptime)
11. [Transaction Success Rate](#transaction-success-rate)
12. [Badly Handled Error Rate](#badly-handled-error-rate)
13. [Error Rate Metrics](#error-rate-metrics)
14. [Infrastructure Pipeline Stability](#infrastructure-pipeline-stability)
15. [Infrastructure Cost Efficiency](#infrastructure-cost-efficiency)
16. [Infrastructure Provisioning Success Rate](#infrastructure-provisioning-success-rate)

## Data Collection and Storage

All KPIs are collected and stored in the "Production Reliability Workbook" Google Sheets document, with different worksheets for each metric. Data collection is automated through various APIs:

- Jira API for development metrics
- New Relic API for application performance metrics
- UptimeRobot API for uptime and incident metrics
- AWS Cost Explorer API for infrastructure costs
- GitHub API for pipeline statistics

Updates are performed through GitHub Actions workflows on daily, weekly, or monthly schedules depending on the metric.

## Repository Structure

```
.
├── infra-automation-health-check/        
├── infra-config-drift-audit/            
├── infrastructure-automation-pipeline-stability/
├── infrastructure-cost-savings/          # Cost efficiency tracking
├── jira-kpi-to-sheets/                  # Development metrics
├── nr-metrics-to-sheets/                # Application metrics
└── uptime-to-sheets/                    # Uptime and incident metrics
```

Each directory contains the scripts and configuration files needed to collect and report its respective metrics.

### Infrastructure Automation Health Check

**Definition**  
Measures the health and reliability of infrastructure automation workflows across all infrastructure repositories.

**Measurement Logic/Formula**
- Tracks workflow runs in the last 24 hours across all infrastructure repositories
- Success Rate = (Successful Runs / Total Runs) × 100%
- Failure Rate = (Failed Runs / Total Runs) × 100%

**Data Sources**
- Primary: GitHub Actions API
- Location: `infra-automation-health-check/main.py`
- Frequency: Continuous monitoring with daily aggregation
- Storage: "Production Reliability Workbook" > "Infra Automation Health Check" sheet

**Workflow Context**
- Automation runs continuously via GitHub Actions
- Monitors infrastructure repositories defined in `infrastructure-repos.yml`
- Tracks status of all workflow runs in the last 24 hours
- Aggregates success/failure metrics per repository
- Identifies failed actions for investigation
- Reports daily aggregated metrics to tracking worksheet


### Lead Time

**Definition**  
Time taken from when an issue is created until it is deployed to production and marked as done.

**Measurement Logic/Formula**
- Calculated by tracking status changes in Jira tickets
- Formula: Lead Time = (Resolution Time - Creation Time) / 3600 (converted to hours)
- Tracked per team through Jira issue transitions

**Data Sources**
- Primary: Jira API
- Location: `jira-kpi-to-sheets/lead-time.py`
- Frequency: Weekly
- Storage: "Production Reliability Workbook" > "Lead Time" worksheet

**Workflow Context**
- Automation runs on a weekly schedule via GitHub Actions
- Fetches all issues that transitioned to "Done" in the last week
- Filters issues by team using `teams.yml` configuration
- Calculates lead time for each issue from creation to deployment
- Aggregates data by team and updates the worksheet
- Supports tracking of deployment pipeline efficiency

### Story Points Closed

**Definition**  
Tracks completed story points per sprint per project to measure team velocity.

**Measurement Logic/Formula**
- Simple sum of story points for completed issues in a sprint
- Formula: Total Story Points = Σ(Points for Completed Issues in Sprint)
- Aggregated by team and sprint period

**Data Sources**
- Primary: Jira API
- Location: `jira-kpi-to-sheets/story-point-closed.py`
- Frequency: Per sprint (bi-weekly)
- Storage: "Production Reliability Workbook" > "Story Points Closed" worksheet

**Workflow Context**
- Automation runs at the end of each sprint via GitHub Actions
- Fetches completed issues from Jira using JQL queries
- Filters issues by team using `teams.yml` configuration
- Sums story points for completed issues
- Tracks velocity trends over time
- Updates worksheet with sprint-wise breakdown per team

### Change Failure Rate

**Definition**  
The percentage of deployments that result in failures or require remediation.

**Measurement Logic/Formula**
- Formula: (Failed Deployments / Total Deployments) * 100
- Failed deployments = Issues that moved to post-deployment QA but did not reach Done
- Total deployments = All issues that reached post-deployment QA

**Data Sources**
- Primary: Jira API
- Location: `jira-kpi-to-sheets/change-failure-rate.py`
- Frequency: Weekly
- Storage: "Production Reliability Workbook" > "Change Failure Rate" worksheet

**Workflow Context**
- Automation runs weekly via GitHub Actions
- Queries Jira for issues using JQL
- Uses `teams.yml` to identify teams and their projects
- Tracks transitions through deployment states
- Identifies failed deployments by state changes
- Calculates failure rates per team
- Supports deployment quality tracking and improvement initiatives

### Deployment Frequency

**Definition**  
Measures how often the team successfully deploys to production.

**Measurement Logic/Formula**
- Tracks successful deployments to production per team
- Calculates total deployments per week for each team
- Based on transitions to post-deployment states in Jira
- Formula: Count of successful deployments per week

**Data Sources**
- Primary: Jira API
- Location: `jira-kpi-to-sheets/deployment-frequency.py`
- Frequency: Weekly
- Storage: "Production Reliability Workbook" > "Deployments per Engineer" worksheet

**Workflow Context**
- Scheduled weekly automation via GitHub Actions
- Fetches deployment data from Jira using JQL
- References `teams.yml` for team configurations
- Tracks deployment state transitions
- Filters for successful deployments only
- Aggregates deployment counts by team and week
- Provides insights into deployment velocity

### Average Deployments per Engineer

**Definition**  
Measures the distribution of deployments across team members.

**Measurement Logic/Formula**
- Tracks deployments by individual engineers
- Formula: Total Team Deployments / Number of Active Engineers
- Provides insights into team workload distribution
- Calculated weekly per team and engineer

**Data Sources**
- Primary: Jira API
- Location: `jira-kpi-to-sheets/deployment-frequency.py`
- Frequency: Weekly
- Storage: "Production Reliability Workbook" > "Deployments per Engineer" worksheet

**Workflow Context**
- Weekly automated analysis via GitHub Actions
- Integrates with `teams.yml` for team member information
- Queries Jira for deployment transitions
- Maps deployments to individual engineers
- Calculates deployment distribution metrics
- Identifies deployment load balancing opportunities
- Supports team capacity planning

### Mean Time Between Failures

**Definition**  
Measures the average time between system failures/outages.

**Measurement Logic/Formula**
- Tracks downtime events from UptimeRobot monitoring
- Only counts downtimes longer than 120 seconds
- Only includes internal services (defined in monitors.yml)
- Formula: Σ(Time between consecutive failures) / Number of failures
- Calculated for each service defined in configuration

**Data Sources**
- Primary: UptimeRobot API
- Location: `uptime-to-sheets/mean-time-between-failure.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook"

**Workflow Context**
- Monthly automated collection via GitHub Actions
- Pulls monitoring data from UptimeRobot API
- Uses `monitors.yml` to identify critical services
- Filters out maintenance windows and brief outages
- Calculates time between significant failures
- Aggregates MTBF metrics by service
- Helps identify reliability trends and areas for improvement

### Mean Time To Restore

**Definition**  
Measures how long it takes to restore service after an outage.

**Measurement Logic/Formula**
- For each downtime event:
  1. Records timestamp when service goes down
  2. Records timestamp when service recovers
  3. Calculates duration = (recovery_time - downtime_time)
- MTTR = Average of all recovery durations in the period
- Calculated per service and aggregated for overall health

**Data Sources**
- Primary: UptimeRobot API
- Location: `uptime-to-sheets/mean-time-to-restore.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Mean Time To Restore" worksheet

**Workflow Context**
- Monthly automated analysis via GitHub Actions
- Pulls downtime data from UptimeRobot API
- Uses `monitors.yml` to identify monitored services
- Calculates recovery times for each incident
- Filters and categorizes incidents by service
- Generates MTTR metrics per service
- Supports incident response improvement initiatives
- Identifies services needing reliability improvements

### Customer Impacting Incidents

**Definition**  
Tracks the number and details of incidents that impacted customers.

**Measurement Logic/Formula**
- Counts incidents affecting customer-facing services
- Categorizes incidents by severity and duration
- Tracks impact scope (users affected, services disrupted)
- Includes both complete outages and degraded service states

**Data Sources**
- Primary: UptimeRobot API
- Location: `uptime-to-sheets/customer-impacting-incidents.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook"

**Workflow Context**
- Monthly automated collection via GitHub Actions
- References `monitors.yml` for customer-facing services
- Analyzes UptimeRobot downtime events
- Filters for customer-impacting incidents
- Categorizes incidents by type and severity
- Tracks incident resolution times
- Supports customer experience improvement initiatives

### Service Uptime

**Definition**  
Measures the percentage of time that services are available and operational.

**Measurement Logic/Formula**
- Tracks uptime for all monitored services using UptimeRobot
- Formula: (Total Up Checks / Total Checks) * 100
- Calculated daily with monitoring intervals defined per service
- Excludes paused monitors and scheduled maintenance
- Weighted by service criticality defined in configuration

**Data Sources**
- Primary: UptimeRobot API
- Location: `uptime-to-sheets/uptime-to-sheets.py`
- Frequency: Daily
- Storage: "Production Reliability Workbook" > "Daily Uptime Dashboard" worksheet

**Workflow Context**
- Daily automated checks via GitHub Actions
- Pulls status data from UptimeRobot API
- Uses `monitors.yml` to identify services and their criticality
- Excludes maintenance windows defined in configuration
- Calculates uptime percentages for each service
- Aggregates overall platform availability
- Generates daily uptime reports
- Supports SLA compliance monitoring

### Transaction Success Rate

**Definition**  
Measures the success rate of different transaction types across the platform.

**Measurement Logic/Formula**  
Average of:
- (Successful Transfers / Total Transfers) * 100
- (Successful Payouts / Total Payouts) * 100 
- (Successful Collections / Total Collections) * 100
- Calculated separately for each transaction type and aggregated
- Excludes transactions cancelled by users

**Data Sources**
- Primary: New Relic Logs
- Location: `nr-metrics-to-sheets/transaction_success_rate.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Transaction Success Rate" worksheet

**Workflow Context**
- Monthly automated analysis via GitHub Actions
- Queries New Relic for transaction events
- Uses NRQL queries to aggregate success/failure counts
- Separates metrics by transaction type
- Excludes user-cancelled transactions
- Tracks trends in success rates
- Identifies transaction failure patterns
- Supports transaction reliability improvements

### Badly Handled Error Rate

**Definition**  
Measures the percentage of errors that lack proper HTTP response codes, indicating potential gaps in error handling.

**Measurement Logic/Formula**
- Formula: (Errors without HTTP codes / Total Errors) * 100
- Identifies errors where error.httpCode is null or empty
- Tracked across all services via New Relic logs
- Categorized by service and error type
- Analyzed for patterns in error handling gaps

**Data Sources**
- Primary: New Relic Logs
- Location: `nr-metrics-to-sheets/badly_handled_error_rate.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Badly Handled Error Rate" worksheet

**Workflow Context**
- Monthly automated collection via GitHub Actions
- Uses New Relic GraphQL API for log analysis
- Executes NRQL queries to identify errors
- Filters for missing HTTP response codes
- Categorizes errors by service and type
- Tracks error handling improvement progress
- Generates detailed error reports
- Supports error handling standardization efforts

### Error Rate Metrics

**Definition**  
Service-level error rates tracking system stability and reliability.

**Measurement Logic/Formula**
- Service Error Rate = (Error Count / Total Transactions) * 100
- Tracked per service through New Relic APM
- Includes 5XX errors and application exceptions
- Segmented by error type and service
- Analyzed for error patterns and trends

**Data Sources**
- Primary: New Relic APM
- Location: `nr-metrics-to-sheets/fetch_nr.py`
- Frequency: Daily, Weekly, and Monthly reports
- Storage: "Production Reliability Workbook" > "APM Metrics Report" worksheet

**Workflow Context**
- Automated collection at multiple intervals via GitHub Actions
- Uses New Relic APM APIs for service metrics
- Executes specific NRQL queries per service
- Categorizes errors by type (5XX, timeouts, etc.)
- Aggregates error rates across services
- Generates trend analysis reports
- Supports service reliability monitoring
- Enables early detection of error rate spikes

### Infrastructure Pipeline Stability

**Definition**  
Measures the stability and success rate of infrastructure automation pipelines across key infrastructure repositories.

**Measurement Logic/Formula**
- Formula: (Successful Runs / Total Runs) * 100
- Tracks:
  - Total pipeline runs
  - Successful runs
  - Failed runs
  - Details of failed actions
  - Pipeline run duration trends

**Monitored Repositories**
- fincra3-deployments: Application deployment infrastructure
- fincra3-infra: Core infrastructure components
- kele-app-infra: Kele mobile app infrastructure
- fincra-org-infra: Organization-wide infrastructure

**Data Sources**
- Primary: GitHub Actions API
- Location: `infrastructure-automation-pipeline-stability/main.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Infrastructure Automation Pipeline Stability" worksheet

**Workflow Context**
- Monthly automated analysis via GitHub Actions
- Pulls workflow data from GitHub Actions API
- References `infrastructure-repos.yml` for monitored repositories
- Analyzes workflow run statistics
- Identifies patterns in pipeline failures
- Tracks duration of pipeline executions
- Generates detailed failure reports
- Supports infrastructure automation reliability

### Infrastructure Cost Efficiency

**Definition**  
Measures infrastructure cost efficiency by tracking AWS costs and transaction volumes.

**Measurement Logic/Formula**
- Monthly AWS Cost (using AWS Cost Explorer)
- Transaction Count = Sum of:
  - Payment initiated events
  - Payout initiated events
  - Collection initiated events
- Cost per Transaction = Monthly AWS Cost / Total Transactions
- Tracked per service and environment

**Data Sources**
- Primary: 
  - AWS Cost Explorer API
  - New Relic Logs (for transaction counts)
- Location: `infrastructure-cost-savings/infrastructure-cost-savings.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Infrastructure Cost Efficiency" worksheet

**Workflow Context**
- Monthly automated analysis via GitHub Actions
- Fetches cost data from AWS Cost Explorer
- Queries New Relic for transaction volumes
- Correlates costs with business metrics
- Calculates cost efficiency indicators
- Identifies cost optimization opportunities
- Tracks resource utilization patterns
- Supports infrastructure cost optimization

### Infrastructure Provisioning Success Rate

**Definition**  
Measures the success rate of infrastructure "apply" workflow runs in Terraform-managed infrastructure repositories, focusing specifically on actual infrastructure provisioning operations.

**Measurement Logic/Formula**
- Tracks "apply" workflow runs in the last month for each monitored repository
- Formula: Success Rate = (Successful Apply Runs / Total Apply Runs) × 100%
- Captures details of failed runs for investigation
- Only considers workflows with "apply" in their path

**Data Sources**
- Primary: GitHub Actions API
- Location: `infrastructure-provisioning-success-rate/main.py`
- Configuration: `infrastructure-provisioning-success-rate/infrastructure-repos.yml`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Infrastructure Provisioning Success Rate" worksheet

**Workflow Context**
- Monthly automated analysis via GitHub Actions
- Monitors repositories defined in `infrastructure-repos.yml` (currently fincra-org-infra)
- For each repository:
  - Fetches all workflow runs from the previous month
  - Filters for workflows containing "apply" in their path
  - Tracks success/failure status of each run
  - Collects details of failed actions including URLs
- Updates worksheet with:
  - Monthly success rate percentage
  - Total number of provisioning attempts
  - Count of successful and failed runs
  - Links to failed workflow runs for investigation
- Supports infrastructure reliability monitoring and improvement initiatives

**Measurement Logic/Formula**
- Monthly AWS Cost (using AWS Cost Explorer)
- Transaction Count = Sum of:
  - Payment initiated events
  - Payout initiated events
  - Collection initiated events
- Cost per Transaction = Monthly AWS Cost / Total Transactions



