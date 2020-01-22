##Resources
##https://www.dataquest.io/blog/apartment-finding-slackbot/
##https://opensource.com/article/17/10/set-postgres-database-your-raspberry-pi
##https://suhas.org/sqlalchemy-tutorial/
##https://stackoverflow.com/questions/15736995/how-can-i-quickly-estimate-the-distance-between-two-latitude-longitude-points
## How I finally got libspatialindex to install in the raspberry pi. RTree package is dependent on it.
##http://www.donkeycar.com/faq/how-do-i-manually-install-the-software-on-raspberry-pi

import craigslist
import datetime
from craigslist import CraigslistHousing
from datetime import datetime
import json
import geojson
from geojson import Feature, Point, FeatureCollection
from math import radians, cos, sin, asin, sqrt
from slackclient import SlackClient
import time
import os
import private


startTime = datetime.now()
SLACK_CHANNEL = "#craigslist"

# Borrowed function to calculate distance between two Lat Long pairs
def coord_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    # Radius of earth in kilometers is 6371
    km = 6371* c
    mi = km * 0.621371
    return mi

# Function to search features in the GeoJson and return the nearest
def findNearest(data, lat, lon):
    nearStation = []
    nearDist = []
    for feature in data['features']:
        point = feature['geometry']['coordinates']
        latitude = point[1]
        longitude = point[0]
        station = feature['properties']['STATION']
        #calculate distance between apartment and station
        dist = coord_distance(lon, lat, longitude, latitude)
        if len(nearDist) == 0:
            nearDist.insert(0, dist)
            nearStation.insert(0, station)
        elif dist < nearDist[0]:
            nearDist[0] = dist
            nearStation[0] = station
    result = [nearStation[0], nearDist[0]]
    return result

# Function to add new features to GeoJson
def createFeature(result):
    newFeature = Feature(geometry=Point((result['geotag'][1], result['geotag'][0])))
    newFeature["properties"]["id"] = result["id"]
    newFeature["properties"]["name"] = result["name"]
    newFeature["properties"]["url"] = result["url"]
    newFeature["properties"]["datetime"] = result["datetime"]
    newFeature["properties"]["price"] = result["price"]
    newFeature["properties"]["bedrooms"] = result["bedrooms"]
    print(newFeature)
    return newFeature

# Load Station GeoJSON
stations = os.path.join(os.getcwd(),'CraigslistHousing', 'GoldLineStations.geojson')
with open(stations) as f:
    data = geojson.load(f)

# Make query to Craigslist using craigslist package
cl_h = CraigslistHousing(site='losangeles', area='sgv', category='apa',
                         filters={'max_price': 1600, 'min_price': 1000, 'min_bedrooms':1, 'max_bedrooms': 1})

# Load Private Token for Slack Channel
sc = SlackClient(private.SLACK_TOKEN)

# Load GeoJSON of previously seen apartments
apartFile = os.path.join(os.getcwd(),'CraigslistHousing', 'apartments.geojson')
with open(apartFile) as f:
    apartments = geojson.load(f)
    
# Get apartments that are already in the GeoJSON
posted = apartments["features"]
# Get Posting ID for each apartment in the GeoJSON
postedID = [item["properties"]["id"] for item in posted]

# For each posting in the new Craigslist results pull the coordinates of the Geotag
for result in cl_h.get_results(sort_by='newest', geotagged=True):
    try:
        location = result['geotag']
        latitude = location[0]
        longitude = location[1]
        #print(str(latitude) + ', ' + str(longitude))
    except:
        continue
# Calculate the closest station based on the geotag
    closestStation = findNearest(data, latitude, longitude)
    closestStationName = closestStation[0]
    print(closestStation)
    closestStationDist = round(float(closestStation[1]),2)
    print(closestStationDist)
# Ignore results that are farther than .5 mi
    if float(closestStationDist) > 0.5:
        continue
        #print("Outside Search Area")
    else:
        # Ignore results that are already in the GeoJSON
        if result['id'] in postedID:
            print("Already Saw It!")
            continue
        # All remaining are new and within the search area.
        else:
            # Format description of apartment
            print(result['geotag'])
            print(result['url'])
            print('Only ' + str(closestStationDist) + 'mi from ' + closestStationName)
            desc = "{0} | {1} mi from {2} | {3} | <{4}>".format(result["price"], str(closestStationDist), closestStationName, result["name"], result["url"])
            # Post description to Slack
            sc.api_call(
            "chat.postMessage", channel=SLACK_CHANNEL, text=desc,
            username='pybot', icon_emoji=':robot_face:'
            )
            # Create a GeoJSON feature for the new apartment
            feature = createFeature(result)
            # Add new apartment to the GeoJSON
            posted.append(feature)
            postedID.append(result['id'])
            #tempResults.update(result)
apartments["features"]=posted
# Save updated GeoJSON to disk.
with open(apartFile , 'w') as outfile:
    json.dump(apartments, outfile)
# Post message to Slack confirming run incase there were no new apartments.
sc.api_call(
            "chat.postMessage", channel=SLACK_CHANNEL, text='Run Complete',
            username='pybot', icon_emoji=':robot_face:'
            )

