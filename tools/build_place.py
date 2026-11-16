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
    dict(name="Dinosaur Island", floor="5AA03C", wall="6A4A2A", top="3C8A2A", theme="dino"),
    dict(name="Lost Desert", floor="E8C878", wall="C8964A", top="F0D890", theme="desert"),
    dict(name="Sakura Gardens", floor="8AD070", wall="8A5A4A", top="FFB0D0", theme="sakura"),
    dict(name="Lost Atlantis", floor="2A6A8A", wall="1A3A5A", top="2AD8C8", theme="atlantis"),
    dict(name="Sky Kingdom", floor="C8E8FF", wall="8AB8E8", top="FFFFFF", theme="sky"),
    dict(name="Halloween Town", floor="3A2A4A", wall="2A1A2A", top="FF8A1C", theme="halloween"),
    dict(name="Tropical Paradise", floor="F0E0A0", wall="3CB4A8", top="4CD964", theme="tropical"),
    dict(name="Toy Factory", floor="9AA4B2", wall="5A6070", top="FFC21C", theme="toy"),
    dict(name="Ice Age", floor="DCEEFF", wall="6A9ACA", top="F4FAFF", theme="iceage"),
    dict(name="Mushroom Kingdom", floor="4A8A3A", wall="5A3A6A", top="E8401C", theme="mushroom"),
    dict(name="Heaven's Gate", floor="FFF4D8", wall="E8D8A0", top="FFE45C", theme="heaven"),
    dict(name="Underworld", floor="2A0A0A", wall="1C0A0A", top="FF3B1C", theme="underworld"),
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
    if theme in ("dino", "desert", "sakura", "atlantis", "sky", "halloween", "tropical", "toy", "iceage", "mushroom", "heaven", "underworld"):
        world2_prop(g, theme, x, z, y, r)
    elif theme == "backyard":
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


def palm(g, x, z, y=0.0, h=None):
    h = h or rnd.uniform(8, 12)
    for k in range(4):
        g.add(part("PalmTrunk", (1.1, h / 4 + 0.2, 1.1), (x + k * 0.35, y + h / 8 + k * h / 4, z), "A0784A"))
    top = (x + 1.4, y + h + 0.3, z)
    for k in range(6):
        a = k * math.pi / 3
        g.add(part("Frond", (5, 0.4, 1.4), (top[0] + math.cos(a) * 2.2, top[1] - 0.6, top[2] + math.sin(a) * 2.2), "3CB44A", rot=a))


def tower(g, x, z, y=0.0, c="FFC21C", roof="FFE45C", h=14, w=5, glow="FFE45C"):
    g.add(part("Tower", (w, h, w), (x, y + h / 2, z), c))
    for k in (-1, 1):
        g.add(part("Crenel", (1.2, 1.4, w), (x + k * (w / 2 - 0.6), y + h + 0.7, z), c))
    g.add(part("Roof", (w * 0.8, 3, w * 0.8), (x, y + h + 2.2, z), roof))
    g.add(part("Window", (1, 1.8, 0.2), (x, y + h * 0.6, z + w / 2 + 0.05), glow, kind="neon"))


