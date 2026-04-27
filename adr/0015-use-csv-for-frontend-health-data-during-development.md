# 015 - Use CSV for Frontend Health Data During Development

**Date:** 2026-04-26

## Status

Accepted (temporary)

## Context

React frontend needs health data for visualization. API Gateway connection is planned but not yet built. Health CSV is already generated locally by the ingestion pipeline.

## Decision

Serve health_summary.csv from frontend/public/ during development, parsed client-side with Papa Parse. File excluded from git via .gitignore to protect personal health data.

## Consequences

- Frontend works immediately without AWS infrastructure
- Health data never committed to GitHub
- Must be manually copied after each ingestion run
- Replaced entirely when API Gateway is implemented
