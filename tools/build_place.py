# Builds ThrowAToy.rbxlx: dense map, brick pets (+rig module), scripts, sounds, lighting, studded MaterialVariants.
# Run: python tools/build_place.py      (reads build/models.json from blender/build_pets.py, src/, assets.json)
import json, math, os, random
from xml.sax.saxutils import escape

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = lambda *a: os.path.join(ROOT, *a)

ASSETS = json.load(open(P("assets.json")))
MODELS = json.load(open(P("build", "models.json")))

# ---------------- XML helpers ----------------
_ref = [0]


def ref():
    _ref[0] += 1
    return f"RBX{_ref[0]:08X}"


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shade(h, f):
    return "".join(f"{max(0, min(255, int(c * f))):02X}" for c in rgb(h))


def c3u8(c):
    r, g, b = rgb(c)
    return 0xFF000000 | (r << 16) | (g << 8) | b


def yrot(a):
    c, s = math.cos(a), math.sin(a)
    return (c, 0, s, 0, 1, 0, -s, 0, c)


def cf_xml(name, pos, R):
    x, y, z = pos
    return (f'<CoordinateFrame name="{name}"><X>{x:.4f}</X><Y>{y:.4f}</Y><Z>{z:.4f}</Z>'
            + "".join(f"<R{i // 3}{i % 3}>{v:.6f}</R{i // 3}{i % 3}>" for i, v in enumerate(R)) + "</CoordinateFrame>")


class Item:
    def __init__(self, cls, name):
        self.cls, self.ref, self.children, self.props = cls, ref(), [], []
        self.str("Name", name)

    def add(self, child):
        self.children.append(child)
        return child

    def str(self, k, v):
        self.props.append(f'<string name="{k}">{escape(v)}</string>')
        return self

    def raw(self, s):
        self.props.append(s)
        return self

    def xml(self, out):
        out.append(f'<Item class="{self.cls}" referent="{self.ref}"><Properties>')
        out.extend(self.props)
        out.append("</Properties>")
        for ch in self.children:
            ch.xml(out)
        out.append("</Item>")


MAT = {"plastic": 256, "smooth": 272, "neon": 288, "glass": 1568, "wood": 512}
COUNT = [0]


def part(name, size, pos, color, kind="plastic", rot=0.0, R=None, collide=True, variant="Studs", transparency=0.0, cls="Part", shadow=True, query=True):
    COUNT[0] += 1
    p = Item(cls, name)
    p.raw('<bool name="Anchored">true</bool>').raw(cf_xml("CFrame", pos, R or yrot(rot)))
    p.raw(f'<bool name="CanCollide">{str(collide).lower()}</bool>')
    if not query:
        p.raw('<bool name="CanQuery">false</bool>').raw('<bool name="CanTouch">false</bool>')
    p.raw(f'<bool name="CastShadow">{str(shadow).lower()}</bool>')
    p.raw(f'<Color3uint8 name="Color3uint8">{c3u8(color)}</Color3uint8>')
    p.raw(f'<token name="Material">{MAT[kind]}</token>')
    if kind == "plastic" and variant:
        p.str("MaterialVariantSerialized", variant)
    if kind == "glass" and transparency == 0:
        transparency = 0.35
    p.raw(f'<float name="Transparency">{transparency}</float>')
    sx, sy, sz = size
    p.raw(f'<Vector3 name="size"><X>{sx:.3f}</X><Y>{sy:.3f}</Y><Z>{sz:.3f}</Z></Vector3>')
    for f in ("Top", "Bottom", "Front", "Back", "Left", "Right"):
        p.raw(f'<token name="{f}Surface">0</token>')
    return p


def content(name, url):
    return f'<Content name="{name}"><url>{escape(url)}</url></Content>' if url else f'<Content name="{name}"><null></null></Content>'


def script_src(cls, name, src):
    assert "]]>" not in src
    s = Item(cls, name)
    s.raw(f'<ProtectedString name="Source"><![CDATA[{src}]]></ProtectedString>')
    return s


def script(cls, name, path):
    return script_src(cls, name, open(path, encoding="utf-8").read())


def color3(name, c):
    r, g, b = rgb(c)
    return f'<Color3 name="{name}"><R>{r / 255:.4f}</R><G>{g / 255:.4f}</G><B>{b / 255:.4f}</B></Color3>'


def tf(origin, rot, lx, ly, lz):
    c, s = math.cos(rot), math.sin(rot)
    ox, oy, oz = origin
    return (ox + lx * c + lz * s, oy + ly, oz - lx * s + lz * c)


