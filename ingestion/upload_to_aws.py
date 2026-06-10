from __future__ import annotations

import json
import os
from decimal import Decimal

import boto3
import pandas as pd

# Constant for AWS resources
S3_BUCKET = "fasting-tracker-rayyan"
FASTING_TABLE = "fasting-records"
HEALTH_TABLE = "health-snapshots"
OVERRIDES_TABLE = "fasting-overrides"

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")


def upload_csv_to_s3(filepath: str, s3_key: str) -> None:
    """
    Uploads a local CSV file to S3.

    Args:
        filepath: Local path to the CSV file.
        s3_key: The name the file will have inside the S3 bucket.
    """

    s3.upload_file(filepath, S3_BUCKET, s3_key)
    print(f"Uploaded {filepath} to s3://{S3_BUCKET}/{s3_key}")


def upload_df_to_dynamodb(df: pd.DataFrame, table_name: str) -> None:
    """
    Uploads a DataFrame to DynamoDB, one row per item.

    Args:
        df: The DataFrame to upload.
        table_name: The name of the target DynamoDB table.
    """

    table = dynamodb.Table(table_name)  # type: ignore

    with table.batch_writer() as batch:
        for _, row in df.iterrows():
            item = json.loads(row.to_json(), parse_float=Decimal)
            batch.put_item(Item=item)

    print(f"Uploaded {len(df)} records to DynamoDB table '{table_name}'")


if __name__ == "__main__":  # pragma: no cover
    health_csv = os.path.join("data", "health_summary.csv")
    fasting_csv = os.path.join("data", "fasting_calendar.csv")

    print("Uploading CSVs to S3...")
    upload_csv_to_s3(health_csv, "health_summary.csv")
    upload_csv_to_s3(fasting_csv, "fasting_calendar.csv")

    print("\nUploading health data to DynamoDB...")
    health_df = pd.read_csv(health_csv)
    upload_df_to_dynamodb(health_df, HEALTH_TABLE)

    print("\nUploading fasting calendar to DynamoDB...")
    fasting_df = pd.read_csv(fasting_csv)
    upload_df_to_dynamodb(fasting_df, FASTING_TABLE)

    print("\nAll done!")
