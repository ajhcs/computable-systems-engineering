# Synthetic system-concept example

This is an invented community tool library used to exercise the system-concept skill. The people, recollections, constraints, and scenario in `input.md` are synthetic. They are not collected research or measurements from a real organization.

`result/concept.json` preserves two alternatives, their evidence gaps, and proposed next decisions. `result/concept-brief.md` is a human view. The record's accepted decision labels refer to explicit constraints in the synthetic input; the checker does not authenticate them. Unknown feasibility assessments remain unknown even when structural review passes.

From the repository root:

```bash
python3 skills/develop-system-concept/scripts/concept.py check examples/tool-library/result/concept.json --review
python3 examples/tool-library/result/capacity_check.py
```

The second command regenerates `capacity-check.txt`. It verifies conditional arithmetic only. It does not verify input recollections, predict queueing delay, establish an acceptable wait, or select a design.
