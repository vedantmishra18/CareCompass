# CareCompass API contract

Status: **provisional**, based on the indicative brief. The released organizer
schema, taxonomy, labels and CSV rules were not provided. They override this file.
Run the API and open `/docs` or `/openapi.json` for the exact implemented schema.
Interactive `/docs` loads Swagger UI assets from a CDN; `/openapi.json` is local.

## Public assessment

`POST /assess` accepts:

| Field | Type | Implemented meaning |
|---|---|---|
| user_input | string, 1-2000 characters | Current synthetic request/answer; whitespace trimmed |
| language | auto / en / hi / hinglish | Defaults to auto; explicit Hinglish selection recommended |
| location | {lat,lng} or null | Valid latitude/longitude; missing distance is not invented |
| conversation_history | array, maximum 16 | Prior {role: user/assistant, content: string} messages |

The response contains exactly these seven fields:

| Field | Type | Meaning |
|---|---|---|
| follow_up_question | string or null | Next relevant question; no final care while asking |
| care_type | allowed label or null | Provisional care destination |
| urgency | routine / same_day / immediate / null | Policy-constrained urgency |
| red_flags | string array | Supported emergency rule IDs or conservative model signal |
| reasoning | string | Facts/policy explanation; no diagnosis or prescription |
| matched_caregivers | array | caregiver_id, score [0,1], reason |

Provisional care labels: `paramedic_home_visit`, `nurse_home_visit`,
`gp_teleconsult`, `specialist_consult`, `emergency_referral`.

Question state: care_type/urgency null and no matches. Emergency state: immediate,
emergency_referral and no matches. Unsupported/unclear requests: no invented care
label, no booking and an explicit human-review explanation. The organizer must
approve that abstention encoding before scoring. Never coerce it into routine care.

Example synthetic request:

```json
{"user_input":"cannot breathe","language":"en","location":null,"conversation_history":[]}
```

This supported demo phrase produces an emergency response with no matches.
Clinical review is still needed; the phrase list is not an exhaustive protocol.

For a stateless conversation, append the exact returned question as an assistant
message, then submit the user's answer. Do not invent negative answers when the
batch test lacks follow-up information. `evaluate.py` uses the same routing policy
but its one-shot input/output mapping must follow the released CSV instructions.

## Separate demo session API

These endpoints return demo metadata and are not additions to the public contract.

| Method/path | Purpose |
|---|---|
| POST /api/sessions | Create synthetic encounter; returns session_id/token/version |
| POST /api/sessions/{sid}/assess | user_input, expected_version, optional question_id/language/location |
| GET /api/sessions/{sid} | Current decision/version and saved mock booking |
| DELETE /api/sessions/{sid} | Delete synthetic case and release its demo reservations |
| POST /api/bookings | Reserve offered caregiver/slot against latest decision version |
| GET /api/bookings/{bid}?session_id=... | Read an owned mock reservation |
| GET /health | Local readiness and provisional-contract marker |

Session and booking routes require `Authorization: Bearer <token>`, except new
session creation. Booking body: session_id, decision_version, caregiver_id,
slot_id, idempotency_key. No real provider receives a request. Repeated identical
booking submissions have one effect; reusing a key for another reservation fails.
An emergency, stale decision, unsuitable slot or access violation blocks booking.

Errors: 401 missing token; 404 unknown/not-owned resource; 409 stale/conflicting
state; 410 expired session; 413 oversized request; 422 invalid input; 429 rate
limit; 503 unavailable demo storage. Public emergency handling skips matching
storage. No response contains raw stack traces or medical treatment advice.

## Organizer adapter checklist

1. Replace/confirm enums in schemas.py and taxonomy.json, and response nullability.
2. Confirm emergency/review outputs, follow-up limits and batch scoring behaviour.
3. Adapt evaluate.predict columns, identifiers and ordering to the official sample.
4. Use permitted doctor-labelled data; group duplicates/translations before split.
5. Review clinical rules, modifiers and unsupported-risk groups with mentors.
6. Confirm caregiver skill, availability, location and language semantics.
7. Train/save/load models consistently under models/ (or the same MODEL_DIR).
8. Keep raw-classifier results separate from deployed-policy results and limitations.
