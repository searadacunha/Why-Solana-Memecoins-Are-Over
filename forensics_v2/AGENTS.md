# Publication and session handover

These instructions preserve the corrections merged on 4 November 2026. The
publication policy names a separate minimum commit for main, forensics-v2 and
ansem-network. Never change these anchors to make a failing check pass.

Before continuing an old session, inspect its branch, uncommitted changes and the
current remote head. Keep unfinished work on its own branch. Bring that work onto
the current destination with a reviewed Git merge or selected commits; do not
replace the destination with a whole checkout, backup or synchronized directory.
Do not force-push, reset away someone else's changes or merge PR #3 automatically.
The three branches have different research scopes and different README snapshots.

Every README present at a branch's policy anchor must keep its path, content and
file mode exactly. This includes README files inside research directories. New
research directories and their new README files are permitted. Put handover notes
and corrections in an appropriate technical document, not an existing README.
Keep frozen research inputs and outputs unchanged.

The guard examines committed trees and performs no fetch, checkout, reset, push or
write. Commit only the intended changes before checking the exact commit that will
be submitted. From the repository root, replace DESTINATION with the actual target
branch:

~~~bash
python forensics_v2/publication_guard.py --branch DESTINATION --commit HEAD
python code/check_no_secrets.py --require-clean
~~~

A missing baseline, missing policy or absent Git object is an error. Obtain the
required history and repeat the check; do not replace the failure with a skip.
For pull requests, the policy is selected by the base branch. Check the real head
commit as well as the simulated merge so the merge cannot hide a stale checkout.

The dedicated publication workflow fetches full history. It runs the original
historical-boundary test on forensics-v2 and ansem-network, and installs DuckDB so
their existing storage tests run. The rollback regression exists on forensics-v2;
it is not claimed as an Ansem test. Main uses its own existing regression tests
and does not run the historical boundary or tracing modules from other branches.
The guard and policy live here so they respect the historical allowed prefixes.

Preserve the regression tests from the correction commits. Ancestry alone cannot
detect a later commit that deliberately restores old code; the tests provide that
additional check. Inspect the resulting diff and CI for the exact submitted commit.

This workflow is not a GitHub branch-protection rule. Repository administrators
must require its successful check and prevent force-pushes to enforce it against
direct writes. A passing software check does not validate research conclusions.
