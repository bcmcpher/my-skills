# Nipoppy Pipeline Commands: `run`, `track`, and `extract`

## Shared pipeline options

All three commands (`run`, `track`, `extract`) accept these options:

| Option | Default | Description |
|--------|---------|-------------|
| `--dataset PATH` | cwd | Path to the nipoppy dataset root. |
| `--pipeline NAME` | — | Pipeline name (e.g., `fmriprep`, `mriqc`). **Required** unless only one pipeline is configured. |
| `--pipeline-version VERSION` | config | Pipeline version. Must match a pulled Apptainer image. |
| `--pipeline-step STEP` | config | Sub-step within the pipeline (if the pipeline defines multiple steps). |
| `--participant-id ID` | all | Operate on a single participant only. |
| `--session-id ID` | all | Operate on a single session only. |
| `--verbose` / `-v` | off | Increase log verbosity. |

---

## `nipoppy run`

Execute a processing pipeline (fMRIPrep, MRIQC, etc.) on BIDS data. Invokes the
pipeline container via Apptainer and Boutiques.

**Platform requirement:** Linux + Apptainer. Will not work on macOS or Windows.

### Synopsis

```bash
nipoppy run [OPTIONS]
```

### Additional options (beyond shared)

| Option | Default | Description |
|--------|---------|-------------|
| `--keep-workdir` | off | Preserve the pipeline's working directory in `scratch/` after completion. Useful for debugging. |
| `--tar` | off | Compress the output directory into a `.tar.gz` archive after completion. |
| `--simulate` | off | Print the Boutiques/Apptainer invocation without executing. |
| `--dry-run` / `-n` | off | Alias for `--simulate`. |
| `--write-list PATH` | — | Write job commands to a file for HPC submission. |

### Pipeline config in `config.json`

```json
{
  "PROC_PIPELINES": {
    "fmriprep": {
      "VERSION": "23.1.3",
      "STEP": "default",
      "CONTAINER": "/containers/fmriprep_23.1.3.sif",
      "DESCRIPTOR": "./code/boutiques/fmriprep_descriptor.json"
    },
    "mriqc": {
      "VERSION": "23.1.0",
      "CONTAINER": "/containers/mriqc_23.1.0.sif"
    }
  }
}
```

### HPC / parallel execution

For large cohorts, generate a job list and submit as a SLURM array:

```bash
# Generate job list
nipoppy run --pipeline fmriprep --write-list /tmp/fmriprep_jobs.txt

# Submit array (example SLURM)
sbatch --array=1-$(wc -l < /tmp/fmriprep_jobs.txt) run_array.sh
```

`run_array.sh` reads line `$SLURM_ARRAY_TASK_ID` from the job list and executes it.

### Example invocations

```bash
# Dry-run fMRIPrep on all participants
nipoppy run --pipeline fmriprep --simulate

# Run fMRIPrep on all participants
nipoppy run --pipeline fmriprep --pipeline-version 23.1.3

# Run MRIQC on one participant, preserving workdir
nipoppy run --pipeline mriqc --participant-id sub-001 --session-id ses-01 --keep-workdir

# Generate job list for HPC
nipoppy run --pipeline fmriprep --write-list /tmp/jobs.txt
```

---

## `nipoppy track`

Record per-participant pipeline completion status into the processing status file
(`tabular/bagel.tsv`). Run after `nipoppy run` to update tracking.

### Synopsis

```bash
nipoppy track [OPTIONS]
```

### No additional options beyond shared.

### Bagel file schema (`bagel.tsv`)

| Column | Values | Description |
|--------|--------|-------------|
| `participant_id` | string | Subject ID |
| `session` | string | Session label |
| `pipeline_name` | string | Pipeline identifier (e.g., `fmriprep`) |
| `pipeline_version` | string | Pipeline version string |
| `pipeline_step` | string | Step label |
| `status` | `SUCCESS`/`FAIL`/`INCOMPLETE`/`UNAVAILABLE` | Completion status |
| `bids_id` | string | BIDS subject ID used by the pipeline |

### Status values

| Value | Meaning |
|-------|---------|
| `SUCCESS` | Pipeline completed without errors; expected outputs present |
| `FAIL` | Pipeline ran but reported errors or missing outputs |
| `INCOMPLETE` | Pipeline started but did not finish (e.g., job killed) |
| `UNAVAILABLE` | Participant/session not eligible (e.g., no BIDS data) |

### Example invocations

```bash
# Track fMRIPrep status for all participants
nipoppy track --pipeline fmriprep --pipeline-version 23.1.3

# Track for a single participant
nipoppy track --pipeline fmriprep --participant-id sub-001 --session-id ses-01
```

---

## `nipoppy extract`

Extract imaging-derived phenotypes (IDPs) from pipeline outputs into analysis-ready
tabular files. Each extractor is defined by a Boutiques descriptor in `config.json`.

**Platform requirement:** Linux + Apptainer (for containerized extractors). Some
extractors may run natively if the extractor binary is available on PATH.

### Synopsis

```bash
nipoppy extract [OPTIONS]
```

### Additional options (beyond shared)

| Option | Default | Description |
|--------|---------|-------------|
| `--simulate` | off | Print the extraction command without executing. |
| `--dry-run` / `-n` | off | Alias for `--simulate`. |
| `--write-list PATH` | — | Write extraction commands to a file for HPC submission. |

### Output format

Extractors write analysis-ready TSV files to `derivatives/<pipeline>/<version>/` or
to a path specified in the extractor descriptor. Each file typically has one row per
participant-session and one column per IDP measure.

### Common extractor pipelines

| Pipeline | What is extracted |
|----------|------------------|
| `fmriprep` | Motion parameters, confound regressors, tissue probability maps |
| `mriqc` | Image quality metrics (IQMs): SNR, TSNR, FD, DVARS, etc. |
| `freesurfer` | Cortical thickness, surface area, subcortical volumes |
| `tractoflow` | Diffusion tensor metrics: FA, MD, AD, RD per tract |

### Extractor config in `config.json`

```json
{
  "EXTRACTORS": {
    "mriqc": {
      "VERSION": "23.1.0",
      "STEP": "extract",
      "DESCRIPTOR": "./code/boutiques/mriqc_extractor.json"
    }
  }
}
```

### Example invocations

```bash
# Dry-run MRIQC IDP extraction
nipoppy extract --pipeline mriqc --simulate

# Extract MRIQC IDPs for all participants
nipoppy extract --pipeline mriqc --pipeline-version 23.1.0

# Extract fMRIPrep confounds for one participant
nipoppy extract --pipeline fmriprep --participant-id sub-001 --session-id ses-01

# Generate extraction job list for HPC
nipoppy extract --pipeline freesurfer --write-list /tmp/extract_jobs.txt
```

### Workflow position

`extract` is the final step. After extraction:
- Review IDP tables in `derivatives/`
- Merge with phenotypic data from `tabular/` for downstream analysis
- Use `nipoppy status` to confirm all participants have been processed and extracted
