import os
import math
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from scapy.all import rdpcap, DNS, DNSQR, IP, TCP, UDP

OUTPUT_DIR = "./extracted_payloads"
ALERT_LOG = "./network_alerts.json"
MANIFEST_FILE = "./payload_manifest.json"

MEDIA_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.bmp', '.wav', '.mp3')
os.makedirs(OUTPUT_DIR, exist_ok=True)

def calculate_entropy(data: str) -> float:
    """Calculates Shannon entropy for DNS query strings."""
    if not data:
        return 0.0
    entropy = 0.0
    for char in set(data):
        prob = data.count(char) / len(data)
        entropy -= prob * math.log2(prob)
    return entropy

def log_alert_to_siem(alert_dict: dict):
    """Appends structured JSON alerts for Sadat's Wazuh SIEM."""
    with open(ALERT_LOG, "a") as f:
        f.write(json.dumps(alert_dict) + "\n")

def inspect_covert_anomalies(pcap_path: str):
    """Parses PCAP via Scapy for DNS tunneling and TCP/UDP header covert channels."""
    print(f"[*] Inspecting network packets for covert channels...")
    packets = rdpcap(pcap_path)
    
    dns_anomalies = 0
    header_anomalies = 0
    total_dns = 0

    for pkt in packets:
        # 1. DNS Tunneling Detection
        if pkt.haslayer(DNS) and pkt.haslayer(DNSQR):
            total_dns += 1
            query_name = pkt[DNSQR].qname.decode('utf-8', errors='ignore').rstrip('.')
            entropy = calculate_entropy(query_name)
            
            if len(query_name) > 40 or entropy > 3.8:
                dns_anomalies += 1
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
                print(f"[ALERT] DNS Tunneling: {query_name} (Entropy: {entropy:.2f})")

        # 2. TCP Header Covert Channel Checks
        if pkt.haslayer(TCP):
            tcp_layer = pkt[TCP]
            src_ip = pkt[IP].src if pkt.haslayer(IP) else "Unknown"
            
            # Check for non-zero reserved bits or URG pointer data leakage
            if tcp_layer.reserved != 0 or (tcp_layer.flags.U and tcp_layer.urgptr > 0):
                header_anomalies += 1
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
                print(f"[ALERT] TCP Covert Header Anomaly from {src_ip}")

    print(f"[*] Anomaly scan done: {total_dns} DNS checked, {dns_anomalies + header_anomalies} total alerts written to {ALERT_LOG}")

def extract_payloads_tshark(pcap_path: str):
    """Carves HTTP objects and generates a structured manifest for Ali & Chris."""
    print(f"[*] Reassembling and carving files to {OUTPUT_DIR} ...")
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

        is_media = fname.lower().endswith(MEDIA_EXTENSIONS)
        file_meta = {
            "filename": fname,
            "filepath": filepath,
            "size_bytes": len(file_bytes),
            "sha256": file_hash,
            "is_stego_candidate": is_media,  # Tells Chris/Sarah if it should enter DSP/ML pipeline
            "extracted_at": datetime.now(timezone.utc).isoformat()
        }
        manifest.append(file_meta)
        print(f"    - File: {fname} | Media Carrier: {is_media} | SHA-256: {file_hash[:12]}...")

    # Write manifest for Ali's hashing module and Chris's DSP intake
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifest, f, indent=4)
    print(f"[+] Handoff manifest written to {MANIFEST_FILE}")

def analyze_pcap(pcap_path: str):
    if not os.path.exists(pcap_path):
        print(f"[!] File not found: {pcap_path}")
        return

    inspect_covert_anomalies(pcap_path)
    extract_payloads_tshark(pcap_path)

if __name__ == "__main__":
    target_pcap = "sample_traffic.pcap"
    analyze_pcap(target_pcap)
    