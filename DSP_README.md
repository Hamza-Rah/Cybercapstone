# DSP DCT/DWT Module Handover

## Project

**Covert Channel-Hunt**

This module is the Digital Signal Processing (DSP) component of the team's steganalysis pipeline.

Its purpose is to convert an image into a fixed numerical feature vector using:

- **DCT — Discrete Cosine Transform**
- **DWT — Discrete Wavelet Transform**

The resulting features are intended to be passed to the machine-learning component for clean/stego classification.

---

## Current Status

### Completed

- Implemented image loading and grayscale conversion.
- Implemented DCT feature extraction.
- Implemented DWT feature extraction using a single-level Haar wavelet.
- Defined a fixed **37-feature output**.
- Added readable feature names.
- Added checks to ensure feature output is numeric and consistent.
- Removed image resizing from the DSP path so subtle image changes are not unnecessarily altered before analysis.
- Normalized energy calculations using mean-squared coefficient energy rather than raw total energy.
- Successfully tested `feature_extractor.py` on an image.
- Successfully tested `build_dataset.py` using two temporary labelled images.
- Confirmed `build_dataset.py` generated:
  - 37 features for the clean-labelled image
  - 37 features for the stego-labelled image
  - 2 CSV rows
  - 0 processing failures
- Successfully validated the DSP module on an image extracted from a PCAP.
- Confirmed the PCAP-extracted image produced the expected **37 DCT/DWT features**.

### Not Yet Completed

- A real public cover/stego dataset has not yet been fully processed.
- `features.csv` generated during testing was only a smoke-test artifact and should not be treated as real ML training data.
- The ML classifier has not yet been trained using these features.

---

## Files

### `feature_extractor.py`

Main DSP implementation.

The primary interface is:

```python
from feature_extractor import extract_features

features = extract_features("image.png")
```

Expected result:

```python
features.shape == (37,)
```

The returned NumPy array contains exactly 37 DCT/DWT features.

---

### `build_dataset.py`

Batch-processes labelled images and generates an ML-ready CSV.

Expected folder structure:

```text
dataset/
├── clean/
└── stego/
```

Labels:

```text
clean = 0
stego = 1
```

Run:

```bash
python build_dataset.py
```

The script outputs:

```text
features.csv
```

Each row contains:

```text
filename
group_id
schema_version
37 DSP features
label
```

---

## Feature Schema

The DSP module currently produces:

```text
9 DCT features
+
28 DWT features
=
37 total features
```

The feature order must remain consistent once an ML model is trained.

---

## DCT Features

The DCT stage produces 9 statistical features:

1. `dct_mean`
2. `dct_std`
3. `dct_mean_abs`
4. `dct_max_abs`
5. `dct_median_abs`
6. `dct_energy`
7. `dct_near_zero_ratio`
8. `dct_skewness`
9. `dct_kurtosis`

The DC coefficient is excluded from the statistical feature calculations because it primarily represents overall image brightness.

---

## DWT Features

A single-level Haar DWT is applied to the image.

The four resulting sub-bands are:

```text
LL
LH
HL
HH
```

For each sub-band, 7 statistical features are calculated:

1. mean
2. standard deviation
3. mean absolute value
4. maximum absolute value
5. energy
6. skewness
7. kurtosis

Therefore:

```text
4 bands × 7 features = 28 DWT features
```

Combined with the 9 DCT features:

```text
28 + 9 = 37 features
```

---

## Current Processing Flow

```text
Image
  ↓
feature_extractor.py
  ↓
┌──────────────┬──────────────┐
│              │              │
DCT            DWT
│              │
9 features     28 features
│              │
└───────┬──────┘
        ↓
   37 features
        ↓
build_dataset.py
        ↓
features.csv
        ↓
ML model
```

# DSP DCT/DWT Module Handover

## Project

**Covert Channel-Hunt**

This module is the Digital Signal Processing (DSP) component of the team's steganalysis pipeline.

Its purpose is to convert an image into a fixed numerical feature vector using:

- **DCT — Discrete Cosine Transform**
- **DWT — Discrete Wavelet Transform**

The resulting features are intended to be passed to the machine-learning component for clean/stego classification.

---

## Current Status

### Completed

- Implemented image loading and grayscale conversion.
- Implemented DCT feature extraction.
- Implemented DWT feature extraction using a single-level Haar wavelet.
- Defined a fixed **37-feature output**.
- Added readable feature names.
- Added checks to ensure feature output is numeric and consistent.
- Removed image resizing from the DSP path so subtle image changes are not unnecessarily altered before analysis.
- Normalized energy calculations using mean-squared coefficient energy rather than raw total energy.
- Successfully tested `feature_extractor.py` on an image.
- Successfully tested `build_dataset.py` using two temporary labelled images.
- Confirmed `build_dataset.py` generated:
  - 37 features for the clean-labelled image
  - 37 features for the stego-labelled image
  - 2 CSV rows
  - 0 processing failures
- Successfully validated the DSP module on an image extracted from a PCAP.
- Confirmed the PCAP-extracted image produced the expected **37 DCT/DWT features**.

### Not Yet Completed

- A real public cover/stego dataset has not yet been fully processed.
- `features.csv` generated during testing was only a smoke-test artifact and should not be treated as real ML training data.
- The ML classifier has not yet been trained using these features.

---

## Files

### `feature_extractor.py`

Main DSP implementation.

The primary interface is:

```python
from feature_extractor import extract_features

features = extract_features("image.png")