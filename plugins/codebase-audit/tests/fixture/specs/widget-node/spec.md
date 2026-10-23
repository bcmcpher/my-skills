# widget-node Specification

## Purpose

Node widgets.

## Requirements
### Requirement: Node widgets have a size
A node widget SHALL report its size once computed, and SHALL raise before it is computed so that no caller reads a stale size.

#### Scenario: Not computed
- **WHEN** `size()` is called before `compute()`
- **THEN** it raises and `_cache` stays `None`
