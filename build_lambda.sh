#!/bin/bash
set -e

echo "Building Lambda deployment package..."

# Clean up any previous build
rm -rf lambda_package
mkdir lambda_package

# Install dependencies
echo "Python packages will be installed for linux/x86_64 (Lambda runtime)..."
pip install --platform manylinux2014_x86_64 \
    --implementation cp \
    --python-version 3.13 \
    --only-binary=:all: \
    --target lambda_package/ \
    requests pandas python-dotenv --upgrade --quiet 2>/dev/null || \
pip install --target lambda_package/ requests pandas python-dotenv --upgrade --quiet

# Copy Lambda function
cp lambda_package/reminder_function.py lambda_package/

# Copy ingestion package
mkdir lambda_package/ingestion
cp ingestion/fetch_hijri_calendar.py lambda_package/ingestion
cp ingestion/upload_to_aws.py lambda_package/ingestion
cp ingestion/parse_health_export.py lambda_package/ingestion
touch lambda_package/ingestion/__init__.py

# Create deployment zip
cd lambda_package
zip -r ../lambda_deployment.zip .
cd ..

# Clean up build folder
rm -rf lambda_package

echo "Done! lambda_deployment.zip is ready to upload to AWS."
echo "Zip size: $(du -sh lambda_deployment.zip | cut -f1)"