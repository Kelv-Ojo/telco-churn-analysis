# Does tenure mix explain the contract churn gap?

## Method

Compare the observed contract churn proportions with a direct standardisation to the pooled tenure distribution of all 7,043 sample customers. Use four bands: 0–12, 13–24, 25–48 and 49+ months. For each contract, multiply its within-band churn proportions by the same pooled band weights, then sum. All 12 contract/band cells contain at least 50 customers. No rows are dropped for missing TotalCharges.

| Contract | Customers | Observed churn | Standardised churn |
|---|---:|---:|---:|
| Month-to-month | 3,875 | 42.71% | 37.15% |
| One year | 1,473 | 11.27% | 10.95% |
| Two year | 1,695 | 2.83% | 1.55% |

The month-to-month versus two-year gap changes from **39.88 percentage points** to **35.59 percentage points** under the common tenure mix. The gap remains, but its size is sensitive to customer mix. This is a descriptive sensitivity comparison, not the causal effect of switching contracts or an estimate of preventable churn.

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
