import os

import matplotlib.pyplot as plt
import numpy as np
import osmnx as ox
import pandas as pd


# Configuration, or what passes as such
font = {'family': 'Titillium'}
tick_font = {'weight': 'bold', 'zorder': 3}
supertitle_font = {'fontsize': 60, 'y': 1.07, **font}
title_font = {'size': 24, 'weight': 'bold', **font}
xtick_font = {'size': 10, 'alpha': 1.0, **font, **tick_font}
ytick_font = {'size': 9, 'alpha': 0.2, **font, **tick_font}

ox.config(log_console=True, use_cache=True)
weight_by_length = False

places = {
    'Augsburg': 'Augsburg, Germany',
    'Berlin': {'state': 'Berlin', 'country': 'Germany'},
    'Bielefeld': 'Bielefeld, Germany',
    'Bochum': 'Bochum, Germany',
    'Bremen': 'Bremen, Germany',
    'Essen': 'Essen, Germany',
    'Gelsenkirchen': 'Gelsenkirchen, Germany',
    'Hannover': 'Hannover, Germany',
    'Karlsruhe': 'Karlsruhe, Germany',
    'Köln': 'Cologne, Germany',
    'München': 'München, Germany',
    'Münster': 'Münster, Germany',
    'Nürnberg': 'Nürnberg, Germany',
}


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


def get_bearing(place):
    query = places[place]
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
        return pd.Series(city_bearings)
    else:
        # don't weight bearings, just take one value per street segment
        return pd.Series([
            data['bearing']
            for u, v, k, data in graph.edges(keys=True, data=True)
        ])


def get_filename(default='images/street-orientation', extension='png'):
    path = f'{default}.{extension}'
    counter = 0
    while os.path.exists(path):
        counter += 1
        path = os.path.join('{default}-{counter}.{extension}')
    return path


if __name__ == '__main__':
    gdf = ox.gdf_from_places(places.values())
    bearings = {
        place: get_bearing(place)
        for place in sorted(places.keys())
    }
    bearings = {
        key: value
        for key, value in bearings.items()
        if value is not None
    }

    # create figure and axes
    n = len(places)
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
            polar_plot(ax, bearings[place], title=place)

    # Add super title and save full image
    fig.suptitle('City Street Network Orientation', **supertitle_font)
    fig.tight_layout()
    fig.subplots_adjust(hspace=0.35)
    plt.gcf().savefig(get_filename(), dpi=120, bbox_inches='tight')
    plt.close()
