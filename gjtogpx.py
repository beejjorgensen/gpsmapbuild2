#!/usr/bin/env python3

# ./gjwaypoints.py test.json

#
# Icons:
#
# https://freegeographytools.com/2008/garmin-gps-unit-waypoint-icons-table

import sys
import json
import re
from xml.sax.saxutils import escape

class Waypoint:
    def __init__(self, name, lat, lon, garmin_sym, osmand_sym, color, desc=None):
        self.name = name
        self.lat = lat
        self.lon = lon
        self.garmin_sym = garmin_sym
        self.osmand_sym = osmand_sym
        self.color = color
        self.desc = desc

class Track:
    def __init__(self, name, coords):
        self.name = name
        self.coords = coords

def usage():
    """
    Print a usage message.
    """

    print("usage: gjwaypoints.py file.json name", file=sys.stderr)

def toxml(name, waypoints, tracks):
    """
    Return XML string of all data.
    """

    r = '<?xml version="1.0"?><gpx version="1.0" creator="gjwaypoints" ' \
        'xmlns="http://www.topografix.com/GPX/1/0" ' \
        'xmlns:osmand="https://osmand.net/docs/technical/osmand-file-formats/osmand-gpx" ' \
        'xmlns:gpxtpx="https://www8.garmin.com/xmlschemas/TrackPointExtensionv1.xsd" ' \
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" ' \
        'xsi:schemaLocation="http://www.topografix.com/GPX/1/0 ' \
        'http://www.topografix.com/GPX/1/0/gpx.xsd">' \
        f'<name>{name}</name>'

    for w in waypoints:
        r += f'<wpt lat="{w.lat}" lon="{w.lon}">'
        r += f'<name>{escape(w.name)}</name>'
        r += f'<sym>{w.garmin_sym}</sym>'
        if w.desc is not None:
            r += f'<cmt>{escape(w.desc)}</cmt>'
        r += '<extensions>'
        r += f'<osmand:color>{w.color}</osmand:color>'
        r += f'<osmand:icon>{w.osmand_sym}</osmand:icon>'
        r += f'<osmand:background>circle</osmand:background>'
        r += '</extensions>'
        r += '</wpt>'

    for t in tracks:
        r += '<trk>'
        r += f'<name>{escape(t.name)}</name>'
        r += '<trkseg>'

        for c in t.coords:
            lon = c[0]
            lat = c[1]
            r += f'<trkpt lat="{lat}" lon="{lon}">'
            r += '</trkpt>'

        r += '</trkseg>'
        r += '</trk>'

    r += "</gpx>"

    return r

def sym_normalize(sym, name):
    placemark2_map = {
        "restroom|bathroom|washroom|toilet": "restroom",
        "ranger sta|guard sta": "residence",
        "Crescent Junction": "pin",  # The town
        "junction": "junction",
        "Edwards Crossing": "bridge",  # The bridge
        "crossing": "crossing",
        "cemetery|grave": "cemetery",
        "museum": "museum",
        "visitors+ center": "museum",
        "summit": "summit",
        "hardware|store|market|bi-?mart|fred meyer|walmart|grocer|minimart|albertsons|vons|safeway|merc[ae]ntile|food center|food place|thriftway|foods|winco|rosauers": "shopping",
        " mine$| mines?|^mining|^mine$|^mines$|mines both sides": "mine",
        "restarea|rest area": "restarea",
        "theater": "theater",
        "bridge": "bridge",
        "post +office|shipping post|ship it": "postoffice",
        "laundry|laundromat": "laundry",
        "wildlife area": "hunting",
        "^lake | lake$|^lake$": "lake",
        "auto parts": "carrepair",
        "u-?haul": "movingvan",
    }

    if sym == "placemark2":
        sym = None

        for key in placemark2_map:
            if re.search(key, name, re.I) is not None:
                sym = placemark2_map[key]
                break

    if sym == "danger" and re.search(r"cemetery|grave", name, re.I) is not None:
        sym = "cemetery"

    if sym == "foodservice" and \
            re.search(r"bar$|pub$|public house|brewpub", name, re.I) is not None:
        sym = "bar"

    if sym == "foodservice" and re.search(r"pizza", name, re.I) is not None:
        sym = "pizza"

    if sym in ("camping", "campfire") and re.search(r"campsite", name, re.I) is not None:
        sym = "campsite"

    return sym

