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
    recipe_ingredients: Dict[str, float]
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

    for ingredient_name, quantity_used in recipe_ingredients.items():
        # Find ALL matching inventory items; consume oldest first
        matches = _match_all_inventory(ingredient_name)
        if not matches:
            results[ingredient_name] = "not found in inventory"
            continue

        remaining = float(quantity_used or 0)
        updates: List[str] = []
        for it in matches:
            if remaining <= 0:
                break
            take = min(it.quantity, remaining)
            new_qty = it.quantity - take
            if new_qty <= 0:
                delete_inventory_item(user_id, it.id)
                updates.append(f"deleted {it.item_name} ({take:g} used)")
            else:
                update_data = InventoryItemUpdate(quantity=new_qty)
                update_inventory_item(user_id, it.id, update_data)
                updates.append(f"updated {it.item_name} (new qty: {new_qty:g})")
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
