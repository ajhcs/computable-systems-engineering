"""Conditional Little-law consistency, not queue simulation or staffing analysis."""
from fractions import Fraction
from .foundation import Invalid, _object

CONDITIONS=('finite_means','strict_stationarity','metrically_transitive_arrivals',
            'matched_boundary_population','compatible_averaging')


def schema(flows,record,quantity,label,basis):
    for key,flow in flows.items():
        _object(flow,('label','subject','boundary','population','averaging_context','units',
                      'conditions','L','arrival_rate','W','tolerance'),key)
        label(flow['label'],key+'.label')
        for field in ('boundary','population','averaging_context'):
            if type(flow[field]) is not str or len(flow[field])>4096:
                raise Invalid(key+'.'+field+' needs bounded documentary text')
        if flow['subject'] not in record['resources']:
            raise Invalid('Flow subject must identify a declared/native-bound resource')
        _object(flow['units'],('population','time'),key+'.units')
        for field in flow['units']:
            label(flow['units'][field],key+'.units.'+field)
        _object(flow['conditions'],CONDITIONS,key+'.conditions')
        for condition,fact in flow['conditions'].items():
            _object(fact,('value','basis'),key+'.'+condition)
            if fact['value'] is not None and type(fact['value']) is not bool:
                raise Invalid('Flow applicability conditions must be Boolean or null')
            basis(fact['basis'],key+'.'+condition+'.basis')
        for field in ('L','arrival_rate','W','tolerance'):
            quantity(flow[field],key+'.'+field)


def analyze(flows,sources,decimal):
    results={}
    for key,flow in flows.items():
        result={'label':flow['label'],'status':'unknown','findings':[],
            'claim_scope':'conditional_consistency_L_equals_arrival_rate_times_W',
            'subject':flow['subject'],'conditions':flow['conditions'],
            'predicted_L':None,'absolute_difference':None,
            'staffing_adequacy':'not_evaluated','applicability_validation':'not_evaluated'}
        def issue(rule,status,detail):result['findings'].append({'rule':rule,'status':status,'ids':[key],'detail':detail})
        for field in ('boundary','population','averaging_context'):
            if not flow[field].strip():issue('flow_context_unknown','unknown','Define the common '+field+' before interpreting means.')
        for condition,fact in flow['conditions'].items():
            if fact['value'] is None or fact['basis'] is None:
                issue('flow_applicability_unknown','unknown','Supply the declared basis for '+condition+'.')
            elif fact['basis'] not in sources:
                issue('flow_basis_missing','fail','Referenced applicability source is absent.')
            elif fact['value'] is False:
                issue('flow_applicability_unsupported','unsupported','The retained 1961 theorem profile does not apply when '+condition+' is false.')
        for field in ('L','arrival_rate','W','tolerance'):
            value=flow[field]
            if value is None or value['basis'] is None:
                issue('flow_quantity_unknown','unknown','Supply '+field+' and its explicit source/assumption.')
            elif value['basis'] not in sources:
                issue('flow_basis_missing','fail','Referenced '+field+' source is absent.')
        if not result['findings']:
            pop,time=flow['units']['population'],flow['units']['time']
            expected={'L':pop,'arrival_rate':pop+'_per_'+time,'W':time,'tolerance':pop}
            if any(flow[field]['unit']!=unit for field,unit in expected.items()):
                issue('flow_units','unsupported','Population/rate/time/tolerance units must match; no conversion is inferred.')
            if Fraction(flow['arrival_rate']['value'])<=0:
                issue('flow_zero_rate','unsupported','The retained 1961 theorem profile requires a nonzero mean arrival rate.')
        if not result['findings']:
            predicted=Fraction(flow['arrival_rate']['value'])*Fraction(flow['W']['value'])
            difference=abs(Fraction(flow['L']['value'])-predicted)
            try:
                result['predicted_L']={'value':decimal(predicted),'unit':flow['units']['population']}
                result['absolute_difference']={'value':decimal(difference),'unit':flow['units']['population']}
                result['tolerance']=flow['tolerance']
                result['status']='pass' if difference<=Fraction(flow['tolerance']['value']) else 'fail'
            except Invalid as exc:
                issue('flow_precision','unsupported',str(exc))
        if result['findings']:
            states={x['status'] for x in result['findings']}
            result['status']=next(x for x in ('error','fail','unsupported','unknown') if x in states)
        results[key]=result
    return results
