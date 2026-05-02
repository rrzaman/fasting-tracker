# 022 - Moto Integration Tests for Lambda Functions

**Date:** 2025-05-01

## Status

Accepted

## Context

Need integration testing to ensure AWS infrastructure interactions worked correctly without risking actual strucuture or incurring additional charges.

## Decision

Utilize moto library to create mock AWS infrastructure and test all functions.

## Consequences

- Allows for more thorough development prior to deployment.
- Saves cost and potentially messing up existing infrastructure.
- Easier to pinpoint immediate issues that arise.
