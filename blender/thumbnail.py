# Game thumbnail (1920x1080): the game's own brick pets in the yard, a player mid-throw, big title.
# Run: blender --background build/ThrowAToy_pets.blend --python blender/thumbnail.py -- <out.png>
import bpy, math, os, sys
from mathutils import Vector

OUT = sys.argv[sys.argv.index("--") + 1]
sc = bpy.context.scene
rnd_state = [7]


def rnd():  # tiny deterministic RNG so re-renders match
    rnd_state[0] = (rnd_state[0] * 1103515245 + 12345) % 2**31
    return rnd_state[0] / 2**31


# ---- keep only the pets we pose; hide every other model ----
HERO = {}
for ob in bpy.data.objects:
    if ob.parent is None and ob.type == "EMPTY":
        HERO[ob.name] = ob
for ob in bpy.data.objects:
    ob.hide_render = True


def bounds(root):
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    bpy.context.view_layer.update()
    for ch in root.children:
        for c in ch.bound_box:
            w = ch.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w))
            hi = Vector(map(max, hi, w))
    return lo, hi


def pose(name, x, y, height, yaw=0.0, z=0.0, tilt=0.0):
    """Show a model, scale it to `height`, stand it on z at (x, y), facing +Y rotated by yaw (deg)."""
    r = HERO[name]
    r.hide_render = False
    for ch in r.children:
        ch.hide_render = False
    r.location, r.scale = (0, 0, 0), (1, 1, 1)
    r.rotation_euler = (math.radians(tilt), 0, math.radians(yaw))
    lo, hi = bounds(r)
    s = height / max(hi.z - lo.z, 1e-3)
    r.scale = (s, s, s)
    lo, hi = bounds(r)
    r.location = (x - (lo.x + hi.x) / 2, y - (lo.y + hi.y) / 2, z - lo.z)
    return r


# ---- materials ----
_m = {}


def mat(hexc, emit=0.0, alpha=1.0, rough=0.55):
    key = (hexc, emit, alpha)
    if key in _m:
        return _m[key]
    m = bpy.data.materials.new(f"T_{hexc}_{emit}_{alpha}")
    b = m.node_tree.nodes["Principled BSDF"]
    lin = [(int(hexc[i:i + 2], 16) / 255) ** 2.2 for i in (0, 2, 4)]
    b.inputs["Base Color"].default_value = (*lin, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*lin, 1)
        b.inputs["Emission Strength"].default_value = emit
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    _m[key] = m
    return m


def box(name, size, loc, color, rot=(0, 0, 0), **kw):
    me = bpy.data.meshes.new(name)
    h = [v / 2 for v in size]
    me.from_pydata([(a * h[0], b * h[1], c * h[2]) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)], [],
                   [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    me.materials.append(mat(color, **kw))
    ob = bpy.data.objects.new(name, me)
    ob.location, ob.rotation_euler = loc, [math.radians(a) for a in rot]
    sc.collection.objects.link(ob)
    return ob


def ball(name, r, loc, color, **kw):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=32, ring_count=16)
    ob = bpy.context.object
    ob.name = name
    bpy.ops.object.shade_smooth()
    ob.data.materials.append(mat(color, **kw))
    return ob


# ---- the yard: checker floor, terraced walls, runway out the back ----
for i in range(-9, 10):
    for j in range(-6, 9):
        box("Floor", (6, 6, 1), (i * 6, j * 6 - 18, -0.5), "62CE48" if (i + j) % 2 == 0 else "52BA3E")
for j in range(9, 40):  # runway into the distance
    for i in range(-2, 2):
        box("Runway", (6, 6, 1), (i * 6 + 3, -j * 6 - 18 + 36, -0.5), "7ADC5A" if (i + j) % 2 == 0 else "6CCC4E")
