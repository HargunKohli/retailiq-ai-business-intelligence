"""Validate the raw Walmart M5 files in data/raw/.

Group 1: file shapes (rows, columns, column names, memory use).
Group 2: calendar checks (dates, day keys, week keys, SNAP, events, sales coverage).

Read-only: this script never modifies files in data/raw/.
Run from the project root:
    .venv/bin/python src/validate_data.py
"""

import csv
import gc
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

EXPECTED_FILES = [
    "calendar.csv",
    "sell_prices.csv",
    "sales_train_validation.csv",
    "sales_train_evaluation.csv",
    "sample_submission.csv",
]

DAY_COLUMN = re.compile(r"^d_\d+$")

# PASS = check succeeded, INFO = measured fact (not pass/fail),
# FAIL = genuine validation problem.
PASS, INFO, FAIL = "PASS", "INFO", "FAIL"
results = []  # list of (level, filename, message)


def record(level, filename, message):
    results.append((level, filename, message))
    print(f"  [{level}] {message}")


def describe_columns(columns):
    """List columns in full, but summarise the long run of d_<n> day columns."""
    day_cols = [c for c in columns if DAY_COLUMN.match(c)]
    other_cols = [c for c in columns if not DAY_COLUMN.match(c)]
    text = ", ".join(other_cols) if other_cols else "(none)"
    if day_cols:
        text += (
            f" + {len(day_cols):,} day columns matching d_<n> "
            f"(first in file: {day_cols[0]}, last in file: {day_cols[-1]})"
        )
    return text


def check_shape(filename):
    path = RAW_DIR / filename
    print(f"\n{filename}")

    if not path.exists():
        record(FAIL, filename, f"file not found at {path}")
        return

    # Read the header line directly: pandas silently renames duplicate
    # column names (x, x.1, ...), which would hide a real problem.
    with path.open(newline="", encoding="utf-8") as f:
        header = next(csv.reader(f), [])
    duplicates = sorted(name for name, n in Counter(header).items() if n > 1)

    try:
        df = pd.read_csv(path)
    except Exception as exc:  # malformed rows, encoding problems, etc.
        record(FAIL, filename, f"could not be read by pandas: {exc}")
        return

    rows, cols = df.shape
    size_mb = path.stat().st_size / 1_000_000
    memory_mb = df.memory_usage(deep=True).sum() / 1_000_000

    record(INFO, filename, f"size on disk: {size_mb:,.1f} MB")
    record(INFO, filename, f"rows: {rows:,} (excluding header)")
    record(INFO, filename, f"columns: {cols:,}")
    record(INFO, filename, f"column names: {describe_columns(list(df.columns))}")
    record(INFO, filename, f"memory once loaded: {memory_mb:,.1f} MB (pandas default types)")

    if rows == 0:
        record(FAIL, filename, "file has a header but no data rows")
    else:
        record(PASS, filename, "file contains data rows")

    if duplicates:
        record(FAIL, filename, f"duplicate column names: {', '.join(duplicates)}")
    else:
        record(PASS, filename, "column names are unique")

    if len(header) != cols:
        record(FAIL, filename, f"header has {len(header):,} names but pandas loaded {cols:,} columns")
    else:
        record(PASS, filename, "header and loaded column count match")

    # Free this file's memory before loading the next one.
    del df
    gc.collect()


# ---------------------------------------------------------------------------
# Group 2 — calendar.csv
# Each check takes the calendar DataFrame and returns a list of results:
#   {"level": PASS | INFO | FAIL, "check": <short name>, "message": <text>}
# Checks never print or modify data, so notebooks can display them as tables.
# Problems produce FAIL results instead of raising errors.
# ---------------------------------------------------------------------------

SALES_FILES = ["sales_train_validation.csv", "sales_train_evaluation.csv"]
SALES_ID_COLUMNS = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"]
SNAP_COLUMNS = ["snap_CA", "snap_TX", "snap_WI"]
EVENT_PAIRS = [("event_name_1", "event_type_1"), ("event_name_2", "event_type_2")]


