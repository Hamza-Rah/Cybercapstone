from scapy.all import wrpcap, Ether, IP, UDP, TCP, DNS, DNSQR

# 1. Synthetic DNS Tunneling PCAP
dns_attack_pkt = Ether() / IP(src="192.168.1.100", dst="8.8.8.8") / UDP(sport=53210, dport=53) / \
                 DNS(rd=1, qd=DNSQR(qname="dGhpczFzYWNvdnJ0ZXhmaWx0cmF0aW9ucGF5bG9hZDEyMzQ1Njc4OTA.attack.com"))
wrpcap("synthetic_dns_attack.pcap", [dns_attack_pkt])
print("[+] Created synthetic_dns_attack.pcap")

# 2. Synthetic TCP Covert Header PCAP
tcp_attack_pkt = Ether() / IP(src="10.0.0.5", dst="10.0.0.1") / \
                 TCP(sport=4444, dport=80, flags="U", urgptr=1337, reserved=3)
wrpcap("synthetic_tcp_attack.pcap", [tcp_attack_pkt])
print("[+] Created synthetic_tcp_attack.pcap")