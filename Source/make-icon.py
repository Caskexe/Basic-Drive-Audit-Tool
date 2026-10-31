# Icon generator for Basic Drive Audit Tool (BDAT)
# Run instructions: python make-icon.py (outputs drive-audit.ico and icon-preview.png)
# Requirements: Pillow (pip install pillow)
# Author: CASK.exe - https://github.com/Caskexe

from PIL import Image, ImageDraw

# Draw at a large size then scale down so the edges stay smooth
S = 1024
img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Colours
BODY = "#1F2933"
BODY_TOP = "#323F4B"
OUTLINE = "#0B0F14"
PLATTER = "#9FB3C8"
HUB = "#1F2933"
PANEL = "#171E26"
LED = "#3DDC84"
GOLD = "#F5B83D"
SLOT = "#3E4C59"

# Drive case with a lighter top half
d.rounded_rectangle((70, 190, 954, 800), radius=100, fill=BODY)
d.rounded_rectangle((70, 190, 954, 500), radius=100, fill=BODY_TOP)
d.rectangle((70, 400, 954, 500), fill=BODY_TOP)
d.rounded_rectangle((70, 190, 954, 800), radius=100, outline=OUTLINE, width=18)

# Platter with hub and read arm
d.ellipse((170, 270, 560, 660), fill=PLATTER, outline=OUTLINE, width=14)
d.ellipse((270, 370, 460, 560), outline=BODY_TOP, width=10)
d.ellipse((330, 430, 400, 500), fill=HUB)
d.line((650, 300, 470, 460), fill="#E4E7EB", width=38)
d.ellipse((630, 280, 676, 326), fill="#E4E7EB")

# Bottom panel with activity light and vent slots
d.rounded_rectangle((88, 690, 936, 782), radius=70, fill=PANEL)
d.rectangle((88, 690, 936, 730), fill=PANEL)
d.ellipse((150, 714, 190, 754), fill=LED)
for i in range(6):
	x = 600 + i * 55
	d.rounded_rectangle((x, 712, x + 26, 764), radius=9, fill=SLOT)

# Magnifying glass: handle first, then a translucent lens on top
cx, cy, r = 700, 540, 190
hx, hy = cx + int(r * 0.72), cy + int(r * 0.72)
d.line((hx, hy, 940, 960), fill=GOLD, width=84)
lens = Image.new("RGBA", (S, S), (0, 0, 0, 0))
ld = ImageDraw.Draw(lens)
ld.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(159, 179, 200, 120))
img = Image.alpha_composite(img, lens)
d = ImageDraw.Draw(img)
d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=GOLD, width=48)

# Export a multi-size ICO plus a preview image
final = img.resize((256, 256), Image.LANCZOS)
final.save("drive-audit.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])
img.resize((512, 512), Image.LANCZOS).save("icon-preview.png")
print("Created drive-audit.ico")
