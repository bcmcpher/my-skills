# widget-edge Specification

## Purpose

Edge widgets.

## Requirements
### Requirement: Edge widgets have a size
An edge widget SHALL report its size once computed, and SHALL raise before it is computed so that no caller reads a stale size.

#### Scenario: Not computed
- **WHEN** `size()` is called before `compute()`
- **THEN** it raises
