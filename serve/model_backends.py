"""Explicit optional-engine profiles; never feed Qwen-only switches to another CLI."""
from __future__ import annotations
import math

def checked_bind(cfg, cli_port, argv):
    """Honor profile ports; using the native API port requires an explicit CLI choice."""
    explicit=any(x=='--port' or x.startswith('--port=') for x in argv)
    port=cli_port if explicit else cfg.get('port',8094)
    if type(port) is not int or not 1024<=port<=65535 or port==8080 or port==8093 and not explicit:
        raise ValueError('8080 is reserved; 8093 requires an explicit --port after the previous server stops')
    return port

def checked_args(cfg):
    kind=cfg.get('engine_kind');backend=cfg.get('backend');args=cfg.get('args')
    if kind not in ('ggml','poly') or backend not in ('cpu','cuda','vulkan'):
        raise ValueError('Unknown optional engine/backend profile')
    if kind=='poly' and backend!='cuda':raise ValueError('The reviewed Poly build is CUDA-only')
    if not isinstance(args,list) or not args or not all(isinstance(x,str) and x and '\0' not in x for x in args):
        raise ValueError('Engine argv must contain separate nonempty string elements')
    if cfg.get('user_args') or cfg.get('layer_split') or cfg.get('replicas'):
        raise ValueError('Regenerate this optional-engine profile; native Qwen argument/split overrides do not apply')
    if cfg.get('parallel') not in (None,1) or cfg.get('gpu_groups'):
        raise ValueError('Parallel slots and GPU groups require separate optional-backend qualification')
    policy=cfg.get('mtp_policy')
    if policy not in ('require','off'):raise ValueError('An explicit MTP policy is required')
    if ('--require-mtp' in args)!=(policy=='require'):raise ValueError('MTP policy and engine argv disagree')
    if cfg.get('drafting') not in (None,'auto','mtp','off') or cfg.get('mtp') is False and policy=='require':
        raise ValueError('This profile requires a compatible native NextN head; no silent drafter fallback')
    if cfg.get('drafting')=='off' and policy=='require' or cfg.get('drafting')=='mtp' and policy=='off' or cfg.get('mtp') is True and policy=='off':
        raise ValueError('Drafting override contradicts the prepared MTP policy; regenerate the profile')
    if cfg.get('vision'):raise ValueError('A family-matched vision encoder is not qualified by this optional profile')
    return list(args)

def sampling_keys(sampling):
    """GGML's sampler has no native Qwen top-k64 ceiling; explicit zero values matter."""
    if sampling.get('strata_tune'):
        raise ValueError('Native Qwen per-request tuning is not supported by this backend')
    result=[]
    fields={'temperature':'temperature','top_p':'top_p','min_p':'min_p','repetition_penalty':'penalty_repeat',
            'frequency_penalty':'penalty_freq','presence_penalty':'penalty_present'}
    for key,wire in fields.items():
        value=sampling.get(key)
        if value is None:continue
        if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Invalid sampling value: '+key)
        result.append(wire+'='+repr(float(value)))
    for key,wire in (('top_k','top_k'),('seed','seed'),('penalty_last_n','penalty_last_n')):
        value=sampling.get(key)
        if value is None:continue
        if type(value) is not int or value<0:raise ValueError('Invalid sampling integer: '+key)
        result.append(wire+'='+str(value))
    if any(k in sampling for k in ('repetition_penalty','frequency_penalty','presence_penalty')) and 'penalty_last_n' not in sampling:
        result.append('penalty_last_n=64')
    return (' '+' '.join(result)) if result else ''
