# Community tool library: initial system concept

**Proposed next exploration:** try the improved paper workflow as the baseline first. It addresses missed board updates with little technical dependency. Keep the laptop candidate open: single entry could simplify updates, but cost, condition, usability, and upkeep are unverified. This is a recommendation, not an accepted selection.

## Need, boundary, and evidence

The need is trustworthy availability and less volunteer administration. The present ledger and board disagree. Success means fewer wasted visits and less administration; no target or delivery date is agreed.

The boundary covers handover, authorization, records, member availability, discrepancy correction, and recovery during Saturday opening. The on-duty volunteer must authorize every loan. Maintenance ownership is unresolved. Detailed scenarios and a complete CONOPS are excluded.

The supplied request establishes about 40 members, usually one volunteer, a two-hour opening, $200 maximum upfront, no recurring software budget, an unassessed laptop, intermittent internet, and no public borrower identities. Three minutes per transaction and ten arrivals in the busiest half-hour are recollections, not measurements. Features below are proposals.

## Essential functions

| Function | Need served | Required transformation |
|---|---|---|
| Authorize a loan | Preserve volunteer control | Member request and tool status → volunteer authorization or refusal |
| Record a loan | Keep status accurate | Authorized handover → private loan record and borrowed status |
| Record a return | Keep status accurate | Received tool → closed loan and updated availability |
| Present availability | Help members check; preserve privacy | Tool status → member-facing information without borrower identities |
| Reconcile discrepancies | Restore trust in status | Record, displayed status, and physical stock → corrected record and display |
| Preserve and recover records | Continue service with manageable upkeep | Current record and retained recovery material → usable, current record after disruption |

## Two candidates

| Consideration | Improved paper ledger and board | Local offline laptop ledger |
|---|---|---|
| Mechanism | Private authoritative ledger; pair handover recording with public-board updating. Reconcile before opening and after discrepancies. | Record each handover once; generate a separate public view from the same data. Tool identifiers/states need agreeing. |
| Accuracy | Addresses missed updates, but still requires two entries; interruptions can separate them. | Removes duplicate board entry; missed or incorrect transactions still create errors. |
| Access and privacy | Tools/status-only board; private ledger stays with volunteer. | Tools/status-only view; member access must exclude private records. Shared-laptop usability needs testing. |
| Cost | Inventory and price materials; $200 compliance is unverified. No software needed. | Repairs, storage/recovery, and setup must fit $200; software must have no recurring charge. Suitability and price are unverified. |
| Effort and waits | Consistent board updates and reconciliation may increase handling time while reducing corrections. | Single entry may save time; training, troubleshooting, and reconciliation can offset savings. |
| Reliability/recovery | Independent of internet/laptop; vulnerable to lost/illegible pages and missed updates. Retention/recovery practice needs review. | Independent of internet; depends on laptop/storage/power. Prepare recoverable copies and a temporary paper record with reconciliation. |

Neither candidate alone offers current information **before travel**. Remote publication or inquiry is unspecified. Fewer wasted trips cannot be claimed until checking location, freshness, and member behavior are understood.

## Feasibility and the next evidence

Assuming one three-minute transaction per arrival, ten arrivals require **30 volunteer-minutes in 30 minutes**: 100% nominal utilization, with no interruption/reconciliation margin. Nominal capacity is 20 transactions/hour, or 40 over two hours. These are conditional bounds; 40 members does not imply 40 weekly transactions. Arrival clustering, multiple transactions per visit, and service-time variation are unknown. No defensible expected wait follows. `capacity-check.txt` includes sensitivity calculations.

Proposed checks: inventory/cost materials; observe agreed Saturdays for arrivals, transactions/times, waits, discrepancies, administration, and wasted-visit reasons; ask members where they check availability. Compare a paper trial with a later offline laptop rehearsal using dummy records. Test an interruption, recovery, and borrower-identity separation; obtain volunteer/member feedback. Trial duration, acceptable waits, and priorities remain for the engineer to agree. No criterion weights are assumed.

## Your next consequential decision

**Choose a paper-workflow baseline trial, as recommended, or prioritize laptop assessment and rehearsal.** Also decide whether checking before travel is essential; if so, extend either candidate with a separately assessed communication mechanism. Purchase, deployment, final selection, and performance acceptance remain undecided. `concept.json` preserves both candidates and their evidence gaps.
