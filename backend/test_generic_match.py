"""
Test the generic fallback matching: ingredient 'chicken breast' matches inventory 'Chicken'.
"""
import sys, os, types
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Stub out Firestore CRUD to avoid external dependency
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


def run_test_generic_fallback():
    print("\n=== TEST: Generic fallback (chicken breast -> chicken) ===")
    user_id = "u"
    now = datetime.utcnow()
    store = [
        InventoryItem(
            id="c1", user_id=user_id, item_name="Chicken", quantity=1.0, unit="lb",
            expiry_date=now + timedelta(days=2), added_at=now, updated_at=now
        )
    ]

    import src.services.inventory_service as invsvc

    def fake_get_user_inventory(uid: str):
        assert uid == user_id
        return list(store)

    def fake_update_inventory_item(uid: str, item_id: str, update: InventoryItemUpdate):
        assert uid == user_id
        for idx, it in enumerate(store):
            if it.id == item_id:
                new_qty = update.quantity if update.quantity is not None else it.quantity
                store[idx] = InventoryItem(
                    id=it.id, user_id=it.user_id, item_name=it.item_name, quantity=new_qty,
                    unit=it.unit, expiry_date=it.expiry_date, added_at=it.added_at, updated_at=now
                )
                return store[idx]
        raise AssertionError("Update target not found")

    def fake_delete_inventory_item(uid: str, item_id: str):
        assert uid == user_id
        return True

    invsvc.get_user_inventory = fake_get_user_inventory  # type: ignore
    invsvc.update_inventory_item = fake_update_inventory_item  # type: ignore
    invsvc.delete_inventory_item = fake_delete_inventory_item  # type: ignore

    result = subtract_inventory_items(user_id, {"chicken breast": 0.5})
    print("Result:", result)
    msg = result.get("chicken breast", "")
    assert "updated Chicken" in msg or "deleted Chicken" in msg, "Should match generic 'Chicken'"
    print("✓ Generic fallback test passed")


if __name__ == "__main__":
    try:
        run_test_generic_fallback()
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print("All generic matching tests passed.")
