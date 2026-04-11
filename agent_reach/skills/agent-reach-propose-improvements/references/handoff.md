# Handoff

Use this skill as the first step in a maintainer workflow.

## Recommended Sequence

1. `agent-reach-propose-improvements`
   Turn external research into a clean shortlist of candidate proposals.
2. `agent-reach-maintain-proposals`
   Perform the formal maintainer review and decide which items are truly `adopt_now`, `defer`, or `reject`.
3. `agent-reach-maintain-release`
   Implement only approved slices, then validate, push, and reinstall from the exact pushed commit.

## Why This Split Is Safer

- proposal generation can stay creative without quietly widening implementation scope
- maintainer review can stay strict about Agent Reach policy and overlap
- release work receives only approved slices instead of a mixed idea list

## Handoff Contract

When passing output to maintainer review, keep only:

- the shortlisted proposals
- the evidence basis
- the suggested decision
- the proposed patch boundary
- the likely touchpoints

Do not carry forward discarded brainstorm items.
