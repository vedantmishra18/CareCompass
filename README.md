# CareCompass

A runnable, synthetic-data care navigation prototype for Team Diligence.
React + FastAPI + SQLite, local TF-IDF/logistic routing models, explicit emergency
rules, targeted intake, eligible caregiver ranking and persisted mock reservations.

**Not a clinical service. No diagnosis, prescribing, real dispatch or real patient data.**
The released organizer dataset/taxonomy/schema were not available when this package
was authored. `data/taxonomy.json` and the sample labels are engineering fixtures,
not doctor-reviewed rules. The API mirrors the indicative PDF, not a verified final
contract. CSV and unresolved-case handling must be adapted to the released format.
The current policy covers only a narrow range of adult care requests; it is not an
exhaustive triage protocol and must not be used for real care decisions.

## Start locally (Mac/Linux)

Run all Python commands from this repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
python -m backend.train
python -m uvicorn backend.main:app --reload --no-access-log
```

In another terminal:

```bash
cd frontend
npm ci
npm run dev
```

Open http://localhost:5173. API docs: http://localhost:8000/docs.
Node 22+ and Python 3.11+ recommended. No API keys or paid model required.
`models/routing.joblib` is generated locally; only load trusted model
files because joblib deserialisation can execute code. Do not upload model files.
Missing local model falls back explicitly to the provisional demo policy.
The learned proposal can choose between the service options permitted by the
provisional policy; it cannot lower the policy urgency floor or override red flags.
A model immediate-urgency signal conservatively enters the emergency path. This limitation is deliberate and
is exposed in demo metadata; the synthetic training set is a pipeline smoke test.

## One server, production build

```bash
cd frontend
npm ci
npm run build
cd ..
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --no-access-log
```

Open http://localhost:8000. Restart the API after building the frontend.
A public host needs HTTPS, a writable persistent volume and the required port.
Environment overrides: `DB_PATH`, `MODEL_DIR`, `SESSION_TTL_HOURS`,
`ALLOWED_ORIGINS` (comma-separated). `.env.example` is a reference: either export
variables in your shell or use your host's settings; the Python process does not load .env automatically. Compose handles its own interpolation.

## Docker Compose (recommended container startup)

```bash
docker compose up --build
```

Open http://localhost:8000. Compose builds the frontend/model into one image and
persists SQLite under a named volume. `docker compose down` stops/removes the
container while retaining the demo volume. A real deployment still requires the
organizer's final contract and reviewed policy.

Compose reads `.env` for interpolation if you create it from `.env.example`.
`PORT` controls the host port; the container always listens on 8000 for its health
check. Container DB/model paths are fixed absolute paths; local MODEL_DIR/DB_PATH
values cannot accidentally point a container at host-relative paths. Models are
baked into the image under /app/models; no empty host model directory masks them.

## Plain Docker alternative

```bash
docker build -t carecompass .
docker run --rm -p 8000:8000 -v carecompass-data:/app/outputs carecompass
```

Docker installs dependencies, builds the UI, and trains the demo model. No checked-in
local database is needed. The SQLite volume is for a single-container prototype,
not a multi-replica architecture. Hosting, Docker daemon and live microphone access
must be verified on the actual demo machine.

## Tests and evaluation

```bash
python -m pytest backend/tests -q
python -m backend.evaluate metrics --output outputs/metrics.json
python -m backend.evaluate predict --input data/demo_train.csv --output outputs/demo_predictions.csv
```

Prediction input requires `case_id,user_input`. Optional `conversation_history`
contains a JSON array of role/content messages. `age` may contain an explicitly supplied age; `safety` may contain an explicit
supplied answer; never invent a negative answer for hidden cases. Output currently
uses `case_id,care_type,urgency`, which is provisional. An unresolved case fails
export by default. `--allow-abstain` emits blank labels for engineering inspection
only; do not submit blanks without organizer approval. Confirm one-shot batch rules.
Metrics separate raw-classifier F1 from deployed-policy F1, abstentions and emergency recall. None constitutes
clinical validation. Never report scores without dataset/split/sample context.

## Approved repository structure

```text
carecompass/
  README.md, .gitignore, .env.example, Dockerfile, docker-compose.yml
  backend/
    main.py, schemas.py, intake.py, triage.py, matching.py, booking.py
    train.py, evaluate.py, requirements.txt
    tests/
      conftest.py, helpers.py
      test_safety.py, test_workflow.py, test_matching.py, test_booking.py
      test_evaluation.py
  frontend/
    package.json, package-lock.json, index.html, vite.config.js
    public/font-license.txt
    src/
      main.jsx, App.jsx, api.js, styles.css
      Intake.jsx, Result.jsx, useCare.js, copy.js
  data/README.md, caregivers.json, taxonomy.json, demo_train.csv
  models/.gitkeep
  docs/api-contract.md
