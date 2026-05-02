# 020 - Cognito JWT Authorization on API Gateway Routes

**Date:** 2026-05-01

## Status

Accepted

## Context

API Gateway routes were publicly accessible — any request to the API URL would reach Lambda and return real health data regardless of whether the caller was authenticated. Cognito protected the dashboard frontend but the underlying API had no independent auth layer.

## Decision

Add a JWT authorizer to API Gateway pointing at the Cognito user pool. Every request to protected routes must include a valid token. API Gateway validates the token's signature and expiry with Cognito before forwarding to Lambda. The /status route is intentionally left without auth as it contains no personal health data.

## Consequences

- Unauthenticated requests return 401 before Lambda executes
- Health data is protected at the infrastructure layer, not just the UI
- React must include the Cognito id_token in every API request header
- Demo mode bypasses the API entirely, so no token is needed for demos
