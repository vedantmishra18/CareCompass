import { useEffect, useRef, useState } from "react";
import { request } from "./api.js";
import { labels } from "./copy.js";

export default function useCare() {
  const [lang, setLang] = useState("en");
  const [text, setText] = useState("");
  const [session, setSession] = useState(null);
  const [decision, setDecision] = useState(null);
  const [booking, setBooking] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [consent, setConsent] = useState(false);
  const [located, setLocated] = useState(true);
  const [idempotencyKey, setIdempotencyKey] = useState("");
  useEffect(() => {
    let saved;
    try {
      saved = JSON.parse(
        sessionStorage.getItem("carecompass-session") || "null",
      );
    } catch {
      return;
    }
    if (!saved) return;
    setBusy(true);
    request(`/api/sessions/${saved.session_id}`, { token: saved.token })
      .then((data) => {
        setSession({ ...saved, version: data.version });
        setDecision(data.decision);
        setBooking(data.booking || null);
        setConsent(true);
        setLang(saved.lang || "en");
        setIdempotencyKey(crypto.randomUUID());
      })
      .catch(() => {
        sessionStorage.removeItem("carecompass-session");
        setError("Previous case is unavailable or expired. Start a new case.");
      })
      .finally(() => setBusy(false));
  }, []);
  useEffect(() => {
    try {
      if (session)
        sessionStorage.setItem(
          "carecompass-session",
          JSON.stringify({ ...session, lang }),
        );
      else sessionStorage.removeItem("carecompass-session");
    } catch {
      /* The current tab still works when browser storage is disabled. */
    }
  }, [session, lang]);
  const resultRef = useRef(null);
  const recognitionRef = useRef(null);
  const [listening, setListening] = useState(false);
  const [voiceNotice, setVoiceNotice] = useState("");

  function dictate() {
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Speech) {
      setVoiceNotice(
        "Speech is unavailable in this browser. Please type instead.",
      );
      return;
    }
    if (listening) {
      recognitionRef.current?.stop();
      return;
    }
    if (!consent) {
      setVoiceNotice("Confirm synthetic-data use before using the microphone.");
      return;
    }
    if (
      !window.confirm(
        "Your browser may send audio to its speech service. Use a fictional example only. Continue?",
      )
    )
      return;
    const speech = new Speech();
    recognitionRef.current = speech;
    speech.lang = lang === "en" ? "en-IN" : "hi-IN";
    speech.continuous = false;
    speech.interimResults = false;
    speech.onresult = (event) => {
      setText(event.results[0][0].transcript);
      setVoiceNotice("Review and edit the transcript before continuing.");
    };
    speech.onerror = () => {
      setVoiceNotice("Speech could not be recognised. Please type or retry.");
      setListening(false);
    };
    speech.onend = () => setListening(false);
    setVoiceNotice("Listening to a synthetic example…");
    try {
      speech.start();
      setListening(true);
    } catch {
      setVoiceNotice("Microphone unavailable. Please type instead.");
    }
  }

  useEffect(() => {
    document.documentElement.lang = lang === "hi" ? "hi" : "en";
  }, [lang]);
  const t = labels[lang];
  const emergency = decision?.status === "emergency";
  const question = decision?.question_id;
  const finished = decision && !question;

  async function send(value, answer = true) {
    if (!value.trim() || busy || !consent) return;
    recognitionRef.current?.stop();
    setBusy(true);
    setError("");
    setBooking(null);
    try {
      const current =
        session || (await request("/api/sessions", { method: "POST" }));
      setSession(current);
      const response = await request(
        `/api/sessions/${current.session_id}/assess`,
        {
          method: "POST",
          token: current.token,
          body: {
            user_input: value,
            expected_version: current.version,
            question_id: answer ? question || null : null,
            language: lang,
            location: located ? { lat: 28.545, lng: 77.273 } : null,
          },
        },
      );
      setSession({ ...current, version: response.version });
      setDecision(response);
      setText("");
      setIdempotencyKey(crypto.randomUUID());
      setTimeout(() => resultRef.current?.focus(), 0);
    } catch (e) {
      setError(e.message);
      if (e.status === 503) {
        try {
          const fallback = await request("/assess", {
            method: "POST",
            body: { user_input: value, language: lang },
          });
          if (fallback.red_flags.length)
            setDecision({
              result: fallback,
              status: "emergency",
              facts: {},
              matches: [],
              question_id: null,
              mode: "emergency_policy",
            });
        } catch {
          /* The static emergency reminder remains visible when the API is down. */
        }
      }
    } finally {
      setBusy(false);
    }
  }

  async function reserve(match, slot) {
    if (busy || emergency) return;
    setBusy(true);
    setError("");
    try {
      const response = await request("/api/bookings", {
        method: "POST",
        token: session.token,
        body: {
          session_id: session.session_id,
          decision_version: session.version,
          caregiver_id: match.caregiver_id,
          slot_id: slot.id,
          idempotency_key: idempotencyKey,
        },
      });
      setBooking({ ...response.booking, name: match.name, start: slot.start });
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function reset() {
    if (busy) return;
    setBusy(true);
    setError("");
    try {
      if (session)
        await request(`/api/sessions/${session.session_id}`, {
          method: "DELETE",
          token: session.token,
        });
      setSession(null);
      setDecision(null);
      setBooking(null);
      setText("");
    } catch (e) {
      setError(`Could not delete this case: ${e.message}`);
    } finally {
      setBusy(false);
    }
  }

  return {
    lang,
    setLang,
    text,
    setText,
    session,
    decision,
    booking,
    busy,
    error,
    consent,
    setConsent,
    located,
    setLocated,
    resultRef,
    listening,
    voiceNotice,
    dictate,
    t,
    emergency,
    question,
    finished,
    send,
    reserve,
    reset,
  };
}
