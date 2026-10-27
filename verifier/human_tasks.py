"""Scoped human/task allocation facts; documentary review, never simulation."""
from copy import deepcopy
import json
import re

from .core import _pairs
from .foundation import Invalid, _object

VERSION = 'human-tasks-1.0'
MARKER = 'CSE-HUMAN-TASKS/1.0'
FIELDS = {'purpose', 'entry', 'inputs', 'completion', 'skills', 'equipment',
          'procedure', 'duration', 'concurrency', 'interruption', 'recovery',
          'training', 'evaluation'}
ID = re.compile(r'[A-Za-z][A-Za-z0-9_-]{0,63}\Z')
DECIMAL = re.compile(r'(?:0|[1-9][0-9]{0,31})(?:\.[0-9]{1,32})?\Z')
ROLES = {'execute', 'assist', 'monitor', 'authorize'}


class UnsupportedTaskProfile(ValueError):
    pass


def _ids(values, where):
    if (type(values) is not list or len(values)>64 or
            any(type(x) is not str or not ID.fullmatch(x) for x in values) or len(set(values))!=len(values)):
        raise Invalid(where + ' needs at most 64 distinct IDs')


def performers(values):
    if type(values) is not list or len(values)>64:
        raise Invalid('Performers need a bounded list')
    identities = set()
    for value in values:
        _object(value, ('element', 'role', 'allocation'), 'performer')
        _ids([value['element']], 'performer element')
        if value['role'] not in ROLES or value['allocation'] not in ('human', 'automation'):
            raise Invalid('Unsupported performer role or declared allocation category')
        identity = (value['element'], value['role'])
        if identity in identities:
            raise Invalid('Duplicate task performer/role')
        identities.add(identity)


def expectation(value):
    _object(value, ('topic','kind','task','function','scenario','performers','fields'), 'human-task expectation')
    _ids([value['task'],value['function'],value['scenario']], 'task/function/scenario')
    performers(value['performers'])
    _ids(value['fields'], 'selected task fields')
    if not value['fields'] or set(value['fields'])-FIELDS:
        raise Invalid('Select at least one supported task fact field')


def schema(register):
    _object(register, ('version', 'tasks'), 'task register')
    if register['version'] != VERSION:
        raise UnsupportedTaskProfile('Unsupported human-task register version')
    tasks = register['tasks']
    if type(tasks) is not dict or len(tasks)>64 or any(not ID.fullmatch(k) for k in tasks):
        raise Invalid('Task register needs a bounded ID map')
    for key, task in tasks.items():
        _object(task, ('function','scenario','performers','facts'), key)
        _ids([task['function'],task['scenario']], key)
        performers(task['performers'])
        if type(task['facts']) is not dict or set(task['facts'])-FIELDS:
            raise Invalid('Unsupported task fact field')
        for field, fact in task['facts'].items():
            keys = ('status','text','basis','refs') + (('value','unit') if field=='duration' else ())
            _object(fact,keys,key+'.'+field)
            if fact['status'] not in ('proposed','reported','unknown'):
                raise Invalid('Task facts distinguish proposed, reported and unknown')
            if type(fact['text']) is not str or len(fact['text'])>4096:
                raise Invalid('Task fact text exceeds its contract')
            if fact['basis'] is not None:
                _ids([fact['basis']], 'task fact basis')
            _ids(fact['refs'], key+'.'+field+' references')
            if field=='duration':
                if fact['value'] is not None and (type(fact['value']) is not str or not DECIMAL.fullmatch(fact['value'])):
                    raise Invalid('Duration needs a bounded nonnegative exact decimal string or null')
                if fact['unit'] is not None and type(fact['unit']) is not str:
                    raise Invalid('Duration unit must be text or null')
    return register


