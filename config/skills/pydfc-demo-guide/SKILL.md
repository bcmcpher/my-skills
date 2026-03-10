---
name: pydfc-demo-guide
description: Use when a user wants a simple guided walkthrough of installing pydfc and running the dFC demo notebook workflow, including downloading sample data and choosing a dFC method (SW, TF, CAP, SWC, HMM, or WINDOWLESS) with copy-paste code snippets.
---

# pydfc Demo Guide (Simple)

Use this skill for a lightweight, interactive walkthrough based on `dFC_methods_demo.ipynb`.

## Goal

Help the user:

1. Install `pydfc`
2. Download the demo sample data used in `dFC_methods_demo.ipynb`
3. Load the data into `TIME_SERIES` objects (`BOLD` or `BOLD_multi`)
4. Choose one dFC method and run it
5. Ask whether they want to try another method

Keep the interaction simple and copy-paste oriented.

## Interaction Flow

Follow this sequence:

1. Ask whether they want:
   - `State-free` method (single subject; fastest start), or
   - `State-based` method (multi-subject; requires fitting)
2. If not installed yet, provide installation commands.
3. Provide the exact data download commands for the chosen path.
4. Provide the minimal loading code (`BOLD` or `BOLD_multi`).
5. Ask: `Which dFC method would you like to use?`
6. Show the matching copy-paste code block.
7. After results are shown, ask: `Are there any other methods you are curious about?`

## Source of Truth in Repo

- `README.rst` for install commands
- `dFC_methods_demo.ipynb` for data download and method examples

Prefer the root notebook (`dFC_methods_demo.ipynb`) unless the user explicitly points to `examples/dFC_methods_demo.ipynb`.

## Installation (from README)

Share this first when needed:

```bash
conda create --name pydfc_env python=3.11
conda activate pydfc_env
pip install pydfc
```

## Common Imports

Use this in notebook cells before method-specific code:

```python
from pydfc import data_loader
import numpy as np
import warnings

warnings.simplefilter("ignore")
```

## State-Free Path (Single Subject)

### 1) Download demo data (Notebook cell)

If the user is in Jupyter, provide exactly:

```python
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0001/func/sub-0001_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz?versionId=UfCs4xtwIEPDgmb32qFbtMokl_jxLUKr -o sample_data/sub-0001_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0001/func/sub-0001_task-restingstate_acq-mb3_desc-confounds_regressors.tsv?versionId=biaIJGNQ22P1l1xEsajVzUW6cnu1_8lD -o sample_data/sub-0001_task-restingstate_acq-mb3_desc-confounds_regressors.tsv
```

If they are using a terminal, remove the leading `!`.

### 2) Load `BOLD`

```python
BOLD = data_loader.nifti2timeseries(
    nifti_file="sample_data/sub-0001_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz",
    n_rois=100,
    Fs=1 / 0.75,
    subj_id="sub-0001",
    confound_strategy="no_motion",  # no_motion, no_motion_no_gsr, or none
    standardize=False,
    TS_name=None,
    session=None,
)

BOLD.visualize(start_time=0, end_time=1000, nodes_lst=range(10))
```

### 3) Ask Which Method

Ask exactly (or very close):

`Which dFC method would you like to use to assess dFC? (SW or TF for the simple state-free path)`

### 4) Method Snippets (State-Free)

#### Sliding Window (SW)

```python
from pydfc.dfc_methods import SLIDING_WINDOW

params_methods = {
    "W": 44,                 # window length (sec)
    "n_overlap": 0.5,
    "sw_method": "pear_corr",
    "tapered_window": True,
    "normalization": True,
    "num_select_nodes": None,  # e.g., 50 for faster runs
}

measure = SLIDING_WINDOW(**params_methods)
dFC = measure.estimate_dFC(time_series=BOLD)
dFC.visualize_dFC(TRs=dFC.TR_array[:], normalize=False, fix_lim=False)
```

Optional summary plot:

```python
import matplotlib.pyplot as plt

avg_dFC = np.mean(np.mean(dFC.get_dFC_mat(), axis=1), axis=1)
plt.figure(figsize=(10, 3))
plt.plot(dFC.TR_array, avg_dFC)
plt.show()
```

