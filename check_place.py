import sys

import osmnx as ox


ox.config(log_console=True, use_cache=True)

query = 'Bielefeld, Germany'
try:
    graph = ox.graph_from_place(query, network_type='drive')
except Exception:
    print('Failed')
    sys.exit(1)

print('Looks good')
