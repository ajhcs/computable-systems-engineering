// Adapter for the pinned OMG SysML v2 Pilot Implementation. See docs/sysml-v2-profile.md.
// Compile against jupyter-sysml-kernel-0.52.0-all.jar; do not copy upstream code here.
import com.google.gson.Gson;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.charset.StandardCharsets;
import java.io.PrintStream;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import org.eclipse.emf.ecore.EObject;
import org.eclipse.xtext.nodemodel.util.NodeModelUtils;
import org.eclipse.xtext.validation.Issue;
import org.omg.sysml.interactive.SysMLInteractive;
import org.omg.sysml.interactive.SysMLInteractiveResult;
import org.omg.sysml.lang.sysml.AttributeUsage;
import org.omg.sysml.lang.sysml.ActionDefinition;
import org.omg.sysml.lang.sysml.ActionUsage;
import org.omg.sysml.lang.sysml.ConstraintUsage;
import org.omg.sysml.lang.sysml.ConcernUsage;
import org.omg.sysml.lang.sysml.Documentation;
import org.omg.sysml.lang.sysml.Element;
import org.omg.sysml.lang.sysml.EventOccurrenceUsage;
import org.omg.sysml.lang.sysml.Feature;
import org.omg.sysml.lang.sysml.FeatureReferenceExpression;
import org.omg.sysml.lang.sysml.FeatureTyping;
import org.omg.sysml.lang.sysml.FeatureValue;
import org.omg.sysml.lang.sysml.PartDefinition;
import org.omg.sysml.lang.sysml.PartUsage;
import org.omg.sysml.lang.sysml.ReferenceUsage;
import org.omg.sysml.lang.sysml.RequirementUsage;
import org.omg.sysml.lang.sysml.ResultExpressionMembership;
import org.omg.sysml.lang.sysml.SubjectMembership;
import org.omg.sysml.lang.sysml.StateDefinition;
import org.omg.sysml.lang.sysml.StateUsage;
import org.omg.sysml.lang.sysml.Type;
import org.omg.sysml.lang.sysml.UseCaseUsage;

public final class SysmlBridge {
    private static final Gson JSON = new Gson();

    private SysmlBridge() {}

    private static <T> T parent(EObject object, Class<T> wanted) {
        EObject cursor = object.eContainer();
        while (cursor != null) {
            if (wanted.isInstance(cursor)) return wanted.cast(cursor);
            cursor = cursor.eContainer();
        }
        return null;
    }

    private static int line(EObject object) {
        var node = NodeModelUtils.getNode(object);
        return node == null ? -1 : node.getStartLine();
    }

    private static String typedBy(Feature feature) {
        if (feature.getOwnedTyping().size() != 1) return null;
        FeatureTyping typing = feature.getOwnedTyping().get(0);
        Type type = typing.getType();
        return type == null ? null : type.getQualifiedName();
    }

    private static String referenceTarget(ReferenceUsage reference) {
        for (EObject next : reference.eContents()) {
            if (next instanceof FeatureReferenceExpression expression) {
                Element referent = expression.getReferent();
                return referent == null ? null : referent.getQualifiedName();
            }
            for (var iterator = next.eAllContents(); iterator.hasNext();) {
                EObject child = iterator.next();
                if (child instanceof FeatureReferenceExpression expression) {
                    Element referent = expression.getReferent();
                    return referent == null ? null : referent.getQualifiedName();
                }
            }
        }
        return null;
    }

    private static boolean directMember(Feature feature, PartDefinition part) {
        String name = feature.getName();
        String qualified = feature.getQualifiedName();
        String owner = part.getQualifiedName();
        return name != null && qualified != null && owner != null &&
                qualified.equals(owner + "::" + name);
    }

    private static boolean hasNativeValue(EObject object) {
        for (var iterator = object.eAllContents(); iterator.hasNext();) {
            EObject child = iterator.next();
            if (child instanceof FeatureValue || child instanceof ResultExpressionMembership)
                return true;
        }
        return false;
    }

