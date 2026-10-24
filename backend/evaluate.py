import argparse
import os
import csv
import hashlib
import json
from pathlib import Path
import joblib
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from backend.intake import language
from backend.train import ROOT, load_rows
from backend.triage import red_flags, route


def metrics(data_path, model_path):
    rows = load_rows(data_path)
    model = joblib.load(model_path)
    sha = hashlib.sha256(Path(data_path).read_bytes()).hexdigest()
    if sha != model['metadata']['data_sha256']:
        raise ValueError('Data differs from model split. Retrain or evaluate a separately labelled external set.')
    ids = set(model['metadata']['test_ids'])
    test = [r for r in rows if r['case_id'] in ids]
    report = {'scope': 'held-out synthetic engineering fixtures; not clinical validation', 'n': len(test)}
    for label in ['care_type', 'urgency']:
        true = [r[label] for r in test]
        pred = list(model[label].predict([r['user_input'] for r in test]))
        labels = sorted({r[label] for r in rows})
        report[label] = {'macro_f1': f1_score(true, pred, labels=labels, average='macro', zero_division=0),
                         'labels': labels, 'confusion_matrix': confusion_matrix(true, pred, labels=labels).tolist(),
                         'per_class': classification_report(true, pred, labels=labels, output_dict=True, zero_division=0)}
    outcomes = []
    for row in test:
        messages = [{'role': 'user', 'content': row['user_input']}]
        answer = {'safety': row['safety']} if row.get('safety') else {}
        if row.get('age'):
            answer['age'] = row['age']
        decision, status, _ = route(messages, answer, language('auto', row['user_input']))
        outcomes.append((row, decision, status))
    emergencies = [r for r in test if r['urgency'] == 'immediate']
    caught = sum(bool(red_flags([{'role': 'user', 'content': r['user_input']}])) for r in emergencies)
    report['deployed_policy'] = {'emergency_cases': len(emergencies), 'caught': caught,
                                  'misses': len(emergencies) - caught,
                                  'emergency_recall': caught / len(emergencies) if emergencies else None,
                                  'abstentions': sum(s == 'review' for _, _, s in outcomes),
                                  'care_type_macro_f1': f1_score([r['care_type'] for r, _, _ in outcomes], [d.get('care_type') or '__abstain__' for _, d, _ in outcomes], labels=sorted({r['care_type'] for r in rows}), average='macro', zero_division=0),
                                  'urgency_macro_f1': f1_score([r['urgency'] for r, _, _ in outcomes], [d.get('urgency') or '__abstain__' for _, d, _ in outcomes], labels=sorted({r['urgency'] for r in rows}), average='macro', zero_division=0)}
    return report


def predict(input_path, output_path, allow_abstain=False):
    with Path(input_path).open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if not rows or not {'case_id', 'user_input'}.issubset(rows[0]):
        raise ValueError('Prediction input requires case_id and user_input. Optional safety must contain a supplied answer.')
    if len({r['case_id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate case IDs.')
    results = []
    for row in rows:
        history = json.loads(row.get('conversation_history') or '[]')
        history.append({'role': 'user', 'content': row['user_input']})
        from backend.intake import reconstruct
        answers = reconstruct(history)
        if row.get('safety'):
            answers['safety'] = row['safety']
        if row.get('age'):
            answers['age'] = row['age']
        result, status, _ = route(history, answers, language(row.get('language') or 'auto', row['user_input']))
        if status == 'review' and not allow_abstain:
            raise ValueError(f"Unresolved case {row['case_id']}: missing/unsupported evidence. Confirm official batch policy; no safety answer was invented.")
        results.append({'case_id': row['case_id'], 'care_type': result.get('care_type', ''), 'urgency': result.get('urgency', '')})
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['case_id', 'care_type', 'urgency'])
        writer.writeheader()
        writer.writerows(results)
    return len(results)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Provisional CSV adapter; adapt columns and batch policy to released instructions.')
    parser.add_argument('command', choices=['metrics', 'predict'])
    parser.add_argument('--input', default=ROOT / 'data/demo_train.csv')
    parser.add_argument('--model', default=Path(os.environ.get('MODEL_DIR', ROOT / 'models')) / 'routing.joblib')
    parser.add_argument('--output', default=ROOT / 'outputs/predictions.csv')
    parser.add_argument('--allow-abstain', action='store_true')
    args = parser.parse_args()
    if args.command == 'metrics':
        report = metrics(args.input, args.model)
        output = Path(args.output).with_suffix('.json')
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    else:
        print(f'Wrote {predict(args.input, args.output, args.allow_abstain)} rows. CSV schema is provisional.')
