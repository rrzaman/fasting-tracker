# CLAUDE.md — Fasting Health Dashboard

This file gives Claude Code instant context on the project architecture,
conventions, and current state. Read this before making any changes.

## Project Summary

Personal Islamic fasting health dashboard built by Rayyan Zaman (Calgary, AB).
Integrates Apple Health data with Islamic fasting schedule. Sends automated
SMS reminders daily and displays health correlations on a React dashboard.

Live URL: https://d225kyvnm52aug.cloudfront.net (Cognito auth required)
Demo: click "Try Demo" on login screen (synthetic data, no auth needed)
GitHub: https://github.com/rrzaman/fasting-tracker

## Tech Stack

- **Backend:** Python 3.13, AWS Lambda, DynamoDB, S3, SNS, EventBridge
- **Frontend:** React 18, Vite, Recharts, react-oidc-context
- **Infrastructure:** Terraform (modules pattern), API Gateway HTTP API
- **Auth:** AWS Cognito (ca-west-1_s938OjSzp)
- **CI:** GitHub Actions running pytest on every push to main
- **Deployment:** deploy.sh (full), deploy-lambda.sh, deploy-frontend.sh

## Repository Structure

```
fasting-tracker/
├── ingestion/                   # Local data pipeline (run manually)
│   ├── parse_health_export.py   # Parses Apple Health XML export
│   ├── fetch_hijri_calendar.py  # Builds fasting calendar via Aladhan API
│   └── upload_to_aws.py         # Uploads to DynamoDB + S3
├── lambda_function/             # All AWS Lambda functions
│   ├── reminder_function.py     # Daily SMS reminders (EventBridge trigger)
│   ├── get_health_data.py       # GET /health API endpoint
│   ├── get_fasting_data.py      # GET /fasting API endpoint
│   ├── manage_overrides.py      # GET/POST/PUT/DELETE /overrides
│   └── get_system_status.py     # GET /status (CloudWatch + DynamoDB)
├── frontend/                    # React dashboard
│   └── src/
│       ├── App.jsx              # Root — auth gate + tab routing
│       ├── api.js               # All API calls (single source of truth)
│       ├── cognitoConfig.js     # Cognito OIDC config
│       ├── demoData.js          # Synthetic data for demo mode
│       ├── constants.js         # Shared fast type colours/labels
│       ├── hooks/
│       │   └── useDashboardData.js  # Fetches health + fasting on mount
│       └── components/
│           ├── FastingCalendar.jsx  # Calendar with Hijri dates + legend
│           ├── HealthTrends.jsx     # Recharts health correlation charts
│           ├── Settings.jsx         # System status + overrides + recipients
│           ├── StarCanvas.jsx       # Shooting stars background animation
│           ├── CrescentMoon.jsx     # SVG crescent in header
│           └── DemoBanner.jsx       # Demo mode indicator banner
├── tests/                       # pytest unit tests
│   ├── test_build_message.py
│   ├── test_classify_day.py
│   └── test_format_date.py
├── terraform/
│   ├── environments/prod/       # Entry point — calls all modules
│   └── modules/
│       ├── storage/             # DynamoDB tables + S3 buckets
│       ├── lambda/              # Lambda functions + IAM role
│       ├── api/                 # API Gateway routes + integrations
│       ├── notifications/       # EventBridge schedule
│       ├── auth/                # Cognito user pool
│       └── frontend/            # CloudFront + S3 frontend bucket
├── adr/                         # Architecture Decision Records
├── deploy.sh                    # Full deployment (Lambda + frontend)
├── deploy-lambda.sh             # Lambda only: ./deploy-lambda.sh [function]
├── deploy-frontend.sh           # Frontend only
├── requirements.txt
├── SECURITY.md
└── ROADMAP.md
```

## AWS Resources

| Resource          | Name/ID                        |
| ----------------- | ------------------------------ |
| Region            | ca-west-1                      |
| Account           | 845517756474                   |
| API Gateway       | 7vdm33gmxh (prod stage)        |
| CloudFront        | EB3M9H9U2HHW1                  |
| Cognito User Pool | ca-west-1_s938OjSzp            |
| Lambda Role       | fasting-tracker-lambda-role    |
| S3 (Lambda zips)  | fasting-tracker-rayyan/lambda/ |
| S3 (Frontend)     | fasting-tracker-frontend       |

