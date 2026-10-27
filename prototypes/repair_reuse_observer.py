"""Typed observer of captured SQL state and returned-output presence.

This is a same-user local observation boundary, not authenticated execution.
Missing, mistyped or contradictory capture facts are rejected, never defaulted.
"""
from datetime import datetime
import re


def _fields(value, fields, where):
    if type(value) is not dict or set(value) != set(fields):
        raise ValueError(where+' needs its complete declared fields')


def _text(value, where, nullable=False):
    if nullable and value is None:
        return
    if type(value) is not str or not value.strip() or len(value)>4096:
        raise ValueError(where+' needs bounded nonempty text')


def _integer(value, where, minimum=None):
    if type(value) is not int or (minimum is not None and value<minimum):
        raise ValueError(where+' needs an integer within its declared bounds')


def _boolean(value, where):
    if type(value) is not bool:
        raise ValueError(where+' needs an explicit Boolean')


def _flag(value, where):
    if type(value) is not int or value not in (0,1):
        raise ValueError(where+' needs a captured SQLite 0/1 flag')


def _snapshot(state, sequence, where):
    _fields(state, ('security','part','record','policy','copies','tombstone','holds',
                    'movements','dispositions','copy_dispositions','audit'), where)
    security=state['security']
    known=type(security) is dict and security.get('actor') is not None
    _fields(security, ('actor','session_valid','revoked','grants',
                      *(('active','epoch','session_epoch') if known else ())), where+'.security')
    _text(security['actor'],where+'.actor',True)
    for key in ('session_valid','revoked'):_boolean(security[key],where+'.'+key)
    if known:
        _flag(security['active'],where+'.active')
        for key in ('epoch','session_epoch'):_integer(security[key],where+'.'+key,0)
    if type(security['grants']) is not list or len(security['grants'])>64:
        raise ValueError('Security grants need a bounded list')
    for grant in security['grants']:
        _fields(grant,('permission','scope'),'grant')
        for key in grant:_text(grant[key],'grant.'+key)
    part=state['part']
    if part is not None:
        _fields(part,('id','book','physical','reserved'),where+'.part');_text(part['id'],'part.id')
        for key in ('book','physical','reserved'):_integer(part[key],'part.'+key,0)
        if part['reserved']>part['book']:raise ValueError('Reserved stock exceeds book stock')
    record=state['record']
    if record is not None:
        _fields(record,('id','class','held','policy','state','payload_present'),where+'.record')
        for key in ('id','class','state'):_text(record[key],'record.'+key)
        _text(record['policy'],'record.policy',True)
        _flag(record['held'],'record.held');_boolean(record['payload_present'],'record.payload_present')
    holds=state['holds']
    if type(holds) is not list or len(holds)>64:
        raise ValueError('Hold snapshot needs a bounded complete row list')
    identities=set()
    for hold in holds:
        _fields(hold,('record_id','hold_id','active'),'hold')
        _text(hold['record_id'],'hold.record_id');_flag(hold['active'],'hold.active')
        if type(hold['hold_id']) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}',hold['hold_id']):
            raise ValueError('Invalid captured hold identity')
        if record is None or hold['record_id']!=record['id']:
            raise ValueError('Hold row belongs to another or unknown record')
        if hold['hold_id'] in identities:raise ValueError('Duplicate captured hold identity')
        identities.add(hold['hold_id'])
    if record is not None and record['held']!=int(any(hold['active'] for hold in holds)):
        raise ValueError('Aggregate hold flag contradicts captured hold rows')
    policy=state['policy']
    if policy is not None:
        _fields(policy,('id','reviewed','not_before_tick','basis'),where+'.policy')
        _text(policy['id'],'policy.id');_text(policy['basis'],'policy.basis')
        _flag(policy['reviewed'],'policy.reviewed');_integer(policy['not_before_tick'],'policy.not_before_tick',0)
    tombstone=state['tombstone']
    if tombstone is not None:
        _fields(tombstone,('record_id','txn'),where+'.tombstone')
        _text(tombstone['record_id'],'tombstone.record_id');_integer(tombstone['txn'],'tombstone.txn',1)
    rows={'copies':('kind',),'movements':('txn','part','kind','quantity'),
          'dispositions':('txn','record_id'),'copy_dispositions':('txn','record_id','kind'),
          'audit':('txn','actor','action','target')}
    for name,fields in rows.items():
        if type(state[name]) is not list or len(state[name])>64:
            raise ValueError(where+'.'+name+' needs a bounded row list')
        for row in state[name]:
            _fields(row,fields,where+'.'+name)
            for key in fields:
                if key=='txn':
                    _integer(row[key],name+'.txn',1)
                    if row[key]!=sequence:raise ValueError('Ledger row belongs to another transaction')
                elif key=='quantity':_integer(row[key],name+'.quantity')
                else:_text(row[key],name+'.'+key,key=='actor')
            if name=='movements' and (row['kind'] not in ('issue','reserve','adjust') or
                    (row['kind']!='adjust' and row['quantity']<=0)):
                raise ValueError('Invalid stock movement kind/quantity')
        if name in ('copies','copy_dispositions'):
            kinds=[row['kind'] for row in state[name]]
            if len(kinds)!=len(set(kinds)):raise ValueError('Duplicate declared copy kind')


