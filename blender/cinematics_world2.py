# World 2 Secret cinematics. Exec'd inside cinematics.py (shares key, shot, ev, flap, rest, hidden_prop, math).
# A small toolkit of keyframed moves; each cinematic below chains a few of them to act out its description.
import math as _m


def cam_orbit(cam, t0, t1, r=8, h=3.5, tz=1.5, a0=20, a1=160, steps=6):
    for k in range(steps + 1):
        t = t0 + (t1 - t0) * k / steps
        a = _m.radians(a0 + (a1 - a0) * k / steps)
        shot(cam, t, (_m.sin(a) * r, _m.cos(a) * r, h), (0, 0, tz))


def cam_end(cam, t=4.8):
    shot(cam, t, (3, 7.5, 2.6), (0, 0, 1.4))


def jump(pet, t0, t1, h, spin=0, tilt=0):
    key(pet, t0, loc=(0, 0, 0), rot=(0, 0, 0))
    key(pet, (t0 + t1) / 2, loc=(0, 0, h), rot=(tilt, 0, spin / 2))
    key(pet, t1, loc=(0, 0, 0), rot=(0, 0, spin))


def squash(pet, t, sx=1.3, sz=0.7):
    key(pet, t, scale=(sx, sx, sz))
    key(pet, t + 0.18, scale=(0.9, 0.9, 1.12))
    key(pet, t + 0.36, scale=1)


def grow(model, name, t0, t1, loc=(0, 0, 0), s0=0.1, s1=1.0, rot0=(0, 0, 0), rot1=(0, 0, 0), fade=None, parent=None):
    ob = hidden_prop(model, name, parent)
    key(ob, t0, loc=loc, rot=rot0, scale=s0, alpha=0)
    key(ob, t1, rot=rot1, scale=s1)
    if fade:
        key(ob, fade[0], alpha=0)
        key(ob, fade[1], alpha=1, scale=s1 * 1.15)
    return ob


def spray(model, base, n, t0, t1, center=(0, 0, 1.5), radius=5, up=2.5, s=1.0, fall=True):
    """n props burst out radially from center, arc up, land (or keep flying) and fade."""
    for k in range(n):
        th = 2 * _m.pi * k / n + 0.3 * (k % 2)
        d = (_m.cos(th) * radius * (0.7 + 0.3 * (k % 3) / 2), _m.sin(th) * radius * (0.7 + 0.3 * (k % 3) / 2))
        ob = hidden_prop(model, f"{base}{k}")
        tk = t0 + 0.04 * k
        key(ob, tk, loc=center, rot=(0, 0, 0), scale=0.2, alpha=0)
        key(ob, tk + (t1 - tk) * 0.4, loc=(center[0] + d[0] * 0.6, center[1] + d[1] * 0.6, center[2] + up), rot=(180, 90, _m.degrees(th)), scale=s)
        end = (center[0] + d[0], center[1] + d[1], 0.3 if fall else center[2] + up * 1.4)
        key(ob, t1, loc=end, rot=(360, 200, _m.degrees(th) + 180), scale=s, alpha=0.2)
        key(ob, t1 + 0.4, alpha=1, scale=s * 0.5)


def rain(model, base, n, t0, t1, r=5, h=10, s=1.0):
    for k in range(n):
        th = 2 * _m.pi * k / n * 2.3
        rr = r * ((k * 37) % 10) / 10
        x, y = _m.cos(th) * rr, _m.sin(th) * rr
        ob = hidden_prop(model, f"{base}{k}")
        tk = t0 + (t1 - t0) * 0.6 * k / n
        key(ob, tk, loc=(x, y, h), rot=(0, 0, k * 40), scale=s, alpha=0)
        key(ob, tk + 1.2, loc=(x, y, 0.2), rot=(180, 90, k * 40 + 200))
        key(ob, tk + 1.6, alpha=1)


def orbit_props(model, base, n, t0, t1, r=2.5, z=1.8, turns=1.5, s=1.0):
    for k in range(n):
        ob = hidden_prop(model, f"{base}{k}")
        for j in range(9):
            t = t0 + (t1 - t0) * j / 8
            a = 2 * _m.pi * (k / n + turns * j / 8)
            key(ob, t, loc=(_m.cos(a) * r, _m.sin(a) * r, z + 0.3 * _m.sin(j + k)), rot=(0, 0, _m.degrees(a)),
                scale=(0.01 if j in (0, 8) else s), alpha=(1 if j in (0, 8) else 0))


def clones(pet_model, n, t0, t1, r=3, spin=2):
    for k in range(n):
        ob = hidden_prop(pet_model, f"clone{k}")
        for j in range(9):
            t = t0 + (t1 - t0) * j / 8
            rr = r * _m.sin(_m.pi * j / 8)
            a = 2 * _m.pi * (k / n + spin * j / 8)
            key(ob, t, loc=(_m.cos(a) * rr, _m.sin(a) * rr, abs(_m.sin(j * 1.3)) * 0.8), rot=(0, 0, _m.degrees(a) + 90),
                scale=1.0, alpha=(1 if j in (0, 8) else 0.35))


def vanish(pet, t, back=None):
    key(pet, t - 0.05, alpha=0, scale=1)
    key(pet, t, alpha=1, scale=0.01)
    if back:
        key(pet, back - 0.05, alpha=1, scale=0.01)
        key(pet, back + 0.25, alpha=0, scale=1.2)
        key(pet, back + 0.5, scale=1)


def finale(color, t=4.2):
    ev(t, f"pillar:{color}")
    ev(t, f"burst:{color}:50")


# ---------------------------------------------------------------- 49 cinematics
def w_ancient_dragon(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.3, 3.4, 45, 0.3)
    key(pet, 1.0, loc=(0, 0, 2.5), rot=(-20, 0, 0))
    key(pet, 2.8, loc=(0, 0, 2.8), rot=(-15, 0, 360))
    grow("FX Meteor", "rock", 1.4, 2.2, (0, 6, 9), 0.3, 1.0, fade=(3.0, 3.4))
    rest(pet, bones, 3.8)
    cam_orbit(cam, 0, 3.8, 9, 4, 2)
    cam_end(cam)
    ev(1.0, "sound:Legendary"), ev(3.8, "shake:2"), ev(3.8, "shock:FFC21C"), finale("FFC21C")


