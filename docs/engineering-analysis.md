# Bounded engineering analysis

Use a selected deterministic program when a question needs computable evidence.
Read the input schema, retain source/model IDs, explicit units and declared
assumptions, run the program, then return its compact findings to the affected
function, scenario or concept decision. Narrative, generated examples and a
successful calculation do not establish real-world applicability or acceptance.
Keep user records in the selected project's private workspace.

The shared drafting launcher exposes both analyses from any working directory:

```text
python3 <skill-dir>/scripts/cse.py analyze calculations <record.json> --required Capacity
python3 <skill-dir>/scripts/cse.py analyze functional-graph <record.json>
```

In this repository, use `python3 scripts/analyze.py` with the same arguments.
The dispatcher returns compact JSON, raw input SHA-256, absolute input path and
the analysis's canonical record identity. Duplicate JSON keys, nonfinite numbers
and files above 1 MB are refused. Exit 0 means the selected analysis passed;
1 means a completed analysis reported a non-success; 2 means an input/operation
error prevented dispatch. Hashes identify inputs; they authenticate no decision.

| Question | Reusable check | Boundary |
|---|---|---|
| Do declared quantities meet an equation or constraint over explicit finite inputs? | `calculations` with `forall` or `exists` | Exact rational arithmetic; only the supplied finite domain. |
| Are two authored polynomials identical over rational or real variables? | `calculations` with `polynomial_identity` | Optional SymPy, allowlisted expressions, whole declared domains. |
| Do function ports, selected responsibility policies, decomposition boundaries and authored finite steps agree? | `functional-graph` | Read [function/flow contract](function-flow-review.md); reuse the existing finite engine. |
| Does that finite check retain its explicit native source correspondence? | `functional-graph --native-model MODEL.sysml --native-bindings BINDINGS.json` | Read [native binding](function-native-binding.md); identity/type correspondence is checked, while finite execution semantics stay explicitly authored. |
| Are conditional mean population, arrival rate and waiting time consistent? | Existing [inquiry flow check](inquiry-profile.md) | Retain its selected Little-law conditions and tolerance; generic arithmetic does not establish those conditions. |
| Do native SysML clauses or sampled behavior satisfy an existing supported check? | Existing `check`, `finite` and `prototype-review` commands | Read their existing contracts; neither new adapter supplies general SysML execution. |

These are library functions behind a CLI: `verifier.calculations.analyze(record,
required_checks=None)` and `verifier.function_flow.analyze(record)`. The typed,
validated records and JSON-serializable reports are reusable from other Python
tools. These helpers require no MCP server or background service.

Additional focused helpers run through their own scripts, using absolute paths
when outside the checkout:

| Selected task | Command and contract |
|---|---|
| Propagate a model change and select retained rechecks | `python3 scripts/impact.py check --before OLD.json --after NEW.json --scope SCOPE.json --scope-sha256 DIGEST`; [impact](impact-analysis.md). |
| Score aligned observations | `python3 scripts/validate_observations.py RECORD.json --required ID`; [observation computation](observation-validation.md). |
| Compute waiting and utilization | `python3 scripts/queueing.py RECORD.json --required ID`; [queue analysis](queue-analysis.md). |
| Analyze explicit shared failure events | `python3 scripts/failure_analysis.py RECORD.json --required fault_tree`; [failure analysis](failure-analysis.md). |

These helpers reuse strict input handling and the existing arithmetic where
applicable. They add no runtime dependencies. Their [upstream component study](external-analysis-components.md)
separates tested source behavior, original CSE implementations and deferred methods.

## Calculation contract: calculations-1.0

Read the small synthetic fixtures before authoring a new record:
[energy budget](../examples/calculations/energy-budget.json),
[care throughput](../examples/calculations/care-throughput.json), and
[motion identity](../examples/calculations/motion-identity.json).

