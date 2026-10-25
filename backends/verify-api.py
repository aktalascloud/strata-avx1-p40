"""Read-only API patch fingerprint check. Never applies patches or changes a running service."""
import argparse,hashlib,json,pathlib,re
def sha(data):return hashlib.sha256(data).hexdigest()
def verify(root):
    root=pathlib.Path(root).resolve(strict=True);here=pathlib.Path(__file__).resolve().parent
    review=json.loads((here/'api-compat-review.json').read_text(encoding='utf8'))
    if not review.get('semantic_reviewed_for_optional_source') or sha((here/'api-compat.patch').read_bytes())!=review['patch_sha256']:
        raise ValueError('API patch semantic review does not match its bytes')
    base=review['base_lf_sha256'];candidate=review['candidate_lf_sha256']
    if set(base)!=set(candidate):raise ValueError('Incomplete API source review')
    values={}
    for rel in base:
        path=root/rel
        if not path.resolve().is_relative_to(root) or path.is_symlink() or pathlib.PurePosixPath(rel).is_absolute() or '..' in pathlib.PurePosixPath(rel).parts:
            raise ValueError('API source path escapes the selected root')
        values[rel]=sha(path.read_bytes().replace(b'\r\n',b'\n')) if path.is_file() else None
    if values==base:state='reviewed_base'
    elif values==candidate:state='reviewed_candidate'
    else:raise ValueError('API source differs from both reviewed base and candidate; perform semantic adaptation, never replace files or overwrite hashes mechanically')
    protected='runtime' in root.parts and 'versions' in root.parts
    return dict(source_state=state,can_apply_patch=state=='reviewed_base' and not protected and (root/'.git').exists(),
                protected_runtime_tree=protected,
                API_source_checked=True,production_qualified=False,new_schema3_control_review_required=True,
                writes=False,model_downloads=False)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True);a=p.parse_args()
    try:print(json.dumps(verify(a.root)))
    except (ValueError,OSError) as e:p.exit(2,str(e)+'\n')
