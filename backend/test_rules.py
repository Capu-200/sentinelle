"""
Test script for Payon restriction rules.
Validates each rule's logic with mocked scenarios.

Usage:
    cd backend
    python test_rules.py
"""
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch
from app.services.restriction_rules import (
    rule_amount_anomaly,
    rule_freq_spike,
    rule_new_account_activity,
    rule_new_beneficiary,
    rule_geo_anomaly,
    rule_odd_hour,
    rule_structuring,
    rule_circular_flow,
    rule_activity_burst,
    rule_recidivism,
)
from app.services.rule_engine import (
    evaluate_transaction,
    _compute_trust_multiplier,
    _resolve_risk_level,
    THRESHOLD_APPROVE,
    THRESHOLD_REVIEW,
)


# ========= Helpers =========

class MockScalar:
    """Mock for db.execute(...).scalar()"""
    def __init__(self, value):
        self._value = value
    def scalar(self):
        return self._value

class MockScalarsAll:
    """Mock for db.execute(...).scalars().all()"""
    def __init__(self, values):
        self._values = values
    def scalars(self):
        return self
    def all(self):
        return self._values

class MockScalarAndAll:
    """Mock that supports both .scalar() and .scalars().all()"""
    def __init__(self, values=None, scalar_value=None):
        self._values = values or []
        self._scalar_value = scalar_value
    def scalar(self):
        return self._scalar_value
    def scalars(self):
        return self
    def all(self):
        return self._values
    def first(self):
        return self._values[0] if self._values else None


passed = 0
failed = 0

def assert_true(condition, test_name):
    global passed, failed
    if condition:
        print(f"  [PASS] {test_name}")
        passed += 1
    else:
        print(f"  [FAIL] {test_name}")
        failed += 1


# ========= Test ODD HOUR (no DB needed) =========

def test_rule_odd_hour():
    print("\n--- RULE_ODD_HOUR ---")
    db = MagicMock()
    
    # 3 AM → should trigger
    ctx_night = {"created_at": "2026-03-27T03:15:00Z"}
    result = rule_odd_hour(ctx_night, db)
    assert_true(result.triggered, "3:15 AM triggers rule")
    assert_true(result.reason_code == "RULE_ODD_HOUR", "correct reason code")
    assert_true(result.score_delta == 0.10, "score delta = 0.10")

    # 10 AM → should NOT trigger
    ctx_day = {"created_at": "2026-03-27T10:00:00Z"}
    result = rule_odd_hour(ctx_day, db)
    assert_true(not result.triggered, "10:00 AM does not trigger")

    # 1 AM → edge case, should trigger
    ctx_edge = {"created_at": "2026-03-27T01:00:00Z"}
    result = rule_odd_hour(ctx_edge, db)
    assert_true(result.triggered, "1:00 AM triggers (edge)")

    # 5 AM → edge case, should trigger (hour=5 is in range 1-5)
    ctx_edge2 = {"created_at": "2026-03-27T05:59:00Z"}
    result = rule_odd_hour(ctx_edge2, db)
    assert_true(result.triggered, "5:59 AM triggers (hour=5 is in 1-5 range)")
    # Actually hour=5 IS in range 1-5, so it should trigger
    # Let me re-check: 1 <= 5 <= 5 is True


def test_rule_odd_hour_edge():
    """Check edge: 5:59 → hour=5 → 1<=5<=5 → yes"""
    print("\n--- RULE_ODD_HOUR (edge) ---")
    db = MagicMock()
    ctx = {"created_at": "2026-03-27T05:59:00Z"}
    result = rule_odd_hour(ctx, db)
    assert_true(result.triggered, "5:59 AM triggers (hour=5 is in 1-5)")

    ctx6 = {"created_at": "2026-03-27T06:00:00Z"}
    result = rule_odd_hour(ctx6, db)
    assert_true(not result.triggered, "6:00 AM does NOT trigger")


# ========= Test TRUST MULTIPLIER =========

def test_trust_multiplier():
    print("\n--- TRUST MULTIPLIER ---")
    assert_true(_compute_trust_multiplier(100) == 1.0, "trust=100 → mult=1.0")
    assert_true(_compute_trust_multiplier(50) == 1.5, "trust=50 → mult=1.5")
    assert_true(_compute_trust_multiplier(0) == 2.0, "trust=0 → mult=2.0")