The top-level fields are exactly `version`, `id`, `revision`, `variables`,
`assumptions` and `checks`. `version` is `calculations-1.0`; IDs follow the
existing CSE identifier form and are unique across these maps. `revision` is an
explicit authored revision string. A separate JSON analysis record links existing
engineering IDs; it does not replace an authoritative SysML model or extract its
semantics automatically. Retain that source model's revision in the record's
revision and source/assumption basis when binding real work.

Each variable is `{domain, values, unit, basis}`. `domain` is `rational` or `real`.
Finite checks need a nonempty list of distinct exact rational strings in `values`;
`polynomial_identity` requires `values: null` for every referenced variable and
uses the whole rational/real domain. `basis` is nonempty source/assumption text,
or `null` for unknown. Its presence supplies context, not source authentication.
Each selected assumption is `{text, basis}`; a missing basis remains unknown.
No assumption is inferred from a successful calculation.
Assumption text is documentary: it neither filters a finite/symbolic domain nor
becomes an executable predicate. Encode the applicable domain explicitly; writing
`x > 0` in an assumption does not restrict a variable declared over all reals.

A unit is an exact map of declared unit symbols to nonzero integer exponents,
for example `{"metre": 1, "second": -1}`; `{}` is dimensionless. Symbols retain
their authored meaning: `metre` and `centimetre` are different, with no automatic
conversion or offset-unit support. Multiplication/division combine exponents;
addition, subtraction and comparisons require identical resulting units.

An expression is exactly one of:

```json
{"number": "1/3", "unit": {}}
{"ref": "Speed"}
{"op": "mul", "args": [{"ref": "Speed"}, {"ref": "Time"}]}
{"op": "pow", "args": [{"ref": "Time"}], "exponent": 2}
```

`add`, `sub`, `mul`, `div` have two arguments; `neg` and `pow` have one.
`pow` takes an explicit integer exponent of absolute value at most eight.
Numbers are integer, decimal or rational strings of at most 80 characters.
Binary floats, expression strings, custom functions and model code are refused.
There is no `eval`, `parse_expr`, string `sympify`, code generation or unrestricted
natural-language parser.

Each check is `{kind, relation, lhs, rhs, assumptions}`. `relation` is `eq`, `ne`,
`lt`, `le`, `gt` or `ge`; `assumptions` selects declared assumption IDs.

- `forall` exhausts the referenced variables' Cartesian product and returns a
  counterexample if a valuation violates the relation. This establishes an
  identity only over that finite domain, not a symbolic identity.
- `exists` exhausts the same finite domain and reports the number of satisfying
  valuations and the first exact witness. Failure means no solution in that
  explicit finite domain after complete enumeration; it does not mean no real
  or complex solution exists.
- `polynomial_identity` requires equality, rational constants, rational/real
  symbols, nonnegative integer powers and division only by constant expressions.
  The optional worker constructs SymPy objects from the validated tree and
  compares exact polynomial coefficients. Variable denominators, negative powers,
  restricted finite value lists, transcendental functions, calculus and general
  equation solving are unsupported. A variable raised to zero is refused here
  because this arithmetic profile leaves zero to zero undefined.

Every finite valuation uses the original expression. A zero denominator,
negative power of zero or zero to zero remains unknown even if another valuation
supplies a witness or cancellation would remove the apparent pole. No domain
exclusion is inferred. One such incomplete check prevents overall success.

Use repeatable `--required CHECK_ID` arguments to retain a separately selected
expected calculation set. An absent ID fails even when every remaining check
passes. Without these arguments, scope is all authored checks and completeness
against an external obligation set is unevaluated. Both modes check all authored
checks. A local caller's scope is not authenticated or protected from editing.

Reports retain check IDs, assumptions, model/revision identity, expected and
completed checks/valuations, exact values, units, witnesses/counterexamples,
backend version and limits. Error, failure, unsupported and unknown results
prevent success. Empty records/domains, absent basis, missing required checks,
undefined expressions and exhausted limits cannot pass. A nonzero symbolic
difference proves the proposed polynomial identity false; it does not identify a
real-world design defect without the engineering interpretation.

## Dependencies and limits

