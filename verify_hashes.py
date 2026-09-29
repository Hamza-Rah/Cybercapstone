"""
Ali's module: Integrity & Hashing verification.
Reads payload_manifest.json (produced by Packet_engine.py) and checks each
carved file's sha256 against:
  1. a KNOWN_THREAT_HASHES table (malicious file signatures)
  2. a BASELINE_HASHES table (expected/clean files, e.g. from a prior known-good run)

Any manifest entry whose hash isn't in either table is "unverified" — new/unknown,
worth a closer look (especially if is_stego_candidate is true).
"""

import json
import os
from datetime import datetime, timezone

MANIFEST_FILE = "./payload_manifest.json"
THREAT_DB_FILE = "./known_threat_hashes.json"   # {sha256: "label/description"}
BASELINE_FILE = "./baseline_hashes.json"        # {sha256: "expected filename"}
VERIFICATION_LOG = "./hash_verification_results.json"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path) as f:
        return json.load(f)


def verify_manifest():
    manifest = load_json(MANIFEST_FILE, [])
    threat_db = load_json(THREAT_DB_FILE, {})
    baseline = load_json(BASELINE_FILE, {})

    if not manifest:
        print(f"[!] No manifest found at {MANIFEST_FILE} — run Packet_engine.py first.")
        return

    results = []
    for entry in manifest:
        sha = entry["sha256"]
        result = {
            "filename": entry["filename"],
            "sha256": sha,
            "is_stego_candidate": entry.get("is_stego_candidate", False),
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }

        if sha in threat_db:
            result["status"] = "MALICIOUS_MATCH"
            result["detail"] = threat_db[sha]
            print(f"[ALERT] {entry['filename']} matches known threat: {threat_db[sha]}")
        elif sha in baseline:
            result["status"] = "BASELINE_MATCH"
            result["detail"] = f"Matches known-good baseline ({baseline[sha]})"
        else:
            result["status"] = "UNVERIFIED"
            result["detail"] = "Not in threat DB or baseline — new/unknown file"
            print(f"[INFO] {entry['filename']} is unverified (no match in either table)")

        results.append(result)

    with open(VERIFICATION_LOG, "w") as f:
        json.dump(results, f, indent=4)

    print(f"[+] Verified {len(results)} file(s). Results written to {VERIFICATION_LOG}")
    return results


if __name__ == "__main__":
    verify_manifest()
