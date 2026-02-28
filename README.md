# Renovation Cost Estimator (Server Side)

This project estimates **material quantities and total material cost** for room renovations.

## What the code does (`main.py`)

`main.py` defines:

- `ROOM_MODULES`: Maps each room type to available work types and required material categories.
- `CATEGORY_QUANTITY_RULES`: Rules for computing quantity per material category (by floor area, wall area, perimeter, or fixed units).

### Functions

1. `calculate_quantities(length, width, height)`
- Computes room geometry:
  - `floor_area = length * width`
  - `wall_area = 2 * height * (length + width)`
  - `perimeter = 2 * (length + width)`

2. `resolve_quantity(category, quantities)`
- Uses `CATEGORY_QUANTITY_RULES` to compute quantity for one category.
- Supports:
  - `floor_area` (optionally with waste and multiplier)
  - `wall_area` (optionally with waste and coverage)
  - `perimeter` (with multiplier)
  - `unit` (fixed quantity)

3. `normalize_tiered_materials(df)`
- Normalizes CSV column names and key values to lowercase/trimmed text.
- Makes matching robust for `category` and `qualita`.

4. `calculate_renovation_cost(room, work_type, quality, length, width, height, tiered_materials)`
- Main estimation function.
- Workflow:
  1. Normalize inputs and material data.
  2. Compute room quantities.
  3. Get required categories from `ROOM_MODULES[room][work_type]`.
  4. For each category, find the matching material row by (`category`, `qualita`).
  5. Compute `cost = quantity * unit_price`.
  6. Return:
     - `results`: list of material breakdown items
     - `total_cost`: total estimated material cost

## Input

### Function input (`calculate_renovation_cost`)

- `room` (`str`): One of `bagno`, `cucina`, `soggiorno`, `camera`
- `work_type` (`str`): Must be valid for that room in `ROOM_MODULES`
- `quality` (`str`): Quality tier (example: `base`, `superiore`)
- `length`, `width`, `height` (`float`): Room dimensions in meters
- `tiered_materials` (`pandas.DataFrame`): Must include at least these columns:
  - `category`
  - `qualita`
  - `prezzo`
  - `u.m.`

### CSV input file

A suitable file exists at:

- `Data/tiered_materials.csv`

Important: in current code, `__main__` uses:

```python
tiered_materials = pd.read_csv("tiered_materials.csv")
```

So either:
- run from a folder where `tiered_materials.csv` is present, or
- update that line to `pd.read_csv("Data/tiered_materials.csv")`.

## Output

`calculate_renovation_cost(...)` returns:

1. `results` (`list[dict]`), each item like:

```python
{
  "category": "pavimento",
  "quantity": 6.6,
  "unit": "mq",
  "unit_price": 22.5,
  "cost": 148.5
}
```

2. `total_cost` (`float`), e.g. `1250.78`

When running `main.py` directly, console output is:

- `materials breakdown:` then one dictionary per category
- `total material cost: <value> eur`

## How to run

From `Server Side` directory:

```powershell
# optional: activate local virtual environment
.\.venv\Scripts\Activate.ps1

# install dependencies if needed
pip install pandas

# run
python main.py
```

## Example default run values (in `__main__`)

- `room = "bagno"`
- `work_type = "ristrutturazione_completa"`
- `quality = "superiore"`
- `length = 3.0`, `width = 2.0`, `height = 2.7`
