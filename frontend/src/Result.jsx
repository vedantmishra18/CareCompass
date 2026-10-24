import React from "react";
import { careName, time } from "./copy.js";
export default function Result(care) {
  const {
    lang,
    decision,
    resultRef,
    question,
    t,
    busy,
    send,
    text,
    setText,
    emergency,
    finished,
    booking,
    reserve,
  } = care;
  return (
    <>
      {decision && (
        <div
          ref={resultRef}
          tabIndex={-1}
          className="result"
          aria-live="polite"
        >
          {question && (
            <section className="panel">
              <span className="eyebrow">02 / CLARIFY</span>
              <h2>{decision.result.follow_up_question}</h2>
              <p className="muted">
                A missing detail helps determine the next step. Answer only for
                this synthetic case.
              </p>
              {question === "safety" ? (
                <div className="answers">
                  {[
                    [t.yes, "yes"],
                    [t.no, "no"],
                    [t.unsure, "not sure"],
                  ].map(([label, value]) => (
                    <button
                      key={value}
                      disabled={busy}
                      onClick={() => send(value)}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              ) : (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    send(text);
                  }}
                >
                  <label className="sr-only" htmlFor="answer">
                    Your answer
                  </label>
                  <input
                    id="answer"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    maxLength={2000}
                    required
                    autoFocus
                  />
                  <button disabled={busy || !text.trim()}>{t.next} →</button>
                </form>
              )}
            </section>
          )}
          {emergency && (
            <section className="panel emergency" role="alert">
              <span className="eyebrow">IMMEDIATE / EMERGENCY PATH</span>
              <h2>{t.warning}</h2>
              <p>{decision.result.reasoning}</p>
              <strong>No caregiver matching or booking is available.</strong>
              <a
                className="call"
                href="tel:112"
                onClick={(e) => {
                  if (
                    !window.confirm(
                      "This places a real emergency call. Do not call during a demo. Continue only for a real emergency.",
                    )
                  )
                    e.preventDefault();
                }}
              >
                Call 112
              </a>
              <p className="muted">
                Do not place a test call. This app does not dispatch assistance.
              </p>
            </section>
          )}
          {finished && !emergency && (
            <>
              <section className="panel recommendation">
                <span className="eyebrow">03 / CARE RECOMMENDATION</span>
                <div className="result-heading">
                  <h2>
                    {careName(decision.result.care_type, lang) || t.review}
                  </h2>
                  {decision.result.urgency && (
                    <span className="urgency">
                      {decision.result.urgency.replace("_", " ")}
                    </span>
                  )}
                </div>
                <p>{decision.result.reasoning}</p>
                <span className="policy-label">
                  {decision.mode.replaceAll("_", " ")} · not clinically
                  validated
                </span>
              </section>
              {decision.status === "ready" && !booking && (
                <section className="matches">
                  <h2>{t.match}</h2>
                  <p className="muted">
                    Synthetic profiles. Times shown in IST. Distance is
                    straight-line, not travel time.
                  </p>
                  {!decision.matches.length && (
                    <div className="panel">
                      No eligible caregiver has an available slot. Do not delay
                      appropriate care while waiting for this demo.
                    </div>
                  )}
                  {decision.matches.map((m) => (
                    <article className="panel caregiver" key={m.id}>
                      <div className="caregiver-head">
                        <div className="avatar">
                          {m.name
                            .split(" ")
                            .map((n) => n[0])
                            .join("")}
                        </div>
                        <div>
                          <h3>{m.name}</h3>
                          <span>{careName(m.role, lang)}</span>
                        </div>
                        <div className="rating">★ {m.rating}</div>
                      </div>
                      <p>{m.reason}</p>
                      <div className="profile-tags">
                        <span>
                          {m.languages
                            .map((l) => (l === "hi" ? "Hindi" : "English"))
                            .join(" / ")}
                        </span>
                        <span>Match score {m.score.toFixed(2)}</span>
                      </div>
                      <label htmlFor={`slot-${m.id}`} className="sr-only">
                        Slot for {m.name}
                      </label>
                      <select id={`slot-${m.id}`} defaultValue={m.slots[0].id}>
                        {m.slots.map((s) => (
                          <option key={s.id} value={s.id}>
                            {time(s.start)} IST
                          </option>
                        ))}
                      </select>
                      <button
                        disabled={busy}
                        onClick={() =>
                          reserve(
                            m,
                            m.slots.find(
                              (s) =>
                                s.id ===
                                document.getElementById(`slot-${m.id}`).value,
                            ),
                          )
                        }
                      >
                        {t.confirm} →
                      </button>
                    </article>
                  ))}
                </section>
              )}
              {booking && (
                <section className="panel confirmed">
                  <span className="eyebrow">04 / DEMO RESERVATION SAVED</span>
                  <h2>You have a next step</h2>
                  <p>
                    {booking.name} · {time(booking.start)} IST
                  </p>
                  <code>{booking.id}</code>
                  <p>
                    This is a synthetic reservation. No real provider has been
                    contacted.
                  </p>
                </section>
              )}
              <section className="panel update">
                <h3>{t.update}</h3>
                <p className="muted">
                  A new warning sign will stop this booking pathway. Existing
                  saved demo reservations are not real appointments.
                </p>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    send(text, false);
                  }}
                >
                  <label className="sr-only" htmlFor="update">
                    New information
                  </label>
                  <input
                    id="update"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    maxLength={2000}
                    placeholder="For example: now cannot breathe"
                    required
                  />
                  <button disabled={busy || !text.trim()}>{t.next} →</button>
                </form>
              </section>
            </>
          )}
          <details className="evidence">
            <summary>What we understood</summary>
            {Object.entries(decision.facts).length ? (
              <ul>
                {Object.entries(decision.facts).map(([k, v]) => (
                  <li key={k}>
                    {k}: {v.state} (turn {v.turn + 1})
                  </li>
                ))}
              </ul>
            ) : (
              <p>No supported symptom facts extracted yet.</p>
            )}
            <p>
              Safety policy checks all supplied turns. The emergency state stays
              active for this case.
            </p>
          </details>
        </div>
      )}
    </>
  );
}
