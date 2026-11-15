# Secret-pet catch cinematics, keyframed in Blender and exported as per-frame tracks for Roblox.
# Run: blender --background --factory-startup --python cinematics.py -- <out_dir> [render] [only=Name,..]
# Every cinematic: the pet starts and ends at rest at the origin facing +Y (Blender), 4.8 s at 30 fps.
# Tracks (all relative to the pet's rest spot): the pet root (+ non-uniform scale + fade), bone rotations about their
# pivots, FX props (from pets.py "FX" group), the camera, and timeline-marker events (bursts, flashes, shakes, sounds).
import bpy
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brick  # noqa: E402
import pets  # noqa: E402,F401  (registers every model)

args = sys.argv[sys.argv.index("--") + 1:]
OUT = args[0]
RENDER = "render" in args
ONLY = sum([a[5:].split(",") for a in args if a.startswith("only=")], [])
FPS, LEN, STEP = 30, 4.8, 2
NF = int(LEN * FPS)
MOD = {m.name: m for m in brick.MODELS}
C = [[1, 0, 0], [0, 0, 1], [0, -1, 0]]


def mm(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


CT = [[C[j][i] for j in range(3)] for i in range(3)]

# ---------------------------------------------------------------- scene helpers
_mats = {}


def mat(hexc, kind):
    key = hexc + kind
    if key not in _mats:
        m = bpy.data.materials.new(key)
        rgb = [(int(hexc[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)]
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*rgb, 1)
        b.inputs["Roughness"].default_value = 0.45
        if kind == "neon":
            b.inputs["Emission Color"].default_value = (*rgb, 1)
            b.inputs["Emission Strength"].default_value = 3
        if kind == "glass":
            b.inputs["Alpha"].default_value = 0.55
        _mats[key] = m
    return _mats[key]


def cube(name, size):
    me = bpy.data.meshes.new(name)
    h = [s / 2 for s in size]
    v = [(a * h[0], b * h[1], c * h[2]) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    return me


def empty(name, parent=None, loc=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent = parent
    ob.location = loc
    ob.rotation_mode = "XYZ"
    return ob


def build(model, name, parent=None, rig=False):
    """Bricks under an empty; with rig=True each bone gets an empty at its pivot that its bricks hang from."""
    m = MOD[model]
    root = empty(name, parent)
    root["alpha"] = 0.0
    root["model"] = model
    bones = {}
    if rig:
        for bone, pv in m.pivots.items():
            bones[bone] = empty(f"{name}:{bone}", root, pv)
    for i, bx in enumerate(m.boxes):
        me = cube(f"{name}_{i}", bx["size"])
        me.materials.append(mat(bx["color"], bx["kind"]))
        ob = bpy.data.objects.new(f"{name}_b{i}", me)
        bpy.context.scene.collection.objects.link(ob)
        host = bones.get(bx["bone"]) if rig else None
        ob.parent = host or root
        p = bx["pos"]
        ob.location = (p[0] - host.location[0], p[1] - host.location[1], p[2] - host.location[2]) if host else p
        if bx["rot"]:
            ob.rotation_euler = tuple(math.radians(a) for a in bx["rot"])
    return root, bones


def key(ob, t, loc=None, rot=None, scale=None, alpha=None):
    f = round(t * FPS)
    if loc is not None:
        ob.location = loc
        ob.keyframe_insert("location", frame=f)
    if rot is not None:
        ob.rotation_euler = tuple(math.radians(a) for a in rot)
        ob.keyframe_insert("rotation_euler", frame=f)
    if scale is not None:
        ob.scale = (scale,) * 3 if isinstance(scale, (int, float)) else scale
        ob.keyframe_insert("scale", frame=f)
    if alpha is not None:
        ob["alpha"] = float(alpha)
        ob.keyframe_insert('["alpha"]', frame=f)


def look(pos, tgt):
    d = [tgt[i] - pos[i] for i in range(3)]
    return (math.degrees(math.atan2(math.hypot(d[0], d[1]), -d[2])), 0, math.degrees(math.atan2(d[1], d[0]) - math.pi / 2))


def shot(cam, t, pos, tgt):
    rx, ry, rz = look(pos, tgt)
    last = cam.get("lastz")
    if last is not None:  # unwrap the heading so the camera turns the short way instead of spinning around
        while rz - last > 180:
            rz -= 360
        while rz - last < -180:
            rz += 360
    cam["lastz"] = rz
    key(cam, t, loc=pos, rot=(rx, ry, rz))


def ev(t, text):
    bpy.context.scene.timeline_markers.new(text, frame=round(t * FPS))


def flap(bones, t0, t1, amp=40, period=0.32):
    t, up = t0, True
    while t <= t1 + 1e-6:
        a = amp if up else -amp * 0.6
        if "wingR" in bones:
            key(bones["wingR"], t, rot=(0, -a, 0))
        if "wingL" in bones:
            key(bones["wingL"], t, rot=(0, a, 0))
        t += period / 2
        up = not up
    for w in ("wingR", "wingL"):
        if w in bones:
            key(bones[w], t1 + 0.25, rot=(0, 0, 0))


def rest(pet, bones, t, z=0):
    key(pet, t, loc=(0, 0, z), rot=(0, 0, 0), scale=1, alpha=0)
    for b in bones.values():
        key(b, t, rot=(0, 0, 0))


def hidden_prop(model, name, parent=None):
    ob, _ = build(model, name, parent)
    key(ob, 0, scale=0.01, alpha=1)
    return ob


# ---------------------------------------------------------------- the 15 cinematics
def c_rainbow_dragon(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.2, 3.6, 45, 0.28)
    r, h = 4.2, 3.2
    for i in range(9):  # take off and fly a full circle, banking into the turn
        t = 0.5 + i * 0.36
        a = math.radians(-90 + i * 45)
        x, y = r * math.cos(a), r * math.sin(a) + r
        key(pet, t, loc=(x, y, h if i else 1.2), rot=(0, -18 if i else 0, math.degrees(a) + 90 if i else 0))
    key(pet, 0.2, loc=(0, 0, 0), rot=(0, 0, 0))
    key(pet, 3.9, loc=(0, 0.6, 1.0), rot=(10, 0, 0))
    key(pet, 4.3, loc=(0, 0, 0), rot=(0, 0, 0))
    key(pet, 4.8, loc=(0, 0, 0), rot=(0, 0, 0))
    beam = hidden_prop("FX Rainbow Beam", "beam", pet)
    key(beam, 1.25, loc=(0, 1.9, 2.0), rot=(-22, 0, 0), scale=0.01, alpha=1)
    key(beam, 1.45, scale=1.0, alpha=0)
    key(beam, 2.9, scale=1.1, alpha=0)
    key(beam, 3.2, scale=0.01, alpha=1)
    if "head" in bones:
        key(bones["head"], 1.2, rot=(0, 0, 0))
        key(bones["head"], 1.35, rot=(-20, 0, 0))
        key(bones["head"], 3.0, rot=(-20, 0, 0))
        key(bones["head"], 3.3, rot=(0, 0, 0))
    shot(cam, 0, (4, 8, 2.4), (0, 0, 1.6))
    shot(cam, 0.5, (4, 8.5, 3.0), (0, 0, 1.6))
    for i in range(1, 9):  # ride along from the middle of the circle, keeping the dragon in frame
        t = 0.5 + i * 0.36
        a = math.radians(-90 + i * 45)
        x, y = r * math.cos(a), r * math.sin(a) + r
        shot(cam, t, (-x * 1.1, r - (y - r) * 1.1, h + 5.5), (x, y, h))
    shot(cam, 4.0, (3.5, 8, 2.6), (0, 0, 1.5))
    shot(cam, 4.8, (3, 7.5, 2.4), (0, 0, 1.5))
    ev(1.3, "burst:FF6AD5:40")
    ev(1.6, "burst:FFE03A:40")
    ev(2.0, "burst:3AA8FF:40")
    ev(1.3, "sound:Legendary")
    ev(4.25, "shake:1.6")
    ev(4.25, "shock:FFFFFF")
    ev(4.3, "pillar:FF6AD5")


def c_shadow_panther(pet, bones, cam):
    rest(pet, bones, 0)
    spots = [(0, 0), (3.2, -1.2), (-3.2, -1.6), (0, 0)]
    t = 0.5
    key(pet, 0.35, loc=(0, 0, 0), scale=(1.05, 1.05, 0.85), alpha=0)
    for i in range(3):
        (x0, y0), (x1, y1) = spots[i], spots[i + 1]
        smoke = hidden_prop("FX Smoke", f"smoke{i}")
        key(smoke, t, loc=(x0, y0, 0), scale=0.2, alpha=0.1)
        key(smoke, t + 0.25, scale=1.5, alpha=0)
        key(smoke, t + 0.9, scale=2.1, alpha=1)
        key(pet, t, loc=(x0, y0, 0), scale=(1.05, 1.05, 0.85), alpha=0)
        key(pet, t + 0.15, loc=(x0, y0, 0), scale=0.6, alpha=1)
        key(pet, t + 0.5, loc=(x1, y1, 0), scale=0.6, alpha=1)
        smoke2 = hidden_prop("FX Smoke", f"smokeB{i}")
        key(smoke2, t + 0.5, loc=(x1, y1, 0), scale=0.2, alpha=0.1)
        key(smoke2, t + 0.7, scale=1.4, alpha=0)
        key(smoke2, t + 1.3, scale=2.0, alpha=1)
        key(pet, t + 0.75, loc=(x1, y1, 0), scale=1.0, alpha=0)
        ev(t + 0.05, "burst:B45CFF:30")
        ev(t + 0.55, "burst:5A3A7A:30")
        ev(t + 0.05, "sound:Catch")
        t += 1.15
    key(pet, 4.2, loc=(0, 0, 0), scale=1, alpha=0)
    rest(pet, bones, 4.8)
    if "head" in bones:
        key(bones["head"], 4.0, rot=(0, 0, 0))
        key(bones["head"], 4.3, rot=(12, 0, 0))
        key(bones["head"], 4.8, rot=(0, 0, 0))
    shot(cam, 0, (0, 9, 3), (0, 0, 1.2))
    shot(cam, 2.4, (2, 10, 4.5), (0, -0.8, 1.0))
    shot(cam, 4.8, (2.5, 7.5, 2.6), (0, 0, 1.3))
    ev(4.0, "flash:B45CFF:0.5")
    ev(4.0, "pillar:B45CFF")


def c_golden_phoenix(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.1, 1.15, 50, 0.24)
    key(pet, 1.1, loc=(0, 0, 2.2), rot=(0, 0, 180), scale=1.2, alpha=0)
    key(pet, 1.2, loc=(0, 0, 2.2), scale=0.01, alpha=1)
    key(pet, 2.9, loc=(0, 0, 2.2), scale=0.01, alpha=1)
    key(pet, 3.3, loc=(0, 0, 2.0), rot=(0, 0, 360), scale=1.25, alpha=0)
    flap(bones, 3.0, 4.2, 50, 0.24)
    key(pet, 4.3, loc=(0, 0, 0), rot=(0, 0, 360), scale=1, alpha=0)
    key(pet, 4.8, loc=(0, 0, 0), rot=(0, 0, 360), scale=1, alpha=0)
    for i in range(16):  # burst into a sphere of golden feathers that hang, then rush back in
        th = 2 * math.pi * i / 16
        ph = math.radians(-30 + 60 * ((i * 5) % 7) / 6)
        d = (math.cos(th) * math.cos(ph), math.sin(th) * math.cos(ph), math.sin(ph))
        f = hidden_prop("FX Feather", f"feather{i}")
        key(f, 1.2, loc=(0, 0, 2.2), rot=(0, 0, 0), scale=0.01, alpha=0)
        key(f, 1.25, scale=1.2)
        key(f, 1.9, loc=(d[0] * 4.2, d[1] * 4.2, 2.2 + d[2] * 3.2), rot=(math.degrees(ph) * 2, 90, math.degrees(th) + 200), scale=1.4)
        key(f, 2.7, loc=(d[0] * 4.8, d[1] * 4.8, 1.6 + d[2] * 3.2), rot=(math.degrees(ph) * 2, 200, math.degrees(th) + 320), scale=1.2)
        key(f, 3.15, loc=(0, 0, 2.1), rot=(0, 360, math.degrees(th) + 500), scale=0.3, alpha=0)
        key(f, 3.25, scale=0.01, alpha=1)
    shot(cam, 0, (4, 8, 2.4), (0, 0, 1.4))
    shot(cam, 1.2, (0, 10, 3.5), (0, 0, 2.2))
    shot(cam, 2.8, (-4, 9, 5), (0, 0, 2.2))
    shot(cam, 4.8, (3, 7.5, 2.6), (0, 0, 1.4))
    ev(1.2, "flash:FFD84A:0.8")
    ev(1.2, "burst:FFC21C:80")
    ev(1.2, "shake:1.4")
    ev(1.2, "sound:Legendary")
    ev(3.2, "flash:FFFFFF:0.7")
    ev(3.2, "pillar:FFC21C")
    ev(3.25, "burst:FFE45C:60")


def c_galaxy_cat(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.4, rot=(0, 0, 0))
        key(bones["head"], 0.9, rot=(25, 0, 0))
        key(bones["head"], 3.6, rot=(25, 0, 0))
        key(bones["head"], 4.2, rot=(0, 0, 0))
    key(pet, 0.9, loc=(0, 0, 0))
    key(pet, 1.6, loc=(0, 0, 0.6))
    key(pet, 3.6, loc=(0, 0, 0.6))
    key(pet, 4.2, loc=(0, 0, 0))
    for p, (model, r, h, ph, spd) in enumerate((("FX Planet A", 2.4, 2.0, 0, 1.0), ("FX Planet B", 3.1, 1.2, 120, -0.8), ("FX Planet C", 2.0, 3.0, 240, 1.3))):
        pl = hidden_prop(model, f"planet{p}")
        for i in range(13):
            t = 0.6 + i * 0.3
            a = math.radians(ph + spd * i * 40)
            key(pl, t, loc=(math.cos(a) * r, math.sin(a) * r, h + 0.3 * math.sin(i)), rot=(20, 0, i * 30),
                scale=(0.01 if i == 0 else 1.0), alpha=(1 if i == 0 else 0))
        key(pl, 4.4, scale=0.01, alpha=1)
    shot(cam, 0, (4, 8, 2.5), (0, 0, 1.4))
    shot(cam, 2.4, (-5, 7, 4.5), (0, 0, 1.8))
    shot(cam, 4.8, (3, 7.5, 2.6), (0, 0, 1.4))
    ev(0.6, "burst:FF6AD5:30")
    ev(0.6, "sound:Rare")
    ev(2.0, "burst:8C7BFF:40")
    ev(4.2, "pillar:8C7BFF")
    ev(4.2, "flash:C8A8FF:0.5")


def c_crystal_wolf(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.3, rot=(0, 0, 0))
        key(bones["head"], 0.8, rot=(40, 0, 0))
        key(bones["head"], 2.3, rot=(42, 0, 0))
        key(bones["head"], 2.8, rot=(0, 0, 0))
    key(pet, 0.3, loc=(0, 0, 0), scale=1)
    key(pet, 0.8, loc=(0, -0.2, 0), rot=(-8, 0, 0), scale=(1, 1, 1.05))
    key(pet, 2.3, loc=(0, -0.2, 0), rot=(-8, 0, 0), scale=(1, 1, 1.05))
    key(pet, 2.8, loc=(0, 0, 0), rot=(0, 0, 0), scale=1)
    for i, t in enumerate((1.0, 1.5, 2.0)):
        ring = hidden_prop("FX Crystal Ring", f"ring{i}")
        key(ring, t, loc=(0, 0, 0), rot=(0, 0, i * 15), scale=0.3, alpha=0)
        key(ring, t + 0.6, rot=(0, 0, i * 15 + 25), scale=1.6 + i * 0.5, alpha=0.1)
        key(ring, t + 1.4, scale=2.6 + i * 0.6, alpha=1)
        ev(t, "shock:8FF0FF")
        ev(t, "burst:C8F6FF:30")
    shot(cam, 0, (3, 8, 2.0), (0, 0, 1.4))
    shot(cam, 1.0, (5, 6, 0.8), (0, 0, 2.0))
    shot(cam, 3.0, (-6, 9, 5.5), (0, 0, 1))
    shot(cam, 4.8, (3, 7.5, 2.6), (0, 0, 1.4))
    ev(0.8, "sound:Legendary")
    ev(1.0, "shake:1.2")
    ev(3.6, "pillar:8FF0FF")


def c_lava_gorilla(pet, bones, cam):
    rest(pet, bones, 0)
    for i, (t0, t1) in enumerate(((0.2, 1.1), (2.0, 2.7))):
        for arm in ("armR", "armL"):
            if arm in bones:
                key(bones[arm], t0, rot=(0, 0, 0))
                key(bones[arm], t1 - 0.3, rot=(-160, 0, 0))
                key(bones[arm], t1, rot=(-150, 0, 0))
                key(bones[arm], t1 + 0.12, rot=(30, 0, 0))
                key(bones[arm], t1 + 0.6, rot=(0, 0, 0))
        key(pet, t0, loc=(0, 0, 0), scale=1)
        key(pet, t1, loc=(0, 0, 0.9), scale=(0.95, 0.95, 1.1))
        key(pet, t1 + 0.12, loc=(0, 0, 0), scale=(1.12, 1.12, 0.85))
        key(pet, t1 + 0.5, loc=(0, 0, 0), scale=1)
        cr = hidden_prop("FX Lava Cracks", f"cracks{i}")
        key(cr, t1 + 0.1, loc=(0, 0.5, 0.02), rot=(0, 0, i * 40), scale=0.2, alpha=0)
        key(cr, t1 + 0.35, scale=1.3 + i * 0.5, alpha=0)
        key(cr, 4.4, scale=1.4 + i * 0.5, alpha=0.2)
        key(cr, 4.8, alpha=1)
        ev(t1 + 0.12, "shake:2.2")
        ev(t1 + 0.12, "burst:FF5A1C:60")
        ev(t1 + 0.12, "shock:FF7A1C")
    shot(cam, 0, (2, 7, 1.5), (0, 0, 2))
    shot(cam, 1.2, (5, 8, 4), (0, 0, 1))
    shot(cam, 2.8, (-4, 8, 6), (0, 0, 0.5))
    shot(cam, 4.8, (3, 8, 2.8), (0, 0, 1.5))
    ev(1.2, "sound:Legendary")
    ev(3.0, "pillar:FF5A1C")


def c_alien_cat(pet, bones, cam):
    rest(pet, bones, 0)
    ufo = hidden_prop("FX UFO", "ufo")
    key(ufo, 0.0, loc=(6, -4, 14), rot=(10, 0, 0), scale=0.01, alpha=1)
    key(ufo, 0.15, scale=1.0, alpha=0)
    key(ufo, 1.0, loc=(0, 0, 6.0), rot=(0, 0, 360))
    key(ufo, 3.3, loc=(0, 0, 6.2), rot=(0, 0, 1440))
    key(ufo, 3.9, loc=(0, 0, 6.0), rot=(0, 0, 1700))
    key(ufo, 4.5, loc=(-8, 6, 18), rot=(-15, 0, 2000), scale=0.3, alpha=0)
    key(ufo, 4.6, scale=0.01, alpha=1)
    beam = hidden_prop("FX UFO Beam", "beam")
    key(beam, 1.0, loc=(0, 0, 5.8), scale=(0.2, 0.2, 1.0), alpha=1)
    key(beam, 1.25, scale=1.0, alpha=0.2)
    key(beam, 3.3, scale=1.0, alpha=0.2)
    key(beam, 3.5, scale=(0.2, 0.2, 1.0), alpha=1)
    key(pet, 1.3, loc=(0, 0, 0), rot=(0, 0, 0), scale=1)
    key(pet, 2.4, loc=(0, 0, 4.9), rot=(25, 0, 540), scale=0.45)
    key(pet, 2.5, loc=(0, 0, 5.4), scale=0.01, alpha=1)
    key(pet, 2.9, loc=(0, 0, 5.4), scale=0.01, alpha=1)
    key(pet, 3.0, loc=(0, 0, 4.9), rot=(0, 0, 720), scale=0.45, alpha=0)
    key(pet, 3.5, loc=(0, 0, 0.3), rot=(0, 0, 1080), scale=1.0)
    key(pet, 3.7, loc=(0, 0, 0), rot=(0, 0, 1080), scale=(1.15, 1.15, 0.8))
    key(pet, 4.0, loc=(0, 0, 0), rot=(0, 0, 1080), scale=1)
    key(pet, 4.8, loc=(0, 0, 0), rot=(0, 0, 1080), scale=1, alpha=0)
    shot(cam, 0, (3, 9, 1.5), (0, 0, 3))
    shot(cam, 2.4, (2, 10, 2.5), (0, 0, 4.5))
    shot(cam, 4.8, (3, 7.5, 2.6), (0, 0, 1.4))
    ev(1.0, "sound:Rare")
    ev(1.1, "burst:B8FF4A:40")
    ev(2.5, "flash:B8FF4A:0.5")
    ev(3.7, "shake:1.2")
    ev(3.7, "burst:B8FF4A:50")
    ev(4.2, "pillar:B8FF4A")


def c_diamond_elephant(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.2, rot=(0, 0, 0))
        key(bones["head"], 0.8, rot=(30, 0, 0))
        key(bones["head"], 2.9, rot=(30, 0, 0))
        key(bones["head"], 3.4, rot=(0, 0, 0))
    for i in range(10):
        t = 0.9 + i * 0.18
        a = math.radians(-60 + (i * 37) % 120)
        dist = 4 + (i % 3)
        d = hidden_prop("FX Diamond", f"gem{i}")
        key(d, t, loc=(0, 2.4, 2.6), rot=(0, 0, 0), scale=0.01, alpha=0)
        key(d, t + 0.05, scale=1.3)
        key(d, t + 0.45, loc=(math.sin(a) * dist * 0.5, 2.4 + math.cos(a) * dist * 0.5, 5.0 + (i % 2)), rot=(180, 90, 0), scale=1.5)
        key(d, t + 0.9, loc=(math.sin(a) * dist, 2.4 + math.cos(a) * dist, 0.3), rot=(360, 180, 90), scale=1.2)
        key(d, 4.3, loc=(math.sin(a) * dist, 2.4 + math.cos(a) * dist, 0.3), rot=(360, 180, 400), scale=1.0, alpha=0)
        key(d, 4.7, scale=0.01, alpha=1)
        ev(t, "burst:8FF0FF:12")
    shot(cam, 0, (5, 6, 2), (0, 0, 2))
    shot(cam, 1.4, (7, 4, 4), (0, 3, 3))
    shot(cam, 3.0, (-3, 12, 6), (0, 2, 1))
    shot(cam, 4.8, (3.5, 8, 2.8), (0, 0, 1.6))
    ev(0.9, "sound:Legendary")
    ev(0.9, "flash:C8F6FF:0.5")
    ev(3.6, "pillar:5CE6FF")


def c_gummy_bear(pet, bones, cam):
    rest(pet, bones, 0)
    seq = [(0.3, (0, 0, 0), (1.0, 1.0, 1.0)), (0.6, (0, 0, 0), (1.45, 1.45, 0.4)), (0.85, (0, 0, 1.6), (0.75, 0.75, 1.5)),
           (1.25, (0, 0, 2.6), (1.0, 1.0, 1.0)), (1.6, (0, 0, 0), (1.5, 1.5, 0.35)), (1.85, (0, 0, 1.2), (0.8, 0.8, 1.35)),
           (2.15, (0, 0, 1.6), (1, 1, 1)), (2.45, (0, 0, 0), (1.35, 1.35, 0.55)), (2.7, (0, 0, 0.6), (0.9, 0.9, 1.15)),
           (2.95, (0, 0, 0), (1.15, 1.15, 0.85)), (3.2, (0, 0, 0), (0.95, 0.95, 1.06)), (3.45, (0, 0, 0), (1, 1, 1))]
    for i, (t, loc, sc) in enumerate(seq):
        key(pet, t, loc=loc, rot=(0, 0, i * 30 if 2 <= i <= 6 else 0), scale=sc)
    key(pet, 4.8, loc=(0, 0, 0), rot=(0, 0, 0), scale=1)
    shot(cam, 0, (3, 7, 1.6), (0, 0, 1.2))
    shot(cam, 1.6, (2, 8, 2.5), (0, 0, 1.6))
    shot(cam, 4.8, (3, 7.5, 2.4), (0, 0, 1.3))
    for t in (0.6, 1.6, 2.45):
        ev(t, "burst:FF3B5C:35")
        ev(t, "shake:0.8")
        ev(t, "sound:Catch")
    ev(3.5, "pillar:FF3B5C")
    ev(3.5, "flash:FF9AB0:0.4")


def c_galaxy_whale(pet, bones, cam):
    rest(pet, bones, 0)
    for t, z, roll in ((0.4, 0, 0), (1.4, 1.8, 6), (2.4, 3.6, -6), (3.2, 3.8, 0), (4.2, 0.3, 0), (4.6, 0, 0)):
        key(pet, t, loc=(0, 0, z), rot=(roll * 0.5, roll, 0))
    if "tail" in bones:
        for i in range(10):
            key(bones["tail"], 0.4 + i * 0.4, rot=(20 if i % 2 else -20, 0, 0))
    vx = hidden_prop("FX Star Vortex", "vortex")
    key(vx, 0.6, loc=(0, 0, -0.2), rot=(0, 0, 0), scale=0.1, alpha=0)
    key(vx, 1.6, rot=(0, 0, 180), scale=1.3)
    key(vx, 3.4, rot=(0, 0, 720), scale=1.6, alpha=0)
    key(vx, 4.4, rot=(0, 0, 900), scale=2.2, alpha=1)
    shot(cam, 0, (5, 9, 2.5), (0, 0, 1.6))
    shot(cam, 2.4, (6, 8, 0.6), (0, 0, 4))
    shot(cam, 3.4, (-6, 8, 9), (0, 0, 2.5))
    shot(cam, 4.8, (4, 8.5, 2.8), (0, 0, 1.6))
    ev(0.6, "sound:Legendary")
    ev(1.0, "burst:8C7BFF:50")
    ev(2.4, "burst:FFFFFF:60")
    ev(4.3, "pillar:8C7BFF")
    ev(4.3, "shake:1")


def c_nuclear_frog(pet, bones, cam):
    rest(pet, bones, 0)
    for t, s in ((0.3, 1.0), (0.6, 1.25), (0.75, 1.15), (1.0, 1.5), (1.15, 1.4), (1.45, 1.85), (1.6, 1.75), (1.75, 2.05)):
        key(pet, t, loc=(0, 0, 0), scale=(s, s, s * 1.05))
    key(pet, 1.8, scale=0.01, alpha=1)
    key(pet, 2.9, loc=(0, 0, 0.5), scale=0.01, alpha=1)
    key(pet, 3.15, loc=(0, 0, 0.5), scale=1.25, alpha=0)
    key(pet, 3.4, loc=(0, 0, 0), scale=(1.2, 1.2, 0.8))
    key(pet, 3.65, scale=(0.95, 0.95, 1.08))
    key(pet, 3.9, loc=(0, 0, 0), scale=1)
    rest(pet, bones, 4.8)
    for i, t in enumerate((1.8, 2.05)):
        ring = hidden_prop("FX Toxic Ring", f"ring{i}")
        key(ring, t, loc=(0, 0, 0.1), rot=(0, 0, 0), scale=0.3, alpha=0)
        key(ring, t + 0.5, rot=(0, 0, 90), scale=2.4 + i, alpha=0.1)
        key(ring, t + 1.3, rot=(0, 0, 140), scale=3.2 + i, alpha=1)
    shot(cam, 0, (2.5, 6, 1.4), (0, 0, 0.9))
    shot(cam, 1.7, (1.8, 5.5, 2.0), (0, 0, 1.4))
    shot(cam, 2.4, (4, 10, 6), (0, 0, 0.5))
    shot(cam, 4.8, (2.5, 6.5, 2.0), (0, 0, 1.0))
    for t in (0.6, 1.0, 1.45):
        ev(t, "sound:Tick")
    ev(1.8, "flash:6BFF3A:0.85")
    ev(1.8, "burst:6BFF3A:120")
    ev(1.8, "shake:2.2")
    ev(1.8, "sound:Legendary")
    ev(3.15, "burst:B8FF4A:40")
    ev(3.4, "pillar:6BFF3A")


def c_ice_dragon(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.2, 3.4, 45, 0.3)
    key(pet, 0.2, loc=(0, 0, 0), rot=(0, 0, 0))
    key(pet, 0.9, loc=(0, -0.3, 1.6), rot=(-25, 0, 0))
    key(pet, 1.3, loc=(0, 0, 0.2), rot=(10, 0, 0))
    key(pet, 1.45, loc=(0, 0, 0), rot=(0, 0, 0), scale=(1.08, 1.08, 0.9))
    key(pet, 1.8, scale=1)
    key(pet, 3.6, loc=(0, 0, 0), rot=(0, 0, 0))
    if "head" in bones:
        key(bones["head"], 1.4, rot=(0, 0, 0))
        key(bones["head"], 1.8, rot=(-15, 0, 0))
        key(bones["head"], 3.0, rot=(-15, 0, 0))
        key(bones["head"], 3.4, rot=(0, 0, 0))
    ice = hidden_prop("FX Ice Floor", "ice")
    key(ice, 1.45, loc=(0, 0, 0.02), rot=(0, 0, 0), scale=0.1, alpha=0)
    key(ice, 2.2, rot=(0, 0, 25), scale=1.6)
    key(ice, 4.3, scale=1.7, alpha=0)
    key(ice, 4.8, alpha=1)
    shot(cam, 0, (5, 9, 2.5), (0, 0, 1.6))
    shot(cam, 1.4, (3, 9, 3.5), (0, 0, 1.4))
    shot(cam, 3.0, (-7, 8, 8), (0, 0, 0.5))
    shot(cam, 4.8, (4, 8.5, 2.8), (0, 0, 1.6))
    ev(1.45, "shake:2")
    ev(1.45, "burst:C8F6FF:90")
    ev(1.45, "flash:E8FAFF:0.7")
    ev(1.45, "sound:Legendary")
    ev(1.45, "shock:8FF0FF")
    ev(3.6, "pillar:6FF0FF")


def c_cyber_dog(pet, bones, cam):
    rest(pet, bones, 0)
    jet = hidden_prop("FX Jetpack", "jet", pet)
    key(jet, 0.3, loc=(3, -5, 4), rot=(0, 0, 200), scale=0.01, alpha=1)
    key(jet, 0.4, scale=1.0, alpha=0)
    key(jet, 1.2, loc=(0, -0.55, 1.6), rot=(0, 0, 0), scale=1.0)
    key(jet, 4.4, loc=(0, -0.55, 1.6), scale=1.0, alpha=0)
    key(jet, 4.7, scale=0.01, alpha=1)
    key(pet, 1.2, loc=(0, 0, 0), rot=(0, 0, 0), scale=1)
    key(pet, 1.35, scale=(1.1, 1.1, 0.9))
    key(pet, 1.6, scale=1)
    key(pet, 2.4, loc=(0, 0, 2.6), rot=(-10, 0, 180))
    key(pet, 3.3, loc=(0, 0, 3.0), rot=(-10, 0, 360))
    key(pet, 4.0, loc=(0, 0, 0), rot=(0, 0, 360), scale=1)
    key(pet, 4.15, scale=(1.1, 1.1, 0.88))
    key(pet, 4.4, loc=(0, 0, 0), rot=(0, 0, 360), scale=1)
    key(pet, 4.8, loc=(0, 0, 0), rot=(0, 0, 360), scale=1, alpha=0)
    shot(cam, 0, (3, 7, 1.8), (0, 0, 1.3))
    shot(cam, 1.2, (2, 6, 2.0), (0, -0.4, 1.6))
    shot(cam, 3.0, (5, 9, 2.0), (0, 0, 3))
    shot(cam, 4.8, (3, 7.5, 2.4), (0, 0, 1.3))
    ev(1.2, "flash:5CE6FF:0.7")
    ev(1.2, "burst:5CE6FF:60")
    ev(1.2, "sound:Legendary")
    ev(2.0, "burst:FFFFFF:30")
    ev(4.15, "shake:1.2")
    ev(4.2, "pillar:5CE6FF")


def c_cursed_teddy(pet, bones, cam):
    rest(pet, bones, 0)
    aura = hidden_prop("FX Dark Aura", "aura")
    key(aura, 0.2, loc=(0, 0, 0.02), rot=(0, 0, 0), scale=0.1, alpha=0)
    key(aura, 0.8, rot=(0, 0, 90), scale=1.2)
    key(aura, 4.0, rot=(0, 0, 400), scale=1.3, alpha=0)
    key(aura, 4.6, scale=0.01, alpha=1)
    if "head" in bones:
        key(bones["head"], 0.6, rot=(0, 0, 0))
        key(bones["head"], 1.4, rot=(0, 0, 360))
        key(bones["head"], 1.7, rot=(0, 0, 340))
        key(bones["head"], 2.1, rot=(0, 0, 720))
        key(bones["head"], 3.9, rot=(0, 0, 720))
        key(bones["head"], 4.3, rot=(0, 0, 720))
    key(pet, 2.0, loc=(0, 0, 0), rot=(0, 0, 0))
    key(pet, 2.8, loc=(0, 0, 2.2), rot=(180, 0, 30))
    key(pet, 3.5, loc=(0, 0, 2.5), rot=(180, 0, -20))
    key(pet, 4.1, loc=(0, 0, 0.2), rot=(360, 0, 0))
    key(pet, 4.3, loc=(0, 0, 0), rot=(360, 0, 0))
    key(pet, 4.8, loc=(0, 0, 0), rot=(360, 0, 0))
    shot(cam, 0, (2, 6, 1.3), (0, 0, 1.2))
    shot(cam, 1.5, (0.8, 4, 1.6), (0, 0, 1.5))
    shot(cam, 3.0, (2.5, 7, 1.0), (0, 0, 2.6))
    shot(cam, 4.8, (2.5, 6.5, 2.0), (0, 0, 1.1))
    ev(0.4, "flash:FF1A2A:0.4")
    ev(1.4, "sound:Error")
    ev(2.1, "flash:000000:0.6")
    ev(2.1, "burst:FF1A2A:40")
    ev(2.8, "sound:Legendary")
    ev(4.2, "shake:1.4")
    ev(4.2, "pillar:FF1A2A")


def c_emperor_penguin(pet, bones, cam):
    rest(pet, bones, 0)
    throne = hidden_prop("FX Throne", "throne")
    key(throne, 0.3, loc=(0, -1.6, -3.6), rot=(0, 0, 0), scale=1.0, alpha=0)
    key(throne, 1.3, loc=(0, -1.6, 0))
    key(throne, 4.3, loc=(0, -1.6, 0), alpha=0)
    key(throne, 4.7, loc=(0, -1.6, -3.6), alpha=1)
    carpet = hidden_prop("FX Carpet", "carpet")
    key(carpet, 0.5, loc=(0, -0.6, 0.01), scale=(1, 0.01, 1), alpha=0)
    key(carpet, 1.3, scale=1.0)
    key(carpet, 4.3, scale=1.0, alpha=0)
    key(carpet, 4.7, alpha=1)
    key(pet, 1.4, loc=(0, 0, 0), rot=(0, 0, 0))
    key(pet, 1.7, loc=(0, -0.8, 2.0), rot=(0, 0, 90))
    key(pet, 2.0, loc=(0, -1.5, 1.0), rot=(0, 0, 0))
    key(pet, 3.8, loc=(0, -1.5, 1.0), rot=(0, 0, 0))
    key(pet, 4.1, loc=(0, -0.6, 1.4), rot=(0, 0, 0))
    key(pet, 4.35, loc=(0, 0, 0), rot=(0, 0, 0))
    key(pet, 4.8, loc=(0, 0, 0), rot=(0, 0, 0))
    for w, s in (("wingR", -1), ("wingL", 1)):
        if w in bones:
            key(bones[w], 2.1, rot=(0, 0, 0))
            key(bones[w], 2.4, rot=(0, s * 110, 0))
            key(bones[w], 3.2, rot=(0, s * 110, 0))
            key(bones[w], 3.5, rot=(0, 0, 0))
    shot(cam, 0, (0, 8, 1.6), (0, 0, 1.2))
    shot(cam, 1.4, (3, 7, 2.6), (0, -1.2, 1.6))
    shot(cam, 3.0, (0, 6.5, 2.4), (0, -1.5, 2.0))
    shot(cam, 4.8, (2.5, 6.5, 2.0), (0, 0, 1.0))
    ev(0.3, "shake:0.8")
    ev(1.3, "burst:FFC21C:40")
    ev(2.4, "flash:FFD84A:0.6")
    ev(2.4, "burst:FFE45C:80")
    ev(2.4, "sound:Legendary")
    ev(2.5, "pillar:FFC21C")


CINEMATICS = {
    "Rainbow Dragon": c_rainbow_dragon, "Shadow Panther": c_shadow_panther, "Golden Phoenix": c_golden_phoenix,
    "Galaxy Cat": c_galaxy_cat, "Crystal Wolf": c_crystal_wolf, "Lava Gorilla": c_lava_gorilla, "Alien Cat": c_alien_cat,
    "Diamond Elephant": c_diamond_elephant, "Gummy Bear": c_gummy_bear, "Galaxy Whale": c_galaxy_whale,
    "Nuclear Frog": c_nuclear_frog, "Ice Dragon": c_ice_dragon, "Cyber Dog": c_cyber_dog, "Cursed Teddy": c_cursed_teddy,
    "Emperor Penguin": c_emperor_penguin,
}


# ---------------------------------------------------------------- export
def rb_pos(v):
    return (v[0], v[2], -v[1])


def rb_rot(R, camera=False):
    return mm(C, R) if camera else mm(mm(C, R), CT)


def r(v, n=3):
    return round(v, n) if abs(v) > 1e-9 else 0


def frame_cf(mw, camera=False):
    loc, rot, scale = mw.decompose()
    R = [list(row) for row in rot.to_matrix()]
    RR = rb_rot(R, camera)
    p = rb_pos(loc)
    return [r(p[0]), r(p[1]), r(p[2])] + [r(RR[i][j], 4) for i in range(3) for j in range(3)], (scale[0], scale[2], scale[1])


def lua(v):
    if isinstance(v, dict):
        return "{" + ", ".join(f'["{k}"] = {lua(x)}' for k, x in v.items()) + "}"
    if isinstance(v, (list, tuple)):
        return "{" + ",".join(lua(x) for x in v) + "}"
    if isinstance(v, str):
        return '"' + v + '"'
    if isinstance(v, float):
        return repr(round(v, 4))
    return str(v)


os.makedirs(os.path.join(OUT, "cinematics"), exist_ok=True)
os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)
for name, fn in CINEMATICS.items():
    if ONLY and name not in ONLY:
        continue
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _mats.clear()
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 0, NF
    pet, bones = build(name, "PET", rig=True)
    cam = bpy.data.objects.new("CAM", bpy.data.cameras.new("CAM"))
    sc.collection.objects.link(cam)
    cam.data.lens = 32
    sc.camera = cam
    fn(pet, bones, cam)
    props = [ob for ob in sc.objects if ob.get("alpha") is not None and ob is not pet and ob.type == "EMPTY" and ":" not in ob.name]
    pet_frames, bone_frames, cam_frames = [], {b: [] for b in bones}, []
    prop_frames = {ob.name: [] for ob in props}
    for f in range(0, NF + 1, STEP):
        sc.frame_set(f)
        cf, s = frame_cf(pet.matrix_world)
        pet_frames += cf + [r(s[0]), r(s[1]), r(s[2]), r(pet.get("alpha", 0.0))]
        for b, ob in bones.items():
            R = [list(row) for row in ob.matrix_basis.to_3x3().normalized()]
            RR = rb_rot(R)
            bone_frames[b] += [r(RR[i][j], 4) for i in range(3) for j in range(3)]
        for ob in props:
            cf, s = frame_cf(ob.matrix_world)
            prop_frames[ob.name] += cf + [r((s[0] + s[1] + s[2]) / 3), r(ob.get("alpha", 0.0))]
        cf, _ = frame_cf(cam.matrix_world, camera=True)
        cam_frames += cf
    events = []
    for mk in sorted(sc.timeline_markers, key=lambda m: m.frame):
        parts = mk.name.split(":")
        events.append([r(mk.frame / FPS), *parts])
    # only bones that actually move
    bone_frames = {b: v for b, v in bone_frames.items() if any(abs(v[i] - v[i % 9]) > 1e-3 for i in range(len(v)))}
    data = {
        "Length": LEN, "Fps": FPS / STEP, "Pet": pet_frames, "Bones": bone_frames,
        "Props": [{"Model": ob["model"], "F": prop_frames[ob.name]} for ob in props],
        "Camera": cam_frames, "Events": events,
    }
    src = f"-- Generated by blender/cinematics.py: the {name} catch cinematic (do not edit by hand).\nreturn " + lua(data) + "\n"
    path = os.path.join(OUT, "cinematics", name.replace(" ", "") + ".luau")
    open(path, "w").write(src)
    print(f"{name:18s} props={len(props):2d} bones={len(bone_frames)} events={len(events)} {len(src) // 1024}KB")
    if RENDER:
        sc.render.engine = "BLENDER_EEVEE"
        sc.render.resolution_x, sc.render.resolution_y = 480, 270
        w = bpy.data.worlds.new("W")
        w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.75, 1.0, 1)
        sc.world = w
        sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
        sun.data.energy = 3
        sun.rotation_euler = (math.radians(40), 0, math.radians(35))
        sc.collection.objects.link(sun)
        gm = bpy.data.meshes.new("G")
        gm.from_pydata([(-60, -60, 0), (60, -60, 0), (60, 60, 0), (-60, 60, 0)], [], [(0, 1, 2, 3)])
        gm.materials.append(mat("62C846", "plastic"))
        sc.collection.objects.link(bpy.data.objects.new("Ground", gm))
        for k, t in enumerate((0.6, 1.5, 2.4, 3.4)):
            sc.frame_set(round(t * FPS))
            for ob in sc.objects:  # preview the fades: hide anything mostly transparent
                if ob.type == "MESH" and ob.parent is not None:
                    host = ob.parent
                    while host.parent is not None and host.get("alpha") is None:
                        host = host.parent
                    ob.hide_render = host.get("alpha", 0.0) > 0.6
            sc.render.filepath = os.path.join(OUT, "renders", f"cine_{name.replace(' ', '')}_{k}.png")
            bpy.ops.render.render(write_still=True)
        # 2x2 contact sheet of the four frames for review
        W, H = 480, 270
        sheet = bpy.data.images.new("sheet", W * 2, H * 2)
        px = [0.0] * (W * 2 * H * 2 * 4)
        for k in range(4):
            fp = os.path.join(OUT, "renders", f"cine_{name.replace(' ', '')}_{k}.png")
            im = bpy.data.images.load(fp)
            src = list(im.pixels)
            ox, oy = (k % 2) * W, (1 - k // 2) * H  # Blender images start bottom-left
            for y in range(H):
                row = src[y * W * 4:(y + 1) * W * 4]
                i0 = ((oy + y) * W * 2 + ox) * 4
                px[i0:i0 + W * 4] = row
            os.remove(fp)
        sheet.pixels = px
        sheet.filepath_raw = os.path.join(OUT, "renders", f"cine_{name.replace(' ', '')}.png")
        sheet.file_format = "PNG"
        sheet.save()
print("CINEMATICS DONE")
