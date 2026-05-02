import json
import os
from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo

import boto3


FASTING_TABLE = os.environ.get("FASTING_TABLE",   "fasting-records")
HEALTH_TABLE = os.environ.get("HEALTH_TABLE",     "health-snapshots")
OVERRIDES_TABLE = os.environ.get("OVERRIDES_TABLE",  "fasting-overrides")
REMINDER_LOG_TABLE = os.environ.get("REMINDER_LOG_TABLE", "reminder-log")
DAYS_AHEAD = 1

RECIPIENTS_TABLE = os.environ.get(
    "RECIPIENTS_TABLE", "notification-recipients")

# Messages in all supported languages.
MESSAGES = {
    "ramadan": {
        "en": lambda d: f"Ramadan Mubarak! The holy month of Ramadan begins tomorrow ({d}). Please verify with your local mosque. Make the most of this blessed month!",
        "bn": lambda d: f"রমজান মোবারক! পবিত্র রমজান মাস আগামীকাল ({d}) থেকে শুরু হতে পারে। আপনার স্থানীয় মসজিদে খোঁজ নিন। আল্লাহ আমাদের এই মাসের রহমত দান করুন।",
    },
    "ayyam_al_bid": {
        "en": lambda d, m: f"Reminder: The White Days (Ayyam al-Bid) begin tomorrow ({d}). The 13th, 14th and 15th of {m} are recommended fasting days.",
        "bn": lambda d, m: f"রিমাইন্ডার: আইয়ামুল বিদ-এর রোজা আগামীকাল ({d}) শুরু হচ্ছে। {m} মাসের ১৩, ১৪ ও ১৫ তারিখ রোজা রাখা মুস্তাহাব।",
    },
    "dhul_hijjah_early": {
        "en": lambda d: f"Reminder: Dhul Hijjah begins tomorrow ({d}). The first 9 days are highly recommended for fasting.",
        "bn": lambda d: f"রিমাইন্ডার: আগামীকাল ({d}) থেকে জিলহজ মাস শুরু হচ্ছে। প্রথম ৯ দিন রোজা রাখা অত্যন্ত ফজিলতপূর্ণ।",
    },
    "arafah": {
        "en": lambda d: f"Reminder: The Day of Arafah is tomorrow ({d}). A highly recommended fast for those not performing Hajj.",
        "bn": lambda d: f"রিমাইন্ডার: আগামীকাল ({d}) আরাফার দিন। যারা হজে যাননি, তাদের জন্য এই দিন রোজা রাখা অত্যন্ত সওয়াবের কাজ।",
    },
    "ashura": {
        "en": lambda d: f"Reminder: Ashura fasting begins tomorrow ({d}). Fast the 9th and 10th or 10th and 11th of Muharram.",
        "bn": lambda d: f"রিমাইন্ডার: আশুরার রোজা আগামীকাল ({d}) থেকে শুরু হচ্ছে। মুহাররমের ৯ ও ১০ অথবা ১০ ও ১১ তারিখ রোজা রাখুন।",
    },
    "weekly_sunnah": {
        "en": lambda d: f"Reminder: Tomorrow ({d}) is a Sunnah fast day (Monday/Thursday).",
        "bn": lambda d: f"রিমাইন্ডার: আগামীকাল ({d}) সুন্নত রোজার দিন (সোমবার/বৃহস্পতিবার)।",
    },
    "eid_al_fitr": {
        "en": lambda d: f"Eid Mubarak! Tomorrow ({d}) is likely Eid al-Fitr. Please verify with your local mosque. May Allah accept your Ramadan efforts.",
        "bn": lambda d: f"ঈদ মোবারক! আগামীকাল ({d}) সম্ভবত ঈদুল ফিতর। স্থানীয় মসজিদে খোঁজ নিন। আল্লাহ আপনার রমজানের সকল ইবাদত কবুল করুন।",
    },
    "eid_al_adha": {
        "en": lambda d: f"Eid Mubarak! Tomorrow ({d}) is likely Eid al-Adha. Fasting is prohibited for the next four days. May your sacrifice be accepted.",
        "bn": lambda d: f"ঈদ মোবারক! আগামীকাল ({d}) সম্ভবত ঈদুল আযহা। আগামী চার দিন রোজা রাখা নিষিদ্ধ। আল্লাহ আপনার কোরবানি কবুল করুন।",
    },
}

