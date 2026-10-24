from datetime import datetime, timedelta, timezone
from backend.matching import rank


def slots():
    now = datetime.now(timezone.utc)
    return [{'id': 'one', 'caregiver_id': 'CG_001', 'start': (now + timedelta(hours=2)).isoformat()},
            {'id': 'two', 'caregiver_id': 'CG_008', 'start': (now + timedelta(hours=1)).isoformat()}]


def test_required_wound_skill_excludes_close_high_rated_nurse():
    results = rank('nurse_home_visit', 'same_day', {'wound': {'state': 'present'}}, None, 'hi', slots())
    assert [m['caregiver_id'] for m in results] == ['CG_001']
    assert results[0]['distance_km'] is None
    assert 0 <= results[0]['score'] <= 1


def test_empty_and_emergency_never_produce_matches():
    assert rank('emergency_referral', 'immediate', {}, None, 'en', slots()) == []
    assert rank('nurse_home_visit', 'same_day', {}, None, 'en', []) == []


def test_distant_home_visit_is_not_returned():
    assert rank('nurse_home_visit', 'same_day', {'wound': {'state': 'present'}},
                {'lat': 12.97, 'lng': 77.59}, 'en', slots()) == []
