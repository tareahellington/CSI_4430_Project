import hashlib
import pandas as pd
import hmac
from pathlib import Path
from config import DATA_PATH, SALT, SAMPLE_SIZE, PROCESSED_DIR, REPORT_DIR, LOCAL_TZ

# columns removed from output (IP address, hostname, payload, etc.)
# City/Lat/Long are not needed for the current questions
DROP_COLS = ["SourceIP", "Prefix", "RDNS", "Samples", "City", "Lat", "Long"]
 
 
def pseudonymize(ip) -> str:
    return hmac.new(SALT.encode(), str(ip).encode(), hashlib.sha256).hexdigest()[:12]
 
 
def load_raw() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, nrows=SAMPLE_SIZE)
 
 
def derive_protocol(df: pd.DataFrame) -> pd.Series:
    proto = pd.Series("Other/unlabelled", index=df.index)
    proto[df["ICMP"].notna()] = "ICMP"
    proto[df["TCP"].notna()] = "TCP"   # TCP wins if a row somehow has both
    return proto
 
 
def clean(raw: pd.DataFrame):
    df = raw.copy()  # work on a copy
    n_raw = len(df)
 
    # exact duplicate rows
    dup_mask = raw.duplicated(keep="first")
 
    # types
    for col in ["First", "Last"]:
        df[col] = pd.to_datetime(df[col], errors="coerce", utc=True).dt.tz_convert(LOCAL_TZ)
    for col in ["Port", "Packets", "Bytes"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
 
    # rules for setting aside rows
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
 
    # pseudonymize so no output files contains raw IPs
    df["src_ip_pseudonym"] = df["SourceIP"].apply(pseudonymize)
    df["timestamp"] = df["First"]
    df["protocol"] = derive_protocol(df)
    df["port_zero"] = df["Port"] == 0   # flagged, kept (see summary)
    df = df.drop(columns=DROP_COLS)
 
    bad = reason != ""
    quarantine = df[bad].copy()
    quarantine["reason"] = reason[bad].str.rstrip(";")
    cleaned = df[~bad].copy()
 
    # before/after table
    rows = [("Records before processing", n_raw, "Original file, unchanged"),
            ("Records retained", len(cleaned), "Passed all checks"),
            ("Records set aside", len(quarantine), "Saved to quarantine.csv")]
    for name, mask in rules.items():
        rows.append((f"  set aside: {name}", int(mask.sum()), "A record can match >1 rule"))
    rows.append(("Retained but flagged: Port == 0", int(cleaned["port_zero"].sum()),
                 "Kept; unusual port value, see limitations"))
    for col in ["City", "TCP", "ICMP"]:
        n = int(raw[col].isna().sum())
        rows.append((f"Left as-is: nulls in {col}", n, "Not applicable"))
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