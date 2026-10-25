"""Fail closed on unreviewed optional-backend or core source changes."""
import hashlib,json,pathlib,subprocess
R=pathlib.Path(__file__).resolve().parent; project=R.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify_files(root,rows):
 for rel,expected in rows.items():
  p=(root/rel).resolve()
  if not p.is_relative_to(root.resolve()) or not p.is_file() or sha(p).lower()!=expected.lower():
   raise SystemExit('Source review mismatch: '+rel)
review=json.loads((R/'poly/REVIEW.json').read_text(encoding='utf8'))
if review.get('semantic_reviewed') is not True:raise SystemExit('Semantic review required')
verify_files(R/'poly',review['files'])
core=json.loads((project/'patches/no-cpu-pin-review.json').read_text(encoding='utf8'))
if not core.get('semantic_reviewed') or sha(project/'patches/no-cpu-pin.patch').lower()!=core['patch_sha256'].lower():
 raise SystemExit('Core aggregate review mismatch')
verify_files(project/'upstream',core['source_hashes'])
print(json.dumps(dict(optional_source_verified=True,core_source_verified=True,model_downloads=False)))
