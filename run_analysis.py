"""
run_analysis.py
Runs Packet_engine.py's analyze_pcap() against the actual pcap files on disk
(sample_traffic.pcap, dns_attack.pcap) instead of relying on Packet_engine.py's
own __main__ block, which hardcodes filenames from generate_test_pcaps.py that
don't match these files.

Run this first. It produces:
  - payload_manifest.json   (input to verify_hashes.py)
  - network_alerts.json     (only created if a covert-channel anomaly fires)
  - extracted_payloads/     (carved files referenced by the manifest)
"""

from Packet_engine import analyze_pcap

PCAPS = ["sample_traffic.pcap", "dns_attack.pcap"]

if __name__ == "__main__":
    for pcap in PCAPS:
        print(f"\n{'='*20} Analyzing: {pcap} {'='*20}")
        analyze_pcap(pcap)
