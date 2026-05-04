# Roadmap

## Completed

- ✅ Apple Health XML ingestion pipeline
- ✅ Hijri calendar integration (Aladhan API)
- ✅ AWS DynamoDB storage (health-snapshots, fasting-records, fasting-overrides)
- ✅ Lambda daily reminder function with EventBridge
- ✅ SNS SMS notifications (English + Bengali)
- ✅ API Gateway REST API (health, fasting, overrides endpoints)
- ✅ React dashboard (calendar, health trends, settings)
- ✅ CloudFront HTTPS deployment
- ✅ AWS Cognito authentication
- ✅ pytest unit tests + GitHub Actions CI
- ✅ Architecture Decision Records
- ✅ Fasting day detail panel (click calendar day → see health metrics)
- ✅ Real last-upload date in Settings from DynamoDB
- ✅ Demo mode with synthetic data for public viewing
- ✅ Terraform infrastructure as code (modular, all AWS resources)
- ✅ Idempotent reminder tracking (reminder-log DynamoDB table)
- ✅ CloudWatch system status panel in Settings
- ✅ CloudWatch metric alarms for all Lambda functions and DynamoDB
- ✅ Modular deployment scripts (deploy-lambda.sh, deploy-frontend.sh)
- ✅ Security and privacy documentation
- ✅ Cognito JWT authorization on API Gateway routes
- ✅ IAM least-privilege custom policies
- ✅ Notification recipients stored in DynamoDB
- ✅ moto integration tests for all Lambda functions
- ✅ Statistical health insights (t-test, trend detection, consistency score)
- ✅ Visual enhancements (aurora, constellation lines, Islamic geometric tessellation, loading skeletons)
- ✅ Python type hints across all Lambda and ingestion files with mypy CI enforcement
- ✅ 25 Architecture Decision Records
- ✅ React error boundary wrapping each tab content area with fallback UI
- ✅ Frontend smoke tests with Vitest + `@testing-library/react` (DemoBanner, FastingCalendar, HealthTrends, App auth gate)
- ✅ Frontend tests wired into GitHub Actions CI alongside pytest and mypy

## Planned — Near Term

- Custom Cognito login page
- Mobile responsive design
- Operational runbook
- Deeper health analytics — HRV, sleep stage breakdown, fasting hours (Fajr to Maghrib)
- Expanded frontend test coverage (Settings tab, calendar interaction, override flows)

## Planned — Later

- Aurora Serverless migration for health-snapshots (complex analytical queries)
- Automated Apple Health ingestion via Mac script or iOS Shortcut
- Deeper health analytics — HRV, sleep stage breakdown, fasting hours (Fajr to Maghrib)
- Multi-user support with individual dashboards
- Custom domain
- Case study writeup

## Known Limitations

- Aladhan API uses astronomical calculation — may differ from moon-sighting announcements by one day
- Ramadan notification fires on day 1 rather than the night before
- Apple Health requires manual export every ~2 weeks
- DynamoDB not optimal for complex analytical queries (see ADR-012)
- Weekly aggregation in Health Trends flags weeks containing any fasting day as a fasting week — majority-threshold fix planned
- Sleep data calculation uses sum of REM + Core + Deep stages; InBed time excluded intentionally
