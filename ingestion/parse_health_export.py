from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd

# Determining data pathway and target metrics for analysis
EXPORT_PATH = os.path.join("data", "export.xml")

# Selected metrics for analysis, edit later as needed.
METRICS = {
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_heart_rate",
    "HKQuantityTypeIdentifierStepCount": "steps",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "active_calories",
}

# Sleep handled separately by Apple Health.
SLEEP_TYPES = {
    "HKCategoryValueSleepAnalysisAsleepREM":   "sleep_rem",
    "HKCategoryValueSleepAnalysisAsleepCore":  "sleep_core",
    "HKCategoryValueSleepAnalysisAsleepDeep":  "sleep_deep",
}


def parse_health_export(filepath: str) -> pd.DataFrame:
    """Parses the Apple Health export XML file and extracts relevant records based on specified metrics into a DataFrame.

    Args:
        filepath: Path to the Apple Health export XML file.

    Returns:
        pandas.DataFrame: a Dataframe containing the following columns:
            - date: The date of the record
            - metric: The type of health metric
            - value: The value of the metric
            - unit: The unit of the metric (if applicable)

    """

    print(f"Parsing {filepath} ...")
    tree = ET.parse(filepath)
    root = tree.getroot()

    records: list[dict[str, str | float | None]] = []

    SLEEP_RECORD_TYPE = "HKCategoryTypeIdentifierSleepAnalysis"

    # Iterates through tree and finds all values which contains record with date, metric, value and unit.
    for record in root.findall("Record"):
        record_type = record.attrib.get("type")

        if record_type in METRICS:
            metric_name = METRICS[record_type]
            # Splices data to get entire day. Return to this later for hourly analysis
            start_date = record.attrib.get("startDate", "")[:10]
            value = record.attrib.get("value")
            unit = record.attrib.get("unit", "")

            records.append(
                {
                    "date": start_date,
                    "metric": metric_name,
                    "value": value,
                    "unit": unit,
                }
            )

        # Sleep records
        elif record_type == SLEEP_RECORD_TYPE:
            sleep_value = record.attrib.get("value", "")
            if sleep_value not in SLEEP_TYPES:
                continue  # skip InBed and other stages

            start_str = record.attrib.get("startDate", "")
            end_str = record.attrib.get("endDate", "")
            if not start_str or not end_str:
                continue

            # Parse full datetime to calculate duration
            fmt = "%Y-%m-%d %H:%M:%S %z"
            try:
                start_dt = datetime.strptime(start_str, fmt)
                end_dt = datetime.strptime(end_str, fmt)
                hours = round((end_dt - start_dt).total_seconds() / 3600, 2)
            except ValueError:
                continue

            date_str = start_str[:10]
            records.append({
                "date":   date_str,
                "metric": "sleep",
                "value":  hours,
                "unit":   "hr",
            })

    # Convert record list into DataFrame
    df = pd.DataFrame(records)
    print(
        f"Found {len(df)} records across {df['metric'].nunique()} metric types.")
    return df


def summarize_by_day(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates raw health data to one row per (date, metric) pair.

    Heart rate is averaged across the day. All other metrics are summed.

    Args:
        df: Raw DataFrame from parse_health_export()
    Returns:
        pandas.DataFrame: Aggregated DataFrame containing:
            - date
            - metric
            - value
    """

    numeric_df = df.copy()
    numeric_df["value"] = pd.to_numeric(numeric_df["value"], errors="coerce")

    # Obtain summary of each value, summed by date and metric, also resetting index.
    summary = (
        numeric_df
        .groupby(["date", "metric"])["value"]
        .sum()
        .reset_index()
    )

    # Override operation for heart rate to be mean
    hr_mask = numeric_df["metric"] == "resting_heart_rate"
    hr_summary = (
        numeric_df[hr_mask]
        .groupby(["date", "metric"])["value"]
        .mean()
        .reset_index()
    )

    summary = summary[summary["metric"] != "resting_heart_rate"]
    summary = pd.concat([summary, hr_summary], ignore_index=True)
    summary = summary.sort_values(["date", "metric"]).reset_index(drop=True)

    return summary


if __name__ == "__main__":
    raw_df = parse_health_export(EXPORT_PATH)
    day_df = summarize_by_day(raw_df)

    print("\nSample output (latest 10 rows):")
    print(day_df.tail(10).to_string(index=False))

    out_path = os.path.join("data", "health_summary.csv")
    day_df.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")