# ---------------- ZONES (mirror Config.luau) ----------------
ZONES = [
    dict(name="Backyard", floor="62CE48", wall="96623C", top="78DC50", theme="backyard"),
    dict(name="Farm", floor="E0C46E", wall="B04034", top="F0D25A", theme="farm"),
    dict(name="Jungle", floor="2E9646", wall="5A6E44", top="28AF50", theme="jungle"),
    dict(name="Safari", floor="E8BE6E", wall="C47840", top="CDB450", theme="safari"),
    dict(name="Arctic", floor="ECF6FF", wall="8CC4F0", top="FFFFFF", theme="arctic"),
    dict(name="Fantasy", floor="7850D2", wall="3C2878", top="FF78E6", theme="fantasy"),
]
CORRIDOR_START, ZONE_LEN, HALF_W = -72, 230, 34
END_Z = CORRIDOR_START - ZONE_LEN * len(ZONES)
rnd = random.Random(42)

workspace = Item("Workspace", "Workspace")
mapm = workspace.add(Item("Model", "Map"))


# ---------------- PROPS ----------------
def tree(g, x, z, y=0.0, trunk="7A4A22", leaf="4CC84A", h=8, w=7):
    g.add(part("Trunk", (1.6, h, 1.6), (x, y + h / 2, z), trunk))
    g.add(part("Branch", (2.6, 0.9, 0.9), (x + 1.1, y + h * 0.7, z), trunk))
    shades = (1.0, 0.88, 1.12)
    for i, (dx, dy, dz, s) in enumerate(((0, 0.2, 0, 1.0), (w * 0.3, w * 0.35, -w * 0.15, 0.7), (-w * 0.35, w * 0.15, w * 0.2, 0.65),
                                         (w * 0.1, w * 0.62, w * 0.1, 0.55), (w * 0.4, -w * 0.05, w * 0.3, 0.5))):
        g.add(part("Leaves", (w * s, w * 0.62 * s, w * s), (x + dx, y + h + dy + w * 0.2, z + dz), shade(leaf, shades[i % 3])))


def bush(g, x, z, y=0.0, c="3FB040", s=3.0):
    g.add(part("Bush", (s, s * 0.7, s), (x, y + s * 0.35, z), c))
    g.add(part("Bush", (s * 0.6, s * 0.5, s * 0.6), (x + s * 0.4, y + s * 0.6, z), shade(c, 1.12)))
    g.add(part("Bush", (s * 0.5, s * 0.45, s * 0.5), (x - s * 0.35, y + s * 0.4, z + s * 0.3), shade(c, 0.9)))


def rock(g, x, z, y=0.0, c="9A9AA6", s=3.0):
    g.add(part("Rock", (s, s * 0.6, s * 0.8), (x, y + s * 0.3, z), c, rot=rnd.uniform(0, 1.5)))
    g.add(part("Rock", (s * 0.6, s * 0.5, s * 0.6), (x + s * 0.3, y + s * 0.7, z + 0.3), shade(c, 1.1), rot=rnd.uniform(0, 1.5)))


def flowers(g, x, z, y=0.0, n=4):
    for _ in range(n):
        c = rnd.choice(["FF5C8A", "FFD23C", "FFFFFF", "B46CFF", "FF8A3C"])
        dx, dz = rnd.uniform(-2, 2), rnd.uniform(-2, 2)
        g.add(part("Stem", (0.25, 1.0, 0.25), (x + dx, y + 0.5, z + dz), "3C9A3C", collide=False, query=False))
        g.add(part("Flower", (0.8, 0.5, 0.8), (x + dx, y + 1.2, z + dz), c, collide=False, query=False))


