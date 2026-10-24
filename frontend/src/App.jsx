import React from "react";
import useCare from "./useCare.js";
import Intake from "./Intake.jsx";
import Result from "./Result.jsx";

export default function App() {
  const care = useCare();
  const {
    t,
    lang,
    setLang,
    busy,
    session,
    decision,
    question,
    finished,
    booking,
    error,
    reset,
  } = care;
  return (
    <div className="shell">
      <header className="topbar">
        <a className="wordmark" href="/">
          CareCompass<span>CARE NAVIGATION</span>
        </a>
        <div className="top-actions">
          <span className="demo-badge">{t.demo}</span>
          <label className="sr-only" htmlFor="language">
            Language
          </label>
          <select
            id="language"
            value={lang}
            onChange={(e) => setLang(e.target.value)}
            disabled={busy || !!session}
          >
            <option value="en">English</option>
            <option value="hi">हिन्दी</option>
            <option value="hinglish">Hinglish</option>
          </select>
        </div>
      </header>
      <main>
        <section className="hero">
          <div className="eyebrow">FROM A CARE NEED TO A CLEAR NEXT STEP</div>
          <h1>
            {t.title}
            <span className="accent">.</span>
          </h1>
          <p>{t.sub}</p>
        </section>
        <p className="emergency-reminder">
          For a real emergency in India, call 112. Do not wait for this demo.
          Never place a test call.
        </p>
        <div className="workspace">
          <aside className="guide">
            <span className="eyebrow">YOUR JOURNEY</span>
            {[
              "Tell us the need",
              "Clarify the details",
              care.emergency ? "Get emergency help" : "Choose suitable care",
              "Reserve a demo slot",
            ].map((s, i) => (
              <div
                key={s}
                className={`step ${(i === 0 && !decision) || (i === 1 && question) || (i === 2 && finished && !booking) || (i === 3 && booking) ? "active" : ""}`}
              >
                <span>{String(i + 1).padStart(2, "0")}</span>
                {s}
              </div>
            ))}
            <div className="scope-note">
              <strong>Guidance, not a diagnosis</strong>
              <p>
                Demo policy and synthetic data. For a real health concern, seek
                qualified medical care.
              </p>
            </div>
            <a
              className="quiet-link"
              href="/docs"
              target="_blank"
              rel="noreferrer"
            >
              API documentation ↗
            </a>
          </aside>
          <section className="flow" aria-busy={busy}>
            {error && (
              <div className="error" role="alert">
                {error}
              </div>
            )}
            <Intake {...care} />
            <Result {...care} />
            {session && (
              <button className="text-button" onClick={reset} disabled={busy}>
                {t.reset} · delete this case
              </button>
            )}
          </section>
        </div>
      </main>
      <footer>
        <span>CareCompass / Team Diligence</span>
        <span>Synthetic prototype · care navigation only</span>
      </footer>
    </div>
  );
}
