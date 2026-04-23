# 010 - Add pytest Unit Tests for Core Functions

**Date:** 2026-04-22

## Status

Accepted

## Context

Core classification and message-building logic contains conditional branches that are difficult to verify manually. Automated tests catch regressions when logic changes.

## Decision

Use pytest to unit test pure functions — build_message(), classify_day(),
and format_date(). Focus on boundary cases and the "first day only"
notification logic.

## Consequences

- Regressions caught immediately when modifying message logic.
- Tests serve as living documentation of expected behaviour.
- pytest is industry standard.
- Lambda deployment and ingestion pipeline scripts remain untested
  for now (require AWS mocking which adds complexity).
