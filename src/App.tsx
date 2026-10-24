
import { useState } from 'react'
import './App.css'

type Language = 'English' | 'हिन्दी' | 'Hinglish'

function App() {
  const [language, setLanguage] = useState<Language>('English')
  const [request, setRequest] = useState('')
  const [message, setMessage] = useState('')

  const copy = {
    English: {
      tagline: 'CARE, MADE SIMPLER',
      heading: 'Find the right care,',
      highlight: 'with confidence.',
      description:
        'Tell us what kind of support you are looking for. We will help you explore the next appropriate care step.',
      label: 'How can we help you today?',
      placeholder:
        'Describe your concern or the kind of care you need...',
      privacy: 'Please use fictional details for this demo.',
      button: 'Continue',
      voice: 'Voice input',
      note: 'Care navigation, not a medical diagnosis.',
      required: 'Please describe what kind of care you need.',
    },
    'हिन्दी': {
      tagline: 'देखभाल, अब आसान',
      heading: 'सही देखभाल चुनें,',
      highlight: 'आत्मविश्वास के साथ।',
      description:
        'बताइए कि आपको किस तरह की सहायता चाहिए। हम आपको देखभाल के अगले उचित कदम को समझने में मदद करेंगे।',
      label: 'आज हम आपकी क्या मदद कर सकते हैं?',
      placeholder: 'अपनी समस्या या ज़रूरत यहाँ लिखें...',
      privacy: 'इस डेमो में काल्पनिक जानकारी का उपयोग करें।',
      button: 'आगे बढ़ें',
      voice: 'आवाज़ से लिखें',
      note: 'यह देखभाल के विकल्प समझाता है, बीमारी का निदान नहीं करता।',
      required: 'कृपया अपनी ज़रूरत के बारे में लिखें।',
    },
    Hinglish: {
      tagline: 'CARE, AB AASAN',
      heading: 'Sahi care chunein,',
      highlight: 'confidence ke saath.',
      description:
        'Batayein aapko kis tarah ki help chahiye. Hum aapko agla suitable care step samajhne mein help karenge.',
      label: 'Aaj hum aapki kya help kar sakte hain?',
      placeholder: 'Apni concern ya care ki zaroorat yahan likhein...',
      privacy: 'Demo ke liye fictional details use karein.',
      button: 'Continue karein',
      voice: 'Voice input',
      note: 'Care navigation hai, medical diagnosis nahi.',
      required: 'Please apni care ki zaroorat likhein.',
    },
  }[language]

  function handleContinue() {
    if (!request.trim()) {
      setMessage(copy.required)
      return
    }

    setMessage(
      'Your request has been captured in this demo. Backend assessment is not connected yet.',
    )
  }

  return (
    <main className="care-app">
      <header className="topbar">
        <a className="brand" href="#" aria-label="CareCompass home">
          <span className="brand-mark">C</span>
          <span>
            Care<span className="brand-accent">Compass</span>
            <small>YOUR GUIDE TO THE NEXT STEP</small>
          </span>
        </a>

        <div className="language-control">
          <label htmlFor="language">Language</label>
          <select
            id="language"
            value={language}
            onChange={(event) => {
              setLanguage(event.target.value as Language)
              setMessage('')
            }}
          >
            <option value="English">English</option>
            <option value="हिन्दी">हिन्दी</option>
            <option value="Hinglish">Hinglish</option>
          </select>
        </div>
      </header>

      <section className="hero-layout">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="status-dot" />
            {copy.tagline}
          </div>

          <h1>
            {copy.heading}
            <br />
            <span>{copy.highlight}</span>
          </h1>

          <p className="hero-description">{copy.description}</p>

          <div className="trust-note">
            <span aria-hidden="true">✳</span>
            Thoughtful guidance. Clear next steps. Human-centred care.
          </div>
        </div>

        <section className="intake-card" aria-labelledby="intake-heading">
          <div className="card-topline">
            <span className="step-label">YOUR FIRST STEP</span>
            <span className="step-count">01 / 03</span>
          </div>

          <div className="card-icon" aria-hidden="true">
            <span>✳</span>
          </div>

          <h2 id="intake-heading">{copy.label}</h2>
          <p className="card-description">
            Share only what is relevant. You can edit your message before continuing.
          </p>

          <label className="request-label" htmlFor="care-request">
            Your message
          </label>

          <textarea
            id="care-request"
            value={request}
            onChange={(event) => {
              setRequest(event.target.value)
              setMessage('')
            }}
            placeholder={copy.placeholder}
            rows={5}
            maxLength={1200}
          />

          <div className="input-footer">
            <span>{copy.privacy}</span>
            <span>{request.length}/1200</span>
          </div>

          <div className="voice-row">
            <button
              className="voice-button"
              type="button"
              onClick={() =>
                setMessage(
                  'Voice capture will be added in a later step. You can type your message for now.',
                )
              }
            >
              <span aria-hidden="true">🎙</span>
              {copy.voice}
            </button>
            <span className="voice-hint">Text input is available</span>
          </div>

          <button
            className="continue-button"
            type="button"
            onClick={handleContinue}
          >
            {copy.button}
            <span aria-hidden="true">→</span>
          </button>

          {message && (
            <p className="feedback-message" role="status">
              {message}
            </p>
          )}

          <p className="safety-note">
            <span aria-hidden="true">ⓘ</span>
            {copy.note}
          </p>
        </section>
      </section>

      <footer className="page-footer">
        <span>CareCompass</span>
        <span>Designed for clearer care navigation</span>
        <span>Prototype · Synthetic demo only</span>
      </footer>
    </main>
  )
}

export default App
