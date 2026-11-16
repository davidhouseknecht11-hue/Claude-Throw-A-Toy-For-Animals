# World 2: the 12 new zones' animals, their Secrets, the 36 extra Secrets, 11 new toys and the extra cinematic FX.
# Exec'd at the end of pets.py, so it shares Brick, variant, legs4, eyes, wings, halo, stars, ball, INK, HI.
# Generic brick builders keep ~100 models consistent: quad / biped / bird / fish / serpent + a few one-offs.
import math as _w2


def _ears(a, kind, x, y, z, c, inner=None):
    if kind == "point":
        a.m((0.2, 0.12, 0.32), (x, y, z), c, "earR")
        if inner:
            a.m((0.1, 0.04, 0.18), (x, y + 0.07, z - 0.02), inner, "earR")
    elif kind == "round":
        a.m((0.28, 0.1, 0.26), (x, y, z), c, "earR")
    elif kind == "long":
        a.m((0.16, 0.1, 0.7), (x, y, z + 0.18), c, "earR")
    elif kind == "big":
        a.m((0.32, 0.1, 0.5), (x + 0.05, y, z + 0.1), c, "earR", rot=(0, -12, 0))
        if inner:
            a.m((0.18, 0.04, 0.32), (x + 0.05, y + 0.06, z + 0.08), inner, "earR", rot=(0, -12, 0))
    else:
        return
    a.pivot("earR", (x, y, z - 0.12)).pivot("earL", (-x, y, z - 0.12))


def quad(name, group, body, belly=None, *, L=1.6, W=0.9, H=0.8, hip=0.6, head=0.75, snout=None, ear="point", tail="thin",
         leg=None, hoof=None, eye=INK, glow_eyes=False, inner=None):
    """Four-legged animal. Returns (brick, info) where info has the head centre / top for accessories."""
    a = Brick(name, group)
    bz = hip + H / 2
    a.b((W, L, H), (0, 0, bz), body)
    if belly:
        a.b((W * 0.7, L * 0.7, 0.08), (0, 0.05, hip - 0.02), belly)
        a.b((W * 0.62, 0.08, H * 0.6), (0, L / 2 + 0.03, bz - H * 0.1), belly)
    legs4(a, hip, W * 0.33, L * 0.34, -L * 0.34, min(0.34, W * 0.36), leg or body, hoof)
    hy, hz = L / 2 + head * 0.25, hip + H + head * 0.2
    a.b((head, head * 0.9, head * 0.85), (0, hy, hz), body, "head").pivot("head", (0, L / 2 - 0.1, hip + H * 0.75))
    front = hy + head * 0.45
    if snout:
        a.b((head * 0.55, head * 0.42, head * 0.38), (0, front + head * 0.18, hz - head * 0.18), snout, "head")
        a.b((head * 0.18, 0.06, head * 0.12), (0, front + head * 0.4, hz - head * 0.06), INK, "head")
    eyes(a, head * 0.24, front, hz + head * 0.1, w=0.11, h=0.14, color=eye, glow=glow_eyes)
    _ears(a, ear, head * 0.3, hy - head * 0.05, hz + head * 0.5, body, inner)
    ty, tz = -L / 2, hip + H * 0.8
    if tail == "thin":
        a.b((0.12, 0.8, 0.12), (0, ty - 0.35, tz + 0.15), body, "tail", rot=(-30, 0, 0))
    elif tail == "fluffy":
        a.b((0.36, 0.9, 0.36), (0, ty - 0.4, tz + 0.15), body, "tail", rot=(-25, 0, 0))
    elif tail == "stub":
        a.b((0.3, 0.3, 0.3), (0, ty - 0.1, tz), body, "tail")
    elif tail == "long":
        a.b((0.4, 1.4, 0.3), (0, ty - 0.65, tz - 0.25), body, "tail", rot=(10, 0, 0))
    if tail:
        a.pivot("tail", (0, ty, tz))
    return a, dict(hy=hy, hz=hz, head=head, top=hz + head * 0.42, front=front, L=L, W=W, H=H, hip=hip, bz=bz)


def biped(name, group, body, belly=None, *, H=1.0, W=0.9, head=0.8, leg=0.45, arms=True, eye=INK, glow_eyes=False, ear="round", tail=None):
    """Upright animal (meerkat, T-Rex, teddy, robot): legs, body, arms, big head."""
    a = Brick(name, group)
    bz = leg + H / 2
    a.b((W, W * 0.8, H), (0, 0, bz), body)
    if belly:
        a.b((W * 0.6, 0.08, H * 0.7), (0, W * 0.41, bz - 0.05), belly)
    a.m((W * 0.32, W * 0.4, leg), (W * 0.24, 0.05, leg / 2), body, "legFR").pivot("legFR", (W * 0.24, 0.05, leg)).pivot("legFL", (-W * 0.24, 0.05, leg))
    a.m((W * 0.34, W * 0.5, 0.12), (W * 0.24, 0.12, 0.06), belly or body, "legFR")
    if arms:
        a.m((0.24, 0.24, H * 0.6), (W / 2 + 0.12, 0.05, bz + H * 0.05), body, "armR").pivot("armR", (W / 2, 0.05, bz + H * 0.3)).pivot("armL", (-W / 2, 0.05, bz + H * 0.3))
    hz = leg + H + head * 0.45
    a.b((head, head * 0.85, head * 0.85), (0, 0.05, hz), body, "head").pivot("head", (0, 0, leg + H))
    front = 0.05 + head * 0.43
    eyes(a, head * 0.24, front, hz + head * 0.08, w=0.12, h=0.15, color=eye, glow=glow_eyes)
    _ears(a, ear, head * 0.32, 0.05, hz + head * 0.48, body)
    if tail:
        a.b((0.3, 1.1, 0.3), (0, -W * 0.4 - 0.5, leg + 0.2), body, "tail", rot=(15, 0, 0)).pivot("tail", (0, -W * 0.4, leg + 0.4))
    return a, dict(hz=hz, head=head, top=hz + head * 0.43, front=front, H=H, W=W, leg=leg, bz=bz)


def bird(name, group, body, wing, beak="FFC21C", *, s=1.0, belly=None, legs="FFC21C", tail=True, eye=INK, glow_eyes=False, neck=0.0):
    """Bird / bat / flier: body, head, beak, flapping wings, tail, thin legs."""
    a = Brick(name, group)
    a.b((0.8 * s, 1.0 * s, 0.8 * s), (0, 0, 0.9 * s + 0.4), body)
    if belly:
        a.b((0.6 * s, 0.1, 0.6 * s), (0, 0.51 * s, 0.85 * s + 0.4), belly)
    hz = 1.55 * s + 0.4 + neck
    if neck:
        a.b((0.3 * s, 0.3 * s, neck + 0.3), (0, 0.3 * s, 1.2 * s + 0.4 + neck / 2), body, "head")
    a.b((0.62 * s, 0.6 * s, 0.56 * s), (0, 0.35 * s, hz), body, "head").pivot("head", (0, 0.25 * s, hz - 0.3 * s))
    a.b((0.22 * s, 0.34 * s, 0.16 * s), (0, 0.8 * s, hz - 0.06 * s), beak, "head")
    eyes(a, 0.16 * s, 0.66 * s, hz + 0.08 * s, w=0.1 * s, h=0.12 * s, color=eye, glow=glow_eyes)
    a.m((1.0 * s, 0.5 * s, 0.12), (0.85 * s, -0.05, 0.95 * s + 0.4), wing, "wingR", rot=(0, -20, 0))
    a.m((0.8 * s, 0.42 * s, 0.1), (1.6 * s, -0.1, 1.25 * s + 0.4), wing, "wingR", rot=(0, -32, 0))
    a.pivot("wingR", (0.38 * s, 0, 1.0 * s + 0.4)).pivot("wingL", (-0.38 * s, 0, 1.0 * s + 0.4))
    if tail:
        a.b((0.4 * s, 0.8 * s, 0.1), (0, -0.85 * s, 0.75 * s + 0.4), wing, "tail", rot=(-20, 0, 0)).pivot("tail", (0, -0.45 * s, 0.85 * s + 0.4))
    if legs:
        a.m((0.08, 0.08, 0.5 + 0.4 * s), (0.16 * s, 0.05, (0.5 + 0.4 * s) / 2), legs, "legFR")
        a.m((0.22, 0.3, 0.05), (0.16 * s, 0.15, 0.025), legs, "legFR").pivot("legFR", (0.16 * s, 0.05, 0.9)).pivot("legFL", (-0.16 * s, 0.05, 0.9))
    return a, dict(hz=hz, top=hz + 0.28 * s, s=s)


