import org.omg.sysml.interactive.*;
import java.nio.file.*;
import com.google.gson.Gson;
import java.util.*;
public class ReferenceEvalProbe {
 public static void main(String[] args)throws Exception {
  var s=SysMLInteractive.getInstance();s.loadLibrary(Path.of(args[0]).toAbsolutePath().toString());
  var result=s.process(Files.readString(Path.of(args[1])));if(result.hasErrors())throw new IllegalStateException(result.formatIssues());
  var rows=new ArrayList<Map<String,Object>>();
  for(var value:new int[]{1799,1800,1801}) {
   var expr="TMTTimingDerived::MaxTimeConstraint("+value+".0,1800.0)";
   var evaluated=s.eval(expr,null).trim();var row=new LinkedHashMap<String,Object>();row.put("input_seconds",value);row.put("expression",expr);row.put("native_result",evaluated);row.put("expected",value<=1800);row.put("literal_english_expected",value<1800);rows.add(row);
  }
  Files.writeString(Path.of(args[2]),new Gson().toJson(rows));System.out.println(new Gson().toJson(rows));
 }
}