def garmin_symbol_map(sym, name, color):
    # All red markers should be red-flagged
    if color == "FF0000" or color == "#FF0000":
        return "Flag, Red"

    sym = sym.split('$')[0]
    sym = sym_normalize(sym, name)

    if sym is None:
        print(f'Unknown name {name} for placemark2', file=sys.stderr)
        sym = "pin"

    sym_map = {
        "airport": "Airport",
        "atv": "Car",
        "automobile": "Car",
        "bar": "Bar",
        "bicycling-downhill": "Bike Trail",
        "bridge": "Bridge",
        "camping": "Campground",
        "campsite": "Park",
        "carrepair": "Car Repair",
        "caving": "Tunnel",
        "cemetery": "Cemetery",
        "circle-p": "Parking Area",
        "crossing": "Crossing",
        "danger": "Skull and Crossbones",
        "drinking-water": "Drinking Water",
        "firelookout": "Short Tower",
        "flag-1": "Flag, Blue",   # Black flag
        "flag-2": "Flag, Green",  # Checkered Flag
        "foodservice": "Restaurant",
        "fuel": "Gas Station",
        "gate-side": "Pin, Green",
        "hiking": "Trail Head",
        "hunting": "Hunting Area",
        "hut": "Lodging",
        "info": "Information",
        "junction": "Pin, Green",
        "lake": "Pin, Blue",
        "laundry": "Block, Green",
        "lodging": "Lodging",
        "mine": "Mine",
        "movingvan": "Truck Stop",
        "museum": "Museum",
        "peak": "Summit",
        "photo": "Scenic Area",
        "picnicbench": "Picnic Area",
        "pin": "Pin, Blue",
        "postoffice": "Post Office",
        "radiotower": "Tall Tower",
        "rangerstation2": "Residence",
        "residence": "Residence",
        "restarea": "Picnic Area",
        "restroom": "Restroom",
        "shelter-empty": "Lodge",
        "shopping": "Shopping Center",
        "summit": "Summit",
        "swimming": "Swimming Area",
        "theater": "Movie Theater",
        "usar-20": "Navaid, Red",    # Do Not Enter
        "warning": "Flag, Red",
        "waterfalls": "Scenic Area",
        "wilderness": "Park",
    }

    # Bank (dollar sign)
    # Park (single tree)
    # Mine (Shovel and pick)
    # Museum (Building with pillars)
    # Residence (House)
    # Fishing Hot Spot Facility (Small hut)
    # Lodge (Small hut with chimney)

    # https://freegeographytools.com/2008/garmin-gps-unit-waypoint-icons-table
    # https://www.gpsbabel.org/htmldoc-development/GarminIcons.html

    if sym not in sym_map:
        print(f'Symbol "{sym}" not in symbol map', file=sys.stderr)
        return "Blue Pin"

    return sym_map[sym]

