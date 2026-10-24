import yaml
import sys

host_name = sys.argv[1]

with open('/root/homelab/inventories/hosts.yml', 'r') as f:
    inv = yaml.safe_load(f)

removed = False
for group, data in inv['all']['children'].items():
    if data and 'hosts' in data and data['hosts']:
        if host_name in data['hosts']:
            del data['hosts'][host_name]
            removed = True
            print(f"Removed {host_name} from group [{group}]")

if not removed:
    print(f"Host {host_name} not found in inventory")

with open('/root/homelab/inventories/hosts.yml', 'w') as f:
    yaml.dump(inv, f, default_flow_style=False)
