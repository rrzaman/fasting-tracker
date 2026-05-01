# 018 - Idempotent Reminder Tracking with DynamoDB

**Date:** 2026-04-30

## Status

Accepted

## Context

AWS EventBridge could theoretically trigger the Lambda reminder function more than once per day on accident. Without deduplication, recipients would receive duplicate SMS messages which is disruptive and unprofessional.

## Decision

Add a `reminder-log` DynamoDB table that records each reminder sent, keyed by date + fast_type. Before sending, check if a reminder was already sent today for that fast type. After sending, write a log record. Records auto-expire after 30 days via DynamoDB TTL.

## Consequences

- Guaranteed at-most-once delivery per fast type per day
- No duplicate SMS regardless of Lambda retry behaviour
- Minimal cost — one read + one write per reminder per day
- 30-day TTL keeps the table clean automatically
- DynamoDB is appropriate here — simple key lookup, no joins needed
