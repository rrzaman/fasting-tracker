import os
from datetime import date

import pandas as pd
import requests

# API endpoint for fetching Hijri calendar data
API_BASE_URL = "https://api.aladhan.com/v1/gToHCalendar"

# Special days in the Hijri calendar for fasting
RAMADAN = {"month": 9}
DHUL_HIJJAH_EARLY = {
    "month": 12,
    "days": list(range(1, 9))
}  # First to eighth of Dhul Hijjah
ARAFAH = {"month": 12, "day": 9}  # Day of Arafah placed separately.
ASHURA_PREFERENCE = "early"  # Indicates personal fasting on 9+10
ASHURA = {
    "month": 1,
    "days": [9, 10] if ASHURA_PREFERENCE == "early" else [10, 11]
}
AYYAM_AL_BID = [13, 14, 15]  # Applies to every Hijri month
EID_AL_FITR = {"month": 10, "day": 1}
EID_AL_ADHA = {"month": 12, "day": 10}
AYYAM_AL_TASHREEQ = {"month": 12, "days": [11, 12, 13]}


def fetch_hijri_month(month: date, year: date) -> list:
    """Fetches Hijri calendar data for a specific Gregorian month and year using the Aladhan API."""

    url = f"{API_BASE_URL}/{month}/{year}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()["data"]


def classify_day(gregorian_date: str, hijri_month: int, hijri_day: int, weekday: str) -> tuple:
    """
    Classifies a single day and returns its fasting status and type.

    Args:
        gregorian_date: Date string in YYYY-MM-DD format.
        hijri_month: Integer representing the Hijri month (1-12).
        hijri_day: Integer representing the day of the Hijri month.
        weekday: Weekday string e.g. "Monday".

    Returns:
        Tuple:
            - is_fasting_day (bool): Whether the day is a fasting day.
            - fast_type (str|None): The type of fast or if prohibited.
            - celebration_type (str|None): Celebration identifier if applicable, e.g. "eid_al_fitr".
    """

    # Prohibited fasting days, early exit.
    if hijri_month == EID_AL_FITR["month"] and hijri_day == EID_AL_FITR["day"]:
        return False, "prohibited", "eid_al_fitr"
    if hijri_month == EID_AL_ADHA["month"] and hijri_day == EID_AL_ADHA["day"]:
        return False, "prohibited", "eid_al_adha"
    if hijri_month == AYYAM_AL_TASHREEQ["month"] and hijri_day in AYYAM_AL_TASHREEQ["days"]:
        return False, "prohibited", "ayyam_al_tashreeq"

    # Fasting days
    # Ramadan
    if hijri_month == RAMADAN["month"]:
        return True, "ramadan", None

    # First eight days of Dhul Hijjah
    if hijri_month == DHUL_HIJJAH_EARLY["month"] and hijri_day in DHUL_HIJJAH_EARLY["days"]:
        return True, "dhul_hijjah_early", None

    # Arafah
    if hijri_month == ARAFAH["month"] and hijri_day == ARAFAH["day"]:
        return True, "arafah", None

    # Ashura
    if hijri_month == ASHURA["month"] and hijri_day in ASHURA["days"]:
        return True, "ashura", None

    # Ayyam Al-Bid (13th-15th of every month)
    if hijri_day in AYYAM_AL_BID:
        return True, "ayyam_al_bid", None

    # Mondays and Thursdays, weekly Sunnah
    if weekday in ["Monday", "Thursday"]:
        return True, "weekly_sunnah", None

    # Default case: not a fasting day
    return False, None, None


def build_fasting_calendar(start_date: date, end_date: date) -> pd.DataFrame:
    """
    Builds a complete fasting fasting calendar between two specified dates.

    Args:
        start_date: date object representing the first day to include.
        end_date: date object representing the last day to include.

    Returns:
        pandas.DataFrame: DataFrame containing one row per date with these columns:
            - date
            - hijri_month
            - hijri_day
            - fast_type
            - is_fasting
            - celebration_type
    """

    records = []

    # Get unique year/month combinations in date range.
    months_to_fetch = set()
    current = start_date
    while current <= end_date:
        months_to_fetch.add((current.month, current.year))
        current = current.replace(day=1)
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)

    # Obtains the target month conversions.
    for month, year in months_to_fetch:
        api_data = fetch_hijri_month(month, year)

        for day_entry in api_data:
            greg = day_entry["gregorian"]
            hijri = day_entry["hijri"]

            # Parse Gregorian date
            greg_date = date(
                int(greg["year"]),
                int(greg["month"]["number"]),
                int(greg["day"])
            )

            # Skip days outside requested range
            if greg_date < start_date or greg_date > end_date:
                continue

            hijri_month = int(hijri["month"]["number"])
            hijri_day = int(hijri["day"])
            weekday = greg["weekday"]["en"]

            is_fasting, fast_type, celebration = classify_day(
                str(greg_date), hijri_month, hijri_day, weekday
            )

            records.append({
                "date": str(greg_date),
                "hijri_month": hijri_month,
                "hijri_day": hijri_day,
                "fast_type": fast_type,
                "is_fasting": is_fasting,
                "celebration_type": celebration,
            })

    df = pd.DataFrame(records)
    df = df.sort_values("date").reset_index(drop=True)
    return df


if __name__ == "__main__":
    from datetime import date, timedelta

    start = date(2025, 6, 1)  # Close to first day of Apple Health tracking
    # Sixty days of future records to allow for fasting calendar
    end = date.today() + timedelta(days=60)

    print(f"Building fasting calendar from {start} to {end}")
    df = build_fasting_calendar(start, end)

    print(f"\nTotal days: {len(df)}")
    print(f"Fasting days: {df["is_fasting"].sum()}")
    print(f"\nBreakdown by fast type:")
    print(df[df["is_fasting"]]["fast_type"].value_counts().to_string())

    out_path = os.path.join("data", "fasting_calendar.csv")
    df.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")