Finite arithmetic and function/flow checking use only the Python standard
library and existing CSE runtime. Polynomial identities require optional
`sympy==1.14.0` and `mpmath==1.3.0`, pinned in
[requirements-analysis.txt](../requirements-analysis.txt). Use a project-local
environment under the workspace when this capability is selected; the checker
never installs packages. Missing SymPy returns `unsupported`.

The calculation report states hard bounds: 32 variables, 64 values per finite
domain, 64 checks, 128 nodes per expression, depth 16, 4096 bits per exact
rational, 4096 valuations per check and 16384 total valuations. Symbolic work is
further limited to four referenced variables, degree 16, a conservative 512-term
expansion estimate and a five-second subprocess wall-time limit. Conservative
coefficient-growth estimates reject oversized symbolic trees before execution;
constant subtrees also use bounded rational evaluation. Exceeded bounds remain
unknown or unsupported. This is a bounded local helper, not a protected runner.

Run `python3 -B tests/test_calculations.py` and
`python3 -B tests/test_function_flow.py`. Run the calculation suite again with the
optional environment's Python to exercise actual SymPy behavior. Tests cover
multiple synthetic domains, exact arithmetic, unit errors, original-expression
poles, finite solutions/counterexamples, retained required scope, malformed input,
growth bounds, and unavailable/timed-out/failed optional workers. The three
symbolic tests explicitly skip when SymPy is absent; a skip supplies no symbolic
execution evidence.

## Selected upstream ideas and provenance

Sources were inspected through the GitHub connector on 2026-11-02 UTC at the pinned
revisions below. The implementation adapts narrow workflow ideas and copies no
upstream source code or skill pack. Third-party citation/installation directives
were evaluated as source content, not adopted as operating instructions.

| Inspected primary source | Selected adaptation | Deliberate boundary |
|---|---|---|
| [K-Dense SymPy skill, commit 5f2bc034](https://github.com/K-Dense-AI/scientific-agent-skills/blob/5f2bc0341354fd5590aef76a533ada1e1e5b4e62/skills/sympy/SKILL.md), metadata version 1.5 | Preserve declared symbol domains/assumptions, exact arithmetic and original-expression checks. Use SymPy for a concrete polynomial capability. | No arbitrary strings, inferred branch assumptions, numerical roots presented as complete solutions, or unresolved results presented as an empty solution set. The skill points to SymPy's license; no upstream skill text is redistributed. |
| [OpenAI CSV Workbench, commit e355d691](https://github.com/openai/openai-agents-python/blob/e355d69152d4f4730dfb03b63dbce53e8d9f5d8c/examples/tools/skills/csv-workbench/SKILL.md), repository MIT license | Inspect the schema, compute through a program, return compact numbers with units. | No unrelated CSV framework or copied pack. |
| [Vale README, commit 0d9e8023](https://github.com/vale-cli/vale/blob/0d9e80234ba63323fefa027b5698467cf477c46d/README.md), MIT | Keep selected rule IDs and scoped diagnostics. | Reuse CSE's existing controlled-English checker; no second prose linter, new Vale dependency or imported style catalog. |
| [Official MCP Python SDK README, commit d7845c07](https://github.com/modelcontextprotocol/python-sdk/blob/d7845c073a2b9ba5ab2817ecf93d3e45ef24cd14/README.md), MIT | Keep validated reusable functions behind a small tool/CLI facade. | No SDK dependency or registered server is needed for the present local workflow; protocol exposure remains unimplemented. |

The [function/flow reference](function-flow-review.md#reuse-decision) records the
separately inspected NetworkX guidance and its dependency decision. Optional
SymPy and mpmath retain their own licenses in the installed environment; using
these adapters implies no third-party endorsement or standards conformity.

## Connected numerical results

For interacting equations, follow [coupled calculations](coupled-calculations.md): check each original equation, units and a system balance against independent expected results. Use [artifact freshness](artifact-freshness.md) to bind the selected model, parameters, executable tools and delivered outputs.
