"""Check curated derivative assertions for selected TMT/APE views.

This public contract is a reviewed interpretation, not independent original-source
validation. Raw archives, XML and generic projections are never written here.
Use check_original_reference_sources.py explicitly for optional local comparison.
"""
from pathlib import Path
import argparse, json, re
ROOT=Path(__file__).resolve().parents[1]
PACK=ROOT/'examples/engineering-reference'
def validate_fact_content(value):
 forbidden={'source_xml','records','trace','attributes','children','effect_body','original_requirement','uuid'}
 if isinstance(value,dict):
  if forbidden.intersection(value):raise ValueError('Raw source serialization is not a public fact contract')
  for v in value.values():validate_fact_content(v)
 elif isinstance(value,list):
  for v in value:validate_fact_content(v)
 elif isinstance(value,str) and re.search(r'<(?:ownedRule|packagedElement)|xmlns[:=]|ALH\.',value):
  raise ValueError('Original source XML or opaque implementation in fact contract')
def load_facts():
 value=json.loads((PACK/'source/view-facts.json').read_text());validate_fact_content(value);return value
def check(projection):
 validate_fact_content(projection)
 if projection.get('schema')!='reviewed-diagram-facts/1':raise ValueError('Wrong derivative fact schema')
 t=projection['slices']['tmt-maintenance']
 expected=[
 ('Initializing','StandBy','InitComplete',None),
 ('StandBy','Maintenance Alignment','Maintenance Alignment',None),
 ('Maintenance Alignment','StandBy','Abort',None),
 ('Correcting Rigid Body and Segment Figure','Broad Band Phasing 1um','Finished','diffTime'),
 ('Broad Band Phasing 1um','Narrow Band Phasing','Finished','diffTime'),
 ('Narrow Band Phasing','StandBy','Finished','FinalDiffTime'),
 ('StandBy','uml:FinalState','Finished',None)]
 got=[(x['source_name'],x['target_name'],x['signals'][0]['name'] if x['signals'] else None,x['effect']) for x in t['transitions'] if x['signals']]
 if sorted(map(str,got))!=sorted(map(str,expected)):raise ValueError('Original lifecycle semantics changed')
 if len(t['transitions'])!=9:raise ValueError('Missing initial transitions')
 timing=projection['slices']['tmt-timing']
 if timing['source_expression']!='p1<=maxTime' or timing['limit_seconds']!=1800:raise ValueError('Wrong timing revision/operator')
 if timing['english_timing_boundary']!='strictly less than 1800 seconds; other operational conditions remain qualitative':raise ValueError('Lost strict English boundary')
 parts=projection['slices']['ape-composition']['parts']
 if {(p['type_name'],p['lower'],p['upper'],p['aggregation']) for p in parts}!={('Segment',61,61,'composite'),('PositionActuator',183,183,'composite'),('Mount',1,1,'composite')}:raise ValueError('Changed composition')
 if any(p['visibility']!='private' for p in parts):raise ValueError('Source composition visibility drift')
 if len({p['owner_id'] for p in parts})!=1:raise ValueError('Invented nested actuator allocation')
 optical_scope=projection['slices']['ape-optical']
 if optical_scope['source_visibility']!={'ut3':'private','ape_t':'private','lg1':'private','ada':'private'} or optical_scope['derived_visibility']!={'ut3':'private','ape_t':'private','lg1':'public','ada':'public'}:raise ValueError('Visibility adaptation drift')
 optical=optical_scope['connectors']
 if len(optical)!=2:raise ValueError('Lost optical connectors')
 proxies=projection['slices']['ape-optical'].get('port_stereotypes',[])
 expected={'_15_1_bf10301_1210764986103_615550_6670','_15_1_bf10301_1210680977392_846759_11441','_15_1_baa02e2_1212914971437_912712_9360'}
 if len(proxies)!=3 or {p['base_Port'] for p in proxies}!=expected or any(p['stereotype']!='ProxyPort' or p['namespace']!='http://www.omg.org/spec/SysML/20181001/SysML' for p in proxies):raise ValueError('Lost original ProxyPort stereotype')
 if projection['slices']['ape-optical']['nested_property_path']!=['_15_0_3c00182_1203339836217_958479_4963','_15_1_baa02e2_1210774914160_880510_12061']:raise ValueError('Nested optical path drift')
 if any(c.get('direction')!='undirected' for c in optical):raise ValueError('Invented optical direction')
 if any(p['owner_id']!='_15_0_bf10301_1202464929960_949157_5982' for p in parts):raise ValueError('Changed composition owner')
 return {'status':'pass','claim_scope':'reviewed-derivative-contracts','checks':['nine transitions and composite Abort','inclusive predicate versus strict narrative','direct 61/183/1 composition','two undirected optical connectors and selected nested path'], 'original_source_validation':'not_run; original XML and broad projections are intentionally not distributed','limits':'No original archive validation, independent source validation, behavioral execution or general equivalence.'}

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--check',action='store_true',help='Check saved curated derivative assertions without original source inputs.')
 parser.parse_args()
 print(json.dumps(check(load_facts()),indent=2))
if __name__=='__main__':main()
