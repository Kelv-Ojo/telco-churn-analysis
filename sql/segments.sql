-- A cross-sectional churn proportion, not a longitudinal monthly hazard.
WITH grouped AS (
 SELECT Contract AS contract, tenure_band, COUNT(*) AS customers,
        SUM(churn_flag) AS churned,
        SUM(CASE WHEN churn_flag=1 THEN MonthlyCharges ELSE 0 END) AS churned_monthly_charge_total
 FROM customers
 GROUP BY Contract, tenure_band
)
SELECT *, ROUND(100.0*churned/customers,2) AS churn_pct,
       DENSE_RANK() OVER (ORDER BY 1.0*churned/customers DESC) AS churn_rate_rank
FROM grouped
WHERE customers >= 50
ORDER BY churn_rate_rank, customers DESC;