#### Time-Frequency (TF)

```python
from pydfc.dfc_methods import TIME_FREQ

params_methods = {
    "TF_method": "WTC",
    "n_jobs": 2,
    "verbose": 0,
    "backend": "loky",
    "normalization": True,
    "num_select_nodes": None,  # e.g., 50 for faster runs
}

measure = TIME_FREQ(**params_methods)
dFC = measure.estimate_dFC(time_series=BOLD)
TRs = dFC.TR_array[np.arange(29, 480 - 29, 29)]
dFC.visualize_dFC(TRs=TRs, normalize=True, fix_lim=False)
```

## State-Based Path (Multi Subject)

State-based methods require fitting FC states on multiple subjects first.

### 1) Download demo data for 5 subjects (Notebook cells)

```python
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0001/func/sub-0001_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz?versionId=UfCs4xtwIEPDgmb32qFbtMokl_jxLUKr -o sample_data/sub-0001_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0001/func/sub-0001_task-restingstate_acq-mb3_desc-confounds_regressors.tsv?versionId=biaIJGNQ22P1l1xEsajVzUW6cnu1_8lD -o sample_data/sub-0001_task-restingstate_acq-mb3_desc-confounds_regressors.tsv
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0002/func/sub-0002_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz?versionId=fUBWmUTg6vfe2n.ywDNms4mOAW3r6E9Y -o sample_data/sub-0002_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0002/func/sub-0002_task-restingstate_acq-mb3_desc-confounds_regressors.tsv?versionId=2zWQIugU.J6ilTFObWGznJdSABbaTx9F -o sample_data/sub-0002_task-restingstate_acq-mb3_desc-confounds_regressors.tsv
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0003/func/sub-0003_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz?versionId=dfNd8iV0V68yuOibes6qiHxjBgQXhPxi -o sample_data/sub-0003_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0003/func/sub-0003_task-restingstate_acq-mb3_desc-confounds_regressors.tsv?versionId=8OpKFrs_8aJ5cVixokBmuTVKNslgtOXb -o sample_data/sub-0003_task-restingstate_acq-mb3_desc-confounds_regressors.tsv
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0004/func/sub-0004_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz?versionId=0Le8eFwJbcLKaMTQat39bzWcGFhRiyP5 -o sample_data/sub-0004_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0004/func/sub-0004_task-restingstate_acq-mb3_desc-confounds_regressors.tsv?versionId=welg1B.VkXHGv06iV56Vp7ezpVTFh2eX -o sample_data/sub-0004_task-restingstate_acq-mb3_desc-confounds_regressors.tsv
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0005/func/sub-0005_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz?versionId=Vwo2YcFvhwbhZktBrPUqi_5BWiR7zcTl -o sample_data/sub-0005_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz
!curl --create-dirs https://s3.amazonaws.com/openneuro.org/ds002785/derivatives/fmriprep/sub-0005/func/sub-0005_task-restingstate_acq-mb3_desc-confounds_regressors.tsv?versionId=FoBZLbFTZaE3ZjOLZI_4hN4OkEKEZTVf -o sample_data/sub-0005_task-restingstate_acq-mb3_desc-confounds_regressors.tsv
```

### 2) Load `BOLD_multi`

```python
subj_id_list = ["sub-0001", "sub-0002", "sub-0003", "sub-0004", "sub-0005"]
nifti_files_list = []
for subj_id in subj_id_list:
    nifti_files_list.append(
        "sample_data/"
        + subj_id
        + "_task-restingstate_acq-mb3_space-MNI152NLin2009cAsym_desc-preproc_bold.nii.gz"
    )

BOLD_multi = data_loader.multi_nifti2timeseries(
    nifti_files_list,
    subj_id_list,
    n_rois=100,
    Fs=1 / 0.75,
    confound_strategy="no_motion",
    standardize=False,
    TS_name=None,
    session=None,
)
```

### 3) Ask Which Method

Ask exactly (or very close):

`Which dFC method would you like to use to assess dFC? (CAP, SWC, CHMM, DHMM, or WINDOWLESS)`