def validate_capture(event):
    """Admit the registered v4 SQL-capture contract before any projection."""
    _fields(event,('sequence','utc','action','actor','part_id','record_id','request_id','hold_id','before','after','result'),'event')
    _integer(event['sequence'],'sequence',1);_text(event['utc'],'utc')
    if datetime.fromisoformat(event['utc']).tzinfo is None:raise ValueError('Capture timestamp needs a timezone')
    _text(event['action'],'action')
    if event['action'] not in ('issue','reserve','issue_reserved','adjust','count','read','revoke','grant_read',
                               'hold','release_hold','set_fixture_policy','dispose','restore'):
        raise ValueError('Unsupported captured operation')
    for key in ('actor','part_id','record_id','request_id'):_text(event[key],key,True)
    if event['action'] in ('hold','release_hold'):
        if type(event['hold_id']) is not str or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}',event['hold_id']):
            raise ValueError('Hold operation needs an explicit captured identity')
    elif event['hold_id'] is not None:
        raise ValueError('Non-hold operation has an unexpected hold identity')
    for key in ('before','after'):
        _snapshot(event[key],event['sequence'],key)
        for group,target in (('part','part_id'),('record','record_id')):
            row=event[key][group]
            if row is not None and row['id']!=event[target]:raise ValueError('Snapshot target differs from captured target')
        if any(row['part']!=event['part_id'] for row in event[key]['movements']):
            raise ValueError('Movement row belongs to another part')
        policy=event[key]['policy'];record=event[key]['record'];tombstone=event[key]['tombstone']
        if policy is not None and (record is None or policy['id']!=record['policy']):
            raise ValueError('Policy row differs from the record policy reference')
        if tombstone is not None and tombstone['record_id']!=event['record_id']:
            raise ValueError('Tombstone belongs to another record')
        for group in ('dispositions','copy_dispositions'):
            if any(row['record_id']!=event['record_id'] for row in event[key][group]):
                raise ValueError('Disposition row belongs to another record')
    if event['actor']!=event['before']['security']['actor']:
        raise ValueError('Event actor differs from decision security actor')
    result=event['result']
    if type(result) is not dict:raise ValueError('Captured result needs an object')
    outcome=result.get('outcome')
    if type(outcome) is not str or outcome not in ('served','denied','committed','observed','replay','no_change'):
        raise ValueError('Unsupported captured outcome')
    extra=('reason',) if outcome in ('denied','replay','no_change') else ('book','physical','reserved') if outcome=='observed' else ()
    _fields(result,('outcome','returned_payload_present',*extra),'result')
    _boolean(result['returned_payload_present'],'result.returned_payload_present')
    if result['returned_payload_present'] != (event['action']=='read' and outcome=='served'):
        raise ValueError('Returned presence contradicts operation/outcome')
    if outcome=='served' and event['action']!='read':raise ValueError('Only reads can serve record content')
    if extra==('reason',):_text(result['reason'],'result.reason')
    if outcome=='observed':
        if event['action']!='count':raise ValueError('Only a count returns stock observations')
        for key in extra:_integer(result[key],'result.'+key,0)
    after=event['after'];before=event['before']
    if outcome=='committed' and event['action'] in ('issue','issue_reserved','adjust'):
        kind='adjust' if event['action']=='adjust' else 'issue'
        if not before['part'] or not after['part'] or not any(row['kind']==kind for row in after['movements']):
            raise ValueError('Committed stock result lacks its stock state/movement capture')
    if after['dispositions'] or (event['action']=='dispose' and outcome=='committed'):
        if not (after['dispositions'] and before['record'] and after['record'] and
                before['record']['payload_present'] and not after['record']['payload_present']):
            raise ValueError('Disposition ledger/result contradicts captured content transition')


