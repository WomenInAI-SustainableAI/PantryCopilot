"""
Tests for inventory subtraction logic: cascading across duplicates, oldest-first.
Run this file directly to execute tests without pytest.
"""
import sys
import os
import types
from datetime import datetime, timedelta

# Ensure src is importable and stub out src.db.crud to avoid Firestore init
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Pre-insert stub module for src.db.crud so inventory_service import doesn't initialize Firestore
crud_mod = types.ModuleType('src.db.crud')
def _stub(*args, **kwargs):
    raise RuntimeError('Stubbed CRUD called before monkeypatch')
crud_mod.create_inventory_item = _stub
crud_mod.get_user_inventory = _stub
crud_mod.update_inventory_item = _stub
crud_mod.delete_inventory_item = _stub
crud_mod.get_expiring_items = _stub
sys.modules['src.db.crud'] = crud_mod

from src.services.inventory_service import subtract_inventory_items
from src.db.models import InventoryItem, InventoryItemUpdate


def run_test_cascading_subtraction():
    """Verify subtraction cascades oldest-first across duplicate items."""
    print("\n=== TEST: Cascading subtraction across duplicates (oldest-first) ===")

    user_id = "test-user"
    now = datetime.utcnow()

    # In-memory inventory store
    store = [
        InventoryItem(
            id="i1",
            user_id=user_id,
            item_name="Milk",
            quantity=1.0,
            unit="litre",
            expiry_date=now + timedelta(days=1),
            added_at=now,
            updated_at=now,
        ),
        InventoryItem(
            id="i2",
            user_id=user_id,
            item_name="Milk",
            quantity=0.5,
            unit="litre",
            expiry_date=now + timedelta(days=0),  # earliest expiry
            added_at=now,
            updated_at=now,
        ),
        InventoryItem(
            id="i3",
            user_id=user_id,
            item_name="Milk",
            quantity=2.0,
            unit="litre",
            expiry_date=now + timedelta(days=3),
            added_at=now,
            updated_at=now,
        ),
    ]

    # Monkeypatch the CRUD functions used inside inventory_service
    import src.services.inventory_service as invsvc

    def fake_get_user_inventory(uid: str):  # returns list[InventoryItem]
        assert uid == user_id
        return list(store)  # return a shallow copy for safety

    def fake_update_inventory_item(uid: str, item_id: str, update: InventoryItemUpdate):
        assert uid == user_id
        for idx, it in enumerate(store):
            if it.id == item_id:
                # Apply only provided fields
                new_qty = update.quantity if update.quantity is not None else it.quantity
                store[idx] = InventoryItem(
                    id=it.id,
                    user_id=it.user_id,
                    item_name=it.item_name,
                    quantity=new_qty,
                    unit=it.unit,
                    expiry_date=it.expiry_date,
                    added_at=it.added_at,
                    updated_at=datetime.utcnow(),
                )
                return store[idx]
        raise AssertionError(f"Item {item_id} not found in store for update")

    def fake_delete_inventory_item(uid: str, item_id: str):
        assert uid == user_id
        nonlocal_store = [it for it in store if it.id != item_id]
        if len(nonlocal_store) == len(store):
            raise AssertionError(f"Item {item_id} not found in store for delete")
        # mutate the original list in place
        store[:] = nonlocal_store
        return True

    invsvc.get_user_inventory = fake_get_user_inventory  # type: ignore
    invsvc.update_inventory_item = fake_update_inventory_item  # type: ignore
    invsvc.delete_inventory_item = fake_delete_inventory_item  # type: ignore

    # Use 2.2 litres of Milk -> should delete i2 (0.5), delete i1 (1.0), and reduce i3 from 2.0 to 1.3
    result = subtract_inventory_items(user_id, {"Milk": 2.2})
    print("Result:", result)

    # Assertions on actions text
    actions = result.get("Milk", "")
    assert "deleted Milk" in actions, "Should delete at least one 'Milk' entry"
    assert "updated Milk" in actions, "Should update the remaining 'Milk' entry"
    assert "missing" not in actions, "Should not report missing quantity"

    # Assertions on final store state: only i3 remains with 0.8? Wait compute: 0.5 + 1.0 = 1.5; remaining to take 0.7 from 2.0 -> left 1.3
    # But we used 2.2: 0.5 + 1.0 + 0.7 = 2.2 -> remaining on i3 should be 1.3
    remaining = {it.id: (it.item_name, it.quantity) for it in store}
    assert "i2" not in remaining and "i1" not in remaining, "Oldest items should be deleted"
    name, qty = remaining.get("i3", (None, None))
    assert name == "Milk" and abs(qty - 1.3) < 1e-6, f"Expected Milk qty 1.3, got {qty}"

    print("✓ Cascading subtraction test passed")


if __name__ == "__main__":
    try:
        run_test_cascading_subtraction()
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print("All inventory subtraction tests passed.")