box("CenterLine", (0.35, 190, 0.08), (0, -110, 0.02), "FFFFFF", emit=3)
box("ThrowLine", (24, 1.0, 0.1), (0, -16, 0.04), "FFFFFF", emit=4)
for k in range(-2, 2):
    for r in range(2):
        box("Launch", (6, 2, 0.12), (k * 6 + 3, -12 - r * 2, 0.04), "FF9A2E" if (k + r) % 2 == 0 else "FFB54A")
for side in (-1, 1):
    for j in range(40):  # canyon walls along the runway
        y = -18 - j * 6
        h = 6 + rnd() * 4
        box("Ledge", (5, 6, h), (side * 14.5, y, h / 2), "96623C")
        box("LedgeTop", (5.3, 6.1, 0.9), (side * 14.5, y, h + 0.45), "7BDC50")
        h2 = 13 + rnd() * 7
        box("Cliff", (10, 6, h2), (side * 22, y, h2 / 2), "8A5A36")
        box("CliffTop", (10.3, 6.1, 1.1), (side * 22, y, h2 + 0.55), "6FD048")
        if rnd() < 0.45:  # blocky tree on the cliff
            tx = side * (19 + rnd() * 6)
            box("Trunk", (1, 1, 3), (tx, y, h2 + 2.5), "7A4A22")
            box("Leaves", (4, 4, 3.4), (tx, y, h2 + 5.4), "4CC84A")
            box("Leaves2", (2.6, 2.6, 1.6), (tx, y, h2 + 7.7), "5CD85A")
    for j in range(6):  # yard side walls near the camera
        h = 9 + rnd() * 4
        box("YardWall", (6, 6, h), (side * (13 + j * 6), -15, h / 2), "96623C")
        box("YardTop", (6.2, 6.2, 1), (side * (13 + j * 6), -15, h + 0.5), "7BDC50")
for side in (-1, 1):  # title arch over the runway mouth
    box("Pillar", (1.6, 1.6, 17), (side * 12, -16, 8.5), "FF8A1C")
box("ArchBoard", (26, 3, 1), (0, -16, 17.5), "FF5CA8")
box("ArchTrim", (26.4, 0.4, 1.2), (0, -16, 16), "FFD23C")
box("ArchTrim", (26.4, 0.4, 1.2), (0, -16, 19), "FFD23C")

# ---- the player: original blocky avatar, mid-throw ----
px, py = -7.5, 3.0
P = lambda name, size, loc, c, rot=(0, 0, 0): box(name, size, (px + loc[0], py + loc[1], loc[2]), c, rot)
SKIN, SHIRT, PANTS, SHOE = "FFCC99", "2F7BE8", "3A3A48", "1E1E26"
P("LegL", (0.95, 1, 2.1), (-0.5, -0.35, 1.05), PANTS, (18, 0, 0))
P("LegR", (0.95, 1, 2.1), (0.5, 0.45, 1.05), PANTS, (-22, 0, 0))
P("Torso", (2, 1, 2.1), (0, 0, 3.15), SHIRT, (0, 0, 12))
P("Stripe", (2.05, 1.05, 0.35), (0, 0, 3.4), "FFFFFF", (0, 0, 12))
P("Head", (1.25, 1.2, 1.2), (0, 0, 4.85), SKIN, (0, 0, 12))
P("Hair", (1.35, 1.3, 0.45), (0, 0.05, 5.55), "4A2A14", (0, 0, 12))
for ex in (-0.28, 0.28):
    P("Eye", (0.18, 0.05, 0.3), (ex + 0.07, -0.61, 4.95), "111111", (0, 0, 12))
