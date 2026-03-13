# BIDS JSON Sidecar Fields

Sidecar inheritance: a `.json` file applies to all files that match its name up to
the point where it is defined. More specific sidecars override less specific ones.

```
# Least specific → most specific
dataset_description.json
sub-01/sub-01_task-rest_bold.json     ← applies only to this file
```

---

## Functional MRI (`func/` — `bold`, `cbv`, `phase`)

### Required
| Field | Type | Description |
|-------|------|-------------|
| `RepetitionTime` | number | TR in seconds |
| `TaskName` | string | Must match `task-<label>` entity |

### Strongly recommended
| Field | Type | Description |
|-------|------|-------------|
| `SliceTiming` | array | Slice acquisition times (s), length = number of slices |
| `PhaseEncodingDirection` | string | `i`, `j`, `k`, `i-`, `j-`, `k-` |
| `TotalReadoutTime` | number | Effective echo spacing × (PE steps − 1) |
| `EchoTime` | number | TE in seconds |
| `FlipAngle` | number | degrees |
| `MultibandAccelerationFactor` | integer | SMS factor |
| `NumberOfVolumesDiscardedByScanner` | integer | Dummies removed before export |
| `NumberOfVolumesDiscardedByUser` | integer | Dummies removed during processing |

---

## Anatomical MRI (`anat/`)

### Recommended
| Field | Type | Description |
|-------|------|-------------|
| `EchoTime` | number | TE in seconds |
| `FlipAngle` | number | degrees |
| `RepetitionTime` | number | TR in seconds |
| `InversionTime` | number | TI in seconds (MP2RAGE, IR sequences) |
| `MagneticFieldStrength` | number | Scanner field strength in Tesla |
| `Manufacturer` | string | e.g. `"Siemens"` |
| `ManufacturersModelName` | string | e.g. `"Prisma"` |
| `ReceiveCoilName` | string | |
| `PulseSequenceType` | string | e.g. `"MPRAGE"` |

---

## Diffusion MRI (`dwi/`)

### Required
| Field | Type | Description |
|-------|------|-------------|
| (none beyond scanner params) | | `.bvec` and `.bval` files are required alongside `.nii.gz` |

### Recommended
| Field | Type | Description |
|-------|------|-------------|
| `PhaseEncodingDirection` | string | `i`, `j`, `k` etc. |
| `TotalReadoutTime` | number | For distortion correction |
| `EchoTime` | number | TE in seconds |
| `MultibandAccelerationFactor` | integer | |

---

## Field maps (`fmap/`)

### `phasediff` / `phase1` / `phase2`
| Field | Required | Description |
|-------|----------|-------------|
| `EchoTime1` | REQUIRED | TE of first echo (s) |
| `EchoTime2` | REQUIRED | TE of second echo (s) |
| `IntendedFor` | REQUIRED | Path(s) relative to subject dir of files this corrects |

### `epi` (opposite phase-encode)
| Field | Required | Description |
|-------|----------|-------------|
| `PhaseEncodingDirection` | REQUIRED | |
| `TotalReadoutTime` | REQUIRED | |
| `IntendedFor` | REQUIRED | |

### `fieldmap` (direct Hz map)
| Field | Required | Description |
|-------|----------|-------------|
| `Units` | REQUIRED | `"Hz"` |
| `IntendedFor` | REQUIRED | |

`IntendedFor` example:
```json
{
  "IntendedFor": [
    "ses-01/func/sub-01_ses-01_task-rest_bold.nii.gz"
  ]
}
```

---

## EEG / iEEG (`eeg/`, `ieeg/`)

### `*_eeg.json` — Required
| Field | Description |
|-------|-------------|
| `TaskName` | Must match task entity |
| `SamplingFrequency` | Hz |
| `PowerLineFrequency` | 50 or 60 Hz |
| `SoftwareFilters` | `"n/a"` or object of filter specs |
| `EEGReference` | e.g. `"CZ"`, `"average"` |
| `EEGPlacementScheme` | e.g. `"10-20"` |

### `*_channels.tsv` — Required columns
`name`, `type`, `units`

Optional: `sampling_frequency`, `low_cutoff`, `high_cutoff`, `notch`, `status`, `status_description`

---

## MEG (`meg/`)

### `*_meg.json` — Required
| Field | Description |
|-------|-------------|
| `TaskName` | |
| `SamplingFrequency` | Hz |
| `PowerLineFrequency` | 50 or 60 Hz |
| `DewarPosition` | e.g. `"upright"` |
| `SoftwareFilters` | |
| `DigitizedLandmarks` | boolean |
| `DigitizedHeadPoints` | boolean |

---

## PET (`pet/`)

### `*_pet.json` — Required
| Field | Description |
|-------|-------------|
| `Manufacturer` | |
| `ManufacturersModelName` | |
| `Units` | `"Bq/mL"` etc. |
| `TracerName` | e.g. `"FDG"` |
| `TracerRadionuclide` | e.g. `"F18"` |
| `InjectedRadioactivity` | MBq |
| `InjectedRadioactivityUnits` | `"MBq"` |
| `InjectedMass` | nmol |
| `InjectedMassUnits` | `"nmol"` |
| `SpecificRadioactivity` | MBq/nmol |
| `SpecificRadioactivityUnits` | |
| `ModeOfAdministration` | `"bolus"` / `"infusion"` / `"bolus-infusion"` |
| `FrameTimesStart` | array (s) |
| `FrameDuration` | array (s) |
| `AcquisitionMode` | `"list mode"` / `"dynamic"` / `"static"` / `"gated"` |
| `ImageDecayCorrected` | boolean |
| `ImageDecayCorrectionTime` | s |
| `ReconMethodName` | |
| `ReconFilterType` | array |
| `ReconFilterSize` | array |
| `AttenuationCorrection` | |

---

## Shared MRI scanner parameters (recommended in all MRI sidecars)

```json
{
  "MagneticFieldStrength": 3,
  "Manufacturer": "Siemens",
  "ManufacturersModelName": "Prisma",
  "InstitutionName": "...",
  "DeviceSerialNumber": "...",
  "StationName": "...",
  "SoftwareVersions": "...",
  "MRAcquisitionType": "2D",
  "SequenceName": "...",
  "SequenceVariant": "SK",
  "ScanOptions": "FS",
  "ImageType": ["ORIGINAL", "PRIMARY", "M", "ND", "NORM"],
  "SliceThickness": 3,
  "SpacingBetweenSlices": 3.75,
  "MatrixCoilMode": "GRAPPA"
}
```
