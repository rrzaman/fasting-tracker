import json
import os
from datetime import date, timedelta

import boto3


FASTING_TABLE = "fasting-records"
HEALTH_TABLE = "health-snapshots"
DAYS_AHEAD = 7

RAYYAN_NUMBER = os.getenv("PHONE_NUMBER_RAYYAN")
PHONE_NUMBERS = [
    RAYYAN_NUMBER,
    os.getenv("PHONE_NUMBER_MA"),
    os.getenv("PHONE_NUMBER_SIMRAH"),
]


def get_upcoming_fasts(days_ahead: int) -> list:
    """
    Queries DynamoDB for fasting days in the next N days.

    Args:
        days_ahead (int): Number of days ahead to look.

    Returns:
        List of fasting record dictionaries.
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(FASTING_TABLE)  # type: ignore

    today = date.today()
    upcoming_fasts = []

    for i in range(1, days_ahead + 1):
        check_date = today + timedelta(days=i)
        date_str = str(check_date)

        response = table.get_item(Key={"date": date_str})
        item = response.get("Item")

        if item and item.get("is_fasting") == True:
            upcoming_fasts.append(item)

    return upcoming_fasts


def build_message(item: dict) -> str | None:
    """
    Builds an SMS reminder message for a given fasting record.

    Args:
        item: DynamoDB fasting record dictionary.

    Returns:
        Formatted message string, or None if no message needed.
    """

    fast_type = item.get("fast_type")
    fast_date = item.get("date")
    hijri_month = int(item.get("hijri_month", 0))
    hijri_day = int(item.get("hijri_day", 0))

    if fast_type == "ramadan":
        return f"Ramadan Mubarak! The holy month of Ramadan begins tomorrow ({fast_date}). Don't forget to prepare for fasting and make the most of this blessed month!"

    if fast_type == "ayyam_al_bid":
        if hijri_day == 12:
            return f"Reminder: The White Days (Ayyam al-Bid) begin tomorrow ({fast_date}). The 13th, 14th and 15th of {hijri_month} are recommended fasting days."
        return f"Reminder: Tomorrow ({fast_date}) is a White Day (Ayyam al-Bid), day {hijri_day - 12} of 3."

    if fast_type == "dhul_hijjah_early":
        return f"Reminder: Dhul Hijjah begins tomorrow, ({fast_date}). The first 9 days are highly recommended for fasting."

    if fast_type == "arafah":
        return f"Reminder: The Day of Arafah is tomorrow, ({fast_date}). It is a highly recommended day for fasting, for those not performing Hajj."

    if fast_type == "ashura":
        return f"Reminder: Ashura fasting begins tomorrow, ({fast_date}). It is recommended to fast on the 9th and 10th or 10th and 11th of Muharram."

    if fast_type == "weekly_sunnah":
        return f"Reminder: Weekly Sunnah (Monday/Thursday) fasting is tomorrow, ({fast_date})."

    if fast_type == "prohibited":
        celebration = item.get("celebration_type")
        if celebration == "eid_al_fitr":
            return f"Eid Mubarak! Tomorrow ({fast_date}) is likely Eid al-Fitr, when fasting is prohibited. Please verify with your local mosque/masjid. May Allah accept your efforts during Ramadan."
        if celebration == "eid_al_adha":
            return f"Eid Mubarak! Tomorrow ({fast_date}) is likely Eid al-Adha. Please verify with your local mosque/masjid. Fasting is prohibited for today and the three following days (10th-13th Dhul Hijjah). May your sacrifice be accepted."
        return None

    return None


def send_sms(message: str, phone_numbers: list) -> None:
    """
    Sends an SMS message to a list of phone number via AWS SNS.

    Args:
        message: The text message to be sent.
        phone_numbers: List of phone numbers in E.164 format (+1xxxxxxxxxx)
    """

    sns = boto3.client("sns")

    for number in phone_numbers:
        if number:
            sns.publish(
                PhoneNumber=number,
                Message=message,
                MessageAttributes={
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    }
                },
            )
            print(f"SMS sent to {number}")


def get_latest_date(table_name: str) -> date | None:
    """
    Scans a DynamoDB table and returns the most recent date value.

    Args:
        table_name: Name of the target DynamoDB table.

    Returns:
        Most recent date as a date object, or None if table is empty.
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(table_name)  # type: ignore

    response = table.scan(
        ProjectionExpression="#d", ExpressionAttributeNames={"#d": "date"}
    )

    all_dates = response.get("Items", [])

    while "LastEvaluatedKey" in response:
        response = table.scan(
            ProjectionExpression="#d",
            ExpressionAttributeNames={"#d": "date"},
            ExclusiveStartKey=response["LastEvaluatedKey"],
        )
        all_dates.extend(response.get("Items", []))

    if not all_dates:
        return None

    # .fromisoformat converts string to date object
    return date.fromisoformat(max(item["date"] for item in all_dates))


def check_health_data_lag(rayyan_number: str) -> None:
    """
    Checks if health data has been updated recently.
    Send a reminder to Rayyan only if data has not been updated in more than 14 days.
    Note: This may later be repurposed for the individual dashboard user.

    Args:
        rayyan_number: Phone number to send reminder to.
    """

    latest = get_latest_date(HEALTH_TABLE)
    if not latest:
        return

    days_since = (date.today() - latest).days

    if days_since > 14:
        message = (
            f"Reminder: Your health data is {days_since} days old. "
            f"Consider exporting and uploading a fresh Apple Health export."
        )
        send_sms(message, [rayyan_number])
        print(f"Health data upload reminder sent. Latest data: {latest}")


def check_calendar_horizon() -> None:
    """
    Checks how far ahead the fasting calendar extends in DynamoDB.
    If the horizon is less than 60 days from today, extends it automatically.
    """

    latest = get_latest_date(FASTING_TABLE)
    if not latest:
        return

    days_ahead = (latest - date.today()).days

    if days_ahead < 60:
        # Extend to 90 days from today rather than latest_date.
        # This is done to prevent having to run the extension daily.
        # End date is selected as today to ensure horizon
        # is measured from current date.
        new_end = date.today() + timedelta(days=90)
        new_start = latest + timedelta(days=1)
        print(f"Extending calendar from {new_start} to {new_end}...")

        from ingestion.fetch_hijri_calendar import build_fasting_calendar
        from ingestion.upload_to_aws import upload_df_to_dynamodb

        df = build_fasting_calendar(new_start, new_end)
        upload_df_to_dynamodb(df, FASTING_TABLE)
        print(f"Calendar extended to {new_end}")


def handler(event, context) -> None:
    """
    AWS Lambda entry point. Runs weekly via EventBridge.
    Sends fasting reminders, checks health data lag, and extends fasting calendar horizon if necessary.
    """

    print("Lambda handler started.")

    upcoming = get_upcoming_fasts(DAYS_AHEAD)
    print(f"Found {len(upcoming)} upcoming fasting days.")

    for item in upcoming:
        message = build_message(item)
        if message:
            send_sms(message, PHONE_NUMBERS)

    check_health_data_lag(RAYYAN_NUMBER)  # type: ignore
    check_calendar_horizon()

    print("Lambda handler complete.")
