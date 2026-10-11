import matplotlib.pyplot as plt
from data_pipeline import load_and_audit

df = load_and_audit()

# Question 1: Traffic Volume Over Time
df.set_index("timestamp").resample("1h").size().plot(
    title="Hourly Traffic Volume"
)
plt.ylabel("Packet/Event Count")
plt.savefig("hourly_volume.png")

# Question 2: Top Destination Ports
print("\nTop 10 Destination Ports:")
print(df["dst_port"].value_counts().head(10))