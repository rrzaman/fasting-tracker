# 021 - IAM Least Privilege Custom Policies

**Date:** 2025-05-01

## Status

Accepted

## Context

Lambda IAM role used AmazonDynamoDBFullAccess and AmazonSNSFullAccess — broad managed policies granting access to all DynamoDB tables and SNS resources in the account, not just project resources.

## Decision

Replace broad managed policies with inline custom policies scoped to specific table ARNs and specific actions. DynamoDB policy grants only GetItem, PutItem, UpdateItem, DeleteItem, Query, Scan, BatchWriteItem on the five project tables. SNS policy grants only sns:Publish.

## Consequences

- More controlled permissions, preventing potential data breaches for other resources.
- Compartmentalizes permission to focus solely on this project.
