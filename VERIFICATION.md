# Verification record

Verified on 24 October 2026 in the provided Linux environment, Python 3.12 / Node 24.
This record concerns engineering behaviour, not clinical safety certification.

## Passed

- 43 pytest checks (retained after test reorganisation): safety/negation, unsupported groups, corrupted model fallback,
  bounded learned choices, urgency floor, public response shape, sessions/access,
  duplicate reservations, slot conflicts, stale booking rejection, deletion,
  expiry, request-size limit, no-match/distance/skills, grouped split and CSV IDs.
- React/Vite production build, including self-hosted Devanagari fonts.
- Browser automation: real backend intake, wound-care recommendation, saved mock
  booking, restored confirmation after reload, emergency update removing booking,
  Hindi interview/routing and a 390px mobile viewport without horizontal overflow.
- No browser page errors during that scripted journey.
- Demo predictions export: 108 synthetic engineering cases, provisional columns.
- Model training and held-out metrics run. All examples/labels are synthetic
  engineering fixtures, not doctor-reviewed validation or hidden-test performance.

## Not verified / still required

- Organizer's released API schema, doctor-labelled data, care taxonomy, hidden-test
  columns, follow-up batch behaviour and actual scoring metric composition.
- Clinical rule completeness, unseen phrasing, generalisation or real outcomes.
- Live microphone capture/recognition on the team's actual devices and event Wi-Fi.
  The permission/fallback path is implemented; text remains the backup.
- Public hosting, HTTPS permissions and cold starts. No public deployment created.
- Docker image execution: Docker daemon unavailable here. UI build/backend run were
  checked separately; verify the supplied Dockerfile on your own machine.
- Repo access, 23 actual development commits, final write-up and demo video. These
  are the team's real event work; no Git history was created in this package.

A Starlette TestClient deprecation warning for the installed httpx integration is
non-failing in this environment. Dependencies are pinned to the versions used.

## Manual release checks

1. Replace/confirm the provisional organizer adapter and clinically review rules.
2. Run README setup from a fresh clone on a second laptop.
3. Test microphone allow/deny, English/Hindi/Hinglish transcripts and edits.
4. Run tests and metrics; report sample size, misses and limitations honestly.
5. Rehearse ordinary booking and emergency interruption without calling 112.
6. Check real commit history and judge access before 11 AM internal upload target.
7. Submit all required assets by 25 October 2026, 11:30 AM IST.

## Repository layout revision

Generated models now live under models/ with a tracked .gitkeep and matching
MODEL_DIR defaults in training, evaluation, runtime and container configuration.
The API contract is under docs/api-contract.md. Dedicated booking tests share
fixtures through conftest.py/helpers.py. Compose starts one app with a persisted
SQLite volume and a health check. Docker/Compose execution still requires a local
Docker daemon and has not been claimed as run in this environment.
