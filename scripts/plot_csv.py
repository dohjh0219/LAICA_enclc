#!/usr/bin/env python3
"""
Usage:
    python3 plot_csv.py sensors_20260507_161535.csv
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt

if len(sys.argv) < 2:
    print('Usage: python3 plot_csv.py <csv_file>')
    sys.exit(1)

df = pd.read_csv(sys.argv[1])
t = df['elapsed_s']

fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
fig.suptitle(sys.argv[1])

axes[0].plot(t, df['lc_mv'], lw=0.8)
axes[0].set_ylabel('lc_mv [mV]')
axes[0].grid(True)

axes[1].plot(t, df['enc_deg'], lw=0.8, color='tab:orange')
axes[1].set_ylabel('enc_deg [°]')
axes[1].grid(True)

axes[2].plot(t, df['enc_rpm'], lw=0.8, color='tab:green')
axes[2].set_ylabel('enc_rpm')
axes[2].set_xlabel('elapsed [s]')
axes[2].grid(True)

plt.tight_layout()
plt.show()
