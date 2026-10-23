# Briefing another tool

An external model gives a read that is not anchored on yours. It is also likely to sample
a dimension and report it as swept. In one audit, three passes by an external tool
reported 16 private-detail tests in 8 files where the script finds 151 in 52, and gave
"checked and sound" lines with no method behind them.

So split the work: the scripts sweep, the external tool judges.

1. Run every script in `dimensions.md` yourself and save the reports.
2. Write a brief that gives the tool:
   - the project rules to read, and the files it must not read (pending changes, your
     own conclusions, earlier audits);
   - the script reports, as its candidate lists;
   - the judgment rule per dimension, from `dimensions.md`;
   - the report template, with its "method and count" rule.
3. Ask for one verdict per candidate: `finding`, `rejected: <reason>` or `merged: <id>`.
   A candidate without a verdict is an incomplete pass.
4. Check the returned report mechanically before reading it: count verdicts against
   candidates per dimension. Then spot-check five rejections per dimension.

Do not send a second pass for a dimension the tool left incomplete. Judge the remaining
candidates yourself; repeated passes cost more than they recover.
