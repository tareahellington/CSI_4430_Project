from pathlib import Path
 
import matplotlib
matplotlib.use("Agg")  # save to files
import matplotlib.pyplot as plt
import pandas as pd
 
from config import FIGURE_DIR, REPORT_DIR, TIME_BIN
from data_pipeline import run
 
df = run()
Path(FIGURE_DIR).mkdir(parents=True, exist_ok=True)
Path(REPORT_DIR).mkdir(parents=True, exist_ok=True)
 
start, end = df["timestamp"].min(), df["timestamp"].max()
period = f"{start:%Y-%m-%d %H:%M} to {end:%H:%M} (UTC-5)"
meta = f"Observation period: {period}  |  n = {len(df)} events, {int(df['Packets'].sum()):,} packets"
print("\n" + meta)
 
 
# ---------- 1. Volume over time (events + packets) ----------
ts = df.set_index("timestamp")
events = ts.resample(TIME_BIN).size().rename("events")
packets = ts["Packets"].resample(TIME_BIN).sum().rename("packets")
vol = pd.concat([events, packets], axis=1)
vol.to_csv(f"{REPORT_DIR}/table_volume_over_time.csv")
 
empty = vol["events"] == 0
print(f"\n{TIME_BIN} bins: {len(vol)} total, {int(empty.sum())} with zero events")
if empty.any():
    grp = (empty != empty.shift()).cumsum()
    for _, run_ in vol[empty].groupby(grp[empty]):
        print(f"  empty run: {run_.index[0]:%H:%M} to {run_.index[-1]:%H:%M} ({len(run_)} bins)")
 
fig, (a1, a2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
w = pd.Timedelta(TIME_BIN) * 0.9
a1.bar(vol.index, vol["events"], width=w, align="edge")
a1.set_ylabel(f"Events per {TIME_BIN}")
a1.set_title("Events over time")
a2.bar(vol.index, vol["packets"], width=w, align="edge", color="tab:orange")
a2.set_ylabel(f"Packets per {TIME_BIN}")
a2.set_title("Packets over time")
a2.set_xlabel("Time (UTC-5)")
fig.suptitle(meta, fontsize=9, y=0.995)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig1_volume_over_time.png", dpi=150)
plt.close(fig)
 
 
# ---------- 2. Protocol distribution (events + packets) ----------
proto = df.groupby("protocol").agg(events=("protocol", "size"), packets=("Packets", "sum"))
proto["pct_events"] = (proto["events"] / proto["events"].sum() * 100).round(1)
proto["pct_packets"] = (proto["packets"] / proto["packets"].sum() * 100).round(1)
proto = proto.sort_values("events", ascending=False)
proto.to_csv(f"{REPORT_DIR}/table_protocol_distribution.csv")
print("\n--- Protocol distribution ---\n", proto)
 
fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 4))
proto["events"].plot.bar(ax=a1, rot=0)
a1.set_title("Events by protocol")
a1.set_ylabel("Events")
a1.set_xlabel("Protocol label")
proto["packets"].plot.bar(ax=a2, rot=0, color="tab:orange")
a2.set_title("Packets by protocol")
a2.set_ylabel("Packets")
a2.set_xlabel("Protocol label")
fig.suptitle(meta, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig2_protocol_distribution.png", dpi=150)
plt.close(fig)
 
 
# ---------- 3. Port distribution (events) ----------
labels = ["0 (reserved)", "1-1023 (well-known)", "1024-49151 (registered)", "49152-65535 (dynamic)"]
bucket = pd.cut(df["Port"], bins=[-1, 0, 1023, 49151, 65535], labels=labels)
ports = bucket.value_counts().reindex(labels).rename("events").to_frame()
ports["pct_events"] = (ports["events"] / ports["events"].sum() * 100).round(1)
ports.to_csv(f"{REPORT_DIR}/table_port_ranges.csv")
top_ports = df["Port"].value_counts().head(10).rename_axis("Port").rename("events").reset_index()
top_ports.to_csv(f"{REPORT_DIR}/table_top10_ports.csv", index=False)
print("\n--- Port ranges ---\n", ports)
print("\n--- Top 10 ports ---\n", top_ports.to_string(index=False))
 
fig, ax = plt.subplots(figsize=(9, 4))
ports["events"].plot.bar(ax=ax, rot=15)
ax.set_title("Port distribution")
ax.set_ylabel("Events (count of records)")
ax.set_xlabel("Port range")
fig.suptitle(meta, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig3_port_distribution.png", dpi=150)
plt.close(fig)
 
print(f"\nSaved figures to {FIGURE_DIR}/ and tables to {REPORT_DIR}/")