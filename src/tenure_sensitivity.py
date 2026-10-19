"""Descriptive direct standardisation of contract churn by customer tenure.

Run from the repository root: python src/tenure_sensitivity.py
Uses the original CSV, preserving every customer in the denominators.
"""
from pathlib import Path
import csv
import hashlib
import json
import math
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
BANDS = ['0–12 months', '13–24 months', '25–48 months', '49+ months']


def main():
    source = ROOT / 'data/WA_Fn-UseC_-Telco-Customer-Churn.csv'
    expected = json.loads((ROOT / 'data/manifest.json').read_text())[source.name]
    assert hashlib.sha256(source.read_bytes()).hexdigest() == expected, 'Source changed'
    with source.open(newline='', encoding='utf-8-sig') as stream:
        records = list(csv.DictReader(stream))
    assert len({r['customerID'] for r in records}) == len(records)
    counts, churned = {}, {}
    for r in records:
        tenure = int(r['tenure'])
        assert tenure >= 0 and r['Churn'] in {'Yes', 'No'}
        band = BANDS[0 if tenure <= 12 else 1 if tenure <= 24 else 2 if tenure <= 48 else 3]
        key = r['Contract'], band
        counts[key] = counts.get(key, 0) + 1
        churned[key] = churned.get(key, 0) + int(r['Churn'] == 'Yes')
    contracts = sorted({key[0] for key in counts})
    # Every group is observed. No absent cell is imputed as zero churn.
    assert all(counts.get((c, b), 0) >= 50 for c in contracts for b in BANDS)
    totals = {b: sum(counts[c, b] for c in contracts) for b in BANDS}
    weights = {b: totals[b] / len(records) for b in BANDS}
    assert math.isclose(sum(weights.values()), 1)
    detail, summary = [], []
    for c in contracts:
        n = sum(counts[c, b] for b in BANDS)
        k = sum(churned[c, b] for b in BANDS)
        adjusted = 0
        for b in BANDS:
            count, events = counts[c, b], churned[c, b]
            contribution = weights[b] * events / count
            adjusted += contribution
            detail.append({'contract': c, 'tenure_band': b, 'customers': count,
                'churned': events, 'within_band_churn_pct': 100 * events / count,
                'pooled_weight': weights[b], 'weighted_contribution_pct': 100 * contribution})
        summary.append({'contract': c, 'customers': n, 'churned': k,
            'observed_churn_pct': 100 * k / n, 'standardised_churn_pct': 100 * adjusted})
    # Independent SQL aggregation starts from the original rows, not the Python groups.
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE TABLE customers(contract TEXT, tenure INTEGER, churned INTEGER)')
        db.executemany('INSERT INTO customers VALUES (?, ?, ?)',
            [(r['Contract'], int(r['tenure']), int(r['Churn'] == 'Yes')) for r in records])
        sql = db.execute('''WITH labelled AS (
          SELECT contract, churned, CASE WHEN tenure<=12 THEN 0 WHEN tenure<=24 THEN 1
            WHEN tenure<=48 THEN 2 ELSE 3 END AS band FROM customers
        ), pooled AS (SELECT band, COUNT(*)*1.0/(SELECT COUNT(*) FROM customers) AS weight
          FROM labelled GROUP BY band), grouped AS (
          SELECT contract, band, COUNT(*) AS n, SUM(churned) AS k
          FROM labelled GROUP BY contract, band)
        SELECT contract, SUM(n), SUM(k), 100.0*SUM(k)/SUM(n),
          100.0*SUM(weight*k/n) FROM grouped JOIN pooled USING(band)
        GROUP BY contract ORDER BY contract''').fetchall()
    for actual, check in zip(summary, sql):
        assert actual['contract'] == check[0]
        assert (actual['customers'], actual['churned']) == check[1:3]
        assert math.isclose(actual['standardised_churn_pct'], check[4], abs_tol=1e-10)
    assert sum(r['customers'] for r in summary) == len(records) == 7043
    assert sum(r['churned'] for r in summary) == 1869
    out = ROOT / 'reports'
    out.mkdir(exist_ok=True)
    for name, rows in [('tenure_standardisation_detail.csv', detail),
                       ('tenure_standardisation.csv', summary)]:
        with (out / name).open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    rates = {r['contract']: r for r in summary}
    observed_gap = rates['Month-to-month']['observed_churn_pct'] - rates['Two year']['observed_churn_pct']
    adjusted_gap = rates['Month-to-month']['standardised_churn_pct'] - rates['Two year']['standardised_churn_pct']
    report = f'''# Does tenure mix explain the contract churn gap?

## Method

Compare the observed contract churn proportions with a direct standardisation to the pooled tenure distribution of all 7,043 sample customers. Use four bands: 0–12, 13–24, 25–48 and 49+ months. For each contract, multiply its within-band churn proportions by the same pooled band weights, then sum. All 12 contract/band cells contain at least 50 customers. No rows are dropped for missing TotalCharges.

| Contract | Customers | Observed churn | Standardised churn |
|---|---:|---:|---:|
'''
    for r in summary:
        report += f"| {r['contract']} | {r['customers']:,} | {r['observed_churn_pct']:.2f}% | {r['standardised_churn_pct']:.2f}% |\n"
    report += f'''
The month-to-month versus two-year gap changes from **{observed_gap:.2f} percentage points** to **{adjusted_gap:.2f} percentage points** under the common tenure mix. The gap remains, but its size is sensitive to customer mix. This is a descriptive sensitivity comparison, not the causal effect of switching contracts or an estimate of preventable churn.

## Limitations and next step

Broad tenure bands leave residual differences within bands, and other customer characteristics remain uncontrolled. Observed tenure may itself reflect retention, contract choice and selection: standardising by it does not establish a valid causal adjustment. No uncertainty interval for the standardised contrast is claimed. The educational sample has no churn dates, acquisition cohorts or intervention outcomes.

Investigate onboarding and service differences within comparable tenure groups, then test an intervention with a control group and a pre-defined follow-up period before claiming an incremental retention effect.

## Reproduce and verify

Run `python src/tenure_sensitivity.py`. Only the Python standard library is required. The script verifies the source fingerprint, customer uniqueness, outcome values, coverage of every cell, pooled weights, total customers and churn events, and independently reproduces the standardised results with SQL over the original records. Detail is in [tenure_standardisation_detail.csv](tenure_standardisation_detail.csv).

## Explain this in an interview

- Why use a common tenure distribution? It removes differences in these four band proportions from this descriptive comparison.
- Why is it not causal? Contract selection, survival, within-band differences and other confounders remain.
- What would you do next? Obtain longitudinal data and evaluate an intervention rather than infer its effect from this snapshot.

Source: the repository's fingerprinted IBM Telco educational sample. See the main README for provenance and rights.
'''
    (out / 'tenure_sensitivity.md').write_text(report)
    print(json.dumps({'observed_gap_pp': observed_gap, 'standardised_gap_pp': adjusted_gap,
                      'contracts': summary, 'pooled_weights': weights}, indent=2))


if __name__ == '__main__':
    main()
