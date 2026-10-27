"""Bounded SQLite reference implementation using dummy stock and records only.

This application is the system under test. CSE supplies the independent monitor.
No network, real authentication, physical inventory or secure-media erasure.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import json
import re
from pathlib import Path
import sqlite3
import uuid

VERSION = 'repair-reuse-prototype-1.3'
SCHEMA_VERSION = 2
DEFAULT_HOLD_ID = 'fixture-default'
HOLD_LIMIT = 64
HOLD_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}\Z')
FAULTS = {'issue_on_mismatch', 'ignore_revocation', 'ignore_hold',
          'omit_adjustment_audit', 'omit_disposition_audit', 'leave_export',
          'ignore_read_scope', 'ignore_issue_permission', 'release_all_holds'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


class Store:
    def __init__(self, path, *, create=False, faults=()):
        self.path = Path(path)
        self.faults = frozenset(faults)
        if self.faults - FAULTS:
            raise ValueError('Unknown fault; fault injection is restricted to reference tests')
        if create:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open('xb'):
                pass
            with self.connection() as db:
                db.executescript('''
                CREATE TABLE actors(id TEXT PRIMARY KEY, active INTEGER NOT NULL, epoch INTEGER NOT NULL);
                CREATE TABLE grants(actor TEXT, permission TEXT, scope TEXT, PRIMARY KEY(actor,permission,scope));
                CREATE TABLE sessions(id TEXT PRIMARY KEY, actor TEXT, epoch INTEGER NOT NULL);
                CREATE TABLE parts(id TEXT PRIMARY KEY, book INTEGER CHECK(book>=0), physical INTEGER CHECK(physical>=0), reserved INTEGER CHECK(reserved>=0 AND reserved<=book));
                CREATE TABLE records(id TEXT PRIMARY KEY, class TEXT, payload TEXT, policy TEXT, state TEXT);
                CREATE TABLE holds(record_id TEXT, hold_id TEXT, active INTEGER NOT NULL CHECK(active IN (0,1)), PRIMARY KEY(record_id,hold_id));
                CREATE TABLE policies(id TEXT PRIMARY KEY, reviewed INTEGER, not_before_tick INTEGER, basis TEXT);
                CREATE TABLE copies(record_id TEXT, kind TEXT, payload TEXT, PRIMARY KEY(record_id,kind));
                CREATE TABLE tombstones(record_id TEXT PRIMARY KEY, txn INTEGER);
                CREATE TABLE movements(txn INTEGER, part TEXT, kind TEXT, quantity INTEGER);
                CREATE TABLE dispositions(txn INTEGER, record_id TEXT);
                CREATE TABLE copy_dispositions(txn INTEGER, record_id TEXT, kind TEXT);
                CREATE TABLE audit(txn INTEGER, actor TEXT, action TEXT, target TEXT);
                CREATE TABLE requests(id TEXT PRIMARY KEY, signature TEXT, result TEXT);
                CREATE TABLE transactions(seq INTEGER PRIMARY KEY, utc TEXT, event TEXT NOT NULL);
                ''')
                for actor in ('ADMIN', 'TECH', 'STORES', 'STEWARD', 'OBSERVER'):
                    db.execute('INSERT INTO actors VALUES(?,1,0)', (actor,))
                permissions = {
                    'ADMIN': ['access.admin', 'policy.fixture', 'record.read', 'record.hold', 'record.dispose', 'stock.read', 'stock.adjust', 'stock.issue', 'stock.reserve'],
                    'TECH': ['record.read', 'stock.read', 'stock.issue', 'stock.reserve'],
                    'STORES': ['stock.read', 'stock.adjust', 'stock.issue', 'stock.reserve'],
                    'STEWARD': ['record.read', 'record.hold', 'record.dispose', 'policy.fixture'],
                    'OBSERVER': []}
                for actor, grants in permissions.items():
                    for permission in grants:
                        scope = 'workshop' if actor == 'TECH' and permission == 'record.read' else '*'
                        db.execute('INSERT INTO grants VALUES(?,?,?)', (actor, permission, scope))
                db.executemany('INSERT INTO parts VALUES(?,?,?,0)', [('P-DEMO-001', 5, 4), ('P-RACE', 1, 1)])
                db.executemany('INSERT INTO records VALUES(?,?,?,?,?)', [
                    ('R-DEMO-001', 'workshop', 'dummy repair record', None, 'active'),
                    ('R-DISPOSE', 'workshop', 'dummy disposition payload', None, 'active'),
                    ('R-OTHER', 'restricted', 'dummy other-class payload', None, 'active'),
                    ('R-EMPTY', 'workshop', '', None, 'active')])
                db.executemany('INSERT INTO holds VALUES(?,?,1)',
                               [(record, DEFAULT_HOLD_ID) for record in ('R-DEMO-001','R-DISPOSE')])
                for record_id in ('R-DEMO-001', 'R-DISPOSE', 'R-OTHER', 'R-EMPTY'):
                    for kind in ('primary', 'export', 'backup'):
                        db.execute('INSERT INTO copies VALUES(?,?,?)', (record_id, kind, 'dummy '+kind+' payload'))
                db.execute('PRAGMA user_version='+str(SCHEMA_VERSION))
        elif not self.path.is_file():
            raise ValueError('Prototype database does not exist')
        with self.connection() as db:
            if db.execute('PRAGMA user_version').fetchone()[0] != SCHEMA_VERSION:
                raise ValueError('Unsupported prototype database schema; create a fresh dummy database, not an implicit migration')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA busy_timeout=10000')
        try:
            yield db
        finally:
            db.close()

    def session(self, actor):
        """Dummy local identity selection, not an authentication mechanism."""
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            person = db.execute('SELECT * FROM actors WHERE id=?', (actor,)).fetchone()
            if person is None or not person['active']:
                db.rollback()
                raise ValueError('Inactive or unknown dummy actor')
            token = uuid.uuid4().hex
            db.execute('INSERT INTO sessions VALUES(?,?,?)', (token, actor, person['epoch']))
            db.commit()
            return token

    @staticmethod
    def _security(db, token):
        row = db.execute('SELECT s.actor,s.epoch AS session_epoch,a.epoch,a.active FROM sessions s JOIN actors a ON a.id=s.actor WHERE s.id=?', (token,)).fetchone()
        if row is None:
            return {'actor': None, 'session_valid': False, 'revoked': False, 'grants': []}
        value = dict(row)
        value['session_valid'] = bool(row['active'] and row['session_epoch'] == row['epoch'])
        value['revoked'] = not value['session_valid']
        value['grants'] = [dict(x) for x in db.execute('SELECT permission,scope FROM grants WHERE actor=? ORDER BY permission,scope', (row['actor'],))]
        return value

    @staticmethod
    def permitted(security, permission, scope='*'):
        return bool(security['session_valid'] and any(g['permission'] == permission and g['scope'] in ('*', scope) for g in security['grants']))

    @staticmethod
    def _snapshot(db, token, part, record, txn):
        def one(query, args):
            r = db.execute(query, args).fetchone()
            return dict(r) if r is not None else None
        value = {'security': Store._security(db, token), 'part': one('SELECT * FROM parts WHERE id=?', (part,)),
                 'record': one('SELECT r.*, EXISTS(SELECT 1 FROM holds h WHERE h.record_id=r.id AND h.active=1) AS held FROM records r WHERE r.id=?', (record,))}
        value['holds'] = [dict(r) for r in db.execute(
            'SELECT record_id,hold_id,active FROM holds WHERE record_id=? ORDER BY hold_id', (record,))]
        policy = value['record']['policy'] if value['record'] else None
        value['policy'] = one('SELECT * FROM policies WHERE id=?', (policy,))
        value['copies'] = [dict(r) for r in db.execute('SELECT kind FROM copies WHERE record_id=? ORDER BY kind', (record,))]
        value['tombstone'] = one('SELECT * FROM tombstones WHERE record_id=?', (record,))
        for table in ('movements', 'dispositions', 'copy_dispositions', 'audit'):
            value[table] = [dict(r) for r in db.execute('SELECT * FROM '+table+' WHERE txn=?', (txn,))]
        return value

    @staticmethod
    def _capture_state(state):
        """Keep decision evidence without making another content-bearing copy."""
        value=dict(state)
        if value['record'] is not None:
            value['record']=dict(value['record'])
            payload=value['record'].pop('payload')
            value['record']['payload_present']=payload is not None
        return value

    def transact(self, token, action, *, part=None, record=None, quantity=None,
                 request_id=None, subject=None, scope=None, not_before_tick=None, hold_id=None):
        if action not in {'issue', 'reserve', 'issue_reserved', 'adjust', 'count', 'read', 'revoke', 'grant_read', 'hold', 'release_hold', 'set_fixture_policy', 'dispose', 'restore'}:
            raise ValueError('Unknown prototype operation')
        if action in ('issue', 'reserve', 'issue_reserved') and (type(quantity) is not int or quantity <= 0):
            raise ValueError('Quantity must be a positive integer')
        if action == 'set_fixture_policy' and (type(not_before_tick) is not int or not_before_tick < 0):
            raise ValueError('Fixture policy needs a nonnegative logical eligibility tick')
        if action in ('hold','release_hold'):
            hold_id = DEFAULT_HOLD_ID if hold_id is None else hold_id
            if type(hold_id) is not str or not HOLD_ID.fullmatch(hold_id):
                raise ValueError('Hold identity needs 1..64 ASCII letters/digits or _.:-, beginning with a letter/digit')
        elif hold_id is not None:
            raise ValueError('A hold identity is only valid for hold/release_hold')
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                txn = db.execute('SELECT COALESCE(MAX(seq),0)+1 FROM transactions').fetchone()[0]
                before = self._snapshot(db, token, part, record, txn)
                security = before['security'];actor = security['actor']
                result = {'outcome': 'denied', 'reason': 'not_authorized'}
                stock = before['part'];item = before['record']
                permission = 'stock.adjust' if action == 'adjust' else 'stock.reserve' if action == 'reserve' else 'stock.issue'
                stock_allowed = self.permitted(security, permission)
                if action.startswith('issue') and 'ignore_issue_permission' in self.faults:
                    stock_allowed = True
                signature = canonical({'actor': actor, 'action': action, 'part': part, 'quantity': quantity})
                cached = db.execute('SELECT * FROM requests WHERE id=?', (request_id,)).fetchone() if request_id else None
                if action in ('issue', 'reserve', 'issue_reserved', 'adjust', 'count'):
                    if stock is None:
                        result = {'outcome': 'denied', 'reason': 'unknown_part'}
                    elif action == 'count':
                        if self.permitted(security,'stock.read'):
                            result = {'outcome': 'observed', 'book': stock['book'], 'physical': stock['physical'], 'reserved': stock['reserved']}
                    elif not stock_allowed:
                        pass
                    elif cached:
                        result = {'outcome': 'replay' if cached['signature'] == signature else 'denied', 'reason': 'idempotent_replay' if cached['signature'] == signature else 'request_id_conflict'}
                    elif action == 'adjust':
                        if stock['physical'] < stock['reserved']:
                            result = {'outcome': 'denied', 'reason': 'reserved_stock_conflict'}
                        elif stock['physical'] == stock['book']:
                            result = {'outcome': 'no_change', 'reason': 'already_reconciled'}
                        else:
                            db.execute('UPDATE parts SET book=physical WHERE id=?', (part,))
                            db.execute('INSERT INTO movements VALUES(?,?,?,?)', (txn, part, 'adjust', stock['physical']-stock['book']))
                            if 'omit_adjustment_audit' not in self.faults:
                                db.execute('INSERT INTO audit VALUES(?,?,?,?)', (txn, actor, 'adjust', part))
                            result = {'outcome': 'committed'}
                    elif stock['book'] != stock['physical'] and 'issue_on_mismatch' not in self.faults:
                        result = {'outcome': 'denied', 'reason': 'stock_discrepancy'}
                    elif action == 'reserve':
                        if quantity > stock['book']-stock['reserved']:
                            result = {'outcome': 'denied', 'reason': 'insufficient_available'}
                        else:
                            db.execute('UPDATE parts SET reserved=reserved+? WHERE id=?', (quantity, part))
                            db.execute('INSERT INTO movements VALUES(?,?,?,?)', (txn, part, 'reserve', quantity))
                            result = {'outcome': 'committed'}
                    else:
                        available = stock['reserved'] if action == 'issue_reserved' else stock['book']-stock['reserved']
                        if quantity > available or quantity > stock['physical']:
                            result = {'outcome': 'denied', 'reason': 'insufficient_available'}
                        else:
                            reserved_delta = quantity if action == 'issue_reserved' else 0
                            db.execute('UPDATE parts SET book=book-?,physical=physical-?,reserved=reserved-? WHERE id=?', (quantity, quantity, reserved_delta, part))
                            db.execute('INSERT INTO movements VALUES(?,?,?,?)', (txn, part, 'issue', quantity))
                            result = {'outcome': 'committed'}
                    if request_id and not cached and result['outcome'] == 'committed':
                        db.execute('INSERT INTO requests VALUES(?,?,?)', (request_id, signature, canonical(result)))
                elif action == 'read':
                    allowed = bool(item and self.permitted(security, 'record.read', item['class']))
                    if 'ignore_revocation' in self.faults and item:
                        allowed = any(g['permission'] == 'record.read' and g['scope'] in ('*',item['class']) for g in security['grants'])
                    if 'ignore_read_scope' in self.faults and security['session_valid']:
                        allowed = True
                    if allowed and item['payload'] is not None:
                        result = {'outcome': 'served', 'payload': item['payload']}
                    elif item and item['payload'] is None:
                        result = {'outcome': 'denied', 'reason': 'disposed_or_absent'}
                elif action in ('revoke', 'grant_read'):
                    if self.permitted(security, 'access.admin'):
                        target = db.execute('SELECT * FROM actors WHERE id=?', (subject,)).fetchone()
                        if target is None:
                            result = {'outcome': 'denied', 'reason': 'unknown_actor'}
                        else:
                            db.execute('UPDATE actors SET active=?,epoch=epoch+1 WHERE id=?', (int(action=='grant_read'), subject))
                            if action == 'grant_read':
                                if not scope:
                                    raise ValueError('A dummy record class is required for a grant')
                                # A read-only regrant does not restore unrelated old duties.
                                db.execute('DELETE FROM grants WHERE actor=?', (subject,))
                                db.execute('INSERT OR IGNORE INTO grants VALUES(?,?,?)', (subject, 'record.read', scope))
                            db.execute('INSERT INTO audit VALUES(?,?,?,?)', (txn, actor, action, subject))
                            result = {'outcome': 'committed'}
                elif action in ('hold', 'release_hold'):
                    if item and self.permitted(security, 'record.hold', item['class']):
                        existing = db.execute('SELECT active FROM holds WHERE record_id=? AND hold_id=?', (record,hold_id)).fetchone()
                        if item['payload'] is None:
                            result = {'outcome':'denied','reason':'record_disposed'}
                        elif action == 'hold' and existing is not None:
                            result = {'outcome':'no_change' if existing['active'] else 'denied',
                                      'reason':'already_held' if existing['active'] else 'hold_id_reused'}
                        elif action == 'release_hold' and existing is None:
                            result = {'outcome':'denied','reason':'unknown_hold'}
                        elif action == 'release_hold' and not existing['active']:
                            result = {'outcome':'no_change','reason':'already_released'}
                        elif action == 'hold' and len(before['holds']) >= HOLD_LIMIT:
                            result = {'outcome':'denied','reason':'hold_limit'}
                        else:
                            if action == 'hold':
                                db.execute('INSERT INTO holds VALUES(?,?,1)', (record,hold_id))
                            elif 'release_all_holds' in self.faults:
                                db.execute('UPDATE holds SET active=0 WHERE record_id=?', (record,))
                            else:
                                db.execute('UPDATE holds SET active=0 WHERE record_id=? AND hold_id=?', (record,hold_id))
                            db.execute('INSERT INTO audit VALUES(?,?,?,?)', (txn, actor, action, record))
                            result = {'outcome': 'committed'}
                elif action == 'set_fixture_policy':
                    if item and self.permitted(security, 'policy.fixture', item['class']):
                        policy = 'DUMMY-POLICY-'+record
                        db.execute('INSERT OR REPLACE INTO policies VALUES(?,1,?,?)', (policy, not_before_tick, 'dummy logical eligibility only; not an adopted retention period'))
                        db.execute('UPDATE records SET policy=? WHERE id=?', (policy, record))
                        db.execute('INSERT INTO audit VALUES(?,?,?,?)', (txn, actor, action, record))
                        result = {'outcome': 'committed'}
                elif action == 'dispose':
                    if item and item['payload'] is None:
                        result = {'outcome': 'no_change', 'reason': 'already_disposed'}
                    elif item and self.permitted(security, 'record.dispose', item['class']):
                        policy = before['policy']
                        if item['held'] and 'ignore_hold' not in self.faults:
                            result = {'outcome': 'denied', 'reason': 'retention_hold'}
                        elif not policy or not policy['reviewed']:
                            result = {'outcome': 'denied', 'reason': 'retention_basis_unknown'}
                        elif txn < policy['not_before_tick']:
                            result = {'outcome': 'denied', 'reason': 'fixture_eligibility_not_reached'}
                        else:
                            db.execute("UPDATE records SET payload=NULL,state='disposed' WHERE id=?", (record,))
                            for copy in before['copies']:
                                if copy['kind'] == 'export' and 'leave_export' in self.faults:
                                    continue
                                db.execute('DELETE FROM copies WHERE record_id=? AND kind=?', (record, copy['kind']))
                                db.execute('INSERT INTO copy_dispositions VALUES(?,?,?)', (txn, record, copy['kind']))
                            db.execute('INSERT INTO tombstones VALUES(?,?)', (record, txn))
                            db.execute('INSERT INTO dispositions VALUES(?,?)', (txn, record))
                            if 'omit_disposition_audit' not in self.faults:
                                db.execute('INSERT INTO audit VALUES(?,?,?,?)', (txn, actor, 'dispose', record))
                            result = {'outcome': 'committed'}
                elif action == 'restore':
                    if before['tombstone']:
                        result = {'outcome': 'denied', 'reason': 'disposition_tombstone'}
                    else:
                        result = {'outcome': 'denied', 'reason': 'arbitrary_restore_unsupported'}
                after = self._snapshot(db, token, part, record, txn)
                captured_result=dict(result)
                captured_result['returned_payload_present']='payload' in captured_result
                captured_result.pop('payload',None)
                event = {'sequence': txn, 'utc': datetime.now(timezone.utc).isoformat(), 'action': action,
                         'actor': actor, 'part_id': part, 'record_id': record, 'request_id': request_id, 'hold_id': hold_id,
                         'before': self._capture_state(before), 'after': self._capture_state(after), 'result': captured_result}
                db.execute('INSERT INTO transactions VALUES(?,?,?)', (txn, event['utc'], canonical(event)))
                db.commit()
                return result
            except BaseException:
                db.rollback()
                raise

    def events(self):
        with self.connection() as db:
            return [json.loads(r[0]) for r in db.execute('SELECT event FROM transactions ORDER BY seq')]


from .repair_reuse_observer import observe


def exercise(store):
    """Actual dummy commands; expected responses live in separate tests."""
    admin=store.session('ADMIN');tech=store.session('TECH');stock=store.session('STORES');steward=store.session('STEWARD');observer=store.session('OBSERVER')
    store.transact(stock,'issue',part='P-DEMO-001',quantity=1)
    store.transact(tech,'adjust',part='P-DEMO-001')
    store.transact(stock,'adjust',part='P-DEMO-001')
    store.transact(stock,'reserve',part='P-DEMO-001',quantity=2)
    store.transact(tech,'issue',part='P-DEMO-001',quantity=3)
    store.transact(tech,'issue',part='P-DEMO-001',quantity=1,request_id='ISSUE-ONE')
    store.transact(tech,'issue',part='P-DEMO-001',quantity=1,request_id='ISSUE-ONE')
    store.transact(tech,'issue',part='P-DEMO-001',quantity=2,request_id='ISSUE-ONE')
    store.transact(stock,'issue_reserved',part='P-DEMO-001',quantity=1)
    store.transact(tech,'read',record='R-DEMO-001')
    store.transact(admin,'revoke',subject='TECH')
    store.transact(tech,'read',record='R-DEMO-001')
    store.transact(admin,'grant_read',subject='TECH',scope='workshop')
    store.transact(tech,'read',record='R-DEMO-001')
    fresh=store.session('TECH')
    store.transact(fresh,'read',record='R-OTHER')
    store.transact(fresh,'read',record='R-EMPTY')
    store.transact(observer,'issue',part='P-RACE',quantity=1)
    store.transact(steward,'dispose',record='R-OTHER')
    store.transact(stock,'dispose',record='R-DISPOSE')
    store.transact(steward,'set_fixture_policy',record='R-DISPOSE',not_before_tick=20)
    store.transact(steward,'dispose',record='R-DISPOSE')
    store.transact(steward,'release_hold',record='R-DISPOSE')
    store.transact(stock,'dispose',record='R-DISPOSE')
    store.transact(steward,'dispose',record='R-DISPOSE')
    store.transact(steward,'restore',record='R-DISPOSE')
    store.transact(steward,'read',record='R-DISPOSE')
    store.transact(steward,'set_fixture_policy',record='R-OTHER',not_before_tick=0)
    store.transact(steward,'hold',record='R-OTHER',hold_id='NOTICE-A')
    store.transact(steward,'hold',record='R-OTHER',hold_id='NOTICE-B')
    store.transact(steward,'release_hold',record='R-OTHER',hold_id='NOTICE-A')
    store.transact(steward,'dispose',record='R-OTHER')
    store.transact(steward,'release_hold',record='R-OTHER',hold_id='NOTICE-B')
    store.transact(steward,'dispose',record='R-OTHER')
    return store.events()
