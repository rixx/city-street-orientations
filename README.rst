German city street network orientations
---------------------------------------

Based on an `osmnx example`_ and the `accompanying blogpost`_, I'm playing
around with German and European cities. I also released a `blog post`_ of my
own, and posted some on-demand images on `mastodon`_, including one image for
all of Denmark.

If you want to use this: Install the requirements named in
``requirements.txt``, then take a look at the data files and build your own.
You can have as many cities in there as you wish, but it should be at least
three. Next, check that the cities you entered all refer to valid regions, and
not just points on the map::

    python street_orientation.py check data/my_cities.json

If this script doesn't print anything, you're good, and can run::

    python street_orientation.py list data/my_cities.json

Depending on the amount of cities you chose, and their size, and the computer
you're running this on, expect it to take about five to fifteen minutes. The
script prints a lot of debug output, so you'll know it's still working.

If you want an image with the radial histogram of one city with the map of the
city, run this instead::

    python street_orientation.py single data/my_cities.json

.. _osmnx example: https://github.com/gboeing/osmnx-examples/blob/master/notebooks/17-street-network-orientations.ipynb
.. _accompanying blogpost: http://geoffboeing.com/2018/07/comparing-city-street-orientations/
.. _blog post: https://rixx.de/blog/street-orientantions/
.. _mastodon: https://chaos.social/@rixx/100374777261107270
