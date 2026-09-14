"""Name-based call index for crane: defs, call sites, and enclosing callers."""
import ast, json, pathlib, sys
from collections import defaultdict
root = pathlib.Path(sys.argv[1])
defs = defaultdict(list)            # name -> [(qualname, file, line, kind)]
calls = defaultdict(set)            # name -> {(caller_qualname, file)}
for f in sorted(root.glob("src/**/*.py")) + sorted(root.glob("tests/**/*.py")) + sorted(root.glob("examples/**/*.py")):
    rel = str(f.relative_to(root)); tree = ast.parse(f.read_text())
    def walk(node, stack):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                q = ".".join(stack + [ch.name])
                if not isinstance(ch, ast.ClassDef) and rel.startswith("src/"):
                    kind = "method" if stack and stack[-1][:1].isupper() else "function"
                    defs[ch.name].append((q, rel, ch.lineno, kind))
                walk(ch, stack + [ch.name])
            else:
                if isinstance(ch, ast.Call):
                    fn = ch.func
                    name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
                    if name: calls[name].add((".".join(stack) or "<module>", rel))
                walk(ch, stack)
    walk(tree, [])
out = {n: {"def": d[0], "callers": sorted(calls.get(n, []))} for n, d in defs.items() if len(d) == 1 and not n.startswith("__")}
json.dump(out, open("/tmp/codegraph-eval/out/ast_calls.json", "w"), indent=1)
rows = sorted(((len(v["callers"]), n, v["def"][3], v["def"][1]) for n, v in out.items() if v["callers"]), reverse=True)
print(f"unique-name defs with >=1 caller: {len(rows)}")
for fanin in (1, 2, 3, 5, 8, 12, 20, 30):
    near = [r for r in rows if r[0] == fanin][:6]
    for r in near: print(f"  fan-in={r[0]:3d} {r[2]:8s} {r[1]:40s} {r[3]}")
print("top:", rows[:8])
