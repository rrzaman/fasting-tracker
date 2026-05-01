#!/bin/bash
set -e
export AWS_PAGER=""

echo "Building frontend..."
cd frontend
npm run build

echo "Deploying frontend to S3..."
for f in dist/assets/*.js; do
    aws s3 cp "$f" "s3://fasting-tracker-frontend/assets/$(basename $f)" \
        --content-type "application/javascript"
done

for f in dist/assets/*.css; do
    aws s3 cp "$f" "s3://fasting-tracker-frontend/assets/$(basename $f)" \
        --content-type "text/css"
done

aws s3 cp dist/index.html s3://fasting-tracker-frontend/index.html \
    --content-type "text/html; charset=utf-8"

aws s3 sync dist/ s3://fasting-tracker-frontend/ \
    --exclude "*.js" --exclude "*.css" --exclude "*.html"

cd ..

aws cloudfront create-invalidation \
    --distribution-id EB3M9H9U2HHW1 \
    --paths "/*" \
    --no-cli-pager

echo "Frontend deployed: https://d225kyvnm52aug.cloudfront.net"
