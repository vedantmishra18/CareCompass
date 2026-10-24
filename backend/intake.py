import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / 'data'
POLICY = json.loads((DATA / 'taxonomy.json').read_text())
QUESTIONS = {
    'safety': {'en': 'Any severe breathing trouble, chest pain, fainting or uncontrolled bleeding?',
               'hi': 'क्या सांस की गंभीर तकलीफ, सीने में दर्द, बेहोशी या न रुकने वाला खून है?',
               'hinglish': 'Kya saans ki serious dikkat, seene mein dard, behoshi ya na rukne wala khoon hai?'},
    'duration': {'en': 'How long has this need or symptom been present?',
                 'hi': 'यह जरूरत या लक्षण कितने समय से है?',
                 'hinglish': 'Yeh zaroorat ya symptom kitne samay se hai?'},
    'need': {'en': 'What help is needed: wound dressing, a home check, a doctor call, or specialist follow-up?',
             'hi': 'क्या मदद चाहिए: पट्टी, घर पर जांच, डॉक्टर से बात या विशेषज्ञ का फॉलो अप?',
             'hinglish': 'Kya help chahiye: patti, home check, doctor call ya specialist follow-up?'},
    'age': {'en': 'What is the patient’s age in years?', 'hi': 'मरीज की उम्र कितने वर्ष है?',
            'hinglish': 'Patient ki age kitne saal hai?'},
}


def language(code, text=''):
    if code != 'auto':
        return code
    return 'hi' if re.search(r'[\u0900-\u097f]', text) else 'en'


def normalise(text):
    text = text.lower().replace('’', "'")
    for word, number in {'एक': '1', 'दो': '2', 'तीन': '3', 'चार': '4', 'पांच': '5', 'साठ': '60'}.items():
        text = re.sub(r'(?<!\w)' + word + r'(?!\w)', number, text)
    return re.sub(r'\s+', ' ', text).strip()


def evidence(text, phrase):
    text, phrase = normalise(text), normalise(phrase)
    pattern = re.escape(phrase)
    if phrase.isascii():
        pattern = r'(?<!\w)' + pattern + r'(?!\w)'
    found = list(re.finditer(pattern, text))
    if not found:
        return None
    value = None
    for hit in found:
        left = re.split(r'[.,;!?]|\b(?:but|lekin|however|and|aur)\b|लेकिन|और', text[:hit.start()])[-1]
        right = re.split(r'[.,;!?]|\b(?:but|lekin|however|and|aur)\b|लेकिन|और', text[hit.end():])[0]
        # Preserve phrases such as "not breathing": negation is part of the danger.
        neg = re.search(r'\b(no|not|without|denies|nahi|nahin)\b|नहीं|नही', left[-35:])
        suffix = re.match(r'^\s*(?:hai\s+)?(?:nahi|nahin|नहीं|नही)(?:\s|$)', right)
        past = re.search(r'last year|years ago|previously|pehle|पिछले साल|पहले', left[-45:] + ' ' + right[:35])
        if past and not re.search(r'now|today|abhi|अब|आज', left[-20:] + right[:25]):
            value = 'unknown'
        else:
            value = 'absent' if neg or suffix else 'present'
    return value


def extract(messages):
    facts = {}
    for index, message in enumerate(messages):
        text = message['content']
        if message['role'] != 'user':
            continue
        for group, phrases in POLICY['symptoms'].items():
            states = [evidence(text, phrase) for phrase in phrases]
            states = [s for s in states if s is not None]
            if states:
                facts[group] = {'state': states[-1], 'turn': index}
    return facts


def answer_state(text):
    text = normalise(text).strip('.! ')
    if text in {'yes', 'haan', 'han', 'ha', 'हाँ', 'हां'}:
        return 'present'
    if text in {'no', 'nahi', 'nahin', 'नहीं', 'नही'}:
        return 'absent'
    return 'unknown'


def reconstruct(history):
    answers = {}
    for i, message in enumerate(history[:-1]):
        if message['role'] != 'assistant' or history[i + 1]['role'] != 'user':
            continue
        for key, versions in QUESTIONS.items():
            if message['content'] in versions.values():
                answers[key] = history[i + 1]['content']
    return answers


def next_question(messages, answers, code):
    text = normalise(' '.join(m['content'] for m in messages if m['role'] == 'user'))
    facts = extract(messages)
    needed = ['safety', 'duration', 'need', 'age']
    if re.search(r'\d+\s*(?:days?|hours?|din|ghante|दिन|घंटे)', text):
        needed.remove('duration')
    if any(facts.get(k, {}).get('state') == 'present' for k in ['wound', 'vitals', 'consult', 'specialist']):
        needed.remove('need')
    if re.search(r'\d+\s*(?:years? old|saal|साल|वर्ष)', text):
        needed.remove('age')
    return next((k for k in needed if k not in answers), None)


def patient_age(messages, answers):
    import re
    for message in reversed(messages):
        if message['role'] != 'user':
            continue
        found = re.search(r'\b(\d{1,3})\s*(?:years? old|saal|साल|वर्ष)', normalise(message['content']), re.I)
        if found:
            return int(found.group(1))
    age = answers.get('age', '').strip()
    return int(age) if age.isdigit() and 0 <= int(age) <= 120 else None
