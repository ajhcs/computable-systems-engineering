"""Bounded multi-trace review with one captured model/runtime configuration.

Only native parser extraction is reused. Compilation and supported monitors run
normally for every case. No persistent cache, executable model code or new
verdict engine is provided.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

from .core import _pairs
from .foundation import read_regular
from . import sysml
from .sysml_batch_context import PARSE_SESSION


def _read_json(path, cap):
    raw = read_regular(path, cap)
    return json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Nonfinite JSON'))), raw


def runtime_identity():
    """Content identities of the checker, bridge, parser and library sources.

    The pilot's generated library index is excluded; it is not source authority.
    Java/OS authenticity and a protected execution boundary are not established.
    """
    files = list((sysml.ROOT/'verifier').glob('*.py'))
    files += [sysml.BRIDGE_SOURCE, sysml.BRIDGE_STAMP, sysml.JAR]
    files += list(sysml.CLASSES.glob('SysmlBridge*.class'))
    files += [p for p in sysml.LIBRARY.rglob('*') if p.suffix in ('.sysml','.kerml')]
    if not (sysml.CLASSES/'SysmlBridge.class').is_file() or not sysml.LIBRARY.is_dir():
        raise ValueError('Pinned parser/library/bridge is unavailable')
    return {str(p): sha256(read_regular(p, 200_000_000)).hexdigest() for p in sorted(set(files))}


def inspect_batch(models, manifest_path, retained_manifest_sha256, cases, *,
                  parser_timeout=60, observation_cap=10000, work_cap=1000000):
    report = {'version':'sysml-trace-batch-1.0','status':'error','results_usable':False,
        'claim_scope':'selected_native_model_sampled_or_event_trace_checks',
        'results':{},'findings':[],'parser_calls':0,'parser_reuses':0,
        'validation':'not_performed','acceptance':'not_evaluated',
        'limits':['Parser extraction only is reused within this call; every trace is compiled/monitored normally.',
            'Complete input and checker/parser/library content identities are checked before and after the batch.',
            'Recorded or synthetic traces are not executed-application evidence merely because they pass.',
            'No native workflow execution, physical model, protected runner or standards conformity is established.']}
    captured=[];token=None;identity=None
    try:
        if type(models) not in (list,tuple) or not 1<=len(models)<=32:
            raise ValueError('Batch needs 1..32 explicit model paths')
        if type(cases) is not dict or not 1<=len(cases)<=64:
            raise ValueError('Batch needs 1..64 separately identified trace cases')
        if any(type(k) is not str or not sysml.ID.fullmatch(k) for k in cases):
            raise ValueError('Trace case IDs must be distinct valid IDs')
        for model in models:
            captured.append((model,read_regular(model,5_000_000),5_000_000))
        manifest, raw = _read_json(manifest_path,1_000_000)
        report['manifest_sha256']=sha256(raw).hexdigest()
        if report['manifest_sha256'] != retained_manifest_sha256:
            raise ValueError('Manifest differs from the retained byte identity')
        captured.append((manifest_path,raw,1_000_000))
        evidence={}
        for key,path in cases.items():
            evidence[key],raw = _read_json(path,5_000_000)
            captured.append((path,raw,5_000_000))
        report['inputs']=[{'path':str(p),'sha256':sha256(raw).hexdigest()} for p,raw,_ in captured]
        identity=runtime_identity();report['runtime_sha256']=identity
        parsed={}
        def parse(source, timeout):
            key=(source,timeout)
            if key not in parsed:
                parsed[key]=sysml._run_parser(source,timeout);report['parser_calls']+=1
            else: report['parser_reuses']+=1
            return deepcopy(parsed[key])
        if PARSE_SESSION.get() is not None:
            raise ValueError('Nested parser-reuse batches are unsupported')
        token=PARSE_SESSION.set(parse)
        for key in cases:
            report['results'][key]=sysml.check_sysml(models,manifest=deepcopy(manifest),
                evidence=deepcopy(evidence[key]),review=True,parser_timeout=parser_timeout,
                observation_cap=observation_cap,work_cap=work_cap)
        states=[v['status'] for v in report['results'].values()]
        report['status']=next((s for s in ('error','fail','unsupported','unknown','not_run') if s in states),
                              'pass' if states and all(s=='pass' for s in states) else 'error')
        report['results_usable']=True
    except (OSError,UnicodeError,ValueError,TypeError,KeyError,RuntimeError,RecursionError) as exc:
        report['findings'].append({'rule':'batch_input_or_operation','status':'error','detail':str(exc)})
        report['status']='error';report['results_usable']=False
    finally:
        if token is not None: PARSE_SESSION.reset(token)
        try:
            if any(read_regular(p,cap)!=raw for p,raw,cap in captured):
                raise ValueError('Batch input changed during checking; all batch results are unusable')
            if identity is not None and runtime_identity()!=identity:
                raise ValueError('Checker/parser/library changed during batch; all batch results are unusable')
        except (OSError,ValueError) as exc:
            report['status']='error';report['results_usable']=False
            report['findings'].append({'rule':'batch_configuration_changed','status':'error','detail':str(exc)})
    return report
