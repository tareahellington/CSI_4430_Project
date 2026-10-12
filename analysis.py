import matplotlib.pyplot as plt
from data_pipeline import load_and_audit

# Load and clean data using your pipeline
df = load_and_audit()

# Question 1: Traffic Volume Over Time
print("\n--- Question 1: Hourly Traffic Volume ---")
hourly_counts = df.set_index("timestamp").resample("1h").size()
print(hourly_counts.head())

# Plot traffic over time
plt.figure(figsize=(10, 4))
hourly_counts.plot(title="Darknet Traffic Volume Over Time")
plt.xlabel("Time")
plt.ylabel("Observation Count")
plt.tight_layout()
plt.savefig("hourly_volume.png")
print("Saved traffic plot to 'hourly_volume.png'")

# Question 2: Top Destination Ports & Protocol Indicators
print("\n--- Question 2: Top 10 Targeted Destination Ports ---")
print(df["Port"].value_counts().head(10))

print("\n--- Protocol / Scanner Summary ---")
# Summarizing traffic signatures present in dataset
print(f"TCP Traffic Records: {df['TCP'].notnull().sum()}")
print(f"ICMP Traffic Records: {df['ICMP'].notnull().sum()}")

# Question 3: Data Quality & Missing Intervals Check
print("\n--- Question 3: Missing Intervals Check ---")
zero_intervals = (hourly_counts == 0).sum()
print(f"Number of 1-hour intervals with zero recorded activity: {zero_intervals}")