import hashlib
import hmac
from pathlib import Path
import pandas as pd
from config import (
    DATA_PATHS,
    SALT,
    SAMPLE_SIZE,
    PROCESSED_DIR,
    REPORT_DIR,
    LOCAL_TZ,
    SCANNER_PATTERNS,
)

# Keep Prefix, RDNS, and Country (if present) for network/scanner analysis.
# Still drop exact SourceIP, raw payload Samples, and precise Lat/Long.
DROP_COLS = ["SourceIP", "Samples", "City", "Lat", "Long"]


def pseudonymize(ip) -> str:
    return hmac.new(SALT.encode(), str(ip).encode(), hashlib.sha256).hexdigest()[:12]


def load_raw() -> pd.DataFrame:
    frames = []
    for path in DATA_PATHS:
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Missing input file: {path}")
        temp = pd.read_csv(p, nrows=SAMPLE_SIZE)
        temp["source_file"] = p.name
        frames.append(temp)
    return pd.concat(frames, ignore_index=True)


def derive_protocol(df: pd.DataFrame) -> pd.Series:
    proto = pd.Series("Other/unlabelled", index=df.index)
    proto[df["ICMP"].notna()] = "ICMP"
    proto[df["TCP"].notna()] = "TCP"  # TCP wins if both are populated
    return proto


def classify_scanner(rdns_series: pd.Series) -> pd.Series:
    return rdns_series.fillna("").str.contains(SCANNER_PATTERNS, regex=True)


def clean(raw: pd.DataFrame):
    df = raw.copy()
    n_raw = len(df)

    # Check exact duplicates across all original data columns (excluding source_file tag)
    data_cols = [c for c in raw.columns if c != "source_file"]
    dup_mask = raw.duplicated(subset=data_cols, keep="first")

    # Parse timestamps and numeric fields
    for col in ["First", "Last"]:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True).dt.tz_convert(LOCAL_TZ)
    for col in ["Port", "Packets", "Bytes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Quarantine rules
    rules = {
        "exact_duplicate_row": dup_mask,
        "unparseable_timestamp": df["First"].isna() | df["Last"].isna(),
        "last_before_first": df["Last"] < df["First"],
        "non_numeric_port_packets_bytes": df[["Port", "Packets", "Bytes"]].isna().any(axis=1),
        "nonpositive_packets_or_bytes": (df["Packets"] <= 0) | (df["Bytes"] <= 0),
        "port_out_of_range": (df["Port"] < 0) | (df["Port"] > 65535),
    }
    reason = pd.Series("", index=df.index)
    for name, mask in rules.items():
        reason = reason.where(~mask, reason + name + ";")

    # Feature engineering & pseudonymization
    df["src_ip_pseudonym"] = df["SourceIP"].apply(pseudonymize)
    df["timestamp"] = df["First"]
    df["duration_sec"] = (df["Last"] - df["First"]).dt.total_seconds()
    df["protocol"] = derive_protocol(df)
    df["is_known_scanner"] = classify_scanner(df["RDNS"])
    df["port_zero"] = df["Port"] == 0

    # Safely drop only columns that exist in the dataframe
    cols_to_drop = [c for c in DROP_COLS if c in df.columns]
    df = df.drop(columns=cols_to_drop)

    bad = reason != ""
    quarantine = df[bad].copy()
    quarantine["reason"] = reason[bad].str.rstrip(";")
    cleaned = df[~bad].copy()

    # Before/after summary table
    rows = [
        ("Records before processing (combined)", n_raw, f"Across {len(DATA_PATHS)} files"),
        ("Records retained", len(cleaned), "Passed all checks"),
        ("Records set aside", len(quarantine), "Saved to quarantine.csv"),
    ]
    for name, mask in rules.items():
        rows.append((f"  set aside: {name}", int(mask.sum()), "A record can match >1 rule"))
    rows.append((
        "Retained: Known research scanners",
        int(cleaned["is_known_scanner"].sum()),
        "Matched RDNS scanner regex",
    ))
    rows.append((
        "Retained but flagged: Port == 0",
        int(cleaned["port_zero"].sum()),
        "Kept; unusual port value",
    ))

    summary = pd.DataFrame(rows, columns=["item", "count", "note"])
    summary["percent_of_raw"] = (summary["count"] / n_raw * 100).round(1)
    return cleaned, quarantine, summary


def run():
    raw = load_raw()
    cleaned, quarantine, summary = clean(raw)

    Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)
    Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(f"{PROCESSED_DIR}/darknet_clean.csv", index=False)
    quarantine.to_csv(f"{PROCESSED_DIR}/quarantine.csv", index=False)
    summary.to_csv(f"{REPORT_DIR}/before_after_summary.csv", index=False)

    print("\n=== Before / after summary ===")
    print(summary.to_string(index=False))
    return cleaned


load_and_audit = run

if __name__ == "__main__":
    run()