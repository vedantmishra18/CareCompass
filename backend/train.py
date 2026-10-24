import argparse
import os
import csv
import hashlib
import json
from pathlib import Path
import joblib
import sklearn
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parent.parent


def load_rows(path):
    with Path(path).open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    required = {'case_id', 'group_id', 'user_input', 'care_type', 'urgency'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError('Training CSV needs case_id, group_id, user_input, care_type, urgency.')
    if len({r['case_id'] for r in rows}) != len(rows):
        raise ValueError('Case IDs must be unique.')
    policy = json.loads((ROOT / 'data/taxonomy.json').read_text())
    for row in rows:
        if not row['user_input'].strip() or row['care_type'] not in policy['care_types'] or row['urgency'] not in policy['urgencies']:
            raise ValueError('Empty text or label outside provisional taxonomy.')
    return rows


def pipeline():
    return Pipeline([('text', TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), max_features=40000)),
                     ('label', LogisticRegression(C=4, class_weight='balanced', max_iter=1500, random_state=42))])


def train(path, target):
    rows = load_rows(path)
    groups = [r['group_id'] for r in rows]
    strata = [r['care_type'] + ':' + r['urgency'] for r in rows]
    train_ids, test_ids = next(StratifiedGroupKFold(n_splits=4, shuffle=True, random_state=42).split(rows, strata, groups))
    training = [rows[i] for i in train_ids]
    bundle = {}
    for label in ['care_type', 'urgency']:
        if len({r[label] for r in training}) < 2:
            raise ValueError('Training split needs at least two classes per task.')
        model = pipeline()
        model.fit([r['user_input'] for r in training], [r[label] for r in training])
        bundle[label] = model
    bundle['metadata'] = {'source': str(Path(path).name), 'data_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                          'sklearn_version': sklearn.__version__, 'train_ids': [r['case_id'] for r in training],
                          'test_ids': [rows[i]['case_id'] for i in test_ids], 'training_rows': len(training),
                          'status': 'synthetic_engineering_model_not_clinically_validated'}
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, target)
    return bundle


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', default=ROOT / 'data/demo_train.csv')
    parser.add_argument('--output', default=Path(os.environ.get('MODEL_DIR', ROOT / 'models')) / 'routing.joblib')
    args = parser.parse_args()
    result = train(args.input, args.output)
    print(json.dumps(result['metadata'], indent=2))
