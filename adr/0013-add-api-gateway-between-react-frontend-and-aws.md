# 013 - Add API Gateway Between React Frontend and AWS

**Date:** 2026-04-25

## Status

Planned

## Context

React frontend needs to read fasting and health data from DynamoDB. Querying
DynamoDB directly from the browser would require exposing AWS credentials
in client-side code — a serious security risk.

## Decision

Add AWS API Gateway as a REST API layer between the React frontend and
DynamoDB. Lambda functions handle each endpoint and query DynamoDB server-side.

## Consequences

- AWS credentials never exposed to the browser
- Clean separation between frontend and data layer
- Adds one Lambda function per API endpoint
- Follows industry standard architecture for React + AWS applications
- Implementation deferred until after initial frontend is functional
