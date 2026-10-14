# Configuration settings
import os

DATA_PATH = "data/Darknet.csv"
SAMPLE_SIZE = None
SALT = "csi4430_secure_project_salt_2026"

OUT_DIR = "outputs"
PROCESSED_DIR = f"{OUT_DIR}/processed"
FIGURE_DIR = f"{OUT_DIR}/figures"
REPORT_DIR = f"{OUT_DIR}/reports"
 
TIME_BIN = "5min"                       # bin size for volume over time
LOCAL_TZ = "Etc/GMT+5"                  # = UTC-05:00 