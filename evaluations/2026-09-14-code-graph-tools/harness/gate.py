"""Gate a set of v3 runs: did the graph tool get used, and did the answer come from it?

usage: gate.py <run-name> [...]   run-name like Q1.crg.r1 (files in v3/runs/)

Per run:
  usable graph calls  graph tool results that are not errors, `ambiguous`, or `not_found`
  graph-first share   of the truth items this tool can reach (v3/truth.json "reachable"), the share
                      that a graph result named before any Grep/Read/Glob/Bash result did
  answer score        truth items named in the final answer
PASS = ≥1 usable graph call AND graph-first share ≥ 50% (when the tool can reach anything).
"""
import json, re, sys
V = "/tmp/codegraph-eval/v3"; truth = json.load(open(f"{V}/truth.json"))
def mention(i, t):
    """Symbol names match on word boundaries. Module paths (crane/pkg/mod.py) also match
    `pkg/mod.py` and the dotted `crane.pkg.mod`; a package `__init__.py` also matches `crane.pkg`."""
    if "/" not in i:
        return re.search(rf"(?<![\w/]){re.escape(i)}\b", t) is not None
    rel = i.split("crane/", 1)[1]
    dotted = "crane." + rel[:-3].replace("/", ".")
    if dotted.endswith(".__init__"): dotted = dotted[: -len(".__init__")]
    return rel in t or re.search(rf"{re.escape(dotted)}(?![\w.])", t) is not None
for run in sys.argv[1:]:
    q, arm = run.split(".")[:2]
    msgs = [json.loads(l) for l in open(f"{V}/runs/{run}.stream.jsonl") if l.strip().startswith("{")]
    names, order = {}, []
    for m in msgs:
        content = m.get("message", {}).get("content")
        if not isinstance(content, list): continue
        for c in content:
            if m["type"] == "assistant" and c.get("type") == "tool_use": names[c["id"]] = c["name"]
            if m["type"] == "user" and c.get("type") == "tool_result":
                t = c.get("content"); text = t if isinstance(t, str) else "\n".join(x.get("text", "") for x in t if isinstance(x, dict))
                order.append((names.get(c["tool_use_id"], "?"), text, bool(c.get("is_error"))))
    result = next((m for m in reversed(msgs) if m.get("type") == "result"), {})
    graph = [(n, t, e) for n, t, e in order if n.startswith("mcp__")]
    usable = [g for g in graph if not g[2] and not re.search(r'"status":\s*"(ambiguous|not_found|error)"', g[1])]
    items = truth[q]["items"]; reach = (truth[q]["reachable"].get(arm) or []) if arm != "base" else []
    first = {}
    for i in items:
        for n, t, _ in order:
            if mention(i, t): first[i] = "graph" if n.startswith("mcp__") else "other"; break
    gshare = (sum(first.get(i) == "graph" for i in reach) / len(reach)) if reach else None
    score = sum(mention(i, result.get("result") or "") for i in items)
    tools = {}
    for n, _, _ in order: tools[n] = tools.get(n, 0) + 1
    verdict = "n/a (baseline)" if arm == "base" else ("PASS" if usable and (gshare is None or gshare >= 0.5) else "FAIL")
    u = result.get("usage", {})
    print(f"{run:12s} {verdict:14s} graph calls={len(graph)} usable={len(usable)} "
          f"graph-first={'-' if gshare is None else f'{gshare:.0%} of {len(reach)} reachable'} "
          f"answer={score}/{len(items)} cost=${result.get('total_cost_usd', 0):.2f} "
          f"tokens(in/cw/cr/out)={u.get('input_tokens')}/{u.get('cache_creation_input_tokens')}/{u.get('cache_read_input_tokens')}/{u.get('output_tokens')} tools={tools}")