def osmand_symbol_map(sym, name, color):
    sym = sym.split('$')[0]
    sym = sym_normalize(sym, name)

    new_color = "#0000ff"  # blue

    if sym is None:
        #print(f'Unknown name {name} for placemark2', file=sys.stderr)
        sym = "special_flag"

    sym_map = {
        "airport": "air_transport",
        "atv": "special_utv",
        "automobile": "shop_car",
        "bar": "amenity_pub",
        "bicycling-downhill": "special_bicycle",
        "bridge": "bridge_structure_arch",
        "camping": "tourism_camp_site",
        "campsite": "firepit",
        "carrepair": "shop_car_repair",
        "caving": "natural_cave_entrance",
        "cemetery": "cemetery",
        "circle-p": "amenity_parking",
        "crossing": "level_crossing",
        "danger": "hazard",
        "drinking-water": "amenity_drinking_water",
        "firelookout": "observation_tower",
        "flag-1": "special_flag",   # Black flag
        "flag-2": "special_flag_finish",  # Checkered Flag
        "foodservice": "restaurants",
        "fuel": "amenity_fuel",
        "gate-side": "barrier_gate",
        "hiking": "special_trekking",
        "hunting": "hunting",
        "hut": "special_house",
        "info": "special_information",
        "junction": "junction",
        "lake": "water",
        "laundry": "shop_laundry",
        "lodging": "tourism_hotel",
        "mine": "man_made_mineshaft",
        "movingvan": "special_truck",
        "museum": "tourism_museum",
        "peak": "natural",   # natural_peak
        "photo": "photo",
        "picnicbench": "tourism_picnic_site",
        "pin": "special_flag",
        "postoffice": "amenity_post_office",
        "radiotower": "communication_tower",
        "rangerstation2": "ranger_station",
        "residence": "special_house",
        "restarea": "rest_area",
        "restroom": "amenity_toilets",
        "shelter-empty": "amenity_shelter",
        "shopping": "shop_supermarket",
        "summit": "natural",
        "swimming": "swimming_pool",
        "theater": "amenity_cinema",
        "usar-20": "access_no",    # Do Not Enter
        "warning": "special_flag",
        "waterfalls": "waterfall",
        "wilderness": "forest",
    }

    # https://osmand.net/docs/technical/osmand-file-formats/osmand-gpx/
    # https://github.com/mariush444/gmapIcons2osmand/blob/main/icons-gmap-osmand.pdf

    # Force red if asked
    if color == "FF0000" or color == "#FF0000" or sym == "usar-20" or sym == "warning":
        new_color = "#ff0000"

    if sym in sym_map:
        sym = sym_map[sym]
    else:
        #print(f'Symbol "{sym}" not in symbol map', file=sys.stderr)
        sym = "special_flag"

    return sym, new_color

def get_waypoints_tracks(jdata):
    waypoints = []
    tracks = []

    assert(jdata["type"] == "FeatureCollection")

    features = jdata["features"]

    for f in features:
        if f["type"] != "Feature":
            continue

        if "geometry" not in f:
            continue

        if f["geometry"] is None:
            continue

        geom_type = f["geometry"]["type"]

        if geom_type == "Point":
            sym = f["properties"]["marker-symbol"]
            name = f["properties"]["title"]
            color = f["properties"]["marker-color"] if "marker-color" in f["properties"] else "#000000"

            garmin_sym = garmin_symbol_map(sym, name, color)
            osmand_sym, color = osmand_symbol_map(sym, name, color)

            if "description" in f["properties"]:
                desc = f["properties"]["description"]
                desc = None if desc == "" else desc
            else:
                desc = None

            # Force to 6 or fewer decimal places
            c = f["geometry"]["coordinates"]
            c = list(map(lambda x: float(f'{x:.6f}'), c))

            wp = Waypoint(name, c[1], c[0], garmin_sym, osmand_sym, color, desc); # switch to lat,lon

            waypoints.append(wp)

        elif geom_type == "LineString":
            name = f["properties"]["title"]
            coords = f["geometry"]["coordinates"]

            track = Track(name, coords)

            tracks.append(track)
            
    return waypoints, tracks

def main(argv):
    """
    Main.
    """

    try:
        file_name = argv[1]
        name = argv[2]
    except:
        usage()
        return 1

    if file_name == "-":
        infile = sys.stdin
    else:
        infile = open(file_name)

    jdata = json.load(infile)

    waypoints, tracks = get_waypoints_tracks(jdata)

    xml_data = toxml(name, waypoints, tracks)

    print(xml_data)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

