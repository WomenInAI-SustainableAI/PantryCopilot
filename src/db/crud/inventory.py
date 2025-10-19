"""
CRUD operations for Inventory subcollection
"""
from typing import List, Optional
from datetime import datetime, date
import uuid
from google.cloud.firestore_v1 import FieldFilter

from src.db.firestore import db
from src.db.models import InventoryItem, InventoryItemCreate, InventoryItemUpdate


class InventoryCRUD:
    """CRUD operations for user inventory subcollection."""
    
    USERS_COLLECTION = "users"
    INVENTORY_SUBCOLLECTION = "inventory"
    
    @staticmethod
    def create(user_id: str, item_data: InventoryItemCreate) -> InventoryItem:
        """
        Create a new inventory item for a user.
        
        Args:
            user_id: User ID
            item_data: Inventory item creation data
            
        Returns:
            Created inventory item
        """
        item_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        item_dict = {
            "id": item_id,
            "user_id": user_id,
            "item_name": item_data.item_name,
            "quantity": item_data.quantity,
            "unit": item_data.unit or "piece",
            "expiry_date": item_data.expiry_date,
            "added_at": now,
            "updated_at": now
        }
        
        db.collection(InventoryCRUD.USERS_COLLECTION).document(user_id).collection(
            InventoryCRUD.INVENTORY_SUBCOLLECTION
        ).document(item_id).set(item_dict)
        
        return InventoryItem(**item_dict)
    
    @staticmethod
    def get(user_id: str, item_id: str) -> Optional[InventoryItem]:
        """
        Get a specific inventory item.
        
        Args:
            user_id: User ID
            item_id: Inventory item ID
            
        Returns:
            Inventory item if found, None otherwise
        """
        doc = (
            db.collection(InventoryCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(InventoryCRUD.INVENTORY_SUBCOLLECTION)
            .document(item_id)
            .get()
        )
        
        if doc.exists:
            return InventoryItem(**doc.to_dict())
        return None
    
    @staticmethod
    def list_by_user(user_id: str, limit: int = 100) -> List[InventoryItem]:
        """
        List all inventory items for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of items to return
            
        Returns:
            List of inventory items
        """
        docs = (
            db.collection(InventoryCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(InventoryCRUD.INVENTORY_SUBCOLLECTION)
            .order_by("expiry_date")
            .limit(limit)
            .get()
        )
        
        return [InventoryItem(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def get_expiring_items(user_id: str, expiry_date: date) -> List[InventoryItem]:
        """
        Get inventory items expiring on or before a specific date.
        
        Args:
            user_id: User ID
            expiry_date: Date to check expiry against
            
        Returns:
            List of expiring inventory items
        """
        docs = (
            db.collection(InventoryCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(InventoryCRUD.INVENTORY_SUBCOLLECTION)
            .where(filter=FieldFilter("expiry_date", "<=", expiry_date))
            .order_by("expiry_date")
            .get()
        )
        
        return [InventoryItem(**doc.to_dict()) for doc in docs]
    
    @staticmethod
    def update(user_id: str, item_id: str, update_data: InventoryItemUpdate) -> Optional[InventoryItem]:
        """
        Update an inventory item.
        
        Args:
            user_id: User ID
            item_id: Inventory item ID
            update_data: Fields to update
            
        Returns:
            Updated inventory item if found, None otherwise
        """
        doc_ref = (
            db.collection(InventoryCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(InventoryCRUD.INVENTORY_SUBCOLLECTION)
            .document(item_id)
        )
        
        doc = doc_ref.get()
        if not doc.exists:
            return None
        
        # Build update dictionary excluding None values
        update_dict = {
            k: v for k, v in update_data.model_dump().items() 
            if v is not None
        }
        update_dict["updated_at"] = datetime.utcnow()
        
        doc_ref.update(update_dict)
        
        updated_doc = doc_ref.get()
        return InventoryItem(**updated_doc.to_dict())
    
    @staticmethod
    def delete(user_id: str, item_id: str) -> bool:
        """
        Delete an inventory item.
        
        Args:
            user_id: User ID
            item_id: Inventory item ID
            
        Returns:
            True if deleted, False if not found
        """
        doc_ref = (
            db.collection(InventoryCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(InventoryCRUD.INVENTORY_SUBCOLLECTION)
            .document(item_id)
        )
        
        doc = doc_ref.get()
        if not doc.exists:
            return False
        
        doc_ref.delete()
        return True
    
    @staticmethod
    def delete_all(user_id: str) -> int:
        """
        Delete all inventory items for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Number of items deleted
        """
        collection_ref = (
            db.collection(InventoryCRUD.USERS_COLLECTION)
            .document(user_id)
            .collection(InventoryCRUD.INVENTORY_SUBCOLLECTION)
        )
        
        docs = collection_ref.get()
        count = 0
        
        for doc in docs:
            doc.reference.delete()
            count += 1
        
        return count


# Convenience functions for easier imports
async def create_inventory_item(user_id: str, item_data: InventoryItemCreate) -> InventoryItem:
    """Create a new inventory item."""
    return InventoryCRUD.create(user_id, item_data)


async def get_inventory_item(user_id: str, item_id: str) -> Optional[InventoryItem]:
    """Get a specific inventory item."""
    return InventoryCRUD.get(user_id, item_id)


async def get_user_inventory(user_id: str, limit: int = 100) -> List[InventoryItem]:
    """List all inventory items for a user."""
    return InventoryCRUD.list_by_user(user_id, limit)


async def get_expiring_items(user_id: str, days: int = 3) -> List[InventoryItem]:
    """Get items expiring within specified days."""
    from datetime import timedelta
    expiry_date = date.today() + timedelta(days=days)
    return InventoryCRUD.get_expiring_items(user_id, expiry_date)


async def update_inventory_item(
    user_id: str,
    item_id: str,
    update_data: InventoryItemUpdate
) -> Optional[InventoryItem]:
    """Update an inventory item."""
    return InventoryCRUD.update(user_id, item_id, update_data)


async def delete_inventory_item(user_id: str, item_id: str) -> bool:
    """Delete an inventory item."""
    return InventoryCRUD.delete(user_id, item_id)


async def delete_all_inventory(user_id: str) -> int:
    """Delete all inventory items for a user."""
    return InventoryCRUD.delete_all(user_id)
