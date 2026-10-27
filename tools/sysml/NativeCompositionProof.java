import org.omg.sysml.interactive.*;
import org.omg.sysml.lang.sysml.*;
import java.nio.file.*;
import java.util.*;
import com.google.gson.GsonBuilder;
import net.sourceforge.plantuml.*;
import java.io.*;
/** Extract facts and native TREE in one session so generated element IDs remain identical. */
public class NativeCompositionProof {
 static Object bound(Expression e) {
  if(e==null)return null;
  if(e instanceof LiteralInteger v)return v.getValue();
  throw new IllegalStateException("Unsupported multiplicity expression: "+e.eClass().getName());
 }
 static Map<String,Object> identity(Element e) {
  var m=new LinkedHashMap<String,Object>();
  m.put("kind",e.eClass().getName());m.put("id",e.getElementId());m.put("qualified",e.getQualifiedName());
  m.put("name",e.getName());return m;
 }
 public static void main(String[] args)throws Exception {
  var session=SysMLInteractive.getInstance();
  session.loadLibrary(Path.of(args[0]).toAbsolutePath().toString());
  var result=session.process(Files.readString(Path.of(args[1])));
  if(result.hasErrors())throw new IllegalStateException(result.formatIssues());
  PartDefinition selected=null;
  for(var it=result.getRootElement().eAllContents();it.hasNext();) {
   var e=it.next();if(e instanceof PartDefinition p && args[2].equals(p.getQualifiedName()))selected=p;
  }
  if(selected==null)throw new IllegalStateException("Missing selected definition");
  var rows=new ArrayList<Map<String,Object>>();
  for(var feature:selected.getOwnedFeature()) {
   if(!(feature instanceof PartUsage p))throw new IllegalStateException("Unsupported selected member "+feature.eClass().getName());
   var row=identity(p);row.put("owner",p.getOwningType().getQualifiedName());
   row.put("owner_id",p.getOwningType().getElementId());row.put("composite",p.isComposite());
   row.put("membership_id",p.getOwningMembership().getElementId());
   row.put("visibility",p.getOwningMembership().getVisibility().toString());
   row.put("definitions",p.getPartDefinition().stream().map(NativeCompositionProof::identity).toList());
   var multiplicity=p.getMultiplicity();
   row.put("multiplicity_kind",multiplicity==null?null:multiplicity.eClass().getName());
   if(multiplicity instanceof MultiplicityRange range) {
    var rawLower=bound(range.getLowerBound());var upper=bound(range.getUpperBound());
    row.put("native_lower_bound",rawLower);row.put("native_bound_count",range.getBound().size());
    if(upper==null || (rawLower==null && range.getBound().size()!=1))throw new IllegalStateException("Unsupported bounds");
    row.put("lower",rawLower==null?upper:rawLower);row.put("upper",upper);
    row.put("multiplicity_origin",rawLower==null?"explicit single-bound shorthand [n] means [n..n]":"explicit range");
   } else if(multiplicity==null || (multiplicity.eClass().getName().equals("Multiplicity") && multiplicity.getOwnedMember().isEmpty())) {
    row.put("lower",1);row.put("upper",1);row.put("multiplicity_origin","implicit language default; no owned bound range");
   } else throw new IllegalStateException("Unsupported multiplicity "+multiplicity.eClass().getName());
   rows.add(row);
  }
  var facts=new LinkedHashMap<String,Object>();facts.put("schema","cse-native-composition-1");
  facts.put("view","TREE");facts.put("selected",identity(selected));facts.put("parts",rows);
  facts.put("parse_has_errors",result.hasErrors());facts.put("parse_issues",result.formatIssues());
  Files.writeString(Path.of(args[3]+".facts.json"),new GsonBuilder().serializeNulls().setPrettyPrinting().create().toJson(facts)+"\n");
  var viz=session.viz(List.of(args[2]),List.of("TREE"),List.of("PUMLCODE"),List.of());
  if(viz.hasException())throw new IllegalStateException(viz.formatException());
  var code=viz.getPlantUML();if(code==null||!code.contains("@startuml"))throw new IllegalStateException("No native graph");
  Files.writeString(Path.of(args[3]+".puml"),code);
  var layout=code.replaceFirst("@startuml","@startuml\n!pragma layout smetana");
  Files.writeString(Path.of(args[3]+".layout.puml"),layout);
  var reader=new SourceStringReader(layout);
  for(var format:List.of(FileFormat.SVG,FileFormat.PNG)) {
   var out=new ByteArrayOutputStream();var description=reader.outputImage(out,new FileFormatOption(format));
   if(description==null||description.getDescription().toLowerCase().contains("error"))throw new IllegalStateException("Render error "+description);
   Files.write(Path.of(args[3]+"."+format.name().toLowerCase()),out.toByteArray());
  }
  System.out.println("PASS linked native composition facts and native TREE; explicit bundled Smetana layout fallback.");
 }
}