def fish(name, group, body, fin, *, L=1.8, H=0.9, W=0.6, z=1.4, belly=None, eye=INK, glow_eyes=False, dorsal=True, tailw=1.0):
    """Swimmer that floats above the ground: body, head, tail fin (wags), side fins (flap), dorsal fin."""
    a = Brick(name, group)
    a.b((W, L, H), (0, 0, z), body)
    if belly:
        a.b((W * 0.8, L * 0.8, 0.1), (0, 0.05, z - H / 2), belly)
    a.b((W * 0.85, L * 0.35, H * 0.85), (0, L / 2 + L * 0.15, z - 0.02), body, "head").pivot("head", (0, L / 2, z))
    a.m((0.06, 0.16, 0.16), (W * 0.43 + 0.01, L / 2 + L * 0.2, z + H * 0.15), "FFFFFF", "head")
    a.m((0.07, 0.09, 0.1), (W * 0.43 + 0.02, L / 2 + L * 0.24, z + H * 0.15), eye, "head", kind="neon" if glow_eyes else "plastic")
    a.b((W * 0.4, L * 0.35, H * 0.6), (0, -L / 2 - L * 0.12, z), body, "tail").pivot("tail", (0, -L / 2, z))
    a.b((0.12, L * 0.3, H * 1.3 * tailw), (0, -L / 2 - L * 0.38, z), fin, "tail")
    a.m((0.5, L * 0.25, 0.08), (W / 2 + 0.22, L * 0.1, z - H * 0.2), fin, "wingR", rot=(0, -20, 0)).pivot("wingR", (W / 2, L * 0.1, z)).pivot("wingL", (-W / 2, L * 0.1, z))
    if dorsal:
        a.b((0.1, L * 0.35, H * 0.5), (0, -L * 0.05, z + H / 2 + H * 0.2), fin, rot=(-15, 0, 0))
    return a, dict(z=z, L=L, H=H, W=W, top=z + H / 2)


