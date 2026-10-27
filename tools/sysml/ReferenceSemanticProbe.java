import org.omg.sysml.interactive.*;
import org.omg.sysml.lang.sysml.*;
import org.eclipse.emf.ecore.*;
import java.nio.file.*;
import java.util.*;
import com.google.gson.Gson;
public class ReferenceSemanticProbe {
 static List<Map<String,Object>> references(EObject root){var rows=new ArrayList<Map<String,Object>>();for(var it=root.eAllContents();it.hasNext();){var e=it.next();if(e instanceof FeatureReferenceExpression ref && ref.getReferent()!=null){var m=new LinkedHashMap<String,Object>();m.put("qualified",ref.getReferent().getQualifiedName());m.put("chain",ref.getReferent().getChainingFeature().stream().map(Feature::getQualifiedName).toList());rows.add(m);}}return rows;}
 public static void main(String[] args)throws Exception {
  var s=SysMLInteractive.getInstance();s.loadLibrary(Path.of(args[0]).toAbsolutePath().toString());
  var result=s.process(Files.readString(Path.of(args[1])));
  if(result.hasErrors())throw new IllegalStateException(result.formatIssues());
  var rows=new ArrayList<Map<String,Object>>();
  for(var it=result.getRootElement().eAllContents();it.hasNext();) {
   EObject e=it.next();
   if(e instanceof ActionUsage a) {
    var row=new LinkedHashMap<String,Object>();row.put("kind",e.eClass().getName());row.put("name",a.getName());row.put("qualified",a.getQualifiedName());
    if(a instanceof SendActionUsage send){row.put("payload",send.getPayloadArgument().getClass().getSimpleName());row.put("sender",send.getSenderArgument() instanceof FeatureReferenceExpression ref && ref.getReferent()!=null ? ref.getReferent().getQualifiedName() : null);}
    if(a instanceof AcceptActionUsage accept){row.put("payload_type",accept.getPayloadParameter()==null?null:accept.getPayloadParameter().getType().stream().map(Type::getQualifiedName).toList());}
    if(a instanceof FlowUsage flow){row.put("owned_feature_references",flow.getOwnedFeature().stream().map(f-> {var m=new LinkedHashMap<String,Object>();m.put("name",f.getName());m.put("qualified",f.getQualifiedName());m.put("reference",f.getOwnedReferenceSubsetting()==null?null:f.getOwnedReferenceSubsetting().getReferencedFeature().getQualifiedName());m.put("subsetted",f.getOwnedSubsetting().stream().map(sub->{var q=new LinkedHashMap<String,Object>();q.put("qualified",sub.getSubsettedFeature().getQualifiedName());q.put("chain",sub.getSubsettedFeature().getChainingFeature().stream().map(Feature::getQualifiedName).toList());return q;}).toList());m.put("value_referents",references(f));m.put("chaining",f.getChainingFeature().stream().map(Feature::getQualifiedName).toList());return m;}).toList());row.put("payload_type",flow.getPayloadType().stream().map(Type::getQualifiedName).toList());row.put("source",flow.getSourceFeature()==null?null:flow.getSourceFeature().getQualifiedName());row.put("targets",flow.getTargetFeature().stream().map(Feature::getQualifiedName).toList());row.put("source_output",flow.getSourceOutputFeature()==null?null:flow.getSourceOutputFeature().getQualifiedName());row.put("target_input",flow.getTargetInputFeature()==null?null:flow.getTargetInputFeature().getQualifiedName());}
    rows.add(row);
   }
   if(e instanceof SuccessionAsUsage c) {
    var row=new LinkedHashMap<String,Object>();row.put("kind","SuccessionAsUsage");row.put("source",c.getSourceFeature()==null?null:c.getSourceFeature().getQualifiedName());row.put("targets",c.getTargetFeature().stream().map(Feature::getQualifiedName).toList());rows.add(row);
   }
  }
  Files.writeString(Path.of(args[2]),new Gson().toJson(rows));System.out.println("Native linked semantic inventory saved.");
 }
}
