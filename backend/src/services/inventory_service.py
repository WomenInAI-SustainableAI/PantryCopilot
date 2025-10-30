"""
Inventory Service - Business logic for inventory management
Auto-calculates expiry dates based on quantity
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List, Tuple
from .foodkeeper_service import estimate_shelf_life_days, choose_storage
from src.db.crud import (
    create_inventory_item,
    get_user_inventory,
    update_inventory_item,
    delete_inventory_item,
    get_expiring_items
)
from src.db.models import InventoryItemCreate, InventoryItem, InventoryItemUpdate


# Deprecated defaults: replaced by FoodKeeper-backed estimation
SHELF_LIFE_DEFAULTS: Dict[str, int] = {"default": 7}


def calculate_expiry_date(item_name: str, quantity: float) -> datetime:
    """
    Calculate expiry date based on item name and quantity.
    Returns datetime object (not date) for Firestore compatibility.
    
    Args:
        item_name: Name of the inventory item
        quantity: Quantity of the item
        
    Returns:
        Calculated expiry date as datetime
    """
    # Base shelf life from FoodKeeper dataset (storage inferred)
    try:
        storage = choose_storage(item_name)
        base_days = int(estimate_shelf_life_days(item_name, storage))
    except Exception:
        base_days = SHELF_LIFE_DEFAULTS.get("default", 7)
    
    # Optional adjustment based on large quantity for highly perishable items
    if base_days <= 14 and quantity > 5:
        base_days = max(1, int(base_days * 0.85))
    
    # Calculate expiry date as datetime (not date) for Firestore compatibility
    # Use UTC for server-side timestamps
    expiry = datetime.now(timezone.utc) + timedelta(days=base_days)
    
    return expiry


def add_inventory_item(
    user_id: str,
    item_name: str,
    quantity: float,
    unit: Optional[str] = "piece"
) -> InventoryItem:
    """
    Add an inventory item with auto-calculated expiry date.
    
    Args:
        user_id: User ID
        item_name: Name of the item
        quantity: Quantity of the item
        unit: Unit of measurement
        
    Returns:
        Created inventory item
    """
    # Auto-calculate expiry date
    expiry_date = calculate_expiry_date(item_name, quantity)
    
    # Create inventory item
    item_data = InventoryItemCreate(
        item_name=item_name,
        quantity=quantity,
        unit=unit,
        expiry_date=expiry_date
    )
    
    return create_inventory_item(user_id, item_data)


def subtract_inventory_items(
    user_id: str,
    recipe_ingredients: Dict[str, float],
    ingredient_units: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """
    Subtract recipe ingredients from user inventory after cooking.
    
    Args:
        user_id: User ID
        recipe_ingredients: Dictionary of ingredient names to quantities used
        
    Returns:
        Dictionary with status of each ingredient update
    """
    results = {}
    inventory = get_user_inventory(user_id)

    def _norm(s: str) -> str:
        return (s or "").strip().lower()

    def _tokenize(s: str) -> List[str]:
        import re
        s = re.sub(r"[\"'`,.:;()\[\]{}]", " ", s)
        s = re.sub(r"\s+", " ", s)
        return [t for t in s.strip().lower().split(" ") if t]

    def _match_inventory(ing_name: str) -> Optional[InventoryItem]:
        ing_norm = _norm(ing_name)
        ing_tokens = _tokenize(ing_name)
        # 1) Exact normalized match
        for it in inventory:
            if _norm(it.item_name) == ing_norm:
                return it
        # 2) Multi-word subset match (avoid matching single words like 'butter' to 'peanut butter')
        if len(ing_tokens) >= 2:
            ing_set = set(ing_tokens)
            for it in inventory:
                inv_tokens = set(_tokenize(it.item_name))
                if ing_set.issubset(inv_tokens):
                    return it
        # 3) No match
        return None

    def _match_all_inventory(ing_name: str) -> List[InventoryItem]:
        """Return all matching inventory items for an ingredient name.

        Matching rules mirror _match_inventory but return a list, sorted by earliest expiry first.
        """
        ing_norm = _norm(ing_name)
        ing_tokens = _tokenize(ing_name)
        matches: List[InventoryItem] = []
        # Allow-list of generic tokens we permit to match more specific ingredients when needed
        GENERIC_FALLBACKS = set([
            # core proteins
            "chicken", "beef", "pork", "lamb", "turkey", "fish", "seafood", "shrimp",
            # common pantry staples (keep conservative)
            "rice", "pasta", "noodles", "tomato", "potato", "onion",
            # dairy basics
            "milk", "cheese", "butter", "yogurt", "egg", "eggs",
            # baking basics
            "flour", "sugar", "oil",
        ])
        # Exact matches first
        for it in inventory:
            if _norm(it.item_name) == ing_norm:
                matches.append(it)
        # Multi-word subset matches next (avoid single-token false positives)
        if len(ing_tokens) >= 2:
            ing_set = set(ing_tokens)
            for it in inventory:
                if _norm(it.item_name) == ing_norm:
                    continue  # already added
                inv_tokens = set(_tokenize(it.item_name))
                if ing_set.issubset(inv_tokens):
                    matches.append(it)
        # Generic fallback: if no matches yet and ingredient is more specific (2+ tokens),
        # allow single-token inventory items that are generic and appear in the ingredient tokens.
        if not matches and len(ing_tokens) >= 2:
            ing_set = set(ing_tokens)
            for it in inventory:
                inv_tokens = set(_tokenize(it.item_name))
                if len(inv_tokens) == 1:
                    token = next(iter(inv_tokens)) if inv_tokens else ""
                    if token and token in GENERIC_FALLBACKS and token in ing_set:
                        matches.append(it)
        # Sort by expiry (earliest first), then by quantity ascending as tiebreaker
        def _expiry_key(it: InventoryItem):
            dt = it.expiry_date
            from datetime import datetime, timezone, date
            if isinstance(dt, date) and not isinstance(dt, datetime):
                dt = datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc)
            if getattr(dt, 'tzinfo', None) is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        matches.sort(key=lambda it: (_expiry_key(it), it.quantity))
        return matches

    # --- Unit handling helpers ---
    def _norm_unit(u: Optional[str]) -> str:
        u = (u or "").strip().lower()
        # common aliases
        aliases = {
            "gram": "g", "grams": "g", "g": "g",
            "kilogram": "kg", "kilograms": "kg", "kg": "kg",
            "milligram": "mg", "milligrams": "mg", "mg": "mg",
            "pound": "lb", "pounds": "lb", "lbs": "lb", "lb": "lb",
            "ounce": "oz", "ounces": "oz", "oz": "oz",
            "milliliter": "ml", "millilitre": "ml", "milliliters": "ml", "millilitres": "ml", "ml": "ml",
            "liter": "l", "litre": "l", "liters": "l", "litres": "l", "l": "l",
            "piece": "piece", "pieces": "piece", "pc": "piece", "pcs": "piece", "count": "piece", "unit": "piece", "item": "piece", "items": "piece",
        }
        return aliases.get(u, u)

    def _unit_family(u: str) -> str:
        if u in ("mg", "g", "kg", "oz", "lb"):
            return "weight"
        if u in ("ml", "l"):
            return "volume"
        if u in ("piece", ""):
            return "count"
        return "other"

    def _to_base(amount: float, unit: str) -> Tuple[float, str]:
        """Convert amount to base unit per family. Returns (amount_in_base, base_unit)."""
        fam = _unit_family(unit)
        if fam == "weight":
            # base: grams
            factors = {"mg": 0.001, "g": 1.0, "kg": 1000.0, "oz": 28.349523125, "lb": 453.59237}
            return amount * factors.get(unit, 1.0), "g"
        if fam == "volume":
            # base: milliliters
            factors = {"ml": 1.0, "l": 1000.0}
            return amount * factors.get(unit, 1.0), "ml"
        # count/other: base is piece or passthrough
        return amount, "piece" if fam == "count" else unit

    def _convert(amount: float, from_unit: str, to_unit: str) -> float:
        """Convert amount between compatible units; if incompatible, return original amount."""
        f = _unit_family(from_unit)
        t = _unit_family(to_unit)
        if f != t:
            return amount  # incompatible or unknown family; no conversion
        # Convert to base then to target
        base_amt, base_u = _to_base(amount, from_unit)
        if f == "weight":
            # base grams -> target
            back = {"mg": 1000.0, "g": 1.0, "kg": 0.001, "oz": 1/28.349523125, "lb": 1/453.59237}
            return base_amt * back.get(to_unit, 1.0)
        if f == "volume":
            # base ml -> target
            back = {"ml": 1.0, "l": 0.001}
            return base_amt * back.get(to_unit, 1.0)
        # count or other
        return amount

    for ingredient_name, quantity_used in recipe_ingredients.items():
        # Find ALL matching inventory items; consume oldest first
        matches = _match_all_inventory(ingredient_name)
        if not matches:
            results[ingredient_name] = "not found in inventory"
            continue

        # Determine the unit used for this ingredient usage (if provided)
        ing_unit = _norm_unit((ingredient_units or {}).get(ingredient_name))
        remaining = float(quantity_used or 0)
        updates: List[str] = []
        for it in matches:
            if remaining <= 0:
                break
            inv_unit = _norm_unit(getattr(it, "unit", None))
            if ing_unit and inv_unit:
                # Compare in ingredient unit
                inv_qty_in_ing_unit = _convert(it.quantity, inv_unit, ing_unit)
                take_in_ing_unit = min(inv_qty_in_ing_unit, remaining)
                # Convert the taken amount back to inventory unit for storage update
                take = _convert(take_in_ing_unit, ing_unit, inv_unit)
            else:
                # No unit info; fall back to raw numbers
                take = min(it.quantity, remaining)
                ing_unit = ing_unit or inv_unit  # carry forward if only inv unit known

            new_qty = it.quantity - take
            if new_qty <= 0:
                delete_inventory_item(user_id, it.id)
                updates.append(f"deleted {it.item_name} ({take:g} used)")
            else:
                update_data = InventoryItemUpdate(quantity=new_qty)
                update_inventory_item(user_id, it.id, update_data)
                updates.append(f"updated {it.item_name} (new qty: {new_qty:g})")
            # Decrease remaining in ingredient unit if available
            if ing_unit and inv_unit:
                remaining_in_ing_unit = _convert(take, inv_unit, ing_unit)
                remaining -= remaining_in_ing_unit
            else:
                remaining -= take

        if remaining > 0:
            updates.append(f"missing {remaining:g}")
        results[ingredient_name] = "; ".join(updates)
    
    return results


def get_expiring_soon(user_id: str, days: int = 3) -> List[InventoryItem]:
    """
    Get inventory items expiring within specified days.
    
    Args:
        user_id: User ID
        days: Number of days to look ahead
        
    Returns:
        List of expiring inventory items
    """
    # Always compute in UTC
    expiry_date = datetime.now(timezone.utc) + timedelta(days=days)
    return get_expiring_items(user_id, expiry_date)
