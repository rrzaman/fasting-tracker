# 006 - Maintain 60 Day Calendar Horizon

**Date:** 2025-04-17

## Status
Accepted

## Context
AWS Lambda requires future fasting records to accurately send reminders. Calendar was initially generated to initial date (April 12, 2026).

## Decision
Add a rolling calendar horizon of 60 days to ensure the availability of sufficient future fasting records. 60 days provides sufficient lookahead for all notification types while minimising accumulated calendar drift from astronomical vs. moon-sighting discrepancies. Processed weekly to maintain 60 day calendar horizon.

## Consequences
- Lambda self-extends the calendar when the horizon drops below the set threshold of 60 days.
- Eliminates the need to manually regenerate fasting calendar.
- Large extensions introduce the possibilty for rolling error if moon sightings alter Hijri month (i.e. calculated date is inaccurate).