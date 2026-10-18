# Telco churn: findings and retention hypotheses

- **26.5%** of the 7,043 sample customers are labelled churned (1,869).
- Month-to-month customers have **42.7%** churn compared with **2.8%** for two-year contracts.
- The highest-rate eligible segment is **Month-to-month, 0–12 months**: **51.4%**, from 1,994 customers.

## Suggested action

Investigate onboarding and service friction for newer month-to-month customers. Design a randomized retention pilot before rolling out incentives. Measure incremental retained customers and contribution margin net of offer cost. Contract length is associated with churn here; these comparisons do not prove that moving customers to longer contracts will reduce churn.

## Data quality and definitions

11 blank TotalCharges values become missing numeric values and remain missing; the customers stay in churn denominators. All those records have zero tenure: True. Customer IDs are checked for uniqueness, then omitted from derived data. Groups smaller than 50 are excluded from segment comparisons. Contract charts show illustrative 95% Wilson binomial intervals; this sample is not a probability sample of a current telecom population.

## Limits

This is the IBM Telco educational sample, not a live client engagement. No acquisition date, churn date, margin or treatment information is available. The churn proportion is cross-sectional, not a monthly churn hazard. Sums of charges for already-churned customers describe sample exposure, not forecast revenue loss or recoverable revenue. Segment rankings are descriptive; multiple comparisons and confounding limit inference. No predictive accuracy or commercial impact is claimed.

Validation: unique customer IDs; valid outcomes; nonnegative charges; SQL customer and churn totals reconcile to pandas; highest-rate SQL segment independently checked.