def w_skeleton_rex(pet, bones, cam):
    rest(pet, bones, 0)
    vanish(pet, 0.8, 2.8)
    spray("FX Bone", "bone", 14, 0.8, 2.6, (0, 0, 2.2), 3.5, 2.5, 1.2, fall=False)
    cam_orbit(cam, 0, 4.2, 8, 3.5, 2)
    cam_end(cam)
    rest(pet, bones, 4.8)
    ev(0.8, "burst:F0ECE0:60"), ev(0.8, "sound:Error"), ev(2.8, "shake:1.5"), finale("F0ECE0")


def w_earth_turtle(pet, bones, cam):
    rest(pet, bones, 0)
    jump(pet, 0.4, 1.2, 2.0, 0, -20)
    squash(pet, 1.2, 1.3, 0.6)
    for k in range(6):
        a = 2 * _m.pi * k / 6
        grow("FX Tree", f"tree{k}", 1.3 + k * 0.08, 2.0 + k * 0.08, (_m.cos(a) * 3, _m.sin(a) * 3, 0), 0.05, 1.3, fade=(4.2, 4.6))
    cam_orbit(cam, 0, 4.8, 9, 4, 1.5)
    rest(pet, bones, 4.8)
    ev(1.2, "shake:2.2"), ev(1.2, "shock:6A9A4A"), ev(1.2, "sound:Legendary"), finale("3CC84A")


def w_pharaoh_cat(pet, bones, cam):
    rest(pet, bones, 0)
    jump(pet, 0.5, 2.0, 2.5, 360)
    grow("FX Gold Wings", "wings", 1.0, 1.6, (0, -0.3, 1.8), 0.1, 1.0, fade=(3.8, 4.4), parent=pet)
    cam_orbit(cam, 0, 4.8, 7, 3, 1.5)
    rest(pet, bones, 4.8)
    ev(1.25, "flash:FFD84A:0.5"), ev(1.25, "sound:Legendary"), finale("FFC21C")


def w_golden_sphinx(pet, bones, cam):
    rest(pet, bones, 0)
    key(pet, 1.6, loc=(0, 0, 3.0), rot=(0, 0, 180))
    key(pet, 3.4, loc=(0, 0, 3.2), rot=(0, 0, 360))
    flap(bones, 1.0, 3.4, 40, 0.4)
    grow("FX Gold Wings", "wings", 0.8, 1.6, (0, -0.4, 2.0), 0.1, 1.6, fade=(3.6, 4.2), parent=pet)
    rest(pet, bones, 4.3)
    cam_orbit(cam, 0, 4.3, 9, 2, 3, 0, 120)
    cam_end(cam)
    ev(1.6, "flash:FFD84A:0.6"), ev(1.6, "sound:Legendary"), finale("FFC21C")


def w_lava_scorpion(pet, bones, cam):
    rest(pet, bones, 0)
    if "tail" in bones:
        key(bones["tail"], 0.4, rot=(0, 0, 0)), key(bones["tail"], 1.0, rot=(-40, 0, 0)), key(bones["tail"], 1.2, rot=(30, 0, 0)), key(bones["tail"], 1.8, rot=(0, 0, 0))
    m = hidden_prop("FX Meteor", "meteor")
    key(m, 1.15, loc=(0, -1, 2.5), scale=0.3, alpha=0)
    key(m, 2.2, loc=(0, -2, 14), rot=(0, 0, 360), scale=1.2)
    key(m, 2.6, loc=(0, -2, 18), alpha=1)
    cam_orbit(cam, 0, 2.4, 7, 2, 4, 30, 100)
    cam_end(cam)
    ev(1.15, "burst:FF5A1C:50"), ev(1.15, "shake:1.5"), ev(1.15, "sound:Legendary"), ev(2.4, "flash:FF7A1C:0.5"), finale("FF5A1C")


def w_sakura_kitsune(pet, bones, cam):
    rest(pet, bones, 0)
    clones("Sakura Kitsune", 3, 0.6, 3.6, 3, 1.5)
    rain("FX Star", "petal", 14, 0.4, 3.2, 5, 8, 0.8)
    cam_orbit(cam, 0, 4.8, 9, 4, 1.5)
    ev(0.6, "burst:FF8AD8:40"), ev(0.6, "sound:Legendary"), finale("FF8AD8")


def w_kitsune(pet, bones, cam):
    rest(pet, bones, 0)
    clones("Kitsune", 5, 0.5, 3.6, 3.5, 2)
    key(pet, 3.6, scale=1), key(pet, 3.8, scale=1.3), key(pet, 4.0, scale=1)
    cam_orbit(cam, 0, 4.8, 9, 4, 1.5)
    ev(0.5, "burst:6FD8FF:40"), ev(3.8, "flash:FFFFFF:0.6"), ev(0.5, "sound:Legendary"), finale("6FD8FF")


def w_nine_tailed_fox(pet, bones, cam):
    rest(pet, bones, 0)
    if "tail" in bones:
        key(bones["tail"], 0.3, rot=(0, 0, 0)), key(bones["tail"], 1.0, rot=(-30, 0, 0)), key(bones["tail"], 3.4, rot=(-30, 0, 0)), key(bones["tail"], 3.8, rot=(0, 0, 0))
    grow("FX Blue Flame", "flame", 1.4, 1.9, (0, 0, 0), 0.2, 2.2, fade=(3.2, 3.9))
    squash(pet, 1.4, 1.2, 0.8)
    cam_orbit(cam, 0, 4.8, 9, 3, 1.5)
    ev(1.4, "flash:3AA8FF:0.85"), ev(1.4, "burst:3AA8FF:100"), ev(1.4, "shake:2.2"), ev(1.4, "sound:Legendary"), finale("3AA8FF")


