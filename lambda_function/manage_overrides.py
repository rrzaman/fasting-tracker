import json
import os
from datetime import datetime, timezone
from decimal import Decimal

import boto3

OVERRIDES_TABLE = os.environ.get("OVERRIDES_TABLE", "fasting-overrides")
FASTING_TABLE = os.environ.get("FASTING_TABLE",   "fasting-records")


def decimal_to_float(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def cors_headers():
    return {
        "Content-Type":                "application/json",
        "Access-Control-Allow-Origin": "*",
    }


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers":    cors_headers(),
        "body":       json.dumps(body, default=decimal_to_float),
    }


def handler(event, context):
    """
    Manages fasting overrides — supports GET, POST, PUT, DELETE.

    GET    /overrides              — fetch all overrides
    POST   /overrides              — create new override
    PUT    /overrides              — update existing override
    DELETE /overrides?date=YYYY-MM-DD — delete override by date
    """

    method = (
        event.get("httpMethod") or
        event.get("requestContext", {}).get("http", {}).get("method", "GET")
    ).upper()
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(OVERRIDES_TABLE)  # type: ignore

    if method == "GET":
        response = table.scan()
        items = response.get("Items", [])
        while "LastEvaluatedKey" in response:
            response = table.scan(
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            items.extend(response.get("Items", []))
        items.sort(key=lambda x: x.get("date", ""))
        return respond(200, {"count": len(items), "data": items})

    elif method == "POST":
        body = json.loads(event.get("body") or "{}")
        date_str = body.get("date")
        override_type = body.get("override_type")

        if not date_str or override_type not in ("skipped", "extra"):
            return respond(400, {"error": "date and override_type (skipped|extra) required"})

        # Look up what was originally scheduled for this date
        fasting_table = dynamodb.Table(FASTING_TABLE)  # type: ignore
        existing = fasting_table.get_item(Key={"date": date_str}).get("Item")
        original_type = existing.get("fast_type") if existing else None

        item = {
            "date":               date_str,
            "override_type":      override_type,
            "original_fast_type": original_type,
            "recorded_at":        datetime.now(timezone.utc).isoformat(),
        }
        table.put_item(Item=item)
        return respond(201, {"message": "Override recorded", "item": item})

    elif method == "PUT":
        body = json.loads(event.get("body") or "{}")
        date_str = body.get("date")
        override_type = body.get("override_type")

        if not date_str or override_type not in ("skipped", "extra"):
            return respond(400, {"error": "date and override_type (skipped|extra) required"})

        table.update_item(
            Key={"date": date_str},
            UpdateExpression="SET override_type = :t, recorded_at = :r",
            ExpressionAttributeValues={
                ":t": override_type,
                ":r": datetime.now(timezone.utc).isoformat(),
            }
        )
        return respond(200, {"message": "Override updated"})

    elif method == "DELETE":
        params = event.get("queryStringParameters") or {}
        date_str = params.get("date")

        if not date_str:
            return respond(400, {"error": "date query parameter required"})

        table.delete_item(Key={"date": date_str})
        return respond(200, {"message": f"Override for {date_str} deleted"})

    else:
        return respond(405, {"error": f"Method {method} not allowed"})
