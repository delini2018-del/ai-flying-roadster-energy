import json, math
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
R = json.load(open("results/results.json"))
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
INK, RED, AMB, BLUE, GREY, TEAL = "#1f2937", "#c2410c", "#e9a23b", "#2563eb", "#94a3b8", "#0f766e"
fill = R["fill_kWh"]["0.58"]
hop_air = [x for v in R["boost_sweep"].values() for x in v["backtoback"] + v["rewarmed"]]
hop_lo, hop_hi = min(hop_air) / 250 * fill, max(hop_air) / 250 * fill
items = [("Lifting the car 2.5 m with an\nelectric motor (the useful work)", R["lift_work_kWh"], R["lift_work_kWh"], TEAL),
         ("Driving an efficient EV 10 km", 1.9, 1.9, GREY),
         ("One hop on compressed air", hop_lo, hop_hi, RED),
         ("Refilling the whole tank once", R["fill_kWh"]["0.70"], R["fill_kWh"]["0.40"], AMB)]
fig, ax = plt.subplots(figsize=(11, 4.8))
for i, (n, lo, hi, c) in enumerate(items):
    mid = math.sqrt(lo * hi)
    ax.barh(i, mid, color=c, height=0.55)
    if hi > lo: ax.plot([lo, hi], [i, i], color=INK, lw=2); ax.plot([lo, lo], [i - .12, i + .12], color=INK, lw=2); ax.plot([hi, hi], [i - .12, i + .12], color=INK, lw=2)
    lab = f"{lo:.3f} kWh" if hi < 0.1 else (f"{lo:.0f}–{hi:.0f} kWh" if hi > lo else f"{lo:.1f} kWh")
    ax.text(hi * 1.25, i, lab, va="center", fontsize=11.5, color=INK)
ax.set_xscale("log"); ax.set_xlim(0.005, 600); ax.set_xticks([0.01, 0.1, 1, 10, 100], ["0.01", "0.1", "1", "10", "100"]); ax.set_yticks(range(len(items)), [n for n, *_ in items]); ax.invert_yaxis()
ax.set_xlabel("Electricity from the wall (kWh, log scale)")
fig.suptitle("One hop costs about a thousand times more energy than the lift itself", x=0.02, ha="left", fontsize=14, color=INK)
fig.tight_layout(); fig.savefig("charts/01_energy_per_hop.png", dpi=200); plt.close(fig)

# 2: tank pressure hop by hop
fig, ax = plt.subplots(figsize=(11, 4.8))
for bg, c in (("2.0", RED), ("3.0", AMB), ("4.0", BLUE)):
    v = R["boost_sweep"][bg]
    for key, ls, lab in (("p_rewarmed", "-", "tank re-warms between hops"), ("p_backtoback", "--", "back-to-back hops (tank cools)")):
        p = [R["tank_pressure_bar"]] + v[key]
        ax.plot(range(len(p)), p, color=c, ls=ls, marker="o", lw=2.4, label=f"{float(bg):.0f} g burns, {lab}")
ax.axhline(20, color=INK, lw=1); ax.text(0.05, 26, "too weak to hop (20 bar)", fontsize=10.5)
ax.set_xticks(range(5)); ax.set_xlabel("Hops completed on one full tank"); ax.set_ylabel("Tank pressure (bar)")
ax.legend(frameon=False, fontsize=9.5, ncol=2, loc="upper right")
fig.suptitle("A full tank buys two to four hops, then hours of refilling", x=0.02, ha="left", fontsize=14, color=INK)
fig.tight_layout(); fig.savefig("charts/02_hops_per_tank.png", dpi=200); plt.close(fig)

# 3: blast wind and noise vs distance
x = np.logspace(math.log10(3), math.log10(400), 200)
u1 = 7.0 * math.sqrt(20e3 / 1.2) / x; u4 = 7.0 * math.sqrt(80e3 / 1.2) / x
fig, ax = plt.subplots(figsize=(11, 5.2))
for lo, hi, lab, c in ((32.7, 400, "Hurricane force (Beaufort 12)", "#fee2e2"), (17.2, 32.7, "Gale to violent storm (Beaufort 8–11)", "#fef3c7")):
    ax.axhspan(lo, hi, color=c, zorder=0); ax.text(3.3, lo * 1.07, lab, ha="left", fontsize=10.5, color=INK)
ax.plot(x, u4, color=RED, lw=2.8, label="All four rear jets merged (80 kN)")
ax.plot(x, u1, color=AMB, lw=2.8, label="One 20 kN jet")
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylim(3, 400); ax.set_xlim(3, 400)
ax.set_xticks([3, 10, 30, 100, 300], ["3 m", "10 m", "30 m", "100 m", "300 m"])
ax.set_yticks([5, 10, 20, 50, 100, 200], ["5", "10", "20", "50", "100", "200"])
ax.set_xlabel("Distance behind the nozzles"); ax.set_ylabel("Wind speed in the blast (m/s)")
ax.legend(frameon=False, loc="upper right")
fig.suptitle("Behind the jets: hurricane-force wind out to about 55 metres", x=0.02, ha="left", fontsize=14, color=INK)
fig.tight_layout(); fig.savefig("charts/03_blast_distance.png", dpi=200); plt.close(fig)
print("ok", hop_lo, hop_hi)
