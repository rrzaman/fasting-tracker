# 003 - Use AlAdhan API for Hijri Calculations

**Date:** 2025-04-12

## Status
Accepted

## Context
To obtain the fasting calendar, requires the Hijri/Islamic calendar conversion of the Gregorian calendar.

## Decision
Use AlAdhan API as the primary source of converting dates from Gregorian to Hijri.

## Consequences
- Free, no API key necessary.
- Returns full month Hijri calendar data in one call.
- Uses astronomical calculations to determine Hijri calendar, which may differ from the more accurate, preferred moon-sighting-based announcements.