def observe(event):
    """Derive signals from typed decision state and committed/returned facts."""
    validate_capture(event)
    before, after = event['before'], event['after']
    security = before['security'];part = before['part'];record = before['record']
    record_class = record['class'] if record else ''
    movements = after['movements']
    adjustment = any(r['kind']=='adjust' for r in movements)
    disposition = bool(after['dispositions'] and before['record'] and after['record']
                       and before['record']['payload_present'] and not after['record']['payload_present'])
    expected_copies = {r['kind'] for r in before['copies']}
    receipts = {r['kind'] for r in after['copy_dispositions']}
    def audited(action, target):
        return any(row['action']==action and row['target']==target and row['actor']==event['actor']
                   for row in after['audit'])
    def permitted(permission, scope='*'):
        valid = bool(security['actor'] and security['active'] and security['session_epoch'] == security['epoch'])
        return valid and any(g['permission']==permission and g['scope'] in ('*',scope) for g in security['grants'])
    valid = bool(security['actor'] and security['active'] and security['session_epoch'] == security['epoch'])
    change_hold=event['action'] in ('hold','release_hold')
    other_holds=lambda state:{h['hold_id']:h['active'] for h in state['holds'] if h['hold_id']!=event['hold_id']}
    values = {
        'stockMismatch': bool(part and part['book'] != part['physical']),
        'adjustmentAuthorized': permitted('stock.adjust'),
        'revocationEffective': bool(event['action']=='read' and security['actor'] and not valid),
        'holdActive': any(hold['active']==1 for hold in before['holds']),
        'holdChangeAttempted': change_hold,
        'unrelatedHoldsPreserved': other_holds(before)==other_holds(after) if change_hold else True,
        'retentionBasisKnown': bool(before['policy'] and before['policy']['reviewed']),
        'dispositionAuthorityKnown': bool(record and permitted('record.dispose', record_class)),
        'issueCommitted': any(r['kind']=='issue' and r['quantity']>0 for r in movements),
        'adjustmentCommitted': adjustment,
        'adjustmentAuditRecorded': adjustment and audited('adjust',event['part_id']),
        'readServed': event['result']['returned_payload_present'],
        'dispositionCommitted': disposition,
        'dispositionAuditRecorded': disposition and audited('dispose',event['record_id']),
        'copiesAccounted': disposition and not after['copies'] and expected_copies == receipts,
        'readAuthorized': bool(record and permitted('record.read', record_class)),
        'issueAuthorized': permitted('stock.issue')}
    return {'DummyRehearsal::probe::'+key:value for key,value in values.items()}
