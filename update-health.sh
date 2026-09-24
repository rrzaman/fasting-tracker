#!/bin/bash
set -e

echo "  Fasting Tracker — Health Data Update"
echo ""
echo "Before continuing, ensure you have:"
echo "  1. Exported from iPhone → Health → Profile → Export All Health Data"
echo "  2. Unzipped the export"
echo "  3. Placed export.xml inside the data/ folder"
echo ""
read -p "Have you added export.xml to data/? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborting. Add export.xml to data/ and try again."
    exit 1
fi

mkdir -p data

if [ ! -f "data/export.xml" ]; then
    echo "Error: data/export.xml not found. Please add it and try again."
    exit 1
fi

# Prefer the project venv so the script works without activating it first.
if [ -x "venv/Scripts/python.exe" ]; then
    PY="venv/Scripts/python.exe"      # Windows
elif [ -x "venv/bin/python" ]; then
    PY="venv/bin/python"              # macOS / Linux
else
    PY="python"
fi

# All project resources live in ca-west-1. Without this, boto3 falls back to
# whatever ~/.aws/config says and the tables are not found.
export AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-ca-west-1}"
export AWS_REGION="$AWS_DEFAULT_REGION"

# boto3 cannot read the session credentials that `aws login` caches. If the AWS
# CLI is present and holds a live session, convert it into temporary env-var
# credentials. No-ops for static keys in ~/.aws/credentials, which boto3 reads
# on its own.
if command -v aws >/dev/null 2>&1; then
    if creds=$(aws configure export-credentials --format env 2>/dev/null); then
        eval "$creds"
    else
        echo "Note: no active AWS CLI session. Relying on the default credential chain."
        echo "      If the upload fails, run: aws configure   (or: aws login)"
    fi
fi

echo ""
"$PY" ingestion/parse_health_export.py

# upload_to_aws.py needs both CSVs. On a fresh clone data/ is empty, so build
# the fasting calendar if it isn't there yet.
if [ ! -f "data/fasting_calendar.csv" ]; then
    echo ""
    echo "data/fasting_calendar.csv missing — building it first..."
    "$PY" ingestion/fetch_hijri_calendar.py
fi

echo ""
"$PY" ingestion/upload_to_aws.py

echo ""
echo "Check the fasting dashboard to verify."