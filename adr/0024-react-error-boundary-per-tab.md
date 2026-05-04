# 024 - React Error Boundary Per Tab Content Area

**Date:** 2026-05-04

## Status

Accepted

## Context

A render-time error anywhere in the React tree propagates to the entire app. The dashboard has three independent tabs and a bug in one should be independent and not affect the other ones.

## Decision

Wrap each tab content div in a per-tab `ErrorBoundary` rather than a single root-level boundary. Implemented as a class component (React has no hook equivalent for `componentDidCatch`). Fallback uses the existing `card--error` styling and a "Reload" button.

## Consequences

- A render error in one tab no longer affects the others
- Class component required — the only one in an otherwise hook-only frontend
- Does not catch errors in event handlers or async code (React error-boundary limitation)
