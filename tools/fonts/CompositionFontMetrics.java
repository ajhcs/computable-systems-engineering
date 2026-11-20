// Offline derivative of the exact saved kit fonts; no model text is executed.
import com.google.gson.*;
import java.awt.Font;
import java.awt.font.FontRenderContext;
import java.awt.geom.AffineTransform;
import java.io.ByteArrayInputStream;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

public final class CompositionFontMetrics {
    static String hash(byte[] raw) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(raw));
    }
    static final int[][] RANGES = {{32,126},{160,591},{880,1327},{7680,8191},{8192,8959},{8960,9215}};
    static boolean admitted(int cp) {
        int kind=Character.getType(cp);
        return kind!=Character.UNASSIGNED && kind!=Character.CONTROL && kind!=Character.FORMAT
            && kind!=Character.NON_SPACING_MARK && kind!=Character.COMBINING_SPACING_MARK
            && kind!=Character.ENCLOSING_MARK && kind!=Character.LINE_SEPARATOR
            && kind!=Character.PARAGRAPH_SEPARATOR && kind!=Character.PRIVATE_USE
            && Character.getDirectionality(cp)!=Character.DIRECTIONALITY_RIGHT_TO_LEFT
            && Character.getDirectionality(cp)!=Character.DIRECTIONALITY_RIGHT_TO_LEFT_ARABIC;
    }
    public static void main(String[] args) throws Exception {
        Path root=Path.of(args[0]);
        byte[] manifestBytes=Files.readAllBytes(root.resolve("manifest.json"));
        String manifestHash="43c8d4dba54124f29d4c07718bfcefbf171fa3658558130b13d8b4f95d3b92e5";
        if(!hash(manifestBytes).equals(manifestHash))throw new IllegalArgumentException("Original manifest changed");
        var manifest=JsonParser.parseString(new String(manifestBytes,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
        byte[] metricBytes=Files.readAllBytes(root.resolve("metrics.json"));
        if(!hash(metricBytes).equals(manifest.getAsJsonObject("metrics").get("sha256").getAsString()))throw new IllegalArgumentException("Original metrics changed");
        var old=JsonParser.parseString(new String(metricBytes,java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonObject("faces");
        Map<String,Object> result=new LinkedHashMap<>(),faces=new LinkedHashMap<>();
        result.put("version","cse-composition-fonts-1");result.put("source_manifest_sha256",manifestHash);
        result.put("coverage","Present glyphs in the declared Latin, Greek, Cyrillic and engineering-symbol ranges; fixed nonjoining left-to-right profile");
        result.put("limits","Combining marks, right-to-left/complex shaping, controls, absent glyphs and characters outside these ranges remain unqualified. No transliteration or fallback font.");
        result.put("ranges",RANGES);result.put("faces",faces);
        var context=new FontRenderContext(new AffineTransform(),true,true);
        for(var value:manifest.getAsJsonArray("faces")) {
            var face=value.getAsJsonObject();String file=face.get("file").getAsString(),family=face.get("family").getAsString();
            int weight=face.get("weight").getAsInt();String key=family+":"+weight;
            byte[] bytes=Files.readAllBytes(root.resolve(file));String digest=hash(bytes);
            if(!digest.equals(face.get("sha256").getAsString()))throw new IllegalArgumentException("Original font changed");
            var prior=old.getAsJsonObject(key);int units=prior.get("units").getAsInt();
            Font font=Font.createFont(Font.TRUETYPE_FONT,new ByteArrayInputStream(bytes)).deriveFont((float)units);
            if(!font.getFamily(Locale.ROOT).equals(family))throw new IllegalArgumentException("Physical font family changed");
            Map<String,Integer> advances=new TreeMap<>();
            for(int[] range:RANGES)for(int cp=range[0];cp<=range[1];cp++) {
                if(!admitted(cp)||!font.canDisplay(cp))continue;
                String text=new String(Character.toChars(cp));var glyphs=font.createGlyphVector(context,text);
                if(glyphs.getNumGlyphs()!=1||glyphs.getGlyphCode(0)==0)continue;
                double advance=glyphs.getGlyphMetrics(0).getAdvanceX();int integer=(int)Math.round(advance);
                if(integer<=0||Math.abs(advance-integer)>0.0001)throw new IllegalArgumentException("Nonintegral source advance");
                advances.put(text,integer);
            }
            for(var entry:prior.getAsJsonObject("advances").entrySet())
                if(!Objects.equals(advances.get(entry.getKey()),entry.getValue().getAsInt()))throw new IllegalArgumentException("Original advance differs: "+key+" "+entry.getKey());
            Map<String,Object> record=new LinkedHashMap<>();record.put("font_sha256",digest);record.put("units",units);record.put("advances",advances);faces.put(key,record);
        }
        String text=new GsonBuilder().setPrettyPrinting().disableHtmlEscaping().create().toJson(result)+"\n";
        Files.writeString(Path.of(args[1]),text,StandardOpenOption.CREATE_NEW);
    }
}