```

Models under `models/` are generated and ignored except `.gitkeep`.
`backend/__init__.py` is the Python package marker. `VERIFICATION.md` records
checks; generated `frontend/dist/` and `outputs/` remain ignored. The extra small
frontend/test support modules keep screens and fixtures easy to maintain.

## Interfaces and files

- `backend/main.py`: public contract, orchestration and demo session API.
- `backend/schemas.py`: provisional public models; replace with released schema.
- `backend/intake.py`: supported-language lexicon, negation and missing questions.
- `backend/triage.py`: safety override, narrow policy and local classifier checks.
- `backend/matching.py`: eligibility, five-factor score, approximate distance.
- `backend/booking.py`: session tokens, version checks and SQLite reservations.
- `backend/train.py`, `evaluate.py`: grouped training and batch/metrics commands.
- `models/`: generated model location; train, evaluate and runtime share MODEL_DIR.
- `docs/api-contract.md`: public contract, demo endpoints and organizer adapter tasks.
- `frontend/src/App.jsx`: layout; `useCare.js`: state/API flow;
  `Intake.jsx` and `Result.jsx`: screens; `copy.js`: language copy;
  `api.js` and `styles.css`: requests and styling.

`POST /assess` returns exactly the seven indicative fields. Question responses have
null care/urgency and no matches. Emergency responses have no matches. Unknown cases
return no fabricated label, with an incomplete/review explanation; this needs final
schema confirmation. `/api/sessions` and `/api/bookings` are separate demo APIs.
Session endpoints use `Authorization: Bearer <token>`; no token is needed for public
stateless assessment. OpenAPI shows all fields and routes. SQLite is seeded with
future mock slots on first startup; old slots are not shifted forward on restart.
Use a fresh DB_PATH for a fresh demonstration, not a real-data reset.

## Demo rehearsal

1. Confirm synthetic-data use. Select English, Hindi or Hinglish.
2. Enter: `Need wound dressing for 2 days, 60 years old`.
3. Answer safety `No`; inspect the qualified nurse and available slots.
4. Save one demo reservation. No provider is contacted.
5. Add `Now cannot breathe`. Matching stops and further booking is blocked.
6. Show the stale-booking test and actual model/safety results in the terminal.
7. Delete/reset the case after the demo. Never place a test call to 112.

Voice uses the browser's SpeechRecognition where available. It can send audio to
the browser provider; permission and connectivity may be required. The app stores no
audio. Review the transcript before submission. Speech is optional at runtime, but
live multilingual voice quality still needs manual device testing. Text is backup.

## Privacy and limitations

Use fictional requests only. SQLite contains synthetic conversation text during an
encounter; browser sessionStorage stores the token/ID, not the transcript. Tokens
expire (default 12 hours); expired rows are purged on the next session creation.
Delete/reset immediately removes the case and its demo reservations. Keep access
logs off; no debug route dumps cases. Basic per-process request/body limits are
included, not production security. Browser privacy/permission and public host
settings need review before any real deployment.

Current limits: finite lexicon, incomplete negation/history understanding, narrow
adult-only policy, unreviewed clinical mappings, provisional labels, small synthetic
training data, no real scheduling/dispatch. Unknown/unsupported cases abstain; new
emergencies keep the current encounter in emergency state. This is a hackathon
prototype, not validated medical software.

## Team and history

Shashank: API/integration. Aditya: intake/routing/safety/evaluation. Vedant: UI/voice.
Priyanshu: matching/booking/tests. The companion development guide has 23 reviewable
patch stages. Apply, understand, test and commit each genuine change when ready.
No history, timestamps or team authorship have been fabricated. Follow event rules
on AI assistance and attribution; inspect and adapt all supplied source yourselves.

## References / attribution

Provided CareCompass brief pp. 1-5 and event timeline pp. 1-3; final deadline confirmed
by the team as 25 Oct 2026, 11:30 AM IST. External implementation references:
- FastAPI: https://fastapi.tiangolo.com/tutorial/static-files/
- Pydantic: https://docs.pydantic.dev/latest/concepts/models/
- scikit-learn: https://scikit-learn.org/stable/modules/feature_extraction.html
- Docker Compose: https://docs.docker.com/reference/compose-file/services/
- Speech support/privacy: https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition
- Emergency example: https://www.nhs.uk/symptoms/shortness-of-breath/
- India emergency number: https://www.incredibleindia.gov.in/en/emergency

All fixture content is newly authored synthetic material. Third-party libraries
retain their own licences. Noto Sans Devanagari is self-hosted via @fontsource
under the SIL Open Font License, included under frontend/public/font-license.txt. The team must review the actual event's source-code,
assistance, data and licensing rules before submission.
