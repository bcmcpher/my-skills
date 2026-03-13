# BIDS Entities

Entities are key-value pairs in filenames (`key-value`). They must appear in the
canonical order below. Not all entities are valid for every datatype — omit those
that don't apply.

## Canonical entity ordering

| Order | Entity | Key | Example | Notes |
|-------|--------|-----|---------|-------|
| 1 | Subject | `sub` | `sub-01` | Required in every filename |
| 2 | Session | `ses` | `ses-baseline` | Optional; use when data spans multiple visits |
| 3 | Sample | `sample` | `sample-A` | Microscopy only |
| 4 | Task | `task` | `task-rest` | Required for func, beh, eeg, meg |
| 5 | Acquisition | `acq` | `acq-mp2rage` | Protocol/sequence variant |
| 6 | Contrast enhancing agent | `ce` | `ce-gadolinium` | |
| 7 | Reconstruction | `rec` | `rec-norm` | Reconstruction algorithm |
| 8 | Direction | `dir` | `dir-AP` | Phase-encoding direction |
| 9 | Run | `run` | `run-01` | Repeated identical acquisitions (1-indexed) |
| 10 | Modality | `mod` | `mod-T1w` | VFA modality label |
| 11 | Echo | `echo` | `echo-1` | Multi-echo (1-indexed) |
| 12 | Flip | `flip` | `flip-1` | Variable flip angle |
| 13 | Inversion | `inv` | `inv-1` | MP2RAGE inversion time |
| 14 | Magnetization transfer | `mt` | `mt-on` | `on` or `off` |
| 15 | Part | `part` | `part-mag` | `mag`, `phase`, `real`, `imag` |
| 16 | Processing | `proc` | `proc-filt` | Post-processing label |
| 17 | Hemisphere | `hemi` | `hemi-L` | `L` or `R` |
| 18 | Space | `space` | `space-MNI152NLin2009cAsym` | Coordinate space |
| 19 | Resolution | `res` | `res-1` | Spatial resolution variant |
| 20 | Density | `den` | `den-91k` | Surface density |
| 21 | Label | `label` | `label-GM` | Discrete label |
| 22 | Splitting | `split` | `split-1` | MEG data splits |
| 23 | Description | `desc` | `desc-preproc` | Free-form descriptor (last before suffix) |

## Filename pattern

```
sub-<label>[_ses-<label>][_<entity>-<label>…]_<suffix>.<extension>
```

- Label values: alphanumeric only (`[A-Za-z0-9]+`), no hyphens or underscores
- Suffix: the modality/file-type identifier (e.g. `bold`, `T1w`, `dwi`)
- Extension: `.nii`, `.nii.gz`, `.json`, `.tsv`, `.bvec`, `.bval`, etc.

## Examples

```
sub-01_task-rest_bold.nii.gz          # minimal func BOLD
sub-01_ses-01_task-nback_run-01_bold.nii.gz
sub-02_acq-mp2rage_inv-1_part-mag_T1map.nii.gz
sub-03_hemi-L_space-fsaverage_den-10k_desc-smoothed_bold.func.gii
```
