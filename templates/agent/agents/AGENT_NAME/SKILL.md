---
name: agent-name
description: When should the main Claude instance delegate to this agent? Be specific about the trigger condition and what outcome the agent produces.
tools: Read, Grep, Glob, Bash
model: inherit
permissionMode: default
maxTurns: 20
---

You are a specialized assistant for [PURPOSE].

When invoked:
1. [Step one]
2. [Step two]
3. Return a concise summary of what you did and any output

Always [constraint]. Never [constraint].
