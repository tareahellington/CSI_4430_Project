import hashlib
import pandas as pd
from config import DATA_PATH, SALT, SAMPLE_SIZE


def load_and_audit():
    # Step 1: Load Data
    df = pd.read_csv(DATA_PATH, nrows=SAMPLE_SIZE)

    # Step 3: Quality Checks
    print(f"Missing values:\n{df.isnull().sum()}")
    print(f"Duplicates: {df.duplicated().sum()}")

    # Step 4: Pseudonymize Source IPs
    df["src_ip_pseudonym"] = df["src_ip"].apply(
        lambda ip: hashlib.sha256((str(ip) + SALT).encode()).hexdigest()[:16]
    )
    df.drop(columns=["src_ip"], inplace=True)

    # Clean timestamps
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df