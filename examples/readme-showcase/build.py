#!/usr/bin/env python3
"""Source-bound explanatory previews of existing synthetic engineering examples."""
import argparse
import copy
from fractions import Fraction
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CASE = ROOT / 'examples/engineering-gallery/water-sampling'
TOOL = ROOT / 'examples/tool-library'
sys.path.insert(0, str(ROOT))
from verifier import verify
from verifier.sysml import check_sysml
from verifier.visual_style import font_css, text_width, wrap_text


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def put(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clean(v) for v in value]
    if isinstance(value, str):
        return value.replace(str(ROOT) + '/', '')
    return value


def source_paths():
    names = ['station.sysml', 'scope.json', 'view-profile.json', 'semantic-ledger.json', 'finite-scenarios.json', 'finite-scope.json', 'build.py', 'evidence-pass.json', 'evidence-late.json', 'evidence-over-limit.json']
    names += ['generated/' + n + '.json' for n in ['shape-concept', 'native-pass', 'native-late', 'native-over-limit', 'finite-disabled-release']]
    return [CASE / n for n in names] + [TOOL / n for n in ['input.md', 'README.md', 'result/concept.json', 'result/concept-brief.md', 'result/capacity_check.py', 'result/capacity-check.txt']] + [ROOT / 'docs/gallery-method.md', ROOT/'skills/develop-system-concept/scripts/concept.py']


def pins(paths):
    return {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}


def acquire():
    shape = check_sysml(str(CASE / 'station.sysml'), syntax_only=True, kind='concept', view_profile=read(CASE / 'view-profile.json'))
    if shape['status'] != 'pass' or clean(shape) != read(CASE / 'generated/shape-concept.json'):
        raise ValueError('Current parsed model differs from the published synthetic shape report')
    inventory = shape['inventory']
    doc = next(d for d in inventory['documents'] if d.get('name') == 'cseViews')
    views = json.loads(doc['body'].split('CSE-VIEWS/1.0', 1)[1])['views']
    reports = {}
    for name in ('pass', 'late', 'over-limit'):
        report = check_sysml(str(CASE / 'station.sysml'), manifest=read(CASE / 'scope.json'), evidence=read(CASE / ('evidence-' + name + '.json')), review=True)
        if clean(report) != read(CASE / ('generated/native-' + name + '.json')):
            raise ValueError('Recomputed monitor result differs: ' + name)
        reports[name] = clean(report)
    ledger = read(CASE / 'semantic-ledger.json')
    finite = copy.deepcopy(read(CASE / 'finite-scenarios.json'))
    finite['scenarios']['FS_NOMINAL']['steps']['FN_HANDOFF']['guard'] = {'all': [
        {'ref': 'labelReadable', 'op': '==', 'value': True}, {'ref': 'labelReadable', 'op': '==', 'value': False}]}
    # The same existing negative-control mutation; verify its semantic digest and full result.
    failed = verify(finite, review=True, manifest=read(CASE / 'finite-scope.json'))
    if failed != read(CASE / 'generated/finite-disabled-release.json'):
        raise ValueError('Contradictory-guard reproduction differs from the existing negative control')
    # Execute a byte-identical temporary copy because the original script writes a report beside itself.
    with tempfile.TemporaryDirectory(prefix='showcase-capacity-', dir=ROOT / '.cache') as temporary:
        script = Path(temporary) / 'capacity_check.py'
        script.write_bytes((TOOL / 'result/capacity_check.py').read_bytes())
        proc = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, encoding='utf-8', check=True)
        if proc.stdout != (TOOL / 'result/capacity-check.txt').read_text(encoding='utf-8'):
            raise ValueError('Recomputed conditional arithmetic differs from its existing report')
    legacy = subprocess.run([sys.executable, str(ROOT/'skills/develop-system-concept/scripts/concept.py'), 'check', str(TOOL/'result/concept.json'), '--review'], capture_output=True, text=True, encoding='utf-8', check=True)
    legacy_report = json.loads(legacy.stdout)
    if legacy_report['structural'] != 'pass' or legacy_report['review_completeness'] != 'pass':
        raise ValueError('Existing legacy concept structural review failed')
    return {'views': {v['id']: v for v in views}, 'inventory': clean(inventory), 'documentary_ledger': ledger,
            'reports': reports, 'evidence': {n: read(CASE / ('evidence-' + n + '.json')) for n in ('pass', 'late', 'over-limit')},
            'legacy_report': legacy_report, 'blocked_fixture': finite, 'blocked_report': failed, 'tool_concept': read(TOOL / 'result/concept.json')}


