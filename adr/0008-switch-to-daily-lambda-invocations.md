# 008 - Switch to Daily Lambda Invocations

**Date:** 2025-04-22

## Status

Accepted

## Context

Weekly Lambda runs mean reminders arrive up to 6 days before the event, making "tomorrow" language inaccurate and receiving multiple messages inconvenient.

## Decision

Run Lambda daily at 8pm Mountain Time (UTC-6)

## Consequences

- More accurate reminders.
- Negligible cost increase (<$0.5/month).
- EventBridge schedule updated.
- Daily invocations correctly catch Ramadan's first day regardless of
  whether Shaban is 29 or 30 days, since we look ahead exactly 1 day.
