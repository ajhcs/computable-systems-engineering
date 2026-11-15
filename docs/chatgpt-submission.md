# ChatGPT Plugin Directory submission

The hosted package targets `https://cse.open-informatics.org/mcp`. Prepare and
verify the actual endpoint, support/privacy/terms pages and exact package before
using the [OpenAI Plugins portal](https://platform.openai.com/plugins).
OpenAI's [submission flow](https://developers.openai.com/plugins/deploy/submission)
and [server review requirements](https://developers.openai.com/plugins/deploy/app-review)
govern approval. Prepared source and passing tests do not constitute a listing.

Select the owning organization/project and its verified developer identity.
Organization owners can submit; other members need Apps Management Write.
Upload the hosted ZIP through the remote-MCP path, connect the HTTPS endpoint,
and resolve the metadata, skills and tool scans. Do not upload the local-executor
package through the skills-only path when requesting browser/mobile access.

The package includes five positive and three negative cases. The public sample
attachments are original synthetic fixtures, and need no reviewer login. Run
them in fresh ChatGPT browser/mobile conversations and record the real main
workflows. Supply that recording's accessible HTTPS URL using
`--demo-recording-url` when generating the final ZIP. A recording of local
source tests alone does not establish supported ChatGPT-client behavior.

Complete the portal's generated domain challenge by serving its exact token at
the shown `/.well-known/openai-apps-challenge` URL. The token must come from this
submission; do not invent one. Add that single public challenge asset to the
selected Worker deployment and verify its exact served bytes, then use Verify
Domain in the portal. Complete required policy attestations and submit. After
OpenAI approval, select Publish. Record the actual directory URL and verify it
from an eligible account; do not infer search discoverability from repository
publication or local catalog installation.

## Tool annotation justifications

All tools set `destructiveHint: false`: they neither alter an existing project
nor send messages, payments or other irreversible external actions.
All set `openWorldHint: false`: they operate on supplied text or the packaged
reference/component catalog, with runtime Internet egress disabled.
The read-only distinction follows actual execution: reference lookups only read
packaged text; analysis and export tools start bounded jobs and create temporary
request/result files even though no project data is retained.

| Tool | readOnlyHint | Read/write justification |
| --- | --- | --- |
| `get_engineering_guidance` | true | Reads one existing packaged skill. |
| `read_engineering_reference` | true | Reads one bounded existing packaged Markdown reference. |
| `check_sysml_model` | false | Starts a parser/checker job on temporary submitted model files. |
| `review_system_concept` | false | Starts a scoped review job with temporary model, scope and source files. |
| `review_system_configuration` | false | Starts a reconciliation job with temporary native model and scope files. |
| `analyze_engineering_queue` | false | Starts a queue-analysis job with a temporary request record. |
| `analyze_system_failures` | false | Starts a Boolean failure-analysis job with a temporary request record. |
| `check_engineering_calculations` | false | Starts bounded numeric/symbolic analysis on a temporary record. |
| `check_function_flow` | false | Starts functional-graph checking on a temporary record. |
| `check_measure_definition` | false | Starts definition checking on a temporary record. |
| `check_finite_model` | false | Starts bounded finite analysis with temporary model, manifest and evidence files. |
| `check_engineering_prose` | false | Starts a lexical-budget check on temporary supplied prose. |
| `generate_property_tests` | false | Starts synthetic test generation from temporary model files. |
| `read_model_context` | false | Starts native parsing/context assembly on temporary model files. |
| `render_function_tree` | false | Creates new temporary SVG, HTML and source/receipt files, returned inline. |
| `search_engineering_components` | false | Starts a bounded catalog-search job with temporary request/output files. |
| `inspect_engineering_component` | false | Starts an exact-ID lookup job with temporary request/output files. |
| `export_engineering_components` | false | Creates new temporary selected-artwork files and returns their contents. |

Enter a justification for each of the three annotations on every scanned tool,
using the shared scope explanations and its specific row above. Portal
justifications do not override the live server's annotation values. After any
server metadata change, rescan and verify the imported values before submitting.
