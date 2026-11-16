# Brick builder: Roblox-style pets made of (optionally rotated) studded blocks, tagged by bone for animation.
# Authoring: Blender Z up, model faces +Y, ground z=0, units = studs.
# Export to Roblox: position (x, z, -y), rotation C*R*C^T with C = [[1,0,0],[0,0,1],[0,-1,0]], size (sx, sz, sy).
import math

MODELS = []


def euler(rot):
    if not rot:
        return [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
    x, y, z = (math.radians(a) for a in rot)
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    # Blender XYZ euler: R = Rz * Ry * Rx
    return [[cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx],
            [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx],
            [-sy, cy * sx, cy * cx]]


def to_roblox(R):
    C = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]
    CT = [[C[j][i] for j in range(3)] for i in range(3)]
    mul = lambda A, B: [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return mul(mul(C, R), CT)


class Brick:
    def __init__(self, name, group):
        self.name, self.group = name, group
        self.boxes = []
        self.pivots = {}
        MODELS.append(self)

    def b(self, size, pos, color, bone="body", rot=None, kind="plastic"):
        self.boxes.append(dict(size=size, pos=pos, color=color, bone=bone, rot=rot, kind=kind))
        return self

    def m(self, size, pos, color, bone="body", rot=None, kind="plastic"):
        """Mirrored pair across X (bone suffix L/R swapped, Y/Z rotation mirrored)."""
        x, y, z = pos
        self.b(size, (x, y, z), color, bone, rot, kind)
        mb = bone[:-1] + {"L": "R", "R": "L"}[bone[-1]] if bone[-1:] in ("L", "R") else bone
        mr = (rot[0], -rot[1], -rot[2]) if rot else None
        return self.b(size, (-x, y, z), color, mb, mr, kind)

    def blob(self, c, r, color, bone="body", slices=4, kind="plastic"):
        """Rounded voxel ellipsoid: stacked slices, each a cross of two boxes (octagon section) shrinking toward the poles."""
        cx, cy, cz = c
        rx, ry, rz = r
        h = 2 * rz / slices
        for i in range(slices):
            zm = -rz + h * (i + 0.5)
            f = math.sqrt(max(0.0, 1 - (zm / rz) ** 2))
            self.b((2 * rx * f, 2 * ry * f * 0.72, h), (cx, cy, cz + zm), color, bone, kind=kind)
            self.b((2 * rx * f * 0.72, 2 * ry * f, h), (cx, cy, cz + zm), color, bone, kind=kind)
        return self

    def limb(self, p0, p1, w0, w1, color, bone="body", kind="plastic", mirror=False):
        """Box(es) from p0 to p1 (long axis = local Y), tapering from width w0 to w1 in two steps."""
        d = [p1[k] - p0[k] for k in range(3)]
        L = math.sqrt(sum(v * v for v in d)) or 1e-3
        rot = (math.degrees(math.atan2(d[2], math.hypot(d[0], d[1]))), 0, math.degrees(math.atan2(-d[0], d[1])))
        put = self.m if mirror else self.b
        if abs(w0 - w1) < 1e-6:
            return put((w0, L, w0), tuple((p0[k] + p1[k]) / 2 for k in range(3)), color, bone, rot, kind)
        for t0, w in ((0.0, w0), (0.5, w1)):
            mid = [p0[k] + d[k] * (t0 + 0.25) for k in range(3)]
            put((w, L * 0.55, w), tuple(mid), color, bone, rot, kind)
        return self

    def pivot(self, bone, pos):
        self.pivots[bone] = pos
        return self

    def eyes(self, x, y, z, w=0.13, h=0.17, color="141418", bone="head", hi=True, glow=False):
        """Small square eyes on a front face at y, with a tiny highlight."""
        k = "neon" if glow else "plastic"
        self.m((w, 0.06, h), (x, y, z), color, bone + "R" if False else bone, kind=k)
        if hi:
            self.m((w * 0.4, 0.07, h * 0.35), (x - w * 0.15, y + 0.01, z + h * 0.22), "FFFFFF", bone, kind="neon")
        return self

    def export(self):
        out = []
        for bx in self.boxes:
            sx, sy, sz = bx["size"]
            x, y, z = bx["pos"]
            R = to_roblox(euler(bx["rot"]))
            out.append(dict(s=[round(sx, 3), round(sz, 3), round(sy, 3)], p=[round(x, 3), round(z, 3), round(-y, 3)],
                            r=[round(v, 5) for row in R for v in row], c=bx["color"], m=bx["kind"], b=bx["bone"]))
        piv = {k: [round(v[0], 3), round(v[2], 3), round(-v[1], 3)] for k, v in self.pivots.items()}
        return dict(boxes=out, pivots=piv, group=self.group)


def roundify(a, minsize=0.55):
    """Turn every big unrotated plastic block (heads, bodies, thick limbs) into a rounded voxel blob of the same extents.
    Thin parts (eyes, ears, stripes, blob slices) stay as they are, so running it twice changes nothing."""
    old, a.boxes = a.boxes, []
    for bx in old:
        sx, sy, sz = bx["size"]
        if bx["rot"] is None and bx["kind"] == "plastic" and min(sx, sy, sz) >= minsize:
            a.blob(bx["pos"], (sx * 0.55, sy * 0.55, sz * 0.53), bx["color"], bx["bone"], slices=max(2, min(5, round(sz / 0.3))))
        else:
            a.boxes.append(bx)
    return a


def legs4(a, hipz, x, yf, yb, w, color, hoof=None, hoofh=0.22, bones=True, legh=None):
    """Four straight legs from hip height to ground; bones legFL.. pivot at the hip."""
    for fb, y in (("F", yf), ("B", yb)):
        for side, sx in (("L", -1), ("R", 1)):
            bone = f"leg{fb}{side}"
            top = hipz
            a.b((w, w, top - hoofh), (sx * x, y, hoofh + (top - hoofh) / 2), color, bone)
            if hoof:
                a.b((w * 1.08, w * 1.12, hoofh), (sx * x, y + 0.02, hoofh / 2), hoof, bone)
            else:
                a.b((w, w, hoofh), (sx * x, y, hoofh / 2), color, bone)
            a.pivot(bone, (sx * x, y, top))