    private static Map<String, Object> extract(Element root) {
        List<Map<String, Object>> attributes = new ArrayList<>();
        List<Map<String, Object>> events = new ArrayList<>();
        List<Map<String, Object>> eventAttributes = new ArrayList<>();
        List<Map<String, Object>> parts = new ArrayList<>();
        List<Map<String, Object>> partDefinitions = new ArrayList<>();
        List<Map<String, Object>> concerns = new ArrayList<>();
        List<Map<String, Object>> useCases = new ArrayList<>();
        List<Map<String, Object>> actions = new ArrayList<>();
        List<Map<String, Object>> states = new ArrayList<>();
        List<Map<String, Object>> requirements = new ArrayList<>();
        List<Map<String, Object>> constraints = new ArrayList<>();
        List<Map<String, Object>> documents = new ArrayList<>();
        List<EObject> all = new ArrayList<>();
        all.add(root);
        for (var iterator = root.eAllContents(); iterator.hasNext();) all.add(iterator.next());
        for (EObject object : all) {
            if (object instanceof AttributeUsage attribute) {
                EventOccurrenceUsage ownerEvent = parent(attribute, EventOccurrenceUsage.class);
                PartDefinition part = parent(attribute, PartDefinition.class);
                if (ownerEvent != null) {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("name", attribute.getName());
                    item.put("event", ownerEvent.getQualifiedName());
                    item.put("type", typedBy(attribute));
                    item.put("has_native_value", hasNativeValue(attribute));
                    item.put("has_non_typing_specialization", attribute.getOwnedSpecialization().stream()
                            .anyMatch(specialization -> !(specialization instanceof FeatureTyping)));
                    item.put("line", line(attribute));
                    eventAttributes.add(item);
                } else if (part != null && directMember(attribute, part)) {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("name", attribute.getName());
                    item.put("qualified_name", attribute.getQualifiedName());
                    item.put("part_definition", part.getQualifiedName());
                    item.put("type", typedBy(attribute));
                    item.put("direction", attribute.getDirection() == null ? null : attribute.getDirection().getName());
                    item.put("has_native_value", hasNativeValue(attribute));
                    item.put("has_non_typing_specialization", attribute.getOwnedSpecialization().stream()
                            .anyMatch(specialization -> !(specialization instanceof FeatureTyping)));
                    item.put("line", line(attribute));
                    attributes.add(item);
                }
            } else if (object instanceof EventOccurrenceUsage event) {
                PartDefinition part = parent(event, PartDefinition.class);
                if (part != null && directMember(event, part)) {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("name", event.getName());
                    item.put("qualified_name", event.getQualifiedName());
                    item.put("part_definition", part.getQualifiedName());
                    item.put("direction", event.getDirection() == null ? null : event.getDirection().getName());
                    item.put("has_non_typing_specialization", !event.getOwnedSpecialization().isEmpty());
                    item.put("line", line(event));
                    events.add(item);
                }
            } else if (object instanceof PartDefinition partDefinition) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("name", partDefinition.getName());
                item.put("qualified_name", partDefinition.getQualifiedName());
                item.put("has_specialization", !partDefinition.getOwnedSpecialization().isEmpty());
                item.put("line", line(partDefinition));
                partDefinitions.add(item);
            } else if (object instanceof PartUsage part) {
                if (parent(part, PartDefinition.class) == null) {
                    Map<String, Object> item = new LinkedHashMap<>();
                    item.put("name", part.getName());
                    item.put("qualified_name", part.getQualifiedName());
                    item.put("type", typedBy(part));
                    item.put("has_native_value", hasNativeValue(part));
                    item.put("has_non_typing_specialization", part.getOwnedSpecialization().stream()
                            .anyMatch(specialization -> !(specialization instanceof FeatureTyping)));
                    item.put("line", line(part));
                    parts.add(item);
                }
            } else if (object instanceof ConcernUsage concern) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("id", concern.getDeclaredShortName());
                item.put("name", concern.getName());
                item.put("qualified_name", concern.getQualifiedName());
                item.put("line", line(concern));
                concerns.add(item);
            } else if (object instanceof UseCaseUsage useCase) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("id", useCase.getDeclaredShortName());
                item.put("name", useCase.getName());
                item.put("qualified_name", useCase.getQualifiedName());
                item.put("line", line(useCase));
                List<Map<String, String>> subjects = new ArrayList<>();
                for (EObject child : all) {
                    if (child instanceof ReferenceUsage ref && parent(ref, UseCaseUsage.class) == useCase &&
                            parent(ref, SubjectMembership.class) != null) {
                        subjects.add(Map.of("name", ref.getName(), "target", referenceTarget(ref) == null ? "" : referenceTarget(ref)));
                    }
                }
                item.put("subjects", subjects);
                useCases.add(item);
            } else if (object instanceof ActionDefinition action) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("name", action.getName());
                item.put("qualified_name", action.getQualifiedName());
                item.put("line", line(action));
                actions.add(item);
            } else if (object instanceof ActionUsage action) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("name", action.getName());
                item.put("qualified_name", action.getQualifiedName());
                item.put("line", line(action));
                actions.add(item);
            } else if (object instanceof StateDefinition state) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("name", state.getName());
                item.put("qualified_name", state.getQualifiedName());
                item.put("line", line(state));
                states.add(item);
            } else if (object instanceof StateUsage state) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("name", state.getName());
                item.put("qualified_name", state.getQualifiedName());
                item.put("line", line(state));
                states.add(item);
            } else if (object instanceof RequirementUsage requirement) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("id", requirement.getDeclaredShortName());
                item.put("name", requirement.getName());
                item.put("qualified_name", requirement.getQualifiedName());
                item.put("kind", requirement.eClass().getName());
                item.put("has_specialization", !requirement.getOwnedSpecialization().isEmpty());
                item.put("line", line(requirement));
                List<Map<String, String>> subjects = new ArrayList<>();
                for (EObject child : all) {
                    if (child instanceof ReferenceUsage ref && parent(ref, RequirementUsage.class) == requirement &&
                            parent(ref, SubjectMembership.class) != null) {
                        subjects.add(Map.of("name", ref.getName(), "target", referenceTarget(ref) == null ? "" : referenceTarget(ref)));
                    }
                }
                item.put("subjects", subjects);
                requirements.add(item);
            } else if (object instanceof ConstraintUsage constraint) {
                RequirementUsage requirement = parent(constraint, RequirementUsage.class);
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("name", constraint.getName());
                item.put("qualified_name", constraint.getQualifiedName());
                item.put("requirement", requirement == null ? null : requirement.getQualifiedName());
                item.put("membership_kind", constraint.eContainer() == null ? null : constraint.eContainer().eClass().getName());
                item.put("line", line(constraint));
                item.put("has_native_expression", hasNativeValue(constraint));
                constraints.add(item);
            } else if (object instanceof Documentation documentation) {
                ConstraintUsage constraint = parent(documentation, ConstraintUsage.class);
                RequirementUsage requirement = parent(documentation, RequirementUsage.class);
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("name", documentation.getName());
                item.put("body", documentation.getBody());
                item.put("constraint", constraint == null || constraint instanceof RequirementUsage
                        ? null : constraint.getQualifiedName());
                item.put("requirement", requirement == null ? null : requirement.getQualifiedName());
                item.put("owner_kind", documentation.getDocumentedElement() == null ? null : documentation.getDocumentedElement().eClass().getName());
                item.put("owner", documentation.getDocumentedElement() == null ? null : documentation.getDocumentedElement().getQualifiedName());
                item.put("line", line(documentation));
                documents.add(item);
            }
        }
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("attributes", attributes);
        result.put("events", events);
        result.put("event_attributes", eventAttributes);
        result.put("parts", parts);
        result.put("part_definitions", partDefinitions);
        result.put("concerns", concerns);
        result.put("use_cases", useCases);
        result.put("actions", actions);
        result.put("states", states);
        result.put("requirements", requirements);
        result.put("constraints", constraints);
        result.put("documents", documents);
        return result;
    }

    public static void main(String[] args) {
        if (args.length != 2) {
            System.err.println("usage: SysmlBridge LIBRARY_DIRECTORY MODEL.sysml");
            System.exit(2);
        }
        PrintStream output = System.out;
        Map<String, Object> response = new LinkedHashMap<>();
        try {
            // The pilot prints library loading to stdout. Reserve stdout for one JSON object.
            System.setOut(System.err);
            SysMLInteractive parser = SysMLInteractive.createInstance();
            parser.loadLibrary(Path.of(args[0]).toAbsolutePath().toString());
            String source = args[1].equals("-")
                    ? new String(System.in.readAllBytes(), StandardCharsets.UTF_8)
                    : Files.readString(Path.of(args[1]));
            SysMLInteractiveResult parsed = parser.process(source);
            List<Map<String, Object>> issues = new ArrayList<>();
            for (Issue issue : parsed.getIssues()) {
                Map<String, Object> item = new LinkedHashMap<>();
                item.put("severity", issue.getSeverity().name());
                item.put("code", issue.getCode());
                item.put("message", issue.getMessage());
                item.put("line", issue.getLineNumber());
                item.put("column", issue.getColumn());
                issues.add(item);
            }
            response.put("issues", issues);
            response.put("error", parsed.getException() == null ? null : parsed.getException().toString());
            if (parsed.getRootElement() != null) response.putAll(extract(parsed.getRootElement()));
        } catch (Exception exc) {
            response.put("error", exc.toString());
        } finally {
            System.setOut(output);
        }
        output.println(JSON.toJson(response));
    }
}
