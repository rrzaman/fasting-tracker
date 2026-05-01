#!/bin/bash
set -e
export AWS_PAGER=""

echo "=== Fasting Tracker Full Deployment ==="

echo "Deploying Lambda functions..."
./deploy-lambda.sh all

echo "Deploying frontend..."
./deploy-frontend.sh

echo ""
echo "=== Deployment Complete ==="
echo "Frontend: https://d225kyvnm52aug.cloudfront.net"