# ========= Test RISK LEVEL RESOLUTION =========

def test_risk_level():
    print("\n--- RISK LEVEL RESOLUTION ---")
    assert_true(_resolve_risk_level(100) == "LOW", "trust=100 → LOW")
    assert_true(_resolve_risk_level(80) == "LOW", "trust=80 → LOW")
    assert_true(_resolve_risk_level(79) == "MEDIUM", "trust=79 → MEDIUM")
    assert_true(_resolve_risk_level(60) == "MEDIUM", "trust=60 → MEDIUM")
    assert_true(_resolve_risk_level(35) == "HIGH", "trust=35 → HIGH")
    assert_true(_resolve_risk_level(10) == "CRITICAL", "trust=10 → CRITICAL")
    assert_true(_resolve_risk_level(0) == "CRITICAL", "trust=0 → CRITICAL")


# ========= Test AMOUNT ANOMALY =========

def test_rule_amount_anomaly():
    print("\n--- RULE_AMOUNT_ANOMALY ---")
    db = MagicMock()
    
    # Not enough history → no trigger
    db.execute.return_value = MockScalarsAll([Decimal("20"), Decimal("25")])  # only 2
    ctx = {"initiator_user_id": "u1", "amount": 500}
    result = rule_amount_anomaly(ctx, db)
    assert_true(not result.triggered, "< 3 history entries → no trigger")

    # Normal amount within range
    db.execute.return_value = MockScalarsAll([
        Decimal("20"), Decimal("25"), Decimal("30"), Decimal("22"), Decimal("28")
    ])
    ctx = {"initiator_user_id": "u1", "amount": 30}
    result = rule_amount_anomaly(ctx, db)
    assert_true(not result.triggered, "amount=30 within normal range")

    # Big spike → trigger
    db.execute.return_value = MockScalarsAll([
        Decimal("20"), Decimal("25"), Decimal("30"), Decimal("22"), Decimal("28")
    ])
    ctx = {"initiator_user_id": "u1", "amount": 450}
    result = rule_amount_anomaly(ctx, db)
    assert_true(result.triggered, "amount=450 >> avg=25 → trigger")
    assert_true(result.score_delta == 0.25, "score delta = 0.25")


# ========= Test FREQ SPIKE =========

def test_rule_freq_spike():
    print("\n--- RULE_FREQ_SPIKE ---")
    db = MagicMock()

    # 5 tx in 10 min → trigger
    db.execute.return_value = MockScalarAndAll(scalar_value=5)
    ctx = {"initiator_user_id": "u1"}
    result = rule_freq_spike(ctx, db)
    assert_true(result.triggered, "5 tx in 10min → trigger")
    assert_true(result.score_delta == 0.30, "score delta = 0.30")


# ========= Test NEW ACCOUNT ACTIVITY =========

def test_rule_new_account_activity():
    print("\n--- RULE_NEW_ACCOUNT_ACTIVITY ---")
    db = MagicMock()

    # New account (2 min old) + high amount → trigger
    mock_user = MagicMock()
    mock_user.created_at = datetime.utcnow() - timedelta(minutes=2)
    db.get.return_value = mock_user
    ctx = {"initiator_user_id": "u1", "amount": 200}
    result = rule_new_account_activity(ctx, db)
    assert_true(result.triggered, "2min old account + 200 PYC → trigger")

    # Old account → no trigger
    mock_user.created_at = datetime.utcnow() - timedelta(days=30)
    result = rule_new_account_activity(ctx, db)
    assert_true(not result.triggered, "30d old account → no trigger")

    # New account but small amount → no trigger
    mock_user.created_at = datetime.utcnow() - timedelta(minutes=2)
    ctx_small = {"initiator_user_id": "u1", "amount": 10}
    result = rule_new_account_activity(ctx_small, db)
    assert_true(not result.triggered, "2min old + 10 PYC → no trigger")


# ========= Run all tests =========

if __name__ == "__main__":
    print("=" * 50)
    print("PAYON RESTRICTION RULES — Unit Tests")
    print("=" * 50)
    
    test_rule_odd_hour()
    test_rule_odd_hour_edge()
    test_trust_multiplier()
    test_risk_level()
    test_rule_amount_anomaly()
    test_rule_freq_spike()
    test_rule_new_account_activity()
    
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    sys.exit(1 if failed else 0)
