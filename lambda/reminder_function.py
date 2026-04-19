import json
import os
from datetime import date, timedelta

import boto3

PHONE_NUMBERS = [
    os.getenv("PHONE_NUMBER_RAYYAN"),
    os.getenv("PHONE_NUMBER_MA"),
    os.getenv("PHONE_NUMBER_SIMRAH")
]

FASTING_TABLE = "fasting-records"
DAYS_AHEAD = 7

def get_upcoming_fasts(days_ahead: int) -> list: 
    """
    Queries DynamoDB for fasting days in the next N days.
    
    Args:
        days_ahead (int): Number of days ahead to look.
    
    Returns:
        List of fasting record dictionaries.
    """

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(FASTING_TABLE) # type: ignore
    
    today = date.today()
    upcoming_fasts = []

    for i in range(1, days_ahead + 1):
        check_date = today + timedelta(days=i)
        date_str = str(check_date)

        response = table.get_item(Key={"date":date_str})
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