# Review connected engineering work

Use the relevant section for dependent outputs, difficult check failures or a review handoff. Keep small edits and discussion direct.

## Set the review boundary

Record the engineering question, source and model revisions, selected IDs, deliverables, retained obligations and what will count as evidence. Keep this in the conversation or existing work record. Reuse the engineer's accepted decisions and keep consequential proposals open while independent work proceeds.

Use subagents as needed when authorized and parts can proceed independently, such as tracing competing explanations or inspecting separate deliverables. Give each worker exact revisions, scope, expected evidence and ownership. Assign one writer per shared record. Reconcile findings against the actual source and outputs. Limit duplicate builds and checks on a shared machine, and clean up the background jobs and temporary files you created when they are no longer needed.

## Diagnose a failed check

Retain the command, input revision, scope and counterexample or diagnostic. Trace the finding to affected IDs. Identify whether the failure comes from the candidate, missing or stale evidence, unsupported semantics, analysis limits or the environment. Test a likely explanation against a working case when helpful. Apply the smallest justified repair and rerun the checks whose inputs changed.

Preserve accepted thresholds, obligations and applicability. Treat revisions to meaning or checker semantics as proposals for the relevant owner. When retries stop producing evidence, report the unresolved cause and the evidence or decision needed. Continue independent work within scope.

## Inspect the delivered result

Review the actual candidate and its derived outputs against the requested result and source definitions. Verify important conditions and evidence stages, including cases a simple structural check cannot resolve. For requested independent review, give the reviewer the source, scope and candidate, and reconcile findings against the contracts and files. Identify self-review when an independent pass is unavailable.

Bind findings to the delivered revisions, supplied dependencies, retained scope and tool/rule version. Inspect exit status and individual results, then report material passes, failures and unrun or unsupported checks. A later result supersedes a failed result only for the evidence and scope it actually covers. Distinguish parser and draft checks, synthetic tests, observed evidence and engineer acceptance.