### 4) Method Snippets (State-Based)

#### CAP

```python
from pydfc.dfc_methods import CAP

params_methods = {
    "n_states": 12,
    "n_subj_clstrs": 20,
    "normalization": True,
    "num_subj": None,
    "num_select_nodes": None,
}

measure = CAP(**params_methods)
measure.estimate_FCS(time_series=BOLD_multi)
dFC = measure.estimate_dFC(time_series=BOLD_multi.get_subj_ts(subjs_id="sub-0001"))
TRs = dFC.TR_array[np.arange(29, 480 - 29, 29)]
dFC.visualize_dFC(TRs=TRs, normalize=True, fix_lim=False)
```

#### SWC (Sliding Window + Clustering)

```python
from pydfc.dfc_methods import SLIDING_WINDOW_CLUSTR

params_methods = {
    "W": 44,
    "n_overlap": 0.5,
    "sw_method": "pear_corr",
    "tapered_window": True,
    "clstr_base_measure": "SlidingWindow",
    "n_states": 12,
    "n_subj_clstrs": 5,
    "normalization": True,
    "num_subj": None,
    "num_select_nodes": None,
}

measure = SLIDING_WINDOW_CLUSTR(**params_methods)
measure.estimate_FCS(time_series=BOLD_multi)
dFC = measure.estimate_dFC(time_series=BOLD_multi.get_subj_ts(subjs_id="sub-0001"))
dFC.visualize_dFC(TRs=dFC.TR_array[:], normalize=True, fix_lim=False)
```

#### CHMM (Continuous HMM)

```python
from pydfc.dfc_methods import HMM_CONT

params_methods = {
    "hmm_iter": 20,
    "n_states": 12,
    "normalization": True,
    "num_subj": None,
    "num_select_nodes": None,
}

measure = HMM_CONT(**params_methods)
measure.estimate_FCS(time_series=BOLD_multi)
dFC = measure.estimate_dFC(time_series=BOLD_multi.get_subj_ts(subjs_id="sub-0001"))
TRs = dFC.TR_array[np.arange(29, 480 - 29, 29)]
dFC.visualize_dFC(TRs=TRs, normalize=True, fix_lim=False)
```

#### DHMM (Discrete HMM)

Note: the demo notebook warns that 5 subjects is too small to fit DHMM well; a warning is expected.

```python
from pydfc.dfc_methods import HMM_DISC

params_methods = {
    "W": 44,
    "n_overlap": 0.5,
    "sw_method": "pear_corr",
    "tapered_window": True,
    "clstr_base_measure": "SlidingWindow",
    "hmm_iter": 20,
    "dhmm_obs_state_ratio": 16 / 24,
    "n_states": 12,
    "n_subj_clstrs": 5,
    "normalization": True,
    "num_subj": None,
    "num_select_nodes": 50,
}

measure = HMM_DISC(**params_methods)
measure.estimate_FCS(time_series=BOLD_multi)
dFC = measure.estimate_dFC(time_series=BOLD_multi.get_subj_ts(subjs_id="sub-0001"))
dFC.visualize_dFC(TRs=dFC.TR_array[:], normalize=True, fix_lim=False)
```

#### WINDOWLESS

```python
from pydfc.dfc_methods import WINDOWLESS

params_methods = {
    "n_states": 12,
    "normalization": True,
    "num_subj": None,
    "num_select_nodes": None,
}

measure = WINDOWLESS(**params_methods)
measure.estimate_FCS(time_series=BOLD_multi)
dFC = measure.estimate_dFC(time_series=BOLD_multi.get_subj_ts(subjs_id="sub-0001"))
TRs = dFC.TR_array[np.arange(29, 480 - 29, 29)]
dFC.visualize_dFC(TRs=TRs, normalize=True, fix_lim=False)
```

## Response Style Rules

- Keep replies short and practical.
- Prefer one code block at a time (do not dump all methods unless the user asks).
- Reuse the exact demo parameters first; optimize later only if requested.
- If the user is unsure, recommend `SW` first (state-free, simplest).
- After each method snippet, ask: `Are there any other methods you are curious about?`

