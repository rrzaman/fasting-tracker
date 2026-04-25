# 012 - Use DynamoDB Over SQL for Health and Fasting Data

**Date:** 2026-04-25

## Status

Accepted (with known limitations)

## Context

Health snapshots and fasting records require storage accessible from both Lambda and the React frontend. AWS RDS Aurora (SQL) and DynamoDB (NoSQL) were both considered.

## Decision

Use DynamoDB for fasting-records (simple date-based key lookups) and health-snapshots (date + metric composite key). Aurora Serverless considered for health analytics, but will deferred for later exploration to facilitate deeper analysis.

## Consequences

- Zero additional setup — already configured for Lambda integration.
- Simple key-based lookups are fast and free at personal scale.
- Complex analytical queries handled by combining data in Lambda memory.
- Aurora Serverless would be more appropriate for heavy analytics. Documented in ROADMAP.md for future consideration.