def w_leviathan(pet, bones, cam):
    rest(pet, bones, 0)
    for k in range(9):
        t = 0.3 + k * 0.42
        a = _m.radians(k * 45)
        key(pet, t, loc=(_m.cos(a) * 3 - 3, _m.sin(a) * 3, 1.5 + _m.sin(k) * 0.8), rot=(0, 0, k * 45 + 90))
    rest(pet, bones, 4.3)
    grow("FX Water Tornado", "wt", 0.6, 1.4, (-3, 0, 0), 0.1, 1.3, rot1=(0, 0, 400), fade=(3.4, 4.0))
    cam_orbit(cam, 0, 4.3, 12, 5, 2)
    cam_end(cam)
    ev(0.6, "sound:Legendary"), ev(1.4, "burst:2AD8C8:60"), finale("2AD8C8")


def w_sea_serpent(pet, bones, cam):
    rest(pet, bones, 0)
    grow("FX Water Tornado", "wt", 0.3, 1.0, (0, 0, 0), 0.1, 1.2, rot1=(0, 0, 500), fade=(3.6, 4.2))
    for k in range(7):
        a = _m.radians(k * 70)
        key(pet, 1.0 + k * 0.38, loc=(_m.cos(a) * 1.5, _m.sin(a) * 1.5, 0.8 + k * 0.7), rot=(0, 0, k * 70 + 90))
    rest(pet, bones, 4.3)
    cam_orbit(cam, 0, 4.3, 10, 4, 3)
    cam_end(cam)
    ev(0.3, "sound:Legendary"), ev(3.5, "burst:3AA8FF:60"), finale("3AA8FF")


def w_cyber_shark(pet, bones, cam):
    rest(pet, bones, 0)
    grow("FX Portal", "p1", 0.3, 0.8, (0, 3, 0), 0.1, 1.0, fade=(2.0, 2.4))
    grow("FX Portal", "p2", 1.6, 2.1, (0, -4, 0), 0.1, 1.0, fade=(3.6, 4.0))
    key(pet, 0.8, loc=(0, 0, 1.5), rot=(0, 0, 0))
    key(pet, 1.2, loc=(0, 3, 1.8), alpha=0)
    key(pet, 1.3, alpha=1)
    key(pet, 2.0, loc=(0, -4, 1.8), alpha=1)
    key(pet, 2.2, alpha=0)
    key(pet, 3.0, loc=(3, 0, 3), rot=(0, 0, 270))
    rest(pet, bones, 4.0)
    cam_orbit(cam, 0, 4.0, 10, 4, 1.8)
    cam_end(cam)
    ev(0.3, "sound:Legendary"), ev(1.2, "burst:5CE6FF:40"), ev(2.2, "burst:5CE6FF:40"), finale("5CE6FF")


def w_alien_octopus(pet, bones, cam):
    rest(pet, bones, 0)
    for k, toy in enumerate(("Tennis Ball", "Rubber Duck", "Yarn Ball", "Teddy Bear")):
        ob = hidden_prop(toy, f"toy{k}")
        for j in range(7):
            t = 0.4 + j * 0.35 + k * 0.08
            a = 2 * _m.pi * (k / 4 + j / 6)
            key(ob, t, loc=(_m.cos(a) * 1.2, _m.sin(a) * 1.2, 2.5 + abs(_m.sin(j * 1.7 + k)) * 1.6), rot=(j * 60, 0, j * 40), scale=0.6, alpha=0)
        key(ob, 3.0 + k * 0.1, loc=(_m.cos(k) * 4, _m.sin(k) * 4, 12), alpha=0.2)
        key(ob, 3.4 + k * 0.1, alpha=1)
    cam_orbit(cam, 0, 4.8, 8, 3.5, 2.2)
    rest(pet, bones, 4.8)
    ev(0.4, "sound:Rare"), ev(3.0, "burst:B45CFF:50"), finale("B45CFF")


def w_cosmic_jellyfish(pet, bones, cam):
    rest(pet, bones, 0)
    key(pet, 1.8, loc=(0, 0, 4.0), rot=(0, 0, 180))
    key(pet, 3.4, loc=(0, 0, 4.2), rot=(0, 0, 360))
    rest(pet, bones, 4.3)
    grow("FX Galaxy Dome", "dome", 1.2, 2.4, (0, 0, 0), 0.1, 1.4, rot1=(0, 0, 90), fade=(3.8, 4.5))
    cam_orbit(cam, 0, 4.3, 10, 1.5, 3.5, 0, 140)
    cam_end(cam)
    ev(1.2, "sound:Legendary"), ev(2.4, "flash:8C7BFF:0.6"), finale("8C7BFF")


def w_cloud_emperor(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.3, 3.6, 40, 0.35)
    for k in range(5):
        a = 2 * _m.pi * k / 5
        grow("FX Cloud", f"cl{k}", 0.3 + k * 0.1, 1.2, (_m.cos(a) * 3, _m.sin(a) * 3, 0.5), 0.1, 1.4, rot1=(0, 0, 30), fade=(3.8, 4.4))
    key(pet, 1.6, loc=(0, 0, 2.5)), key(pet, 3.2, loc=(0, 0, 2.7), rot=(0, 0, 360))
    rest(pet, bones, 4.0)
    cam_orbit(cam, 0, 4.0, 9, 4, 2)
    cam_end(cam)
    ev(1.6, "flash:FFFFFF:0.6"), ev(1.6, "sound:Legendary"), finale("FFE45C")


def w_celestial_unicorn(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.3, 3.4, 50, 0.3)
    key(pet, 1.8, loc=(0, 2, 6), rot=(-25, 0, 0)), key(pet, 2.8, loc=(0, 0, 7), rot=(-10, 0, 180))
    rain("FX Star", "star", 18, 1.8, 3.6, 6, 9, 1.0)
    rest(pet, bones, 4.0)
    cam_orbit(cam, 0, 4.0, 10, 2, 4, 0, 90)
    cam_end(cam)
    ev(1.8, "burst:FFE45C:60"), ev(1.8, "sound:Legendary"), finale("C8D8FF")


def w_thunder_wolf(pet, bones, cam):
    rest(pet, bones, 0)
    for k in range(6):
        key(pet, 0.3 + k * 0.15, loc=(0.08 * (1 if k % 2 else -1), 0, 0))
    grow("FX Lightning", "bolt", 1.3, 1.45, (0, 0, 0), 1.0, 1.4, fade=(1.9, 2.3))
    key(pet, 1.45, loc=(0, 0, 0), scale=(1.15, 1.15, 0.85)), key(pet, 1.8, scale=1)
    cam_orbit(cam, 0, 4.8, 8, 2.5, 2)
    rest(pet, bones, 4.8)
    ev(0.3, "sound:Tick"), ev(1.3, "flash:FFFFFF:0.9"), ev(1.3, "shake:2.5"), ev(1.3, "sound:Legendary"), ev(1.35, "shock:FFE14A"), finale("FFE14A")


