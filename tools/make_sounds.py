# Synthesizes every Throw a Toy sound effect + a music loop into assets/sounds/*.wav (no dependencies).
import math, os, random, struct, wave

SR = 44100
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "sounds")
os.makedirs(OUT, exist_ok=True)
random.seed(7)


def note(n):  # MIDI -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


def osc(kind, f, t, ph=0.0):
    x = (f * t + ph) % 1.0
    if kind == "sine":
        return math.sin(2 * math.pi * x)
    if kind == "square":
        return 1.0 if x < 0.5 else -1.0
    if kind == "saw":
        return 2 * x - 1
    if kind == "tri":
        return 4 * abs(x - 0.5) - 1
    raise ValueError(kind)


def env(t, dur, a=0.005, d=0.1, s=0.6, r=0.1):
    if t < a:
        return t / a
    if t < a + d:
        return 1 - (1 - s) * (t - a) / d
    if t < dur - r:
        return s
    return max(0.0, s * (dur - t) / r) if r > 0 else 0.0


def buf(sec):
    return [0.0] * int(SR * sec)


def add_tone(b, start, dur, freq, kind="sine", vol=0.5, a=0.005, d=0.08, s=0.6, r=0.08, slide=0.0, vib=0.0):
    i0 = int(start * SR)
    ph = 0.0
    for i in range(int(dur * SR)):
        if i0 + i >= len(b):
            break
        t = i / SR
        f = freq * (1 + slide * t / dur) * (1 + vib * math.sin(2 * math.pi * 6 * t))
        ph += f / SR
        b[i0 + i] += vol * env(t, dur, a, d, s, r) * osc(kind, 1, ph)


def add_noise(b, start, dur, vol=0.4, lp=0.2, a=0.002, r=None, sweep=0.0):
    i0 = int(start * SR)
    y = 0.0
    r = dur if r is None else r
    for i in range(int(dur * SR)):
        if i0 + i >= len(b):
            break
        t = i / SR
        k = min(0.99, max(0.005, lp * (1 + sweep * t / dur)))
        y += k * (random.uniform(-1, 1) - y)
        e = min(1, t / a) * max(0.0, 1 - max(0, t - (dur - r)) / r) if r > 0 else 1
        b[i0 + i] += vol * e * y


def chord(b, start, dur, notes, kind="saw", vol=0.18, **kw):
    for n in notes:
        add_tone(b, start, dur, note(n), kind, vol, **kw)
        add_tone(b, start, dur, note(n) * 1.004, kind, vol * 0.6, **kw)  # detune for width


def lowpass(b, k):
    y = 0.0
    for i, v in enumerate(b):
        y += k * (v - y)
        b[i] = y
    return b


