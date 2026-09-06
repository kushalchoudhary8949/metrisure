"""
Generates three realistic-looking package label images for demo purposes:
1. compliant_label.jpg      -> all mandatory fields present, clear text
2. missing_declaration.jpg  -> country of origin / consumer care / unit price missing
3. low_confidence_label.jpg -> all fields present but blurred/noisy (triggers REVIEW)
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import numpy as np

OUT_DIR = os.path.dirname(__file__)


def get_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def draw_label(lines, path, blur=False, noise=False, jpeg_quality=95):
    W, H = 900, 1100
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    # border like a real product label
    d.rectangle([10, 10, W - 10, H - 10], outline=(20, 20, 20), width=3)

    y = 50
    for text, size, bold, gap in lines:
        font = get_font(size, bold)
        d.text((45, y), text, fill=(10, 10, 10), font=font)
        y += gap

    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=2.0))

    if noise:
        np.random.seed(42)  # fixed seed -> reproducible REVIEW-band confidence every run
        arr = np.array(img).astype(np.int16)
        noise_arr = np.random.normal(0, 25, arr.shape).astype(np.int16)
        arr = np.clip(arr + noise_arr, 0, 255).astype("uint8")
        img = Image.fromarray(arr)

    img.save(path, quality=jpeg_quality)
    print("wrote", path)


# ---- Scenario 1: Fully compliant ----
draw_label(
    [
        ("SURYA GOLD REFINED SUNFLOWER OIL", 30, True, 55),
        ("", 10, False, 15),
        ("Net Quantity: 1 Litre", 24, False, 42),
        ("MRP: Rs. 189.00 (Incl. of all taxes)", 24, False, 42),
        ("Unit Sale Price: Rs. 189.00 per litre", 22, False, 40),
        ("Mfg. Date: 03/2026", 22, False, 40),
        ("Best Before: 12 months from Mfg. Date", 22, False, 42),
        ("Manufactured & Packed by:", 22, True, 32),
        ("Surya Agro Foods Pvt. Ltd.,", 22, False, 30),
        ("Plot 14, Industrial Area, Jaipur, Rajasthan - 302013", 20, False, 40),
        ("Country of Origin: India", 22, False, 42),
        ("Consumer Care: 1800-123-4567", 22, False, 30),
        ("care@suryaagro.example.com", 20, False, 42),
    ],
    os.path.join(OUT_DIR, "1_compliant_label.jpg"),
)

# ---- Scenario 2: Missing declarations (country of origin, consumer care, unit price) ----
draw_label(
    [
        ("SURYA GOLD REFINED SUNFLOWER OIL", 30, True, 55),
        ("", 10, False, 15),
        ("Net Quantity: 1 Litre", 24, False, 42),
        ("MRP: Rs. 189.00 (Incl. of all taxes)", 24, False, 42),
        ("Mfg. Date: 03/2026", 22, False, 40),
        ("Best Before: 12 months from Mfg. Date", 22, False, 42),
        ("Manufactured & Packed by:", 22, True, 32),
        ("Surya Agro Foods Pvt. Ltd.,", 22, False, 30),
        ("Plot 14, Industrial Area, Jaipur, Rajasthan - 302013", 20, False, 46),
    ],
    os.path.join(OUT_DIR, "2_missing_declaration.jpg"),
)

# ---- Scenario 3: Low confidence / blurry photo (all fields present but hard to read) ----
draw_label(
    [
        ("SURYA GOLD REFINED SUNFLOWER OIL", 30, True, 55),
        ("", 10, False, 15),
        ("Net Quantity: 1 Litre", 24, False, 42),
        ("MRP: Rs. 189.00 (Incl. of all taxes)", 24, False, 42),
        ("Unit Sale Price: Rs. 189.00 per litre", 22, False, 40),
        ("Mfg. Date: 03/2026", 22, False, 40),
        ("Best Before: 12 months from Mfg. Date", 22, False, 42),
        ("Manufactured & Packed by:", 22, True, 32),
        ("Surya Agro Foods Pvt. Ltd.,", 22, False, 30),
        ("Plot 14, Industrial Area, Jaipur, Rajasthan - 302013", 20, False, 40),
        ("Country of Origin: India", 22, False, 42),
        ("Consumer Care: 1800-123-4567", 22, False, 30),
        ("care@suryaagro.example.com", 20, False, 42),
    ],
    os.path.join(OUT_DIR, "3_low_confidence_label.jpg"),
    blur=True,
    noise=True,
    jpeg_quality=35,
)
