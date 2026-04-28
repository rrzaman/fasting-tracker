#!/bin/bash
set -e

echo "Building Lambda deployment packages..."

build_package() {
    local name=$1
    local source=$2

    echo "Building $name..."
    rm -rf lambda_package
    mkdir lambda_package

    cp "$source" lambda_package/lambda_function.py

    zip -r -q "${name}.zip" -j lambda_package/
    rm -rf lambda_package
    echo "Built ${name}.zip ($(du -sh ${name}.zip | cut -f1))"
}

build_full_package() {
    echo "Building fasting-tracker-reminder (full package)..."
    rm -rf lambda_package
    mkdir lambda_package

    pip install --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.13 \
        --only-binary=:all: \
        --target lambda_package/ \
        requests pandas python-dotenv --upgrade --quiet 2>/dev/null || \
    pip install --target lambda_package/ requests pandas python-dotenv --upgrade --quiet

    cp lambda_function/reminder_function.py lambda_package/

    mkdir lambda_package/ingestion
    cp ingestion/fetch_hijri_calendar.py lambda_package/ingestion/
    cp ingestion/upload_to_aws.py lambda_package/ingestion/
    cp ingestion/parse_health_export.py lambda_package/ingestion/
    touch lambda_package/ingestion/__init__.py

    cd lambda_package
    zip -r -q ../fasting-tracker-reminder.zip .
    cd ..
    rm -rf lambda_package
    echo "Built fasting-tracker-reminder.zip ($(du -sh fasting-tracker-reminder.zip | cut -f1))"
}

# Build simple API functions
build_package "fasting-tracker-get-health"      "lambda_function/get_health_data.py"
build_package "fasting-tracker-get-fasting"     "lambda_function/get_fasting_data.py"
build_package "fasting-tracker-manage-overrides" "lambda_function/manage_overrides.py"

# Build full reminder package
build_full_package

# Upload all to S3
echo "Uploading to S3..."
for zip in fasting-tracker-get-health.zip fasting-tracker-get-fasting.zip fasting-tracker-manage-overrides.zip fasting-tracker-reminder.zip; do
    aws s3 cp "$zip" "s3://fasting-tracker-rayyan/lambda/$zip"
    echo "Uploaded $zip"
done

# Deploy all to Lambda
echo "Deploying to Lambda..."
aws lambda update-function-code \
    --function-name fasting-tracker-get-health \
    --s3-bucket fasting-tracker-rayyan \
    --s3-key lambda/fasting-tracker-get-health.zip

aws lambda update-function-code \
    --function-name fasting-tracker-get-fasting \
    --s3-bucket fasting-tracker-rayyan \
    --s3-key lambda/fasting-tracker-get-fasting.zip

aws lambda update-function-code \
    --function-name fasting-tracker-manage-overrides \
    --s3-bucket fasting-tracker-rayyan \
    --s3-key lambda/fasting-tracker-manage-overrides.zip

aws lambda update-function-code \
    --function-name fasting-tracker-reminder \
    --s3-bucket fasting-tracker-rayyan \
    --s3-key lambda/fasting-tracker-reminder.zip

echo "Cleaning up zips..."
rm -f fasting-tracker-get-health.zip fasting-tracker-get-fasting.zip fasting-tracker-manage-overrides.zip fasting-tracker-reminder.zip

echo "All done! All four Lambda functions deployed."