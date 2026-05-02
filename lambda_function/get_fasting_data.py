from __future__ import annotations

import json
import os
from datetime import date, timedelta
from decimal import Decimal

import boto3

FASTING_TABLE = os.environ.get("FASTING_TABLE",   "fasting-records")
OVERRIDES_TABLE = os.environ.get("OVERRIDES_TABLE",  "fasting-overrides")


def decimal_to_float(obj: object) -> float:
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def handler(event: dict, context: object) -> dict:
    """
    Fetches fasting calendar records for a given date range,
    merged with any user overrides.

    Query parameters:
        days_back (int): Number of days backwards to fetch. Default 365.
        days_forward (int): Number of days forward to fetch. Default 90.
    """

    params = event.get("queryStringParameters") or {}
    days_back = int(params.get("days_back", 365))
    days_forward = int(params.get("days_forward", 90))

    today = date.today()
    start_date = str(today - timedelta(days=days_back))
    end_date = str(today + timedelta(days=days_forward))

    dynamodb = boto3.resource("dynamodb")

    # Get fasting records.
    fasting_table = dynamodb.Table(FASTING_TABLE)  # type: ignore

    response = fasting_table.scan(
        FilterExpression="#d BETWEEN :start AND :end",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={":start": start_date, ":end": end_date}
    )
    items = response.get("Items", [])
    while "LastEvaluatedKey" in response:
        response = fasting_table.scan(
            FilterExpression="#d BETWEEN :start AND :end",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={":start": start_date, ":end": end_date},
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    # Fetch fasting overrides that exist.
    overrides_table = dynamodb.Table(OVERRIDES_TABLE)  # type: ignore

    ov_response = overrides_table.scan(
        FilterExpression="#d BETWEEN :start AND :end",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={":start": start_date, ":end": end_date}
    )
    overrides = {item["date"]: item for item in ov_response.get("Items", [])}
    while "LastEvaluatedKey" in ov_response:
        ov_response = overrides_table.scan(
            FilterExpression="#d BETWEEN :start AND :end",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={":start": start_date, ":end": end_date},
            ExclusiveStartKey=ov_response["LastEvaluatedKey"]
        )
        overrides.update(
            {item["date"]: item for item in ov_response.get("Items", [])})

    # Merge overrides into fasting records
    fasting_by_date = {item["date"]: item for item in items}

    for override_date, override in overrides.items():
        if override_date in fasting_by_date:
            # Existing record — apply override
            if override["override_type"] == "skipped":
                fasting_by_date[override_date]["is_fasting"] = False
                fasting_by_date[override_date]["fast_type"] = None
                fasting_by_date[override_date]["override"] = "skipped"
            elif override["override_type"] == "extra":
                fasting_by_date[override_date]["is_fasting"] = True
                fasting_by_date[override_date]["override"] = "extra"
        else:
            # New record — extra fast on non-scheduled day
            fasting_by_date[override_date] = {
                "date":       override_date,
                "is_fasting": True,
                "fast_type":  "extra",
                "override":   "extra",
            }

    result = sorted(fasting_by_date.values(), key=lambda x: x["date"])

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps({
            "count":      len(result),
            "start_date": start_date,
            "end_date":   end_date,
            "data":       result,
        }, default=decimal_to_float)
    }
