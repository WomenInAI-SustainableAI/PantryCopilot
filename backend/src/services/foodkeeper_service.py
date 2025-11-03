"""
FoodKeeper Service

Loads and queries the FSIS USDA FoodKeeper dataset (foodkeeper.json) to estimate
shelf life (in days) for items based on storage location.

Primary entrypoints:
- estimate_shelf_life_days(item_name: str, storage: Optional[str] = None) -> int
- choose_storage(item_name: str) -> str

Notes about the dataset structure:
- The JSON file is a set of sheets; we rely on the sheet with name == "Product".
- Each row in Product.data is a list of single-key dicts that we flatten into one row dict.
- Relevant fields include Name, Name_subtitle, Keywords and timing columns like
  DOP_Pantry_Min/Max/Metric, DOP_Refrigerate_*, DOP_Freeze_*, Pantry_*, Refrigerate_*, Freeze_*.

If no match or no usable timing is found, we fall back to a conservative default.
"""
from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any, Dict, List, Optional, Tuple

# Default fallback in days when no information is found
DEFAULT_SHELF_LIFE_DAYS = 7

# Multipliers for unit conversion to days
_UNIT_TO_DAYS = {
    "day": 1,
    "days": 1,
    "week": 7,
    "weeks": 7,
    "month": 30,
    "months": 30,
    "year": 365,
    "years": 365,
}

# Column name templates we will probe for a given storage key
# Precedence order: DOP_* (date of purchase) over generic, and Max over Min if present
_STORAGE_COLUMNS = {
    "pantry": [
        ("DOP_Pantry_Max", "DOP_Pantry_Metric"),
        ("DOP_Pantry_Min", "DOP_Pantry_Metric"),
        ("Pantry_Max", "Pantry_Metric"),
        ("Pantry_Min", "Pantry_Metric"),
    ],
    "refrigerate": [
        ("DOP_Refrigerate_Max", "DOP_Refrigerate_Metric"),
        ("DOP_Refrigerate_Min", "DOP_Refrigerate_Metric"),
        ("Refrigerate_Max", "Refrigerate_Metric"),
        ("Refrigerate_Min", "Refrigerate_Metric"),
        # As a last resort, sometimes after opening fields exist
        ("Refrigerate_After_Opening_Max", "Refrigerate_After_Opening_Metric"),
        ("Refrigerate_After_Opening_Min", "Refrigerate_After_Opening_Metric"),
    ],
    "freeze": [
        ("DOP_Freeze_Max", "DOP_Freeze_Metric"),
        ("DOP_Freeze_Min", "DOP_Freeze_Metric"),
        ("Freeze_Max", "Freeze_Metric"),
        ("Freeze_Min", "Freeze_Metric"),
    ],
}


def _this_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def _foodkeeper_path() -> str:
    # backend/src/services -> backend
    backend_dir = os.path.abspath(os.path.join(_this_dir(), "..", ".."))
    return os.path.join(backend_dir, "foodkeeper.json")


@lru_cache(maxsize=1)
def _load_foodkeeper() -> Dict[str, Any]:
    path = _foodkeeper_path()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_product_rows() -> List[Dict[str, Any]]:
    data = _load_foodkeeper()
    sheets = data if isinstance(data, list) else data.get("sheets") or data
    # The dataset we have appears to be a list of sheet dicts; each with name and data
    # Sometimes top-level may already be a dict keyed by sheet names. Try both.
    rows: List[Dict[str, Any]] = []

    if isinstance(sheets, list):
        # Find the sheet with name == "Product"
        for sheet in sheets:
            if isinstance(sheet, dict) and sheet.get("name") == "Product":
                raw_rows = sheet.get("data") or []
                for row in raw_rows:
                    # row is a list of single-key dicts; flatten them
                    row_dict: Dict[str, Any] = {}
                    for cell in row:
                        if isinstance(cell, dict):
                            row_dict.update(cell)
                    rows.append(row_dict)
                break
    elif isinstance(sheets, dict) and "Product" in sheets:
        raw_rows = sheets["Product"].get("data") or []
        for row in raw_rows:
            row_dict: Dict[str, Any] = {}
            for cell in row:
                if isinstance(cell, dict):
                    row_dict.update(cell)
            rows.append(row_dict)

    return rows


@lru_cache(maxsize=1)
def _build_index() -> List[Dict[str, Any]]:
    """Build a simplified product index for fast matching."""
    index: List[Dict[str, Any]] = []
    for row in _get_product_rows():
        name = str(row.get("Name") or "").strip()
        subtitle = str(row.get("Name_subtitle") or "").strip()
        keywords = str(row.get("Keywords") or "").strip()
        norm_name = _norm_text(f"{name} {subtitle}".strip())
        keyword_list = [k.strip().lower() for k in keywords.split(",") if k and k.strip()]
        index.append({
            "name": name,
            "subtitle": subtitle,
            "norm_name": norm_name,
            "keywords": keyword_list,
            "row": row,
        })
    return index


