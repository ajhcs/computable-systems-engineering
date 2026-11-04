# Source observations

These are the exact source views inspected for this study. Source images are not redistributed. Each SVG is an original generic drawing, not a dimensional reproduction of the cited equipment.

## Pulley geometry

1. [Ropeblock cast sheave, model SE.260.5012.6.5](https://ropeblock.com/configurator/product_details.php?name=SE.260.5012.6.5), product render and linked cross-sectional sketch. The render shows a flanged wheel and central bearing in a shallow oblique view. The section shows a circular wire cross-section in the groove between the flanges. Both actual linked images were retrieved and visually inspected for this study.

   The manufacturer's nominal example lists a 300 mm outside diameter, 260 mm tread diameter, and 12 mm wire diameter. If the wire is seated on that tread without deformation, its outer path has an illustrative diameter of 284 mm: below the 300 mm flange outside diameter. **Inference:** from a true face view, that particular flange can hide the wrap. This is not a rule for every sheave, and these values were not used as dimensions for the icons.

2. [Petzl, “How to calculate mechanical advantage”](https://www.petzl.com/us/en/professional/tech-tips/basic-techniques/how-to-calculate-mechanical-advantage/MAESTRO-Pe06-RapportsMouflage_PRO_a771r000000Co9vAAC.html), “The pulley effect” illustration. The actual linked SVG was retrieved and visually inspected. It shows one rope bending around a wheel with two free segments. It is a relationship diagram; it does not specify a groove or establish the face visibility of the Ropeblock product.

The candidate 04 pulley used an outside wheel radius of 35 SVG units and a rope-path radius of 36 units. At 64 px, that difference is less than half a pixel before stroke width is considered; this explains the observed merged upper arcs.

## Spring geometry

3. [Lee Spring, “Compression Spring Basic Features”](https://www.leespring.com/sites/default/files/pdf/Lee%20Spring%20-%20WhitePaper%20-%20Compression%20Spring%20Basic%20Features_US.pdf#page=2), page 1 compression-spring photographs and page 2 “Open End” illustration. The existing exact cached pages were visually inspected again. They support an open helical wire and consistent pitch at an open end. The new vectors do not copy a specific spring or establish wire diameter, handedness, pitch, end finish or spring rate.

The spring boundary studies use a constant-width stroke around a projected analytic center path. That is a useful illustration, not an exact projected silhouette of a swept round wire. `spring-geometry.json` records the turn counts and crossing calculations. Spring A and C use the same four-turn projected path, with and without a wire boundary; Spring B deliberately shows three turns.

Candidate 04's primary spring SVG is the wire-boundary drawing shown as the baseline here. Its inherited `comparison_candidate_qualifier` says “WIRE CENTERLINE”; that qualifier is stale and does not describe the primary SVG. This focused study labels the two treatments explicitly and leaves candidate 04 unchanged.