def world2_prop(g, theme, x, z, y, r):
    """Props for the 12 World 2 zones (same idea as theme_prop: a weighted pick per spot)."""
    if theme == "dino":
        if r < 0.35:
            for k in range(6):
                a = k * math.pi / 3
                g.add(part("GiantFern", (7, 0.5, 2), (x + math.cos(a) * 3, y + 2.5, z + math.sin(a) * 3), shade("2E9A3A", rnd.uniform(0.9, 1.1)), rot=a, collide=False))
        elif r < 0.6:
            for k, (w, hh) in enumerate(((12, 4), (9, 4), (6, 3), (4, 2))):
                g.add(part("Volcano", (w, hh, w), (x, y + 2 + sum((4, 4, 3, 2)[:k]), z), shade("5A3A2A", 1 - k * 0.06)))
            g.add(part("Lava", (3, 0.6, 3), (x, y + 13.3, z), "FF5A1C", kind="neon"))
        else:
            for k in range(3):
                g.add(part("DinoEgg", (1.6, 2.2, 1.6), (x + k * 2, y + 1.1, z + (k % 2)), rnd.choice(["F4F0E0", "C8E8A0", "E8D8F0"])))
                g.add(part("Spot", (0.5, 0.5, 0.2), (x + k * 2, y + 1.4, z + (k % 2) + 0.8), "6A8A4A", collide=False))
    elif theme == "desert":
        if r < 0.3:
            for k, w in enumerate((14, 10, 6, 2.5)):
                g.add(part("Pyramid", (w, 3.2, w), (x, y + 1.6 + k * 3.2, z), shade("E8C070", 1 - k * 0.04)))
        elif r < 0.6:
            g.add(part("Dune", (10, 3, 7), (x, y + 1.5, z), "F0D08A", rot=rnd.uniform(0, 1)))
            g.add(part("Dune", (6, 2, 5), (x + 2, y + 3.4, z), "F4D898"))
        elif r < 0.8:
            palm(g, x, z, y)
            g.add(part("Oasis", (7, 0.3, 6), (x - 3, y + 0.15, z + 2), "3AA8FF", kind="glass", transparency=0.25, collide=False))
        else:
            g.add(part("Cactus", (1.4, 5, 1.4), (x, y + 2.5, z), "4CA03A"))
            g.add(part("CactusArm", (2.4, 1, 1), (x + 1.2, y + 3.2, z), "4CA03A"))
    elif theme == "sakura":
        if r < 0.5:
            tree(g, x, z, y, trunk="6A3A2A", leaf=rnd.choice(["FFB0D0", "FF9AC8", "FFD0E8"]), h=rnd.uniform(7, 11), w=rnd.uniform(7, 10))
        elif r < 0.75:
            for k in range(5):
                g.add(part("Bridge", (2.2, 0.6, 4), (x + k * 2 - 4, y + 1 + math.sin(k / 4 * math.pi) * 2, z), "D8301C"))
            for k in (-5, 5):
                g.add(part("BridgePost", (0.6, 3, 0.6), (x + k, y + 1.5, z + 1.8), "D8301C"))
        else:
            g.add(part("KoiPond", (8, 0.3, 6), (x, y + 0.15, z), "3AA8FF", kind="glass", transparency=0.25, collide=False))
            for k in range(3):
                g.add(part("Koi", (1.2, 0.4, 0.5), (x + rnd.uniform(-2.5, 2.5), y + 0.4, z + rnd.uniform(-2, 2)), rnd.choice(["FF7A3C", "FFFFFF"]), collide=False))
    elif theme == "atlantis":
        if r < 0.4:
            h = rnd.uniform(8, 14)
            g.add(part("Column", (2.2, h, 2.2), (x, y + h / 2, z), "8AA8B8"))
            g.add(part("Capital", (3, 1, 3), (x, y + h + 0.5, z), "A8C8D8"))
            g.add(part("Rune", (0.4, h * 0.6, 0.2), (x, y + h / 2, z + 1.15), "2AD8C8", kind="neon"))
        elif r < 0.7:
            g.add(part("Ruin", (8, 3, 5), (x, y + 1.5, z), "6A8A9A", rot=0.3))
            g.add(part("RuinGlow", (6, 0.4, 0.4), (x, y + 3.2, z), "6FF0FF", kind="neon", rot=0.3))
        else:
            for k in range(4):
                g.add(part("Kelp", (0.6, rnd.uniform(4, 8), 0.6), (x + k * 1.2, y + 3, z + (k % 2)), "2A9A6A", collide=False))
            g.add(part("Coral", (2, 2, 2), (x - 2, y + 1, z), rnd.choice(["FF6AA0", "FF9A2A", "B45CFF"])))
    elif theme == "sky":
        if r < 0.4:
            hh = y + rnd.uniform(10, 20)
            g.add(part("FloatIsland", (9, 4, 8), (x, hh, z), "8A6A4A"))
            g.add(part("FloatGrass", (9.4, 1, 8.4), (x, hh + 2.5, z), "6CD04A"))
            g.add(part("FloatRock", (5, 3, 4), (x, hh - 3.2, z), "7A5A3A"))
        elif r < 0.7:
            for dx, dy, s2 in ((0, 0, 5), (3, 0.5, 4), (-3, 0.3, 4), (1, 2, 3.5)):
                g.add(part("Cloud", (s2, s2 * 0.6, s2), (x + dx, y + rnd.uniform(6, 12) + dy, z), "FFFFFF", collide=False))
        else:
            h = rnd.uniform(10, 18)
            g.add(part("Waterfall", (3, h, 1), (x, y + h / 2, z), "8FD8FF", kind="glass", transparency=0.3, collide=False))
            g.add(part("Splash", (5, 0.6, 4), (x, y + 0.3, z), "C8F0FF", kind="glass", transparency=0.3, collide=False))
    elif theme == "halloween":
        if r < 0.3:
            g.add(part("House", (8, 7, 7), (x, y + 3.5, z), "3A2A3A"))
            g.add(part("HouseRoof", (9, 3, 8), (x, y + 8.5, z), "1C1018"))
            for k in (-2, 2):
                g.add(part("HouseWindow", (1.4, 1.6, 0.2), (x + k, y + 4.5, z + 3.55), "FFC21C", kind="neon"))
        elif r < 0.65:
            for k in range(2):
                g.add(part("Pumpkin", (2.4, 2, 2.4), (x + k * 2.8, y + 1, z), "FF8A1C"))
                g.add(part("PumpkinFace", (1.2, 0.4, 0.2), (x + k * 2.8, y + 1.1, z + 1.25), "FFE14A", kind="neon"))
                g.add(part("PumpkinStem", (0.4, 0.6, 0.4), (x + k * 2.8, y + 2.3, z), "3C9A3C"))
        else:
            h = rnd.uniform(7, 11)
            g.add(part("DeadTrunk", (1.2, h, 1.2), (x, y + h / 2, z), "2A1A1A"))
            for k in range(3):
                g.add(part("DeadBranch", (4, 0.6, 0.6), (x + 1.5 * (1 if k % 2 else -1), y + h * (0.5 + k * 0.15), z), "2A1A1A", rot=0.4 * k))
    elif theme == "tropical":
        if r < 0.5:
            palm(g, x, z, y)
        elif r < 0.75:
            g.add(part("Hut", (7, 4, 6), (x, y + 2, z), "C8A070"))
            g.add(part("HutRoof", (8.5, 2, 7.5), (x, y + 5, z), "E8C870"))
            g.add(part("HutDoor", (1.4, 2.6, 0.2), (x, y + 1.3, z + 3.05), "6A4A2A"))
        else:
            g.add(part("UmbrellaPole", (0.3, 4, 0.3), (x, y + 2, z), "FFFFFF"))
            g.add(part("Umbrella", (5, 0.6, 5), (x, y + 4.2, z), rnd.choice(["FF4A5A", "3AA8FF", "FFE03A"])))
            g.add(part("Towel", (2, 0.1, 3.5), (x + 2, y + 0.05, z), "FF8AB8", collide=False))
    elif theme == "toy":
        if r < 0.4:
            for k in range(3):
                c = rnd.choice(["FF4A5A", "3AA8FF", "FFE03A", "4CD964", "B45CFF"])
                s2 = rnd.uniform(2.5, 4)
                g.add(part("ToyBlock", (s2, s2, s2), (x + k * 1.5, y + s2 / 2 + k * 2.6, z + (k % 2)), c, rot=k * 0.3))
        elif r < 0.7:
            g.add(part("Conveyor", (12, 1.2, 3), (x, y + 1.6, z), "3A3F4A"))
            for k in range(5):
                g.add(part("ConveyorStripe", (0.4, 0.1, 3), (x - 5 + k * 2.5, y + 2.25, z), "FFC21C", collide=False))
            g.add(part("ConveyorLeg", (0.6, 1, 0.6), (x - 5, y + 0.5, z), "5A6070"))
            g.add(part("ConveyorLeg", (0.6, 1, 0.6), (x + 5, y + 0.5, z), "5A6070"))
        else:
            g.add(part("Machine", (5, 6, 4), (x, y + 3, z), rnd.choice(["FF6A3C", "3AA8FF", "B45CFF"])))
            g.add(part("Gear", (3, 3, 0.5), (x, y + 4, z + 2.3), "FFC21C", kind="neon", rot=0.4))
            g.add(part("Pipe", (0.8, 4, 0.8), (x + 1.5, y + 8, z), "9AA4B2"))
    elif theme == "iceage":
        if r < 0.4:
            h = rnd.uniform(10, 18)
            g.add(part("Glacier", (8, h, 6), (x, y + h / 2, z), "A8DCFF", kind="glass", transparency=0.25))
            g.add(part("GlacierCap", (8.4, 1.2, 6.4), (x, y + h + 0.6, z), "FFFFFF"))
        elif r < 0.7:
            for k, w in enumerate((12, 8, 4)):
                g.add(part("SnowPeak", (w, 4, w), (x, y + 2 + k * 4, z), shade("F4FAFF", 1 - k * 0.03)))
        else:
            g.add(part("CaveL", (2, 6, 4), (x - 3, y + 3, z), "6A9ACA"))
            g.add(part("CaveR", (2, 6, 4), (x + 3, y + 3, z), "6A9ACA"))
            g.add(part("CaveTop", (8, 2, 4), (x, y + 7, z), "8AB8E8"))
            g.add(part("Icicle", (0.6, 1.6, 0.6), (x, y + 5.2, z + 1), "C8F0FF", kind="glass"))
    elif theme == "mushroom":
        if r < 0.5:
            h = rnd.uniform(5, 12)
            g.add(part("Stem", (1.8, h, 1.8), (x, y + h / 2, z), "F4F0E8"))
            cap = rnd.choice(["E8401C", "B45CFF", "FF8A1C", "3AA8FF"])
            g.add(part("Cap", (9, 2.4, 9), (x, y + h + 1.2, z), cap))
            g.add(part("Cap", (6, 1.2, 6), (x, y + h + 3, z), shade(cap, 1.12)))
            for k in range(4):
                g.add(part("Dot", (1.2, 0.4, 1.2), (x + rnd.uniform(-3, 3), y + h + 2.5, z + rnd.uniform(-3, 3)), "FFFFFF"))
        elif r < 0.75:
            g.add(part("GlowLake", (8, 0.3, 6), (x, y + 0.15, z), "6FF0FF", kind="neon", transparency=0.3, collide=False))
        else:
            g.add(part("TinyHouse", (2.4, 2, 2.4), (x, y + 1, z), "F4E8D0"))
            g.add(part("TinyRoof", (3, 1.4, 3), (x, y + 2.7, z), "E8401C"))
            g.add(part("TinyWindow", (0.6, 0.6, 0.2), (x, y + 1.2, z + 1.25), "FFE14A", kind="neon"))
    elif theme == "heaven":
        if r < 0.35:
            tower(g, x, z, y, "FFE8A0", "FFC21C", rnd.uniform(12, 18), 5, "FFFFFF")
        elif r < 0.65:
            for dx, s2 in ((0, 5), (3, 4), (-3, 4)):
                g.add(part("Cloud", (s2, s2 * 0.55, s2), (x + dx, y + rnd.uniform(1, 4), z), "FFFFFF", collide=False))
        else:
            for k in (-3, 3):
                g.add(part("GatePillar", (1.4, 12, 1.4), (x + k, y + 6, z), "FFC21C"))
            g.add(part("GateArch", (8, 1.4, 1.4), (x, y + 12.5, z), "FFC21C"))
            g.add(part("GateGlow", (5, 10, 0.3), (x, y + 6, z), "FFF4C2", kind="neon", transparency=0.4, collide=False))
    elif theme == "underworld":
        if r < 0.35:
            tower(g, x, z, y, "2A1A1A", "141010", rnd.uniform(12, 20), 5, "FF3B1C")
        elif r < 0.65:
            g.add(part("LavaPool", (8, 0.4, 6), (x, y + 0.2, z), "FF5A1C", kind="neon", collide=False))
            g.add(part("LavaRim", (9, 0.3, 7), (x, y + 0.1, z), "1C0A0A"))
        else:
            hh = y + rnd.uniform(6, 14)
            for k in range(6):
                g.add(part("ChainLink", (0.4, 1.2, 0.9), (x, hh + k * 1.0, z), "5A5A62", rot=(k % 2) * math.pi / 2, collide=False))


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
YARD_X, YARD_Z0, YARD_Z1 = 150, -70, 30  # courtyard: x in [-160, 160], z from the runway mouth to behind the plots
for i in range(-8, 8):  # checker yard floor
    for j in range(5):
        c = "62CE48" if (i + j) % 2 == 0 else "58BE40"
        base.add(part("Floor", (20, 2, 20), (i * 20 + 10, -1, YARD_Z0 + 10 + j * 20), c))
