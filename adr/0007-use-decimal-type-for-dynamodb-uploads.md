# 007 - Use Decimal Type for DynamoDB Uploads

**Date:** 2025-04-13

## Status
Accepted

## Context
DynamoDB rejects Python float types because it uses its own numeric type system. pandas DataFrames produced from CSV parsing contain numpy float64 values which boto3 cannot serialize.

## Decision
Alter uploads to convert floats to Decimal type to prevent error.

## Consequences
- Using json.loads() with parse_float = Decimal handles conversion automatically.
- One line-fix with no performance impact.