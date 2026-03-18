---
name: hello
description: >
  Greet the user with a friendly message that includes context about their current project
  directory and any open files. Invoke when the user says hello, hi, or greet, or runs /hello.
  Do NOT trigger for task requests that happen to start with a greeting (e.g., "Hello, fix my bug").
argument-hint: [name]
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Glob
---

# Skill: hello

Greet the user warmly. If $ARGUMENTS contains a name, address them by that name.

## Steps

1. Say hello to the user. If $ARGUMENTS contains a name, address them by that name.
   If $ARGUMENTS is empty, omit the name and greet generically.
2. Use the Glob tool to list files in the current directory (top-level only).
3. Mention 1-3 interesting files or the general purpose of the project if you can infer it.
4. Offer to help with whatever they are working on.

## Constraints

- Keep the greeting to 3-5 sentences — friendly but brief.
- Never make up project details you cannot see from the file listing.
- If the directory is empty, just greet warmly and ask what they are building.
