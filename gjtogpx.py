#!/usr/bin/env python3

# ./gjwaypoints.py test.json

import sys
import json
import re

class Waypoint:
    def __init__(self, name, lat, lon, sym, desc=None):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.sym = sym
        self.desc = desc

def usage():
    """
    Print a usage message.
    """

    print("usage: gjwaypoints.py file.json name", file=sys.stderr)

def toxml(name, waypoints):
    """
    Return XML string of all data.
    """

    r = '<?xml version="1.0"?><gpx version="1.0" creator="gjwaypoints" ' \
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
        'xmlns="http://www.topografix.com/GPX/1/0" ' \
        'xsi:schemaLocation="http://www.topografix.com/GPX/1/0 ' \
        'http://www.topografix.com/GPX/1/0/gpx.xsd">' \
        f'<name>{name}</name>'

    for w in waypoints:
        r += f'<wpt lat="{w.lat}" lon="{w.lon}">'
        r += f'<name>{w.name}</name>'
        r += f'<sym>{w.sym}</sym>'
        if w.desc is not None:
            r += f'<cmt>{w.desc}</cmt>'
        r += '</wpt>'

    r += "</gpx>"

    return r

def symbol_map(sym, name, color):
    # All red markers should be red-flagged
    if color == "#FF0000":
        return "Flag, Red"

    sym = sym.split('$')[0]

    placemark2_map = {
        "restroom": "restroom",
        "ranger sta|guard sta": "residence",
        "Crescent Junction": "pin",  # The town
        "junction": "junction",
        "Edwards Crossing": "pin",  # The bridge
        "crossing": "crossing",
        "cemetery|grave": "cemetery",
        "store|market": "store",
        " mines?|^mining|^mine$|^mines$": "mine",
        "restarea|rest area": "restarea",
        "theater": "theater"
    }

    if sym == "placemark2":
        found = False

        for key in placemark2_map:
            if re.search(key, name, re.I) is not None:
                sym = placemark2_map[key]
                found = True
                break

        if not found:
            print(f'Unknown name {name} for placemark2',
                    file=sys.stderr)
            sym = "pin"

    if sym == "danger" and re.search(r"cemetery|grave", name, re.I) is not None:
        sym = "cemetery"

    if sym == "foodservice" and \
            re.search(r"bar$|pub$|public house|brewpub", name, re.I) is not None:
        sym = "bar"

    if sym == "foodservice" and re.search(r"pizza", name, re.I) is not None:
        sym = "pizza"

    sym_map = {
        "bar": "Bar",
        "atv": "Car",
        "bicycling-downhill": "Bike Trail",
        "camping": "Campground",
        "caving": "Tunnel",
        "restroom": "Restroom",
        "residence": "Residence",
        "drinking-water": "Drinking Water",
        "firelookout": "Short Tower",
        "flag-2": "Flag, Green",  # Checkered Flag
        "fuel": "Gas Station",
        "info": "Information",
        "peak": "Summit",
        "photo": "Scenic Area",
        "picnicbench": "Picnic Area",
        "restarea": "Picnic Area",
        "pin": "Pin, Blue",
        "usar-20": "Navaid, Red",    # Do Not Enter
        "waterfalls": "Scenic Area",
        "junction": "Pin, Green",
        "crossing": "Crossing",
        "warning": "Flag, Red",
        "danger": "Skull and Crossbones",
        "cemetery": "Cemetery",
        "hut": "Lodge",
        "lodging": "Lodge",
        "foodservice": "Restaurant",
        "shelter-empty": "Lodge",
        "rangerstation2": "Residence",
        "mine": "Mine",
        "museum": "Museum",
        "gate-side": "Pin, Green",
        "store": "Shopping",
        "theater": "Movie Theater",
        "airport": "Airport",
        "automobile": "Car",
    }

    # Bank (dollar sign)
    # Park (single tree)
    # Trail Head (hiking boot)
    # Mine (Shovel and pick)
    # Museum (Building with pillars)
    # Residence (House)
    # Fishing Hot Spot Facility (Small hut)
    # Lodge (Small hut with chimney)

    if sym not in sym_map:
        print(f'Symbol "{sym}" not in symbol map', file=sys.stderr)
        return "Blue Pin"

    return sym_map[sym]


def get_waypoints(jdata):
    waypoints = []

    assert(jdata["type"] == "FeatureCollection")

    features = jdata["features"]

    for f in features:
        if f["type"] != "Feature":
            continue

        if "geometry" not in f:
            continue

        if f["geometry"] is None:
            continue

        if f["geometry"]["type"] != "Point":
            continue

        sym = f["properties"]["marker-symbol"]
        name = f["properties"]["title"]
        color = f["properties"]["marker-color"] if "marker-color" in f["properties"] else "#000000"

        sym = symbol_map(sym, name, color)

        if "description" in f["properties"]:
            desc = f["properties"]["description"]
            desc = None if desc == "" else desc
        else:
            desc = None

        # Force to 6 or fewer decimal places
        c = f["geometry"]["coordinates"]
        c = list(map(lambda x: float(f'{x:.6f}'), c))

        wp = Waypoint(name, c[1], c[0], sym, desc); # switch to lat,lon

        waypoints.append(wp)

    return waypoints

def main(argv):
    """
    Main.
    """
    if len(argv) != 3:
        usage()
        return 1

    name = argv[2]

    with open(argv[1]) as fp:
        jdata = json.load(fp)

    # Read the data into internal representation
    waypoints = get_waypoints(jdata)

    # Output final XML
    print(toxml(name, waypoints))

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

