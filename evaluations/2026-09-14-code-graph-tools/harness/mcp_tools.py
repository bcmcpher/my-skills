"""Speak MCP over stdio: initialize, then tools/list; dump the tool schemas as JSON."""
import json, subprocess, sys, os
out, cmd = sys.argv[1], sys.argv[2:]
p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, cwd="/tmp/codegraph-eval/crane")
def send(m): p.stdin.write(json.dumps(m) + "\n"); p.stdin.flush()
def recv(i):
    while True:
        line = p.stdout.readline()
        if not line: raise SystemExit(f"server closed: {cmd}")
        try: m = json.loads(line)
        except ValueError: continue
        if m.get("id") == i: return m
send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "eval", "version": "0"}}})
recv(1); send({"jsonrpc": "2.0", "method": "notifications/initialized"})
send({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
tools = recv(2)["result"]["tools"]; p.kill()
json.dump(tools, open(out, "w"), indent=1)
print(f"{len(tools)} tools, {len(json.dumps(tools))} chars -> {out}:", [t["name"] for t in tools])
