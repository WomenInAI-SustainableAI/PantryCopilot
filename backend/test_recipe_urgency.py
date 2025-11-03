"""
Tests for expiry urgency scoring: earliest expiry among matches is used and unique names are collected.
Run this file directly to execute tests without pytest.
"""
import sys
import os
from datetime import datetime, timedelta, timezone

# Ensure src is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.services.recipe_scoring_service import calculate_expiry_urgency_score
from src.db.models import InventoryItem


def run_test_earliest_expiry_minimum():
    print("\n=== TEST: Urgency uses earliest expiry among duplicates ===")
    now = datetime.now(timezone.utc)
    user_id = "u"

    inv = [
        InventoryItem(
            id="t1", user_id=user_id, item_name="Tomato", quantity=2.0, unit="pcs",
            expiry_date=now + timedelta(days=5, hours=1), added_at=now, updated_at=now
        ),
        InventoryItem(
            id="t2", user_id=user_id, item_name="Fresh Tomato", quantity=1.0, unit="pcs",
            expiry_date=now + timedelta(days=1, hours=1), added_at=now, updated_at=now
        ),
        InventoryItem(
            id="b1", user_id=user_id, item_name="Basil", quantity=0.3, unit="bunch",
            expiry_date=now + timedelta(days=10), added_at=now, updated_at=now
        ),
    ]

    # Recipe mentions plural form "tomatoes", which should match both entries by substring logic
    score, expiring = calculate_expiry_urgency_score(["tomato", "cheese"], inv)
    print("Urgency score:", score)
    print("Expiring ingredients collected:", expiring)

    # Earliest of (5,1) days is 1 day => urgency contribution: 8
    assert score == 8, f"Expected urgency 8 for 1 day to expiry, got {score}"
    # Names are unique, and since min_days<=3 the matched names are recorded
    assert "Tomato" in expiring and "Fresh Tomato" in expiring, "Should record unique matched names"
    # Basil not included because it wasn't part of recipe ingredients
    assert all("Basil" not in name for name in expiring), "Non-recipe ingredients should not be recorded"

    print("✓ Earliest-expiry urgency test passed")


if __name__ == "__main__":
    try:
        run_test_earliest_expiry_minimum()
    except AssertionError as e:
        print(f"✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    print("All urgency scoring tests passed.")