def theme_prop(g, theme, x, z, y=0.0):
    r = rnd.random()
    if theme == "backyard":
        if r < 0.45:
            tree(g, x, z, y, h=rnd.uniform(6, 10), w=rnd.uniform(6, 9))
        elif r < 0.75:
            bush(g, x, z, y)
        else:
            flowers(g, x, z, y)
    elif theme == "farm":
        if r < 0.3:
            g.add(part("Hay", (4, 3, 4), (x, y + 1.5, z), "F2CC52"))
            g.add(part("HayBand", (4.1, 0.4, 4.1), (x, y + 1.0, z), "C89A2A"))
            g.add(part("HayBand", (4.1, 0.4, 4.1), (x, y + 2.0, z), "C89A2A"))
        elif r < 0.55:
            tree(g, x, z, y, leaf="5CC83E", h=7, w=7)
        elif r < 0.8:
            for k in range(3):
                g.add(part("Crop", (1.2, 1.4, 1.2), (x + k * 2.2, y + 0.7, z), "4CB43A"))
                g.add(part("Carrot", (0.6, 0.6, 0.6), (x + k * 2.2, y + 1.6, z), "FF8A2A"))
        else:
            for k in (-2.7, 0, 2.7):
                g.add(part("Post", (0.6, 3, 0.6), (x + k, y + 1.5, z), "7A4A28"))
            g.add(part("Fence", (6, 0.6, 0.4), (x, y + 2.2, z), "8A5A32"))
            g.add(part("Fence", (6, 0.6, 0.4), (x, y + 1.2, z), "8A5A32"))
    elif theme == "jungle":
        if r < 0.55:
            h = rnd.uniform(10, 18)
            tree(g, x, z, y, trunk="6B4A2A", leaf=rnd.choice(["1F9A3C", "28B04A", "3CC85A"]), h=h, w=rnd.uniform(8, 12))
            g.add(part("Vine", (0.4, h * 0.6, 0.4), (x + 2.5, y + h * 0.75, z), "2E8A3A", collide=False, query=False))
        elif r < 0.8:
            for k in range(5):
                a = k * math.pi * 2 / 5
                g.add(part("Fern", (3.5, 0.4, 1.2), (x + math.cos(a) * 1.5, y + 1.2, z + math.sin(a) * 1.5), shade("36B44E", rnd.uniform(0.9, 1.1)), rot=a, collide=False))
        else:
            rock(g, x, z, y, c="6E7A6A")
    elif theme == "safari":
        if r < 0.4:
            h = rnd.uniform(7, 11)
            g.add(part("Trunk", (1.2, h, 1.2), (x, y + h / 2, z), "7A5232"))
            g.add(part("Canopy", (12, 1.6, 9), (x, y + h + 0.8, z), "6E9A3A"))
            g.add(part("Canopy", (8, 1.2, 6), (x + 1, y + h + 2.0, z), "7AAA42"))
            g.add(part("Canopy", (5, 1, 4), (x - 2, y + h + 2.6, z + 1), "86B84A"))
        elif r < 0.7:
            for k in range(6):
                g.add(part("Grass", (0.5, rnd.uniform(1.5, 3), 0.5), (x + rnd.uniform(-1.5, 1.5), y + 1, z + rnd.uniform(-1.5, 1.5)), "D8B84A", collide=False, query=False))
        elif r < 0.85:
            g.add(part("Mound", (3, 6, 3), (x, y + 3, z), "B9764A"))
            g.add(part("Mound", (2, 3, 2), (x + 0.5, y + 7, z), "B9764A"))
        else:
            rock(g, x, z, y, c="C98A5A", s=4)
    elif theme == "arctic":
        if r < 0.35:
            h = rnd.uniform(5, 12)
            g.add(part("IceSpike", (2.5, h, 2.5), (x, y + h / 2, z), "A8DCFF", kind="glass", transparency=0.3))
            g.add(part("IceSpike", (1.4, h * 0.5, 1.4), (x, y + h + h * 0.25, z), "C8ECFF", kind="glass", transparency=0.3))
        elif r < 0.65:
            g.add(part("Trunk", (1.2, 3, 1.2), (x, y + 1.5, z), "6B4A2A"))
            for k, w in enumerate((7, 5, 3)):
                g.add(part("Pine", (w, 2.5, w), (x, y + 3 + k * 2.4, z), "2E7A5A"))
                g.add(part("Snow", (w * 0.8, 0.5, w * 0.8), (x, y + 4.4 + k * 2.4, z), "FFFFFF"))
        else:
            g.add(part("SnowMound", (6, 2, 5), (x, y + 1, z), "FFFFFF"))
            g.add(part("SnowMound", (3.5, 1.5, 3), (x + 1, y + 2.4, z), "F4FAFF"))
    elif theme == "fantasy":
        if r < 0.4:
            c = rnd.choice(["B48CFF", "5CE6FF", "FF78E6"])
            h = rnd.uniform(4, 10)
            g.add(part("Crystal", (2, h, 2), (x, y + h / 2, z), c, kind="neon", rot=0.6))
            g.add(part("Crystal", (1.2, h * 0.6, 1.2), (x + 1.6, y + h * 0.3, z + 0.8), c, kind="glass", transparency=0.2, rot=0.3))
        elif r < 0.75:
            h = rnd.uniform(4, 9)
            g.add(part("Stem", (1.4, h, 1.4), (x, y + h / 2, z), "F4F0FF"))
            cap = rnd.choice(["FF5CA8", "9B5CFF", "5CC8FF"])
            g.add(part("Cap", (7, 2, 7), (x, y + h + 1, z), cap))
            g.add(part("Cap", (5, 1, 5), (x, y + h + 2.4, z), shade(cap, 1.12)))
            for k in range(3):
                g.add(part("Dot", (1, 0.4, 1), (x + rnd.uniform(-2.5, 2.5), y + h + 2.1, z + rnd.uniform(-2.5, 2.5)), "FFFFFF", kind="neon"))
        else:
            g.add(part("FloatRock", (4, 2.5, 4), (x, y + rnd.uniform(8, 16), z), "5A4A8A"))


