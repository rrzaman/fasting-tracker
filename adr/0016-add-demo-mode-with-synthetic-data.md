# 016 - Add Demo Mode With Synthetic Data

**Date:** 2026-04-30

## Status

Planned

## Context

The dashboard is protected by Cognito authentication and contains personal
health data. Other users (guests) cannot see the app without credentials.

## Decision

Add a demo mode accessible from the login screen that loads synthetic
but realistic fasting and health data without requiring authentication.
A clearly visible banner will indicate demo mode throughout the session.

## Consequences

- Others can experience the full dashboard without credentials
- Real health data remains protected behind Cognito
- Synthetic data must be realistic enough to demonstrate correlations
- Demo mode state managed in React, no AWS infrastructure changes needed