# Mapping of Hijri month numbers to names for easy reference
HIJRI_MONTHS = {
    1:  "Muharram",
    2:  "Safar",
    3:  "Rabi al-Awwal",
    4:  "Rabi al-Thani",
    5:  "Jumada al-Awwal",
    6:  "Jumada al-Thani",
    7:  "Rajab",
    8:  "Shaban",
    9:  "Ramadan",
    10: "Shawwal",
    11: "Dhul Qadah",
    12: "Dhul Hijjah",
}


def get_recipients() -> list[dict]:
    """
    Fetches SMS recipients from DynamoDB.
    Returns list of dicts with phone, name, lang fields.
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(RECIPIENTS_TABLE)  # type: ignore
    try:
        response = table.scan()
        return response.get("Items", [])
    except Exception as e:
        print(f"Failed to fetch recipients: {e}")
        return []


def get_local_today() -> date:
    """Returns today's date in Mountain Time rather than UTC."""
    return datetime.now(ZoneInfo("America/Edmonton")).date()


def get_upcoming_fasts(days_ahead: int) -> list:
    """
    Queries DynamoDB for fasting days in the next N days, not including current day.

    Args:
        days_ahead (int): Number of days ahead to look.

    Returns:
        List of fasting record dictionaries.
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(FASTING_TABLE)  # type: ignore

    today = get_local_today()
    upcoming_fasts = []

    for i in range(1, days_ahead + 1):
        check_date = today + timedelta(days=i)
        date_str = str(check_date)

        response = table.get_item(Key={"date": date_str})
        item = response.get("Item")

        if item and item.get("is_fasting") == True:
            upcoming_fasts.append(item)

    return upcoming_fasts


def format_date(date_str: str) -> str:
    """Converts YYYY-MM-DD to a human-readable format e.g. April 27th."""

    if not date_str:
        return "unknown date"

    d = date.fromisoformat(date_str)
    day = d.day
    suffix = "th" if 11 <= day <= 13 else {
        1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return d.strftime(f"%B {day}{suffix}")


def already_sent_today(fast_type: str) -> bool:
    """
    Checks if a reminder for this fast type was already sent today.
    Prevents duplicate SMS if Lambda fires multiple times.

    Args:
        fast_type: The type of fast being reminded about.

    Returns:
        True if reminder was already sent today, False otherwise.
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(REMINDER_LOG_TABLE)  # type: ignore

    today = str(get_local_today())

    try:
        response = table.get_item(
            Key={"date": today, "fast_type": fast_type}
        )
        return "Item" in response
    except Exception as e:
        print(f"Warning: Could not check reminder log: {e}")
        return False


def log_reminder_sent(fast_type: str) -> None:
    """
    Records that a reminder was sent today for this fast type.
    Automatically expires after 30 days via DynamoDB TTL.

    Args:
        fast_type: The type of fast that was reminded about.
    """
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(REMINDER_LOG_TABLE)  # type: ignore

    today = str(get_local_today())
    expires_at = int((get_local_today() + timedelta(days=30)).strftime("%s"))

    try:
        table.put_item(Item={
            "date":       today,
            "fast_type":  fast_type,
            "sent_at":    datetime.now(ZoneInfo("America/Edmonton")).isoformat(),
            "expires_at": expires_at,
        })
    except Exception as e:
        print(f"Warning: Could not log reminder: {e}")