def write(name, b, gain=0.9):
    peak = max(1e-6, max(abs(v) for v in b))
    path = os.path.join(OUT, name + ".wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, v / peak * gain)) * 32767)) for v in b))
    return path


S = {}
b = buf(0.08); add_tone(b, 0, 0.06, 1400, "square", 0.3, d=0.03, s=0.2, r=0.03); add_tone(b, 0, 0.05, 2100, "sine", 0.3); S["Click"] = b
b = buf(0.25); add_tone(b, 0, 0.22, 500, "tri", 0.5, slide=1.2); add_noise(b, 0, 0.2, 0.15, 0.3, sweep=2); S["Open"] = b
b = buf(0.5)
for i, n in enumerate((76, 81, 88)):
    add_tone(b, i * 0.07, 0.3, note(n), "square", 0.22, d=0.1, s=0.4, r=0.15)
    add_tone(b, i * 0.07, 0.3, note(n + 12), "sine", 0.18)
add_noise(b, 0, 0.12, 0.2, 0.6); S["Buy"] = b
b = buf(0.3); add_tone(b, 0, 0.12, 180, "square", 0.4); add_tone(b, 0.13, 0.15, 140, "square", 0.4); S["Error"] = b
b = buf(0.6); add_noise(b, 0, 0.55, 0.7, 0.05, sweep=6); add_tone(b, 0, 0.4, 220, "saw", 0.25, slide=2.5); S["Throw"] = b
b = buf(0.7)
add_noise(b, 0, 0.6, 0.5, 0.02, a=0.15, sweep=8)
for i, n in enumerate((72, 76, 79, 84)):
    add_tone(b, 0.05 + i * 0.06, 0.35, note(n), "tri", 0.25, r=0.2)
S["Zone"] = b
b = buf(0.9); add_tone(b, 0, 0.6, 110, "sine", 0.9, slide=-0.6, d=0.2, s=0.3, r=0.3); add_noise(b, 0, 0.5, 0.8, 0.08, r=0.45); add_noise(b, 0, 0.08, 0.6, 0.6); S["Land"] = b
b = buf(1.4)
for k in range(9):
    t = k * 0.15
    add_noise(b, t, 0.06, 0.5, 0.15, r=0.05)
    add_tone(b, t, 0.05, 90, "sine", 0.4)
S["Footsteps"] = b
b = buf(0.5)
for k in range(3):
    add_noise(b, k * 0.13, 0.08, 0.6, 0.25, r=0.06)
    add_tone(b, k * 0.13, 0.07, 300 + k * 40, "square", 0.15)
S["Munch"] = b
b = buf(0.07); add_tone(b, 0, 0.05, 1800, "sine", 0.6, d=0.02, s=0.3, r=0.02); add_tone(b, 0, 0.03, 3600, "sine", 0.2); S["Tick"] = b
b = buf(1.0)
for i, n in enumerate((72, 76, 79, 84, 88)):
    add_tone(b, i * 0.06, 0.6, note(n), "tri", 0.3, r=0.4)
    add_tone(b, i * 0.06, 0.6, note(n + 12), "sine", 0.12, r=0.4)
S["Catch"] = b
b = buf(1.8)
for i, n in enumerate((67, 71, 74, 79, 83, 86, 91)):
    add_tone(b, i * 0.055, 1.0, note(n), "square", 0.12, d=0.2, s=0.4, r=0.6)
    add_tone(b, i * 0.055, 1.0, note(n), "tri", 0.2, r=0.6)
chord(b, 0.4, 1.3, (55, 62, 67, 71), "saw", 0.08, a=0.02, r=0.8)
add_noise(b, 0.4, 1.2, 0.25, 0.5, r=1.1)
S["Rare"] = lowpass(b, 0.5)
# Legendary fanfare: brass-like stacked saws, rising arpeggio, crash
b = buf(3.6)
add_noise(b, 0, 0.9, 0.5, 0.03, a=0.85, sweep=12)  # riser
for i, n in enumerate((60, 64, 67, 72, 76, 79, 84)):
    add_tone(b, 0.1 + i * 0.1, 0.25, note(n), "square", 0.1, r=0.1)
chord(b, 0.95, 0.35, (60, 67, 72, 76), "saw", 0.1, a=0.01, d=0.1, s=0.8, r=0.1)
chord(b, 1.3, 0.35, (62, 69, 74, 77), "saw", 0.1, a=0.01, d=0.1, s=0.8, r=0.1)
chord(b, 1.65, 1.8, (64, 71, 76, 79, 83), "saw", 0.11, a=0.02, d=0.3, s=0.7, r=1.0, vib=0.004)
add_tone(b, 0.95, 2.5, note(40), "saw", 0.25, a=0.01, r=1.2)
add_noise(b, 0.95, 2.4, 0.45, 0.7, a=0.002, r=2.3)  # crash
add_tone(b, 0.95, 0.5, 60, "sine", 0.9, slide=-0.5, r=0.4)  # boom
S["Legendary"] = lowpass(b, 0.35)
b = buf(0.6)
for i, n in enumerate((84, 91, 96)):
    add_tone(b, i * 0.05, 0.4, note(n), "sine", 0.3, r=0.3)
add_noise(b, 0, 0.3, 0.15, 0.8, r=0.28); S["Cash"] = b
b = buf(0.9)
for i, n in enumerate((72, 79, 84, 88, 91)):
    add_tone(b, i * 0.045, 0.5, note(n), "square", 0.16, d=0.1, s=0.4, r=0.3)
add_tone(b, 0, 0.6, 300, "saw", 0.15, slide=3); S["Perfect"] = lowpass(b, 0.4)
b = buf(0.18); add_tone(b, 0, 0.15, 520, "tri", 0.5, slide=0.6, r=0.1); add_noise(b, 0, 0.05, 0.2, 0.4); S["Rep"] = b

# Music: 8-bar upbeat loop at 128 BPM (bass, chords, lead, drums)
beat = 60 / 128
bars = 8
b = buf(bars * 4 * beat)
prog = [(60, 64, 67), (57, 60, 64), (65, 69, 72), (67, 71, 74)] * 2  # C Am F G
lead = [72, 74, 76, 79, 76, 74, 72, 74, 76, 76, 74, 72, 69, 72, 74, 76,
        77, 76, 74, 72, 74, 76, 79, 81, 79, 76, 74, 72, 74, 72, 71, 72]
for bar, ch in enumerate(prog):
    t0 = bar * 4 * beat
    for k in range(8):  # bass eighths
        add_tone(b, t0 + k * beat / 2, beat / 2 * 0.9, note(ch[0] - 24 + (7 if k % 4 == 3 else 0)), "square", 0.16, d=0.05, s=0.5, r=0.03)
    for k in (0, 1.5, 2.5):  # chord stabs
        for n in ch:
            add_tone(b, t0 + k * beat, beat * 0.45, note(n), "tri", 0.07, r=0.08)
    for k in range(4):  # drums
        t = t0 + k * beat
        add_tone(b, t, 0.12, 120, "sine", 0.6, slide=-0.7, d=0.05, s=0.2, r=0.05)  # kick
        add_noise(b, t + beat / 2, 0.04, 0.12, 0.9, r=0.03)  # hat
        if k in (1, 3):
            add_noise(b, t, 0.12, 0.3, 0.45, r=0.1)  # snare
for i, n in enumerate(lead * 2):
    add_tone(b, i * beat, beat * 0.8, note(n), "square", 0.06, d=0.05, s=0.6, r=0.05, vib=0.003)
S["Music"] = lowpass(b, 0.6)

for name, data in S.items():
    write(name, data, 0.6 if name == "Music" else 0.9)
print("wrote", len(S), "sounds to", os.path.abspath(OUT))
assert all(os.path.getsize(os.path.join(OUT, n + ".wav")) > 1000 for n in S)
