# 004 - Store Fasting Overrides in DynamoDB

**Date:** 2025-04-12

## Status
Accepted

## Context
During extra or skipped fasting days, need a method to record deviations from initially outlined fasting schedule, to ensure accurate health data correlation.

## Decision
Provide fasting override on online dashboard, which directly interfaces with fasting calendar in DynamoDB.

## Consequences
- Accessible from anywhere, due to being integrated into the dashboard.
- No JSON files needed.
- Requires dashboard UI to be deployed before overrides can be utilized.