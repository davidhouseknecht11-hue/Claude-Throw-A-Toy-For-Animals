# Builds the brick pets in Blender, renders review shots, exports models.json (+ .blend, FBX).
# Run: blender --background --factory-startup --python build_pets.py -- <out_dir> <studs.png> [render] [only=Group,..]
import bpy, json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import brick  # noqa: E402
import pets  # noqa: F401,E402  (registers models)

args = sys.argv[sys.argv.index("--") + 1:]
OUT, STUDS = args[0], args[1]
RENDER = "render" in args
ONLY = sum([a[5:].split(",") for a in args if a.startswith("only=")], [])
os.makedirs(os.path.join(OUT, "renders"), exist_ok=True)
os.makedirs(os.path.join(OUT, "fbx"), exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
STUD_IMG = bpy.data.images.load(STUDS)
_mats = {}


def mat(hexc, kind):
    key = hexc + kind
    if key in _mats:
        return _mats[key]
    m = bpy.data.materials.new(key)
    rgb = [int(hexc[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    lin = [c ** 2.2 for c in rgb]
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.5
    if kind == "neon":
        bsdf.inputs["Base Color"].default_value = (*lin, 1)
        bsdf.inputs["Emission Color"].default_value = (*lin, 1)
        bsdf.inputs["Emission Strength"].default_value = 2.5
    else:
        tc, mp, tex, mix = (nt.nodes.new(t) for t in ("ShaderNodeTexCoord", "ShaderNodeMapping", "ShaderNodeTexImage", "ShaderNodeMix"))
        mp.inputs["Scale"].default_value = (4.0,) * 3  # 4 studs per stud-unit: fine studs like the reference pets
        tex.image, tex.projection = STUD_IMG, "BOX"
        mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        mix.inputs["A"].default_value = (*lin, 1)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        nt.links.new(mp.outputs["Vector"], tex.inputs["Vector"])
        nt.links.new(tex.outputs["Color"], mix.inputs["B"])
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Base Color"])
        if kind == "glass":
            bsdf.inputs["Alpha"].default_value = 0.6
            bsdf.inputs["Roughness"].default_value = 0.08
    _mats[key] = m
    return m


def cube_mesh(name, sx, sy, sz):
    me = bpy.data.meshes.new(name)
    h = (sx / 2, sy / 2, sz / 2)
    v = [(a * h[0], b * h[1], c * h[2]) for a in (-1, 1) for b in (-1, 1) for c in (-1, 1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    me.from_pydata(v, [], f)
    return me


models = [m for m in brick.MODELS if not ONLY or m.group in ONLY]
export = {}
for m in models:
    root = bpy.data.objects.new(m.name, None)
    bpy.context.scene.collection.objects.link(root)
    for i, bx in enumerate(m.boxes):
        me = cube_mesh(f"{m.name}_{i}", *bx["size"])
        me.materials.append(mat(bx["color"], bx["kind"]))
        ob = bpy.data.objects.new(f"{m.name}_{bx['bone']}_{i}", me)
        ob.location = bx["pos"]
        if bx["rot"]:
            ob.rotation_euler = tuple(math.radians(a) for a in bx["rot"])
        ob.parent = root
        bpy.context.scene.collection.objects.link(ob)
    export[m.name] = m.export()
    print(f"{m.name:14s} bricks={len(m.boxes)}")

if not ONLY:
    with open(os.path.join(OUT, "models.json"), "w") as f:
        json.dump(export, f)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "ThrowAToy_pets.blend"))
    for m in models:
        bpy.ops.object.select_all(action="DESELECT")
        for ob in bpy.data.objects[m.name].children:
            ob.select_set(True)
        bpy.ops.export_scene.fbx(filepath=os.path.join(OUT, "fbx", m.name.replace(" ", "") + ".fbx"), use_selection=True)
if not RENDER:
    raise SystemExit

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.view_settings.view_transform = "Standard"
sc.render.resolution_x, sc.render.resolution_y = 1600, 900
w = bpy.data.worlds.new("Sky")
w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.86, 0.88, 0.92, 1)
w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.85
sc.world = w
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy, sun.data.angle = 2.6, math.radians(25)
sun.rotation_euler = (math.radians(40), 0, math.radians(35))
sc.collection.objects.link(sun)
gm = bpy.data.meshes.new("Ground")
gm.from_pydata([(-300, -300, 0), (300, -300, 0), (300, 300, 0), (-300, 300, 0)], [], [(0, 1, 2, 3)])
gmat = bpy.data.materials.new("G")
gmat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.62, 0.66, 0.72, 1)
gmat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
gm.materials.append(gmat)
sc.collection.objects.link(bpy.data.objects.new("Ground", gm))
cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
sc.collection.objects.link(cam)
sc.camera = cam
cam.data.lens = 45


def extent(name):
    xs, zs = [], []
    for bx in brick.MODELS[[mm.name for mm in brick.MODELS].index(name)].boxes:
        xs += [bx["pos"][0] - bx["size"][0] / 2, bx["pos"][0] + bx["size"][0] / 2]
        zs.append(bx["pos"][2] + bx["size"][2] / 2)
    return max(xs) - min(xs), max(zs)


groups = {}
for m in models:
    groups.setdefault(m.group, []).append(m.name)
for g in list(groups):  # big groups review in sheets of 8 so each model is large enough to judge
    names = groups[g]
    if len(names) > 10:
        del groups[g]
        for k in range(0, len(names), 8):
            groups[f"{g}_{k // 8}"] = names[k:k + 8]
for g, names in groups.items():
    roots = [bpy.data.objects[n] for n in names]
    for ob in bpy.data.objects:
        if ob.parent is not None:
            ob.hide_render = ob.parent not in roots
    ws = [extent(n)[0] + 1.0 for n in names]
    hmax = max(extent(n)[1] for n in names)
    x = sum(ws) / 2
    for r, wd in zip(roots, ws):  # lay out right->left so the camera (front-left) sees them in order
        r.location = (x - wd / 2, 0, 1.0 if g == "Toys" else 0)
        x -= wd
    total = sum(ws)
    dist = max(total * 1.0, hmax * 2.8) + 3
    cam.location = (-dist * 0.5, dist * 0.85, dist * 0.32 + hmax * 0.35)
    tgt = (0, 0, hmax * 0.42)
    d = [tgt[i] - cam.location[i] for i in range(3)]
    cam.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
    sc.render.filepath = os.path.join(OUT, "renders", f"p_{g}.png")
    bpy.ops.render.render(write_still=True)
    for r in roots:
        r.location = (0, 0, 0)
print("RENDERED")
