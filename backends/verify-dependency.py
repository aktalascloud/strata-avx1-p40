"""Check actual library inputs against the existing pinned archive; fetch no sources or weights."""
import hashlib,json,pathlib,zipfile
R=pathlib.Path(__file__).resolve().parents[1];pin='3cf03257f219afbe7334045ff7c6a06ac68c627d'
zpath=R/'deps'/('llama.cpp-'+pin+'.zip');root=R/'deps/llama.cpp';prefix='llama.cpp-'+pin+'/'
count=0
with zipfile.ZipFile(zpath) as z:
 for i in z.infolist():
  if i.is_dir() or not i.filename.startswith(prefix):continue
  rel=i.filename[len(prefix):];first=rel.split('/')[0]
  if first not in ('src','include','common','ggml','cmake','vendor','CMakeLists.txt','LICENSE'):continue
  p=(root/rel).resolve()
  if not p.is_relative_to(root.resolve()) or not p.is_file():raise SystemExit('Dependency input missing: '+rel)
  if hashlib.sha256(p.read_bytes()).digest()!=hashlib.sha256(z.read(i)).digest():raise SystemExit('Dependency input changed: '+rel)
  count+=1
if count<500:raise SystemExit('Incomplete pinned source archive')
print(json.dumps(dict(pin=pin,verified_files=count,archive_sha256=hashlib.sha256(zpath.read_bytes()).hexdigest())))