def result(level, check, message):
    return {"level": level, "check": check, "message": message}


def as_table(results):
    """Turn a list of results into a DataFrame for display."""
    return pd.DataFrame(results, columns=["level", "check", "message"])


def missing_columns(calendar, columns, name):
    """FAIL result listing required columns that are absent, or [] if all are present."""
    absent = [c for c in columns if c not in calendar.columns]
    if absent:
        return [result(FAIL, name, f"required column(s) missing: {', '.join(absent)}; check skipped")]
    return []


def parsed_dates(calendar):
    """`date` parsed strictly as YYYY-MM-DD; anything else becomes NaT."""
    return pd.to_datetime(calendar["date"], format="%Y-%m-%d", errors="coerce")


def fmt_date(value):
    """YYYY-MM-DD, or 'invalid date' for NaT/None — never raises."""
    return "invalid date" if pd.isna(value) else f"{value:%Y-%m-%d}"


def file_lines(mask, limit=3):
    """First few CSV line numbers where `mask` is True (header = line 1)."""
    lines = [str(i + 2) for i in mask[mask].index[:limit]]
    more = " …" if int(mask.sum()) > limit else ""
    return ", ".join(lines) + more


def preview(items, limit=3):
    """First few items as text, with … if there are more."""
    items = list(items)
    return ", ".join(map(str, items[:limit])) + (" …" if len(items) > limit else "")


def load_calendar():
    """Load calendar.csv in memory; parse `date` if the column exists. File is not changed."""
    calendar = pd.read_csv(RAW_DIR / "calendar.csv")
    if "date" in calendar.columns:
        calendar["date"] = parsed_dates(calendar)
    return calendar


def read_header(filename, raw_dir=RAW_DIR):
    """Column names from a CSV's first line ([] if the file is empty).

    Raises OSError if the file cannot be opened; callers turn that into FAIL.
    """
    with (raw_dir / filename).open(newline="", encoding="utf-8") as f:
        return next(csv.reader(f), [])


# --- 2.1 Unique dates ------------------------------------------------------
def check_unique_dates(calendar):
    name = "unique dates"
    if fail := missing_columns(calendar, ["date"], name):
        return fail
    dates = parsed_dates(calendar)
    bad = dates.isna()
    valid = dates[~bad]
    out = []

    if bad.any():
        out.append(result(FAIL, name, f"{int(bad.sum()):,} of {len(dates):,} dates are missing "
                                      f"or not YYYY-MM-DD (file lines {file_lines(bad)})"))
    else:
        out.append(result(PASS, name, "all dates parse as YYYY-MM-DD"))

    if valid.empty:
        out.append(result(FAIL, name, "no valid dates: duplicate check and date range not possible"))
        return out

    dupes = valid.duplicated()
    if dupes.any():
        out.append(result(FAIL, name, f"{int(dupes.sum()):,} duplicate dates (file lines {file_lines(dupes)})"))
    else:
        out.append(result(PASS, name, "every valid date appears exactly once"))

    out.append(result(INFO, name, f"range of valid dates: {fmt_date(valid.min())} to {fmt_date(valid.max())}"))
    return out


# --- 2.2 Date continuity ---------------------------------------------------
def check_date_continuity(calendar):
    name = "date continuity"
    if fail := missing_columns(calendar, ["date"], name):
        return fail
    dates = parsed_dates(calendar)
    if dates.empty:
        return [result(FAIL, name, "calendar has no rows")]
    invalid = int(dates.isna().sum())
    if invalid:
        return [result(FAIL, name, f"not checked: {invalid:,} dates are missing or invalid "
                                   f"(see 'unique dates')")]
    out = []
    if dates.is_monotonic_increasing:
        out.append(result(PASS, name, "dates are in ascending order in the file"))
    else:
        out.append(result(FAIL, name, "dates are not in ascending order in the file"))
    breaks = int((dates.diff().dropna() != pd.Timedelta(days=1)).sum())
    days_in_range = (dates.max() - dates.min()).days + 1
    if breaks == 0 and days_in_range == len(dates):
        out.append(result(PASS, name, f"{len(dates):,} consecutive daily dates, no gaps"))
    else:
        out.append(result(FAIL, name, f"{breaks:,} breaks in the daily sequence; "
                                      f"{days_in_range:,} days in range vs {len(dates):,} rows"))
    return out


