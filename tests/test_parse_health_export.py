import os
import tempfile

import pandas as pd
import pytest

from ingestion.parse_health_export import (
    METRICS,
    SLEEP_TYPES,
    parse_health_export,
    summarize_by_day,
)


SAMPLE_XML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE HealthData [
<!ATTLIST Workout workoutActivityType CDATA #REQUIRED>
]>
<HealthData locale="en_CA">
    <Record type="HKQuantityTypeIdentifierRestingHeartRate"
            sourceName="Watch" sourceVersion="10.0"
            unit="count/min" value="62.0"
            startDate="2026-04-01 06:00:00 -0600"
            endDate="2026-04-01 06:05:00 -0600"/>
    <Record type="HKQuantityTypeIdentifierRestingHeartRate"
            sourceName="Watch" sourceVersion="10.0"
            unit="count/min" value="64.0"
            startDate="2026-04-01 14:00:00 -0600"
            endDate="2026-04-01 14:05:00 -0600"/>
    <Record type="HKQuantityTypeIdentifierStepCount"
            sourceName="Watch" sourceVersion="10.0"
            unit="count" value="5000"
            startDate="2026-04-01 08:00:00 -0600"
            endDate="2026-04-01 08:05:00 -0600"/>
    <Record type="HKQuantityTypeIdentifierActiveEnergyBurned"
            sourceName="Watch" sourceVersion="10.0"
            unit="kcal" value="250.5"
            startDate="2026-04-01 08:00:00 -0600"
            endDate="2026-04-01 08:05:00 -0600"/>
    <Record type="HKCategoryTypeIdentifierSleepAnalysis"
            sourceName="Watch" sourceVersion="10.0"
            value="HKCategoryValueSleepAnalysisAsleepREM"
            startDate="2026-04-01 23:00:00 -0600"
            endDate="2026-04-02 01:30:00 -0600"/>
    <Record type="HKCategoryTypeIdentifierSleepAnalysis"
            sourceName="Watch" sourceVersion="10.0"
            value="HKCategoryValueSleepAnalysisAsleepCore"
            startDate="2026-04-02 01:30:00 -0600"
            endDate="2026-04-02 04:00:00 -0600"/>
    <Record type="HKCategoryTypeIdentifierSleepAnalysis"
            sourceName="Watch" sourceVersion="10.0"
            value="HKCategoryValueSleepAnalysisAsleepDeep"
            startDate="2026-04-02 04:00:00 -0600"
            endDate="2026-04-02 06:00:00 -0600"/>
    <Record type="HKCategoryTypeIdentifierSleepAnalysis"
            sourceName="Watch" sourceVersion="10.0"
            value="HKCategoryValueSleepAnalysisInBed"
            startDate="2026-04-02 06:00:00 -0600"
            endDate="2026-04-02 07:00:00 -0600"/>
