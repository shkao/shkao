from PIL import Image, ImageDraw, ImageFont

SCREEN_W, SCREEN_H = 340, 736
STATUS = 51
RIM = 5
BEZEL = 7
BTN = 3
EDGE = RIM + BEZEL
W = SCREEN_W + 2 * (EDGE + BTN)
H = SCREEN_H + 2 * EDGE
X0 = BTN
SX, SY = X0 + EDGE, EDGE

SS = 8
img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

SILVER = (208, 208, 212, 255)
SILVER_DK = (150, 150, 155, 255)
APP_BG = (22, 19, 15, 255)
FG = (255, 255, 255, 235)
FG_DIM = (255, 255, 255, 120)

for x0, y0, x1, y1 in [
    (0, 120, X0 + 6, 146),
    (0, 168, X0 + 6, 214),
    (0, 224, X0 + 6, 270),
    (W - X0 - 6, 186, W, 262),
]:
    d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), radius=2 * SS, fill=SILVER, outline=SILVER_DK, width=SS)

body = (X0 * SS, 0, (W - X0) * SS - 1, H * SS - 1)
d.rounded_rectangle(body, radius=56 * SS, fill=SILVER)
d.rounded_rectangle(body, radius=56 * SS, outline=SILVER_DK, width=SS)

inner = ((X0 + RIM) * SS, RIM * SS, (W - X0 - RIM) * SS - 1, (H - RIM) * SS - 1)
d.rounded_rectangle(inner, radius=51 * SS, fill=(8, 8, 9, 255))

BOTTOM = 16                       # safe-area bar under the tab bar
Y2 = SY + SCREEN_H - BOTTOM - 2   # video hole bottom; covers the viewport's bottom edge rows
screen = (SX * SS, SY * SS, (SX + SCREEN_W) * SS - 1, (SY + SCREEN_H) * SS - 1)
d.rounded_rectangle(screen, radius=44 * SS, fill=APP_BG)
d.rounded_rectangle((SX * SS, (SY + STATUS) * SS, (SX + SCREEN_W) * SS - 1, Y2 * SS - 1), radius=44 * SS, fill=(0, 0, 0, 0), corners=(False, False, True, True))

iw, ih = 96, 26
ix = (W - iw) // 2
iy = SY + 9
d.rounded_rectangle((ix * SS, iy * SS, (ix + iw) * SS, (iy + ih) * SS), radius=(ih // 2) * SS, fill=(10, 10, 10, 255))

# ---- status bar, all glyphs share vertical center cy ----
cy = iy + ih / 2
font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14 * SS, index=1)
d.text(((SX + 36) * SS, int(cy * SS)), "9:41", font=font, fill=FG, anchor="mm")

GAP = 7  # gap between glyph clusters

# battery: 24x12 body + nub, centered on cy
bw, bh = 24, 12
bx1 = SX + SCREEN_W - 27          # body right edge (nub adds 2)
bx0 = bx1 - bw
d.rounded_rectangle((bx0 * SS, int((cy - bh / 2) * SS), bx1 * SS, int((cy + bh / 2) * SS)), radius=3 * SS, outline=FG_DIM, width=SS)
d.rounded_rectangle(((bx0 + 2) * SS, int((cy - bh / 2 + 2) * SS), (bx1 - 7) * SS, int((cy + bh / 2 - 2) * SS)), radius=2 * SS, fill=FG)
d.rounded_rectangle(((bx1 + 1) * SS, int((cy - 2.5) * SS), (bx1 + 3) * SS, int((cy + 2.5) * SS)), radius=SS, fill=FG_DIM)

# wifi: arcs fanning up from base point, base sits on the shared baseline
base_y = cy + 5.5
wx = bx0 - GAP - 9                # wifi center x (glyph is ~18 wide)
d.pieslice((int((wx - 2.6) * SS), int((base_y - 2.6 - 1.5) * SS), int((wx + 2.6) * SS), int((base_y + 2.6 - 1.5) * SS)), start=180, end=360, fill=FG)
for r in (5.8, 9.0):
    box = (int((wx - r) * SS), int((base_y - r) * SS), int((wx + r) * SS), int((base_y + r) * SS))
    d.arc(box, start=228, end=312, fill=FG, width=int(2.2 * SS))

# cellular: four bars, bottoms on the shared baseline
cx1 = wx - 9 - GAP                # right edge of bars
for i in range(4):
    h = 4.5 + i * 2.5
    x = cx1 - (3 - i) * 5 - 3
    d.rounded_rectangle((x * SS, int((base_y - h) * SS), (x + 3) * SS, int(base_y * SS)), radius=SS, fill=FG)

hw = 118
d.rounded_rectangle(((SX + (SCREEN_W - hw) // 2) * SS, (SY + SCREEN_H - 10) * SS, (SX + (SCREEN_W + hw) // 2) * SS, (SY + SCREEN_H - 6) * SS), radius=2 * SS, fill=(255, 255, 255, 220))

img = img.resize((W, H), Image.LANCZOS)
img.save("frame.png")

# geometry consumed by compose_gif.sh; keeps the ffmpeg filter in sync with this file
with open("frame.env", "w") as f:
    f.write(f"W={W}\nH={H}\nVX={SX}\nVY={SY + STATUS}\nVW={SCREEN_W}\nVH={SCREEN_H - STATUS - BOTTOM}\n")
print("ok")
