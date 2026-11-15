# Generates assets/studs.png: one tileable grey stud (multiplied by part color in Blender and Roblox).
import math, os, struct, zlib

N = 256
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "studs.png")


def shade(x, y):
    """Classic Roblox stud: raised rounded square, lit from top-left, on a flat tile."""
    u, v = (x + 0.5) / N - 0.5, (y + 0.5) / N - 0.5  # -0.5..0.5, y down
    H, RAD, BEV = 0.31, 0.09, 0.05  # half size, corner radius, bevel width

    def sdf(px, py):  # signed distance to rounded square
        qx, qy = abs(px) - (H - RAD), abs(py) - (H - RAD)
        return math.hypot(max(qx, 0), max(qy, 0)) + min(max(qx, qy), 0) - RAD

    val = 0.88
    edge = max(abs(u), abs(v))
    if edge > 0.488:
        val = 0.80  # tile seam
    elif edge > 0.474:
        val = 0.93
    if sdf(u - 0.03, v - 0.035) < 0 and sdf(u, v) >= 0:
        val = 0.74  # drop shadow bottom-right
    d = sdf(u, v)
    if d < 0:
        if d > -BEV:
            # bevel: brightness from which side we're on (top/left lit)
            nx = (abs(u) > abs(v)) * (1 if u > 0 else -1)
            ny = (abs(v) >= abs(u)) * (1 if v > 0 else -1)
            lit = -(nx + ny)  # +1 top/left, -1 bottom/right
            val = 0.90 + 0.10 * lit if lit > 0 else 0.90 + 0.18 * lit
        else:
            val = 0.95
    return max(0, min(1, val))


def write_png(path, pixels):
    raw = b"".join(b"\x00" + bytes(row) for row in pixels)
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", N, N, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


# 2x2 supersampling for smooth edges
rows = []
for y in range(N):
    row = []
    for x in range(N):
        s = sum(shade(x + dx, y + dy) for dx in (-0.25, 0.25) for dy in (-0.25, 0.25)) / 4
        c = int((1 - (1 - s) * 0.5) * 255)  # soft, low-contrast studs like classic Roblox pets
        row += [c, c, c]
    rows.append(row)
write_png(OUT, rows)
assert open(OUT, "rb").read(8) == b"\x89PNG\r\n\x1a\n"
print("wrote", os.path.abspath(OUT))
