"""Aggregate the full matrix (reps r3-r6, variant b): medians per question x arm, plus pooled totals.

Per run: answer score, API-rate cost, token classes, wall time, tool calls by kind (graph / Read /
Grep / Glob), and — for graph arms — graph-first share of reachable truth (as in gate.py).
"""
import glob, json, re, statistics as st, collections
V = "/tmp/codegraph-eval/v3"; truth = json.load(open(f"{V}/truth.json"))
def mention(i, t):
    if "/" not in i: return re.search(rf"(?<![\w/]){re.escape(i)}\b", t) is not None
    rel = i.split("crane/", 1)[1]; dotted = "crane." + rel[:-3].replace("/", ".")
    if dotted.endswith(".__init__"): dotted = dotted[: -len(".__init__")]
    return rel in t or re.search(rf"{re.escape(dotted)}(?![\w.])", t) is not None
rows = collections.defaultdict(list)
for path in sorted(glob.glob(f"{V}/runs/Q?.*.r[3-6].b.stream.jsonl")):
    run = path.split("/")[-1][: -len(".stream.jsonl")]; q, arm = run.split(".")[:2]
    msgs = [json.loads(l) for l in open(path) if l.strip().startswith("{")]
    res = next((m for m in reversed(msgs) if m.get("type") == "result"), None)
    if not res: continue
    names, order = {}, []
    for m in msgs:
        cl = m.get("message", {}).get("content")
        if not isinstance(cl, list): continue
        for c in cl:
            if m["type"] == "assistant" and c.get("type") == "tool_use": names[c["id"]] = c["name"]
            if m["type"] == "user" and c.get("type") == "tool_result":
                t = c.get("content"); order.append((names.get(c["tool_use_id"], "?"), t if isinstance(t, str) else "\n".join(x.get("text", "") for x in t if isinstance(x, dict))))
    kinds = collections.Counter("graph" if n.startswith("mcp__") else n for n, _ in order)
    items = truth[q]["items"]; reach = truth[q]["reachable"].get(arm) or [] if arm != "base" else []
    first = {}
    for i in items:
        for n, t in order:
            if mention(i, t): first[i] = n.startswith("mcp__"); break
    u = res.get("usage", {})
    rows[(q, arm)].append({
        "score": sum(mention(i, res.get("result") or "") for i in items) / len(items),
        "cost": res.get("total_cost_usd", 0), "secs": (res.get("duration_ms") or 0) / 1000,
        "in": u.get("input_tokens", 0), "cw": u.get("cache_creation_input_tokens", 0), "cr": u.get("cache_read_input_tokens", 0), "out": u.get("output_tokens", 0),
        "graph": kinds["graph"], "read": kinds["Read"], "grep": kinds["Grep"] + kinds["Glob"], "calls": sum(kinds.values()),
        "gfirst": (sum(first.get(i, False) for i in reach) / len(reach)) if reach else None, "error": res.get("is_error") or res.get("subtype") != "success"})
med = lambda xs: st.median(xs) if xs else float("nan")
print(f"{'Q':3s} {'arm':5s} {'n':>2s} {'score':>6s} {'cost$':>6s} {'secs':>5s} {'calls':>5s} {'graph':>5s} {'read':>4s} {'grep':>4s} {'ctx_k':>6s} {'out_k':>5s} {'g-first':>7s}  (medians; ctx_k = input+cache write+cache read, thousands)")
for q in ("Q1", "Q2", "Q3", "Q4"):
    for arm in ("base", "crg", "cg"):
        r = rows.get((q, arm), [])
        if not r: print(f"{q:3s} {arm:5s}  0  (no runs yet)"); continue
        gf = [x["gfirst"] for x in r if x["gfirst"] is not None]
        print(f"{q:3s} {arm:5s} {len(r):2d} {med([x['score'] for x in r]):6.0%} {med([x['cost'] for x in r]):6.2f} {med([x['secs'] for x in r]):5.0f} "
              f"{med([x['calls'] for x in r]):5.1f} {med([x['graph'] for x in r]):5.1f} {med([x['read'] for x in r]):4.1f} {med([x['grep'] for x in r]):4.1f} "
              f"{med([(x['in']+x['cw']+x['cr'])/1000 for x in r]):6.0f} {med([x['out']/1000 for x in r]):5.1f} {(f'{med(gf):.0%}' if gf else '-'):>7s}"
              + (f"  errors={sum(x['error'] for x in r)}" if any(x["error"] for x in r) else ""))
print("\npooled across questions:")
for arm in ("base", "crg", "cg"):
    r = [x for (q, a), xs in rows.items() if a == arm for x in xs]
    if r: print(f"  {arm:5s} runs={len(r):2d} total_cost=${sum(x['cost'] for x in r):.2f} median_cost=${med([x['cost'] for x in r]):.2f} "
                f"mean_score={st.mean(x['score'] for x in r):.0%} median_calls={med([x['calls'] for x in r])} runs_with_graph_call={sum(x['graph']>0 for x in r)}/{len(r)}")
