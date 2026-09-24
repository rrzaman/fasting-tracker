# 026 - Store Terraform State in a Versioned S3 Backend

**Date:** 2026-09-23

## Status

Accepted

## Context

Terraform state was stored localled as `terraform.tfstate` file which only existed on machine that last ran `terraform apply`. Upon moving to a new computer, state file did not trasfer due to being gitignored. Therefore, this led to Terraform being unable to identify current configuration.

Fortunately, previous Terraform state was recovered from git history. 

## Decision

Store state in S3 using Terraform's `s3` backend, in a dedicated bucket (`fasting-tracker-tfstate-rayyan`). This is independent of the Terraform-managed infrastructure (made with AWS CLI), to prevent Terraform from accidentally deleting it. 

Also includes bucket versioning to prevent accidental changes, S3 locking to prevent multiple machines writing simultaneously, encryption, and stricter Terraform versioning.

## Consequences

- State is now shared by every machine and makes transitions more seamless
- Allows versioning of state through the bucket
- Cannot run `terraform apply` from multiple machines concurrently
- State bucket independent of all other cloud infrastructure in this project for safe storage
- Requires Terraform 1.16 or later on all machines, otherwise risking issues
- Negligible cost: around 100 KB object stored in S3
