import os, glob, subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Renders the newest FAST-LIO map (.pcd) to a 3D + top-down PNG and opens it.
d = os.path.expanduser('~/fastlio_ws/src/FAST_LIO_ROS2/PCD/')
f = max([p for p in glob.glob(d + '*.pcd') if 'backup' not in p], key=os.path.getmtime)
out = f.replace('.pcd', '_3d.png')
assert not os.path.exists(out), 'image already exists: ' + out
raw = open(f, 'rb').read()
i = raw.index(b'DATA ')
j = raw.index(b'\n', i) + 1
h = {l.split()[0]: l.split()[1:] for l in raw[:j].decode().split('\n') if l.strip()}
assert h['DATA'][0] == 'binary', 'not a binary pcd'
assert all(c == '1' for c in h['COUNT']), 'unexpected COUNT'
m = {('F', 4): '<f4', ('F', 8): '<f8', ('U', 1): 'u1', ('U', 2): '<u2', ('U', 4): '<u4',
     ('I', 1): 'i1', ('I', 2): '<i2', ('I', 4): '<i4'}
dt = np.dtype([(n, m[(t, int(s))]) for n, t, s in zip(h['FIELDS'], h['TYPE'], h['SIZE'])])
a = np.frombuffer(raw[j:], dtype=dt, count=int(h['POINTS'][0]))
x, y, z = a['x'].astype(float), a['y'].astype(float), a['z'].astype(float)
ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
x, y, z = x[ok], y[ok], z[ok]
print('points:', len(x), ' x %.1f..%.1f  y %.1f..%.1f  z %.1f..%.1f' % (x.min(), x.max(), y.min(), y.max(), z.min(), z.max()))
k = np.random.default_rng(0).choice(len(x), min(len(x), 120000), replace=False)
fig = plt.figure(figsize=(15, 7))
ax = fig.add_subplot(121, projection='3d')
ax.scatter(x[k], y[k], z[k], c=z[k], s=0.4, cmap='viridis')
ax.set_xlabel('x (m)')
ax.set_ylabel('y (m)')
ax.set_zlabel('z (m)')
ax.set_title('3D map (FAST-LIO frame)')
ax2 = fig.add_subplot(122)
sc = ax2.scatter(x[k], y[k], c=z[k], s=0.4, cmap='viridis')
ax2.set_aspect('equal')
ax2.set_xlabel('x (m)')
ax2.set_ylabel('y (m)')
ax2.set_title('Top-down view')
fig.colorbar(sc, ax=ax2, label='height z (m)')
fig.savefig(out, dpi=150, bbox_inches='tight')
print('saved', out)
subprocess.Popen(['xdg-open', out])
