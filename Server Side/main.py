import pandas as pd

ROOM_MODULES = {
    "bagno": {
        "ristrutturazione_completa": [
            "pavimento",
            "rivestimento",
            "impermeabilizzazione",
            "collante",
            "stucco_fughe",
            "wc",
            "lavabo",
            "doccia",
            "tubo_pex",
            "tubo_pvc",
            "cavo_elettrico",
            "interruttore",
            "ventilazione",
            "pittura",
        ],
        "sostituzione_piastrelle": [
            "pavimento",
            "rivestimento",
            "collante",
            "stucco_fughe",
            "impermeabilizzazione",
        ],
        "sostituzione_sanitari": ["wc", "lavabo", "doccia"],
    },
    "cucina": {
        "ristrutturazione_completa": [
            "pavimento",
            "rivestimento",
            "collante",
            "stucco_fughe",
            "tubo_pex",
            "tubo_pvc",
            "cavo_elettrico",
            "presa",
            "interruttore",
            "pittura",
        ],
        "sostituzione_pavimento": ["pavimento", "collante", "stucco_fughe"],
        "aggiornamento_impianto_idraulico": ["tubo_pex", "tubo_pvc"],
    },
    "soggiorno": {
        "ristrutturazione_completa": [
            "pavimento",
            "parquet",
            "laminato",
            "pittura",
            "cavo_elettrico",
            "presa",
            "interruttore",
        ],
        "sostituzione_pavimento": ["pavimento", "parquet", "laminato"],
        "tinteggiatura": ["pittura"],
    },
    "camera": {
        "ristrutturazione_completa": [
            "parquet",
            "laminato",
            "pittura",
            "cavo_elettrico",
            "presa",
            "interruttore",
        ],
        "sostituzione_pavimento": ["parquet", "laminato"],
        "tinteggiatura": ["pittura"],
    },
}

CATEGORY_QUANTITY_RULES = {
    "pavimento": {"type": "floor_area", "waste": 0.10},
    "rivestimento": {"type": "wall_area", "waste": 0.10},
    "impermeabilizzazione": {"type": "floor_area", "waste": 0.15},
    "collante": {"type": "floor_area", "multiplier": 0.2},
    "stucco_fughe": {"type": "floor_area", "multiplier": 0.05},
    "pittura": {"type": "wall_area", "coverage": 10},
    "tubo_pex": {"type": "perimeter", "multiplier": 1.0},
    "tubo_pvc": {"type": "perimeter", "multiplier": 1.0},
    "wc": {"type": "unit", "quantity": 1},
    "lavabo": {"type": "unit", "quantity": 1},
    "doccia": {"type": "unit", "quantity": 1},
    "ventilazione": {"type": "unit", "quantity": 1},
    "radiatore": {"type": "unit", "quantity": 1},
    "caldaia": {"type": "unit", "quantity": 1},
    "presa": {"type": "unit", "quantity": 6},
    "interruttore": {"type": "unit", "quantity": 3},
    "cavo_elettrico": {"type": "perimeter", "multiplier": 1.5},
}


def calculate_quantities(length, width, height):
    floor_area = length * width
    wall_area = 2 * height * (length + width)
    perimeter = 2 * (length + width)

    return {
        "floor_area": floor_area,
        "wall_area": wall_area,
        "perimeter": perimeter,
    }


def resolve_quantity(category, quantities):
    rule = CATEGORY_QUANTITY_RULES.get(category)

    if not rule:
        return 1

    rule_type = rule["type"]

    if rule_type == "floor_area":
        qty = quantities["floor_area"]
        qty *= 1 + rule.get("waste", 0)
        qty *= rule.get("multiplier", 1)
    elif rule_type == "wall_area":
        qty = quantities["wall_area"]
        qty *= 1 + rule.get("waste", 0)
        if "coverage" in rule:
            qty = qty / rule["coverage"]
    elif rule_type == "perimeter":
        qty = quantities["perimeter"] * rule.get("multiplier", 1)
    elif rule_type == "unit":
        qty = rule.get("quantity", 1)
    else:
        qty = 1

    return qty


def normalize_tiered_materials(df):
    normalized = df.copy()
    normalized.columns = [str(c).strip().lower() for c in normalized.columns]

    for col in ["category", "qualita"]:
        if col in normalized.columns:
            normalized[col] = normalized[col].astype(str).str.strip().str.lower()

    return normalized


def calculate_renovation_cost(room, work_type, quality, length, width, height, tiered_materials):
    room = room.strip().lower()
    work_type = work_type.strip().lower()
    quality = quality.strip().lower()

    tiered_materials = normalize_tiered_materials(tiered_materials)
    quantities = calculate_quantities(length, width, height)
    required_categories = ROOM_MODULES[room][work_type]

    results = []
    total_cost = 0

    for category in required_categories:
        material = tiered_materials[
            (tiered_materials["category"] == category)
            & (tiered_materials["qualita"] == quality)
        ]

        if material.empty:
            continue

        material = material.iloc[0]
        unit_price = material["prezzo"]
        unit = material["u.m."]

        qty = resolve_quantity(category, quantities)

        cost = qty * unit_price
        total_cost += cost

        results.append(
            {
                "category": category,
                "quantity": round(qty, 2),
                "unit": unit,
                "unit_price": float(round(unit_price, 2)),
                "cost": float(round(cost, 2)),
            }
        )

    return results, round(total_cost, 2)


if __name__ == "__main__":
    room = "bagno"
    work_type = "ristrutturazione_completa"
    quality = "superiore"
    length = 3.0
    width = 2.0
    height = 2.7

    tiered_materials = pd.read_csv("tiered_materials.csv")
    materials_used, total = calculate_renovation_cost(
        room,
        work_type,
        quality,
        length,
        width,
        height,
        tiered_materials,
    )

    print("materials breakdown:")
    for material in materials_used:
        print(material)

    print("\ntotal material cost:", total, "eur")
