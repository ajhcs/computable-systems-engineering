import org.omg.sysml.interactive.*;
import org.omg.sysml.lang.sysml.*;
import org.eclipse.emf.ecore.*;
import java.nio.file.*;
import java.util.*;
import com.google.gson.GsonBuilder;
import java.io.*;
public class EcosystemReferenceProbe {
 static Object ref(Element e) {
  if(e==null)return null;
  var m=new LinkedHashMap<String,Object>();m.put("qualified",e.getQualifiedName());m.put("name",e.getName());m.put("kind",e.eClass().getName());
  if(e instanceof Feature f)m.put("chain",f.getChainingFeature().stream().map(x->x.getQualifiedName()).toList());return m;
 }
 static Object expression(Expression e) {
  if(e==null)return null;
  var m=new LinkedHashMap<String,Object>();m.put("kind",e.eClass().getName());
  if(e instanceof LiteralBoolean x)m.put("value",x.isValue());
  if(e instanceof LiteralInteger x)m.put("value",x.getValue());
  if(e instanceof LiteralRational x)m.put("value",x.getValue());
  if(e instanceof LiteralString x)m.put("value",x.getValue());
  if(e instanceof FeatureReferenceExpression x)m.put("referent",ref(x.getReferent()));
  if(e instanceof OperatorExpression x)m.put("operator",x.getOperator());
  if(e instanceof InvocationExpression x)m.put("arguments",x.getArgument().stream().map(EcosystemReferenceProbe::expression).toList());
  return m;
 }
 public static void main(String[] args)throws Exception {
  if(args.length<3 || args.length>4)throw new IllegalArgumentException("Usage: EcosystemReferenceProbe REFERENCE_ROOT LIBRARY_ROOT NEW_OUTPUT_DIRECTORY [EXACT_CASE]");
  var keys=List.of("C-maintenance","D-smart-grid","E-ape-allocation");
  if(args.length==4 && !keys.contains(args[3]))throw new IllegalArgumentException("Unsupported or held case: "+args[3]+"; only C-maintenance, D-smart-grid and E-ape-allocation are released");
  var selected=args.length==4?List.of(args[3]):keys;
  var root=Path.of(args[0]).toRealPath();
  var requested=Path.of(args[2]).toAbsolutePath().normalize();
  var output=requested.getParent().toRealPath().resolve(requested.getFileName());
  if(output.startsWith(root) || Files.exists(output))throw new IllegalArgumentException("Output must be a new directory outside the curated reference root, with an existing parent");
  for(var key:selected)if(!Files.isRegularFile(root.resolve("models/"+key+".sysml")))throw new IllegalArgumentException("Missing required retained model: "+key);
  var session=SysMLInteractive.getInstance();session.loadLibrary(Path.of(args[1]).toAbsolutePath().toString());
  Files.createDirectory(output);
  var gson=new GsonBuilder().setPrettyPrinting().serializeNulls().create();
  for(var key:selected) {
   var source=root.resolve("models/"+key+".sysml");var result=session.process(Files.readString(source));
   var facts=new LinkedHashMap<String,Object>();facts.put("source_file","models/"+key+".sysml");facts.put("source_sha256",HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(source))));facts.put("parse_has_errors",result.hasErrors());facts.put("issues",result.formatIssues());
   if(result.hasErrors()){Files.writeString(output.resolve(key+".facts.json"),gson.toJson(facts));throw new IllegalStateException(key+" PARSE_ERROR "+result.formatIssues());}
   var rows=new ArrayList<Map<String,Object>>();
   for(var it=result.getRootElement().eAllContents();it.hasNext();) {
    var o=it.next();if(!(o instanceof Element e))continue;
    if(!(e instanceof Feature || e instanceof Definition))continue;
    // Include declared features plus anonymous connectors and guarded successions. Exclude implied library relationships.
    if(e.isImpliedIncluded())continue;
    var m=new LinkedHashMap<String,Object>();m.put("id",e.getElementId());m.put("qualified",e.getQualifiedName());m.put("name",e.getDeclaredName());m.put("kind",e.eClass().getName());m.put("owner",e.getOwningNamespace()==null?null:e.getOwningNamespace().getQualifiedName());
    m.put("docs",e.getDocumentation().stream().map(Documentation::getBody).toList());
    if(e instanceof Feature f){m.put("types",f.getType().stream().map(Type::getQualifiedName).toList());m.put("composite",f.isComposite());m.put("direction",f.getDirection()==null?null:f.getDirection().toString());m.put("visibility",e.getOwningMembership()==null?null:e.getOwningMembership().getVisibility().toString());m.put("value",f.getOwnedMembership().stream().filter(x->x instanceof FeatureValue).map(x->expression(((FeatureValue)x).getValue())).toList());}
    if(e instanceof Connector c){m.put("source",ref(c.getSourceFeature()));m.put("targets",c.getTargetFeature().stream().map(EcosystemReferenceProbe::ref).toList());m.put("ends",c.getRelatedFeature().stream().map(EcosystemReferenceProbe::ref).toList());}
    if(e instanceof TransitionUsage t){m.put("transition_source",ref(t.getSource()));m.put("transition_target",ref(t.getTarget()));m.put("guards",t.getGuardExpression().stream().map(EcosystemReferenceProbe::expression).toList());}
    rows.add(m);
   }
   facts.put("elements",rows);Files.writeString(output.resolve(key+".facts.json"),gson.toJson(facts)+"\n");
   System.out.println(key+" parse/link PASS; linked facts extracted.");
  }
 }
}