def cliff_side(g, Z, side, z0, z1):
    """Irregular terraced canyon wall made of studded columns with shaded faces and grass drips."""
    wall, top = Z["wall"], Z["top"]
    zz = z0
    while zz > z1:
        step = min(rnd.choice((6, 8, 10)), zz - z1)
        cz = zz - step / 2
        h1 = rnd.uniform(10, 15)
        w1 = rnd.uniform(7, 10)
        x1 = side * (HALF_W + w1 / 2)
        g.add(part("Ledge", (w1, h1, step), (x1, h1 / 2, cz), shade(wall, rnd.uniform(0.9, 1.08))))
        g.add(part("LedgeTop", (w1 + 0.4, 1.6, step), (x1, h1 + 0.8, cz), shade(top, rnd.uniform(0.94, 1.06))))
        if rnd.random() < 0.5:
            dh = rnd.uniform(1.5, 3.5)
            g.add(part("Drip", (1.2, dh, rnd.uniform(1.5, step)), (side * (HALF_W - 0.3), h1 - dh / 2 + 0.8, cz + rnd.uniform(-1, 1)), shade(top, 0.95)))
        h2 = rnd.uniform(28, 40)
        w2 = rnd.uniform(16, 26)
        x2 = side * (HALF_W + w1 + w2 / 2 - 1)
        g.add(part("Cliff", (w2, h2, step), (x2, h2 / 2, cz), shade(wall, rnd.uniform(0.86, 1.04))))
        g.add(part("CliffTop", (w2 + 0.4, 2.2, step), (x2, h2 + 1.1, cz), shade(top, rnd.uniform(0.94, 1.06))))
        if rnd.random() < 0.55:
            dh = rnd.uniform(2, 5)
            g.add(part("Drip", (1.4, dh, rnd.uniform(2, step)), (side * (HALF_W + w1 - 1.3), h2 - dh / 2 + 1, cz), shade(top, 0.92)))
        if rnd.random() < 0.3:
            theme_prop(g, Z["theme"], side * (HALF_W + rnd.uniform(2.5, w1 - 2)), cz, h1 + 1.6)
        if rnd.random() < 0.4:
            theme_prop(g, Z["theme"], side * (HALF_W + w1 + rnd.uniform(3, w2 - 4)), cz, h2 + 2.2)
        if rnd.random() < 0.35:  # stone accents on the wall face
            g.add(part("Stone", (1.0, rnd.uniform(1.5, 3), rnd.uniform(1.5, 3)), (side * (HALF_W - 0.2), rnd.uniform(2, h1 - 3), cz), shade(wall, 0.78)))
        zz -= step


# ---------------- BASE PLAZA ----------------
base = mapm.add(Item("Model", "Base"))
for i in range(-6, 7):  # checker plaza floor
    for j in range(-5, 5):
        c = "62CE48" if (i + j) % 2 == 0 else "58BE40"
        base.add(part("Floor", (20, 2, 20), (i * 20, -1, 30 + j * 20 + 10), c))
base.add(part("Path", (40, 0.2, 170), (0, 0.1, 45), "E8D9A8", collide=False))
for k in range(-8, 9):
    base.add(part("PathEdge", (1, 0.3, 9), (-20.5, 0.15, 45 + k * 10), "C9B888", collide=False))
    base.add(part("PathEdge", (1, 0.3, 9), (20.5, 0.15, 45 + k * 10), "C9B888", collide=False))
for side in (-1, 1):
    for k in range(10):
        zc = 125 - k * 20
        h = rnd.uniform(20, 28)
        base.add(part("Wall", (20, h, 20), (side * 140, h / 2, zc), shade("96623C", rnd.uniform(0.9, 1.06))))
        base.add(part("WallTop", (22, 3, 20), (side * 140, h + 1.5, zc), shade("78DC50", rnd.uniform(0.95, 1.05))))
for k in range(15):
    h = rnd.uniform(20, 28)
    base.add(part("Wall", (20, h, 20), (-140 + k * 20, h / 2, 140), shade("96623C", rnd.uniform(0.9, 1.06))))
    base.add(part("WallTop", (20, 3, 22), (-140 + k * 20, h + 1.5, 140), shade("78DC50", rnd.uniform(0.95, 1.05))))