for k in range(-2, 2):  # orange checker launch strip at the runway mouth
    for r in range(2):
        c = "FF9A2E" if (k + r) % 2 == 0 else "FFB54A"
        base.add(part("LaunchStrip", (17, 0.3, 4), (k * 17 + 8.5, 0.15, -60 - r * 4), c, collide=False))


def terrace(g, x, z, sx, sz):
    """Two-step grass terrace block (dirt sides, grass cap) like the reference's yard walls."""
    h = rnd.uniform(9, 13)
    g.add(part("Wall", (sx, h, sz), (x, h / 2, z), shade("96623C", rnd.uniform(0.9, 1.06))))
    g.add(part("WallTop", (sx + 0.4, 2, sz + 0.4), (x, h + 1, z), shade("78DC50", rnd.uniform(0.95, 1.05))))
    return h


for side in (-1, 1):  # side walls: low step, then a tall step behind
    for k in range(-1, 7):  # runs past the front and back walls so the corners are closed
        zc = YARD_Z0 + 10 + k * 20
        terrace(base, side * (YARD_X + 6), zc, 12, 20)
        h = rnd.uniform(24, 32)
        base.add(part("Wall", (24, h, 20), (side * (YARD_X + 24), h / 2, zc), shade("96623C", rnd.uniform(0.9, 1.06))))
        base.add(part("WallTop", (24.4, 3, 20.4), (side * (YARD_X + 24), h + 1.5, zc), shade("78DC50", rnd.uniform(0.95, 1.05))))
