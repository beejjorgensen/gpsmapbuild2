"""
* **Write GJ to GPX converter**
* Run gpxcat -d 50 to merge NCR data
* **Write track splitter based on max points**
* Run existing gjwaypoints tool
* Run existing simplification process
"""

import sys
import json

from math import asin, sin, cos, sqrt

def usage():
    s = "usage: gjjoinway.py [options] way_name json_file\n" \
        "       --indent indent_level\n" \
        "       -o outfile"

    print(s, file=sys.stderr)

def usage_exit(status=1):
    usage()
    sys.exit(status)

class AppContext:
    def __init__(self, argv):
        self.argv = argv[:]

        self.indent_level = None
        self.way_name = None
        self.in_file_name = None
        self.out_file_name = None

        self.parse_cl()
    
    def consume_option_with_arg(self):
        self.argv.pop(0) 

        if self.argv == []:
            usage_exit()

    def read_indent_option(self):
        self.consume_option_with_arg()

        try:
            self.indent_level = int(self.argv[0])
        except:
            usage_exit(2)
    
    def read_o_option(self):
        self.consume_option_with_arg()

        self.out_file_name = self.argv[0]

    def parse_cl(self):
        self.command = self.argv.pop(0)

        while self.argv != []:
            if self.argv[0] == "-h" or self.argv[0] == "--help":
                usage_exit(0)

            elif self.argv[0] == "--indent":
                self.read_indent_option()

            elif self.argv[0] == "-o":
                self.read_o_option()

            elif self.way_name is None:
                self.way_name = self.argv[0]

            elif self.in_file_name is None:
                self.in_file_name = self.argv[0]

            else:
                usage_exit()

            self.argv.pop(0)

        if self.way_name is None or self.in_file_name is None:
            usage_exit()

def lldist(lat0, lon0, lat1, lon1):

    f1 = sin((lat0 - lat1) / 2)**2  
    f2 = cos(lat0) * cos(lat1)
    f3 = sin((lon0 - lon1) / 2)**2

    x = sqrt(f1 + f2 * f3)

    d = 2 * asin(x)

    return d

def read_input_file(in_file_name):
    if in_file_name == "-":
        in_file = sys.stdin

    else:
        in_file = open(in_file_name)

    data_str = in_file.read()

    in_file.close()

    return json.loads(data_str)

def get_feature_geom_type(f):
    try:
        return f["geometry"]["type"]
    except KeyError:
        return None

def get_feature_title(f):
    try:
        return f["properties"]["title"]
    except KeyError:
        return None

def extract_ways(data, name):
    features = data["features"]
    ways = []

    # Inventory ways of name "name"

    for f in features:

        if f["type"] != "Feature":
            continue

        geom_type = get_feature_geom_type(f)

        title = get_feature_title(f)

        if geom_type == "LineString" and title == name:
            ways.append(f)

    # Delete those ways from the original object

    for w in ways:
        features.remove(w)

    return ways

def merge_ways(ways):
    new_way = {}

    # The new way can take on the properties of the first old one
    new_way["type"] = ways[0]["type"]
    new_way["id"] = ways[0]["id"]
    new_way["properties"] = ways[0]["properties"]

    coords = []


    # -- bookmark --
    # TODO sort the ways


    geometry = {
        "type": "LineString",
        "coordinates": coords
    }

    new_way["geometry" ] = geometry

    return new_way

def main(argv):
    ac = AppContext(argv)

    input_data = read_input_file(ac.in_file_name)

    ways = extract_ways(input_data, ac.way_name)

    ways = merge_ways(ways)

    #print(json.dumps(ways, indent=4))
    #print(json.dumps(input_data, indent=4))

if __name__ == "__main__":
    sys.exit(main(sys.argv))

