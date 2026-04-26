# 014 - Use Timezone-Aware Dates in Lambda

**Date:** 2026-04-25

## Status

Accepted

## Context

AWS Lambda runs in UTC by default. Python's date.today() returns the UTC date, which is 6-7 hours ahead of Mountain Time (Calgary). This caused fasting reminders to fire a day early — Lambda running at 2am UTC on Sunday would query Monday's fasting record and send "tomorrow is a fasting day" while it was still Saturday evening locally.

## Decision

Replace all date.today() calls in reminder_function.py with a get_local_today() helper that uses Python's zoneinfo module to return the current date in America/Edmonton timezone.

## Consequences

- Reminders fire at the correct local time regardless of UTC offset
- America/Edmonton handles MST/MDT daylight saving automatically
- zoneinfo is built into Python 3.9+ — no additional dependencies
- All date comparisons (health lag, calendar horizon) now consistent with local time
