# Reproducing and validating this analysis

Use Python 3.11 for the automated validation environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-ci.txt
python ci_validate.py
```

On Windows activate with `.venv\Scripts\activate`. Direct analysis dependencies are pinned in requirements-ci.txt; this is not a complete transitive or cross-platform lockfile. GitHub Actions records the resolved packages with pip freeze. The runner records Python, platform, pandas and NumPy versions in reports/environment.json.

The workflow runs on pushes to main, pull requests and manual dispatch. It checks source fingerprints, executes the analysis and its built-in quality assertions, and checks fixed-snapshot totals against validation-baseline.json. If the input version changes, review the source and expected totals before updating the baseline. Do not update expectations simply to silence a failure.

Python success does not verify Power BI Desktop, native Excel refresh, Power Query, PivotTables or deployed dashboards. The Excel workbook authoring runtime, where applicable, is separate from the Python analysis workflow.
