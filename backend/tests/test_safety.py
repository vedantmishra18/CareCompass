import pytest
from backend.triage import red_flags, route


def msg(text):
    return [{'role': 'user', 'content': text}]


@pytest.mark.parametrize('text', ['cannot breathe', 'Papa ko seene mein dard hai',
                                   'सांस नहीं आ रही है', 'not breathing', 'uncontrolled bleeding'])
def test_warning_signs(text):
    result, status, _ = route(msg(text), {}, 'en')
    assert status == 'emergency'
    assert result['urgency'] == 'immediate'


@pytest.mark.parametrize('text', ['no chest pain', 'chest pain nahi hai', 'no unconsciousness',
                                   'chest pain last year', 'last year chest pain'])
def test_negated_or_unmatched(text):
    assert red_flags(msg(text)) == []


def test_negation_does_not_cross_but():
    assert 'severe_breathing' in red_flags(msg('no chest pain but cannot breathe'))


def test_unknown_safety_never_becomes_routine():
    result, status, _ = route(msg('fever'), {'safety': 'not sure'}, 'en')
    assert status == 'review'
    assert result.get('care_type') is None


def test_child_and_pregnancy_requests_do_not_book():
    for text in ['Need wound dressing, 8 years old', 'pregnant and fever']:
        result, status, _ = route(msg(text), {'safety': 'no'}, 'en')
        assert status == 'review'
        assert result.get('care_type') is None


@pytest.mark.parametrize('text', ['no fever and chest pain', 'no fever aur seene mein dard hai', 'बुखार नहीं है और सीने में दर्द है'])
def test_negation_does_not_cross_unrelated_symptom(text):
    assert 'chest_pain' in red_flags(msg(text))


def test_hindi_negated_chest_pain():
    assert red_flags(msg('सीने में दर्द नहीं है')) == []


def test_missing_age_does_not_silently_book():
    result, status, _ = route(msg('fever'), {'safety': 'no'}, 'en')
    assert status == 'review'


def test_corrupt_model_falls_back_to_explicit_policy(tmp_path, monkeypatch):
    from backend.triage import model_suggestion
    (tmp_path / 'routing.joblib').write_bytes(b'not a valid model')
    monkeypatch.setenv('MODEL_DIR', str(tmp_path))
    assert model_suggestion(msg('wound dressing')) is None
    result, status, _ = route(msg('wound dressing, 60 years old'), {'safety': 'no'}, 'en')
    assert status == 'ready'
    assert result['care_type'] == 'nurse_home_visit'


def test_hindi_word_numbers_do_not_repeat_known_duration():
    from backend.intake import next_question
    assert next_question(msg('दो दिन से बुखार है'), {'safety': 'no'}, 'hi') == 'need'


def test_model_choice_is_used_within_policy_bounds(monkeypatch):
    import backend.triage as triage
    monkeypatch.setattr(triage, 'model_suggestion', lambda _: {'care_type': 'gp_teleconsult', 'urgency': 'routine'})
    result, status, _ = triage.route(msg('fever, 60 years old'), {'safety': 'no'}, 'en')
    assert status == 'ready'
    assert result['care_type'] == 'gp_teleconsult'
    assert result['urgency'] == 'same_day'


def test_model_cannot_choose_unqualified_service(monkeypatch):
    import backend.triage as triage
    monkeypatch.setattr(triage, 'model_suggestion', lambda _: {'care_type': 'gp_teleconsult', 'urgency': 'routine'})
    result, status, _ = triage.route(msg('wound dressing, 60 years old'), {'safety': 'no'}, 'en')
    assert result['care_type'] == 'nurse_home_visit'
    assert result['urgency'] == 'same_day'


def test_model_immediate_signal_does_not_enter_booking(monkeypatch):
    import backend.triage as triage
    monkeypatch.setattr(triage, 'model_suggestion', lambda _: {'care_type': 'gp_teleconsult', 'urgency': 'immediate'})
    result, status, _ = triage.route(msg('fever, 60 years old'), {'safety': 'no'}, 'en')
    assert status == 'emergency'
    assert result['red_flags'] == ['model_urgency_signal']
