# 019 - Store Notification Recipients in DynamoDB

**Date:** 2026-05-01

## Status

Accepted

## Context

SMS notification recipients were hardcoded in the React frontend (Settings.jsx) and in Lambda environment variables. This means adding or removing a recipient requires both a code change and a Lambda redeployment — easy to forget and error-prone.

## Decision

Store recipients in a DynamoDB table `notification-recipients` with fields: `phone` (PK), `name`, `lang`. Fetch recipients in the get_system_status Lambda and include them in the /status API response.
The reminder Lambda reads recipients from DynamoDB instead of environment variables. The frontend displays recipients dynamically from the API response.

## Consequences

- Adding/removing recipients requires only a DynamoDB item change
- No code deployments needed for recipient management
- Single source of truth for recipient data
- Reminder Lambda needs DynamoDB read permission for new table (already covered by existing policy)
- Small additional DynamoDB read on every reminder run
