"""Reproducible descriptive segmentation of the IBM Telco sample dataset."""
from pathlib import Path
import json
import sqlite3
import math
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]

def wilson(k,n):
    z=1.96;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return center-half,center+half

def main():
    out=ROOT/'reports';out.mkdir(exist_ok=True)
    df=pd.read_csv(ROOT/'data/WA_Fn-UseC_-Telco-Customer-Churn.csv')
    assert df.customerID.is_unique and not df.customerID.isna().any()
    assert set(df.Churn)=={'Yes','No'}
    raw=df.TotalCharges.astype(str).str.strip()
    df['TotalCharges']=pd.to_numeric(raw,errors='coerce')
    invalid=raw.ne('') & df.TotalCharges.isna()
    assert not invalid.any(), 'Unexpected nonnumeric TotalCharges'
    assert df.tenure.between(0,1000).all() and df.MonthlyCharges.ge(0).all()
    df['churn_flag']=df.Churn.eq('Yes').astype(int)
    df['tenure_band']=pd.cut(df.tenure,[-1,12,24,48,float('inf')],labels=['0–12 months','13–24 months','25–48 months','49+ months']).astype(str)
    # Customer identifiers are unnecessary for this aggregate study.
    clean=df.drop(columns='customerID')
    clean.to_csv(out/'customers_clean.csv',index=False)
    with sqlite3.connect(':memory:') as db:
        clean.to_sql('customers',db,index=False)
        segments=pd.read_sql_query((ROOT/'sql/segments.sql').read_text(),db)
    segments.to_csv(out/'contract_tenure_segments.csv',index=False)
    contract=df.groupby('Contract').agg(customers=('churn_flag','size'),churned=('churn_flag','sum'))
    contract['churn_pct']=100*contract.churned/contract.customers
    assert contract.customers.sum()==len(df) and contract.churned.sum()==df.churn_flag.sum()
    # Check one SQL group independently with pandas.
    first=segments.iloc[0]
    check=df[df.Contract.eq(first.contract)&df.tenure_band.eq(first.tenure_band)]
    assert len(check)==first.customers and check.churn_flag.sum()==first.churned
    intervals=[wilson(int(r.churned),int(r.customers)) for r in contract.itertuples()]
    contract['ci_low_pct']=[100*x[0] for x in intervals]
    contract['ci_high_pct']=[100*x[1] for x in intervals]
    contract.to_csv(out/'contract_summary.csv')
    plt.rcParams.update({'font.family':'DejaVu Sans','axes.spines.top':False,'axes.spines.right':False})
    fig,ax=plt.subplots(figsize=(8,5))
    ax.bar(contract.index,contract.churn_pct,color=['#D87A36','#176B87','#57A69B'])
    ax.errorbar(contract.index,contract.churn_pct,
                yerr=[contract.churn_pct-contract.ci_low_pct,contract.ci_high_pct-contract.churn_pct],fmt='none',color='#333',capsize=5)
    ax.set(title='Churn proportion by contract type',ylabel='Churned customers (%)',xlabel='Contract')
    for i,r in enumerate(contract.itertuples()):
        ax.text(i,r.ci_high_pct+1,f'{r.churn_pct:.1f}%\nn={r.customers:,}',ha='center',fontsize=10)
    ax.set_ylim(0, max(contract.ci_high_pct)+10)
    fig.tight_layout();fig.savefig(out/'contract_churn.png',dpi=160);plt.close(fig)
    pivot=segments.pivot(index='contract',columns='tenure_band',values='churn_pct')
    pivot=pivot.reindex(columns=['0–12 months','13–24 months','25–48 months','49+ months'])
    fig,ax=plt.subplots(figsize=(9,4.5))
    image=ax.imshow(pivot,cmap='YlOrRd',vmin=0,vmax=100)
    ax.set_xticks(range(len(pivot.columns)),pivot.columns)
    ax.set_yticks(range(len(pivot.index)),pivot.index)
    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            val=pivot.iloc[i,j]
            ax.text(j,i,f'{val:.1f}%' if pd.notna(val) else 'n<50',ha='center',va='center')
    ax.set_title('Churn proportion by contract and tenure (groups with at least 50 customers)')
    fig.colorbar(image,ax=ax,label='Churn (%)');fig.tight_layout();fig.savefig(out/'segment_heatmap.png',dpi=160);plt.close(fig)
    metrics={'customers':len(df),'churned':int(df.churn_flag.sum()),'churn_pct':float(df.churn_flag.mean()*100),
             'missing_total_charges':int(df.TotalCharges.isna().sum()),
             'missing_total_charges_all_zero_tenure':bool(df.loc[df.TotalCharges.isna(),'tenure'].eq(0).all())}
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2)+'\n')
    top=segments.iloc[0]
    (out/'findings.md').write_text(f'''# Telco churn: findings and retention hypotheses

- **{metrics['churn_pct']:.1f}%** of the {len(df):,} sample customers are labelled churned ({metrics['churned']:,}).
- Month-to-month customers have **{contract.loc['Month-to-month','churn_pct']:.1f}%** churn compared with **{contract.loc['Two year','churn_pct']:.1f}%** for two-year contracts.
- The highest-rate eligible segment is **{top.contract}, {top.tenure_band}**: **{top.churn_pct:.1f}%**, from {top.customers:,} customers.

## Suggested action

Investigate onboarding and service friction for newer month-to-month customers. Design a randomized retention pilot before rolling out incentives. Measure incremental retained customers and contribution margin net of offer cost. Contract length is associated with churn here; these comparisons do not prove that moving customers to longer contracts will reduce churn.

## Data quality and definitions

{metrics['missing_total_charges']} blank TotalCharges values become missing numeric values and remain missing; the customers stay in churn denominators. All those records have zero tenure: {metrics['missing_total_charges_all_zero_tenure']}. Customer IDs are checked for uniqueness, then omitted from derived data. Groups smaller than 50 are excluded from segment comparisons. Contract charts show illustrative 95% Wilson binomial intervals; this sample is not a probability sample of a current telecom population.

## Limits

This is the IBM Telco educational sample, not a live client engagement. No acquisition date, churn date, margin or treatment information is available. The churn proportion is cross-sectional, not a monthly churn hazard. Sums of charges for already-churned customers describe sample exposure, not forecast revenue loss or recoverable revenue. Segment rankings are descriptive; multiple comparisons and confounding limit inference. No predictive accuracy or commercial impact is claimed.

Validation: unique customer IDs; valid outcomes; nonnegative charges; SQL customer and churn totals reconcile to pandas; highest-rate SQL segment independently checked.
''')
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':
    main()
