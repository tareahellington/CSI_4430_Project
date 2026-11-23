# Configuration settings
DATA_PATHS = [
    "data/Darknet_test_data1.csv",
    "data/Darknet_test_data2.csv",
]
SAMPLE_SIZE = None
SALT = "csi4430_secure_project_salt_2026"

OUT_DIR = "outputs"
PROCESSED_DIR = f"{OUT_DIR}/processed"
FIGURE_DIR = f"{OUT_DIR}/figures"
REPORT_DIR = f"{OUT_DIR}/reports"

TIME_BIN = "5min"
LOCAL_TZ = "Etc/GMT+5"  # UTC-05:00

# Regex patterns to identify known benign/research scanners via RDNS
SCANNER_PATTERNS = r"(?i)(shodan|censys|rapid7|shadowserver|binaryedge|internet-census|stretchoid|netcraft|onyphe|leakix|driftnet|masscan)"