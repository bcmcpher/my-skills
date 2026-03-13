# BIDS Datatypes and Suffixes

## Dataset-level required files

```
dataset_description.json   # REQUIRED: name, BIDSVersion, License, Authors, …
README                     # REQUIRED: plain text or .md
participants.tsv           # RECOMMENDED: one row per subject
participants.json          # RECOMMENDED: column descriptions
CHANGES                    # RECOMMENDED: changelog
.bidsignore                # Optional: gitignore-style exclusions
```

`dataset_description.json` minimum required fields:
```json
{
  "Name": "My Dataset",
  "BIDSVersion": "1.9.0"
}
```

## Datatype directories and common suffixes

### `anat/` — Anatomical MRI

| Suffix | Description |
|--------|-------------|
| `T1w` | T1-weighted |
| `T2w` | T2-weighted |
| `FLAIR` | Fluid attenuated inversion recovery |
| `T2star` | T2* map |
| `T1map` | Quantitative T1 |
| `T2map` | Quantitative T2 |
| `PD` | Proton density |
| `PDmap` | Quantitative PD |
| `UNIT1` | MP2RAGE uniform T1 image |
| `angio` | MR angiography |
| `defacemask` | Defacing mask |

### `func/` — Functional MRI

| Suffix | Description |
|--------|-------------|
| `bold` | BOLD time series (requires `task` entity) |
| `cbv` | Cerebral blood volume |
| `phase` | Phase time series |
| `sbref` | Single-band reference |
| `events` | Stimulus events (`.tsv`) |
| `physio` | Physiological recording |
| `stim` | Stimulus recording |

### `dwi/` — Diffusion MRI

| Suffix | Description |
|--------|-------------|
| `dwi` | Diffusion-weighted image |
| `sbref` | Single-band reference |
| `bvec` | Gradient directions (`.bvec`) |
| `bval` | b-values (`.bval`) |

### `fmap/` — Field maps

| Suffix | Description |
|--------|-------------|
| `phasediff` | Phase difference map |
| `phase1`, `phase2` | Individual phase images |
| `magnitude1`, `magnitude2` | Magnitude images |
| `magnitude` | Single magnitude |
| `fieldmap` | Direct field map (Hz) |
| `epi` | Opposite phase-encoded EPI (requires `dir`) |
| `TB1map` | B1+ transmit field |
| `RB1map` | B1- receive field |

### `perf/` — Perfusion (ASL)

| Suffix | Description |
|--------|-------------|
| `asl` | ASL time series |
| `m0scan` | M0 calibration scan |
| `aslcontext` | Volume type labels (`.tsv`) |

### `eeg/` — EEG

| Suffix | Description |
|--------|-------------|
| `eeg` | EEG data |
| `channels` | Channel list (`.tsv`) |
| `events` | Events (`.tsv`) |
| `electrodes` | Electrode locations (`.tsv`) |
| `coordsystem` | Coordinate system (`.json`) |
| `headshape` | Head shape digitization |
| `photo` | Electrode placement photo |

### `ieeg/` — Intracranial EEG

Same structure as `eeg/`; suffix `ieeg`.

### `meg/` — MEG

| Suffix | Description |
|--------|-------------|
| `meg` | MEG data |
| `channels`, `events`, `coordsystem`, `headshape`, `electrodes` | Same as EEG |
| `photo` | Sensor placement photo |

### `pet/` — Positron Emission Tomography

| Suffix | Description |
|--------|-------------|
| `pet` | PET time series |
| `events` | Events (`.tsv`) |
| `blood` | Blood recording (`.tsv`) |

### `beh/` — Behavioral

| Suffix | Description |
|--------|-------------|
| `events` | Events (`.tsv`); requires `task` entity |
| `physio`, `stim` | Physiological / stimulus |
| `beh` | Behavioral data |

### `micr/` — Microscopy

| Suffix | Description |
|--------|-------------|
| `TEM`, `SEM`, `uCT`, `BF`, `DF`, `PC`, `DIC`, `FLUO`, `CONF`, `PLI`, `CARS`, `2PE`, `MPE`, `SR`, `NLO`, `OCT`, `SPIM` | Various microscopy modalities |

### Derivatives (`derivatives/<pipeline>/`)

Derivatives live outside the raw BIDS root. Common patterns:

```
derivatives/
└── fmriprep/
    └── sub-01/
        ├── anat/
        │   └── sub-01_space-MNI152NLin2009cAsym_desc-preproc_T1w.nii.gz
        └── func/
            └── sub-01_task-rest_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
```

Use `desc` entity to distinguish derivative variants; `space` for coordinate space.
