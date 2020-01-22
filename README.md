# CraigslistHousing
Python Exercise with Craigslist Scraper

Tools:

Python

Craigslist package

GeoJSON

Script pulls Apartment listings from Craigslist based on defined search parameters.

Compares geotagged location to the location of a group of points in a GeoJSON.
- LA Metro Gold Line Stations in this case.

Determines the straight-line distance to the nearest station.

If the distance is less than a defined value and the posting hasn't been seen previously, it is posted to a private Slack channel.

Project is intended to run on a Raspbery Pi, so distance calculations are performed in pure Python.
Might update in future to leverage Geopandas.
