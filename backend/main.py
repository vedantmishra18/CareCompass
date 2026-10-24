import os
import time
import sqlite3
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from backend import booking
from backend.intake import QUESTIONS, extract, language, next_question, reconstruct
from backend.matching import rank
from backend.schemas import AssessmentRequest, AssessmentResponse, BookingRequest, Turn
from backend.triage import HELP, model_suggestion, red_flags, route


@asynccontextmanager
async def lifespan(app):
    booking.initialise()
    _recent.clear()
    yield


app = FastAPI(title='CareCompass', version='1.0.0', lifespan=lifespan)
origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:5173').split(',')
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=['GET', 'POST', 'DELETE'],
                   allow_headers=['Content-Type', 'Authorization'])


# Single-process demo limit. Shared rate limiting is needed for multiple replicas.
_recent = defaultdict(deque)


@app.middleware('http')
async def request_limits(request: Request, call_next):
    if request.method == 'POST':
        ip = request.client.host if request.client else 'local'
        now = time.monotonic()
        queue = _recent[ip]
        while queue and queue[0] < now - 60:
            queue.popleft()
        if len(queue) >= 80:
            return JSONResponse({'detail': 'Too many requests. Retry in a minute.'}, status_code=429)
        queue.append(now)
        size = request.headers.get('content-length')
        if size and (not size.isdigit() or int(size) > 65536):
            return JSONResponse({'detail': 'Request is too large.'}, status_code=413)
        body = b''
        async for chunk in request.stream():
            body += chunk
            if len(body) > 65536:
                return JSONResponse({'detail': 'Request is too large.'}, status_code=413)
        request._body = body
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['Cache-Control'] = 'no-store' if request.url.path.startswith('/api') else 'no-cache'
    return response


@app.exception_handler(sqlite3.OperationalError)
async def database_unavailable(request, exc):
    return JSONResponse({'detail': 'Demo storage is unavailable. Retry later; do not delay real emergency help.'}, status_code=503)


def token_from(header):
    if not header or not header.startswith('Bearer '):
        raise HTTPException(401, 'A session token is required.')
    return header[7:]


def assess(history, answers, code, location):
    facts = extract(history)
    flags = red_flags(history, answers)
    if flags:
        result = AssessmentResponse(care_type='emergency_referral', urgency='immediate',
                                    red_flags=flags, reasoning=HELP[code])
        return {'result': result.model_dump(), 'status': 'emergency', 'facts': facts,
                'question_id': None, 'matches': [], 'mode': 'provisional_demo_policy'}
    question_id = next_question(history, answers, code)
    if question_id:
        question = QUESTIONS[question_id][code]
        result = AssessmentResponse(follow_up_question=question,
                                    reasoning='A relevant fact is missing; no final care decision has been made.')
        return {'result': result.model_dump(), 'status': 'question', 'facts': facts,
                'question_id': question_id, 'matches': [], 'mode': 'provisional_demo_policy'}
    values, status, facts = route(history, answers, code)
    matches = []
    if status == 'ready':
        matches = rank(values['care_type'], values['urgency'], facts, location, code, booking.open_slots())
    result = AssessmentResponse(**values, matched_caregivers=[
        {'caregiver_id': m['caregiver_id'], 'score': m['score'], 'reason': m['reason']} for m in matches])
    return {'result': result.model_dump(), 'status': status, 'facts': facts,
            'question_id': None, 'matches': matches, 'mode': 'model_checked_demo_policy' if model_suggestion(history) else 'provisional_demo_policy',
            'model_proposal': model_suggestion(history)}


@app.get('/health')
def health():
    return {'status': 'ok', 'mode': 'synthetic_demo', 'contract': 'provisional'}


@app.post('/assess', response_model=AssessmentResponse)
def public_assess(request: AssessmentRequest):
    history = [m.model_dump() for m in request.conversation_history]
    history.append({'role': 'user', 'content': request.user_input})
    code = language(request.language, request.user_input)
    result = assess(history, reconstruct(history), code,
                    request.location.model_dump() if request.location else None)
    return result['result']


@app.post('/api/sessions', status_code=201)
def create_session():
    return booking.new_session()


@app.post('/api/sessions/{sid}/assess')
def session_assess(sid: str, request: Turn, authorization: str | None = Header(default=None)):
    token = token_from(authorization)
    try:
        session = booking.get_session(sid, token)
        if session['version'] != request.expected_version:
            raise booking.StoreError('Stale case version. Reload the case before continuing.')
        state = session['state']
        history, answers = state['history'], state['answers']
        if len(history) >= 24 and not red_flags([{'role': 'user', 'content': request.user_input}]):
            raise booking.StoreError('Case limit reached. Start a new synthetic case.', 422)
        if request.question_id:
            last = state.get('last') or {}
            if last.get('question_id') != request.question_id:
                raise booking.StoreError('This question is no longer active.')
            answers[request.question_id] = request.user_input
        code = language(request.language, request.user_input)
        history.append({'role': 'user', 'content': request.user_input})
        location = request.location.model_dump() if request.location else state.get('location')
        decision = assess(history, answers, code, location)
        previous = state.get('last') or {}
        if previous.get('status') == 'emergency' and decision['status'] != 'emergency':
            decision = previous
        if decision['status'] != 'question':
            state['question_complete'] = True
        if decision['question_id']:
            history.append({'role': 'assistant', 'content': decision['result']['follow_up_question']})
        state.update(history=history, answers=answers, language=code, location=location, last=decision)
        version = booking.save_session(sid, token, request.expected_version, state)
        return {**decision, 'session_id': sid, 'version': version}
    except booking.StoreError as exc:
        raise HTTPException(exc.status, exc.message) from None


@app.get('/api/sessions/{sid}')
def read_session(sid: str, authorization: str | None = Header(default=None)):
    try:
        s = booking.get_session(sid, token_from(authorization))
        return {'session_id': sid, 'version': s['version'], 'decision': s['state'].get('last'),
                'booking': booking.latest_booking(sid, token_from(authorization))}
    except booking.StoreError as exc:
        raise HTTPException(exc.status, exc.message) from None


@app.delete('/api/sessions/{sid}', status_code=204)
def remove_session(sid: str, authorization: str | None = Header(default=None)):
    try:
        booking.delete_session(sid, token_from(authorization))
    except booking.StoreError as exc:
        raise HTTPException(exc.status, exc.message) from None


@app.post('/api/bookings', status_code=201)
def create_booking(request: BookingRequest, authorization: str | None = Header(default=None)):
    try:
        return {'booking': booking.reserve(request, token_from(authorization)), 'synthetic': True}
    except booking.StoreError as exc:
        raise HTTPException(exc.status, exc.message) from None


@app.get('/api/bookings/{bid}')
def read_booking(bid: str, session_id: str, authorization: str | None = Header(default=None)):
    try:
        return {'booking': booking.get_booking(bid, session_id, token_from(authorization)), 'synthetic': True}
    except booking.StoreError as exc:
        raise HTTPException(exc.status, exc.message) from None


WEB = Path(__file__).resolve().parent.parent / 'frontend/dist'
if WEB.exists():
    app.mount('/assets', StaticFiles(directory=WEB / 'assets'), name='assets')

    @app.get('/', include_in_schema=False)
    def index():
        return FileResponse(WEB / 'index.html')
