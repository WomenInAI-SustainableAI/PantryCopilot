"""
Regression test: unit-aware subtraction.
Inventory has Chicken in mixed units (g and kg). Subtract 300g and ensure only 200g + 100g are consumed.
Run this file directly.
"""
import sys, os, types
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Stub CRUD
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


def run_test_unit_conversion():
    print("\n=== TEST: Unit-aware subtraction (g vs kg) ===")
    user_id = "u"
    now = datetime.utcnow()
    # Inventory: 200g today, 1kg tomorrow, 2kg day after
    store = [
        InventoryItem(
            id="g200", user_id=user_id, item_name="Chicken", quantity=200.0, unit="g",
            expiry_date=now + timedelta(days=0), added_at=now, updated_at=now,
        ),
        InventoryItem(
            id="kg1", user_id=user_id, item_name="Chicken", quantity=1.0, unit="kg",
            expiry_date=now + timedelta(days=1), added_at=now, updated_at=now,
        ),
        InventoryItem(
            id="kg2", user_id=user_id, item_name="Chicken", quantity=2.0, unit="kg",
            expiry_date=now + timedelta(days=2), added_at=now, updated_at=now,
        ),
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
                    unit=it.unit, expiry_date=it.expiry_date, added_at=it.added_at, updated_at=now,
                )
                return store[idx]
        raise AssertionError("Update target not found")

    def fake_delete_inventory_item(uid: str, item_id: str):
        assert uid == user_id
        # mutate original list
        remaining = [x for x in store if x.id != item_id]
        store[:] = remaining
        return True

    invsvc.get_user_inventory = fake_get_user_inventory  # type: ignore
    invsvc.update_inventory_item = fake_update_inventory_item  # type: ignore
    invsvc.delete_inventory_item = fake_delete_inventory_item  # type: ignore

    # Subtract 300g of chicken
    result = subtract_inventory_items(user_id, {"chicken": 300.0}, {"chicken": "g"})
    print("Result:", result)

    # Expect: g200 deleted; kg1 reduced to 0.9; kg2 unchanged
    ids = {it.id for it in store}
    assert "g200" not in ids, "200g item should be deleted"
    # find kg1 and kg2
    q_by_id = {it.id: it.quantity for it in store}
    assert abs(q_by_id.get("kg1", -1) - 0.9) < 1e-6, f"kg1 expected 0.9, got {q_by_id.get('kg1')}"
    assert abs(q_by_id.get("kg2", -1) - 2.0) < 1e-6, f"kg2 expected 2.0, got {q_by_id.get('kg2')}"

    print("✓ Unit-aware subtraction test passed")


if __name__ == "__main__":
    try:
        run_test_unit_conversion()
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print("All unit conversion tests passed.")
