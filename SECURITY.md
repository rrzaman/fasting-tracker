# Security Policy

## Data Handled

This project processes personal health data from Apple HealthKit including resting heart rate, sleep duration, step count, and active calories. This data is stored in AWS DynamoDB in a private AWS account and is never shared.

## Security Architecture

- **Authentication:** AWS Cognito protects the dashboard — only authenticated
  users can access health data
- **Transport:** All data transmitted over HTTPS via CloudFront and API Gateway
- **Storage:** Health data stored in private DynamoDB tables, never in public
  S3 buckets or version control
- **Credentials:** AWS credentials stored in environment variables and
  Terraform tfvars files, both are gitignored
- **API:** AWS credentials never exposed to the browser — all DynamoDB access
  is server-side via Lambda

## Known Limitations

- API Gateway routes currently use AUTHORIZATION_TYPE = NONE — Cognito JWT
  authorization is planned
- IAM roles use broad managed policies — least-privilege custom policies planned
- SNS is in sandbox mode — only verified phone numbers receive SMS

## Reporting a Vulnerability

This is a personal project. If you find a security issue, please open a
GitHub issue or contact rayyan.rz5@gmail.com.