def inspect_tasks(workflow, selected):
    report = {'version':VERSION,'status':'error','findings':[],'tasks':{},
        'claim_scope':'selected_task_documentation_and_declared_function_allocation',
        'behavior':'not_run','staffing_adequacy':'not_evaluated','performance_qualification':'not_evaluated'}
    def issue(rule,status,ids,detail):
        report['findings'].append({'rule':rule,'status':status,'ids':ids,'detail':detail})
    try:
        documents = workflow.get('supplemental_documents',{}).get('cseHumanTasks',[])
        if not documents:
            issue('task_register_missing','fail',list(selected),'The selected task register is absent.')
            return report
        if len(documents)!=1:
            raise Invalid('Exactly one selected cseHumanTasks document is required')
        document = documents[0]
        owners = workflow['native_inventory']['concerns']
        if sum(x.get('qualified_name')==document.get('owner') for x in owners)!=1:
            raise Invalid('The task register must be owned by one parsed concern')
        lines = document['body'].strip().splitlines()
        if not lines or lines[0].strip()!=MARKER:
            raise UnsupportedTaskProfile('Unsupported human-task document header')
        payload = '\n'.join(lines[1:])
        if len(payload.encode())>1_000_000:
            raise Invalid('Task register exceeds 1 MB')
        register = json.loads(payload,object_pairs_hook=_pairs,
            parse_constant=lambda x: (_ for _ in ()).throw(Invalid('Nonfinite task record')))
        schema(register)
        record = workflow['record'];elements = record['elements'];sources = record['sources']
        allocations = {(x['from'],x['to']) for x in record['relations'].values() if x['kind']=='allocated_to'}
        def binding(key,kinds,ids):
            if key not in elements or elements[key]['kind'] not in kinds:
                issue('task_binding','fail',ids+[key],'Task reference is absent or has the wrong parsed documentary kind.')
        # All recorded task references are structural obligations; unselected
        # substantive facts do not acquire invented performance requirements.
        for key,task in register['tasks'].items():
            binding(key,{'step'},[key]);binding(task['function'],{'function'},[key])
            binding(task['scenario'],{'scenario'},[key])
            for performer in task['performers']:
                binding(performer['element'],{'element','system'},[key])
                if (task['function'],performer['element']) not in allocations:
                    issue('task_allocation_missing','fail',[key,task['function'],performer['element']],
                        'Declared task responsibility lacks its documentary function allocation.')
            for field,fact in task['facts'].items():
                if fact['basis'] is not None and fact['basis'] not in sources:
                    issue('task_source_missing','fail',[key,field],'Task fact basis is absent.')
                for ref in fact['refs']:
                    if field=='evaluation':
                        evidence=record['evidence'].get(ref)
                        if evidence is None or evidence['target'] not in (key,task['function'],task['scenario']):
                            issue('task_evaluation_binding','fail',[key,ref],'Evaluation must target this task, its function or its scenario.')
                    else:
                        binding(ref,{'element','system'} if field in ('equipment','procedure') else set(elements[x]['kind'] for x in elements),[key,field])
        for expected_id, expected in selected.items():
            key = expected['task'];task = register['tasks'].get(key)
            if task is None:
                issue('task_missing','fail',[expected_id,key],'An expected task row was removed, not completed.')
                continue
            if (task['function'],task['scenario']) != (expected['function'],expected['scenario']):
                issue('task_context_changed','fail',[expected_id,key],'Expected task function or scenario changed.')
            normalize=lambda values: sorted((x['element'],x['role'],x['allocation']) for x in values)
            if normalize(task['performers']) != normalize(expected['performers']):
                issue('task_responsibility_changed','fail',[expected_id,key],'Expected human/automation responsibilities changed.')
            if not task['performers']:
                issue('task_performer_unknown','unknown',[key],'Identify the proposed responsible performer(s).')
            checked = {}
            for field in expected['fields']:
                fact = task['facts'].get(field)
                if fact is None:
                    issue('task_fact_missing','fail',[expected_id,key,field],'A selected task fact is absent.')
                    continue
                checked[field] = deepcopy(fact)
                if fact['status']=='unknown' or not fact['text'].strip() or fact['basis'] is None:
                    issue('task_fact_unknown','unknown',[key,field],'Task fact or its basis remains unresolved.')
                if fact['basis'] is not None and workflow.get('sources',{}).get(fact['basis'],{}).get('status')!='pass':
                    issue('task_source_unchecked','unknown',[key,field,fact['basis']],
                        'Supply and check the selected fact source through the project scope; a declared source alone is not checked provenance.')
                if fact['status']=='reported' and sources.get(fact['basis'],{}).get('kind')!='reported_observation':
                    issue('task_observation_basis','fail',[key,field],'A proposed/source statement cannot be relabelled as a reported observation.')
                if field in ('equipment','procedure','evaluation') and not fact['refs']:
                    issue('task_dependency_unknown','unknown',[key,field],'Identify the selected dependency/evaluation reference.')
                if field=='duration':
                    if fact['value'] is None or fact['unit'] is None:
                        issue('task_duration_unknown','unknown',[key],'Duration or its unit is unresolved.')
                    elif fact['unit'] not in ('second','minute','hour'):
                        issue('task_duration_unit','unsupported',[key],'This documentary duration profile admits second, minute and hour; no unit conversion is performed.')
            report['tasks'][key] = {'label':elements.get(key,{}).get('label',key),
                'function':task['function'],'scenario':task['scenario'],
                'performers':deepcopy(task['performers']),'selected_facts':checked,
                'observation_limit':'Reported means attributed to supplied bytes, not independently measured or qualified.'}
    except UnsupportedTaskProfile as exc:
        issue('task_profile_unsupported','unsupported',list(selected),str(exc))
    except (ValueError,TypeError,KeyError,RecursionError) as exc:
        issue('task_register_input','error',list(selected),str(exc))
    finally:
        states={x['status'] for x in report['findings']}
        report['status']=next((x for x in ('error','fail','unsupported','unknown') if x in states),'pass')
    return report
