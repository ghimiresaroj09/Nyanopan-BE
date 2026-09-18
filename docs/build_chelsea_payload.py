"""Build the complete Chelsea Boot test payloads.

Run:  python docs/build_chelsea_payload.py
Out:  docs/chelsea_images/*.png          (10 real test photos)
      docs/chelsea_product.json          (full JSON body, data-URI pictures)
      docs/test_chelsea_boot_json.sh     (setup + JSON product create)
      docs/test_chelsea_boot_multipart.sh(setup + multipart product create)
"""

import base64
import io
import json
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
IMG_DIR = os.path.join(HERE, "chelsea_images")

COLORS = [
    # (name, key, price NPR, main rgb, side rgb)
    ("Black", "black", "12995.00", (30, 30, 30), (90, 90, 90)),
    ("Brown", "brown", "13495.00", (111, 78, 40), (160, 130, 90)),
    ("Tan", "tan", "11995.00", (210, 180, 140), (230, 210, 175)),
    ("Burgundy", "burgundy", "14995.00", (128, 0, 32), (170, 60, 80)),
    ("Grey", "grey", "12495.00", (128, 128, 128), (180, 180, 180)),
]
SIZES = ["39", "40", "41", "42", "43", "44", "45", "46", "47", "48"]


def png_bytes(rgb, size=(12, 12)):
    buf = io.BytesIO()
    Image.new("RGB", size, rgb).save(buf, format="PNG")
    return buf.getvalue()


def data_uri(rgb):
    return "data:image/png;base64," + base64.b64encode(png_bytes(rgb)).decode()