P("Smile", (0.55, 0.05, 0.1), (0.1, -0.61, 4.55), "111111", (0, 0, 12))
P("ArmL", (0.95, 0.95, 2.0), (-1.45, -0.1, 3.0), SKIN, (25, 0, -8))
P("ArmR", (0.95, 0.95, 2.0), (1.35, -0.55, 4.6), SKIN, (-150, 0, 20))  # thrown arm up and forward
# the toy: tennis ball flying off toward the runway, with a speed trail
toy = pose("Tennis Ball", 1.5, -14, 2.2, yaw=0, z=10.5)
for k in range(1, 9):  # trail back toward the hand
    t = k / 9
    ball("Trail", 1.0 * (1 - t * 0.7), (px + 1.3 + (1.5 - px - 1.3) * (1 - t), py - 0.8 + (-14 - py + 0.8) * (1 - t), 6.2 + (11.6 - 6.2) * (1 - t) + 2.2 * math.sin(math.pi * (1 - t))),
         "FFF7C8", emit=2.5, alpha=0.55 * (1 - t))

# ---- the stars: Secret / exclusive pets around the yard ----
pose("Rainbow Dragon", 8.5, 1, 7.2, yaw=-28)
pose("Void Kitsune", 3.2, 5, 3.6, yaw=-10)
pose("Golden Phoenix", -2, -9, 3.6, yaw=20, z=13, tilt=-10)
pose("Galaxy Cat", -13.5, 4.5, 3.2, yaw=30)
pose("Dog", -2.6, 6.8, 2.0, yaw=-5)
pose("Rainbow Pegacorn", 15.5, -6, 5.0, yaw=-40)
pose("World Ender", -15, -30, 13, yaw=25)
for k, (x, y, z, c) in enumerate(((5, -2, 9, "FFE45C"), (-11, -5, 11, "FF78E6"), (12, 6, 10, "78E6FF"), (-4, 1, 12.5, "FFFFFF"))):
    box("Sparkle", (0.7, 0.7, 0.7), (x, y, z), c, rot=(45, 45, 0), emit=6)

# ---- light, sky, camera ----
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.film_transparent = False
w = bpy.data.worlds.new("Sky")
nt = w.node_tree
bg = nt.nodes["Background"]
bg.inputs["Color"].default_value = (0.32, 0.62, 1.0, 1)
bg.inputs["Strength"].default_value = 1.0
sc.world = w
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy, sun.data.angle = 4.2, math.radians(8)
sun.rotation_euler = (math.radians(48), math.radians(-12), math.radians(-35))
sc.collection.objects.link(sun)
fill = bpy.data.objects.new("Fill", bpy.data.lights.new("Fill", "SUN"))
fill.data.energy = 1.2
fill.rotation_euler = (math.radians(60), 0, math.radians(150))
sc.collection.objects.link(fill)

cam = bpy.data.objects.new("ThumbCam", bpy.data.cameras.new("ThumbCam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 30
cam.location = (0, 26, 7.5)
tgt = Vector((0, -6, 6.5))
cam.rotation_euler = (tgt - cam.location).to_track_quat("-Z", "Y").to_euler()

# ---- title, locked to the camera ----
FONT = bpy.data.fonts.load(r"C:\Windows\Fonts\ariblk.ttf")


def title(text, y, size, face, edge, rot=0.0):
    for k, (col, off, depth, z) in enumerate(((edge, 0.035, 0.03, -0.03), (face, 0.0, 0.06, 0.0))):
        cu = bpy.data.curves.new(f"Title{k}", "FONT")
        cu.body, cu.font, cu.size, cu.align_x, cu.align_y = text, FONT, size, "CENTER", "CENTER"
        cu.offset, cu.extrude, cu.bevel_depth = off, depth, 0.012
        ob = bpy.data.objects.new(f"Title{k}", cu)
        ob.data.materials.append(mat(col, emit=0.35 if k else 0, rough=0.35))
        sc.collection.objects.link(ob)
        ob.parent = cam
        ob.location = (0, y, -4 + z)
        ob.rotation_euler = (0, 0, math.radians(rot))


title("THROW A TOY!", 0.92, 0.46, "FFD23C", "1A2A6C", rot=3)
title("CATCH SECRET PETS!", 0.5, 0.17, "FFFFFF", "1A2A6C", rot=3)

sc.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("THUMB", OUT)
