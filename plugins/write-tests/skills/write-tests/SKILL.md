---
name: write-tests
description: write unit tests for a passed file
argument-hint: a source code file
user-invocable: true
disable-model-invocation: false
allowed-tools: Read, Grep, Glob
---

# Skill: write-tests

Write comprehensive unit tests for a source code file: $ARGUMENT

Perform and validate tests for functions / classes one at a time.

Write tests with conditions that fail first, then write the correct condition.

Make sure all tests pass before moving on.

Coverage:
- Test paths
- Test edge cases
- Test error states

## Steps

1. Identify a unit to test.
2. Create a plan for complete coverage of the object.
3. Write a negative test - one that fails has bad inputs and should fail
4. Create the positive test - one that passes with correct inputs.

## Constraints

- Always flag tests you create as AI generated
- Never modifiy or remove non-AI generated tests
- Never change source code to make tests pass - that is not the goal in this process.
