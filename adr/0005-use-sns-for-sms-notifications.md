# 005 - Use SNS for SMS Notifications

**Date:** 2025-04-12

## Status
Accepted

## Context
Need a notification system to remind user(s) of upcoming fasting dates. Both email and SMS were considered.

## Decision
SMS notifications via the Amazon Simple Notification Service (SNS) platform.

## Consequences
- ~$1 CAD/month at a personal scale.
- Reaches recipients without requiring email.
- Simple to add additional phone numbers and feels more personalized and more likely to be read.