# --- 2.3 Day-key sequence --------------------------------------------------
def check_day_keys(calendar):
    name = "day keys"
    if fail := missing_columns(calendar, ["d"], name):
        return fail
    actual = calendar["d"].tolist()
    expected = [f"d_{i}" for i in range(1, len(actual) + 1)]
    out = []
    dupes = int(calendar["d"].duplicated().sum())
    if dupes:
        out.append(result(FAIL, name, f"{dupes:,} duplicate day keys"))
    else:
        out.append(result(PASS, name, "every day key is unique"))
    mismatches = [i for i, (a, e) in enumerate(zip(actual, expected)) if a != e]
    if mismatches:
        i = mismatches[0]
        out.append(result(FAIL, name, f"{len(mismatches):,} rows break the d_1..d_N sequence; "
                                      f"first at file line {i + 2}: found {actual[i]}, expected {expected[i]}"))
    else:
        out.append(result(PASS, name, f"day keys run d_1 to d_{len(actual)} in date order"))
    return out


# --- 2.4 Week-key completeness ---------------------------------------------
def check_week_keys(calendar):
    name = "week keys"
    if fail := missing_columns(calendar, ["wm_yr_wk"], name):
        return fail
    raw = calendar["wm_yr_wk"]
    if raw.empty:
        return [result(FAIL, name, "calendar has no rows")]

    numeric = pd.to_numeric(raw, errors="coerce")
    missing = raw.isna()
    non_numeric = raw.notna() & numeric.isna()
    non_integer = numeric.notna() & (numeric % 1 != 0)
    out = []

    if missing.any():
        out.append(result(FAIL, name, f"{int(missing.sum()):,} days have no week key "
                                      f"(file lines {file_lines(missing)})"))
    if non_numeric.any():
        out.append(result(FAIL, name, f"{int(non_numeric.sum()):,} week keys are not numbers, "
                                      f"e.g. {preview(raw[non_numeric].map(repr))} "
                                      f"(file lines {file_lines(non_numeric)})"))
    if non_integer.any():
        out.append(result(FAIL, name, f"{int(non_integer.sum()):,} week keys are not whole numbers, "
                                      f"e.g. {preview(numeric[non_integer])} "
                                      f"(file lines {file_lines(non_integer)})"))
    if (missing | non_numeric | non_integer).any():
        out.append(result(INFO, name, "order, run and week-length checks skipped until week keys are valid"))
        return out

    out.append(result(PASS, name, "every day has a whole-number week key"))
    wk = numeric.astype("int64")

    if wk.is_monotonic_increasing:
        out.append(result(PASS, name, "week keys never decrease over time"))
    else:
        out.append(result(FAIL, name, "week keys decrease at some point in file order"))

    runs = int((wk != wk.shift()).sum())
    if runs == wk.nunique():
        out.append(result(PASS, name, "each week key covers one unbroken run of days"))
    else:
        out.append(result(FAIL, name, f"{wk.nunique():,} week keys appear in {runs:,} separate runs"))

    sizes = wk.groupby(wk, sort=True).size()
    first, last = sizes.index[0], sizes.index[-1]
    interior = [k for k in sizes.index[sizes != 7] if k not in (first, last)]
    out.append(result(INFO, name, f"{len(sizes):,} week keys; {int((sizes == 7).sum()):,} have 7 days"))
    if interior:
        out.append(result(FAIL, name, f"{len(interior):,} weeks inside the range do not have 7 days, "
                                      f"e.g. {preview(interior)}"))
    else:
        out.append(result(PASS, name, "all weeks inside the range have 7 days"))
    for k, position in [(first, "first"), (last, "last")]:
        if sizes[k] != 7:
            out.append(result(INFO, name, f"{position} week ({k}) is partial: {int(sizes[k])} days"))
        if first == last:
            break  # a single week is both first and last; report it once
    return out