for side in (-1, 1):
    for k in range(5):
        h = rnd.uniform(20, 28)
        base.add(part("Wall", (20, h, 10), (side * (45 + k * 20), h / 2, -70), shade("96623C", rnd.uniform(0.9, 1.06))))
        base.add(part("WallTop", (20, 3, 12), (side * (45 + k * 20), h + 1.5, -70), shade("78DC50", rnd.uniform(0.95, 1.05))))
for _ in range(22):
    side = rnd.choice((-1, 1))
    theme_prop(base, "backyard", side * rnd.uniform(108, 126), rnd.uniform(-55, 125))
for x in (-30, 30):
    for z in (-40, 10, 60, 110):
        base.add(part("LampPost", (0.8, 9, 0.8), (x, 4.5, z), "3A3A48"))
        base.add(part("Lamp", (1.8, 1.8, 1.8), (x, 9.5, z), "FFE9A0", kind="neon"))
# title arch over the canyon mouth
for side in (-1, 1):
    base.add(part("ArchPillar", (4, 50, 4), (side * 33, 25, -68), "FF8A1C"))
    base.add(part("ArchCap", (5, 2, 5), (side * 33, 51, -68), "FFD23C"))
base.add(part("TitleBoard", (60, 8, 2), (0, 52, -68), "FF5CA8"))  # high enough for the throw camera
base.add(part("TitleTrim", (62, 1, 2.4), (0, 47.6, -68), "FFD23C"))
base.add(part("TitleTrim", (62, 1, 2.4), (0, 56.4, -68), "FFD23C"))

spawn = part("SpawnLocation", (12, 1, 12), (0, 0.5, 118), "FFFFFF", cls="SpawnLocation")
spawn.raw('<bool name="Neutral">true</bool>').raw('<int name="Duration">0</int>')
mapm.add(spawn)
mapm.add(part("ThrowLine", (68, 0.3, 1.5), (0, 0.15, -66.5), "FFFFFF", kind="neon", collide=False))

sell = mapm.add(Item("Model", "SellStand"))
sx0, sz0 = 26, -52
sell.add(part("Counter", (10, 4, 4), (sx0, 2, sz0), "F4F4F4"))
sell.add(part("CounterStripe", (10.1, 1, 4.1), (sx0, 3, sz0), "E23B3B"))
for k in (-4.5, 4.5):
    sell.add(part("Post", (0.8, 9, 0.8), (sx0 + k, 4.5, sz0 - 1.6), "F4F4F4"))
for i in range(6):
    sell.add(part("Awning", (1.8, 0.6, 5.5), (sx0 - 4.5 + i * 1.8, 9.2, sz0), "E23B3B" if i % 2 == 0 else "FFFFFF"))
sell.add(part("Coin", (2.4, 2.4, 0.5), (sx0, 6.5, sz0 + 1), "FFC93C", kind="neon"))
for i, c in enumerate(("FFC93C", "FFD84A", "FFC93C")):
    sell.add(part("CoinPile", (1.6, 0.5, 1.6), (sx0 - 3 + i * 0.6, 4.25 + i * 0.5, sz0), c, kind="neon"))

# ---------------- TOY SHOP: blue/white stall + classic Noob vendor ----------------
shop = mapm.add(Item("Model", "ToyShop"))
hx, hz = -27.5, -50
shop.add(part("Counter", (3, 3.4, 10), (hx, 1.7, hz), "F4F4F4"))
shop.add(part("CounterStripe", (3.1, 0.9, 10.1), (hx, 2.6, hz), "2F7BE8"))
for dz in (-4.6, 4.6):
    shop.add(part("Post", (0.8, 9, 0.8), (hx + 1.0, 4.5, hz + dz), "F4F4F4"))
    shop.add(part("Post", (0.8, 9, 0.8), (hx - 6.0, 4.5, hz + dz), "F4F4F4"))
for i in range(6):
    shop.add(part("Awning", (8.5, 0.6, 1.8), (hx - 2.5, 9.2, hz - 4.5 + i * 1.8), "2F7BE8" if i % 2 == 0 else "FFFFFF"))
shop.add(part("ShopSign", (0.6, 2.2, 7), (hx + 1.6, 10.6, hz), "2F7BE8"))


