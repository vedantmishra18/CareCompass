import csv
import pytest
from backend.evaluate import predict
from backend.train import ROOT, train


def test_training_groups_do_not_cross_split(tmp_path):
    bundle = train(ROOT / 'data/demo_train.csv', tmp_path / 'model.joblib')
    with (ROOT / 'data/demo_train.csv').open() as f:
        rows = {r['case_id']: r for r in csv.DictReader(f)}
    train_groups = {rows[i]['group_id'] for i in bundle['metadata']['train_ids']}
    test_groups = {rows[i]['group_id'] for i in bundle['metadata']['test_ids']}
    assert train_groups.isdisjoint(test_groups)
    assert any(rows[i]['urgency'] == 'immediate' for i in bundle['metadata']['test_ids'])


def test_batch_export_fails_without_supplied_safety(tmp_path):
    source = tmp_path / 'cases.csv'
    source.write_text('case_id,user_input\none,fever\n')
    with pytest.raises(ValueError, match='Unresolved'):
        predict(source, tmp_path / 'out.csv')
    assert not (tmp_path / 'out.csv').exists()


def test_batch_preserves_ids_and_exact_column_order(tmp_path):
    source = tmp_path / 'cases.csv'
    source.write_text('case_id,user_input,safety,age\nb,Need wound dressing,no,60\na,cannot breathe,,60\n')
    out = tmp_path / 'predictions.csv'
    assert predict(source, out) == 2
    with out.open() as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == ['case_id', 'care_type', 'urgency']
        assert [r['case_id'] for r in reader] == ['b', 'a']
