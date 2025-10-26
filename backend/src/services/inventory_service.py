"""
Inventory Service - Business logic for inventory management
Auto-calculates expiry dates based on quantity
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, List
from src.db.crud import (
    create_inventory_item,
    get_user_inventory,
    update_inventory_item,
    delete_inventory_item,
    get_expiring_items
)
from src.db.models import InventoryItemCreate, InventoryItem, InventoryItemUpdate


# Default shelf life for common items (in days)
SHELF_LIFE_DEFAULTS: Dict[str, int] = {
    # Dairy
    "milk": 7,
    "cheese": 14,
    "yogurt": 10,
    "butter": 30,
    "cream": 7,
    
    # Produce
    "lettuce": 5,
    "tomatoes": 7,
    "tomato": 7,
    "carrots": 14,
    "carrot": 14,
    "potatoes": 30,
    "potato": 30,
    "onions": 30,
    "onion": 30,
    "garlic": 30,
    "bananas": 5,
    "banana": 5,
    "apples": 14,
    "apple": 14,
    "berries": 3,
    "strawberries": 3,
    "blueberries": 5,
    "spinach": 5,
    "broccoli": 7,
    "bell pepper": 10,
    "peppers": 10,
    
    # Proteins
    "chicken": 2,
    "beef": 3,
    "pork": 3,
    "fish": 1,
    "salmon": 2,
    "eggs": 21,
    "egg": 21,
    
    # Herbs
    "basil": 5,
    "cilantro": 7,
    "parsley": 7,
    "mint": 7,
    
    # Pantry (longer shelf life)
    "flour": 180,
    "sugar": 730,
    "rice": 365,
    "pasta": 730,
    "beans": 365,
    "lentils": 365,
    "canned": 730,
    
    # Default for unknown items
    "default": 7
}


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
    # Normalize item name
    item_lower = item_name.lower().strip()
    
    # Find matching shelf life
    base_days = SHELF_LIFE_DEFAULTS.get("default", 7)
    
    for key, days in SHELF_LIFE_DEFAULTS.items():
        if key in item_lower or item_lower in key:
            base_days = days
            break
    
    # Adjust based on quantity (larger quantities might expire sooner)
    # For perishables, if quantity > 5, reduce shelf life slightly
    if base_days <= 14 and quantity > 5:
        base_days = int(base_days * 0.8)
    
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
    
    for ingredient_name, quantity_used in recipe_ingredients.items():
        # Find matching inventory item
        matching_item = None
        for item in inventory:
            if ingredient_name.lower() in item.item_name.lower() or \
               item.item_name.lower() in ingredient_name.lower():
                matching_item = item
                break
        
        if matching_item:
            new_quantity = matching_item.quantity - quantity_used
            
            if new_quantity <= 0:
                # Delete item if quantity is 0 or less
                delete_inventory_item(user_id, matching_item.id)
                results[ingredient_name] = "deleted (quantity depleted)"
            else:
                # Update quantity
                update_data = InventoryItemUpdate(quantity=new_quantity)
                update_inventory_item(user_id, matching_item.id, update_data)
                results[ingredient_name] = f"updated (new quantity: {new_quantity})"
        else:
            results[ingredient_name] = "not found in inventory"
    
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