def _norm_text(s: str) -> str:
    s = s.lower()
    # remove punctuation and collapse whitespace
    s = re.sub(r"[\"'`,.:;()\[\]{}]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _tokenize(s: str) -> List[str]:
    return [t for t in _norm_text(s).split(" ") if t]


def _match_product(item_name: str) -> Optional[Dict[str, Any]]:
    """Find best matching product entry for the given item name."""
    name_norm = _norm_text(item_name)
    name_tokens = set(_tokenize(item_name))

    best: Optional[Tuple[float, Dict[str, Any]]] = None

    for entry in _build_index():
        score = 0.0
        ename = entry["norm_name"]

        # Exact or substring matches get high score
        if name_norm == ename:
            score = 1.0
        elif name_norm in ename or ename in name_norm:
            score = 0.9
        else:
            # Token overlap with name
            etokens = set(_tokenize(ename))
            inter = name_tokens & etokens
            if inter:
                # Jaccard-like score
                union = name_tokens | etokens
                score = max(score, len(inter) / max(1, len(union)))

            # Keywords equality/overlap
            kscore = 0.0
            for kw in entry.get("keywords", []):
                nkw = _norm_text(kw)
                if not nkw:
                    continue
                if name_norm == nkw:
                    kscore = max(kscore, 0.8)
                elif nkw in name_norm or name_norm in nkw:
                    kscore = max(kscore, 0.7)
                else:
                    kw_tokens = set(_tokenize(nkw))
                    inter2 = name_tokens & kw_tokens
                    if inter2:
                        union2 = name_tokens | kw_tokens
                        kscore = max(kscore, len(inter2) / max(1, len(union2)))
            score = max(score, kscore)

        # Penalize prepared/cooked variants unless explicitly requested
        cooked_like_terms = ["cooked", "prepared", "ready to eat", "ready-to-eat", "leftover", "opened"]
        if any(t in ename for t in cooked_like_terms) and not any(t in name_norm for t in cooked_like_terms):
            score *= 0.6

        if best is None or score > best[0]:
            best = (score, entry)

    # Require minimal confidence
    if best and best[0] >= 0.25:
        return best[1]
    return None


def _convert_to_days(value: Optional[float], metric: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    unit = (metric or "").strip().lower()
    if not unit:
        return None
    # handle special sentinel strings like "when ripe"
    if unit.startswith("when ripe"):
        # heuristically: once ripe, assume ~7 days
        return 7
    mult = _UNIT_TO_DAYS.get(unit)
    if mult is None:
        # try to normalize plurals/singulars
        if unit.endswith("s") and unit[:-1] in _UNIT_TO_DAYS:
            mult = _UNIT_TO_DAYS[unit[:-1]]
    if mult is None:
        return None
    return max(1, int(round(value * mult)))


def _extract_days_for_storage(row: Dict[str, Any], storage: str) -> Optional[int]:
    for val_col, unit_col in _STORAGE_COLUMNS.get(storage, []):
        val = row.get(val_col)
        unit = row.get(unit_col)
        days = _convert_to_days(val, unit)
        if days:
            return days
    return None


def choose_storage(item_name: str) -> str:
    """Heuristically choose storage when not provided: pantry|refrigerate|freeze"""
    s = _norm_text(item_name)
    # Freezer candidates
    if any(w in s for w in ["frozen", "ice cream", "freezer", "icecream"]):
        return "freeze"
    # Obvious pantry staples
    pantry_hits = [
        "rice", "flour", "sugar", "salt", "oil", "vinegar", "spice", "spices",
        "cereal", "pasta", "noodle", "noodles", "beans", "lentils", "canned", "can ", "jar",
        "sauce", "ketchup", "mustard", "mayonnaise", "mayo", "soy sauce", "worcestershire",
    ]
    if any(w in s for w in pantry_hits):
        return "pantry"
    # Meats & dairy -> fridge
    if any(w in s for w in [
        "chicken", "beef", "pork", "lamb", "fish", "seafood", "turkey", "ham",
        "milk", "cheese", "yogurt", "cream", "butter", "egg", "eggs",
    ]):
        return "refrigerate"
    # Most fresh produce is refrigerated (except some like tomatoes pre-ripening; we keep it simple)
    if any(w in s for w in [
        "lettuce", "spinach", "greens", "herb", "basil", "cilantro", "parsley",
        "broccoli", "berries", "strawberry", "blueberry", "raspberry", "grape",
        "cherry", "mushroom", "asparagus", "kale", "arugula", "zucchini",
    ]):
        return "refrigerate"
    # Default to refrigerate for safety
    return "refrigerate"


def estimate_shelf_life_days(item_name: str, storage: Optional[str] = None) -> int:
    """Estimate shelf life in days for the given item using FoodKeeper data.

    If storage is not provided, a heuristic chooser is used. If no product match or
    timing is found, returns DEFAULT_SHELF_LIFE_DAYS.
    """
    storage_given = storage is not None
    storage_key = (storage or choose_storage(item_name)).strip().lower()
    if storage_key not in ("pantry", "refrigerate", "freeze"):
        storage_key = "refrigerate"

    entry = _match_product(item_name)
    if not entry:
        return DEFAULT_SHELF_LIFE_DAYS

    days = _extract_days_for_storage(entry["row"], storage_key)
    if days is not None:
        return int(days)

    # Fallback: only try alternative storages if storage wasn't explicitly provided
    if not storage_given:
        for alt in ("refrigerate", "pantry", "freeze"):
            if alt == storage_key:
                continue
            days = _extract_days_for_storage(entry["row"], alt)
            if days is not None:
                return int(days)

    return DEFAULT_SHELF_LIFE_DAYS
