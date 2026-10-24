import os
from functools import lru_cache
from pathlib import Path
from backend.intake import POLICY, answer_state, evidence, extract, patient_age


HELP = {
    'en': 'Seek emergency help now. In India call 112, or ask someone nearby to help. Do not wait for a home-care booking.',
    'hi': 'अभी आपातकालीन मदद लें। भारत में 112 पर कॉल करें या पास के व्यक्ति की मदद लें। होम केयर बुकिंग का इंतजार न करें।',
    'hinglish': 'Abhi emergency help lein. India mein 112 call karein ya paas ke kisi vyakti ki help lein. Home-care booking ka wait na karein.',
}


@lru_cache(maxsize=2)
def _load_model(path, modified):
    import joblib
    return joblib.load(path)


def model_suggestion(messages):
    path = Path(os.environ.get('MODEL_DIR', Path(__file__).resolve().parent.parent / 'models')) / 'routing.joblib'
    if not path.is_file():
        return None
    try:
        bundle = _load_model(str(path), path.stat().st_mtime_ns)
        text = ' '.join(m['content'] for m in messages if m['role'] == 'user')
        return {label: str(bundle[label].predict([text])[0]) for label in ['care_type', 'urgency']}
    except Exception:  # Model loading is optional; the explicit policy remains available.
        return None


def red_flags(messages, answers=None):
    flags = set()
    for message in messages:
        if message['role'] != 'user':
            continue
        for name, phrases in POLICY['red_flags'].items():
            if any(evidence(message['content'], p) == 'present' for p in phrases):
                flags.add(name)
    if answer_state((answers or {}).get('safety', '')) == 'present':
        flags.add('reported_warning_sign')
    return sorted(flags)


def review_text(reason, code):
    if code == 'hi':
        return 'जानकारी अधूरी है या अनुरोध इस सीमित वयस्क डेमो के दायरे में नहीं है। योग्य स्वास्थ्यकर्मी से मूल्यांकन लें। यहां बुकिंग उपलब्ध नहीं है।'
    if code == 'hinglish':
        return 'Information incomplete hai ya request is limited adult demo ke scope mein nahi hai. Qualified health professional se assessment lein. Yahan booking available nahi hai.'
    return reason


def route(messages, answers, code):
    facts = extract(messages)
    active = [k for k, v in facts.items() if v['state'] == 'present']
    flags = red_flags(messages, answers)
    if flags:
        return {'care_type': 'emergency_referral', 'urgency': 'immediate',
                'red_flags': flags, 'reasoning': HELP[code]}, 'emergency', facts
    if answer_state(answers.get('safety', '')) != 'absent':
        return {'reasoning': review_text('Assessment incomplete: warning signs remain unclear. Seek qualified human assessment; no booking is offered.', code)}, 'review', facts
    age = patient_age(messages, answers)
    text = ' '.join(m['content'].lower() for m in messages if m['role'] == 'user')
    if age is not None and age < 18 or any(word in text for word in ['pregnan', 'गर्भवती', 'newborn', 'infant', 'शिशु']):
        return {'reasoning': review_text('Children, pregnancy and infant care are outside this demo policy. Seek qualified human assessment; no booking is offered.', code)}, 'review', facts
    if age is None:
        return {'reasoning': review_text('Patient age is unclear. This narrow adult demo requires human assessment rather than a booking.', code)}, 'review', facts
    for symptom, policy in POLICY['routing'].items():
        care, urgency = policy['care'], policy['urgency_floor']
        if symptom in active:
            suggestion = model_suggestion(messages)
            used_model = False
            if suggestion:
                if suggestion['urgency'] == 'immediate':
                    return {'care_type': 'emergency_referral', 'urgency': 'immediate',
                            'red_flags': ['model_urgency_signal'], 'reasoning': HELP[code]}, 'emergency', facts
                if suggestion['care_type'] in policy['allowed_care']:
                    care = suggestion['care_type']
                    used_model = True
                if suggestion['urgency'] == 'same_day':
                    urgency = 'same_day'
            reason = {'en': f'You reported {symptom}. The provisional demo policy routes this need to {care.replace("_", " ")}. No warning signs were reported in the safety answer.',
                      'hi': f'आपकी बताई जरूरत ({symptom}) के लिए डेमो नीति यह सेवा सुझाती है। सुरक्षा प्रश्न में चेतावनी लक्षणों से इनकार किया गया।',
                      'hinglish': f'Aapne {symptom} report kiya. Demo policy ke hisaab se yeh care option hai. Safety answer mein warning signs deny kiye gaye.'}[code]
            if used_model:
                reason += {'en': ' Local classifier selected an option within the demo policy bounds.', 'hi': ' स्थानीय मॉडल ने डेमो नीति की सीमा में यह विकल्प चुना।', 'hinglish': ' Local classifier ne demo policy ki limits ke andar option choose kiya.'}[code]
            return {'care_type': care, 'urgency': urgency, 'red_flags': [], 'reasoning': reason}, 'ready', facts
    return {'reasoning': review_text('This request is outside the supported demo policy. Please seek a qualified care assessment; no booking is offered.', code)}, 'review', facts