def w_wind_deer(pet, bones, cam):
    rest(pet, bones, 0)
    jump(pet, 0.4, 2.2, 4.0, 720)
    grow("FX Tornado", "tor", 0.8, 1.6, (0, 0, 0), 0.1, 1.3, rot1=(0, 0, 720), fade=(3.4, 4.0))
    cam_orbit(cam, 0, 4.8, 10, 3, 2.5)
    rest(pet, bones, 4.8)
    ev(0.8, "sound:Legendary"), ev(2.2, "burst:8FF0D8:60"), finale("8FF0D8")


def w_godly_owl(pet, bones, cam):
    rest(pet, bones, 0)
    for k, toy in enumerate(("Tennis Ball", "Frisbee", "Yarn Ball", "Toy Rocket", "Squeaky Bone", "Robot Toy")):
        a = 2 * _m.pi * k / 6
        ob = hidden_prop(toy, f"toy{k}")
        key(ob, 0.6, loc=(_m.cos(a) * 2.2, _m.sin(a) * 2.2, 1.6), scale=0.6, alpha=0)
        key(ob, 2.4, loc=(_m.cos(a) * 2.3, _m.sin(a) * 2.3, 1.7), rot=(0, 0, 10), scale=0.6)
        key(ob, 3.0, loc=(_m.cos(a) * 9, _m.sin(a) * 9, 4), rot=(360, 0, 200), alpha=0.1)
        key(ob, 3.4, alpha=1)
    flap(bones, 2.4, 3.2, 50, 0.25)
    cam_orbit(cam, 0, 4.8, 9, 3.5, 1.8)
    rest(pet, bones, 4.8)
    ev(0.6, "flash:FFE45C:0.4"), ev(0.6, "sound:Tick"), ev(2.4, "shock:FFE45C"), ev(2.4, "sound:Legendary"), finale("FFE45C")


def w_pumpkin_reaper(pet, bones, cam):
    rest(pet, bones, 0)
    if "armR" in bones:
        key(bones["armR"], 0.5, rot=(0, 0, 0)), key(bones["armR"], 1.2, rot=(-120, 0, 0)), key(bones["armR"], 1.5, rot=(60, 0, 0)), key(bones["armR"], 2.2, rot=(0, 0, 0))
    grow("FX Scythe", "scy", 0.4, 1.0, (1.4, 0, 0.5), 0.1, 1.2, rot1=(0, 0, 360), fade=(2.4, 2.8))
    for k in range(5):
        a = 2 * _m.pi * k / 5
        grow("FX Smoke", f"pmp{k}", 1.5, 2.2, (_m.cos(a) * 3.5, _m.sin(a) * 3.5, 0), 0.1, 0.8, fade=(3.8, 4.4))
    cam_orbit(cam, 0, 4.8, 8, 3, 1.8)
    rest(pet, bones, 4.8)
    ev(1.5, "flash:FF8A1C:0.6"), ev(1.5, "shock:FF8A1C"), ev(1.5, "sound:Legendary"), finale("FF8A1C")


def w_phantom_bunny(pet, bones, cam):
    rest(pet, bones, 0)
    vanish(pet, 0.5, 3.4)
    clones("Phantom Bunny", 4, 0.5, 3.3, 3, 1)
    cam_orbit(cam, 0, 4.8, 8, 3, 1.4)
    rest(pet, bones, 4.8)
    ev(0.5, "burst:C8D8FF:40"), ev(3.4, "flash:FFFFFF:0.7"), ev(3.4, "sound:Legendary"), finale("C8D8FF")


def w_nightmare_owl(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.3, 2.0, 70, 0.4)
    key(pet, 1.0, loc=(0, 0, 1.5)), key(pet, 2.0, loc=(0, 0, 1.5))
    for k in range(3):
        grow("FX Black Hole", f"ring{k}", 1.6 + k * 0.25, 2.4 + k * 0.25, (0, 0, 1.0), 0.2, 2.5 + k, rot0=(90, 0, 0), rot1=(90, 0, 120), fade=(2.6 + k * 0.25, 3.2 + k * 0.25))
    rest(pet, bones, 3.2)
    cam_orbit(cam, 0, 4.8, 9, 3, 1.8)
    ev(1.6, "flash:000000:0.85"), ev(1.6, "shake:2"), ev(1.6, "sound:Legendary"), finale("B45CFF")


def w_zombie_bear(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.4, rot=(0, 0, 0)), key(bones["head"], 0.8, rot=(-60, 0, 0)), key(bones["head"], 2.8, rot=(-60, 0, 30)), key(bones["head"], 3.2, rot=(0, 0, 0))
    key(pet, 0.8, loc=(0, 0, 0)), key(pet, 1.6, loc=(1.5, 0, 0), rot=(0, 0, 40)), key(pet, 2.4, loc=(-1.5, 0.5, 0), rot=(0, 0, -40)), key(pet, 3.0, loc=(0, 0, 0.8), rot=(0, 0, 0))
    rest(pet, bones, 3.4)
    cam_orbit(cam, 0, 4.8, 7, 2.5, 1.4)
    ev(0.8, "sound:Error"), ev(3.2, "burst:7AA06A:40"), ev(3.3, "shake:1.2"), finale("B8FF4A")


def w_reaper_raven(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.3, 2.6, 50, 0.3)
    grow("FX Scythe", "scy", 0.6, 1.2, (0, 1.4, 1.8), 0.2, 1.6, rot0=(0, 90, 0), rot1=(0, 90, 0), fade=(2.6, 3.0))
    s = hidden_prop("FX Scythe", "swing")
    key(s, 1.2, loc=(0, 1.0, 1.5), rot=(0, 90, -60), scale=1.8, alpha=1)
    key(s, 1.3, alpha=0)
    key(s, 1.7, rot=(0, 90, 200))
    key(s, 2.0, alpha=1)
    grow("FX Black Hole", "wave", 1.6, 2.4, (0, 0, 0.3), 0.2, 3.5, rot0=(90, 0, 0), rot1=(90, 0, 0), fade=(2.4, 3.0))
    cam_orbit(cam, 0, 4.8, 9, 3, 1.8)
    rest(pet, bones, 4.8)
    ev(1.6, "flash:B45CFF:0.6"), ev(1.6, "shake:1.8"), ev(1.6, "sound:Legendary"), finale("B45CFF")


