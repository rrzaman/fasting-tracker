# 002 - Use Manual Apple Health Export

**Date:** 2025-04-11

## Status
Accepted

## Context
Requires Apple Watch health data to analyze for different trends during fasting vs. non-fasting days. No public API is available.

## Decision
Manually import health data through Apple Health by exporting all health data as an XML file.

## Consequences
- Simple to implement and maintain.
- Requires manual effort to export data from phone, upload onto computer and run corresponding scripts every ~2 weeks.
- Automation possible later via Mac script or third-party tools/apps.