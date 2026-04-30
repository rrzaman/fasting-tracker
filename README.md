# Fasting Health Dashboard and Reminder Service

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat&logo=python&logoColor=white)
![React](https://img.shields.io/badge/React-18.2.0-61DAFB?style=flat&logo=react&logoColor=black)
![AWS Serverless](https://img.shields.io/badge/AWS_Serverless-Lambda_|_SNS-FF9900?style=flat&logo=amazonaws&logoColor=white)
![AWS Storage](https://img.shields.io/badge/AWS_Storage-DynamoDB_|_S3-4053D6?style=flat&logo=amazondynamodb&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat)

Personal fasting tracking dashboard and automated reminder service built around Islamic fasting practices.

It integrates with Apple Health data (sleep, heart rate, steps, calories) obtained from Apple Watch to analyze health trends under both fasting and non-fasting conditions. Also sends SMS reminders to subscribed users of key obligatory and supererogatory fasting dates in the Islamic (Hijri) calendar.

This project was designed after my mother got mad at me for forgetting to remind her to fast with me, after I suddenly remembered at midnight the night before.

This problem cannot be addressed by a typical calendar app due to the dynamic nature of the Hijri lunar calendar, which changes based on the sighting of the new crescent moon. The project combines personal health analytics, full-stack development, cloud infrastructure, and serverless automation into a single cohesive system.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup & Installation](#setup--installation)
- [Usage](#usage)
- [Design Decisions](#design-decisions)
- [Roadmap](#roadmap)
- [License](#license)

## Features

- **Apple Health Integration** — Parses native XML exports from Apple Watch, extracting sleep, resting heart rate, active calories, and step count.
- **Islamic Fasting Calendar** — Dynamically computes fasting schedule using the Aladhan API, classifying Ramadan, Ayyam al-Bid, Arafah, Ashura, Dhul Hijjah, and weekly Sunnah fasts with full Hijri date mapping.
- **Cloud Storage Pipeline** — Processed health and fasting data uploaded to AWS S3 (file backup) and DynamoDB (queryable records).
- **Self-Maintaining Calendar** — AWS Lambda automatically extends the fasting calendar horizon, requiring no manual intervention.
- **SMS Reminder Service** — Automated weekly reminders via AWS SNS to multiple recipients before upcoming fasting dates, including Eid greetings.
- **Health Trend Analysis** _(in progress)_ — Correlates fasting days with health metrics to surface trends across fasting vs. non-fasting conditions.
- **Personal Dashboard** _(in progress)_ — React-based web interface for viewing calendar, health correlations, and managing fasting overrides.

## Architecture

The project is structured in four layers:

**Layer 1 — Data Ingestion** _(local Python scripts)_
Parses Apple Health XML exports to extract key health metrics. Separately fetches Gregorian-to-Hijri date mappings from the AlAdhan API and classifies each day against a list of common Islamic fasting days.

**Layer 2 — Cloud Storage** _(AWS S3 + DynamoDB)_
Processed health snapshots and fasting records are uploaded to DynamoDB for fast key-based querying, with CSV backups stored in S3. DynamoDB uses a composite key of `date` + `metric` for health data and `date` alone for fasting records.

**Layer 3 — Automation** _(AWS Lambda + EventBridge)_
A scheduled Lambda function runs weekly to send SMS reminders via SNS for upcoming fasting dates, deliver Eid greetings, and self-extend the fasting calendar horizon to maintain 60 days of future records.

**Layer 4 — Dashboard** _(React, hosted on S3)_ _(in progress)_
A React single-page application served as a static site from S3, displaying the fasting calendar, health trend correlations, and fasting override controls.

See [`adr/`](./adr) for the architectural decisions behind each major design choice.

Diagram included below.

```mermaid
flowchart TD
    subgraph Local["Layer 1 — Data Ingestion (local)"]
        A[parse_health_export.py\nApple Health XML]
        B[fetch_hijri_calendar.py\nAladhan API]
    end

    subgraph AWS["Layer 2 — Cloud Storage (AWS)"]
        C[(DynamoDB\nhealth-snapshots)]
        D[(DynamoDB\nfasting-records)]
        E[S3\nCSV backups + frontend]
    end

    subgraph Automation["Layer 3 — Automation (AWS)"]
        F[Lambda\nreminder_function.py]
        G[EventBridge\nweekly schedule]
        H[SNS\nSMS to recipients]
    end

    subgraph Frontend["Layer 4 — Dashboard (in progress)"]
        I[React SPA\nhosted on S3]
    end

    A -->|upload_to_aws.py| C
    A -->|upload_to_aws.py| E
    B -->|upload_to_aws.py| D
    B -->|upload_to_aws.py| E
    G -->|triggers| F
    F -->|reads| D
    F -->|reads| C
    F -->|sends| H
    F -->|extends| D
    C --> I
    D --> I
```

## Tech Stack

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-FF9900?logo=amazon-aws&logoColor=white)
![React](https://img.shields.io/badge/React-61DAFB?logo=react&logoColor=black)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![DynamoDB](https://img.shields.io/badge/DynamoDB-4053D6?logo=amazondynamodb&logoColor=white)

| Category            | Technology               | Purpose                                                         |
| ------------------- | ------------------------ | --------------------------------------------------------------- |
| **Languages**       | Python 3.10+, JavaScript | Backend ingestion and automation, React frontend                |
| **Cloud Compute**   | AWS Lambda + EventBridge | Serverless weekly reminder function, self-triggered on schedule |
| **Cloud Storage**   | AWS DynamoDB             | Queryable fasting and health records                            |
| **Cloud Storage**   | AWS S3                   | CSV backups and static frontend hosting                         |
| **Notifications**   | AWS SNS                  | SMS reminders                                                   |
| **Frontend**        | React                    | Personal health dashboard                                       |
| **Data Processing** | pandas, boto3            | Health data aggregation, AWS SDK for Python                     |
| **External API**    | AlAdhan                  | Gregorian-to-Hijri calendar conversion                          |
| **Data Source**     | Apple HealthKit          | Health metrics via XML export from Apple Watch                  |

## Project Structure

```
fasting-tracker/
├── adr/                                # Architecture Decision Records
│   ├── 0001-choose-aws-as-cloud-platform.md
│   ├── 0002-use-manual-apple-health-export.md
│   ├── 0003-use-aladhan-api-for-hijri-calculations.md
│   ├── 0004-store-fasting-overrides-in-dynamodb.md
│   ├── 0005-use-sns-for-sms-notifications.md
│   ├── 0006-maintain-60-day-calendar-horizon.md
│   └── 0007-use-decimal-type-for-dynamodb-uploads.md
├── ingestion/                          # Local data pipeline scripts
│   ├── parse_health_export.py          # Parses Apple Health XML export
│   ├── fetch_hijri_calendar.py         # Builds fasting calendar via Aladhan API
│   └── upload_to_aws.py                # Uploads processed data to S3 and DynamoDB
├── lambda/                             # AWS Lambda function
│   └── reminder_function.py            # Sends SMS reminders, extends calendar horizon
├── frontend/                           # React dashboard (in progress)
│   └── src/
│       ├── App.jsx
│       └── components/
│           ├── Dashboard.jsx
│           └── FastingCalendar.jsx
├── data/                               # gitignored — local exports only
│   ├── export.xml                      # Apple Health XML export
│   ├── health_summary.csv              # Processed health data
│   └── fasting_calendar.csv            # Computed fasting schedule
├── .env                                # gitignored — credentials
├── requirements.txt                    # Python dependencies
├── LICENSE
└── README.md
```

## Setup & Installation

### Prerequisites

- Python 3.10+
- Git
- An AWS account with S3, DynamoDB, and SNS configured (see [`adr/`](./adr))
- An Apple Health XML export from the Health app on iPhone, optimally with Apple Watch health data (steps, heart rate, sleep, etc.)

### Steps

1. **Clone the repository**

```bash
   git clone https://github.com/rrzaman/fasting-tracker.git
   cd fasting-tracker
```

2. **Create and activate a virtual environment**

```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows (Git Bash)
   source venv/bin/activate      # macOS / Linux
```

3. **Install dependencies**

```bash
   pip install -r requirements.txt
```

4. **Configure environment variables**

   Create a `.env` file in the project root:

```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   AWS_REGION=ca-west-1
   PHONE_NUMBER_1=+1xxxxxxxxxx
```

5. **Add your Apple Health export**

   Export your data from the Health app on iPhone, unzip it, and place `export.xml` inside the `data/` folder.

6. **Run the ingestion pipeline**

```bash
   python ingestion/parse_health_export.py
   python ingestion/fetch_hijri_calendar.py
   python ingestion/upload_to_aws.py
```

## Usage

### Day-to-day

After deployment, the system runs automatically. AWS Lambda checks for upcoming fasting dates every Sunday evening and sends SMS reminders to all subscribed recipients — no manual interaction required.

### Updating health data

Apple Health does not provide a public API, so data must be exported manually every 1–2 weeks. Currently searching for alternatives to automate this process.

1. Open the **Health** app on iPhone → tap your profile picture → **Export All Health Data**
2. Unzip the export and place `export.xml` into the `data/` folder
3. Run the ingestion pipeline:
   ```bash
   python ingestion/parse_health_export.py
   python ingestion/upload_to_aws.py
   ```

### Adding or removing notification recipients

Update the phone numbers in the local `.env` file and in the Lambda environment variables in the AWS console.

### Extending the fasting calendar manually

The Lambda function self-extends the calendar automatically. To regenerate from scratch or backfill historical dates:

```bash
python ingestion/fetch_hijri_calendar.py
python ingestion/upload_to_aws.py
```

## Design Decisions

See [`adr/`](./adr) for detailed design decisions.

## Roadmap

- ✅ **April 2026:** Lambda deployment, automated SMS reminder system, initial AWS infrastructure
- **May 2026:** React dashboard with fasting calendar view and health trend correlations
- **May 2026:** AWS Cognito authentication to protect personal health data
- **June 2026:** Deeper health analytics. Heart rate variability, sleep stage breakdown during fasting, focus on fasting hours (Fajr to Maghrib).
- **Long-Term:** Automated Apple Health ingestion via scheduled Mac script or iOS Shortcut.
- **Long-Term:** Multi-user support with individual dashboards and personalized fasting schedules.

## License

Licensed under the MIT License. See [`LICENSE`](./LICENSE) for details.
