import json
from datetime import datetime, timedelta, timezone
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

PROFILES = json.loads((Path(__file__).resolve().parent.parent / 'data/caregivers.json').read_text())


def distance_km(a, b):
    lat1, lon1, lat2, lon2 = map(radians, [a['lat'], a['lng'], b['lat'], b['lng']])
    v = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * asin(sqrt(min(1, v)))


def rank(care, urgency, facts, location, language, slots, now=None):
    if care == 'emergency_referral' or not care:
        return []
    now = now or datetime.now(timezone.utc)
    deadline = now + timedelta(hours=12 if urgency == 'same_day' else 7 * 24)
    required = 'wound' if care == 'nurse_home_visit' and facts.get('wound', {}).get('state') == 'present' else None
    if care == 'paramedic_home_visit':
        required = next((k for k in ['fever', 'cough', 'vitals'] if facts.get(k, {}).get('state') == 'present'), 'general')
    lang = 'hi' if language in ['hi', 'hinglish'] else 'en'
    matches = []
    for profile in PROFILES:
        if profile['role'] != care or required and required not in profile['skills']:
            continue
        usable = sorted([s for s in slots if s['caregiver_id'] == profile['id']
                         and now < datetime.fromisoformat(s['start']) <= deadline], key=lambda s: s['start'])
        if not usable:
            continue
        km = distance_km(location, profile) if location else None
        if km is not None and care != 'gp_teleconsult' and km > 30:
            continue
        hours = (datetime.fromisoformat(usable[0]['start']) - now).total_seconds() / 3600
        parts = {'skill': 1.0, 'availability': max(0, 1 - hours / (12 if urgency == 'same_day' else 168)),
                 'distance': max(0, 1 - km / 30) if km is not None else None,
                 'language': float(lang in profile['languages']), 'rating': profile.get('rating', 2.5) / 5}
        weights = {'skill': .30, 'availability': .25, 'distance': .20, 'language': .15, 'rating': .10}
        total = sum(weights[k] for k, v in parts.items() if v is not None)
        score = sum(weights[k] * v for k, v in parts.items() if v is not None) / total
        reason = [f"Required role and {required or 'care'} skills", 'slot within requested urgency']
        reason.append(f'{km:.1f} km straight-line' if km is not None else 'distance not assessed')
        reason.append('preferred language available' if lang in profile['languages'] else 'preferred language not listed')
        if language == 'hi':
            reason = ['जरूरी भूमिका और कौशल उपलब्ध', 'तात्कालिकता के अनुसार स्लॉट उपलब्ध',
                      f'{km:.1f} किमी सीधी दूरी' if km is not None else 'दूरी का आकलन नहीं हुआ',
                      'पसंदीदा भाषा उपलब्ध' if lang in profile['languages'] else 'पसंदीदा भाषा सूची में नहीं है']
        elif language == 'hinglish':
            reason = ['Required role aur skills available', 'Urgency ke andar slot available',
                      f'{km:.1f} km seedhi doori' if km is not None else 'Distance assess nahi hua',
                      'Preferred language available' if lang in profile['languages'] else 'Preferred language listed nahi hai']
        matches.append({**profile, 'caregiver_id': profile['id'], 'score': round(score, 3),
                        'distance_km': round(km, 1) if km is not None else None,
                        'reason': '; '.join(reason), 'slots': usable[:3], 'breakdown': parts})
    return sorted(matches, key=lambda m: (-m['score'], m['slots'][0]['start'], m['id']))[:3]
