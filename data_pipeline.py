import hashlib
import pandas as pd
from config import DATA_PATH, SALT, SAMPLE_SIZE


def load_and_audit():
    # Step 1: Load Data
    df = pd.read_csv(DATA_PATH, nrows=SAMPLE_SIZE)

    # Step 3: Print Quality Audits
    print(f"Missing values:\n{df.isnull().sum()}")
    print(f"\nDuplicates: {df.duplicated().sum()}")

    # Step 4: Pseudonymize Source IPs (Using exact column name 'SourceIP')
    df["src_ip_pseudonym"] = df["SourceIP"].apply(
        lambda ip: hashlib.sha256((str(ip) + SALT).encode()).hexdigest()[:16]
    )
    df.drop(columns=["SourceIP"], inplace=True)

    # Clean and parse timestamps (Using exact column name 'First')
    df["timestamp"] = pd.to_datetime(df["First"], errors="coerce")

    return df