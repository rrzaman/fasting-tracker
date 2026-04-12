import xml.etree.ElementTree as ET
import pandas as pd
import os

# Determining data pathway and target metrics for analysis
EXPORT_PATH = os.path.join("data", "export.xml")

# Selected metrics for analysis, edit later as needed.
METRICS = {
    "HKQuantityTypeIdentifierRestingHeartRate": "resting_heart_rate",
    "HKQuantityTypeIdentifierStepCount": "steps",
    "HKQuantityTypeIdentifierActiveEnergyBurned": "active_calories",
    "HKCategoryTypeIdentifierSleepAnalysis": "sleep",
}

def parse_health_export(filepath):
    print(f"Parsing {filepath} ...")
    tree = ET.parse(filepath)
    root = tree.getroot()

    records = []

    # Iterates through tree and finds all values which contains record with date, metric, value and unit.
    for record in root.findall("Record"):
        record_type = record.attrib.get("type")

        if record_type not in METRICS:
            continue

        metric_name = METRICS[record_type]
        start_date = record.attrib.get("startDate", "")[:10] # Splices data to get entire day. Return to this later for hourly analysis
        value = record.attrib.get("value")
        unit = record.attrib.get("unit", "")

        records.append({
            "date" : start_date,
            "metric" : metric_name,
            "value": value,
            "unit":unit
        })

    # Convert record list into DataFrame
    df = pd.DataFrame(records)
    print(f"Found {len(df)} records across {df['metric'].nunique()} metric types.")
    return df

def summarize_by_day(df):
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

    print("\nSample output (first 10 rows):")
    print(day_df.head(10).to_string(index=False))

    out_path = os.path.join("data", "health_summary.csv")
    day_df.to_csv(out_path, index=False)
    print(f"\nSaved to {out_path}")