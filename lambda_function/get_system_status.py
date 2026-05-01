import json
import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import boto3

FASTING_TABLE = os.environ.get("FASTING_TABLE",   "fasting-records")
HEALTH_TABLE = os.environ.get("HEALTH_TABLE",    "health-snapshots")
REMINDER_LOG_TABLE = os.environ.get("REMINDER_LOG_TABLE", "reminder-log")
REMINDER_LAMBDA = os.environ.get("REMINDER_LAMBDA", "fasting-tracker-reminder")
LOG_GROUP = f"/aws/lambda/{REMINDER_LAMBDA}"


def cors_headers():
    return {
        "Content-Type":                "application/json",
        "Access-Control-Allow-Origin": "*",
    }


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers":    cors_headers(),
        "body":       json.dumps(body),
    }


def get_latest_date(table_name: str) -> str | None:
    """Returns most recent date string from a DynamoDB table."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)  # type: ignore

    response = table.scan(ProjectionExpression="#d",
                          ExpressionAttributeNames={"#d": "date"})
    all_dates = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ProjectionExpression="#d",
            ExpressionAttributeNames={"#d": "date"},
            ExclusiveStartKey=response["LastEvaluatedKey"]
        )
        all_dates.extend(response.get("Items", []))

    if not all_dates:
        return None
    return max(item["date"] for item in all_dates)


def get_last_reminder_run() -> dict:
    """Reads CloudWatch logs to find the last Lambda execution."""
    logs = boto3.client("logs")

    try:
        streams = logs.describe_log_streams(
            logGroupName=LOG_GROUP,
            orderBy="LastEventTime",
            descending=True,
            limit=1
        )

        if not streams.get("logStreams"):
            return {"status": "No logs found", "timestamp": None}

        stream = streams["logStreams"][0]
        last_event_ms = stream.get("lastEventTimestamp")

        if not last_event_ms:
            return {"status": "No events found", "timestamp": None}

        last_event_dt = datetime.fromtimestamp(
            last_event_ms / 1000,
            tz=ZoneInfo("America/Edmonton")
        )

        # Get recent events to check for errors
        events = logs.get_log_events(
            logGroupName=LOG_GROUP,
            logStreamName=stream["logStreamName"],
            limit=50
        )

        messages = [e["message"] for e in events.get("events", [])]
        has_error = any("ERROR" in m or "Error" in m or "Traceback" in m
                        for m in messages)
        completed = any("Lambda handler complete" in m for m in messages)

        return {
            "timestamp": last_event_dt.isoformat(),
            "status":    "Error detected" if has_error else
            "Completed successfully" if completed else "Running",
            "has_error": has_error,
        }

    except Exception as e:
        return {"status": f"Could not read logs: {str(e)}", "timestamp": None}


def get_last_sms_sent() -> str | None:
    """Returns the most recent date an SMS reminder was sent."""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(REMINDER_LOG_TABLE)  # type: ignore

    try:
        response = table.scan(
            ProjectionExpression="#d, sent_at",
            ExpressionAttributeNames={"#d": "date"}
        )
        items = response.get("Items", [])
        if not items:
            return None
        latest = max(items, key=lambda x: x.get("sent_at", ""))
        return latest.get("date")
    except Exception:
        return None


def get_calendar_horizon() -> int | None:
    """Returns how many days ahead the fasting calendar extends."""
    from datetime import date
    latest = get_latest_date(FASTING_TABLE)
    if not latest:
        return None
    today = datetime.now(ZoneInfo("America/Edmonton")).date()
    return (date.fromisoformat(latest) - today).days


def get_health_data_age() -> int | None:
    """Returns how many days since health data was last updated."""
    from datetime import date
    latest = get_latest_date(HEALTH_TABLE)
    if not latest:
        return None
    today = datetime.now(ZoneInfo("America/Edmonton")).date()
    return (today - date.fromisoformat(latest)).days


def handler(event, context):
    """Returns system status for dashboard display."""
    reminder_run = get_last_reminder_run()
    last_sms = get_last_sms_sent()
    calendar_horizon = get_calendar_horizon()
    health_age = get_health_data_age()

    return respond(200, {
        "last_reminder_run": reminder_run,
        "last_sms_sent":     last_sms,
        "calendar_horizon":  calendar_horizon,
        "health_data_age":   health_age,
    })
