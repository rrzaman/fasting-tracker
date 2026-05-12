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

if [ ! -f "data/export.xml" ]; then
    echo "Error: data/export.xml not found. Please add it and try again."
    exit 1
fi

echo ""
python ingestion/parse_health_export.py

echo ""
python ingestion/upload_to_aws.py

echo ""
echo "Check the fasting dashboard to verify."