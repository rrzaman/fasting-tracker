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

## Planned — Near Term

- Demo mode with synthetic data for public portfolio viewing
- Custom Cognito login page matching dashboard aesthetic
- Mobile responsive design
- Loading skeleton animations
- Fasting day detail panel (click calendar day → see health metrics)
- Real last-upload date in Settings from DynamoDB

## Planned — Later

- Aurora Serverless migration for health-snapshots (complex analytical queries)
- CloudWatch monitoring dashboard
- Automated Apple Health ingestion via Mac script or iOS Shortcut
- Deeper health analytics — HRV, sleep stage breakdown, fasting hours (Fajr to Maghrib)
- Multi-user support with individual dashboards

## Known Limitations

- Aladhan API uses astronomical calculation — may differ from moon-sighting announcements by one day
- Ramadan notification fires on day 1 rather than the night before
- Apple Health requires manual export every ~2 weeks
- DynamoDB not optimal for complex analytical queries (see ADR-012)
- Weekly aggregation in Health Trends flags weeks containing any fasting day as a fasting week — majority-threshold fix planned
- Sleep data calculation uses sum of REM + Core + Deep stages; InBed time excluded intentionally
