def session(client):
    s = client.post('/api/sessions').json()
    return s, {'Authorization': 'Bearer ' + s['token']}

def turn(client, s, headers, text, version, q=None):
    return client.post(f"/api/sessions/{s['session_id']}/assess", headers=headers,
                       json={'user_input': text, 'expected_version': version,
                             'question_id': q, 'language': 'en',
                             'location': {'lat': 28.545, 'lng': 77.273}})

def ready(client):
    s, h = session(client)
    response = turn(client, s, h, 'Need wound dressing for 2 days, 60 years old', 0).json()
    assert response['question_id'] == 'safety'
    response = turn(client, s, h, 'no', 1, 'safety').json()
    assert response['status'] == 'ready'
    assert response['matches']
    return s, h, response

def reservation(s, response):
    m = response['matches'][0]
    return {'session_id': s['session_id'], 'decision_version': response['version'],
            'caregiver_id': m['caregiver_id'], 'slot_id': m['slots'][0]['id'],
            'idempotency_key': 'test-reservation-001'}