def build_message(item: dict, lang: str = "en") -> str | None:
    """
    Builds an SMS reminder message for a given fasting record.

    Args:
        item: DynamoDB fasting record dictionary.
        lang: Language of the message.

    Returns:
        Formatted message string, or None if no message needed.
    """

    fast_type = item.get("fast_type")
    fast_date = format_date(item.get("date", ""))
    hijri_month = int(item.get("hijri_month", 0))
    hijri_day = int(item.get("hijri_day", 0))

    # Prohibited fasts messaged first, due to it not being listed as "prohibited" in the dictionary.
    if fast_type == "prohibited":
        celebration = item.get("celebration_type")
        if celebration in ("eid_al_fitr", "eid_al_adha"):
            celebration_msgs = MESSAGES.get(celebration, {})
            fn = celebration_msgs.get(lang) or celebration_msgs.get("en")
            return fn(fast_date) if fn else None
        return None

    msgs = MESSAGES.get(fast_type, {})  # type: ignore
    if not msgs:
        return None

    if fast_type == "ramadan" and hijri_day == 1:
        return msgs.get(lang, msgs["en"])(fast_date)

    if fast_type == "ayyam_al_bid":
        if hijri_day == 13:
            month_name = HIJRI_MONTHS.get(hijri_month, "this month")
            return msgs.get(lang, msgs["en"])(fast_date, month_name)
        if hijri_month == 12 and hijri_day == 14:
            if lang == "bn":
                return (f"রিমাইন্ডার: আইয়ামুল বিদ আগামীকাল ({fast_date}) শুরু হচ্ছে। "
                        f"জিলহজ মাসে ১৩ তারিখ আইয়ামুত তাশরীকের কারণে নিষিদ্ধ, তাই ১৪, ১৫ ও ১৬ তারিখ রোজা রাখা হয়।")
            return (f"Reminder: The White Days (Ayyam al-Bid) begin tomorrow ({fast_date}). "
                    f"In Dhul Hijjah, fasting is observed on the 14th, 15th and 16th as the 13th is Ayyam al-Tashreeq.")
        return None

    if fast_type in ("dhul_hijjah_early", "arafah", "ashura", "weekly_sunnah"):
        if fast_type == "dhul_hijjah_early" and hijri_day != 1:
            return None
        return msgs.get(lang, msgs["en"])(fast_date)

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

    days_since = (get_local_today() - latest).days

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

    days_ahead = (latest - get_local_today()).days

    if days_ahead < 60:
        # Extend to 90 days from today rather than latest_date.
        # This is done to prevent having to run the extension daily.
        # End date is selected as today to ensure horizon
        # is measured from current date.
        new_end = get_local_today() + timedelta(days=90)
        new_start = latest + timedelta(days=1)
        print(f"Extending calendar from {new_start} to {new_end}...")

        from ingestion.fetch_hijri_calendar import build_fasting_calendar
        from ingestion.upload_to_aws import upload_df_to_dynamodb

        df = build_fasting_calendar(new_start, new_end)
        upload_df_to_dynamodb(df, FASTING_TABLE)
        print(f"Calendar extended to {new_end}")


def handler(event, context) -> None:
    """
    AWS Lambda entry point. Runs daily via EventBridge.
    Sends fasting reminders, checks health data lag, and extends fasting calendar horizon if necessary.
    """

    recipients = get_recipients()
    # Override for testing messaging
    if event.get("test_message"):
        test_item = event["test_message"]
        for recipient in recipients:
            if not recipient["phone"]:
                continue
            message = build_message(test_item, lang=recipient["lang"])
            if message:
                test_message = f"[TEST] {message}"
                send_sms(test_message, [recipient["phone"]])
        return

    print("Lambda handler started.")

    upcoming = get_upcoming_fasts(DAYS_AHEAD)
    print(f"Found {len(upcoming)} upcoming fasting days.")
    rayyan = next((r for r in recipients if r.get("name") == "Rayyan"), None)
    rayyan_number = rayyan.get("phone") if rayyan else None

    for item in upcoming:
        fast_type = item.get("fast_type", "unknown")

        if already_sent_today(fast_type):
            print(f"Reminder already sent today for {fast_type} — skipping.")
            continue

        messages_sent = False
        for recipient in recipients:
            if not recipient["phone"]:
                continue
            message = build_message(item, lang=recipient["lang"])
            if message:
                send_sms(message, [recipient["phone"]])
                messages_sent = True

        if messages_sent:
            log_reminder_sent(fast_type)
            print(f"Reminder logged for {fast_type}")

    if rayyan_number:
        check_health_data_lag(rayyan_number)

    check_calendar_horizon()

    print("Lambda handler complete.")
