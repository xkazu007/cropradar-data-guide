#!/usr/bin/env python3
"""Build index.html for the CropRadar data-source guide site from the markdown guide."""
import re, html, pathlib

MD = pathlib.Path.home() / "workspace/cropradar/data-source-guide-wheat-barley.md"
SITE = pathlib.Path.home() / "workspace/cropradar/data-guide-site"
TEMPLATE = (SITE / "template.html").read_text()

# entry name (substring match) -> functionality tags (what the dataset is FOR)
FUNC = {
    "Moroccan parcels": ["Ground truth", "Irrigation & water"],
    "LWDCD2020": ["Disease classification"],
    "Wheat Leaf Dataset": ["Disease classification"],
    "nitrogen deficiency & leaf rust": ["Disease classification"],
    "yilikal wheat leaf disease": ["Disease classification"],
    "Wheat_Coccinellid": ["Pest modeling"],
    "MaBaKI": ["Phenotyping"],
    "Barley hyperspectral": ["Disease classification"],
    "Ethiopian barley disease": ["Disease classification"],
    "MMIDDWF": ["Weed detection"],
    "smallSSD": ["Weed detection"],
    "NarrabriWheat": ["Weed detection"],
    "PMDNet": ["Weed detection"],
    "RoboWeedMap": ["Weed detection"],
    "BAWSeg": ["Weed detection"],
    "Helsinki perennial weed": ["Weed detection"],
    "SoilGrids": ["Soil properties"],
    "FAOSTAT": ["Yield prediction"],
    "Crop-yield prediction dataset": ["Yield prediction"],
    "GWHD 2021": ["Yield prediction", "Phenotyping"],
    "CropHarvest": ["Crop mapping"],
    "Fertilizer recommendation": ["Fertilizer recommendation"],
    "Kaggle S5E6": ["Fertilizer recommendation"],
    "Crop water requirement": ["Irrigation & water"],
    "NASA POWER": ["Weather data"],
    "Open-Meteo": ["Weather data"],
    "CHIRPS": ["Weather data"],
    "WorldCereal": ["Crop mapping"],
    "BreizhCrops": ["Crop mapping"],
    "Kazakhstan UAV": ["Crop mapping", "Phenotyping"],
    "chlorophyll-fluorescence": ["Phenotyping"],
    "HyperLeaf": ["Phenotyping"],
    "Wheat aphid loads": ["Pest modeling"],
    "ICARDA RWA trials": ["Pest modeling"],
    "PLOS ONE winter-wheat": ["Irrigation & water"],
    "Seasonal agriculture dataset": ["Yield prediction", "Irrigation & water", "Fertilizer recommendation"],
    "ICARDA genebank": ["Varieties & breeding"],
    "Saïs wheat tillage": ["Yield prediction", "Fertilizer recommendation"],
    "Al Moutmir": ["Yield prediction"],
}
FUNCS_ORDER = ["Ground truth", "Yield prediction", "Disease classification", "Weed detection",
               "Soil properties", "Weather data", "Irrigation & water", "Fertilizer recommendation",
               "Crop mapping", "Phenotyping", "Pest modeling", "Varieties & breeding"]

# entry name (substring match) -> crop chips
CROPS = {
    "Moroccan parcels": ["14 crops", "Wheat (2,854 parcels)"],
    "LWDCD2020": ["Wheat"],
    "Wheat Leaf Dataset": ["Wheat"],
    "nitrogen deficiency & leaf rust": ["Wheat"],
    "yilikal wheat leaf disease": ["Wheat"],
    "Wheat_Coccinellid": ["Wheat"],
    "MaBaKI": ["Barley"],
    "Barley hyperspectral": ["Barley"],
    "Ethiopian barley disease": ["Barley"],
    "MMIDDWF": ["Wheat", "Weeds"],
    "smallSSD": ["Wheat", "Weeds"],
    "NarrabriWheat": ["Wheat", "Weeds"],
    "PMDNet": ["Wheat", "Weeds"],
    "RoboWeedMap": ["Barley", "Weeds"],
    "BAWSeg": ["Barley", "Weeds"],
    "Helsinki perennial weed": ["Barley", "Weeds"],
    "SoilGrids": ["All crops"],
    "FAOSTAT": ["Wheat", "Barley", "+170 crops"],
    "Crop-yield prediction dataset": ["Wheat"],
    "GWHD 2021": ["Wheat"],
    "CropHarvest": ["Multi-crop"],
    "Fertilizer recommendation": ["Wheat", "Barley"],
    "Kaggle S5E6": ["Wheat", "Barley"],
    "Crop water requirement": ["Multi-crop"],
    "NASA POWER": ["All crops"],
    "Open-Meteo": ["All crops"],
    "CHIRPS": ["All crops"],
    "WorldCereal": ["Wheat", "Barley (+ rye)"],
    "BreizhCrops": ["Wheat", "Barley"],
    "Kazakhstan UAV": ["Wheat", "Barley"],
    "chlorophyll-fluorescence": ["Wheat"],
    "HyperLeaf": ["Barley"],
    "Wheat aphid loads": ["Wheat"],
    "ICARDA RWA trials": ["Wheat", "Barley (host)"],
    "PLOS ONE winter-wheat": ["Wheat"],
    "Seasonal agriculture dataset": ["Wheat", "7 more crops"],
    "ICARDA genebank": ["Wheat", "Barley", "Chickpea", "Lentil"],
    "Saïs wheat tillage": ["Wheat"],
    "Al Moutmir": ["Cereals"],
}

