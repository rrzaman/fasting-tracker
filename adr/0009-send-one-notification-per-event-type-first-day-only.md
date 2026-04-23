# 009 - Send One Notification Per Event Type, First Day Only

**Date:** 2025-04-22

## Status

Accepted

## Context

Multi-day fasting periods (Ramadan, Ayyam al-Bid, Dhul Hijjah) would generate repeated identical reminders.

## Decision

Only send notifications on the day before an event begins, return None for subsequent days (e.g. only on the first of Ramadan, not daily)

## Consequences

- Cleaner user experience
- Fewer reminders for fasting which may lead to forgetting
- Ramadan daily reminders intentionally omitted after day 1 —
  users are expected to know they are fasting once Ramadan begins.
