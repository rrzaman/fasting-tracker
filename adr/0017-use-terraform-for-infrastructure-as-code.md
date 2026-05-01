# 017 - Use Terraform for Infrastructure as Code

**Date:** 2026-04-30

## Status

Accepted

## Context

AWS infrastructure was initially provisioned manually via the AWS console. Manual provisioning is not reproducible, not version controlled, and not transferable. As the project grew to include DynamoDB, Lambda, API Gateway, Cognito, CloudFront, SNS, EventBridge, S3, and IAM roles, the need for infrastructure as code became clear.

## Decision

Use Terraform to define all AWS infrastructure. Organize using a modules pattern with a single prod environment. Existing resources will be imported into Terraform state rather than recreated.

## Consequences

- Infrastructure is fully reproducible from a single terraform apply command
- All infrastructure changes are version controlled and reviewable
- terraform import required for existing resources — one-time migration cost
- terraform.tfvars containing secrets is gitignored
- Adds Terraform as a required tool for infrastructure changes
- Directly relevant to DevOps and MLOps job applications
