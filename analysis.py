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


# ---------- 1. Volume over time (events + packets, combined) ----------
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


# ---------- 2. Protocol distribution (events + packets, combined) ----------
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


# ---------- 3. Port distribution (events, combined) ----------
labels = ["0 (reserved)", "1-1023 (well-known)", "1024-49151 (registered)", "49152-65535 (dynamic)"]
df["port_range"] = pd.cut(df["Port"], bins=[-1, 0, 1023, 49151, 65535], labels=labels)
ports = df["port_range"].value_counts().reindex(labels).rename("events").to_frame()
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


# ---------- 4. Side-by-side comparison by source file ----------
# 4a. Side-by-side protocol summary table + grouped bar chart
proto_by_file = (
    df.groupby(["protocol", "source_file"])
    .agg(events=("protocol", "size"), packets=("Packets", "sum"))
    .unstack(fill_value=0)
)
print("\n--- Side-by-side protocol comparison ---\n", proto_by_file)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.5))
proto_by_file["events"].plot.bar(ax=a1, rot=0)
a1.set_title("Events by protocol (Side-by-side)")
a1.set_ylabel("Events")
a1.set_xlabel("Protocol label")
a1.legend(title="Source file")

proto_by_file["packets"].plot.bar(ax=a2, rot=0)
a2.set_title("Packets by protocol (Side-by-side)")
a2.set_ylabel("Packets")
a2.set_xlabel("Protocol label")
a2.legend(title="Source file")

fig.suptitle(meta, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig4_protocol_side_by_side.png", dpi=150)
plt.close(fig)

# Flatten column headers for clean CSV export
proto_by_file_flat = proto_by_file.copy()
proto_by_file_flat.columns = [f"{metric}_{fname}" for metric, fname in proto_by_file.columns]
proto_by_file_flat.to_csv(f"{REPORT_DIR}/table_protocol_side_by_side.csv")

# 4b. Side-by-side port range table + grouped bar chart
ports_by_file = (
    df.groupby(["port_range", "source_file"], observed=False)
    .size()
    .unstack(fill_value=0)
    .reindex(labels)
)
ports_by_file.to_csv(f"{REPORT_DIR}/table_port_ranges_side_by_side.csv")
print("\n--- Side-by-side port ranges ---\n", ports_by_file)

fig, ax = plt.subplots(figsize=(9, 4.5))
ports_by_file.plot.bar(ax=ax, rot=15)
ax.set_title("Port distribution (Side-by-side)")
ax.set_ylabel("Events (count of records)")
ax.set_xlabel("Port range")
ax.legend(title="Source file")
fig.suptitle(meta, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig5_port_side_by_side.png", dpi=150)
plt.close(fig)


# ---------- 5. Known scanners vs. unknown sources (side-by-side) ----------
scanner_summary = (
    df.groupby(["is_known_scanner", "source_file"])
    .agg(
        events=("protocol", "size"),
        packets=("Packets", "sum"),
        unique_sources=("src_ip_pseudonym", "nunique"),
    )
    .unstack(fill_value=0)
)
print("\n--- Known scanners vs. unknown sources ---\n", scanner_summary)

fig, ax = plt.subplots(figsize=(7.5, 4))
scanner_summary["events"].plot.bar(ax=ax, rot=0)
ax.set_xticklabels(["Unknown Sources", "Known Scanners"])
ax.set_title("Events: Known Research Scanners vs. Unknown Sources")
ax.set_ylabel("Events")
ax.set_xlabel("")
ax.legend(title="Source file")
fig.suptitle(meta, fontsize=9)
fig.tight_layout()
fig.savefig(f"{FIGURE_DIR}/fig6_scanner_vs_unknown.png", dpi=150)
plt.close(fig)

scanner_summary_flat = scanner_summary.copy()
scanner_summary_flat.columns = [f"{metric}_{fname}" for metric, fname in scanner_summary.columns]
scanner_summary_flat.to_csv(f"{REPORT_DIR}/table_scanner_vs_unknown.csv")


# ---------- 6. Top source networks (Prefix) & countries ----------
group_cols = (
    ["Country", "Prefix", "is_known_scanner"]
    if "Country" in df.columns
    else ["Prefix", "is_known_scanner"]
)
top_prefixes = (
    df.groupby(group_cols, dropna=False)
    .agg(
        events=("protocol", "size"),
        packets=("Packets", "sum"),
        unique_ips=("src_ip_pseudonym", "nunique"),
    )
    .sort_values("events", ascending=False)
    .head(15)
)
top_prefixes.to_csv(f"{REPORT_DIR}/table_top15_prefixes.csv")
print("\n--- Top 15 prefixes ---\n", top_prefixes)

if "Country" in df.columns:
    top_countries = (
        df.groupby(["Country", "source_file"], dropna=False)
        .size()
        .unstack(fill_value=0)
    )
    top_countries["Total"] = top_countries.sum(axis=1)
    top_countries = top_countries.sort_values("Total", ascending=False).head(10).drop(columns="Total")
    top_countries.to_csv(f"{REPORT_DIR}/table_top10_countries.csv")
    print("\n--- Top 10 countries (side-by-side) ---\n", top_countries)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    top_countries.plot.bar(ax=ax, rot=25)
    ax.set_title("Top 10 Source Countries (Side-by-side)")
    ax.set_ylabel("Events")
    ax.legend(title="Source file")
    fig.suptitle(meta, fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{FIGURE_DIR}/fig7_top10_countries.png", dpi=150)
    plt.close(fig)


# ---------- 7. Long-running flows ----------
long_flows = df[df["duration_sec"] > 60].sort_values("duration_sec", ascending=False)
long_flows.to_csv(f"{REPORT_DIR}/table_long_running_flows.csv", index=False)
print(f"\n--- Long-running flows (>60s): {len(long_flows)} records ---")
if not long_flows.empty:
    preview_cols = [
        c for c in [
            "source_file", "src_ip_pseudonym", "Prefix", "protocol",
            "Port", "Packets", "duration_sec", "is_known_scanner"
        ]
        if c in long_flows.columns
    ]
    print(long_flows[preview_cols].head(10).to_string(index=False))


# ---------- 8. Merit traffic-code inspection ----------
code_audit = (
    df.groupby(["protocol", "TCP", "ICMP", "source_file"], dropna=False)
    .agg(events=("protocol", "size"), packets=("Packets", "sum"))
    .reset_index()
    .sort_values("events", ascending=False)
)
code_audit.to_csv(f"{REPORT_DIR}/table_merit_code_audit.csv", index=False)
print("\n--- Merit traffic-code audit ---\n", code_audit.to_string(index=False))


print(f"\nSaved all figures to {FIGURE_DIR}/ and tables to {REPORT_DIR}/")