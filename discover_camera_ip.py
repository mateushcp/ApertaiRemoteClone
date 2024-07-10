from scapy.all import ARP, Ether, srp
import nmap
import netifaces

def get_local_ip_and_gateway():
    # Get the local IP address and gateway using netifaces
    gateways = netifaces.gateways()
    default_gateway = gateways['default'][netifaces.AF_INET][0]
    interfaces = netifaces.interfaces()
    local_ip = None
    for interface in interfaces:
        if interface != 'lo':  # Skip the loopback interface
            addresses = netifaces.ifaddresses(interface)
            if netifaces.AF_INET in addresses:
                for addr in addresses[netifaces.AF_INET]:
                    if 'addr' in addr and addr['addr'].startswith(default_gateway.rsplit('.', 1)[0]):
                        local_ip = addr['addr']
                        break
    return local_ip, default_gateway

def get_local_ip_range():
    local_ip, default_gateway = get_local_ip_and_gateway()
    print(f"local_ip: {local_ip}, gateway: {default_gateway}")
    if not local_ip:
        return None
    ip_parts = default_gateway.split('.')
    ip_parts[-1] = '0/24'
    return '.'.join(ip_parts)

def arp_scan(ip_range):
    if not ip_range:
        print("Invalid IP range.")
        return []
    # Create ARP request
    arp = ARP(pdst=ip_range)
    ether = Ether(dst="ff:ff:ff:ff:ff:ff")
    packet = ether/arp

    # Send the packet and get the response
    result = srp(packet, timeout=2, verbose=False)[0]

    # Extract IP addresses from the response
    devices = []
    for sent, received in result:
        devices.append(received.psrc)
    
    return devices

def scan_rtsp_ports(devices):
    nm = nmap.PortScanner()
    rtsp_devices = []
    for ip in devices:
        try:
            print(f"Scanning {ip} for RTSP port 554...")
            nm.scan(ip, '554')
            if ip in nm.all_hosts():
                print(f"{ip} is in scan results.")
                if nm[ip].state() == 'up' and 'tcp' in nm[ip] and 554 in nm[ip]['tcp'] and nm[ip]['tcp'][554]['state'] == 'open':
                    print(f"RTSP port 554 is open on {ip}.")
                    rtsp_devices.append(ip)
                else:
                    print(f"RTSP port 554 is not open on {ip}.")
            else:
                print(f"{ip} not found in scan results.")
        except Exception as e:
            print(f"Error scanning {ip}: {e}")
    return rtsp_devices

def get_rtsp_ips():
    # Discover devices using ARP scan
    ip_range = get_local_ip_range()
    if not ip_range:
        print("Failed to determine the local IP range.")
        return []
    devices = arp_scan(ip_range)
    print("Discovered devices:")
    for device in devices:
        print(f"IP: {device}")

    # Filter devices with open RTSP port
    rtsp_devices = scan_rtsp_ports(devices)
    print("Discovered RTSP devices:")
    for device in rtsp_devices:
        print(f"IP: {device}")

    return rtsp_devices

# Run the script
if __name__ == "__main__":
    get_rtsp_ips()
