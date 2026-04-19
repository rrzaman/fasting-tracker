# 001 - Choose AWS as Cloud Platform

**Date:** 2025-04-11

## Status
Accepted

## Context
This project requires cloud storage for Apple Health data, a serverless compute layer for scheduled fasting reminders and a database for fasting records. Several cloud platforms were considered such as AWS, Microsoft Azure and Google Cloud.

## Decision
Use AWS (S3, DynamoDB, Lambda, SNS, EventBridge) as the sole cloud platform.

## Consequences
- AWS free tier with an additional $100 in activity credits make it cost-free at a personal scale.
- Learning AWS is an explicit goal, providing hands-on experience.
- All services integrate natively with each other.
- Vendor lock-in to AWS. Migrating later to another platform would require rewriting code.