for k in range(-10, 10):  # back wall behind the plots, out to the side walls
    xc = k * 20 + 10
    terrace(base, xc, YARD_Z1 + 6, 20, 12)
    h = rnd.uniform(24, 32)
    base.add(part("Wall", (20, h, 24), (xc, h / 2, YARD_Z1 + 24), shade("96623C", rnd.uniform(0.9, 1.06))))
    base.add(part("WallTop", (20.4, 3, 24.4), (xc, h + 1.5, YARD_Z1 + 24), shade("78DC50", rnd.uniform(0.95, 1.05))))
for side in (-1, 1):  # front wall either side of the runway mouth
    for k in range(8):  # out past the side walls
        xc = side * (44 + k * 20)
        h = rnd.uniform(22, 30)
        base.add(part("Wall", (20, h, 12), (xc, h / 2, -76), shade("96623C", rnd.uniform(0.9, 1.06))))
        base.add(part("WallTop", (20.4, 3, 12.4), (xc, h + 1.5, -76), shade("78DC50", rnd.uniform(0.95, 1.05))))
for _ in range(30):  # trees/bushes up on the terraces
    if rnd.random() < 0.5:
        side = rnd.choice((-1, 1))
        theme_prop(base, "backyard", side * rnd.uniform(YARD_X + 14, YARD_X + 34), rnd.uniform(YARD_Z0, YARD_Z1 + 20), 30)
    else:
        theme_prop(base, "backyard", rnd.uniform(-160, 160), rnd.uniform(YARD_Z1 + 14, YARD_Z1 + 34), 30)
