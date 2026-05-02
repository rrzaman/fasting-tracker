# 023 - CloudWatch Alarms for Operational Monitoring

**Date:** 2026-05-02

## Status

Accepted

## Context

The system had no alerting, failures were only discoverable by checking CloudWatch logs or noticing that reminders stopped arriving. A production system serving real users needs proactive failure detection.

## Decision

Add four CloudWatch metric alarms managed via Terraform in a new monitoring module. Alarms cover reminder Lambda errors, reminder Lambda duration, API Lambda errors, and DynamoDB throttling. All alarms notify via a dedicated SNS to email.

## Consequences

- Failures are detected within one evaluation period (5 minutes for API, 24 hours for daily reminder)
- Email notifications on every state transition (OK, ALARM, INSUFFICIENT_DATA)
- Alarm infrastructure is version controlled and reproducible via Terraform
- fasting-tracker-local IAM user required CloudWatchFullAccess to manage alarms
