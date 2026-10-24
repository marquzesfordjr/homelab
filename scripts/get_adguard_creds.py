import yaml
import sys

with open('/opt/adguard-sync/config.yaml', 'r') as f:
    config = yaml.safe_load(f)

print(config['origin']['password'])
print(config['replicas'][0]['password'])