class Drawing:
    def __init__(self, key, title, subtitle, height):
        self.key, self.height = key, height
        self.parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="800" height="{height}" viewBox="0 0 800 {height}" role="img" aria-labelledby="title description">', f'<title id="title">{escape(title)}</title><desc id="description">{escape(subtitle)} Source-bound synthetic explanatory presentation, not a native SysML graphical view.</desc>', '<style>' + font_css() + '</style>', '<rect width="800" height="100%" fill="#faf9f5"/>', '<g font-family="Space Grotesk" fill="#182b3b">']
        self.text('SYNTHETIC EXAMPLE  /  ' + key[:2], 32, 35, 18, color='#486171')
        self.text(title, 32, 83, 31, weight=700)
        self.lines(subtitle, 32, 120, 22, 736, color='#486171')
        self.text_bounds = []
    def text(self, text, x, y, size=22, weight=400, color='#182b3b', box=None):
        attrs = f' data-box="{box}"' if box else ''
        self.parts.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}"{attrs}>{escape(str(text))}</text>')
    def lines(self, value, x, y, size=22, width=700, weight=400, color='#182b3b', box=None, leading=None):
        lines = wrap_text(value, width, size, 'Space Grotesk', weight)
        for i, line in enumerate(lines):
            self.text(line.rstrip(), x, y + i * (leading or size * 1.3), size, weight, color, box)
        return len(lines) * (leading or size * 1.3)
    def box(self, x, y, w, h, fill='#ffffff', stroke='#b4c2cb', key=None):
        attr = f' id="{key}"' if key else ''
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}"{attr}/>')
    def line(self, x1, y1, x2, y2, color='#486171', dash=None, width=2):
        attr = f' stroke-dasharray="{dash}"' if dash else ''
        self.parts.append(f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}"{attr}/>')
    def circle(self, x, y, radius=7, fill='#faf9f5', stroke='#235e7b'):
        self.parts.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    def footer(self, line1, line2):
        self.line(32, self.height-83, 768, self.height-83, '#b4c2cb')
        self.text(line1, 32, self.height-53, 18)
        self.text(line2, 32, self.height-25, 18, color='#486171')
    def svg(self):
        return '\n'.join(self.parts + ['</g></svg>\n'])


def handoffs(facts, selection):
    view = facts['views']['SQ_NOMINAL' if selection['id'].startswith('01') else 'SQ_RECOVERY']
    d = Drawing(selection['id'], selection['display_title'], 'Four existing handoffs, in their recorded order.', 740)
    for i, exchange in enumerate(view['exchanges']):
        y = 170 + 112*i
        d.box(32, y, 736, 96, key='row'+str(i))
        d.circle(64, y+29, 18, fill='#e4edf2')
        d.text(str(i+1), 58, y+36, 22, weight=700)
        d.text(exchange['from'].capitalize() + '  to  ' + exchange['to'].capitalize(), 101, y+32, 22, weight=700, box='row'+str(i))
        d.lines(exchange['message'], 101, y+65, 22, 635, box='row'+str(i))
    d.footer(view['id'] + '  /  E1 through E4; exact messages in source', 'Documentary exchanges; no timing, UI or executable control flow inferred.')
    return d.svg()


