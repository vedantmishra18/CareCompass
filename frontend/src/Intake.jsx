import React from "react";
export default function Intake(care) {
  const {
    decision,
    t,
    consent,
    setConsent,
    located,
    setLocated,
    text,
    setText,
    send,
    busy,
    voiceNotice,
    dictate,
    listening,
  } = care;
  return (
    <>
      {!decision && (
        <section className="panel intake">
          <span className="eyebrow">01 / INTAKE</span>
          <h2>{t.input}</h2>
          <p className="muted">
            Use a fictional example. Do not enter real names, records or health
            information.
          </p>
          <label className="consent">
            <input
              type="checkbox"
              checked={consent}
              onChange={(e) => setConsent(e.target.checked)}
            />
            I am using synthetic information only
          </label>
          <label className="location-choice">
            <input
              type="checkbox"
              checked={located}
              onChange={(e) => setLocated(e.target.checked)}
            />
            Use demo location: IIIT Delhi area
          </label>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(text);
            }}
          >
            <label className="sr-only" htmlFor="need">
              {t.input}
            </label>
            <textarea
              id="need"
              value={text}
              onChange={(e) => setText(e.target.value)}
              maxLength={2000}
              placeholder="Papa ko do din se bukhar hai aur khansi bhi…"
              required
            />
            <p className="voice-note" role="status">
              {voiceNotice ||
                "Voice is optional. Always confirm the transcript."}
            </p>
            <div className="form-actions">
              <button
                type="button"
                className="secondary"
                disabled={busy || !consent}
                onClick={dictate}
              >
                {listening ? "Stop recording" : "Use voice"}
              </button>
              <button disabled={busy || !consent || !text.trim()}>
                {busy ? "Working…" : t.start}
                <span>→</span>
              </button>
            </div>
          </form>
          <div className="examples">
            <span>Try a synthetic case</span>
            {[
              "Need wound dressing for 2 days, 60 years old",
              "Papa ko do din se bukhar hai aur khansi bhi",
              "Cannot breathe",
            ].map((s) => (
              <button className="chip" key={s} onClick={() => setText(s)}>
                {s}
              </button>
            ))}
          </div>
        </section>
      )}
    </>
  );
}