def main():
    os.makedirs(IMG_DIR, exist_ok=True)

    # -- 1. real PNG files (multipart script uses these) --
    for name, key, _price, main_rgb, side_rgb in COLORS:
        with open(os.path.join(IMG_DIR, f"{key}.png"), "wb") as f:
            f.write(png_bytes(main_rgb))
        with open(os.path.join(IMG_DIR, f"{key}_side.png"), "wb") as f:
            f.write(png_bytes(side_rgb))

    # -- 2. full JSON payload (data-URI pictures) --
    attribute_values = []
    for name, key, _price, main_rgb, side_rgb in COLORS:
        attribute_values.append({
            "key": key,
            "attribute": "Color",
            "attribute_value": name,
            "feature_image": {
                "file": data_uri(main_rgb),
                "title": f"{name} Chelsea Boot",
                "caption": f"{name} full-grain leather Chelsea boot",
                "alt": f"{name} Chelsea boot",
            },
            "additional_images": [{
                "file": data_uri(side_rgb),
                "title": f"{name} side view",
                "alt": f"{name} boot from the side",
            }],
        })
    for size in SIZES:
        attribute_values.append({"key": size, "attribute": "Size", "attribute_value": size})

    variants = []
    for _name, key, price, _a, _b in COLORS:
        for size in SIZES:
            variants.append({
                "price": price,
                "options": [{"key": key}, {"key": size}],
            })

    payload = {
        "name": "Chelsea Boot",
        "model": "chelsea",
        "gender": "MEN",
        "description": "Classic elastic-sided Chelsea boot in full-grain leather.",
        "general_information": "Handcrafted Goodyear-welted boot.",
        "materials_used": "Full-grain leather upper, rubber sole.",
        "category": "boots",
        "is_featured": True,
        "key_features": [
            {"title": "Upper Material", "value": "Full-grain leather"},
            {"title": "Sole", "value": "Rubber"},
            {"title": "Closure", "value": "Elastic side gore"},
        ],
        "attribute_values": attribute_values,
        "variants": variants,
    }
    with open(os.path.join(HERE, "chelsea_product.json"), "w") as f:
        json.dump(payload, f, indent=2, ensure_ascii=True)
        f.write("\n")

    setup = """# ---- API 1: prerequisites (safe to re-run; 400 "already exists" is fine) ----
echo "== category =="
curl -s -o /dev/null -w "POST categories HTTP %{http_code}\\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Boots","description":"Sturdy boots."}' $BASE/api/v1/admin/categories/
echo "== model =="
curl -s -o /dev/null -w "POST product-models HTTP %{http_code}\\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Chelsea","description":"Elastic-sided boot line."}' $BASE/api/v1/admin/product-models/
echo "== attributes + values (Color with 5, Size with 10) =="
curl -s -o /dev/null -w "POST Color HTTP %{http_code}\\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Color","requires_image":true,"value":["Black","Brown","Tan","Burgundy","Grey"]}' $BASE/api/v1/admin/attributes/
curl -s -o /dev/null -w "POST Size HTTP %{http_code}\\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Size","value":["39","40","41","42","43","44","45","46","47","48"]}' $BASE/api/v1/admin/attributes/
"""

    header = """#!/bin/bash
# Chelsea Boot test. 1) log in and paste the ACCESS token below. 2) run: bash docs/test_chelsea_boot_XXX.sh
BASE="http://127.0.0.1:8000"
TOKEN="PASTE_ACCESS_TOKEN_HERE"
"""

    # -- 3. JSON runner --
    json_runner = header + setup + """
# ---- API 2: product create (JSON, pictures inline as base64) ----
echo "== product (JSON) =="
curl -s -w "\\nHTTP %{http_code}\\n" -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data @docs/chelsea_product.json $BASE/api/v1/admin/products/ | python3 -c "
import json,sys
raw = sys.stdin.read()
body, _, status = raw.rpartition(chr(10)+'HTTP ')
print('HTTP', status.strip())
d = json.loads(body)
if not d.get('success'):
    print(json.dumps(d, indent=2)[:2000]); sys.exit(1)
p = d['data']
print('slug:', p['slug'], '| values:', len(p['attribute_values']), '| variants:', len(p['variants']))
print('first SKU:', p['variants'][0]['sku'], '| last SKU:', p['variants'][-1]['sku'])
print('first image:', p['attribute_values'][0]['feature_image']['url'][:70])
"
"""
    with open(os.path.join(HERE, "test_chelsea_boot_json.sh"), "w") as f:
        f.write(json_runner)

    # -- 4. multipart runner (same data, file parts instead of base64) --
    mp_values = []
    for name, key, _price, _a, _b in COLORS:
        mp_values.append({
            "key": key, "attribute": "Color", "attribute_value": name,
            "feature_image": {"file": f"{key}-feat", "title": f"{name} Chelsea Boot", "alt": f"{name} Chelsea boot"},
            "additional_images": [{"file": f"{key}-add", "title": f"{name} side view"}],
        })
    for size in SIZES:
        mp_values.append({"key": size, "attribute": "Size", "attribute_value": size})
    mp_variants = [
        {"price": price, "options": [{"key": key}, {"key": size}]}
        for _name, key, price, _a, _b in COLORS for size in SIZES
    ]
    file_parts = " ".join(
        f'-F {key}-feat=@docs/chelsea_images/{key}.png -F {key}-add=@docs/chelsea_images/{key}_side.png'
        for _n, key, _p, _a, _b in COLORS
    )
    mp_runner = (
        header + setup + "\n# ---- API 3: product create (multipart, binary files) ----\n"
        'echo "== product (multipart) ==\\n"\n'
        "curl -s -w \"\\nHTTP %{http_code}\\n\" -X POST -H \"Authorization: Bearer $TOKEN\" \\\n"
        '  -F name="Chelsea Boot" -F model="chelsea" -F gender="MEN" -F category="boots" \\\n'
        '  -F description="Classic elastic-sided Chelsea boot in full-grain leather." \\\n'
        "  -F is_featured=true \\\n"
        "  -F key_features='[{\"title\": \"Upper Material\", \"value\": \"Full-grain leather\"}, {\"title\": \"Sole\", \"value\": \"Rubber\"}, {\"title\": \"Closure\", \"value\": \"Elastic side gore\"}]' \\\n"
        f"  -F attribute_values='{json.dumps(mp_values, ensure_ascii=True)}' \\\n"
        f"  -F variants='{json.dumps(mp_variants, ensure_ascii=True)}' \\\n"
        f"  {file_parts} \\\n"
        "  $BASE/api/v1/admin/products/\n"
    )
    with open(os.path.join(HERE, "test_chelsea_boot_multipart.sh"), "w") as f:
        f.write(mp_runner)

    print(f"values: {len(attribute_values)} (5 colors + 10 sizes), variants: {len(variants)}")
    print("wrote chelsea_images/, chelsea_product.json, test_chelsea_boot_json.sh, test_chelsea_boot_multipart.sh")


if __name__ == "__main__":
    main()