for x in (-110, 110):  # lamps out by the stalls
    base.add(part("LampPost", (0.8, 9, 0.8), (x, 4.5, -55), "3A3A48"))
    base.add(part("Lamp", (1.8, 1.8, 1.8), (x, 9.5, -55), "FFE9A0", kind="neon"))
# title arch over the canyon mouth
for side in (-1, 1):
    base.add(part("ArchPillar", (4, 50, 4), (side * 33, 25, -68), "FF8A1C"))
    base.add(part("ArchCap", (5, 2, 5), (side * 33, 51, -68), "FFD23C"))
base.add(part("TitleBoard", (60, 8, 2), (0, 52, -68), "FF5CA8"))  # high enough for the throw camera
base.add(part("TitleTrim", (62, 1, 2.4), (0, 47.6, -68), "FFD23C"))
base.add(part("TitleTrim", (62, 1, 2.4), (0, 56.4, -68), "FFD23C"))

spawn = part("SpawnLocation", (12, 1, 12), (0, 0.5, -48), "FFFFFF", cls="SpawnLocation")
spawn.raw('<bool name="Neutral">true</bool>').raw('<int name="Duration">0</int>')
mapm.add(spawn)
mapm.add(part("ThrowLine", (68, 0.3, 1.5), (0, 0.15, -66.5), "FFFFFF", kind="neon", collide=False, transparency=1))  # logic line (invisible)
dots = mapm.add(Item("Model", "ThrowDots"))  # what players see: a dotted row of glowing white squares, like the reference
for k in range(34):
    dots.add(part("Dot", (1.1, 0.26, 1.1), (-33 + k * 2, 0.13, -66.5), "FFFFFF", kind="neon", collide=False, variant=None, shadow=False, query=False))

