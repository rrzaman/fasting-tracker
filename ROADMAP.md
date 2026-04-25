# Roadmap

## In Progress

- React dashboard
- S3 static hosting

## Planned — Near Term

- API Gateway REST API layer
- GitHub Actions CI pipeline
- AWS Cognito authentication

## Planned — Later

- Aurora Serverless for health analytics
- CloudWatch monitoring dashboard
- Automated Apple Health ingestion
- Deeper health analysis including focus on fasting hours
- Mobile responsive design
- Multi-user support

## Known Limitations

- Aladhan API uses astronomical calculation — may differ from moon-sighting announcements by one day
- Ramadan notification fires on day 1 rather than the night before
- Apple Health requires manual export every ~2 weeks
- DynamoDB not optimal for complex analytical queries (see ADR-012)
