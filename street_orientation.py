import json
import os
import subprocess
import sys
from contextlib import suppress

import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import pandas as pd
import requests


# Configuration, or what passes as such
font = {'family': 'Titillium'}
tick_font = {'weight': 'bold', 'zorder': 3}
supertitle_font = {'fontsize': 60, 'y': 1.07, **font}
title_font = {'size': 24, 'weight': 'bold', **font}
xtick_font = {'size': 10, 'alpha': 1.0, **font, **tick_font}
ytick_font = {'size': 9, 'alpha': 0.2, **font, **tick_font}

ox.config(log_console=True, use_cache=True)
weight_by_length = False


def polar_plot(ax, bearings, slices=36, title=''):
    """Draw a polar histogram for a set of edge bearings."""

    bins = [angle * 360 / slices for angle in range(0, slices + 1)]
    count = count_and_merge(slices, bearings)
    _, division = np.histogram(bearings, bins=bins)
    frequency = count / count.sum()
    division = division[0:-1]
    width = 2 * np.pi / slices

    ax.set_theta_zero_location('N')
    ax.set_theta_direction('clockwise')

    x = division * np.pi / 180
    ax.bar(
        x, height=frequency, width=width, align='center', bottom=0, zorder=2,
        color='#003366', edgecolor='k', linewidth=0.5, alpha=0.7,
    )
    ax.set_ylim(top=frequency.max())
    ax.set_title(title.upper(), y=1.05, fontdict=title_font)

    ax.set_yticks(np.linspace(0, max(ax.get_ylim()), 5))
    yticklabels = ['{:.2f}'.format(y) for y in ax.get_yticks()]
    yticklabels[0] = ''
    ax.set_yticklabels(labels=yticklabels, fontdict=ytick_font)

    xticklabels = ['N', '', 'E', '', 'S', '', 'W', '']
    ax.set_xticklabels(labels=xticklabels, fontdict=xtick_font)
    ax.tick_params(axis='x', which='major', pad=-2)


def count_and_merge(n, bearings):
    # make twice as many bins as desired, then merge them in pairs
    # this prevents bin-edge effects around common values like 0° and 90°
    n = n * 2
    bins = [ang * 360 / n for ang in range(0, n + 1)]
    count, _ = np.histogram(bearings, bins=bins)

    # Move the last bin to the front to merge e.g. 0.01° and 359.99°
    count = count.tolist()
    count = [count[-1]] + count[:-1]
    count_merged = []
    count_iter = iter(count)
    for count in count_iter:
        merged_count = count + next(count_iter)
        count_merged.append(merged_count)

    return np.array(count_merged)


def get_bearing(place, query):
    try:
        graph = ox.graph_from_place(query, network_type='drive')
    except Exception:
        return

    # calculate edge bearings
    graph = ox.add_edge_bearings(graph)

    if weight_by_length:
        # weight bearings by length (meters)
        streets = [
            (d['bearing'], int(d['length']))
            for u, v, k, d in graph.edges(keys=True, data=True)
        ]
        city_bearings = []
        for street in streets:
            city_bearings.extend([street[0]] * street[1])
        return graph, pd.Series(city_bearings)
    else:
        # don't weight bearings, just take one value per street segment
        return graph, pd.Series([
            data['bearing']
            for u, v, k, data in graph.edges(keys=True, data=True)
            if data['bearing'] != 0.0
        ])


def get_filename(default='images/street-orientation', extension='png'):
    path = f'{default}.{extension}'
    counter = 0
    while os.path.exists(path):
        counter += 1
        path = os.path.join(f'{default}-{counter}.{extension}')
    return path


def load_places():
    try:
        with open(sys.argv[-1], 'r', encoding='utf-8') as source:
            result = json.load(source)
    except Exception:
        print(f'Tried and failed to open file at {sys.argv[-1]}. '
              'Please pass a json file with city data to this program.')
        sys.exit(-1)
    return result


def get_bearings(places):
    try:
        gdf = ox.gdf_from_places(places.values())
    except Exception as e:
        print(f'Failed to load city data: {e}')

    bearings = {
        place: get_bearing(place, places[place])
        for place in sorted(places.keys())
    }
    return {
        key: value
        for key, value in bearings.items()
        if value is not None
    }


def print_list():
    places = load_places()
    bearings = get_bearings(places)
    # create figure and axes
    n = len(places)
    if n < 2:
        print('Please use the "list" mode only if you have two or more cities to display!')
        sys.exit(-1)
    ncols = int(np.ceil(np.sqrt(n)))
    nrows = int(np.ceil(n / ncols))
    figsize = (ncols * 5, nrows * 5)
    fig, axes = plt.subplots(
        nrows, ncols, figsize=figsize,
        subplot_kw={'projection': 'polar'},
    )
    axes = [item for sublist in axes for item in sublist]

    # plot each city's polar histogram
    for ax, place in zip(axes, sorted(places.keys())):
        if place in bearings:
            try:
                polar_plot(ax, bearings[place][1], title=place)
            except Exception as e:
                print(f'Failed to build polar plot for {place}: {e}')
                continue
    plt.gcf().savefig(get_filename(default=f'images/street_orientation'), dpi=120, bbox_inches='tight')
    plt.close()


def print_single():
    places = load_places()
    bearings = get_bearings(places)

    for place in places:
        # create figure and axes
        graph, bearing = bearings[place]
        axes = plt.subplot(projection='polar')
        try:
            polar_plot(axes, bearing, title=place)
            polar_path = get_filename(f'images/{place}_polar')
            plt.gcf().savefig(polar_path, dpi=120, bbox_inches='tight')
            plt.close()
        except Exception as e:
            print(f'Failed to build polar plot for {place}: {e}')
            continue
        fig, axes = ox.plot_graph(graph, fig_height=12, node_size=0, edge_linewidth=0.8, show=False)
        map_path = get_filename(f'images/{place}_map')
        fig.savefig(map_path, show=False)

        goal_path = get_filename(f'images/{place}')
        with suppress(Exception):
            subprocess.call(f'composite {polar_path} {map_path} -gravity SouthEast -blend 100 {goal_path}', shell=True)
            os.remove(polar_path)
            os.remove(map_path)


def check_places():
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


def print_help():
    print('Usage: street_orientation.py MODE FILE')
    print('Generates radial histogram plots from the direction of a region\'s streets.')
    print('\nThe MODE argument must be "check", "list" or "single".\n')
    print('  check data/cities.json   Checks that all data points in data/cities.json are')
    print('                           regions, not points.')
    print('  list data/cities.json    Generate a file in images/ containing charts for all,')
    print('                           cities in data/cities.json')
    print('  single data/cities.json  Generate files in images/ for all, cities in')
    print('                           data/cities.json')


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print_help()
        sys.exit(-1)
    mode = sys.argv[1]
    if mode == 'list':
        try:
            print_list()
        except Exception as e:
            print(f'Error during list generation: {e}.')
    elif mode == 'single':
        try:
            print_single()
        except Exception as e:
            print(f'Error during image generation: {e}.')
    elif mode == 'check':
        check_places()
    else:
        print_help()
        sys.exit(-1)