def w_haunted_doll_cat(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.6, rot=(0, 0, 0)), key(bones["head"], 2.6, rot=(0, 0, 360))
    vanish(pet, 2.9, 3.7)
    key(pet, 3.5, loc=(0, -2.5, 0))
    key(pet, 4.3, loc=(0, 0, 0))
    shot(cam, 0, (1.5, 5, 1.6), (0, 0, 1.6))
    shot(cam, 2.6, (0.8, 3.5, 1.8), (0, 0, 1.8))
    cam_end(cam)
    rest(pet, bones, 4.8)
    ev(0.6, "sound:Tick"), ev(2.9, "flash:000000:0.8"), ev(3.7, "sound:Error"), finale("FF8AB8")


def w_tropical_phoenix(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.2, 3.6, 50, 0.26)
    key(pet, 1.4, loc=(0, 0, 3), rot=(0, 0, 360)), key(pet, 2.8, loc=(0, 0, 3.4), rot=(0, 0, 720))
    spray("FX Star", "spark", 12, 1.4, 3.0, (0, 0, 3), 5, 1, 0.8)
    rest(pet, bones, 4.0)
    cam_orbit(cam, 0, 4.0, 9, 2.5, 2.5)
    cam_end(cam)
    ev(1.4, "burst:FF6AD5:60"), ev(1.4, "sound:Legendary"), finale("1CB4A8")


def w_bubblegum_flamingo(pet, bones, cam):
    rest(pet, bones, 0)
    b = grow("FX Bubble", "bubble", 0.4, 1.4, (0, 0.8, 0.5), 0.1, 1.2, fade=(3.6, 3.8))
    key(b, 2.0, loc=(0, 0, 0)), key(b, 3.4, loc=(0, 0, 3), rot=(0, 0, 180))
    key(pet, 1.6, loc=(0, 0, 0.4)), key(pet, 2.0, loc=(0, 0, 0.6)), key(pet, 3.4, loc=(0, 0, 3.6), rot=(0, 0, 180))
    rest(pet, bones, 4.3)
    cam_orbit(cam, 0, 4.3, 8, 2.5, 2.5)
    cam_end(cam)
    ev(3.6, "burst:FF8AD8:60"), ev(3.6, "sound:Legendary"), finale("FF8AD8")


def w_watermelon_turtle(pet, bones, cam):
    rest(pet, bones, 0)
    key(pet, 0.4, rot=(0, 0, 0)), key(pet, 2.4, rot=(0, 0, 1440))
    spray("FX Melon Slice", "slice", 14, 0.8, 2.6, (0, 0, 1.0), 5, 2.5, 1.4)
    cam_orbit(cam, 0, 4.8, 8, 3, 1.2)
    rest(pet, bones, 4.8)
    ev(0.8, "sound:Legendary"), ev(0.8, "burst:FF4A5A:40"), finale("4CB44A")


def w_choco_croc(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.4, rot=(0, 0, 0)), key(bones["head"], 0.8, rot=(-30, 0, 0)), key(bones["head"], 2.6, rot=(-30, 0, 0)), key(bones["head"], 3.0, rot=(0, 0, 0))
    spray("FX Choco Coin", "coin", 18, 0.9, 2.8, (0, 1.2, 2.0), 5, 3, 1.4)
    cam_orbit(cam, 0, 4.8, 8, 3, 1.5)
    rest(pet, bones, 4.8)
    ev(0.9, "sound:Cash"), ev(0.9, "burst:FFC21C:50"), finale("C8905A")


def w_toymaster(pet, bones, cam):
    rest(pet, bones, 0)
    toys = ("Tennis Ball", "Rubber Duck", "Frisbee", "Yarn Ball", "Teddy Bear", "Toy Rocket", "Robot Toy", "Crystal Orb")
    for k, toy in enumerate(toys):
        a = 2 * _m.pi * k / len(toys)
        ob = hidden_prop(toy, f"toy{k}")
        key(ob, 0.4 + k * 0.08, loc=(0, 0, 3), scale=0.1, alpha=0)
        key(ob, 1.6, loc=(_m.cos(a) * 3, _m.sin(a) * 3, 2 + (k % 3) * 0.6), rot=(0, 0, 90), scale=0.9)
        key(ob, 3.2, loc=(_m.cos(a + 2) * 3, _m.sin(a + 2) * 3, 2 + (k % 3) * 0.6), rot=(0, 0, 360))
        key(ob, 3.8, loc=(0, 0, 3), scale=0.1, alpha=1)
    jump(pet, 3.6, 4.4, 1.5, 360)
    cam_orbit(cam, 0, 4.8, 9, 3.5, 2)
    ev(0.4, "sound:Legendary"), ev(3.8, "flash:FFC21C:0.6"), finale("FF2A6A")


def w_space_hamster(pet, bones, cam):
    rest(pet, bones, 0)
    ball = grow("FX Hamster Ball", "ball", 0.3, 0.8, (0, 0, 0), 0.1, 1.0, fade=(4.0, 4.4))
    for k in range(9):
        t = 0.9 + k * 0.33
        a = _m.radians(k * 45)
        p = (_m.cos(a) * 4, _m.sin(a) * 4 - 1, 2 + _m.sin(k) * 0.8)
        key(pet, t, loc=p, rot=(k * 60, 0, k * 45))
        key(ball, t, loc=(p[0], p[1], p[2] - 1.2), rot=(k * 60, 0, k * 45))
    rest(pet, bones, 4.2)
    cam_orbit(cam, 0, 4.2, 11, 4, 2)
    cam_end(cam)
    ev(0.3, "sound:Rare"), ev(4.0, "burst:8FF0FF:40"), finale("8FF0FF")


