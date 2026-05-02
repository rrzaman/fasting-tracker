from __future__ import annotations

import json
import os
from datetime import date, timedelta
from decimal import Decimal

import boto3

HEALTH_TABLE = os.environ.get("HEALTH_TABLE", "health-snapshots")


def decimal_to_float(obj: object) -> float:
    """Convert DynamoDB Decimal types to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def get_date_range(days: int) -> tuple[str, str]:
    """Returns start and end date strings for a given number of days back."""
    end = date.today()
    start = end - timedelta(days=days)
    return str(start), str(end)


def handler(event: dict, context: object) -> dict:
    """
    Fetches health snapshots from DynamoDB for a given date range.

    Query parameters:
        days (int): Number of days back to fetch. Default 90.
        metric (str): Optional — filter to a specific metric.
    """

    # Parse query parameters
    params = event.get("queryStringParameters") or {}
    days = int(params.get("days", 90))
    metric = params.get("metric")

    start_date, end_date = get_date_range(days)

    # Query DynamoDB
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(HEALTH_TABLE)  # type: ignore

    # Scan with date filter
    response = table.scan(
        FilterExpression="#d BETWEEN :start AND :end",
        ExpressionAttributeNames={"#d": "date"},
        ExpressionAttributeValues={
            ":start": start_date,
            ":end":   end_date,
        }
    )

    items = response.get("Items", [])

    # Handle pagination
    while "LastEvaluatedKey" in response:
        response = table.scan(
            FilterExpression="#d BETWEEN :start AND :end",
            ExpressionAttributeNames={"#d": "date"},
            ExpressionAttributeValues={
                ":start": start_date,
                ":end":   end_date,
            },
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        items.extend(response.get("Items", []))

    # Optional metric filter
    if metric:
        items = [item for item in items if item.get("metric") == metric]

    # Sort by date then metric
    items.sort(key=lambda x: (x.get("date", ""), x.get("metric", "")))

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type":                "application/json",
            "Access-Control-Allow-Origin": "*",  # CORS — required for React
        },
        "body": json.dumps({
            "count": len(items),
            "start_date": start_date,
            "end_date":   end_date,
            "data": items,
        }, default=decimal_to_float)
    }