# --- 2.5 SNAP values -------------------------------------------------------
def check_snap(calendar):
    name = "SNAP values"
    out = []
    for col in SNAP_COLUMNS:
        if col not in calendar.columns:
            out.append(result(FAIL, name, f"{col}: column missing; check skipped"))
            continue
        values = calendar[col]
        missing = int(values.isna().sum())
        invalid = int((values.notna() & ~values.isin([0, 1])).sum())
        if missing or invalid:
            out.append(result(FAIL, name, f"{col}: {missing:,} missing, {invalid:,} values other than 0/1"))
        else:
            out.append(result(PASS, name, f"{col}: only 0 or 1, none missing"))
            out.append(result(INFO, name, f"{col}: {int(values.sum()):,} SNAP days of {len(values):,}"))
    return out


# --- 2.6 Missing event values ----------------------------------------------
def check_events(calendar):
    name = "event values"
    event_cols = [c for pair in EVENT_PAIRS for c in pair]
    if fail := missing_columns(calendar, event_cols, name):
        return fail
    out = []
    for name_col, type_col in EVENT_PAIRS:
        no_name = calendar[name_col].isna()
        no_type = calendar[type_col].isna()
        out.append(result(INFO, name, f"{name_col}: blank on {int(no_name.sum()):,} of "
                                      f"{len(calendar):,} days ({no_name.mean():.1%}); blank = no event"))
        mismatch = int((no_name != no_type).sum())
        if mismatch:
            out.append(result(FAIL, name, f"{mismatch:,} days have {name_col} without {type_col}, or the reverse"))
        else:
            out.append(result(PASS, name, f"{name_col} and {type_col} are always filled together"))
    orphan = int((calendar["event_name_2"].notna() & calendar["event_name_1"].isna()).sum())
    if orphan:
        out.append(result(FAIL, name, f"{orphan:,} days have a second event but no first event"))
    else:
        out.append(result(PASS, name, "a second event only appears when a first event exists"))
    types = sorted(set(calendar["event_type_1"].dropna()) | set(calendar["event_type_2"].dropna()))
    names = set(calendar["event_name_1"].dropna()) | set(calendar["event_name_2"].dropna())
    out.append(result(INFO, name, f"{len(names):,} distinct event names; types: {', '.join(types)}"))
    return out


# --- 2.7 Calendar vs. sales day coverage -----------------------------------
def check_sales_day_coverage(calendar, raw_dir=RAW_DIR, files=SALES_FILES):
    name = "sales coverage"
    if fail := missing_columns(calendar, ["d", "date"], name):
        return fail
    cal_days = calendar["d"].tolist()
    cal_set = set(cal_days)
    date_of = dict(zip(calendar["d"], parsed_dates(calendar)))
    out = []

    for filename in files:
        try:
            header = read_header(filename, raw_dir)
        except OSError as exc:
            out.append(result(FAIL, name, f"{filename}: header could not be read ({type(exc).__name__})"))
            continue
        if not header:
            out.append(result(FAIL, name, f"{filename}: file is empty (no header line)"))
            continue

        day_cols = [c for c in header if DAY_COLUMN.match(c)]
        other_cols = [c for c in header if not DAY_COLUMN.match(c)]

        missing_ids = [c for c in SALES_ID_COLUMNS if c not in other_cols]
        if missing_ids:
            out.append(result(FAIL, name, f"{filename}: missing ID column(s): {preview(missing_ids, 6)}"))
        unexpected = [c for c in other_cols if c not in SALES_ID_COLUMNS]
        if unexpected:
            out.append(result(FAIL, name, f"{filename}: unexpected non-day column(s): {preview(unexpected)}"))

        if not day_cols:
            out.append(result(FAIL, name, f"{filename}: no day columns (d_<n>) found"))
            continue

        dup_days = sorted(c for c, n in Counter(day_cols).items() if n > 1)
        if dup_days:
            out.append(result(FAIL, name, f"{filename}: duplicate day columns: {preview(dup_days)}"))

        unknown = [c for c in day_cols if c not in cal_set]
        if unknown:
            out.append(result(FAIL, name, f"{filename}: {len(unknown):,} day columns not in calendar, "
                                          f"e.g. {preview(unknown)}"))
        else:
            out.append(result(PASS, name, f"{filename}: every sales day column has a calendar date"))

        n = len(day_cols)
        if n > len(cal_days):
            out.append(result(FAIL, name, f"{filename}: {n:,} day columns but calendar has "
                                          f"only {len(cal_days):,} days"))
        elif day_cols == cal_days[:n]:
            out.append(result(PASS, name, f"{filename}: day columns match the first {n:,} "
                                          f"calendar days in order"))
        else:
            out.append(result(FAIL, name, f"{filename}: day columns are not the first {n:,} "
                                          f"calendar days in order"))

        if not unknown and not dup_days and n <= len(cal_days):
            first, last = day_cols[0], day_cols[-1]
            out.append(result(INFO, name, f"{filename}: sales cover {fmt_date(date_of.get(first))} to "
                                          f"{fmt_date(date_of.get(last))}; {len(cal_days) - n:,} "
                                          f"calendar days after {last} have no sales"))
    return out


