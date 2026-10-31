"""Rebuild the Workshop images that carry version text. Run from the repo root; needs Pillow."""
import glob, random
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1920, 1080
RED, GOLD, WHITE, GREY = (227, 10, 23), (236, 196, 90), (245, 245, 245), (190, 195, 205)
PANEL, EDGE, BAND = (13, 17, 26), (66, 72, 84), (9, 11, 16)
FONT = 'C:/Windows/Fonts/bahnschrift.ttf'
VERSION = 'MD 2.0.3'
OUT = '_workshop_gallery/'


def font(size, bold=True):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([700 if bold else 400, 100])
    return f


def mosaic(seed):
    """Dark wall of event pictures, the background of every card."""
    pics = sorted(glob.glob('gfx/event_pictures/turkey/*.dds'))
    random.Random(seed).shuffle(pics)
    img = Image.new('RGB', (W, H))
    for i in range(48):
        tile = Image.open(pics[i]).convert('RGB').crop((14, 12, 203, 151)).resize((240, 180), Image.LANCZOS)
        img.paste(tile, ((i % 8) * 240, (i // 8) * 180))
    img = img.filter(ImageFilter.GaussianBlur(1.2))
    return ImageEnhance.Brightness(img).enhance(0.2)


def footer(img, text):
    d = ImageDraw.Draw(img)
    d.rectangle((0, 1016, W, H), fill=BAND)
    d.rectangle((0, 1016, W, 1020), fill=RED)
    d.text((110, 1028), text, font=font(26), fill=GREY)


def hero():
    img = mosaic(7)
    old = Image.open(OUT + '01_hero.jpg').convert('RGB')
    img.paste(old.crop((1224, 294, 1818, 728)), (1224, 294))
    img.paste(old.crop((110, 150, 228, 229)), (110, 150))
    d = ImageDraw.Draw(img)
    d.text((104, 240), 'MILLENNIUM DAWN', font=font(112), fill=WHITE)
    d.text((104, 356), '+TURKEY', font=font(162), fill=RED)
    for y, line in ((558, 'The most detailed Turkey of Millennium Dawn,'), (614, 'for MD 2.0.3 and Hearts of Iron IV 1.19')):
        d.text((110, y), line, font=font(42, False), fill=GREY)
    x = 112
    for big, small, step in (('4,700+', 'FOCUSES', 300), ('19', 'POLITICAL PATHS', 270), ('1,200+', 'EVENTS', 270),
                             ('1,300+', 'NATIONAL SPIRITS', 330)):
        d.text((x, 758), big, font=font(76), fill=GOLD)
        d.text((x, 848), small, font=font(26), fill=WHITE)
        x += step
    footer(img, 'FULL TURKISH LANGUAGE SUPPORT  ·  TÜRKÇE DİL DESTEĞİ')
    img.save(OUT + '01_hero.jpg', quality=92)


def update():
    img = mosaic(11)
    d = ImageDraw.Draw(img)
    d.rectangle((110, 90, 119, 240), fill=RED)
    d.text((144, 88), 'UPDATE 2.0.3-TUR.8  ·  THE ATATÜRK UPDATE', font=font(32), fill=GOLD)
    d.text((140, 128), "What's New", font=font(88), fill=WHITE)
    rows = ('Atatürk path no longer softlocks', 'Atatürk wins the elections and leads the CHP', 'Return of the Father: +25% PP and building',
            'Atatürk focuses build twice the factories', 'Atatürk focuses give 50% more political power',
            'Path Guide: 10 pages with every date window', 'Tells you when to wait and for how long', '48 focuses had a condition the game ignored',
            '8 decisions lost half their effects: fixed', 'Fake tooltips and dead conditions removed')
    for i, text in enumerate(rows):
        x, y = (110 if i < 5 else 1000), 340 + (i % 5) * 110
        d.rounded_rectangle((x, y, x + 820, y + 88), radius=8, fill=PANEL, outline=EDGE, width=2)
        d.rectangle((x + 34, y + 36, x + 51, y + 53), fill=GOLD)
        d.text((x + 84, y + 22), text, font=font(34, False), fill=WHITE)
    footer(img, f'MILLENNIUM DAWN +TURKEY  ·  {VERSION}  ·  HOI4 1.19')
    img.save(OUT + '06_update.jpg', quality=92)


def refresh_footers():
    for name in ('02_paths.jpg', '03_events.jpg', '04_systems.jpg'):
        img = Image.open(OUT + name).convert('RGB')
        footer(img, f'MILLENNIUM DAWN +TURKEY  ·  {VERSION}  ·  HOI4 1.19')
        img.save(OUT + name, quality=92)


hero()
update()
refresh_footers()
