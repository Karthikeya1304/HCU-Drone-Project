import os, re, glob
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Plots the flown path from the newest ~/avoid8_*.log and saves a PNG next to it.
log = max(glob.glob(os.path.expanduser('~/avoid8_*.log')), key=os.path.getmtime)
out = log.replace('.log', '_path.png')
assert not os.path.exists(out), 'image already exists: ' + out
pts = [tuple(map(float, m.groups())) for m in
       (re.search(r'pos=\(([-\d.]+), ([-\d.]+), ([-\d.]+)\)', l) for l in open(log) if 'phase' in l) if m]
assert pts, 'no position lines in ' + log
n = [p[0] for p in pts]
e = [p[1] for p in pts]
plt.figure(figsize=(7, 7))
plt.plot(e, n, '-', lw=1.5, label='flight path')
plt.plot(e[0], n[0], 'go', label='start')
plt.plot(e[-1], n[-1], 'rs', label='end')
plt.plot(-6, -1.75, 'k^', ms=10, label='test box')
plt.xlabel('East (m)')
plt.ylabel('North (m)')
plt.axis('equal')
plt.grid(True)
plt.legend()
plt.title(os.path.basename(log))
plt.savefig(out, dpi=150, bbox_inches='tight')
print('saved', out)
