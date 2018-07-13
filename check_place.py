import json
import requests
import sys


def load_places():
    try:
        with open(sys.argv[-1], 'r') as source:
            result = json.load(source)
    except Exception as e:
        print(f'Tried and failed to open file at {sys.argv[-1]}: {e}\n'
              'Please pass a json file with city data to this program.')
        sys.exit(-1)
    return result


places = load_places()
url = 'https://nominatim.openstreetmap.org/search'

for place, query in places.items():
    params = {
        'format': 'json',
        'limit': 1,
        'dedupe': 0,
        'polygon_geojson': 1
    }
    if isinstance(query, str):
        params['q'] = query
    else:
        params = {**params, **query}

    response = requests.get(url, params)
    if response.status_code != 200:
        print(f'Got non-200 response for {place}: {response.content.decode()}')
        continue

    data = json.loads(response.content.decode())
    if len(data) != 1:
        print(f'Got non-1 length response for {place}: {data}')
        continue
    if 'geojson' not in data[0]:
        print('Got malformed response without geojson key for {place}: {data}')
        continue
    geojson_type = data[0]['geojson']['type']
    if geojson_type not in ['Polygon', 'MultiPolygon']:
        print(f'Response for {place} is of type {geojson_type}!')
        continue
