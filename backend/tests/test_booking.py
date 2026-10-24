from backend.tests.helpers import ready, reservation


def test_full_booking_and_duplicate(client):
    s, h, response = ready(client)
    body = reservation(s, response)
    a = client.post('/api/bookings', headers=h, json=body)
    b = client.post('/api/bookings', headers=h, json=body)
    assert a.status_code == b.status_code == 201
    assert a.json()['booking']['id'] == b.json()['booking']['id']
    bid = a.json()['booking']['id']
    assert client.get(f'/api/bookings/{bid}', params={'session_id': s['session_id']}, headers=h).status_code == 200


def test_wrong_token_and_conflicting_slot(client):
    s, h, result = ready(client)
    payload = reservation(s, result)
    assert client.post('/api/bookings', json=payload).status_code == 401
    assert client.post('/api/bookings', headers={'Authorization': 'Bearer wrong'}, json=payload).status_code == 404
    other, other_h, other_result = ready(client)
    assert client.post('/api/bookings', headers=h, json=payload).status_code == 201
    assert client.post('/api/bookings', headers=other_h, json=reservation(other, other_result)).status_code == 409


def test_delete_case_releases_demo_slot(client):
    s, h, result = ready(client)
    payload = reservation(s, result)
    assert client.post('/api/bookings', headers=h, json=payload).status_code == 201
    assert client.delete(f"/api/sessions/{s['session_id']}", headers=h).status_code == 204
    assert client.get(f"/api/sessions/{s['session_id']}", headers=h).status_code == 404


def test_reload_returns_saved_confirmation(client):
    s, h, result = ready(client)
    saved = client.post('/api/bookings', headers=h, json=reservation(s, result)).json()['booking']
    restored = client.get(f"/api/sessions/{s['session_id']}", headers=h).json()
    assert restored['booking']['id'] == saved['id']
    assert restored['booking']['start']


def test_session_expiry_blocks_booking(client):
    from backend import booking
    s, h, result = ready(client)
    with booking.connect() as db:
        db.execute("UPDATE sessions SET expires='2000-01-01T00:00:00+00:00' WHERE id=?", (s['session_id'],))
        db.commit()
    assert client.post('/api/bookings', headers=h, json=reservation(s, result)).status_code == 410
