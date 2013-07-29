import socket

""" Some utilities to simulate allocating networks/addresses when there is no
    observer.
"""

SUBNET_BASE = "10.0.0.0"
SUBNET_NODE_BITS = 12     # enough for 4096 bits per subnet
SUBNET_SUBNET_BITS = 12   # enough for 4096 private networks

def ip_to_int(ip):
    return int(socket.inet_aton(ip).encode('hex'),16)

def int_to_ip(i):
    return socket.inet_ntoa(hex(i)[2:].zfill(8).decode('hex'))

def find_unused_subnet(base=SUBNET_BASE, subnet_bits=SUBNET_SUBNET_BITS, node_bits=SUBNET_NODE_BITS, existing_subnets=[]):
    # enumerate possible subnets until we find one that isn't used
    i=1
    while True:
        subnet_i = ip_to_int(base) | (i<<node_bits)
        subnet = int_to_ip(subnet_i) + "/" + str(32-node_bits)
        if (subnet not in existing_subnets):
            return subnet
        i=i+1
        # TODO: we could run out...

def find_unused_address(subnet, existingAddresses):
    # enumerate possible addresses until we find one that isn't used
    (network, bits) = subnet.split("/")
    network_i = ip_to_int(network)
    max_addr = 1<<(32-int(bits))
    i = 1
    while True:
        if i>=max_addr:
            raise ValueError("No more ips available")
        ip = int_to_ip(network_i | i)
        if not (ip in existingAddresses):
            return ip
        i=i+1