</HealthData>
"""


class TestParseHealthExport:
    """parse_health_export — parses Apple Health XML and extracts relevant records."""

    def test_parses_heart_rate_records(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_XML)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            hr_records = df[df["metric"] == "resting_heart_rate"]
            assert len(hr_records) == 2
            assert set(hr_records["value"]) == {"62.0", "64.0"}
        finally:
            os.unlink(path)

    def test_parses_step_count_records(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_XML)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            step_records = df[df["metric"] == "steps"]
            assert len(step_records) == 1
            assert step_records.iloc[0]["value"] == "5000"
        finally:
            os.unlink(path)

    def test_parses_active_calories_records(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_XML)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            cal_records = df[df["metric"] == "active_calories"]
            assert len(cal_records) == 1
            assert cal_records.iloc[0]["value"] == "250.5"
        finally:
            os.unlink(path)

    def test_parses_sleep_records(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_XML)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            sleep_records = df[df["metric"] == "sleep"]
            # REM (2.5h), Core (2.5h), Deep (2.0h) = 7.0h total
            assert len(sleep_records) == 3
            total_sleep = sleep_records["value"].astype(float).sum()
            assert total_sleep == pytest.approx(7.0, 0.1)
        finally:
            os.unlink(path)

    def test_skips_in_bed_records(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_XML)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            assert not any(df["metric"] == "sleep_in_bed")
            assert not any("InBed" in str(v) for v in df["value"])
        finally:
            os.unlink(path)

    def test_returns_dataframe_with_expected_columns(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(SAMPLE_XML)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            assert list(df.columns) == ["date", "metric", "value", "unit"]
        finally:
            os.unlink(path)

    def test_returns_empty_dataframe_for_empty_xml(self):
        empty_xml = '<HealthData locale="en_CA"></HealthData>'
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(empty_xml)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            assert df.empty
        finally:
            os.unlink(path)

    def test_skips_unknown_record_types(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<HealthData locale="en_CA">
    <Record type="HKQuantityTypeIdentifierUnknownMetric"
            value="123"
            startDate="2026-04-01 06:00:00 -0600"/>
</HealthData>"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            assert df.empty
        finally:
            os.unlink(path)

    def test_handles_invalid_sleep_datetime_gracefully(self):
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<HealthData locale="en_CA">
    <Record type="HKCategoryTypeIdentifierSleepAnalysis"
            value="HKCategoryValueSleepAnalysisAsleepREM"
            startDate="invalid-date"
            endDate="2026-04-02 01:30:00 -0600"/>
</HealthData>"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml)
            f.flush()
            path = f.name

        try:
            df = parse_health_export(path)
            assert df.empty
        finally:
            os.unlink(path)


class TestSummarizeByDay:
    """summarize_by_day — aggregates raw health data to one row per (date, metric)."""

    def test_sums_steps_per_day(self):
        raw = pd.DataFrame({
            "date": ["2026-04-01", "2026-04-01", "2026-04-02"],
            "metric": ["steps", "steps", "steps"],
            "value": ["1000", "2000", "3000"],
            "unit": ["count", "count", "count"],
        })
        summary = summarize_by_day(raw)
        day1 = summary[(summary["date"] == "2026-04-01") & (summary["metric"] == "steps")]
        assert len(day1) == 1
        assert day1.iloc[0]["value"] == 3000

    def test_averages_heart_rate_per_day(self):
        raw = pd.DataFrame({
            "date": ["2026-04-01", "2026-04-01", "2026-04-02"],
            "metric": ["resting_heart_rate", "resting_heart_rate", "resting_heart_rate"],
            "value": ["60.0", "62.0", "64.0"],
            "unit": ["count/min", "count/min", "count/min"],
        })
        summary = summarize_by_day(raw)
        day1 = summary[(summary["date"] == "2026-04-01") & (summary["metric"] == "resting_heart_rate")]
        assert len(day1) == 1
        assert day1.iloc[0]["value"] == 61.0

    def test_sums_calories_per_day(self):
        raw = pd.DataFrame({
            "date": ["2026-04-01", "2026-04-01"],
            "metric": ["active_calories", "active_calories"],
            "value": ["100.5", "200.5"],
            "unit": ["kcal", "kcal"],
        })
        summary = summarize_by_day(raw)
        day1 = summary[(summary["date"] == "2026-04-01") & (summary["metric"] == "active_calories")]
        assert len(day1) == 1
        assert day1.iloc[0]["value"] == 301.0

    def test_returns_sorted_results(self):
        raw = pd.DataFrame({
            "date": ["2026-04-02", "2026-04-01"],
            "metric": ["steps", "steps"],
            "value": ["1000", "2000"],
            "unit": ["count", "count"],
        })
        summary = summarize_by_day(raw)
        dates = summary["date"].tolist()
        assert dates == sorted(dates)

    def test_empty_dataframe_returns_empty(self):
        raw = pd.DataFrame(columns=["date", "metric", "value", "unit"])
        summary = summarize_by_day(raw)
        assert summary.empty

    def test_single_record_returns_single_row(self):
        raw = pd.DataFrame({
            "date": ["2026-04-01"],
            "metric": ["steps"],
            "value": ["5000"],
            "unit": ["count"],
        })
        summary = summarize_by_day(raw)
        assert len(summary) == 1
        assert summary.iloc[0]["date"] == "2026-04-01"
        assert summary.iloc[0]["metric"] == "steps"
        assert summary.iloc[0]["value"] == 5000


class TestSleepMissingDates:
    """parse_health_export — skips sleep records with missing start/end dates."""

    def test_skips_sleep_with_empty_start(self, tmp_path):
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<HealthData locale="en_CA">
    <Record type="HKCategoryTypeIdentifierSleepAnalysis"
            value="HKCategoryValueSleepAnalysisAsleepREM"
            startDate=""
            endDate="2026-04-02 01:30:00 -0600"/>
</HealthData>'''
        path = tmp_path / "test.xml"
        path.write_text(xml)
        df = parse_health_export(str(path))
        assert df.empty

    def test_skips_sleep_with_empty_end(self, tmp_path):
        xml = '''<?xml version="1.0" encoding="UTF-8"?>
<HealthData locale="en_CA">
    <Record type="HKCategoryTypeIdentifierSleepAnalysis"
            value="HKCategoryValueSleepAnalysisAsleepREM"
            startDate="2026-04-01 23:00:00 -0600"
            endDate=""/>
</HealthData>'''
        path = tmp_path / "test.xml"
        path.write_text(xml)
        df = parse_health_export(str(path))
        assert df.empty