def place_model(group, name, origin, scale, rot=0.0):
    """Copy a Blender model's bricks into the map (static decoration)."""
    c, s = math.cos(rot), math.sin(rot)
    for b in MODELS[name]["boxes"]:
        px, py, pz = (v * scale for v in b["p"])
        R = b["r"]
        Rw = (c * R[0] + s * R[6], c * R[1] + s * R[7], c * R[2] + s * R[8], R[3], R[4], R[5],
              -s * R[0] + c * R[6], -s * R[1] + c * R[7], -s * R[2] + c * R[8])
        group.add(part(b["b"], tuple(v * scale for v in b["s"]), tf(origin, rot, px, py, pz), b["c"], kind=b["m"], R=Rw,
                       collide=False, variant="StudsSmall", query=False))


for i, toy in enumerate(("Tennis Ball", "Rubber Duck", "Teddy Bear")):
    place_model(shop, toy, (hx, 3.75, hz - 3 + i * 3), 0.42, rot=math.pi / 2)

vendor = mapm.add(Item("Model", "ShopVendor"))
vo, vr = (hx - 3.5, 0, hz), -math.pi / 2  # stands behind the counter, facing the path (+X)
V = lambda lx, ly, lz: tf(vo, vr, lx, ly, lz)
YEL, BLU, GRN = "F5CD30", "0D69AC", "A4BD47"
vendor.add(part("Torso", (2, 2, 1), V(0, 3, 0), BLU, rot=vr, variant=None))
head = part("Head", (2, 1, 1), V(0, 4.5, 0), YEL, rot=vr, variant=None)
head.add(Item("SpecialMesh", "Mesh")).raw('<token name="MeshType">0</token>').raw('<Vector3 name="Scale"><X>1.25</X><Y>1.25</Y><Z>1.25</Z></Vector3>')
head.add(Item("Decal", "face")).raw(content("Texture", "rbxasset://textures/face.png")).raw('<token name="Face">5</token>')
vendor.add(head)
vendor.add(part("Left Arm", (1, 2, 1), V(-1.5, 3, 0), YEL, rot=vr, variant=None, collide=False))
vendor.add(part("Right Arm", (1, 2, 1), V(1.5, 3, 0), YEL, rot=vr, variant=None, collide=False))
vendor.add(part("Left Leg", (1, 2, 1), V(-0.5, 1, 0), GRN, rot=vr, variant=None))
vendor.add(part("Right Leg", (1, 2, 1), V(0.5, 1, 0), GRN, rot=vr, variant=None))

# ---------------- PLOTS ----------------
plots = mapm.add(Item("Folder", "Plots"))
idx = 0
for side, rot in ((-1, math.pi / 2), (1, -math.pi / 2)):
    for z in (0, 50, 100):
        idx += 1
        o = (side * 72, 0, z)
        pm = plots.add(Item("Model", f"Plot{idx}"))
        L = lambda lx, ly, lz: tf(o, rot, lx, ly, lz)
        pm.add(part("Floor", (46, 0.4, 60), L(0, 0.2, 0), "4FB83A", rot=rot))
        pm.add(part("Border", (48, 0.3, 62), L(0, 0.05, 0), "E8D9A8", rot=rot, collide=False))
        for lx in (-23.5, 23.5):
            pm.add(part("Fence", (0.6, 0.6, 60), L(lx, 2.2, 0), "C8935A", rot=rot))
            pm.add(part("Fence", (0.6, 0.6, 60), L(lx, 1.1, 0), "C8935A", rot=rot))
            for lz in range(-30, 31, 6):
                pm.add(part("FencePost", (0.9, 3, 0.9), L(lx, 1.5, lz), "A8703C", rot=rot))
                pm.add(part("PostCap", (1.1, 0.4, 1.1), L(lx, 3.2, lz), "C8935A", rot=rot))
            for lz in range(-27, 28, 9):  # flower bed along the fence
                c = rnd.choice(["FF5C8A", "FFD23C", "B46CFF", "FF8A3C"])
                pm.add(part("Flower", (0.8, 0.8, 0.8), L(lx - 1.4 * (1 if lx > 0 else -1), 0.8, lz), c, rot=rot, collide=False))
                pm.add(part("Leaf", (1.2, 0.5, 1.2), L(lx - 1.4 * (1 if lx > 0 else -1), 0.45, lz), "3C9A3C", rot=rot, collide=False))
        pm.add(part("Fence", (47, 0.6, 0.6), L(0, 2.2, -30), "C8935A", rot=rot))
        pm.add(part("Fence", (47, 0.6, 0.6), L(0, 1.1, -30), "C8935A", rot=rot))
        bush(pm, *L(-18, 0, -27)[0::2])
        bush(pm, *L(18, 0, -27)[0::2])
        pm.add(part("Spawn", (6, 0.2, 6), L(0, 0.5, 22), "FFFFFF", rot=rot, collide=False, transparency=0.6))
        for lx in (-6, 6):
            pm.add(part("SignPost", (0.8, 8, 0.8), L(lx, 4, 29), "A8703C", rot=rot))
        pm.add(part("OwnerSign", (14, 3, 0.8), L(0, 8, 29), "FFC93C", rot=rot))
        pm.add(part("OwnerTrim", (14.4, 0.4, 1.0), L(0, 9.6, 29), "FF8A1C", rot=rot))
        pm.add(part("SlotSign", (5, 4, 0.6), L(-16, 2.5, 25), "FFFFFF", rot=rot))
        pm.add(part("SlotSignStripe", (5.1, 0.8, 0.7), L(-16, 4.1, 25), "4CC84A", rot=rot))
        for lx in (12, 20):
            pm.add(part("BarFrame", (1, 10, 1), L(lx, 5, 12), "4656C8", rot=rot))
            pm.add(part("BarFoot", (2, 0.6, 2), L(lx, 0.3, 12), "2A2A3A", rot=rot))
        pm.add(part("BarFrame", (9, 0.8, 0.8), L(16, 9.6, 12), "4656C8", rot=rot))
        pm.add(part("BarGlow", (7, 0.4, 0.4), L(16, 9.6, 12.5), "FFFFFF", kind="neon", rot=rot, collide=False))
        pm.add(part("TrainSpot", (2, 2, 1), L(16, 6.2, 13), "FFFFFF", rot=rot, collide=False, transparency=1))
        pm.add(part("UpgradePad", (6, 0.4, 6), L(16, 0.5, 22), "FFC93C", kind="neon", rot=rot, collide=False))

