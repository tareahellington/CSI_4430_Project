import pandas as pd
from config import DATA_PATHS, PROCESSED_DIR, REPORT_DIR
from data_pipeline import load_raw

raw = load_raw()
clean = pd.read_csv(f"{PROCESSED_DIR}/darknet_clean.csv")
quarantine = pd.read_csv(f"{PROCESSED_DIR}/quarantine.csv")
summary = pd.read_csv(f"{REPORT_DIR}/before_after_summary.csv")

print("=== AUTOMATED TEST & VERIFICATION REPORT ===")

# Test 1: Multi-file Record Reconciliation
raw_n = len(raw)
clean_n = len(clean)
quar_n = len(quarantine)
assert raw_n == clean_n + quar_n, f"Mismatch! Raw ({raw_n}) != Clean ({clean_n}) + Quar ({quar_n})"
print(f"1. Reconciliation Test: PASSED ({len(DATA_PATHS)} files: Raw {raw_n} = Clean {clean_n} + Quarantine {quar_n})")

# Test 2: Chart/Table Total Agreement
table_vol = pd.read_csv(f"{REPORT_DIR}/table_volume_over_time.csv")
assert table_vol["events"].sum() == clean_n, "Volume table sum does not match clean dataset count!"
print(f"2. Chart/Table Agreement Test: PASSED (Summary events {table_vol['events'].sum()} == Clean count {clean_n})")

# Test 3: Sensitive Identifier Audit (Raw IP must be gone; Prefix/RDNS allowed for attribution)
assert "SourceIP" not in clean.columns, "Raw SourceIP column found in clean output!"
print("3. Privacy Disclosure Test: PASSED (0 raw SourceIP columns present in clean CSV)")

# Test 4: File Origin Check
print("\nRecords Retained by Source File:")
print(clean["source_file"].value_counts().to_string())

# Test 5: Quarantine Transparency
print("\nQuarantine Reasons Summary:")
print(quarantine["reason"].value_counts().to_string())