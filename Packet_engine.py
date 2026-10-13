import os
import math
import hashlib
import json
import shutil
import subprocess
import argparse
from datetime import datetime, timezone
from scapy.all import rdpcap, sniff, DNS, DNSQR, IP, TCP, UDP, wrpcap

OUTPUT_DIR = "./extracted_payloads"
ALERT_LOG = "./network_alerts.json"
MANIFEST_FILE = "./payload_manifest.json"

# Sarah's Random Forest detector only evaluates lossless formats; lossy formats (JPEG) destroy LSB signals
STEGO_CANDIDATE_EXTENSIONS = ('.png', '.bmp')

def init_environment(clean_extracted: bool = True):
    """Ensures extraction directory exists and isolates runs from residual files."""
    if clean_extracted and os.path.exists(OUTPUT_DIR):
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def calculate_entropy(data: str) -> float:
    """Calculates Shannon entropy for DNS query strings: H(X) = -sum(P * log2(P))."""
    if not data:
        return 0.0
    entropy = 0.0
    length = len(data)
    for char in set(data):
        prob = data.count(char) / length
        entropy -= prob * math.log2(prob)
    return entropy

def log_alert_to_siem(alert_dict: dict):
    """Appends structured JSON alerts for Sadat's Wazuh SIEM collector."""
    with open(ALERT_LOG, "a") as f:
        f.write(json.dumps(alert_dict) + "\n")

def process_packet_anomalies(pkt) -> bool:
    """Evaluates a single packet for DNS tunneling and TCP covert channels."""
    alert_created = False
    
    # 1. DNS Tunneling Detection (Shannon Entropy & Length Thresholds)
    if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
        query_name = pkt[DNSQR].qname.decode('utf-8', errors='ignore').rstrip('.')
        entropy = calculate_entropy(query_name)
        
        # Threshold: entropy > 3.8 indicates high randomness (Base64/Hex exfiltration)
        if len(query_name) > 40 or entropy > 3.8:
            src_ip = pkt[IP].src if pkt.haslayer(IP) else "Unknown"
            alert = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "layer": "Network_Protocol",
                "event_type": "DNS_Tunneling_Detected",
                "src_ip": src_ip,
                "query": query_name,
                "query_length": len(query_name),
                "entropy": round(entropy, 2),
                "severity": "HIGH"
            }
            log_alert_to_siem(alert)
            print(f"[ALERT] DNS Tunneling Detected: {query_name[:35]}... (Entropy: {entropy:.2f})")
            alert_created = True

    # 2. TCP Header Covert Channels (Reserved Bits & Urgent Pointer Abuse)
    if pkt.haslayer(TCP):
        tcp_layer = pkt[TCP]
        src_ip = pkt[IP].src if pkt.haslayer(IP) else "Unknown"
        
        if tcp_layer.reserved != 0 or (tcp_layer.flags.U and tcp_layer.urgptr > 0):
            alert = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "layer": "Transport_Header",
                "event_type": "TCP_Covert_Channel_Anomaly",
                "src_ip": src_ip,
                "reserved_bits": tcp_layer.reserved,
                "urg_ptr": tcp_layer.urgptr,
                "severity": "MEDIUM"
            }
            log_alert_to_siem(alert)
            print(f"[ALERT] TCP Covert Header Anomaly from {src_ip} (Flags: {tcp_layer.flags})")
            alert_created = True
            
    return alert_created

def inspect_covert_anomalies(pcap_path: str):
    """Parses offline PCAP captures via Scapy."""
    print(f"[*] Inspecting {pcap_path} for covert channels...")
    packets = rdpcap(pcap_path)
    total_alerts = sum(1 for pkt in packets if process_packet_anomalies(pkt))
    print(f"[*] Offline scan complete: {len(packets)} packets inspected, {total_alerts} alert(s) logged to {ALERT_LOG}")

def extract_payloads_tshark(pcap_path: str):
    """Carves HTTP objects and generates a structured handoff manifest for Chris & Sarah."""
    print(f"[*] Reassembling TCP streams & carving HTTP objects to {OUTPUT_DIR} ...")
    cmd = ["tshark", "-r", pcap_path, "--export-objects", f"http,{OUTPUT_DIR}", "-q"]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    extracted_files = [f for f in os.listdir(OUTPUT_DIR) if os.path.isfile(os.path.join(OUTPUT_DIR, f))]
    if not extracted_files:
        print("[!] No HTTP payloads found.")
        return

    manifest = []
    print(f"[+] Successfully carved {len(extracted_files)} files:")
    
    for fname in extracted_files:
        filepath = os.path.join(OUTPUT_DIR, fname)
        with open(filepath, "rb") as f:
            file_bytes = f.read()
            file_hash = hashlib.sha256(file_bytes).hexdigest()

        # Tag specifically for lossless images required by stego_detector.py
        is_candidate = fname.lower().endswith(STEGO_CANDIDATE_EXTENSIONS)
        file_meta = {
            "filename": fname,
            "filepath": filepath,
            "size_bytes": len(file_bytes),
            "sha256": file_hash,
            "is_stego_candidate": is_candidate,
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }
        manifest.append(file_meta)
        print(f"    - File: {fname} | Stego Candidate: {is_candidate} | SHA-256: {file_hash[:12]}...")

    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=4)
    print(f"[+] Handoff manifest written to {MANIFEST_FILE}")

def run_pipeline(pcap_path: str):
    """Executes offline analysis on a target PCAP."""
    if not os.path.exists(pcap_path):
        print(f"[!] File not found: {pcap_path}")
        return
    init_environment(clean_extracted=True)
    inspect_covert_anomalies(pcap_path)
    extract_payloads_tshark(pcap_path)

def start_live_sniff(interface: str, packet_count: int = 50):
    """Sniffs live traffic, flags anomalies, dumps to temp PCAP, and carves payloads."""
    temp_pcap = "live_capture.pcap"
    init_environment(clean_extracted=True)
    print(f"[*] Sniffing on interface '{interface}' for {packet_count} packets...")
    
    captured_packets = sniff(iface=interface, count=packet_count, prn=process_packet_anomalies)
    wrpcap(temp_pcap, captured_packets)
    print(f"[+] Live capture saved to {temp_pcap}")
    
    extract_payloads_tshark(temp_pcap)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Covert Channel-Hunt: Network Intake & Payload Carving Engine")
    parser.add_argument("-p", "--pcap", help="Path to PCAP file for offline analysis", type=str)
    parser.add_argument("-i", "--interface", help="Network interface for live sniffing (e.g., eth0, any)", type=str)
    parser.add_argument("-c", "--count", help="Packet count for live capture (default: 50)", type=int, default=50)
    args = parser.parse_args()

    if args.interface:
        start_live_sniff(interface=args.interface, packet_count=args.count)
    elif args.pcap:
        run_pipeline(args.pcap)
    else:
        # Fallback regression test across synthetic attack PCAPs
        default_pcaps = ["synthetic_dns_attack.pcap", "synthetic_tcp_attack.pcap"]
        for p in default_pcaps:
            print(f"\n{'='*25} Regression Test: {p} {'='*25}")
            run_pipeline(p)