## API Endpoints

Base URL: `https://7vdm33gmxh.execute-api.ca-west-1.amazonaws.com/prod`

| Method | Path       | Lambda            | Description                                       |
| ------ | ---------- | ----------------- | ------------------------------------------------- |
| GET    | /health    | get_health_data   | Health snapshots (?days=90)                       |
| GET    | /fasting   | get_fasting_data  | Fasting calendar (?days_back=365&days_forward=90) |
| GET    | /overrides | manage_overrides  | All fasting overrides                             |
| POST   | /overrides | manage_overrides  | Create override                                   |
| PUT    | /overrides | manage_overrides  | Update override                                   |
| DELETE | /overrides | manage_overrides  | Delete override (?date=YYYY-MM-DD)                |
| GET    | /status    | get_system_status | CloudWatch + system health                        |

## DynamoDB Tables

| Table             | Partition Key | Sort Key      | Notes                             |
| ----------------- | ------------- | ------------- | --------------------------------- |
| fasting-records   | date (S)      | —             | Fasting calendar                  |
| health-snapshots  | date (S)      | metric (S)    | Apple Health data                 |
| fasting-overrides | date (S)      | —             | User overrides                    |
| reminder-log      | date (S)      | fast_type (S) | Idempotent send tracking, 30d TTL |

## Key Conventions

**Python:**

- All dates as `YYYY-MM-DD` strings in DynamoDB
- Timezone-aware dates via `get_local_today()` using `America/Edmonton`
- `Decimal` used for DynamoDB numerics (not float)
- `build_message(item, lang="en")` returns None if no message needed
- `MESSAGES` dict uses lambda functions for all message strings

**React:**

- `useDashboardData` hook fetches all data once on app mount
- Data passed as props to components (no individual fetching)
- `isDemoMode` prop gates API calls — demo uses `demoData.js` instead
- `fastTypeToClass` and `fastTypeToLabel` live in `constants.js`
- CSS variables for all colours — defined in `:root` in `App.css`
- Nabawi colour palette: deep emerald greens + warm gold accents

**Deployment:**

- `./deploy-lambda.sh get-status` to deploy a single function
- `./deploy-lambda.sh reminder` for the full package (pandas etc.)
- `./deploy-frontend.sh` after any React changes
- `./deploy.sh` for full releases
- Always run `terraform plan` before `terraform apply`
- `terraform.tfvars` is gitignored — contains phone numbers

**Testing:**

- Run `pytest -v` from project root
- GitHub Actions runs pytest on every push to main
- Tests are pure unit tests — no AWS mocking yet (moto planned)

## Fasting Logic

Types: `ramadan`, `weekly_sunnah`, `ayyam_al_bid`, `dhul_hijjah_early`,
`arafah`, `ashura`, `prohibited` (with `celebration_type`)

Special cases:

- Dhul Hijjah 13th is Ayyam al-Tashreeq (prohibited) — fast 14th/15th/16th instead
- Ashura preference: 9th + 10th of Muharram (ASHURA_PREFERENCE = "early")
- Ramadan notification fires on hijri_day == 1 (correct — Lambda runs day before)
- Ayyam al-Bid notification fires on hijri_day == 13 (day before white days begin)

## Known Limitations

- Apple Health requires manual XML export every ~2 weeks
- Aladhan API uses astronomical calculation — may differ from moon-sighting by 1 day
- API Gateway routes have no auth (NONE) — Cognito JWT planned
- IAM uses broad DynamoDB/SNS full access — least-privilege planned
- Weekly aggregation in HealthTrends flags any fasting-day week as fasting week

## What's In Progress / Planned

See ROADMAP.md for full list. Near-term:

- Cognito JWT authorization on API Gateway routes
- IAM least-privilege custom policies
- moto integration tests
- Security and privacy README section
- Operational runbook