def w_mecha_spider(pet, bones, cam):
    rest(pet, bones, 0)
    key(pet, 0.5, loc=(0, 0, 0)), key(pet, 1.0, loc=(0, 0, 1.2), scale=(1.4, 1.4, 1.1))
    grow("FX Web", "web", 1.0, 2.0, (0, -2, 0), 0.1, 1.6, fade=(3.8, 4.4))
    key(pet, 3.6, loc=(0, 0, 1.2), scale=(1.4, 1.4, 1.1))
    rest(pet, bones, 4.2)
    cam_orbit(cam, 0, 4.8, 9, 3, 2)
    ev(1.0, "sound:Legendary"), ev(2.0, "flash:5CE6FF:0.5"), finale("5CE6FF")


def w_mecha_lion(pet, bones, cam):
    rest(pet, bones, 0)
    key(pet, 0.4, rot=(0, 0, 0), scale=1)
    key(pet, 1.2, loc=(0, 0, 0), rot=(-60, 0, 0), scale=1.6)
    grow("FX Laser", "laser", 1.4, 1.6, (0, 1.6, 4.0), 0.2, 1.0, rot0=(-10, 0, 0), rot1=(-10, 0, 0), fade=(2.8, 3.1))
    key(pet, 3.0, rot=(-60, 0, 0), scale=1.6)
    rest(pet, bones, 3.8)
    cam_orbit(cam, 0, 4.8, 11, 3, 3, 40, 120)
    ev(1.2, "flash:5CE6FF:0.6"), ev(1.4, "shake:2.4"), ev(1.4, "sound:Legendary"), ev(1.4, "burst:FF2A6A:50"), finale("FF2A6A")


def w_marshmallow_sheep(pet, bones, cam):
    rest(pet, bones, 0)
    key(pet, 0.3, scale=1), key(pet, 1.0, scale=5.0)
    for k, t in enumerate((1.2, 1.8, 2.4)):
        key(pet, t, loc=(0, 0, 0), scale=(5.4, 5.4, 4.2)), key(pet, t + 0.3, loc=(0, 0, 3 - k * 0.6), scale=5.0)
        ev(t, "shake:1.6")
    key(pet, 2.8, loc=(0, 0, 0), scale=5.0), key(pet, 3.4, scale=1)
    rest(pet, bones, 4.0)
    shot(cam, 0, (4, 10, 3), (0, 0, 1.5)), shot(cam, 1.0, (8, 22, 10), (0, 0, 6)), shot(cam, 2.8, (8, 22, 10), (0, 0, 6))
    cam_end(cam)
    ev(1.0, "sound:Legendary"), finale("FFD0E8")


def w_pizza_cat(pet, bones, cam):
    rest(pet, bones, 0)
    key(pet, 0.4, rot=(0, 0, 0), loc=(0, 0, 0)), key(pet, 2.6, rot=(0, 0, 1800), loc=(0, 0, 1.0)), key(pet, 3.0, rot=(0, 0, 1800), loc=(0, 0, 0))
    spray("FX Pepperoni", "pep", 14, 0.8, 2.8, (0, 0, 1.4), 6, 2.0, 2.0)
    cam_orbit(cam, 0, 4.8, 8, 3, 1.3)
    rest(pet, bones, 4.8)
    ev(0.8, "sound:Legendary"), ev(0.8, "burst:C8301C:40"), finale("F0C860")


def w_frozen_mammoth_king(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.4, rot=(0, 0, 0)), key(bones["head"], 1.0, rot=(30, 0, 0)), key(bones["head"], 2.2, rot=(30, 0, 0)), key(bones["head"], 2.6, rot=(0, 0, 0))
    jump(pet, 1.0, 1.8, 1.5)
    grow("FX Ice Floor", "ice", 1.8, 2.6, (0, 0, 0.02), 0.1, 2.0, fade=(4.0, 4.6))
    grow("FX Crystal Ring", "ring", 1.8, 2.8, (0, 0, 0), 0.3, 3.0, fade=(3.2, 4.0))
    cam_orbit(cam, 0, 4.8, 11, 4, 2)
    rest(pet, bones, 4.8)
    ev(1.8, "shake:2.5"), ev(1.8, "flash:E8FAFF:0.8"), ev(1.8, "sound:Legendary"), finale("6FF0FF")


def w_frost_saber(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.3, rot=(0, 0, 0)), key(bones["head"], 0.8, rot=(-25, 0, 0)), key(bones["head"], 1.6, rot=(-25, 0, 0)), key(bones["head"], 2.0, rot=(0, 0, 0))
    for k in range(10):
        a = 2 * _m.pi * k / 10
        grow("FX Diamond", f"ice{k}", 1.0 + k * 0.03, 1.4, (_m.cos(a) * 2.5, _m.sin(a) * 2.5, 0), 0.1, 3.0, rot1=(45, 0, _m.degrees(a)), fade=(3.6, 4.2))
    cam_orbit(cam, 0, 4.8, 9, 3, 1.5)
    rest(pet, bones, 4.8)
    ev(0.8, "sound:Legendary"), ev(1.0, "shake:2.2"), ev(1.0, "burst:C8F6FF:80"), ev(1.0, "shock:8FF0FF"), finale("6FF0FF")


def w_ice_cream_penguin(pet, bones, cam):
    rest(pet, bones, 0)
    grow("FX Ice Cream Cone", "cone", 0.3, 1.0, (0, -2, 0), 0.1, 1.4, fade=(4.0, 4.5))
    key(pet, 1.2, loc=(0, -2, 6.5), rot=(0, 0, 0))
    key(pet, 2.2, loc=(0, -1.5, 3.5), rot=(40, 0, 0))
    key(pet, 3.0, loc=(0, 1.5, 0.3), rot=(10, 0, 0))
    rest(pet, bones, 3.5)
    cam_orbit(cam, 0, 4.8, 9, 3.5, 2.5, 60, 130)
    ev(0.3, "sound:Rare"), ev(3.0, "burst:FF9AC8:50"), ev(3.0, "sound:Legendary"), finale("FF9AC8")


