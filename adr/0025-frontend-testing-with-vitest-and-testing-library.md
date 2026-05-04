# 025 - Frontend Testing with Vitest and Testing Library

**Date:** 2026-05-04

## Status

Accepted

## Context

The backend has 266 tests at 97% coverage but the React frontend had zero automated tests. Issues could only be detected by manually clicking through the app.

## Decision

Add Vitest for component smoke tests which cover basic paths initially such as the Sign in / Try Demo page.

Vitest chosen over Jest because it shares Vite's transformer — JSX, ESM, and path resolution all work without a separate Babel pipeline. Testing Library chosen over Enzyme because Enzyme is unmaintained for React 18+ and Testing Library's role-based queries match how a screen reader (and a user) actually find elements.

## Consequences

- Frontend issues in core render paths are caught on every push
- CI workflow extended to include covering these tests
- Will require further, more comprehensive testing in the near future, added to ROADMAP.
