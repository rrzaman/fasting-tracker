#!/bin/bash
set -e
export AWS_PAGER=""

TARGET=${1:-"all"}

build_and_deploy() {
    local name=$1
    local source=$2
    local full=${3:-false}

    echo "Building fasting-tracker-${name}..."
    rm -rf lambda_package
    mkdir lambda_package

    if [ "$full" = "true" ]; then
        pip install --platform manylinux2014_x86_64 \
            --implementation cp --python-version 3.13 \
            --only-binary=:all: --target lambda_package/ \
            requests pandas --upgrade --quiet 2>/dev/null || \
        pip install --target lambda_package/ requests pandas --upgrade --quiet

        cp lambda_function/reminder_function.py lambda_package/
        mkdir lambda_package/ingestion
        cp ingestion/fetch_hijri_calendar.py lambda_package/ingestion/
        cp ingestion/upload_to_aws.py lambda_package/ingestion/
        cp ingestion/parse_health_export.py lambda_package/ingestion/
        touch lambda_package/ingestion/__init__.py
    else
        cp "$source" lambda_package/lambda_function.py
    fi

    cd lambda_package
    zip -r -q "../fasting-tracker-${name}.zip" .
    cd ..
    rm -rf lambda_package

    aws s3 cp "fasting-tracker-${name}.zip" \
        "s3://fasting-tracker-rayyan/lambda/fasting-tracker-${name}.zip"

    aws lambda update-function-code \
        --function-name "fasting-tracker-${name}" \
        --s3-bucket fasting-tracker-rayyan \
        --s3-key "lambda/fasting-tracker-${name}.zip" \
        --no-cli-pager

    rm -f "fasting-tracker-${name}.zip"
    echo "Deployed fasting-tracker-${name}"
}

case "$TARGET" in
    all)
        build_and_deploy "get-health"       "lambda_function/get_health_data.py"
        build_and_deploy "get-fasting"      "lambda_function/get_fasting_data.py"
        build_and_deploy "manage-overrides" "lambda_function/manage_overrides.py"
        build_and_deploy "get-status"       "lambda_function/get_system_status.py"
        build_and_deploy "reminder"         "" "true"
        ;;
    get-health)       build_and_deploy "get-health"       "lambda_function/get_health_data.py" ;;
    get-fasting)      build_and_deploy "get-fasting"      "lambda_function/get_fasting_data.py" ;;
    manage-overrides) build_and_deploy "manage-overrides" "lambda_function/manage_overrides.py" ;;
    get-status)       build_and_deploy "get-status"       "lambda_function/get_system_status.py" ;;
    reminder)         build_and_deploy "reminder"         "" "true" ;;
    *)                echo "Unknown: $TARGET. Use: get-health | get-fasting | manage-overrides | get-status | reminder | all"; exit 1 ;;
esac

echo "Lambda deployment complete."