def w_mycelium_dragon(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.3, 3.4, 45, 0.3)
    key(pet, 1.4, loc=(0, 0, 2.5), rot=(-20, 0, 0)), key(pet, 2.8, loc=(0, 0, 2.6), rot=(-15, 0, 360))
    for k in range(6):
        a = 2 * _m.pi * k / 6
        grow("FX Tree", f"shroom{k}", 1.6 + k * 0.1, 2.4 + k * 0.1, (_m.cos(a) * 3.5, _m.sin(a) * 3.5, 0), 0.1, 1.5, fade=(4.0, 4.6))
    rest(pet, bones, 3.6)
    cam_orbit(cam, 0, 4.8, 10, 4, 2)
    ev(1.6, "burst:B8FF4A:60"), ev(1.6, "sound:Legendary"), finale("B8FF4A")


def w_crystal_butterfly(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.2, 1.4, 60, 0.3)
    key(pet, 1.0, loc=(0, 0, 1.5)), key(pet, 1.4, loc=(0, 0, 1.6), scale=1.3)
    spray("FX Diamond", "crys", 16, 1.5, 3.2, (0, 0, 2), 6, 2.5, 1.4)
    rest(pet, bones, 3.6)
    cam_orbit(cam, 0, 4.8, 9, 3, 1.8)
    ev(1.5, "flash:FF8AD8:0.8"), ev(1.5, "burst:8FF0FF:100"), ev(1.5, "shake:1.6"), ev(1.5, "sound:Legendary"), finale("FF8AD8")


def w_divine_seraphim(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.2, 3.6, 55, 0.3)
    key(pet, 1.6, loc=(0, 0, 3.5), rot=(0, 0, 180)), key(pet, 3.2, loc=(0, 0, 3.8), rot=(0, 0, 360))
    grow("FX Gold Wings", "gw", 1.0, 1.8, (0, -0.5, 2.0), 0.1, 2.0, fade=(3.6, 4.2), parent=pet)
    rain("FX Star", "star", 14, 1.6, 3.4, 5, 9)
    rest(pet, bones, 4.2)
    cam_orbit(cam, 0, 4.2, 10, 1.5, 3.5, 0, 120)
    cam_end(cam)
    ev(1.6, "flash:FFFFFF:0.85"), ev(1.6, "sound:Legendary"), finale("FFE45C")


def w_celestial_emperor(pet, bones, cam):
    rest(pet, bones, 0)
    grow("FX Throne", "throne", 0.3, 1.2, (0, -1.6, 0), 0.1, 1.2, fade=(4.2, 4.6))
    key(pet, 1.4, loc=(0, 0, 0)), key(pet, 1.8, loc=(0, -1.2, 2.4)), key(pet, 2.1, loc=(0, -1.6, 1.2))
    key(pet, 3.6, loc=(0, -1.6, 1.2)), key(pet, 4.1, loc=(0, 0, 0))
    cam_orbit(cam, 0, 4.8, 9, 3, 1.8, 0, 60)
    rest(pet, bones, 4.6)
    ev(2.6, "flash:FFD84A:0.9"), ev(2.6, "burst:FFC21C:120"), ev(2.6, "shake:2.2"), ev(2.6, "shock:FFC21C"), ev(2.6, "sound:Legendary"), finale("FFC21C")


def w_infinity_serpent(pet, bones, cam):
    rest(pet, bones, 0)
    for k in range(13):
        t = 0.3 + k * 0.25
        a = 2 * _m.pi * k / 12
        key(pet, t, loc=(2.4 * _m.cos(a), 0, 2.5 + 1.2 * _m.sin(2 * a)), rot=(0, -_m.degrees(_m.atan2(2.4 * _m.cos(2 * a), -2.4 * _m.sin(a))), 90))
    grow("FX Infinity", "inf", 1.0, 2.0, (0, 0, 0), 0.1, 1.3, fade=(3.6, 4.2))
    rest(pet, bones, 4.0)
    shot(cam, 0, (0, 11, 3), (0, 0, 2.5)), shot(cam, 3.5, (2, 12, 4), (0, 0, 2.5))
    cam_end(cam)
    ev(3.3, "shock:FF4A5A"), ev(3.3, "flash:FFFFFF:0.6"), ev(3.3, "sound:Legendary"), finale("9B5CFF")


def w_infinity_dragon(pet, bones, cam):
    rest(pet, bones, 0)
    vanish(pet, 0.6, 3.0)
    spray("FX Diamond", "shard", 20, 0.6, 2.6, (0, 0, 2), 4, 1.5, 1.0, fall=False)
    key(pet, 3.0, scale=0.01), key(pet, 3.5, scale=1.8), key(pet, 4.2, scale=1)
    cam_orbit(cam, 0, 4.8, 10, 4, 2)
    rest(pet, bones, 4.8)
    ev(0.6, "burst:C8A8FF:80"), ev(0.6, "sound:Error"), ev(3.0, "flash:FFFFFF:0.85"), ev(3.0, "sound:Legendary"), finale("C8A8FF")


def w_eternal_wolf(pet, bones, cam):
    rest(pet, bones, 0)
    if "head" in bones:
        key(bones["head"], 0.3, rot=(0, 0, 0)), key(bones["head"], 0.8, rot=(40, 0, 0)), key(bones["head"], 2.2, rot=(42, 0, 0)), key(bones["head"], 2.6, rot=(0, 0, 0))
    grow("FX Moon", "moon", 0.8, 2.0, (0, -8, 9), 0.1, 2.0, fade=(4.0, 4.6))
    key(pet, 2.4, scale=1), key(pet, 2.8, scale=1.4), key(pet, 3.3, scale=1)
    shot(cam, 0, (3, 7, 1.2), (0, 0, 1.6)), shot(cam, 1.6, (2, 9, 1.0), (0, -6, 7))
    cam_end(cam)
    rest(pet, bones, 4.8)
    ev(0.8, "sound:Legendary"), ev(2.8, "flash:C8D8FF:0.8"), ev(2.8, "burst:C8D8FF:60"), finale("C8D8FF")


