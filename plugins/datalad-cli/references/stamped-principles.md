# STAMPED Principles Reference

> Plugin-local distillation of Macdonald, Baker, To & Halchenko, *STAMPED principles for
> reproducible research objects* (Center for Open Neuroscience, Dartmouth, 2026). STAMPED is
> the framework the `datalad-stamped-assess` skill grades against. YODA (see
> `yoda-layout.md`) is STAMPED's **Self-containment + Modularity** origin — this reference
> covers the full seven.

STAMPED describes the *operational maturity* of a **research object** — a collection of data,
code, environment, and metadata that together represent the research as a complete,
re-runnable unit. Each principle is a **spectrum, not a pass/fail gate**. Requirements use
RFC 2119 keywords: **MUST** = the practical minimum (often what a careful researcher already
does); **SHOULD** / **MAY** = progressively more aspirational, tool-automated practice.

## The seven principles

| Letter | Principle | One-line meaning |
|--------|-----------|------------------|
| **S** | Self-containment | A complete retrieval unit — obtainable and understandable in scope without implicit external state ("don't look up"). |
| **T** | Tracking | The identity and provenance of every component is recorded (content-addressed versions + history). |
| **A** | Actionability | Machine-actionable instructions carry out the procedures — executable specs, not just prose. |
| **M** | Modularity | Independent, composable modules with clear boundaries (separation of concerns). |
| **P** | Portability | Runs on a different host while retaining its STAMPED properties — no undocumented host state. |
| **E** | Ephemerality | Execution happens in disposable environments rebuilt from spec each run. |
| **D** | Distributability | All modules are persistently retrievable by others in a frozen, licensed state. |

## Normative checklist backbone

Grade each item as satisfied / partial / unmet, citing evidence found in the research object.

- **Self-containment**
  - **S.1 (MUST)** — all modules essential to replicate execution are reachable within one
    top-level research object (literally or by explicit reference: subdatasets, registered URLs).
  - **S.2 (MUST)** — license declarations are retrievable alongside what they govern.
- **Tracking**
  - **T.1 (MUST)** — persistent content identification is recorded for all components.
  - **T.2 (SHOULD)** — all components use the same content-addressed VCS.
  - **T.3 (MUST)** — provenance of all modifications is recorded.
  - **T.4 (SHOULD / MUST)** — code-driven provenance is captured programmatically (SHOULD) and
    MUST include component versions.
- **Actionability**
  - **A.1 (MUST)** — sufficient instructions to reproduce all results are present.
  - **A.2 (SHOULD)** — procedures are executable specifications (`git clone`, `datalad rerun`,
    `conda env create`, `docker compose`), not just prose.
- **Modularity**
  - **M.1 (SHOULD)** — components are organized modularly.
  - **M.2 (MAY)** — modules are included directly or linked as subdatasets.
  - **M.3 (SHOULD)** — each module's license is declared independently and checked for
    compatibility at combination boundaries.
- **Portability**
  - **P.1 (MUST NOT)** — procedures do not depend on undocumented host state.
  - **P.2 (MUST)** — computational environments are explicitly specified.
  - **P.3 (MUST)** — environment definitions are version controlled.
- **Ephemerality**
  - **E.1 (SHOULD)** — results are produced in ephemeral environments rebuilt from spec.
- **Distributability**
  - **D.1 (MUST)** — all referenced modules are persistently retrievable by others.
  - **D.2 (SHOULD)** — environment specs support reproducible builds.
  - **D.3 (SHOULD)** — each module carries an explicit license with a resolvable identifier
    (SPDX / REUSE).

## DataLad tooling map — where to find evidence

STAMPED is tool-agnostic, but for a DataLad research object each principle maps to concrete
evidence and to skills in this plugin:

| Principle | Evidence to gather | Related skills / commands |
|-----------|--------------------|---------------------------|
| **S** | `.datalad/` present; inputs linked (not copied) via `.gitmodules`; registered URLs; a top-level README | `datalad-init`, `datalad-clone`, `datalad-subdatasets`, `datalad-addurls` |
| **T** | git history; git-annex content IDs; `datalad run` provenance in commit messages; `download-url` records | `datalad-log`, `datalad-run`, `datalad-status`, `datalad-diff` |
| **A** | a README/Makefile with runnable steps; `datalad run`/`rerun`-replayable commits | `datalad-run`, `datalad-log` |
| **M** | `inputs/`, `code/`, `outputs/` separation; subdatasets with their own boundaries/licenses | `datalad-subdatasets`, `datalad-clone` |
| **P** | env specs present (`Dockerfile`, `environment.yml`, `pyproject.toml`, `requirements.txt`); registered containers; no absolute host paths in provenance | `datalad-container-run`, `datalad-configuration` |
| **E** | container image registered and used by runs; env rebuilt per run rather than assumed | `datalad-container-run` |
| **D** | a sibling/remote configured; DOI (Zenodo/Figshare); a `LICENSE` / `.reuse/` with an SPDX id | `datalad-push`, `datalad-siblings`, `datalad-export` |

## YODA's place in STAMPED

The three YODA principles (see `yoda-layout.md`) are STAMPED's **Self-containment (S)** and
**Modularity (M)** origin: *everything is a (sub)dataset* (S/M), *record where data comes from*
(overlaps T), and *never modify a dataset you didn't create* (M boundaries). A YODA-compliant
dataset is a strong starting point but does not by itself satisfy Tracking, Actionability,
Portability, Ephemerality, or Distributability — which is what a STAMPED assessment surfaces.