def deadlines(facts, selection):
    d = Drawing(selection['id'], selection['display_title'], 'Each ID has its own inclusive two-second deadline.', 810)
    origin, span = 138, 580
    xpos = lambda value: origin + float(Fraction(value) * Fraction(span, 5) * 2)
    # The axis is absolute time 0..2.5 seconds; derive each deadline from its trigger.
    for panel, name in enumerate(('pass', 'late')):
        top = 170 + panel * 262
        report = facts['reports'][name]['results']['R_CORRELATION__correlation']
        deadline = Fraction(report['deadline_ms']) / 1000
        status = report['check']['status'].upper()
        d.box(32, top, 736, 238, fill='#f0f5f0' if name=='pass' else '#fbf0ed')
        d.text('Within deadline' if name=='pass' else 'W001 receipt arrives too late', 52, top+36, 24, weight=700)
        d.text(status, 667, top+36, 22, weight=700, color='#285a43' if name=='pass' else '#9b382d')
        events = facts['evidence'][name]['events']
        for row, ident in enumerate(('W001', 'W002')):
            y = top+90+row*80
            trigger = next(e for e in events if e['correlationId']==ident and e['event'].endswith('containerPresented'))
            response = next(e for e in events if e['correlationId']==ident and e['event'].endswith('receiptIssued'))
            start, end = Fraction(trigger['time']), Fraction(response['time'])
            due = start+deadline
            d.text(ident, 52, y+7, 22, weight=700)
            d.line(origin, y, xpos('2.5'), y, '#b4c2cb')
            d.line(xpos(str(float(due))), y-22, xpos(str(float(due))), y+22, '#486171', dash='4 4')
            d.line(xpos(trigger['time']), y, xpos(response['time']), y, '#285a43' if end<=due else '#9b382d', width=4)
            d.circle(xpos(trigger['time']), y, fill='#faf9f5')
            d.circle(xpos(response['time']), y, fill='#285a43' if end<=due else '#9b382d', stroke='#285a43' if end<=due else '#9b382d')
            d.text(trigger['time']+' s', xpos(trigger['time'])-8, y+31, 18)
            d.text(response['time']+' s', xpos(response['time'])-10, y-29, 18)
            d.text('by '+str(float(due)).rstrip('0').rstrip('.')+' s', xpos(str(float(due)))-72, y+31, 18)
        d.text('Dashed mark = each ID\'s deadline', 52, top+225, 18, color='#486171')
    d.text('Open dot: container presented. Filled dot: receipt issued.', 32, 704, 20)
    d.footer('R_CORRELATION  /  W002 returns before W001, correctly paired by ID.', 'Synthetic event evidence; a passing trace is not an implementation claim.')
    return d.svg()