sell = mapm.add(Item("Model", "SellStand"))
sx0, sz0 = 58, -50  # front-right of the yard, by the runway
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
hx, hz = -58, -50  # front-left of the yard, by the runway
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
for px in (-120, -72, -24, 24, 72, 120):
    for rot in (math.pi,):  # local +z (the pen's open front) faces the runway (-z)
        idx += 1
        o = (px, 0, 4)  # close to the runway, like the reference
        pm = plots.add(Item("Model", f"Plot{idx}"))
        L = lambda lx, ly, lz: tf(o, rot, lx, ly, lz)
        pm.add(part("Floor", (46, 0.4, 46), L(0, 0.2, 0), "4FB83A", rot=rot))
        pm.add(part("Border", (48, 0.3, 48), L(0, 0.05, 0), "E8D9A8", rot=rot, collide=False))
        for lx in (-23.5, 23.5):
            pm.add(part("Fence", (0.6, 0.6, 46), L(lx, 2.2, 0), "C8935A", rot=rot))
            pm.add(part("Fence", (0.6, 0.6, 46), L(lx, 1.1, 0), "C8935A", rot=rot))
            for lz in (-23, -17.25, -11.5, -5.75, 0, 5.75, 11.5, 17.25, 23):
                pm.add(part("FencePost", (0.9, 3, 0.9), L(lx, 1.5, lz), "A8703C", rot=rot))
                pm.add(part("PostCap", (1.1, 0.4, 1.1), L(lx, 3.2, lz), "C8935A", rot=rot))
            for lz in (-20, -11, -2, 7, 16):  # flower bed along the fence
                c = rnd.choice(["FF5C8A", "FFD23C", "B46CFF", "FF8A3C"])
                pm.add(part("Flower", (0.8, 0.8, 0.8), L(lx - 1.4 * (1 if lx > 0 else -1), 0.8, lz), c, rot=rot, collide=False))
                pm.add(part("Leaf", (1.2, 0.5, 1.2), L(lx - 1.4 * (1 if lx > 0 else -1), 0.45, lz), "3C9A3C", rot=rot, collide=False))
        pm.add(part("Fence", (47, 0.6, 0.6), L(0, 2.2, -23), "C8935A", rot=rot))
        pm.add(part("Fence", (47, 0.6, 0.6), L(0, 1.1, -23), "C8935A", rot=rot))
        bush(pm, *L(-18, 0, -20)[0::2])
        bush(pm, *L(18, 0, -20)[0::2])
        pm.add(part("Spawn", (6, 0.2, 6), L(0, 0.5, 14), "FFFFFF", rot=rot, collide=False, transparency=0.6))
        for lx in (-6, 6):
            pm.add(part("SignPost", (0.8, 8, 0.8), L(lx, 4, 24), "A8703C", rot=rot))
        pm.add(part("OwnerSign", (14, 3, 0.8), L(0, 8, 24), "FFC93C", rot=rot))
        pm.add(part("OwnerTrim", (14.4, 0.4, 1.0), L(0, 9.6, 24), "FF8A1C", rot=rot))
        # slot upgrade: yellow wooden sign on posts (text "🐾 18 > 20 / $price" comes from the server), like the reference
        for dx in (-3.2, 3.2):
            pm.add(part("SlotPost", (0.7, 5.2, 0.7), L(-16 + dx, 2.6, 20), "A8703C", rot=rot))
        pm.add(part("SlotSign", (7, 3.4, 0.7), L(-16, 3.9, 20), "FFC21C", rot=rot))
        pm.add(part("SlotSignPlate", (5.6, 1.1, 0.75), L(-16, 3.2, 20), "2A2A3A", rot=rot, collide=False))
        # pull-up bar in the bar level's colour (BarFrame parts are recoloured by the server), dashed ring, round gold pad
        for lx in (12, 20):
            pm.add(part("BarFrame", (1, 10, 1), L(lx, 5, 30), "4656C8", rot=rot))
            pm.add(part("BarFoot", (2, 0.6, 2), L(lx, 0.3, 30), "2A2A3A", rot=rot))
        pm.add(part("BarFrame", (9, 0.8, 0.8), L(16, 9.6, 30), "4656C8", rot=rot))
        pm.add(part("BarGlow", (7, 0.4, 0.4), L(16, 9.6, 30.5), "FFFFFF", kind="neon", rot=rot, collide=False))
        cx, _, cz = L(16, 0, 30)
        for k in range(18):  # dashed ring around the bar
            t = 2 * math.pi * k / 18
            pm.add(part("BarRing", (1.5, 0.08, 0.4), (cx + 7.5 * math.cos(t), 0.06, cz + 7.5 * math.sin(t)), "FFFFFF", kind="neon",
                        rot=-t - math.pi / 2, collide=False, shadow=False, query=False))
        pm.add(part("TrainSpot", (2, 2, 1), L(16, 6.2, 31), "FFFFFF", rot=rot, collide=False, transparency=1))
        ROLL = (0, -1, 0, 1, 0, 0, 0, 0, 1)  # cylinder axis (X) stood upright
        pm.add(part("PadRim", (0.3, 6.6, 6.6), L(16, 0.2, 41.5), "8A8A96", R=ROLL, collide=False)).raw('<token name="shape">2</token>')
        pm.add(part("UpgradePad", (0.4, 5.6, 5.6), L(16, 0.4, 41.5), "FFC93C", kind="neon", R=ROLL, collide=False)).raw('<token name="shape">2</token>')

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
cine = shared.add(Item("Folder", "Cinematics"))  # Secret catch cinematics exported by blender/cinematics.py
_cdir = P("build", "cinematics")
for _f in sorted(os.listdir(_cdir)) if os.path.isdir(_cdir) else []:
    cine.add(script("ModuleScript", _f[:-5], os.path.join(_cdir, _f)))
rig = ["-- Generated by tools/build_place.py from the Blender pets: bone pivot points in model space (studs).", "return {"]
mfolder = rs.add(Item("Folder", "Models"))
for name, mdl in MODELS.items():
    m = mfolder.add(Item("Model", name))
    root = part("Root", (1, 1, 1), (0, 0, 0), "FFFFFF", collide=False, transparency=1, variant=None, shadow=False, query=False)
    m.add(root)
    m.raw(f'<Ref name="PrimaryPart">{root.ref}</Ref>')
    for b in mdl["boxes"]:
        bp = m.add(part(b["b"], b["s"], b["p"], b["c"], kind=b["m"], R=b["r"], collide=False, variant="StudsSmall", query=False))
        if b.get("sh") == "cyl":
            bp.raw('<token name="shape">2</token>')
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
