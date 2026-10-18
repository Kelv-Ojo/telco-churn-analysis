"""Verify input provenance, rebuild outputs, and check fixed-snapshot totals."""
from pathlib import Path
import hashlib,json,subprocess,sys,platform,importlib.metadata

root=Path(__file__).resolve().parent
manifest=root/'data/manifest.json'
if manifest.exists():
    for name,expected_hash in json.loads(manifest.read_text()).items():
        actual=hashlib.sha256((root/'data'/name).read_bytes()).hexdigest()
        if actual!=expected_hash: raise ValueError(f'Input fingerprint changed: {name}')
elif (root/'data/provenance.json').exists():
    expected_hash=json.loads((root/'data/provenance.json').read_text())['csv_zip_sha256']
    if hashlib.sha256((root/'data/bookings.csv.zip').read_bytes()).hexdigest()!=expected_hash:
        raise ValueError('Input fingerprint changed: bookings.csv.zip')
subprocess.run([sys.executable,str(root/'src/analyze.py')],cwd=root,check=True)
actual=json.loads((root/'reports/metrics.json').read_text())
expected=json.loads((root/'validation-baseline.json').read_text())
for key,value in expected.items():
    if actual.get(key)!=value: raise ValueError(f'{key}: expected {value!r}, got {actual.get(key)!r}')
environment={'python':platform.python_version(),'platform':platform.platform(),
             'packages':{p:importlib.metadata.version(p) for p in ['pandas','numpy']}}
(root/'reports/environment.json').write_text(json.dumps(environment,indent=2)+'\n')
print('Verified source fingerprint, pipeline checks and snapshot totals:',expected)
