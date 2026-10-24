from backend.tests.helpers import session, turn, ready, reservation


def test_emergency_invalidates_stale_booking(client):
    s, h, response = ready(client)
    stale = reservation(s, response)
    emergency = turn(client, s, h, 'Now cannot breathe', response['version']).json()
    assert emergency['status'] == 'emergency'
    assert emergency['result']['matched_caregivers'] == []
    assert client.post('/api/bookings', headers=h, json=stale).status_code == 409
    stale['decision_version'] = emergency['version']
    assert client.post('/api/bookings', headers=h, json=stale).status_code == 409


def test_contract_only_has_public_fields(client):
    response = client.post('/assess', json={'user_input': 'cannot breathe'})
    assert response.status_code == 200
    assert set(response.json()) == {'follow_up_question', 'care_type', 'urgency', 'red_flags', 'reasoning', 'matched_caregivers'}


def test_whitespace_and_location_validation(client):
    assert client.post('/assess', json={'user_input': '  '}).status_code == 422
    assert client.post('/assess', json={'user_input': 'help', 'location': {'lat': 100, 'lng': 0}}).status_code == 422


def test_stale_turn_and_question_tampering(client):
    s, h = session(client)
    first = turn(client, s, h, 'Need wound dressing', 0)
    assert first.status_code == 200
    assert turn(client, s, h, 'no', 0, 'safety').status_code == 409
    assert turn(client, s, h, 'no', 1, 'duration').status_code == 409


def test_unknown_after_four_questions_abstains(client):
    s, h = session(client)
    d = turn(client, s, h, 'I need help', 0).json()
    count = 0
    while d['question_id']:
        count += 1
        d = turn(client, s, h, 'not sure', d['version'], d['question_id']).json()
    assert count == 4
    assert d['status'] == 'review'
    assert d['matches'] == []


def test_large_request_rejected(client):
    result = client.post('/assess', content='x' * 66000, headers={'Content-Type': 'application/json'})
    assert result.status_code == 413


def test_health_and_unauthenticated_read(client):
    assert client.get('/health').json()['contract'] == 'provisional'
    s, h = session(client)
    assert client.get(f"/api/sessions/{s['session_id']}").status_code == 401


def test_emergency_path_does_not_need_matching_storage(client, monkeypatch):
    from backend import booking
    monkeypatch.setattr(booking, 'open_slots', lambda: (_ for _ in ()).throw(RuntimeError('offline')))
    response = client.post('/assess', json={'user_input': 'cannot breathe'})
    assert response.status_code == 200
    assert response.json()['urgency'] == 'immediate'
    assert response.json()['matched_caregivers'] == []


def test_emergency_update_survives_case_turn_limit(client):
    from backend import booking
    import json
    s, h, result = ready(client)
    with booking.connect() as db:
        row = db.execute('SELECT state FROM sessions WHERE id=?', (s['session_id'],)).fetchone()
        state = json.loads(row['state'])
        state['history'] += [{'role': 'user', 'content': 'unchanged'}] * 25
        db.execute('UPDATE sessions SET state=? WHERE id=?', (json.dumps(state), s['session_id']))
        db.commit()
    response = turn(client, s, h, 'Now cannot breathe', result['version'])
    assert response.status_code == 200
    assert response.json()['status'] == 'emergency'
