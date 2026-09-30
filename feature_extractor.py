import os

import cv2
import numpy as np
import pywt
from scipy.stats import skew, kurtosis


# ---------------------------------------------------------
# Feature names
# ---------------------------------------------------------

DCT_FEATURE_NAMES = [
    "dct_mean",
    "dct_std",
    "dct_mean_abs",
    "dct_max_abs",
    "dct_median_abs",
    "dct_energy",
    "dct_near_zero_ratio",
    "dct_skewness",
    "dct_kurtosis",
]

DWT_STATS = [
    "mean",
    "std",
    "mean_abs",
    "max_abs",
    "energy",
    "skewness",
    "kurtosis",
]

DWT_BANDS = ["LL", "LH", "HL", "HH"]

DWT_FEATURE_NAMES = [
    f"dwt_{band}_{stat}"
    for band in DWT_BANDS
    for stat in DWT_STATS
]

FEATURE_SCHEMA_VERSION = "1.0"

FEATURE_NAMES = tuple(
    DCT_FEATURE_NAMES + DWT_FEATURE_NAMES
)

FEATURE_COUNT = len(FEATURE_NAMES)

assert FEATURE_COUNT == 37


# ---------------------------------------------------------
# Load and preprocess image
# ---------------------------------------------------------

def load_image(image_path):
    """
    Loads an image as grayscale and converts it to float32.
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image does not exist: {image_path}")

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    image = image.astype(np.float32) / 255.0

    return image


# ---------------------------------------------------------
# DCT feature extraction
# ---------------------------------------------------------

def extract_dct_features(image):
    """
    Applies the Discrete Cosine Transform (DCT)
    and extracts statistical attributes.
    """

    # Perform 2D DCT
    dct = cv2.dct(image)

    # Flatten matrix into one-dimensional array
    coefficients = dct.flatten()

    # Ignore the first DC coefficient
    # because it mainly represents overall image brightness
    ac_coefficients = coefficients[1:]

    features = [
        np.mean(ac_coefficients),
        np.std(ac_coefficients),
        np.mean(np.abs(ac_coefficients)),
        np.max(np.abs(ac_coefficients)),
        np.median(np.abs(ac_coefficients)),
        np.mean(ac_coefficients ** 2),
        np.mean(np.abs(ac_coefficients) < 0.01),
        skew(ac_coefficients),
        kurtosis(ac_coefficients),
    ]

    # Prevent NaN/Infinity from being sent to ML model
    features = np.nan_to_num(
        features,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    return features.tolist()


# ---------------------------------------------------------
# DWT feature extraction
# ---------------------------------------------------------

def extract_dwt_features(image):
    """
    Applies a single-level Discrete Wavelet Transform (DWT)
    using the Haar wavelet.

    Produces four sub-bands:
        LL - approximation
        LH - horizontal/vertical detail
        HL - horizontal/vertical detail
        HH - diagonal/high-frequency detail
    """

    LL, (LH, HL, HH) = pywt.dwt2(image, "haar")

    bands = [LL, LH, HL, HH]

    features = []

    for band in bands:
        coefficients = band.flatten()

        band_features = [
            np.mean(coefficients),
            np.std(coefficients),
            np.mean(np.abs(coefficients)),
            np.max(np.abs(coefficients)),
            np.mean(coefficients ** 2),
            skew(coefficients),
            kurtosis(coefficients),
        ]

        band_features = np.nan_to_num(
            band_features,
            nan=0.0,
            posinf=0.0,
            neginf=0.0,
        )

        features.extend(band_features.tolist())

    return features


# ---------------------------------------------------------
# Combined feature extraction
# ---------------------------------------------------------

def extract_features(image_path):
    """
    Extracts DCT + DWT features from an image.

    Returns:
        numpy array containing 37 features
    """

    image = load_image(image_path)

    dct_features = extract_dct_features(image)
    dwt_features = extract_dwt_features(image)

    combined_features = dct_features + dwt_features

    return np.array(combined_features, dtype=np.float32)


# ---------------------------------------------------------
# Human-readable feature output
# ---------------------------------------------------------

def extract_feature_dict(image_path):
    """
    Returns features as a dictionary with readable names.
    Useful for debugging and CSV generation.
    """

    feature_vector = extract_features(image_path)

    return dict(zip(FEATURE_NAMES, feature_vector.tolist()))


# ---------------------------------------------------------
# Testing
# ---------------------------------------------------------

if __name__ == "__main__":
    image_path = "screenshot-baseline-match.png"

    feature_dict = extract_feature_dict(image_path)

    print("Image:", image_path)
    print("Feature count:", len(feature_dict))
    print()

    for name, value in feature_dict.items():
        print(f"{name}: {value}")