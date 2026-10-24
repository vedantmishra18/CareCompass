import hashlib
import json
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from backend.matching import PROFILES

ROOT = Path(__file__).resolve().parent.parent


class StoreError(Exception):
    def __init__(self, message, status=409):
        self.message, self.status = message, status


@contextmanager
def connect():
    path = Path(os.environ.get('DB_PATH', ROOT / 'outputs/carecompass.db'))
    path.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
    finally:
        db.close()


def initialise():
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY, token_hash TEXT NOT NULL, version INTEGER NOT NULL,
            state TEXT NOT NULL, expires TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS slots (
            id TEXT PRIMARY KEY, caregiver_id TEXT NOT NULL, start TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS bookings (
            id TEXT PRIMARY KEY, session_id TEXT NOT NULL REFERENCES sessions(id),
            decision_version INTEGER NOT NULL, caregiver_id TEXT NOT NULL,
            slot_id TEXT NOT NULL UNIQUE REFERENCES slots(id),
            idempotency_key TEXT NOT NULL, created TEXT NOT NULL,
            UNIQUE(session_id, idempotency_key));
        """)
        now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        for profile in PROFILES:
            for i, hours in enumerate(profile['slot_offsets_hours']):
                db.execute('INSERT OR IGNORE INTO slots VALUES (?,?,?)',
                           (f"{profile['id']}_{i}", profile['id'], (now + timedelta(hours=hours)).isoformat()))
        db.commit()


def new_session():
    sid, token = secrets.token_urlsafe(18), secrets.token_urlsafe(32)
    ttl = max(1, min(24, int(os.environ.get('SESSION_TTL_HOURS', 12))))
    expires = (datetime.now(timezone.utc) + timedelta(hours=ttl)).isoformat()
    state = {'history': [], 'answers': {}, 'language': 'en', 'last': None}
    with connect() as db:
        now = datetime.now(timezone.utc).isoformat()
        db.execute('DELETE FROM bookings WHERE session_id IN (SELECT id FROM sessions WHERE expires<=?)', (now,))
        db.execute('DELETE FROM sessions WHERE expires<=?', (now,))
        db.execute('INSERT INTO sessions VALUES (?,?,?,?,?)',
                   (sid, hashlib.sha256(token.encode()).hexdigest(), 0, json.dumps(state), expires))
        db.commit()
    return {'session_id': sid, 'token': token, 'version': 0, 'expires': expires}


def checked_session(db, sid, token):
    row = db.execute('SELECT * FROM sessions WHERE id=?', (sid,)).fetchone()
    digest = hashlib.sha256(token.encode()).hexdigest()
    if not row or not secrets.compare_digest(row['token_hash'], digest):
        raise StoreError('Session not found or access denied.', 404)
    if datetime.fromisoformat(row['expires']) <= datetime.now(timezone.utc):
        raise StoreError('Session expired. Start a new synthetic case.', 410)
    return {**dict(row), 'state': json.loads(row['state'])}


def get_session(sid, token):
    with connect() as db:
        return checked_session(db, sid, token)


def save_session(sid, token, version, state):
    with connect() as db:
        checked_session(db, sid, token)
        result = db.execute('UPDATE sessions SET state=?, version=version+1 WHERE id=? AND version=?',
                            (json.dumps(state), sid, version))
        if result.rowcount != 1:
            raise StoreError('This case changed in another tab. Reload or start a new case.')
        db.commit()
    return version + 1


def open_slots():
    with connect() as db:
        return [dict(r) for r in db.execute('SELECT * FROM slots WHERE id NOT IN (SELECT slot_id FROM bookings)')]


def reserve(request, token):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        session = checked_session(db, request.session_id, token)
        state = session['state']
        last = state.get('last') or {}
        if session['version'] != request.decision_version or last.get('status') != 'ready':
            raise StoreError('Decision changed or booking is not permitted. Reassess this case.')
        if last['result'].get('red_flags') or last['result'].get('urgency') == 'immediate':
            raise StoreError('Emergency cases cannot be booked.')
        old = db.execute('SELECT * FROM bookings WHERE session_id=? AND idempotency_key=?',
                         (request.session_id, request.idempotency_key)).fetchone()
        if old:
            if old['slot_id'] != request.slot_id or old['caregiver_id'] != request.caregiver_id:
                raise StoreError('Idempotency key was already used for a different reservation.')
            return dict(old)
        allowed = any(m['caregiver_id'] == request.caregiver_id and
                      any(s['id'] == request.slot_id for s in m['slots']) for m in last.get('matches', []))
        if not allowed:
            raise StoreError('This caregiver or slot was not offered for this decision.')
        slot = db.execute('SELECT * FROM slots WHERE id=? AND caregiver_id=?',
                          (request.slot_id, request.caregiver_id)).fetchone()
        if not slot or datetime.fromisoformat(slot['start']) <= datetime.now(timezone.utc):
            raise StoreError('This slot is no longer available. Reassess to refresh options.')
        record = (secrets.token_urlsafe(12), request.session_id, request.decision_version,
                  request.caregiver_id, request.slot_id, request.idempotency_key,
                  datetime.now(timezone.utc).isoformat())
        try:
            db.execute('INSERT INTO bookings VALUES (?,?,?,?,?,?,?)', record)
            db.commit()
        except sqlite3.IntegrityError:
            raise StoreError('This slot was just reserved. Reassess for another option.') from None
        return dict(db.execute('SELECT * FROM bookings WHERE id=?', (record[0],)).fetchone())


def get_booking(bid, sid, token):
    with connect() as db:
        checked_session(db, sid, token)
        row = db.execute('SELECT * FROM bookings WHERE id=? AND session_id=?', (bid, sid)).fetchone()
        if not row:
            raise StoreError('Booking not found.', 404)
        return dict(row)


def delete_session(sid, token):
    with connect() as db:
        checked_session(db, sid, token)
        db.execute('DELETE FROM bookings WHERE session_id=?', (sid,))
        db.execute('DELETE FROM sessions WHERE id=?', (sid,))
        db.commit()


def latest_booking(sid, token):
    with connect() as db:
        checked_session(db, sid, token)
        row = db.execute('SELECT b.*, s.start FROM bookings b JOIN slots s ON s.id=b.slot_id WHERE b.session_id=? ORDER BY b.created DESC LIMIT 1', (sid,)).fetchone()
        if not row:
            return None
        profile = next(p for p in PROFILES if p['id'] == row['caregiver_id'])
        return {**dict(row), 'name': profile['name']}