def w_world_ender(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.3, 3.6, 45, 0.35)
    key(pet, 1.4, loc=(0, 0, 3), rot=(-25, 0, 0), scale=1.5)
    grow("FX Meteor", "m1", 1.6, 2.4, (3, 4, 12), 0.5, 1.5, fade=(2.4, 2.6))
    grow("FX Meteor", "m2", 1.8, 2.6, (-4, 2, 12), 0.5, 1.5, fade=(2.6, 2.8))
    grow("FX Lava Cracks", "cr", 2.5, 3.0, (0, 0, 0.02), 0.2, 2.5, fade=(4.2, 4.7))
    rest(pet, bones, 3.8)
    cam_orbit(cam, 0, 4.8, 13, 5, 2.5)
    ev(2.5, "shake:3"), ev(2.5, "flash:FF3B1C:0.85"), ev(2.5, "burst:FF3B1C:120"), ev(1.4, "sound:Legendary"), finale("FF3B1C")


def w_demon_dragon(pet, bones, cam):
    rest(pet, bones, 0)
    flap(bones, 0.3, 3.2, 45, 0.3)
    key(pet, 1.2, loc=(0, 0, 2.2), rot=(-15, 0, 0))
    grow("FX Laser", "breath", 1.4, 1.6, (0, 1.8, 3.2), 0.2, 0.7, rot0=(-25, 0, 0), rot1=(-25, 0, 0), fade=(2.8, 3.1))
    grow("FX Lava Cracks", "cr", 1.6, 2.0, (0, 5, 0.02), 0.2, 1.8, fade=(4.0, 4.5))
    rest(pet, bones, 3.6)
    cam_orbit(cam, 0, 4.8, 11, 4, 2)
    ev(1.4, "shake:2"), ev(1.4, "sound:Legendary"), ev(1.6, "burst:FF5A1C:60"), finale("B0102A")


def w_magma_phoenix(pet, bones, cam):
    rest(pet, bones, 0)
    key(pet, 0.8, scale=1.2)
    vanish(pet, 1.0, 2.6)
    spray("FX Meteor", "lava", 8, 1.0, 2.4, (0, 0, 1.6), 4, 2, 0.4)
    flap(bones, 2.6, 4.0, 60, 0.25)
    key(pet, 3.0, loc=(0, 0, 1.5)), key(pet, 3.6, loc=(0, 0, 1.5))
    rest(pet, bones, 4.2)
    cam_orbit(cam, 0, 4.8, 9, 3, 1.8)
    ev(1.0, "flash:FF5A1C:0.85"), ev(1.0, "burst:FF5A1C:100"), ev(1.0, "shake:2"), ev(2.6, "flash:FFD23C:0.7"), ev(2.6, "sound:Legendary"), finale("FF5A1C")


def w_void_creature(pet, bones, cam):
    rest(pet, bones, 0)
    bh = grow("FX Black Hole", "hole", 0.3, 1.0, (0, 0, 1.5), 0.1, 1.8, rot0=(90, 0, 0), rot1=(90, 0, 360), fade=(2.2, 2.6))
    key(pet, 1.0, loc=(0, 0, 0), rot=(0, 0, 0), scale=1)
    key(pet, 1.8, loc=(0, 0, 1.5), rot=(0, 0, 720), scale=0.01, alpha=1)
    key(pet, 3.0, loc=(0, -5, 0), scale=0.01, alpha=1)
    key(pet, 3.3, loc=(0, -5, 0), scale=1.2, alpha=0)
    key(pet, 4.2, loc=(0, 0, 0), rot=(0, 0, 720), scale=1)
    key(pet, 4.8, loc=(0, 0, 0), rot=(0, 0, 720), scale=1)
    cam_orbit(cam, 0, 4.8, 10, 3, 1.5)
    ev(0.3, "sound:Error"), ev(1.8, "flash:000000:0.85"), ev(3.0, "burst:B45CFF:60"), ev(3.0, "sound:Legendary"), finale("B45CFF")


W2 = {
    "Ancient Dragon": w_ancient_dragon, "Skeleton Rex": w_skeleton_rex, "Earth Turtle": w_earth_turtle,
    "Pharaoh Cat": w_pharaoh_cat, "Golden Sphinx": w_golden_sphinx, "Lava Scorpion": w_lava_scorpion,
    "Sakura Kitsune": w_sakura_kitsune, "Kitsune": w_kitsune, "Nine-Tailed Fox": w_nine_tailed_fox,
    "Atlantis Leviathan": w_leviathan, "Sea Serpent": w_sea_serpent, "Cyber Shark": w_cyber_shark,
    "Alien Octopus": w_alien_octopus, "Cosmic Jellyfish": w_cosmic_jellyfish,
    "Cloud Emperor": w_cloud_emperor, "Celestial Unicorn": w_celestial_unicorn, "Thunder Wolf": w_thunder_wolf,
    "Wind Spirit Deer": w_wind_deer, "Godly Owl": w_godly_owl,
    "Pumpkin Reaper": w_pumpkin_reaper, "Phantom Bunny": w_phantom_bunny, "Nightmare Owl": w_nightmare_owl,
    "Zombie Bear": w_zombie_bear, "Reaper Raven": w_reaper_raven, "Haunted Doll Cat": w_haunted_doll_cat,
    "Tropical Phoenix": w_tropical_phoenix, "Bubblegum Flamingo": w_bubblegum_flamingo,
    "Watermelon Turtle": w_watermelon_turtle, "Chocolate Crocodile": w_choco_croc,
    "Ultimate Toymaster": w_toymaster, "Space Hamster": w_space_hamster, "Mecha Spider": w_mecha_spider,
    "Mecha Lion": w_mecha_lion, "Pizza Cat": w_pizza_cat, "Marshmallow Sheep": w_marshmallow_sheep,
    "Frozen Mammoth King": w_frozen_mammoth_king, "Frost Saber": w_frost_saber, "Ice Cream Penguin": w_ice_cream_penguin,
    "Mycelium Dragon": w_mycelium_dragon, "Crystal Butterfly": w_crystal_butterfly,
    "Divine Seraphim": w_divine_seraphim, "Celestial Emperor": w_celestial_emperor, "Infinity Serpent": w_infinity_serpent,
    "Infinity Dragon": w_infinity_dragon, "Eternal Wolf": w_eternal_wolf,
    "World Ender": w_world_ender, "Demon Dragon": w_demon_dragon, "Magma Phoenix": w_magma_phoenix, "Void Creature": w_void_creature,
}