CALENDAR_CHECKS = [
    check_unique_dates,
    check_date_continuity,
    check_day_keys,
    check_week_keys,
    check_snap,
    check_events,
    check_sales_day_coverage,
]


# --- Small summary tables for notebooks ------------------------------------
def calendar_missing_summary(calendar):
    """Missing values per column."""
    missing = calendar.isna().sum()
    return pd.DataFrame({"missing": missing, "missing_pct": (missing / len(calendar) * 100).round(1)})


def calendar_week_sizes(calendar):
    """How many week keys have 1, 2, ... 7 days."""
    sizes = calendar.groupby("wm_yr_wk").size()
    return sizes.value_counts().sort_index().rename_axis("days_in_week").reset_index(name="weeks")


def calendar_event_types(calendar):
    """Number of event occurrences per event type, across both event columns."""
    types = pd.concat([calendar["event_type_1"], calendar["event_type_2"]]).dropna()
    return types.value_counts().rename_axis("event_type").reset_index(name="occurrences")


def calendar_days_without_sales(calendar, filename="sales_train_evaluation.csv", raw_dir=RAW_DIR):
    """Calendar rows whose day key is not a column in the sales file.

    Runs the sales-coverage check for this file first and raises ValueError
    if it has any FAIL, so an invalid header can never produce a misleading
    table. The FAIL details are included in the error message.
    """
    coverage = check_sales_day_coverage(calendar, raw_dir=raw_dir, files=[filename])
    fails = [r["message"] for r in coverage if r["level"] == FAIL]
    if fails:
        raise ValueError(f"cannot list days without sales until coverage checks pass: {'; '.join(fails)}")
    sales_days = {c for c in read_header(filename, raw_dir) if DAY_COLUMN.match(c)}
    cols = [c for c in ["d", "date", "weekday", "wm_yr_wk", "event_name_1", "event_name_2"]
            if c in calendar.columns]
    return calendar.loc[~calendar["d"].isin(sales_days), cols]


def run_calendar_group():
    """Command-line runner: print Group 2 results in the same format as Group 1."""
    print("\nGroup 2 — calendar.csv")
    calendar = load_calendar()
    for check in CALENDAR_CHECKS:
        for r in check(calendar):
            record(r["level"], "calendar.csv", f"{r['check']}: {r['message']}")


def print_summary():
    counts = Counter(level for level, _, _ in results)
    print("\n" + "=" * 60)
    print(f"SUMMARY: {counts[PASS]} passed, {counts[FAIL]} failed, {counts[INFO]} informational")
    failures = [(f, m) for level, f, m in results if level == FAIL]
    for filename, message in failures:
        print(f"  FAIL  {filename}: {message}")
    return len(failures)


def main():
    print("Group 1 — file shapes")
    print(f"Reading from: {RAW_DIR}")
    for filename in EXPECTED_FILES:
        check_shape(filename)
    run_calendar_group()
    failures = print_summary()
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
