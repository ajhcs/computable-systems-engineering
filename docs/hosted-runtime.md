# Hosted ChatGPT runtime

The optional hosted edition connects the same eleven skills to a stateless
Streamable HTTP MCP service. It is intended for ChatGPT browser, mobile and
desktop clients with custom MCP/plugin access. Account, workspace, regional and
OpenAI review restrictions still apply. A source checkout or passing local test
does not establish that an endpoint is deployed or a plugin is publicly listed.

When the hosted tools are connected, use them for supported computations rather
than asking the engineer to install Python or Java. Command blocks in existing
skills describe the separate local route. Read only the selected workflow and
the contracts needed for its current check, through `get_engineering_guidance`
and `read_engineering_reference` when packaged files are unavailable.

| Work | Hosted operation |
| --- | --- |
| Concept, CONOPS, scenario or architecture drafting | `check_sysml_model`, with explicit source texts and companion profiles |
| Retained concept review and evidence gaps | `review_system_concept` |
| Selected architecture/configuration reconciliation | `review_system_configuration` |
| Measure definitions | `check_measure_definition` |
| Queues | `analyze_engineering_queue` |
| Fault trees and linked FMEA | `analyze_system_failures` |
| Exact calculations or functional graphs | `check_engineering_calculations`, `check_function_flow` |
| Existing opt-in version-2 finite records | `check_finite_model` |
| Actual delivered prose | `check_engineering_prose`, with caller-selected budgets |
| Synthetic variable-influence tests | `generate_property_tests` |
| Existing native identity/context | `read_model_context` |
| Declared function-tree presentation | `render_function_tree` |
| Reusable artwork | Search, inspect and export engineering components by exact ID |

`files` is a map of flat filenames to exact UTF-8 contents. Supply every model
dependency, retained scope, required source and sibling `.english.json` profile
explicitly. Names cannot contain directory paths; adapt the request's file
bindings explicitly rather than silently rewriting engineering identities.
Up to 32 files and 1 MB combined input are accepted. Checks have a 30-second wall
limit, a 25-second CPU limit and a bounded response. Busy, incomplete, unsupported
and errored checks cannot satisfy required review. Do not split a required
review into smaller views to conceal unmet obligations.

Retained scope digests come from the engineer's previously selected exact bytes.
Computing a digest inside a request cannot authenticate the choice of scope.
Evidence binds to the checker-reported model digest. Reusing exact filename/text
sets gives stable multi-file identities in this deployment; local absolute-path
identities may differ and require explicit reconciliation.

The service processes only the selected submitted text. It cannot read the
engineer's computer, fetch arbitrary URLs, execute submitted code, retain
projects or accept a design. Generated UTF-8 artifacts return inline with their
hashes; preserve them in the conversation or selected project storage. No
persistent download URLs or cross-session project database are supplied. Other
diagram families, captured observations, visual inspection and legacy workflows
remain subject to their documented execution limits; do not report an omitted
operation as run.

Explain that selected text is sent to the hosted service through ChatGPT before
using it for project material. Keep PHI, credentials, payment-card data,
government identifiers and other restricted data out of requests. Offer the
local route when the material must remain on the engineer's computer. The
service deletes request files when a job finishes, including failures; the
hosting provider and ChatGPT have their own data policies.

## Deployment

The target is `https://cse.open-informatics.org/mcp`. Deployment lives in
`hosted/cloudflare/`, separate from the Open Informatics Pages site. The Worker
serves public listing/support/privacy pages and forwards MCP traffic to one
Cloudflare Container with outbound Internet disabled. It rate-limits requests,
bounds request bodies and returns no-store responses. The container sleeps after
one minute of inactivity. Python dependencies are hash-locked; the pinned OMG
parser is installed and verified at image build time. The container size retains
the existing parser's Java heap allowance.

Build the image from the reviewed source and qualify the actual image before
deployment. Set a digest-pinned image in a deployment-specific Wrangler config
when building elsewhere. Run `npm ci`, `npm run check` and `npm run preview` from
`hosted/cloudflare`, then deploy only the selected Worker/container/custom domain.
Cloudflare Containers require a Workers Paid account and incur usage charges.
The checked-in instance count and inactivity controls limit intended operation;
they are not a billing cap.

After deployment, verify HTTPS, HTTP MCP initialization, every advertised tool,
negative requests, public policy/support URLs and clean ChatGPT conversations.
Create the submission ZIP from that same committed source with
`scripts/package_chatgpt.py`. Record source commit, image digest, Worker version,
ZIP digest and actual results separately. Public review requires a verified
developer identity, domain verification, review cases and a real demo recording.
Upload/approval/publication are distinct account actions in the
[OpenAI portal](https://platform.openai.com/plugins).