def serpent(name, group, c1, c2, *, segs=7, r=0.5, z=0.9, eye=INK, glow_eyes=False, wave=0.5):
    """Long snake / serpent: big head, a wavy chain of body segments (the back half wags as the tail)."""
    a = Brick(name, group)
    for i in range(segs):
        y = -i * r * 1.25
        zz = z + _w2.sin(i * 0.9) * wave * r
        s = r * (1.0 - i * 0.06)
        bone = "tail" if i >= segs // 2 else "body"
        a.b((s * 1.6, r * 1.4, s * 1.6), (0, y, zz), c1 if i % 2 == 0 else c2, bone)
    a.pivot("tail", (0, -(segs // 2) * r * 1.25 + r * 0.6, z))
    hz = z + r * 0.3
    a.b((r * 2.0, r * 1.8, r * 1.5), (0, r * 1.5, hz), c1, "head").pivot("head", (0, r * 0.6, z))
    a.b((r * 1.6, r * 0.8, r * 0.7), (0, r * 2.6, hz - r * 0.3), c2, "head")
    eyes(a, r * 0.55, r * 2.4, hz + r * 0.45, w=0.14, h=0.16, color=eye, glow=glow_eyes)
    return a, dict(hz=hz, top=hz + r * 0.75, r=r)


def horn(a, x, y, z, c, h=0.5, tilt=20, bone="head"):
    a.m((0.14, 0.14, h), (x, y, z + h / 2), c, bone, rot=(tilt, 0, -15))


def crown(a, y, z, gem="FF3B6B", w=0.6, bone="head"):
    a.b((w, w, 0.14), (0, y, z), "FFC21C", bone)
    for x, yy in ((-w * 0.36, w * 0.36), (w * 0.36, w * 0.36), (-w * 0.36, -w * 0.36), (w * 0.36, -w * 0.36)):
        a.b((0.12, 0.12, 0.22), (x, y + yy, z + 0.16), "FFC21C", bone)
    a.b((0.1, 0.06, 0.1), (0, y + w / 2 + 0.02, z + 0.02), gem, bone, kind="neon")


def flames(a, x, y, z, c1="FF5A1C", c2="FFD23C", bone="body", s=1.0):
    a.b((0.28 * s, 0.28 * s, 0.4 * s), (x, y, z + 0.2 * s), c1, bone, kind="neon").b((0.16 * s, 0.16 * s, 0.26 * s), (x, y, z + 0.5 * s), c2, bone, kind="neon")


def multi_tail(a, n, c, tip, spread=110, base=(0, -0.7, 1.0), length=0.9):
    """n fanned tails (kitsune) on the tail bone, tips glowing."""
    a.pivot("tail", base)
    for i in range(n):
        ang = -spread / 2 + spread * i / max(n - 1, 1)
        rz = _w2.radians(ang)
        x, y = _w2.sin(rz) * length * 0.5, -_w2.cos(rz) * length * 0.5
        a.b((0.3, length, 0.3), (base[0] + x, base[1] + y, base[2] + 0.35), c, "tail", rot=(-35, 0, ang))
        a.b((0.32, 0.3, 0.32), (base[0] + x * 2.0, base[1] + y * 2.0, base[2] + 0.7), tip, "tail", rot=(-35, 0, ang), kind="neon")


# ====================================================================== REGULAR ANIMALS (12 zones)
# Dinosaur Island
a, i = biped("Raptor", "World2", "6FA84A", "D8E8A0", H=0.8, W=0.7, head=0.7, leg=0.55, ear=None, tail=True)
a.b((0.5, 0.5, 0.3), (0, 0.55, i["hz"] - 0.1), "6FA84A", "head").b((0.4, 0.1, 0.06), (0, 0.8, i["hz"] - 0.2), "FFFFFF", "head")
for k in range(3):
    a.b((0.1, 0.25, 0.14), (0, -0.2 - k * 0.25, 0.55 + 0.85), "D8582A")
a, i = quad("Triceratops", "World2", "5A8AC8", "B8D0F0", L=1.9, W=1.1, H=0.95, hip=0.55, head=0.9, ear=None, tail="long")
a.b((1.5, 0.12, 0.95), (0, i["hy"] - 0.25, i["hz"] + 0.35), "E0C080", "head", rot=(-25, 0, 0))
horn(a, 0.25, i["front"], i["hz"] + 0.3, "FFF6EA", 0.6, 40)
a.b((0.14, 0.14, 0.35), (0, i["front"] + 0.15, i["hz"] - 0.05), "FFF6EA", "head", rot=(40, 0, 0))
a, i = bird("Pterodactyl", "World2", "B87A4A", "8A5A32", "E0B060", s=1.0, legs="8A5A32", tail=False)
a.b((0.18, 0.7, 0.18), (0, -0.05, i["hz"] + 0.25), "B87A4A", "head", rot=(30, 0, 0))
a, i = biped("T-Rex", "World2", "3E8A3A", "C8E0A0", H=1.4, W=1.2, head=1.2, leg=0.75, ear=None, tail=True, arms=True)
a.b((1.0, 0.7, 0.5), (0, 0.85, i["hz"] - 0.25), "3E8A3A", "head")
for x in (-0.3, -0.1, 0.1, 0.3):
    a.b((0.08, 0.08, 0.14), (x, 1.15, i["hz"] - 0.42), "FFFFFF", "head")
# Lost Desert
a, i = biped("Meerkat", "World2", "C8A06A", "F0DCB0", H=1.1, W=0.6, head=0.55, leg=0.4, ear="round", tail=True)
a.b((0.2, 0.25, 0.25), (0, 0.38, i["hz"] - 0.05), "8A6A40", "head")
a, i = quad("Camel", "World2", "D8B070", "F0DCB0", L=1.9, W=0.95, H=0.9, hip=1.0, head=0.65, snout="E8C890", ear="round", tail="thin")
a.b((0.7, 0.6, 0.55), (0, -0.25, i["bz"] + 0.65), "C89A58").b((0.3, 0.32, 0.7), (0, 0.95, i["bz"] + 0.6), "D8B070")
a, i = quad("Fennec Fox", "World2", "F0D2A0", "FFF6EA", L=1.3, W=0.7, H=0.6, hip=0.55, head=0.65, snout="FFF6EA", ear="big", tail="fluffy", inner="FFB8C0")
a, i = quad("Scorpion", "World2", "B8642A", None, L=1.4, W=1.0, H=0.4, hip=0.3, head=0.6, ear=None, tail=None)
for k in range(5):
    a.b((0.32, 0.4, 0.32), (0, -0.85 - k * 0.12, 0.6 + k * 0.38), "C87430" if k % 2 else "B8642A", "tail", rot=(-35 + k * 25, 0, 0))
a.b((0.2, 0.2, 0.35), (0, -0.95, 2.35), "FF5A1C", "tail", rot=(120, 0, 0), kind="neon").pivot("tail", (0, -0.7, 0.5))
a.m((0.35, 0.6, 0.25), (0.6, 1.0, 0.45), "C87430", "armR").m((0.15, 0.35, 0.15), (0.72, 1.35, 0.5), "B8642A", "armR")
a.pivot("armR", (0.45, 0.6, 0.45)).pivot("armL", (-0.45, 0.6, 0.45))
# Sakura Gardens
a, i = fish("Koi Fish", "World2", "FFFFFF", "FF7A3C", L=1.6, H=0.8, W=0.6, z=1.2)
for x, y in ((0.31, 0.3), (-0.31, -0.2), (0.31, -0.5)):
    a.b((0.02, 0.5, 0.4), (x, y, 1.3), "FF5A2A")
a.b((0.4, 0.5, 0.05), (0, 0.1, 1.61), "FF5A2A")
a, i = quad("Red Panda", "World2", "C8502A", "2A1A14", L=1.4, W=0.8, H=0.65, hip=0.45, head=0.75, snout="FFF6EA", ear="point", tail="fluffy", leg="2A1A14", inner="FFF6EA")
for k in range(3):
    a.b((0.38, 0.12, 0.38), (0, -1.0 - k * 0.22, 0.75 + k * 0.08), "FFF6EA", "tail", rot=(-25, 0, 0))
a.m((0.2, 0.05, 0.16), (0.22, i["front"] + 0.01, i["hz"] - 0.12), "FFF6EA", "head")
a, i = bird("Crane", "World2", "FFFFFF", "FFFFFF", "3A3A42", s=1.0, legs="3A3A42", neck=0.7)
a.b((0.28, 0.28, 0.08), (0, 0.35, i["hz"] + 0.3), "E23B3B", "head")
a.m((0.5, 0.3, 0.12), (1.7, -0.2, 1.65), "1C1C22", "wingR", rot=(0, -32, 0))
a = variant("Fox", "Sakura Fox", {"F07A26": "FF9AC8", "FFF6EA": "FFF0F6", "2A1D18": "C85A8A"})
a.group = "World2"
stars(a, ((0.41, 0.2, 1.1), (-0.41, -0.3, 1.2)), "FFD0E8", 0.12)
# Lost Atlantis
a = Brick("Seahorse", "World2")
O, Y = "FF9A2A", "FFE36A"
for k, (y, z, s) in enumerate(((0, 1.8, 0.6), (-0.1, 1.3, 0.55), (-0.05, 0.85, 0.48), (0.1, 0.5, 0.38), (0.25, 0.3, 0.3))):
    a.b((s, s, s * 1.1), (0, y, z), O if k % 2 == 0 else Y, "tail" if k >= 3 else "body")
a.b((0.4, 0.15, 0.3), (0, 0.25, 0.15), O, "tail", rot=(0, 0, 0)).pivot("tail", (0, 0, 0.8))
a.b((0.5, 0.55, 0.5), (0, 0.15, 2.3), O, "head").b((0.2, 0.5, 0.2), (0, 0.55, 2.22), Y, "head").pivot("head", (0, 0, 2.05))
eyes(a, 0.15, 0.4, 2.38, w=0.1, h=0.12)
a.b((0.08, 0.5, 0.5), (0, -0.35, 1.6), Y, kind="neon")
a, i = fish("Dolphin", "World2", "6A9ACA", "4A7AAA", L=2.2, H=0.8, W=0.7, z=1.3, belly="E8F0FF")
a.b((0.25, 0.5, 0.2), (0, 1.75, 1.15), "6A9ACA", "head")
a, i = fish("Shark", "World2", "7A8A9A", "5A6A7A", L=2.4, H=1.0, W=0.8, z=1.4, belly="F0F4F8", tailw=1.4)
for x in (-0.2, 0, 0.2):
    a.b((0.08, 0.06, 0.12), (x, 1.98, 1.12), "FFFFFF", "head")
a, i = serpent("Sea Snake", "World2", "2AB0A8", "1A7A8A", segs=7, r=0.45, z=0.8)
# Sky Kingdom
a = variant("Hamster", "Flying Squirrel", {"E8B465": "9A7A5A", "FFF3E0": "F0E0C8", "D4893A": "6A4A32"})
a.group = "World2"
a.m((0.7, 0.8, 0.06), (0.75, 0, 0.45), "C8A880", "armR", rot=(0, -10, 0)).pivot("armR", (0.5, 0, 0.5)).pivot("armL", (-0.5, 0, 0.5))
a, i = bird("Owl", "World2", "8A6A4A", "6A4A32", "FFC21C", s=1.0, belly="E0C8A0", legs="FFC21C")
a.m((0.14, 0.14, 0.3), (0.22, 0.3, i["hz"] + 0.38), "6A4A32", "head", rot=(0, -20, 0))
a.m((0.22, 0.06, 0.22), (0.15, 0.66, i["hz"] + 0.08), "FFD23C", "head")
a, i = bird("Eagle", "World2", "6A4A2A", "4A321C", "FFC21C", s=1.15, belly="8A6A4A", legs="FFC21C")
a.b((0.66, 0.62, 0.3), (0, 0.4, i["hz"] + 0.18), "FFFFFF", "head")
a = variant("Zebra", "Pegasus", {"222228": "F0F4FF", "3A3A42": "C8D0E0"})
a.group = "World2"
wings(a, 0.52, 0.2, 1.8, "FFFFFF", "C8E8FF", 1.3)
# Halloween Town
a, i = bird("Bat", "World2", "2A2236", "3A2A55", "2A2236", s=0.8, legs=None, tail=False, eye="FF3B3B", glow_eyes=True)
a.m((0.14, 0.12, 0.3), (0.16, 0.3, i["hz"] + 0.32), "2A2236", "head")
a = variant("Cat", "Black Cat", {"E8A055": "1C1C22", "C27532": "2A2A30", "F8EEDD": "3A3A42", "2E6B1E": ("FFD23C", "neon"), "F7B2C2": "5A3A4A"})
a.group = "World2"
a = variant("Dog", "Zombie Dog", {"D8A266": "7AA06A", "F3E1C4": "A8C090", "C08548": "5A7A4A", "8A5A32": "4A5A3A", "D6383A": "6A3A2A"})
a.group = "World2"
a.b((0.3, 0.06, 0.06), (0.3, 0.35, 1.3), "3A2A1A", rot=(0, 30, 0)).b((0.06, 0.06, 0.3), (-0.2, 0.84, 1.1), "3A2A1A")
a = Brick("Ghost", "World2")
a.b((1.1, 1.0, 1.3), (0, 0, 1.9), "F4F8FF", kind="glass").b((1.2, 1.1, 0.9), (0, 0, 1.0), "F4F8FF", kind="glass")
for k, x in enumerate((-0.4, 0, 0.4)):
    a.b((0.3, 1.0, 0.4), (x, 0, 0.45 - 0.1 * (k % 2)), "E8F0FF", "tail", kind="glass")
a.pivot("tail", (0, 0, 0.8))
a.m((0.16, 0.06, 0.24), (0.22, 0.51, 2.0), "141418").b((0.3, 0.06, 0.2), (0, 0.51, 1.6), "141418")
a.m((0.3, 0.3, 0.5), (0.7, 0.2, 1.4), "F4F8FF", "armR", kind="glass").pivot("armR", (0.55, 0.1, 1.6)).pivot("armL", (-0.55, 0.1, 1.6))
# Tropical Paradise
a = Brick("Crab", "World2")
a.b((1.2, 0.9, 0.5), (0, 0, 0.55), "E8401C").b((1.0, 0.7, 0.2), (0, 0, 0.88), "FF6A3C")
for x in (0.25, -0.25):
    a.b((0.1, 0.1, 0.35), (x, 0.35, 1.05), "E8401C", "head").b((0.18, 0.18, 0.18), (x, 0.35, 1.28), "FFFFFF", "head").b((0.1, 0.06, 0.1), (x, 0.44, 1.3), INK, "head")
a.pivot("head", (0, 0.35, 0.9))
for k in range(3):
    a.m((0.5, 0.12, 0.12), (0.75, 0.2 - k * 0.25, 0.3), "C8301C", "legBR" if k else "legFR", rot=(0, 30, 0))
a.pivot("legBR", (0.55, 0, 0.4)).pivot("legBL", (-0.55, 0, 0.4)).pivot("legFR", (0.55, 0.2, 0.4)).pivot("legFL", (-0.55, 0.2, 0.4))
a.m((0.4, 0.5, 0.35), (0.85, 0.65, 0.6), "FF5A2A", "armR").m((0.18, 0.3, 0.12), (0.92, 0.95, 0.7), "C8301C", "armR")
a.pivot("armR", (0.6, 0.4, 0.55)).pivot("armL", (-0.6, 0.4, 0.55))
a, i = bird("Flamingo", "World2", "FF8AB8", "FF6AA0", "1C1C22", s=1.0, legs="FF6AA0", neck=0.8)
a, i = bird("Toucan", "World2", "1C1C22", "2A2A30", "FF9A2A", s=1.0, belly="FFE36A", legs="4CB4FF")
a.b((0.28, 0.6, 0.3), (0, 0.95, i["hz"] - 0.02), "FF9A2A", "head").b((0.3, 0.2, 0.32), (0, 1.25, i["hz"] - 0.02), "E8401C", "head")
a, i = biped("Sea Lion", "World2", "6A5A4A", "8A7A6A", H=1.0, W=0.9, head=0.7, leg=0.2, ear=None, arms=True)
a.b((0.4, 0.3, 0.25), (0, 0.45, i["hz"] - 0.15), "8A7A6A", "head").m((0.2, 0.05, 0.05), (0.18, 0.62, i["hz"] - 0.1), "E8E0D0", "head")
# Toy Factory
a = variant("Hamster", "Wind-Up Mouse", {"E8B465": "9AA4B2", "FFF3E0": "C8D0DC", "D4893A": "6A7080", "F7B6C8": "FF8AB8"})
a.group = "World2"
a.b((0.08, 0.4, 0.08), (0, -0.7, 0.6), "FFC21C", "tail").b((0.4, 0.06, 0.25), (0, -0.92, 0.6), "FFC21C", "tail").pivot("tail", (0, -0.55, 0.6))
a = variant("Polar Bear", "Plush Bear", {"F4F8FB": "C89A6A", "DCE6EE": "F0D8B8", "1C1C22": "5A3A2A", "3E7BFA": "FF8AB8"})
a.group = "World2"
a.b((0.6, 0.08, 0.6), (0, 0.85, 1.25), "FF6AA0").b((0.04, 0.1, 0.5), (0.2, 0.9, 1.25), "FFFFFF")
a = variant("Bunny", "Robot Rabbit", {"F4F1EE": "9AA4B2", "FFFFFF": "C8D0DC", "ECE6E2": "6A7080", "F7B6C8": ("5CE6FF", "neon"), "F28BA5": "FF2A6A"})
a.group = "World2"
a.b((0.6, 0.06, 0.12), (0, 0.72, 1.74), "5CE6FF", "head", kind="neon")
# Ice Age
a = variant("Gorilla", "Giant Sloth", {"34343C": "8A7A5A", "28282E": "5A4A3A", "6A6A78": "C8B898", "8E8E9A": "A89A7A"})
a.group = "World2"
for x in (1.0, -1.0):
    a.b((0.12, 0.3, 0.12), (x, 0.55, 0.12), "F0E8D8", "armR" if x > 0 else "armL")
a = variant("Elephant", "Mammoth", {"9AA4B2": "7A4A2A", "8E98A6": "5A3A20", "E6E0D4": "4A2A18", "D9473B": "6A3A20", "FFC93C": "7A4A2A", "F2B0BE": "8A5A3A"})
a.group = "World2"
a.m((0.14, 0.9, 0.14), (0.35, 1.55, 1.7), "FFF6EA", "head", rot=(-55, 0, 10)).m((0.14, 0.4, 0.14), (0.4, 2.05, 2.05), "FFF6EA", "head", rot=(30, 0, 10))
a = variant("Tiger", "Saber-Tooth Tiger", {"F28A24": "C8A070", "1C1414": "8A6A4A", "FFF6EA": "F0E0C8"})
a.group = "World2"
a.m((0.08, 0.06, 0.4), (0.15, 2.0, 1.15), "FFFFFF", "head")
# Mushroom Kingdom
a = variant("Hamster", "Forest Mouse", {"E8B465": "9A6A4A", "FFF3E0": "E8D0B0", "D4893A": "6A4A32"})
a.group = "World2"
a.b((0.08, 0.9, 0.08), (0, -0.85, 0.3), "C88A8A", "tail", rot=(-10, 0, 0)).pivot("tail", (0, -0.5, 0.3))
a = Brick("Snail", "World2")
a.b((0.6, 1.8, 0.4), (0, 0, 0.2), "A8C870").b((0.5, 0.5, 0.6), (0, 0.85, 0.6), "A8C870", "head").pivot("head", (0, 0.7, 0.4))
a.m((0.06, 0.06, 0.45), (0.15, 0.95, 1.1), "A8C870", "head").m((0.14, 0.14, 0.14), (0.15, 0.95, 1.35), "FFFFFF", "head").m((0.08, 0.08, 0.08), (0.15, 1.0, 1.37), INK, "head")
for k, (s, c) in enumerate(((1.3, "C87A3A"), (0.95, "E89A4A"), (0.6, "F0B860"))):
    a.b((0.7, s, s), (0, -0.25, 0.85 + k * 0.05), c)
a, i = quad("Mushroom Frog", "World2", "4CB44A", "C8F0A0", L=1.2, W=1.1, H=0.6, hip=0.25, head=0.8, ear=None, tail=None)
a.b((1.3, 1.3, 0.35), (0, i["hy"], i["top"] + 0.15), "E8401C", "head").b((0.9, 0.9, 0.2), (0, i["hy"], i["top"] + 0.4), "E8401C", "head")
for x, y in ((0.35, 0.2), (-0.3, -0.15), (0.05, 0.45)):
    a.b((0.18, 0.18, 0.06), (x, i["hy"] + y, i["top"] + 0.51), "FFFFFF", "head")
# Heaven's Gate
a, i = quad("Celestial Deer", "World2", "F0E8FF", "FFFFFF", L=1.6, W=0.75, H=0.75, hip=0.9, head=0.6, snout="FFFFFF", ear="point", tail="stub", hoof="FFC21C", glow_eyes=True, eye="8CB8FF")
for x in (0.2, -0.2):
    a.b((0.08, 0.08, 0.6), (x, i["hy"], i["top"] + 0.3), "FFE45C", "head", kind="neon").b((0.3, 0.08, 0.08), (x * 1.6, i["hy"], i["top"] + 0.45), "FFE45C", "head", kind="neon")
stars(a, ((0.38, 0.2, 1.4), (-0.38, -0.3, 1.5), (0.38, -0.5, 1.2)), "C8D8FF", 0.1)
a, i = bird("Golden Eagle", "World2", "D8A030", "B8801C", "FFFFFF", s=1.2, belly="F0C860", legs="FFC21C")
a.b((0.66, 0.62, 0.3), (0, 0.42, i["hz"] + 0.2), "FFE45C", "head", kind="neon")
a = variant("Lion", "Angelic Lion", {"E8B05A": "FFF8E8", "F5DDB0": "FFFFFF", "A65A1E": "FFE45C", "C8742C": "FFD23C", "5C2E14": "FFC21C"})
a.group = "World2"
wings(a, 0.65, 0.0, 1.9, "FFFFFF", "FFF2C2", 1.5)
halo(a, 1.25, 2.85, 0.38)
# Underworld
a, i = bird("Demon Bat", "World2", "4A1018", "7A1A28", "2A0A10", s=0.9, legs=None, tail=False, eye="FF3B1C", glow_eyes=True)
horn(a, 0.18, 0.35, i["hz"] + 0.2, "1C0A0A", 0.35, -10)
a = variant("Dog", "Hellhound", {"D8A266": "1C1418", "F3E1C4": "3A1A1A", "C08548": "2A1414", "8A5A32": "141010", "D6383A": ("FF5A1C", "neon"), "141418": ("FF3B1C", "neon")})
a.group = "World2"
flames(a, 0, -1.2, 0.9, bone="tail")
flames(a, 0.3, 0.6, 2.4, bone="head", s=0.7)
flames(a, -0.3, 0.6, 2.4, bone="head", s=0.7)
a = variant("Dragon", "Cursed Dragon", {"7B3FE4": "3A1A2A", "4A1FA0": "1C0A14", "C9ADFF": "6A2A3A", "A985FF": "5A1A2A", "neon:5CFF9D": "B45CFF", "neon:FFE14A": "FF3B6B"})
a.group = "World2"

# ====================================================================== SECRETS (zone Secrets + the 36 extras)
def S(model, name):  # mark a Secret
    model.group = "Secret2"
    return model


# Dinosaur Island
S(variant("Dragon", "Ancient Dragon", {"7B3FE4": "8A6A3A", "4A1FA0": "5A4020", "C9ADFF": "D8B880", "A985FF": "B89060", "neon:5CFF9D": "FFC21C"}), "")
a = S(variant("T-Rex", "Skeleton Rex", {"3E8A3A": "F0ECE0", "C8E0A0": "C8C0A8"}), "")
for k in range(4):
    a.b((1.24, 0.1, 0.1), (0, 0, 1.0 + k * 0.3), "8A8270")
a, i = quad("Earth Turtle", "Secret2", "6A9A4A", "C8B880", L=1.5, W=1.3, H=0.4, hip=0.4, head=0.6, ear=None, tail="stub", leg="6A9A4A")
a.b((1.5, 1.7, 0.7), (0, -0.05, 1.15), "7A5A32").b((1.1, 1.3, 0.3), (0, -0.05, 1.6), "8A6A3A")
for x, y in ((0.3, 0.2), (-0.35, -0.3), (0.1, -0.5)):
    a.b((0.3, 0.3, 0.6), (x, y, 2.0), "3CC84A").b((0.25, 0.25, 0.4), (x + 0.1, y, 2.45), "8FF0FF", kind="glass")
# Lost Desert
a = S(variant("Cat", "Pharaoh Cat", {"E8A055": "FFC21C", "C27532": "D8A010", "F8EEDD": "FFF4C2", "2E6B1E": ("3AA8FF", "neon")}), "")
a.b((0.95, 0.5, 0.15), (0, 0.15, 2.1), "3A5AE0", "head").m((0.15, 0.4, 0.6), (0.45, 0.1, 1.8), "3A5AE0", "head").b((0.3, 0.1, 0.3), (0, 0.42, 2.2), "FFC21C", "head", kind="neon")
a = S(variant("Lion", "Golden Sphinx", {"E8B05A": "E8C060", "F5DDB0": "F5E0A0", "A65A1E": "3A5AE0", "C8742C": "FFC21C", "5C2E14": "3A5AE0"}), "")
wings(a, 0.65, 0.0, 1.9, "FFE45C", "FFC21C", 1.4)
a = S(variant("Scorpion", "Lava Scorpion", {"B8642A": "2A2A30", "C87430": "FF5A1C"}), "")
# Sakura Gardens
a = S(variant("Fox", "Sakura Kitsune", {"F07A26": "FFB0D8", "FFF6EA": "FFFFFF", "2A1D18": "FF6AB0", "141418": ("FF3B9A", "neon")}), "")
multi_tail(a, 3, "FFB0D8", "FFFFFF", 80, (0, -0.7, 1.0))
a = S(variant("Fox", "Kitsune", {"F07A26": "FFFFFF", "FFF6EA": "F0F0FF", "2A1D18": "C8C8E0", "141418": ("FF3B3B", "neon")}), "")
multi_tail(a, 5, "FFFFFF", "6FD8FF", 120, (0, -0.7, 1.0))
a = S(variant("Fox", "Nine-Tailed Fox", {"F07A26": "FF8A2A", "FFF6EA": "FFF0D8", "2A1D18": "C85A1C", "141418": ("3AA8FF", "neon")}), "")
multi_tail(a, 9, "FF8A2A", "3AA8FF", 170, (0, -0.7, 1.0))
# Lost Atlantis
a, i = serpent("Atlantis Leviathan", "Secret2", "1A6A8A", "2AD8C8", segs=9, r=0.6, z=1.1, eye="6FF0FF", glow_eyes=True)
for k in range(5):
    a.b((0.12, 0.3, 0.5), (0, -k * 0.75, 1.1 + 0.6 + _w2.sin(k * 0.9) * 0.3), "6FF0FF", "body" if k < 4 else "tail", kind="neon")
crown(a, 0.9, i["top"] + 0.05, "6FF0FF")
a, i = serpent("Sea Serpent", "Secret2", "2A5AE0", "6A9AFF", segs=8, r=0.5, z=1.0, eye="FFE45C", glow_eyes=True)
horn(a, 0.2, 0.9, i["top"], "FFFFFF", 0.4, -20)
a = S(variant("Shark", "Cyber Shark", {"7A8A9A": "5A6070", "5A6A7A": ("5CE6FF", "neon"), "F0F4F8": "C8D0DC"}), "")
a, i = biped("Alien Octopus", "Secret2", "B45CFF", "D8A8FF", H=0.9, W=1.1, head=1.1, leg=0.15, arms=False, ear=None, eye="B8FF4A", glow_eyes=True)
for k in range(8):
    t = 2 * _w2.pi * k / 8
    bone = ("armR", "legFR", "armL", "legFL")[k % 4]
    a.b((0.22, 0.22, 0.9), (_w2.cos(t) * 0.7, _w2.sin(t) * 0.7, 0.3), "9B5CFF", bone, rot=(_w2.degrees(_w2.sin(t)) * 0.6, -_w2.degrees(_w2.cos(t)) * 0.6, 0))
a = Brick("Cosmic Jellyfish", "Secret2")
for k, (w, z) in enumerate(((1.6, 1.6), (1.35, 1.95), (1.0, 2.25), (0.55, 2.45))):
    a.b((w, w, 0.35), (0, 0, z), ("8C7BFF", "A890FF", "C8A8FF", "E8D8FF")[k], kind="glass")
a.b((1.3, 1.3, 0.3), (0, 0, 1.75), "6FF0FF", kind="neon")
a.m((0.14, 0.06, 0.18), (0.25, 0.66, 1.85), "FFFFFF", kind="neon")
for k in range(8):
    t = 2 * _w2.pi * k / 8
    a.b((0.1, 0.1, 1.3), (_w2.cos(t) * 0.55, _w2.sin(t) * 0.55, 0.85), "C8A8FF" if k % 2 else "6FF0FF", "tail", kind="neon")
a.pivot("tail", (0, 0, 1.5))
stars(a, ((0.4, 0.3, 2.1), (-0.3, 0.2, 2.3), (0.1, -0.4, 2.0)), "FFFFFF", 0.1)
# Sky Kingdom
a = S(variant("Griffin", "Cloud Emperor", {"C89A5A": "F4F8FF", "F5E8D0": "FFFFFF", "FFC21C": "FFE45C"}), "")
crown(a, 1.25, 2.6, "5CE6FF")
for x, y in ((0.6, -0.6), (-0.6, -0.2), (0.4, 0.5)):
    a.b((0.9, 0.7, 0.4), (x, y, 0.25), "FFFFFF")
a = S(variant("Rainbow Pegacorn", "Celestial Unicorn", {"FF4A5A": "C8D8FF", "FF9A2A": "E8E0FF", "FFE03A": "C8D8FF", "4CD964": "E8E0FF", "3AA8FF": "C8D8FF",
                                                            "7A5CFF": "E8E0FF", "C85CFF": "C8D8FF", "FFB8E0": "B45CFF"}), "")
stars(a, ((0.46, 0.4, 1.7), (-0.46, -0.3, 1.6), (0.46, -0.6, 1.4), (0, 0.9, 2.9)), "FFE45C", 0.12)
a = S(variant("Fox", "Thunder Wolf", {"F07A26": "3A3F5A", "FFF6EA": "6A7AA0", "2A1D18": "FFE14A", "141418": ("FFE14A", "neon")}), "")
for x, y, z in ((0.3, 0.0, 1.4), (-0.3, -0.4, 1.4), (0, 0.4, 1.4)):
    a.b((0.08, 0.3, 0.5), (x, y, z), "FFE14A", kind="neon", rot=(0, 25, 0))
a = S(variant("Celestial Deer", "Wind Spirit Deer", {"F0E8FF": ("8FF0D8", "glass"), "FFFFFF": ("C8FFF0", "glass"), "FFC21C": "6FF0C8", "neon:FFE45C": "6FF0C8"}), "")
a = S(variant("Owl", "Godly Owl", {"8A6A4A": "FFE45C", "6A4A32": "FFC21C", "E0C8A0": "FFFFFF"}), "")
halo(a, 0.35, 2.55, 0.34)
# Halloween Town
a, i = biped("Pumpkin Reaper", "Secret2", "1C1C22", None, H=1.3, W=0.9, head=1.0, leg=0.5, ear=None, eye="FFC21C", glow_eyes=True)
a.b((1.05, 0.95, 0.85), (0, 0.05, i["hz"]), "FF8A1C", "head").b((0.14, 0.14, 0.3), (0, 0.05, i["top"] + 0.15), "3C9A3C", "head")
a.b((0.5, 0.06, 0.12), (0, 0.52, i["hz"] - 0.25), "FFC21C", "head", kind="neon")
a.b((0.08, 0.08, 2.4), (0.65, 0.2, 1.3), "6A4A2A", "armR").b((0.9, 0.08, 0.3), (1.0, 0.2, 2.5), "C8D0DC", "armR", rot=(0, 20, 0))
a = S(variant("Bunny", "Phantom Bunny", {"F4F1EE": ("C8D8FF", "glass"), "FFFFFF": ("E8F0FF", "glass"), "ECE6E2": ("A8B8E8", "glass"), "141418": ("6FF0FF", "neon")}), "")
a = S(variant("Owl", "Nightmare Owl", {"8A6A4A": "2A1A3A", "6A4A32": "1C0A2A", "E0C8A0": "4A2A5A", "FFC21C": "B45CFF", "141418": ("FF3B3B", "neon")}), "")
a.m((0.9, 0.4, 0.1), (0.85, -0.1, 0.8), "1C0A2A", "wingR", rot=(0, 20, 0))
a = S(variant("Polar Bear", "Zombie Bear", {"F4F8FB": "7AA06A", "DCE6EE": "A8C090", "1C1C22": "3A2A1A", "3E7BFA": "6A3A2A", "141418": ("B8FF4A", "neon")}), "")
a.b((0.4, 0.06, 0.06), (0.3, 0.6, 1.0), "3A2A1A", rot=(0, 30, 0))
a = S(variant("Eagle", "Reaper Raven", {"6A4A2A": "141418", "4A321C": "2A2236", "8A6A4A": "1C1C22", "FFC21C": "3A2A55", "FFFFFF": "2A2236", "141418": ("B45CFF", "neon")}), "")
a = S(variant("Cat", "Haunted Doll Cat", {"E8A055": "F4E8E0", "C27532": "E0C8C0", "F8EEDD": "FFFFFF", "2E6B1E": ("3AA8FF", "neon"), "F7B2C2": "FF8AB8"}), "")
a.b((0.04, 0.1, 0.5), (0.25, 0.86, 1.7), "3A2A2A").b((0.6, 0.08, 0.3), (0, 0.5, 1.3), "B0102A")
# Tropical Paradise
a = S(variant("Phoenix", "Tropical Phoenix", {"E8341C": "1CB4A8", "FF6A1C": "FF8AB8", "FFE36A": "FFE45C", "neon:FF6A1C": "FF6AD5", "neon:FFC21C": "6FF0C8"}), "")
a = S(variant("Flamingo", "Bubblegum Flamingo", {"FF8AB8": ("FF8AD8", "glass"), "FF6AA0": ("FFB0E8", "glass"), "1C1C22": "FF3B9A"}), "")
a, i = quad("Watermelon Turtle", "Secret2", "4CB44A", "C8F0A0", L=1.4, W=1.2, H=0.35, hip=0.35, head=0.55, ear=None, tail="stub")
a.b((1.4, 1.6, 0.7), (0, -0.05, 1.05), "2E9A2A").b((1.2, 1.4, 0.2), (0, -0.05, 1.45), "FF4A5A")
for x, y in ((0.3, 0.2), (-0.35, -0.3), (0.1, -0.5), (-0.2, 0.4)):
    a.b((0.08, 0.14, 0.04), (x, y, 1.56), "141418")
a = S(variant("Raptor", "Chocolate Crocodile", {"6FA84A": "6A3A20", "D8E8A0": "C8905A", "D8582A": "4A2614"}), "")
for x in (-0.15, 0.15):
    a.b((0.1, 0.1, 0.1), (x, 0.95, 1.5), "FFC21C", "head", kind="neon")
# Toy Factory
a, i = biped("Ultimate Toymaster", "Secret2", "9AA4B2", "5CE6FF", H=1.3, W=1.0, head=0.9, leg=0.55, ear=None, eye="5CE6FF", glow_eyes=True)
crown(a, 0.05, i["top"] + 0.05, "FF3B6B")
a.b((0.6, 0.06, 0.12), (0, 0.48, i["hz"] - 0.15), "FF2A6A", "head", kind="neon").b((0.4, 0.4, 0.4), (0.75, 0.3, 1.0), "FFC21C", "armR")
a = S(variant("Hamster", "Space Hamster", {"E8B465": "F0C890", "D4893A": "C88A4A"}), "")
a.b((1.4, 1.3, 1.25), (0, 0, 0.62), "8FF0FF", kind="glass").b((0.3, 0.3, 0.3), (0, 0, 1.35), "FF3B3B", kind="neon")
a = Brick("Mecha Spider", "Secret2")
a.b((1.0, 1.2, 0.6), (0, 0, 0.9), "5A6070").b((0.7, 0.6, 0.5), (0, 0.8, 0.9), "9AA4B2", "head").pivot("head", (0, 0.5, 0.9))
for x in (-0.2, 0, 0.2):
    a.b((0.12, 0.06, 0.12), (x, 1.11, 1.0), "FF2A6A", "head", kind="neon")
for k in range(4):
    y = 0.45 - k * 0.3
    bone = ("legFR", "legBR", "legFR", "legBR")[k]
    a.m((0.8, 0.12, 0.12), (0.85, y, 1.05), "9AA4B2", bone, rot=(0, -30, 0)).m((0.12, 0.12, 0.9), (1.25, y, 0.5), "5A6070", bone)
a.pivot("legFR", (0.5, 0.2, 1.0)).pivot("legFL", (-0.5, 0.2, 1.0)).pivot("legBR", (0.5, -0.3, 1.0)).pivot("legBL", (-0.5, -0.3, 1.0))
a.b((0.3, 0.3, 0.1), (0, 0, 1.22), "5CE6FF", kind="neon")
a = S(variant("Lion", "Mecha Lion", {"E8B05A": "9AA4B2", "F5DDB0": "C8D0DC", "A65A1E": "5A6070", "C8742C": "6A7080", "5C2E14": "3A3F4A",
                                     "neon:FFD23C": "FF2A6A", "141418": ("5CE6FF", "neon")}), "")
a = S(variant("Cat", "Pizza Cat", {"E8A055": "F0C860", "C27532": "D8501C", "F8EEDD": "FFE8A0"}), "")
for x, y, z in ((0.3, 0.1, 1.2), (-0.3, -0.2, 1.1), (0.1, -0.4, 1.3)):
    a.b((0.02, 0.22, 0.22), (x if x > 0 else x, y, z), "C8301C")
a = S(variant("Sheep", "Marshmallow Sheep", {"F5F3EE": "FFD0E8", "FFFFFF": "C8F0FF", "2E2E34": "FFF4E0", "1A1A20": "E8C8D8"}), "")
# Ice Age
a = S(variant("Mammoth", "Frozen Mammoth King", {"7A4A2A": ("A8DCFF", "glass"), "5A3A20": ("7ABCE8", "glass"), "4A2A18": "5A9ACA", "6A3A20": "C8F0FF", "8A5A3A": "E8FAFF"}), "")
crown(a, 1.0, 2.75, "6FF0FF", 0.7)
a = S(variant("Saber-Tooth Tiger", "Frost Saber", {"C8A070": "E8F4FF", "8A6A4A": "6FD8FF", "F0E0C8": "FFFFFF", "C8D838": ("6FF0FF", "neon")}), "")
a = S(variant("Penguin", "Ice Cream Penguin", {"232A3A": "FF9AC8", "FFFFFF": "FFF4E0", "E23B3B": "8A5A3A"}), "")
a.b((0.5, 0.5, 0.3), (0, 0.05, 2.12), "E8C08A", "head").b((0.4, 0.4, 0.3), (0, 0.05, 2.4), "FFFFFF", "head").b((0.12, 0.12, 0.12), (0, 0.05, 2.62), "E8401C", "head")
# Mushroom Kingdom
a = S(variant("Dragon", "Mycelium Dragon", {"7B3FE4": "C8A8E8", "4A1FA0": "8A5A3A", "C9ADFF": "F0E8FF", "A985FF": "E8401C", "neon:5CFF9D": "B8FF4A"}), "")
for x, y in ((0.3, 0.3), (-0.3, -0.3), (0, -0.8)):
    a.b((0.2, 0.2, 0.3), (x, y, 2.05), "F4F0E8").b((0.6, 0.6, 0.2), (x, y, 2.3), "E8401C")
a = Brick("Crystal Butterfly", "Secret2")
a.b((0.25, 1.0, 0.25), (0, 0, 1.3), "3A2A55").b((0.3, 0.3, 0.3), (0, 0.6, 1.4), "3A2A55", "head").pivot("head", (0, 0.45, 1.35))
a.m((0.04, 0.04, 0.4), (0.08, 0.7, 1.7), "3A2A55", "head")
a.m((1.2, 0.9, 0.06), (0.75, 0.2, 1.5), "8FF0FF", "wingR", kind="glass", rot=(0, -15, 0)).m((0.9, 0.7, 0.06), (0.6, -0.5, 1.2), "FF8AD8", "wingR", kind="glass", rot=(0, -10, 0))
a.m((0.3, 0.3, 0.07), (0.8, 0.25, 1.52), "FFFFFF", "wingR", kind="neon", rot=(0, -15, 0)).pivot("wingR", (0.12, 0, 1.35)).pivot("wingL", (-0.12, 0, 1.35))
# Heaven's Gate
a = S(variant("Phoenix", "Divine Seraphim", {"E8341C": "FFFFFF", "FF6A1C": "FFF4C2", "FFE36A": "FFE45C", "neon:FF6A1C": "FFFFFF", "neon:FFC21C": "FFE45C"}), "")
a.m((0.9, 0.45, 0.1), (0.75, -0.1, 2.2), "FFFFFF", "wingR", rot=(0, -50, 0)).m((0.9, 0.45, 0.1), (0.7, -0.1, 0.95), "FFF4C2", "wingR", rot=(0, 10, 0))
halo(a, 0.35, 2.75, 0.36)
a = S(variant("Griffin", "Celestial Emperor", {"C89A5A": "FFE45C", "F5E8D0": "FFF4C2", "FFFFFF": "FFFFFF", "FFC21C": "FFFFFF"}), "")
crown(a, 1.25, 2.6, "B45CFF")
a, i = serpent("Infinity Serpent", "Secret2", "FF4A5A", "3AA8FF", segs=9, r=0.5, z=1.0, eye="FFFFFF", glow_eyes=True)
for k, c in enumerate(("FF9A2A", "FFE03A", "4CD964", "9B5CFF")):
    a.b((0.85, 0.3, 0.85), (0, -(k * 2 + 1) * 0.625, 1.0 + _w2.sin((k * 2 + 1) * 0.9) * 0.25), c, "body" if k < 2 else "tail")
a = S(variant("Dragon", "Infinity Dragon", {"7B3FE4": ("C8A8FF", "glass"), "4A1FA0": ("8FF0FF", "glass"), "C9ADFF": "FFFFFF", "A985FF": ("FF8AD8", "glass"), "neon:5CFF9D": "FFFFFF"}), "")
a = S(variant("Arctic Wolf", "Eternal Wolf", {"E6EEF5": "2A2A6A", "FFFFFF": "C8D8FF", "9DB7CC": "4A4A9A", "2B3A4A": "141430", "8FE3FF": ("FFE45C", "neon"), "5CD6FF": ("C8D8FF", "neon")}), "")
stars(a, ((0.45, 0.2, 1.5), (-0.45, -0.3, 1.6), (0.45, -0.6, 1.3), (0, 0.5, 2.3)), "C8D8FF", 0.12)
halo(a, 1.0, 2.6, 0.3)
# Underworld
a = S(variant("Dragon", "World Ender", {"7B3FE4": "1C0A0A", "4A1FA0": "3A0A0A", "C9ADFF": "FF3B1C", "A985FF": "6A0A0A", "neon:5CFF9D": "FF3B1C", "neon:FFE14A": "FFE14A"}), "")
for x, y in ((0.4, 1.2), (0.6, 0.9)):
    horn(a, x, y, 2.6, "141418", 0.6, -15)
flames(a, 0, -2.7, 1.1, bone="tail", s=1.3)
a = S(variant("Dragon", "Demon Dragon", {"7B3FE4": "B0102A", "4A1FA0": "3A0A14", "C9ADFF": "FF6A3C", "A985FF": "5A0A1A", "neon:5CFF9D": "FFD23C"}), "")
horn(a, 0.3, 1.3, 2.7, "1C0A0A", 0.7, -25)
a = S(variant("Phoenix", "Magma Phoenix", {"E8341C": "2A1A1A", "FF6A1C": "FF5A1C", "FFE36A": "FF8A2A", "neon:FF6A1C": "FF3B1C", "neon:FFC21C": "FFD23C"}), "")
a = Brick("Void Creature", "Secret2")
a.b((1.4, 1.3, 1.3), (0, 0, 0.9), "14081C").b((1.0, 1.0, 0.6), (0, 0, 1.75), "1C0A2A", "head").pivot("head", (0, 0, 1.5))
for x, z, s in ((0.3, 1.3, 0.3), (-0.3, 1.2, 0.22), (0, 1.05, 0.18), (0.15, 1.75, 0.15)):
    a.b((s, 0.06, s), (x, 0.66, z), "B45CFF", "head" if z > 1.5 else "body", kind="neon")
for k in range(6):
    t = 2 * _w2.pi * k / 6
    a.b((0.25, 0.25, 0.7), (_w2.cos(t) * 0.7, _w2.sin(t) * 0.7, 0.3), "2A0A3A", "tail", rot=(20, 0, _w2.degrees(t)))
a.pivot("tail", (0, 0, 0.6))

# ====================================================================== 11 NEW TOYS
a = Brick("Meteor Ball", "Toys")
ball(a, 1.3, "3A2A2A", "FF5A1C", "FF5A1C")
a.b((0.5, 0.5, 0.5), (0, 0, 0), "FFD23C", kind="neon")
a = Brick("Dragon Plush", "Toys")
a.b((1.0, 1.0, 1.0), (0, 0, 0), "9B5CFF").b((0.7, 0.7, 0.6), (0, 0.6, 0.6), "9B5CFF").m((0.6, 0.1, 0.4), (0.7, -0.1, 0.4), "C8A8FF")
a.b((0.12, 0.06, 0.12), (0.18, 0.96, 0.7), INK).b((0.12, 0.06, 0.12), (-0.18, 0.96, 0.7), INK)
a = Brick("Galaxy Orb", "Toys")
ball(a, 1.3, "2A1A5A", "8C7BFF")
stars(a, ((0.4, 0.5, 0.2), (-0.3, 0.55, -0.3), (0.2, 0.55, 0.5)))
a = Brick("Prismatic Frisbee", "Toys")
for k, c in enumerate(("FF4A5A", "FFE03A", "4CD964", "3AA8FF", "9B5CFF")):
    a.b((1.6 - k * 0.25, 1.6 - k * 0.25, 0.16), (0, 0, k * 0.03), c, kind="neon" if k == 4 else "plastic")
a = Brick("Void Orb", "Toys")
ball(a, 1.3, "14081C", "B45CFF", "B45CFF")
a.b((0.6, 0.6, 0.6), (0, 0, 0), "B45CFF", kind="neon")
a = Brick("Phoenix Feather", "Toys")
a.b((0.08, 1.8, 0.08), (0, 0, 0), "FFE36A").b((0.6, 1.4, 0.06), (0, 0.15, 0), "FF5A1C").b((0.4, 0.5, 0.07), (0, 0.75, 0), "FFD23C", kind="neon")
a = Brick("King's Ball", "Toys")
ball(a, 1.3, "B0102A", "FFC21C", "FFC21C")
crown(a, 0, 0.6, "5CE6FF", 0.7, "body")
a = Brick("Floating Crystal", "Toys")
a.b((0.7, 0.7, 1.6), (0, 0, 0), "8FF0FF", kind="glass", rot=(0, 0, 45)).b((0.4, 0.4, 0.9), (0, 0, 0), "FFFFFF", kind="neon", rot=(0, 0, 45))
a = Brick("Thunder Bolt", "Toys")
for k, (x, z) in enumerate(((0.2, 0.7), (-0.15, 0.1), (0.15, -0.5))):
    a.b((0.3, 0.3, 0.8), (x, 0, z), "FFE14A", kind="neon", rot=(0, 25 if k % 2 == 0 else -25, 0))
a = Brick("Galaxy Destroyer", "Toys")
ball(a, 1.4, "1C0A2A", "FF3B6B", "8C7BFF")
for k in range(4):
    t = 2 * _w2.pi * k / 4
    a.b((0.2, 0.2, 0.6), (_w2.cos(t) * 0.85, _w2.sin(t) * 0.85, 0), "FF3B6B", kind="neon", rot=(90, 0, _w2.degrees(t)))
a = Brick("Infinity Sphere", "Toys")
ball(a, 1.4, "FFFFFF", "FF4A5A", "3AA8FF")
a.b((0.8, 0.8, 0.8), (0, 0, 0), "FFE45C", kind="neon")
stars(a, ((0.5, 0.6, 0.3), (-0.4, 0.6, -0.3)), "FF6AD5", 0.12)

# ====================================================================== extra FX for the new cinematics
a = Brick("FX Tornado", "FX")
for k in range(12):
    r = 0.6 + k * 0.28
    for j in range(6):
        t = 2 * _w2.pi * j / 6 + k * 0.5
        a.b((0.5 + k * 0.08, 0.2, 0.3), (_w2.cos(t) * r, _w2.sin(t) * r, k * 0.55), "E8F4FF" if (j + k) % 2 else "B8D0E8", kind="glass", rot=(0, 0, _w2.degrees(t) + 90))
a = Brick("FX Water Tornado", "FX")
for k in range(12):
    r = 0.7 + k * 0.3
    for j in range(6):
        t = 2 * _w2.pi * j / 6 + k * 0.5
        a.b((0.5 + k * 0.08, 0.2, 0.3), (_w2.cos(t) * r, _w2.sin(t) * r, k * 0.55), "3AA8FF" if (j + k) % 2 else "8FF0FF", kind="glass", rot=(0, 0, _w2.degrees(t) + 90))
a = Brick("FX Black Hole", "FX")
a.b((2.0, 0.3, 2.0), (0, 0, 0), "000000").b((2.4, 0.2, 2.4), (0, -0.05, 0), "B45CFF", kind="neon", rot=(0, 45, 0))
for k in range(10):
    t = 2 * _w2.pi * k / 10
    a.b((0.6, 0.1, 0.18), (_w2.cos(t) * 1.8, 0, _w2.sin(t) * 1.8), "8C7BFF", kind="neon", rot=(0, -_w2.degrees(t), 0))
a = Brick("FX Meteor", "FX")
ball(a, 1.6, "3A2A2A", "FF5A1C", "FF5A1C")
a.b((0.9, 0.9, 0.9), (0, 0, 0), "FFD23C", kind="neon").b((0.8, 2.0, 0.8), (0, -1.4, 0), "FF7A1C", kind="neon")
a = Brick("FX Lightning", "FX")
for k in range(8):
    a.b((0.35, 0.35, 1.6), (0.5 * (1 if k % 2 else -1), 0, k * 1.4 + 0.8), "FFE14A", kind="neon", rot=(0, 25 if k % 2 else -25, 0))
a = Brick("FX Moon", "FX")
ball(a, 3.0, "F0F4FF")
a.b((0.6, 0.2, 0.6), (0.5, 1.5, 0.4), "C8D0DC").b((0.4, 0.2, 0.4), (-0.6, 1.5, -0.3), "C8D0DC")
a = Brick("FX Galaxy Dome", "FX")
for k in range(16):
    t = 2 * _w2.pi * k / 16
    for j in range(4):
        e = _w2.radians(10 + j * 22)
        a.b((0.9, 0.12, 0.5), (_w2.cos(t) * _w2.cos(e) * 4, _w2.sin(t) * _w2.cos(e) * 4, _w2.sin(e) * 4), ("2A1A5A", "8C7BFF", "C8A8FF", "6FF0FF")[(k + j) % 4], kind="glass" if (k + j) % 3 else "neon", rot=(0, -_w2.degrees(e), _w2.degrees(t) + 90))
a = Brick("FX Hamster Ball", "FX")
a.b((2.4, 2.4, 2.4), (0, 0, 1.2), "C8F6FF", kind="glass").b((2.5, 0.1, 0.1), (0, 0, 1.2), "FFFFFF").b((0.1, 2.5, 0.1), (0, 0, 1.2), "FFFFFF")
a = Brick("FX Bubble", "FX")
a.b((3.0, 3.0, 3.0), (0, 0, 1.5), "FF8AD8", kind="glass").b((0.5, 0.2, 0.5), (0.8, 1.4, 2.4), "FFFFFF", kind="neon")
a = Brick("FX Ice Cream Cone", "FX")
a.b((1.2, 1.2, 2.5), (0, 0, 1.25), "E8C08A").b((1.6, 1.6, 1.0), (0, 0, 2.9), "FF9AC8").b((1.2, 1.2, 0.8), (0, 0, 3.7), "FFF4E0").b((0.3, 0.3, 0.3), (0, 0, 4.25), "E8401C")
a = Brick("FX Choco Coin", "FX")
a.b((0.6, 0.12, 0.6), (0, 0, 0), "FFC21C").b((0.5, 0.14, 0.5), (0, 0, 0), "6A3A20")
a = Brick("FX Melon Slice", "FX")
a.b((0.9, 0.2, 0.5), (0, 0, 0), "FF4A5A").b((0.9, 0.22, 0.12), (0, 0, -0.3), "2E9A2A").b((0.06, 0.22, 0.08), (0.2, 0, 0.05), "141418")
a = Brick("FX Pepperoni", "FX")
a.b((0.8, 0.1, 0.8), (0, 0, 0), "C8301C").b((0.2, 0.12, 0.2), (0.15, 0, 0.1), "8A1A14")
a = Brick("FX Scythe", "FX")
a.b((0.15, 0.15, 3.0), (0, 0, 1.5), "3A2A55").b((1.8, 0.1, 0.5), (0.9, 0, 3.0), "B45CFF", kind="neon", rot=(0, 15, 0))
a = Brick("FX Gold Wings", "FX")
for x in (1, -1):
    for k in range(4):
        a.b((1.2 - k * 0.15, 0.1, 0.4), (x * (0.8 + k * 0.5), 0, 0.3 + k * 0.45), "FFE45C" if k % 2 else "FFC21C", kind="neon" if k == 3 else "plastic", rot=(0, -x * (20 + k * 12), 0))
a = Brick("FX Blue Flame", "FX")
for k in range(9):
    t = 2 * _w2.pi * k / 9
    h = 1.0 + (k % 3) * 0.5
    a.b((0.6, 0.6, h), (_w2.cos(t) * 1.4, _w2.sin(t) * 1.4, h / 2), "3AA8FF" if k % 2 else "8FF0FF", kind="neon")
a = Brick("FX Tree", "FX")
a.b((0.4, 0.4, 1.4), (0, 0, 0.7), "7A4A22").b((1.4, 1.4, 1.2), (0, 0, 1.8), "3CC84A").b((0.4, 0.4, 0.8), (0.6, 0, 0.4), "8FF0FF", kind="glass")
a = Brick("FX Web", "FX")
for k in range(8):
    t = 2 * _w2.pi * k / 8
    a.b((0.08, 0.06, 3.0), (_w2.cos(t) * 1.5, 0, _w2.sin(t) * 1.5 + 2), "5CE6FF", kind="neon", rot=(0, -_w2.degrees(t) + 90, 0))
for r in (0.8, 1.6, 2.4):
    for k in range(8):
        t = 2 * _w2.pi * (k + 0.5) / 8
        a.b((r * 0.8, 0.05, 0.06), (_w2.cos(t) * r, 0, _w2.sin(t) * r + 2), "8FF0FF", kind="neon", rot=(0, -_w2.degrees(t), 0))
a = Brick("FX Laser", "FX")
a.b((0.5, 12, 0.5), (0, 6, 0), "FF2A6A", kind="neon").b((0.25, 12, 0.25), (0, 6, 0), "FFFFFF", kind="neon")
a = Brick("FX Portal", "FX")
for k in range(14):
    t = 2 * _w2.pi * k / 14
    a.b((0.6, 0.2, 0.3), (_w2.cos(t) * 1.6, 0, _w2.sin(t) * 1.6 + 1.8), "5CE6FF" if k % 2 else "B45CFF", kind="neon", rot=(0, -_w2.degrees(t), 0))
a.b((2.4, 0.08, 2.4), (0, 0, 1.8), "2A1A5A", kind="glass", rot=(0, 45, 0))
a = Brick("FX Bone", "FX")
a.b((0.2, 0.9, 0.2), (0, 0, 0), "F0ECE0").b((0.35, 0.2, 0.35), (0, 0.5, 0), "F0ECE0").b((0.35, 0.2, 0.35), (0, -0.5, 0), "F0ECE0")
a = Brick("FX Infinity", "FX")
for k in range(24):
    t = 2 * _w2.pi * k / 24
    x, z = 2.2 * _w2.cos(t), 1.1 * _w2.sin(2 * t)
    a.b((0.5, 0.3, 0.5), (x, 0, z + 2.5), ("FF4A5A", "FF9A2A", "FFE03A", "4CD964", "3AA8FF", "9B5CFF")[k % 6], kind="neon")
a = Brick("FX Cloud", "FX")
for x, y, z, s in ((0, 0, 0.5, 1.6), (0.9, 0.2, 0.4, 1.2), (-0.9, -0.1, 0.4, 1.3), (0.3, 0.3, 1.1, 1.0)):
    a.b((s, s, s * 0.7), (x, y, z), "FFFFFF")
a = Brick("FX Star", "FX")
a.b((0.5, 0.5, 0.15), (0, 0, 0), "FFE45C", kind="neon", rot=(0, 0, 45)).b((0.5, 0.5, 0.15), (0, 0, 0), "FFFFFF", kind="neon")
