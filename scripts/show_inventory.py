import yaml

with open('/root/homelab/inventories/hosts.yml', 'r') as f:
    inv = yaml.safe_load(f)

print("\n=== Current Inventory ===\n")
for group, data in inv['all']['children'].items():
    if data and 'hosts' in data and data['hosts']:
        print(f"[{group}]")
        for host, vars in data['hosts'].items():
            ip = vars.get('ansible_host', 'N/A') if vars else 'N/A'
            print(f"  {host} -> {ip}")
        print()
