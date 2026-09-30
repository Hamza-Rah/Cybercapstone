from pathlib import Path
import csv

from feature_extractor import (
    FEATURE_NAMES,
    FEATURE_COUNT,
    FEATURE_SCHEMA_VERSION,
    extract_features,
)


DATASET_DIR = Path("dataset")
OUTPUT_FILE = Path("features.csv")

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
}


def find_images(folder):
    return sorted(
        path
        for path in folder.rglob("*")
        if path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


def get_group_id(path):
    """
    pair_0001_clean.png -> pair_0001
    pair_0001_stego.png -> pair_0001
    """

    stem = path.stem

    if stem.endswith("_clean"):
        return stem[:-6]

    if stem.endswith("_stego"):
        return stem[:-6]

    return stem


def build_dataset():

    rows = []
    failed = []

    categories = [
        ("clean", 0),
        ("stego", 1),
    ]

    for category, label in categories:

        folder = DATASET_DIR / category

        images = find_images(folder)

        print(
            f"[*] Processing {len(images)} "
            f"{category} image(s)"
        )

        for image_path in images:

            try:

                features = extract_features(
                    str(image_path)
                )

                if len(features) != FEATURE_COUNT:
                    raise ValueError(
                        f"Expected {FEATURE_COUNT} features"
                    )

                row = {
                    "filename": str(image_path),
                    "group_id": get_group_id(image_path),
                    "schema_version": FEATURE_SCHEMA_VERSION,
                }

                for name, value in zip(
                    FEATURE_NAMES,
                    features
                ):
                    row[name] = float(value)

                row["label"] = label

                rows.append(row)

                print(
                    f"[+] {image_path.name}: "
                    f"{len(features)} features"
                )

            except Exception as error:

                failed.append(
                    (str(image_path), str(error))
                )

                print(
                    f"[!] Failed: {image_path}"
                )

                print(
                    f"    Reason: {error}"
                )

    fieldnames = (
        [
            "filename",
            "group_id",
            "schema_version",
        ]
        + list(FEATURE_NAMES)
        + ["label"]
    )

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as csv_file:

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(rows)

    print()
    print(
        f"[+] Dataset written to {OUTPUT_FILE}"
    )

    print(
        f"[+] Successful samples: {len(rows)}"
    )

    print(
        f"[+] Failed samples: {len(failed)}"
    )


if __name__ == "__main__":
    build_dataset()