# ---------------- CORRIDOR ----------------
cor = mapm.add(Item("Model", "Corridor"))
for zi, Z in enumerate(ZONES):
    g = cor.add(Item("Model", Z["name"]))
    z0 = CORRIDOR_START - zi * ZONE_LEN + (7 if zi == 0 else 0)
    z1 = CORRIDOR_START - (zi + 1) * ZONE_LEN
    mid, length = (z0 + z1) / 2, z0 - z1
    tiles = int(length // 17) + 1
    for t in range(tiles):
        tz0 = z0 - t * 17
        tl = min(17, tz0 - z1)
        if tl <= 0:
            break
        for col in range(-2, 2):
            c = Z["floor"] if (t + col) % 2 == 0 else shade(Z["floor"], 0.92)
            g.add(part("Floor", (17, 2, tl), (col * 17 + 8.5, -1, tz0 - tl / 2), c))
    g.add(part("CenterLine", (0.8, 0.12, length), (0, 0.06, mid), "FFFFFF", kind="neon", collide=False, shadow=False, query=False))
    g.add(part("ZoneLine", (68, 0.14, 1.4), (0, 0.07, z0 - 0.7), "FFFFFF", kind="neon", collide=False, shadow=False, query=False))
    for side in (-1, 1):
        cliff_side(g, Z, side, z0, z1)
        for k in range(int(length // 22)):
            zz = z0 - 10 - k * 22 + rnd.uniform(-5, 5)
            if rnd.random() < 0.6:
                theme_prop(g, Z["theme"], side * rnd.uniform(24, 31), zz + 4, 0)
    for side in (-1, 1):
        g.add(part("ArchPillar", (3, 30, 3), (side * 31, 15, z0 - 2), Z["top"]))
    g.add(part("ArchBeam", (65, 3, 3), (0, 31.5, z0 - 2), Z["wall"]))
    g.add(part("ZoneSign", (24, 6, 1), (0, 35, z0 - 2), Z["top"]))
cor.add(part("EndWall", (120, 60, 10), (0, 30, END_Z - 5), "3C2878"))
for k in range(-2, 3):
    cor.add(part("EndCrystal", (4, 14, 4), (k * 12, 7, END_Z - 1), "FF78E6", kind="neon"))

# ---------------- PET MODELS ----------------
rs = Item("ReplicatedStorage", "ReplicatedStorage")
shared = rs.add(Item("Folder", "Shared"))
shared.add(script("ModuleScript", "Config", P("src", "shared", "Config.luau")))
shared.add(script("ModuleScript", "Util", P("src", "shared", "Util.luau")))
shared.add(script("ModuleScript", "ThrowAnim", P("src", "shared", "ThrowAnim.luau")))
shared.add(script("ModuleScript", "Mutations", P("src", "shared", "Mutations.luau")))
rig = ["-- Generated by tools/build_place.py from the Blender pets: bone pivot points in model space (studs).", "return {"]
mfolder = rs.add(Item("Folder", "Models"))
for name, mdl in MODELS.items():
    m = mfolder.add(Item("Model", name))
    root = part("Root", (1, 1, 1), (0, 0, 0), "FFFFFF", collide=False, transparency=1, variant=None, shadow=False, query=False)
    m.add(root)
    m.raw(f'<Ref name="PrimaryPart">{root.ref}</Ref>')
    for b in mdl["boxes"]:
        m.add(part(b["b"], b["s"], b["p"], b["c"], kind=b["m"], R=b["r"], collide=False, variant="StudsSmall", query=False))
    rig.append(f'\t["{name}"] = {{ ' + ", ".join(f'{k} = Vector3.new({v[0]}, {v[1]}, {v[2]})' for k, v in mdl["pivots"].items()) + " },")
rig.append("}")
shared.add(script_src("ModuleScript", "PetRig", "\n".join(rig)))

sounds = rs.add(Item("Folder", "Sounds"))
VOL = {"Music": 0.3, "Legendary": 0.9, "Land": 0.8, "Throw": 0.7}
for fname in sorted(os.listdir(P("assets", "sounds"))):
    n = fname[:-4]
    s = sounds.add(Item("Sound", n))
    s.raw(content("SoundId", ASSETS["sounds"].get(n, "")))
    s.raw(f'<float name="Volume">{VOL.get(n, 0.6)}</float>')

# ---------------- SERVICES ----------------
sss = Item("ServerScriptService", "ServerScriptService")
sss.add(script("Script", "GameServer", P("src", "server", "GameServer.server.luau")))
sp = Item("StarterPlayer", "StarterPlayer")
sps = sp.add(Item("StarterPlayerScripts", "StarterPlayerScripts"))
sps.add(script("LocalScript", "GameClient", P("src", "client", "GameClient.client.luau")))

lighting = Item("Lighting", "Lighting")
# Matched to Throw Food for Animals: high midday sun, bright ambient (short, light shadows), almost no haze so the
# canyon stays crisp, deep blue sky with puffy clouds (Clouds are added at runtime), and punchy saturated color.
lighting.raw(color3("Ambient", "7A7A8C")).raw(color3("OutdoorAmbient", "B4B4C8"))
lighting.raw('<float name="Brightness">3</float>').raw('<float name="ClockTime">13</float>').raw('<float name="ShadowSoftness">0.5</float>')
lighting.raw('<bool name="GlobalShadows">true</bool>').raw('<float name="EnvironmentDiffuseScale">1</float>').raw('<float name="EnvironmentSpecularScale">0.3</float>')
atm = lighting.add(Item("Atmosphere", "Atmosphere"))
atm.raw('<float name="Density">0.18</float>').raw('<float name="Offset">0</float>').raw(color3("Color", "C7DCFF")).raw(color3("Decay", "6A9ADC")).raw('<float name="Glare">0</float>').raw('<float name="Haze">0</float>')
ccx = lighting.add(Item("ColorCorrectionEffect", "ColorCorrection"))
ccx.raw('<float name="Saturation">0.32</float>').raw('<float name="Contrast">0.12</float>').raw('<float name="Brightness">0.03</float>').raw(color3("TintColor", "FFFFFF"))
bloom = lighting.add(Item("BloomEffect", "Bloom"))
bloom.raw('<float name="Intensity">0.8</float>').raw('<float name="Size">24</float>').raw('<float name="Threshold">1.3</float>')
lighting.add(Item("SunRaysEffect", "SunRays")).raw('<float name="Intensity">0.04</float>').raw('<float name="Spread">0.8</float>')

matsvc = Item("MaterialService", "MaterialService")
for vname, tile in (("Studs", 1.0), ("StudsSmall", 0.25)):
    mv = matsvc.add(Item("MaterialVariant", vname))
    mv.raw('<token name="BaseMaterial">256</token>').raw(content("ColorMap", ASSETS.get("studs", ""))).raw(f'<float name="StudsPerTile">{tile}</float>')
    mv.raw('<token name="MaterialPattern">0</token>')

out = ['<roblox xmlns:xmime="http://www.w3.org/2005/05/xmlmime" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
       'xsi:noNamespaceSchemaLocation="http://www.roblox.com/roblox.xsd" version="4">']
for top in (workspace, rs, sss, sp, lighting, matsvc):
    top.xml(out)
out.append("</roblox>")
path = P("ThrowAToy.rbxlx")
open(path, "w", encoding="utf-8").write("\n".join(out))
print(f"wrote {os.path.abspath(path)}  ({COUNT[0]} parts, {len(MODELS)} models, {_ref[0]} instances)")