def badges(body):
    low = body.lower()
    out = []
    if "fully open" in low or "open download" in low or "open:" in low:
        out.append(("Open", "b-open"))
    if ("login" in low or "account" in low) and "no account" not in low:
        out.append(("Login needed", "b-login"))
    if "paper-only" in low or "not public" in low or "request-only" in low:
        out.append(("Not public", "b-closed"))
    if "⚠️" in body or "unverified" in low or "verify" in low:
        out.append(("Verify license", "b-verify"))
    # dedupe preserving order
    seen, uniq = set(), []
    for b in out:
        if b[0] not in seen:
            seen.add(b[0]); uniq.append(b)
    return uniq

def crops_for(name):
    for key, chips in CROPS.items():
        if key.lower() in name.lower():
            return chips
    return []

def funcs_for(name):
    for key, tags in FUNC.items():
        if key.lower() in name.lower():
            return tags
    return []

def esc(s):
    return html.escape(s)

text = MD.read_text()
# drop title + intro lines before first section
m0 = re.search(r"^## \d+\. ", text, flags=re.M)
text = text[m0.start():] if m0 else text
raw_sections = re.split(r"^## (\d+)\. (.+)$", text, flags=re.M)
# raw_sections: [pre, num, title, body, num, title, body, ...]
sections_html = []
for i in range(1, len(raw_sections), 3):
    num, title, body = raw_sections[i], raw_sections[i+1].strip(), raw_sections[i+2]
    parked = "parked" in title.lower()
    clean_title = re.sub(r"\s*\(parked[^)]*\)\s*", "", title).strip()
    sec_id = "sec-" + re.sub(r"[^a-z0-9]+", "-", clean_title.lower()).strip("-")
    entries = re.findall(r"^\*\*(.+?)\*\* — (.+?)(?=^\*\*|\Z)", body, flags=re.M | re.S)
    if not entries:
        # single paragraph section: use section title as the entry name
        entries = [(clean_title, body.strip())]
    cards = []
    for name, para in entries:
        name = name.strip()
        para = " ".join(para.split())
        chips = crops_for(name)
        funcs = funcs_for(name)
        chip_html = "".join(f'<span class="chip">{esc(c)}</span>' for c in chips)
        func_html = "".join(f'<span class="funchip">{esc(f)}</span>' for f in funcs)
        badge_html = "".join(f'<span class="badge {cls}">{esc(label)}</span>' for label, cls in badges(para))
        search = esc((name + " " + para).lower())
        data_func = esc("|".join(funcs))
        cards.append(
            f'<article class="card" data-search="{search}" data-func="{data_func}">'
            f'<div class="catlabel">{esc(clean_title)}</div>'
            f"<h3>{esc(name)}</h3>"
            f'<div class="tags">{chip_html}{func_html}</div>'
            f"<p>{esc(para)}</p>"
            + (f'<div class="meta">{badge_html}</div>' if badge_html else "")
            + "</article>"
        )
    parked_note = (
        '<div class="parked"><b>Parked for now</b> — satellite crop-mapping is out of current scope. '
        "Kept here for reference; revisit later.</div>" if parked else ""
    )
    sections_html.append(
        f'<section class="cat" id="{sec_id}" data-nav="{esc(clean_title)}">'
        f"<h2 class=\"sec\">{esc(clean_title)}</h2>"
        f"{parked_note}"
        f'<div class="grid">{"".join(cards)}</div>'
        "</section>"
    )

out = TEMPLATE.replace("<!--SECTIONS-->", "\n".join(sections_html))
functs_js = "const FUNCS=" + "[" + ",".join('"' + f + '"' for f in FUNCS_ORDER) + "];"
out = out.replace("<!--FUNCS-->", "<script>" + functs_js + "</script>")
(SITE / "index.html").write_text(out)
print(f"wrote index.html with {len(sections_html)} sections, {sum(s.count('class=\"card\"') for s in sections_html)} cards")
