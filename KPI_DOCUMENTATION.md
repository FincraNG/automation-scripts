# Production Reliability KPI Documentation

This document provides comprehensive documentation for all Key Performance Indicators### Infrastructure Automation Health Check
**Definition**  
Measures the health and reliability of infrastructure automation workflows across all infrastructure repositories.

**Calculation Method**  
- Tracks workflow runs in the last 24 hours across all infrastructure repositories
- Success Rate = (Successful Runs / Total Runs) × 100%
- Failure Rate = (Failed Runs / Total Runs) × 100%

**Data Collection**
- Source: GitHub Actions API
- Frequency: Continuous monitoring with daily aggregation
- Storage: Results stored in "Production Reliability Workbook" > "Infra Automation Health Check" sheet

**Purpose**
- Monitor the stability of infrastructure automation workflows
- Early detection of infrastructure automation issues
- Track reliability of deployment and infrastructure management processes

**Target Thresholds**
- Green: Success Rate ≥ 95%
- Yellow: Success Rate between 85-95%
- Red: Success Rate < 85%

### System Reliability KPIs(KPIs) being tracked across Fincra's production systems.

## Table of Contents

1. [Development Performance KPIs](#development-performance-kpis)
   - [Lead Time](#lead-time)
   - [Story Points Closed](#story-points-closed)
2. [Deployment Quality KPIs](#deployment-quality-kpis)
   - [Change Failure Rate](#change-failure-rate)
   - [Deployment Frequency](#deployment-frequency)
   - [Average Deployments per Engineer](#average-deployments-per-engineer)
3. [System Reliability KPIs](#system-reliability-kpis)
   - [Mean Time Between Failures (MTBF)](#mean-time-between-failures)
   - [Mean Time To Restore (MTTR)](#mean-time-to-restore)
   - [Customer Impacting Incidents](#customer-impacting-incidents)
   - [Service Uptime](#service-uptime)
   - [Transaction Success Rate](#transaction-success-rate)
   - [Badly Handled Error Rate](#badly-handled-error-rate)
   - [Error Rate Metrics](#error-rate-metrics)
4. [Infrastructure Health KPIs](#infrastructure-health-kpis)
   - [Infrastructure Pipeline Stability](#infrastructure-pipeline-stability)
   - [Infrastructure Cost Efficiency](#infrastructure-cost-efficiency)
   - [Infrastructure Provisioning Success Rate](#infrastructure-provisioning-success-rate)

## Development Performance KPIs

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

**Owner**  
Engineering teams tracked in teams.yml

### Story Points Closed

**Definition**  
Tracks completed story points per sprint per project to measure team velocity.

**Measurement Logic/Formula**
- Simple sum of story points for completed issues in a sprint
- Data manually input through GitHub workflow

**Data Sources**
- Primary: Manual input via GitHub Actions workflow
- Location: `jira-kpi-to-sheets/story-point-closed.py`
- Tracking: Per sprint
- Storage: "Production Reliability Workbook" > "Story Points Closed" worksheet

**Owner**  
Project teams submitting story point data

## Deployment Quality KPIs

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

**Owner**  
Engineering teams defined in teams.yml including:
- Cross Border Product Development
- HQ
- Kele Mobile App
- Stablecoin VS
- Global Collection
- Treasury VS

### Deployment Frequency

**Definition**  
Measures how often the team successfully deploys to production.

**Measurement Logic/Formula**
- Tracks successful deployments to production per team
- Calculates total deployments per week for each team
- Based on transitions to post-deployment states in Jira

**Data Sources**
- Primary: Jira API
- Location: `jira-kpi-to-sheets/deployment-frequency.py`
- Frequency: Weekly
- Storage: "Production Reliability Workbook" > "Deployments per Engineer" worksheet

**Owner**  
Engineering teams defined in teams.yml

### Average Deployments per Engineer

**Definition**  
Measures the distribution of deployments across team members.

**Measurement Logic/Formula**
- Tracks deployments by individual engineers
- Formula: Total Team Deployments / Number of Active Engineers
- Provides insights into team workload distribution

**Data Sources**
- Primary: Jira API
- Location: `jira-kpi-to-sheets/deployment-frequency.py`
- Frequency: Weekly
- Storage: "Production Reliability Workbook" > "Deployments per Engineer" worksheet

**Owner**  
Engineering teams defined in teams.yml

## System Reliability KPIs

### Mean Time Between Failures

**Definition**  
Measures the average time between system failures/outages.

**Measurement Logic/Formula**
- Tracks downtime events from UptimeRobot monitoring
- Only counts downtimes longer than 120 seconds
- Only includes internal services (defined in monitors.yml)
- Calculates average time between detected downtimes

**Data Sources**
- Primary: UptimeRobot API
- Location: `uptime-to-sheets/mean-time-between-failure.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook"

**Owner**  
Platform Reliability team

### Mean Time To Restore

**Definition**  
Measures how long it takes to restore service after an outage.

**Measurement Logic/Formula**
- For each downtime event:
  1. Records timestamp when service goes down
  2. Records timestamp when service recovers
  3. Calculates duration = (recovery_time - downtime_time)
- MTTR = Average of all recovery durations in the period

**Data Sources**
- Primary: UptimeRobot API
- Location: `uptime-to-sheets/mean-time-to-restore.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Mean Time To Restore" worksheet

**Owner**  
Platform Reliability team

### Customer Impacting Incidents

**Definition**  
Tracks the number and details of incidents that impacted customers.

**Data Sources**
- Primary: UptimeRobot API
- Location: `uptime-to-sheets/customer-impacting-incidents.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook"

**Owner**  
Platform Reliability team

### Service Uptime

**Definition**  
Measures the percentage of time that services are available and operational.

**Measurement Logic/Formula**
- Tracks uptime for all monitored services using UptimeRobot
- Formula: (Total Up Checks / Total Checks) * 100
- Calculated daily with monitoring intervals defined per service
- Excludes paused monitors from calculations

**Data Sources**
- Primary: UptimeRobot API
- Location: `uptime-to-sheets/uptime-to-sheets.py`
- Frequency: Daily
- Storage: "Production Reliability Workbook" > "Daily Uptime Dashboard" worksheet

**Owner**  
Platform Reliability team

### Transaction Success Rate

**Definition**  
Measures the success rate of different transaction types across the platform.

**Measurement Logic/Formula**  
Average of:
- (Successful Transfers / Total Transfers) * 100
- (Successful Payouts / Total Payouts) * 100 
- (Successful Collections / Total Collections) * 100

**Data Sources**
- Primary: New Relic Logs
- Location: `nr-metrics-to-sheets/transaction_success_rate.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Transaction Success Rate" worksheet

**Owner**  
Platform Engineering team

### Badly Handled Error Rate

**Definition**  
Measures the percentage of errors that lack proper HTTP response codes, indicating potential gaps in error handling.

**Measurement Logic/Formula**
- Formula: (Errors without HTTP codes / Total Errors) * 100
- Identifies errors where error.httpCode is null or empty
- Tracked across all services via New Relic logs

**Data Sources**
- Primary: New Relic Logs
- Location: `nr-metrics-to-sheets/badly_handled_error_rate.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Badly Handled Error Rate" worksheet

**Owner**  
Platform Engineering team

### Error Rate Metrics

**Definition**  
Service-level error rates tracking system stability and reliability.

**Measurement Logic/Formula**
- Service Error Rate = (Error Count / Total Transactions) * 100
- Tracked per service through New Relic APM
- Includes 5XX errors and application exceptions

**Data Sources**
- Primary: New Relic APM
- Location: `nr-metrics-to-sheets/fetch_nr.py`
- Frequency: Daily, Weekly, and Monthly reports
- Storage: "Production Reliability Workbook" > "APM Metrics Report" worksheet

**Owner**  
Platform Engineering team

## Infrastructure Health KPIs

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

**Monitored Repositories**
Tracks pipelines in the following infrastructure repositories:
- fincra3-deployments: Application deployment infrastructure
- fincra3-infra: Core infrastructure components
- kele-app-infra: Kele mobile app infrastructure
- fincra-org-infra: Organization-wide infrastructure

**Data Sources**
- Primary: GitHub Actions API
- Location: `infrastructure-automation-pipeline-stability/main.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Infrastructure Automation Pipeline Stability" worksheet

**Owner**  
Infrastructure Engineering team

### Infrastructure Cost Efficiency

**Definition**  
Measures infrastructure cost efficiency by tracking AWS costs and transaction volumes.

### Infrastructure Provisioning Success Rate

**Definition**  
Measures the success rate of infrastructure provisioning and configuration management across all environments.

**Measurement Logic/Formula**
- Tracks success of infrastructure deployments and configuration changes
- Formula: (Successful Provisioning Jobs / Total Provisioning Jobs) * 100
- Monitors configuration drift through automated checks
- Includes both initial provisioning and configuration updates

**Configuration Management**
Monitors configuration drift and provisioning success in:
- fincra-org-infra: Primary infrastructure configuration repository
- Infrastructure templates and configurations
- Terraform state and resource provisioning
- CloudFormation templates and deployments

**Data Sources**
- Primary: GitHub Actions Workflow API
- Location: `infra-config-drift-audit/main.py`
- Frequency: Daily checks with weekly reporting
- Storage: "Production Reliability Workbook" > "Infra Config Drift Audit" worksheet

**Target Thresholds**
- Green: Success Rate ≥ 98%
- Yellow: Success Rate between 90-98%
- Red: Success Rate < 90%

**Owner**  
Infrastructure Engineering team

**Measurement Logic/Formula**
- Monthly AWS Cost (using AWS Cost Explorer)
- Transaction Count = Sum of:
  - Payment initiated events
  - Payout initiated events
  - Collection initiated events
- Cost per Transaction = Monthly AWS Cost / Total Transactions

**Data Sources**
- Primary: 
  - AWS Cost Explorer API
  - New Relic Logs (for transaction counts)
- Location: `infrastructure-cost-savings/infrastructure-cost-savings.py`
- Frequency: Monthly
- Storage: "Production Reliability Workbook" > "Infrastructure Cost Efficiency" worksheet

**Owner**  
Infrastructure/Platform team

## Data Collection and Storage

All KPIs are collected and stored in the "Production Reliability Workbook" Google Sheets document, with different worksheets for each metric. Data collection is automated through various APIs:

- Jira API for development metrics
- New Relic API for application performance metrics
- UptimeRobot API for uptime and incident metrics
- AWS Cost Explorer API for infrastructure costs
- GitHub API for pipeline statistics

Updates are performed through GitHub Actions workflows on daily, weekly, or monthly schedules depending on the metric.

## Monitoring and Alerts

While this documentation focuses on KPI measurement and tracking, these metrics are also used in real-time monitoring and alerting systems through:

- New Relic APM alerts
- UptimeRobot monitoring
- GitHub Actions workflow notifications

## Repository Structure

```
.
├── infra-automation-health-check/        # Infrastructure health monitoring
├── infra-config-drift-audit/            # Configuration drift detection
├── infrastructure-automation-pipeline-stability/
├── infrastructure-cost-savings/          # Cost efficiency tracking
├── jira-kpi-to-sheets/                  # Development metrics
├── nr-metrics-to-sheets/                # Application metrics
└── uptime-to-sheets/                    # Uptime and incident metrics
```

Each directory contains the scripts and configuration files needed to collect and report its respective metrics.
