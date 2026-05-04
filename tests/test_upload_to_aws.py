"""Tests for ingestion/upload_to_aws.py.

Shared fixtures (aws_env, dynamodb, s3_client, fasting_table, health_table)
live in tests/conftest.py.
"""

from decimal import Decimal

import pandas as pd

S3_BUCKET = "fasting-tracker-rayyan"
FASTING_TABLE = "fasting-records"
HEALTH_TABLE = "health-snapshots"


class TestUploadCsvToS3:
    """upload_csv_to_s3 — uploads a local CSV file to S3."""

    def test_uploads_file_successfully(self, tmp_path, monkeypatch, s3_client):
        # Override the module-level s3 client with the moto mock
        from ingestion import upload_to_aws
        monkeypatch.setattr(upload_to_aws, "s3", s3_client)

        csv_path = tmp_path / "test.csv"
        csv_path.write_text("date,metric,value\n2026-04-01,steps,1000\n")

        upload_to_aws.upload_csv_to_s3(str(csv_path), "health/test.csv")

        obj = s3_client.get_object(Bucket=S3_BUCKET, Key="health/test.csv")
        body = obj["Body"].read().decode("utf-8")
        assert "2026-04-01,steps,1000" in body

    def test_uploads_to_correct_bucket(self, tmp_path, monkeypatch, s3_client):
        from ingestion import upload_to_aws
        monkeypatch.setattr(upload_to_aws, "s3", s3_client)

        csv_path = tmp_path / "fasting.csv"
        csv_path.write_text("date,fast_type\n2026-04-01,ramadan\n")

        upload_to_aws.upload_csv_to_s3(str(csv_path), "fasting_calendar.csv")

        buckets = s3_client.list_buckets()["Buckets"]
        assert any(b["Name"] == S3_BUCKET for b in buckets)
        keys = s3_client.list_objects_v2(Bucket=S3_BUCKET)["Contents"]
        assert any(k["Key"] == "fasting_calendar.csv" for k in keys)


class TestUploadDfToDynamoDB:
    """upload_df_to_dynamodb — uploads a DataFrame to DynamoDB, one row per item."""

    def test_uploads_health_data_rows(self, monkeypatch, dynamodb, health_table):
        from ingestion import upload_to_aws
        monkeypatch.setattr(upload_to_aws, "dynamodb", dynamodb)

        df = pd.DataFrame({
            "date": ["2026-04-01", "2026-04-01", "2026-04-02"],
            "metric": ["steps", "resting_heart_rate", "steps"],
            "value": [10000, 62.0, 12000],
        })

        upload_to_aws.upload_df_to_dynamodb(df, HEALTH_TABLE)

        response = health_table.scan()
        items = response["Items"]
        assert len(items) == 3
        dates = {item["date"] for item in items}
        assert dates == {"2026-04-01", "2026-04-02"}

    def test_uploads_fasting_data_rows(self, monkeypatch, dynamodb, fasting_table):
        from ingestion import upload_to_aws
        monkeypatch.setattr(upload_to_aws, "dynamodb", dynamodb)

        df = pd.DataFrame({
            "date": ["2026-04-01", "2026-04-02"],
            "hijri_month": [9, 9],
            "hijri_day": [1, 2],
            "fast_type": ["ramadan", "ramadan"],
            "is_fasting": [True, True],
            "celebration_type": [None, None],
        })

        upload_to_aws.upload_df_to_dynamodb(df, FASTING_TABLE)

        response = fasting_table.scan()
        items = response["Items"]
        assert len(items) == 2

    def test_decimal_values_preserved(self, monkeypatch, dynamodb, health_table):
        from ingestion import upload_to_aws
        monkeypatch.setattr(upload_to_aws, "dynamodb", dynamodb)

        df = pd.DataFrame({
            "date": ["2026-04-01"],
            "metric": ["resting_heart_rate"],
            "value": [62.5],
        })

        upload_to_aws.upload_df_to_dynamodb(df, HEALTH_TABLE)

        item = health_table.get_item(
            Key={"date": "2026-04-01", "metric": "resting_heart_rate"})["Item"]
        # DynamoDB stores floats as Decimal
        assert isinstance(item["value"], Decimal)
        assert float(item["value"]) == 62.5

    def test_empty_dataframe_no_error(self, monkeypatch, dynamodb, fasting_table):
        from ingestion import upload_to_aws
        monkeypatch.setattr(upload_to_aws, "dynamodb", dynamodb)

        df = pd.DataFrame(columns=["date", "fast_type", "is_fasting"])

        upload_to_aws.upload_df_to_dynamodb(df, FASTING_TABLE)

        response = fasting_table.scan()
        assert response["Count"] == 0

    def test_null_values_excluded(self, monkeypatch, dynamodb, fasting_table):
        from ingestion import upload_to_aws
        monkeypatch.setattr(upload_to_aws, "dynamodb", dynamodb)

        df = pd.DataFrame({
            "date": ["2026-04-01"],
            "fast_type": ["ramadan"],
            "is_fasting": [True],
            "celebration_type": [None],
        })

        upload_to_aws.upload_df_to_dynamodb(df, FASTING_TABLE)

        response = fasting_table.scan()
        items = response["Items"]
        assert len(items) == 1
        # None values appear as DynamoDB NULL type in the item
        assert "celebration_type" in items[0]
        assert items[0]["celebration_type"] is None
