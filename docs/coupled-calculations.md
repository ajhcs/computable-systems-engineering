# Coupled calculations

Use this guidance when electrical, mechanical, thermal, flow or control models
exchange quantities. Reuse [bounded calculations](engineering-analysis.md) for
typed arithmetic and polynomial identities. Use a named solver for differential
equations; CSE does not supply general native SysML equation execution.

Retain the model IDs, governing equations, units, signed reference directions,
parameters and initial conditions. State which losses leave a subsystem and
which enter another. Distinguish controller requests from applied actuator
values under a fault. Specify sampling, equality at thresholds, mode memory and
the ordering of control, load changes and integration.

Check each original equation as well as a system balance. Conservation alone
does not establish correct coupling: reversing both torque and back-EMF signs
can preserve the total energy balance while violating both original equations.
Exercise independent wrong-sign, missing-loss, wrong-unit and switching-boundary
cases. Use a separately derived equilibrium or small exact solution as an oracle.
Do not compute the oracle by importing the solver being checked.

Name the numerical method and tolerances. Exact rational arithmetic removes
arithmetic rounding from a discrete calculation; it does not remove integration
error. Sampled values do not establish intersample bounds. A finite corner sweep
does not bound a continuous parameter box without an additional argument.
Preserve failed predicates and distinguish them from failures of the solver.

Use [artifact freshness](artifact-freshness.md) to bind the model, parameter file,
solver, results and delivered views. Check the full dependency set after a
parameter or equation changes. Keep detailed derivations, traces and receipts in
supporting evidence; return the compact engineering result and its applicable
scope. Consequential changes to limits, assumptions or model meaning remain
engineer decisions.