def responsibilities(facts, selection):
    d = Drawing(selection['id'], selection['display_title'], 'Selected responsibilities, kept distinct from participant names.', 760)
    allocations = {(a['function'], a['performer']) for a in facts['documentary_ledger']['documentary_allocations']}
    actions = {n['id']: n['element'] for n in facts['views']['FT_STATION']['nodes']}
    parts = {p['qualified_name'] for p in facts['inventory']['parts']}
    cards = [('Operator', [('F11','Identify container'),('F22','Reconcile label')], 'WaterSampling::operator'),
             ('Station', [('F12','Record receipt'),('F32','Record custody transfer')], 'WaterSampling::station'),
             ('Custodian', [('F42','Inspect and restore')], 'WaterSampling::custodian'),
             ('Courier', [], 'WaterSampling::courier')]
    for i, (role, assigned, qualified) in enumerate(cards):
        if qualified not in parts:
            raise ValueError('Unknown responsibility participant')
        x, y = 32+(i%2)*384, 170+(i//2)*244
        key='role'+str(i)
        d.box(x,y,352,215,key=key)
        d.text(role,x+20,y+38,26,weight=700,box=key)
        if assigned:
            offset=77
            for fid,label in assigned:
                if label != selection['presentation_labels'][fid]:
                    raise ValueError('Documentary function label drift')
                if (fid,qualified) not in allocations or fid not in actions:
                    raise ValueError('Responsibility was not recorded in the existing ledger')
                offset += d.lines(label,x+20,y+offset,22,312,box=key)
                d.text(fid,x+20,y+offset,18,color='#486171',box=key)
                offset+=36
            if role=='Custodian':
                d.lines('Operational release remains a separate decision.',x+20,y+145,18,312,box=key)
        else:
            if any(a['performer']==qualified for a in facts['documentary_ledger']['documentary_allocations']):
                raise ValueError('Courier allocation scope changed')
            d.lines('Pickup participant; no function allocation is recorded.',x+20,y+80,22,312,box=key)
            d.text('SQ_NOMINAL',x+20,y+183,18,color='#486171',box=key)
    d.footer('Five of twelve documentary allocations shown; full ledger is linked.', 'Assignments are fictional illustrations, not native allocations or proof.')
    return d.svg()


def traces(facts, selection):
    d = Drawing(selection['id'], selection['display_title'], 'Read the recorded relationship, including its direction.', 1000)
    aliases=selection['presentation_labels']
    actual={i['id']:k for k in ('requirements','concerns','use_cases') for i in facts['inventory'][k]}
    links=facts['documentary_ledger']['typed_traces']
    expected={'justifies':('requirements','concerns'),'addresses':('use_cases','requirements')}
    for t in links:
        if (actual[t['from']],actual[t['to']])!=expected[t['kind']]:
            raise ValueError('Trace endpoint type mismatch')
    for group,kind in enumerate(('justifies','addresses')):
        start=190+group*358
        d.text('Requirement to need' if group==0 else 'Scenario to requirement',32,start-20,24,weight=700)
        for i,trace in enumerate(t for t in links if t['kind']==kind):
            y=start+i*96
            for side,key in [(32,'from'),(468,'to')]:
                card='trace'+str(group)+str(i)+key
                d.box(side,y,300,84,key=card)
                d.text(trace[key],side+16,y+27,18,color='#486171',box=card)
                d.lines(aliases[trace[key]],side+16,y+59,22,268,box=card)
            d.text(kind,349,y+30,18,color='#486171')
            d.line(344,y+59,456,y+59)
            d.line(446,y+52,456,y+59)
            d.line(446,y+66,456,y+59)
    d.lines('No scenario link to R_ELAPSED is recorded in this ledger.',32,887,20,736,color='#486171')
    d.footer('All six source links shown; layout adds no new relationships.', 'A typed link is not evidence that a need or requirement is satisfied.')
    return d.svg()


def quantity(facts, selection):
    d=Drawing(selection['id'],selection['display_title'],'Compare the same recorded receipt with one changed observation.',790)
    base='WaterSampling::station::'
    for row,name in enumerate(('pass','over-limit')):
        y=170+row*212
        obs=facts['evidence'][name]['observations'][3]
        report=facts['reports'][name]['results']['R_ELAPSED__duration']
        clause=report['compiled_clause']
        match=re.fullmatch(r'Whenever unit.receiptRecorded = true, unit shall always satisfy unit.processingElapsed <= (\d+) second\.',clause)
        if not match or obs[base+'receiptRecorded'] is not True:
            raise ValueError('Receipt-time quantity meaning changed')
        limit=int(match[1]);value=obs[base+'processingElapsed']
        state=report['check']['status'].upper()
        for check in ('R_RECORD__receipt','R_CORRELATION__correlation'):
            if facts['reports'][name]['results'][check]['check']['status']!='pass':
                raise ValueError('Quantity comparison no longer isolates the one clause')
        d.box(32,y,736,186,fill='#f0f5f0' if state=='PASS' else '#fbf0ed')
        d.text(str(value)+' seconds observed at recorded receipt',52,y+37,24,weight=700)
        d.text(state,665,y+37,22,weight=700,color='#285a43' if state=='PASS' else '#9b382d')
        origin=140;factor=90
        d.box(origin,y+78,value*factor,28,fill='#3c7057' if state=='PASS' else '#a3483b',stroke='none')
        for tick in (0,2,4,6):
            d.text(str(tick)+' s',origin+factor*tick-6,y+137,18)
        d.line(origin+factor*limit,y+65,origin+factor*limit,y+116,'#486171',dash='4 4')
        d.text(str(limit)+' s limit',origin+factor*limit-26,y+166,18,color='#486171')
    annotation=next(x['body'] for x in facts['inventory']['documents'] if x.get('name')=='cseType' and x['owner']=='WaterSampling::Station::processingElapsed')
    domain=re.fullmatch(r'CSE-INT/2\.0\s+range (-?\d+) (-?\d+) scale ([0-9.]+) unit (\w+)\s*',annotation)
    if not domain:
        raise ValueError('Quantity domain annotation changed')
    low,high,scale,unit=domain.groups()
    d.lines(f'Both values are valid in the declared {low} to {high} {unit} domain.',32,620,22,736)
    d.lines('Receipt and correlated-event checks still pass in both traces.',32,656,22,736)
    d.footer(f'R_ELAPSED  /  sample 3, receiptRecorded = true; scale {scale} {unit}.', 'Observed values, not an inferred clock or a real-system performance claim.')
    return d.svg()


def blocked(facts,selection):
    d=Drawing(selection['id'],selection['display_title'],'A deliberately broken finite fixture, with actual checker findings.',820)
    scenario=facts['blocked_fixture']['scenarios']['FS_NOMINAL']
    steps=scenario['steps']
    if steps['FN_HANDOFF']['guard']!={'all':[{'ref':'labelReadable','op':'==','value':True},{'ref':'labelReadable','op':'==','value':False}]}:
        raise ValueError('Blocked guard mutation differs')
    for i,node in enumerate(('received','recorded','done')):
        x=32+i*268
        d.box(x,190,200,96,fill='#ffffff' if i<2 else '#f3f3f0',stroke='#b4c2cb')
        d.text(node,x+24,245,26,weight=700)
    for x1,x2,color,dash in [(232,300,'#486171',None),(500,568,'#9b382d','5 4')]:
        d.line(x1,238,x2,238,color,dash)
        d.line(x2-9,231,x2,238,color)
        d.line(x2-9,245,x2,238,color)
    d.line(526,220,543,256,'#9b382d',width=3)
    d.line(543,220,526,256,'#9b382d',width=3)
    d.text('FN_RECORD',40,320,18,color='#486171')
    d.text('FN_HANDOFF blocked',450,320,18,color='#9b382d')
    d.box(32,355,736,137,fill='#fbf0ed')
    d.text('The handoff requires both:',52,390,24,weight=700)
    d.text('labelReadable == true',52,430,22)
    d.text('AND labelReadable == false',52,468,22)
    findings=facts['blocked_report']['findings']
    guard=next(f for f in findings if f['rule']=='step-reachability' and 'FN_HANDOFF' in f['ids'])
    progress=next(f for f in findings if f['rule']=='progress' and 'FS_NOMINAL' in f['ids'])
    d.box(32,530,736,145)
    d.text('FAIL  /  '+guard['explanation'],52,570,24,weight=700,color='#9b382d')
    d.lines(progress['explanation']+'.',52,612,22,696)
    d.text('Counterexample node: '+progress['evidence']['node'],52,651,20,color='#486171')
    d.text('The arrow exists; its guard prevents execution.',32,712,22)
    d.footer('FS_NOMINAL  /  exact existing contradictory-guard negative control.', 'Separate finite model; no SysML conversion or physical failure inferred.')
    return d.svg()


def tools(facts,selection):
    d=Drawing(selection['id'],selection['display_title'],'Two existing proposals; costs and outcomes remain unverified.',890)
    model=facts['tool_concept']
    if model['decisions']['D_SELECTION']['status']!='deferred':
        raise ValueError('The existing no-selection disposition changed')
    cards=[('K_PAPER','Paper ledger + board','Private loan record; separate public tools/status board. Handover updates both.'),('K_LAPTOP','Local ledger on laptop','Record each handover once; derive a separate tools/status view from the same data.')]
    for i,(ident,label,summary) in enumerate(cards):
        if ident not in model['concepts']:
            raise ValueError('Missing existing concept')
        x=32+i*384
        d.box(x,170,352,260)
        d.text(label,x+20,210,24,weight=700)
        if summary != selection['presentation_readings'][ident]:
            raise ValueError('Concept presentation reading drift')
        d.lines(summary,x+20,253,22,312)
        d.text(ident,x+20,408,18,color='#486171')
    d.text('Both keep on-duty volunteer authorization.',32,477,22,weight=700)
    d.text('Upfront ceiling: $200; no recurring software budget.',32,513,22)
    report=(TOOL/'result/capacity-check.txt').read_text(encoding='utf-8')
    match=re.search(r'Required work: (\d+) x (\d+) x (\d+) = (\d+) volunteer-minutes in (\d+) minutes\.',report)
    if not match:
        raise ValueError('Conditional arithmetic report shape changed')
    arrivals,transactions,minutes,work,window=map(int,match.groups())
    if arrivals*transactions*minutes!=work:
        raise ValueError('Conditional workload arithmetic mismatch')
    d.box(32,548,736,194,fill='#eaf0f3')
    d.text('Conditional workload, not a wait prediction',52,585,24,weight=700)
    d.text(f'{arrivals} x {transactions} x {minutes} = {work} volunteer-minutes',52,628,28,weight=700)
    d.text('arrivals x transactions/arrival x minutes/transaction',52,663,20)
    d.text(f'{work} work-minutes / {window} available minutes = {work*100//window}% nominal load',52,703,22)
    d.text('Assumes one continuously available volunteer.',52,730,18,color='#486171')
    d.lines('No final choice. Costs, upkeep and waiting remain unknown.',32,785,22,736)
    d.footer('K_PAPER / K_LAPTOP  /  D_SELECTION remains deferred.', 'Fictional recollections; no measured speed advantage or expected wait.')
    return d.svg()


RENDERERS = {'01-normal-handoffs': handoffs, '02-label-recovery': handoffs, '03-responsibilities': responsibilities,
             '04-need-traces': traces, '05-receipt-deadlines': deadlines, '06-quantity-bound': quantity,
             '07-blocked-handoff': blocked, '08-tool-library': tools}


def engines():
    return pins([p for p in (ROOT/'verifier').glob('*.py')]+[p for p in (ROOT/'assets/diagram-style').rglob('*') if p.is_file()]+[ROOT/'tools/sysml/SysmlBridge.java',ROOT/'scripts/install_sysml_parser.py'])


def generators():
    return pins([p for p in HERE.iterdir() if p.is_file()])


def alternatives(facts, selection):
    key=selection['id']
    if key.startswith(('01','02')):
        view=facts['views']['SQ_NOMINAL' if key.startswith('01') else 'SQ_RECOVERY']
        return [f"{e['id']}: {e['from']} to {e['to']}: {e['message']}" for e in view['exchanges']]
    if key.startswith('03'):
        return [f"{a['function']} is documentarily assigned to {a['performer']}" for a in facts['documentary_ledger']['documentary_allocations'] if a['function'] in selection['selected_ids']]+['Courier: a pickup participant, with no function allocation recorded. Seven other documentary allocations are omitted from this scoped preview.']
    if key.startswith('04'):
        return [f"{t['from']} {t['kind']} {t['to']}" for t in facts['documentary_ledger']['typed_traces']]+['No scenario link to R_ELAPSED is recorded in the existing ledger. Links do not prove satisfaction.']
    if key.startswith('05'):
        return ['Passing trace: W001 presented at 0s, receipt at 2s, inclusive deadline 2s. W002 presented at 0.5s, receipt at 1s, deadline 2.5s. The later trigger receives its matching receipt first.','Late trace: W001 receipt at 2.1s misses its 2s deadline; W002 still matches. The monitor reports 1 matched of 2 triggers and FAIL.']
    if key.startswith('06'):
        return [f"{name}: sample 3 receiptRecorded=true, processingElapsed={facts['evidence'][name]['observations'][3]['WaterSampling::station::processingElapsed']} seconds; R_ELAPSED {facts['reports'][name]['results']['R_ELAPSED__duration']['check']['status']}. R_RECORD and R_CORRELATION pass." for name in ('pass','over-limit')]+['The fictional limit is 4 seconds, checked whenever receiptRecorded is true. Both 4 and 5 are valid integer ticks in the declared 0..20 domain, scale 1 second.']
    if key.startswith('07'):
        return ['Existing negative control replaces FN_HANDOFF guard with labelReadable==true AND labelReadable==false. The original finite source is preserved.','FN_RECORD connects received to recorded; the contradictory FN_HANDOFF guard blocks recorded to done.']+[f"{f['rule']}: {f['explanation']} ({', '.join(f['ids'])})" for f in facts['blocked_report']['findings']]
    return [facts['tool_concept']['concepts'][key]['summary'] for key in ('K_PAPER','K_LAPTOP')]+['Conditional recalled baseline: 10 arrivals x 1 transaction per arrival x 3 minutes = 30 volunteer-minutes in 30 minutes, assuming one continuously available volunteer. Nominal load 100%; no expected wait or candidate speed advantage follows.','D_SELECTION remains deferred. Paper is only recommended for a baseline exploration; no final choice, accepted weights or wait limit is recorded.']


def source_links(selection):
    # Nearby links target real files, with plain captions; fragments document selected IDs.
    return [(str(Path('..')/'..'/'..'/str(p.relative_to(ROOT))),str(p.relative_to(ROOT))) for p in source_paths() if (selection['id'].startswith('08') and p.is_relative_to(TOOL)) or (not selection['id'].startswith('08') and p.is_relative_to(CASE) and any(str(p.relative_to(CASE))==s.split('#')[0] for s in selection['source_bindings']))]


def build(output, only=None):
    if output.exists():
        raise ValueError('Output must be a fresh directory')
    facts = acquire()
    ledger = read(HERE / 'semantic-ledger.json')
    selected = [v for v in ledger['views'] if not only or v['id'] in only]
    if not selected or (only and {s['id'] for s in selected} != set(only)):
        raise ValueError('Unknown or empty showcase selection')
    output.mkdir(parents=True)
    # Freeze selected source meaning and hashes before any geometry is emitted.
    put(output / 'meaning-ledger.json', {'scope': ledger, 'source_sha256': pins(source_paths()), 'facts': facts})
    put(output / 'blocked-handoff-fixture.json',facts['blocked_fixture'])
    put(output / 'blocked-handoff-result.json',facts['blocked_report'])
    put(output / 'legacy-structural-review.json',facts['legacy_report'])
    for selection in selected:
        (output / (selection['id'] + '.svg')).write_text(RENDERERS[selection['id']](facts, selection), encoding='utf-8')
    notices=output/'font-notices';notices.mkdir()
    for name in ('inter-OFL.txt','space-OFL.txt','manifest.json'):
        (notices/name).write_bytes((ROOT/'assets/diagram-style/fonts'/name).read_bytes())
    sections=[]
    for s in selected:
        sources=' · '.join(f'<a href="{escape(link,quote=True)}">{escape(label)}</a>' for link,label in source_links(s))
        text=''.join('<li>'+escape(t)+'</li>' for t in alternatives(facts,s))
        sections.append('<section id="'+s['id'][3:]+'"><h2>'+escape(s['display_title'])+'</h2><p>'+escape(s['meaning_boundary'])+'</p><p><strong>Try this prompt</strong></p><pre>'+escape(s['prompt'])+'</pre><p class="narrow-note">Full-size 800px diagram: scroll inside the frame on narrow screens. The text alternative below carries every selected fact.</p><div class="diagram" tabindex="0" aria-label="Scrollable '+escape(s['display_title'],quote=True)+'">'+(output/(s['id']+'.svg')).read_text()+'</div><p><a href="'+s['id']+'.svg">Editable SVG</a> · <a href="'+s['id']+'.png">ActualPNG</a> · <a href="../README.md#'+s['id'][3:]+'">Reading guide</a></p><details><summary>Text alternative and exact source IDs</summary><ul>'+text+'</ul></details><p class="sources">Sources: '+sources+'</p></section>')
    html='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Engineering questions, readable outputs</title><style>body{font:20px/1.55 system-ui,sans-serif;margin:0 auto;padding:32px 20px;max-width:1100px;background:#faf9f5;color:#182b3b}h1{font-size:38px;line-height:1.2}h2{font-size:30px;line-height:1.25}a{color:#155d87;overflow-wrap:anywhere}section{margin:56px 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#e4edf2;padding:20px;font:18px/1.6 system-ui}.diagram{overflow:auto;border:1px solid #b4c2cb;max-width:100%}svg{max-width:none;display:block}.narrow-note,.sources{font-size:18px}details{padding:16px 0}li{margin:12px 0}:focus-visible{outline:3px solid #ad4b19;outline-offset:4px}</style><main><h1>Engineering questions, readable outputs</h1><p>Eight views of existing synthetic examples. Start with a question and a copy-ready prompt, then inspect the source-linked output. All timing limits, policies, allocations and evidence are fictional demonstration choices.</p><p>These are explanatory presentations, not native SysML graphical views. This artifact reader is read-only documentation, not a designed station UI. At 390px, dense diagrams remain 800px and scroll; no claim is made that the PNGs are readable when shrunk to a phone width.</p><nav>'+ ' · '.join('<a href="#'+s['id'][3:]+'">'+escape(s['display_title'])+'</a>' for s in selected)+'</nav>'+''.join(sections)+'<p><a href="../README.md">Complete guide</a> · <a href="meaning-ledger.json">Bound meaning and source facts</a> · <a href="build-manifest.json">Build pins</a> · <a href="font-notices/manifest.json">Font notices</a></p></main></html>\n'
    (output / 'index.html').write_text(html, encoding='utf-8')
    put(output / 'build-manifest.json', {'version':1,'claim':'Strict artifact freshness and source-bound explanatory outputs; not authenticated acceptance.','sources':pins(source_paths()),'generator':generators(),'engines':engines(),'views':[s['id'] for s in selected],'files':{str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file()}})


def drift(expected,actual):
    paths=sorted(p for p in expected.keys()|actual.keys() if expected.get(p)!=actual.get(p))
    return ', '.join(paths[:12])+(f' (+{len(paths)-12} more)' if len(paths)>12 else '')


def check(output=None):
    output=Path(output) if output is not None else HERE/'generated'
    manifest=read(output/'build-manifest.json')
    if manifest['sources']!=pins(source_paths()) or manifest['generator']!=generators() or manifest['engines']!=engines():
        raise ValueError('Source or generator/engine drift; rebuild and review the showcase')
    expected_ids=[v['id'] for v in read(HERE/'semantic-ledger.json')['views']]
    if manifest['views']!=expected_ids:
        raise ValueError('Missing or unclassified showcase view')
    actual={str(p.relative_to(output)):digest(p) for p in output.rglob('*') if p.is_file() and p.name!='build-manifest.json'}
    if actual!=manifest['files']:
        raise ValueError('Artifact drift, deletion or addition: '+drift(manifest['files'],actual))
    receipt=read(output/'render-receipt.json')
    if set(receipt['views'])!=set(expected_ids):
        raise ValueError('Rendered PNG scope mismatch')
    for key,item in receipt['views'].items():
        if item!={'svg_sha256':digest(output/(key+'.svg')),'png_sha256':digest(output/(key+'.png'))}:
            raise ValueError('Stale rendered PNG binding: '+key)
    inspection=read(output/'browser-inspection.json')
    if inspection['errors'] or [v['id'] for v in inspection['views']]!=expected_ids:
        raise ValueError('Browser inspection failed or omitted a selected view')
    for v in inspection['views']:
        if v['failures'] or v['narrow']['document']!=390 or v['narrow']['naturalWidth']!=800:
            raise ValueError('Recorded clipping or narrow-screen layout failure: '+v['id'])
    optional={'render-receipt.json','browser-inspection.json','build-manifest.json'}|{i+'.png' for i in expected_ids}
    with tempfile.TemporaryDirectory(prefix='showcase-rebuild-',dir=ROOT/'.cache') as temporary:
        fresh=Path(temporary)/'showcase'
        build(fresh)
        rebuilt={str(p.relative_to(fresh)):digest(p) for p in fresh.rglob('*') if p.is_file() and p.name not in optional}
        stored={k:v for k,v in actual.items() if k not in optional}
        if rebuilt!=stored:
            raise ValueError('Rebuilt SVG/content/source-map drift: '+drift(stored,rebuilt))
    print('PASS source-bound showcase: 8 previews, reproduced checks, strict SVG/content and PNG/receipt pins')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--output', type=Path)
    group.add_argument('--check', action='store_true')
    parser.add_argument('--only', nargs='+',help='partial checkpoint build only; never qualifies tracked --check')
    args = parser.parse_args()
    try:
        check() if args.check else build(args.output,args.only)
    except (OSError, ValueError, KeyError,subprocess.CalledProcessError) as error:
        print('Showcase error: '+str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
