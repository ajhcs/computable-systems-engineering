# Ownership and interface-agreement review

This selected documentary profile identifies who owns, operates, funds, changes,
supports and accepts constituent systems or shared interfaces. Projects select
relevant roles and agreement/change/withdrawal facts; none of these roles is a
universal mandatory committee or protected approval mechanism. Proposed roles
are not authentic organizational commitments.

The source direction comes from the DoD *Systems Engineering Guide for Systems of
Systems*, Version 1.0, August 2008, already in the course reading inventory. Its
acknowledged-system discussion distinguishes constituent ownership, objectives,
funding and independent development. [Official course reference](https://www.cto.mil/wp-content/uploads/2024/06/DoD-SE-for-SoS-2008.pdf).
For pre-2000 change-management method, NASA's *Systems Engineering Handbook*,
June 1995, configuration-management discussion, PDF pp. 61–62, addresses affected
organizations, impact analysis, baseline communication and proportional change
control. [Original edition](https://ocw.mit.edu/courses/16-892j-space-system-architecture-and-design-fall-2004/e5e9dea39ad9594ab73c4c56024bf659_nasasysenghbookpdf.pdf#page=61).
This is a tailored CSE adaptation, not adoption of every source governance rule.

## Contract

Use one native SysML model with its existing CSE workflow. Put exactly one
`cseOwnership` document on a parsed concern:

```text
doc cseOwnership /*CSE-OWNERSHIP/1.0
{"version":"ownership-1.0","items":{...}}
*/
```

Each item key identifies either a workflow element/system or an `interfaces_with`
relation. An item has `target_kind` (element/interface), `roles` and `facts`:

```json
{
  "target_kind":"element",
  "roles":{
    "operate":{"parties":["ORG_A"],"status":"proposed","basis":"CASE"}
  },
  "facts":{
    "withdrawal":{"status":"unknown","text":"Fallback responsibilities remain unresolved.","basis":null,"refs":[]}
  }
}
```

Roles are own/operate/fund/change/support/accept. Parties reference native-bound
workflow actors, systems or elements. Multiple parties can intentionally share a
role; no unique-owner rule or party-count inference is imposed. Facts may be
agreement/change_control/withdrawal/handoff/evaluation. Facts have status, text,
basis and references to existing workflow elements, relations or evidence records.

Role/fact status is proposed/reported/unknown/withdrawn. Selected unknowns remain
unknown; a withdrawn selected responsibility/agreement fails. Reported claims need
a supplied/checked source classified reported_observation. Byte matching does not
authenticate assent, delegated authority or contractual applicability. Sources are
explicit arguments; nothing in a model can contact a party or enforce approval.

Select an `ownership` expectation in explicit concept-review-1.2 scope:

```json
{
  "topic":"ownership","kind":"ownership","target":"SERVICE_A","target_kind":"element",
  "roles":{"operate":["ORG_A"],"support":["ORG_B"]},
  "fields":["agreement","change_control","withdrawal"]
}
```

The separate scope pins selected role/party identities and facts. Use the existing
relation expectation to retain an interface's expected endpoints. Version 1.0/1.1
scopes retain their meanings; 1.2 is required for this extension. Normal concept
review extracts the named document from the same captured native snapshot and
aggregates its selected checks. Missing roles/items/facts, changed party identity,
wrong target kind, withdrawn claims and unread sources cannot become a pass.

## Workflow and evidence boundary

Identify independent constituents and interfaces, then tailor the roles and
commitments needed for the current decision. Ask who may change an endpoint,
which organizations are affected, and what happens on withdrawal or support loss.
Record evidence plans and unresolved agreements before claiming integration is
available. Reuse existing source, identity, relation and scope checks.

The helper checks declared documentary content. It does not prove that an owner
agreed, funds exist, governance is effective, an interface is technically
compatible or continuity is achieved. Ordinary drafting does not require a formal
change board or protected acceptance service. Actual commitments need real owners.
