import sys
import json
import math

from math import asin, sin, cos, sqrt

MERGE_DIST_M = 50

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

def lldist(lat1, lon1, lat2, lon2):
    R = 6.3781e6  # Earth radius in meters

    a1 = lat1 * math.pi/180;
    a2 = lat2 * math.pi/180;
    d1 = (lat2-lat1) * math.pi/180;
    d2 = (lon2-lon1) * math.pi/180;

    a = math.sin(d1/2)**2 + \
        math.cos(a1) * math.cos(a2) * \
        math.sin(d2/2)**2;

    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a));

    d = R * c

    return d  # meters

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

def copy_way_props(new_way, old_way):
    new_way["type"] = old_way["type"]
    new_way["id"] = old_way["id"]
    new_way["properties"] = old_way["properties"]
    new_way["geometry"] = old_way["geometry"]


def merge_ways(ways):
    new_way = {}

    # The new way can take on the properties of the last old one
    copy_way_props(new_way, ways.pop(0))

    # Go through all remaining ways and see if they're leaders or
    # trailers of the current way

    while ways != []:
        merged_way = None

        for w in ways:
            wgc = w["geometry"]["coordinates"]
            nwgc = new_way["geometry"]["coordinates"]

            # Check for leader
            dist = lldist(*wgc[-1], *nwgc[0])

            if dist <= MERGE_DIST_M:
                if dist < 0.1: wgc.pop()
                merged_way = wgc + nwgc
                break
                
            # Check for reversed leader
            dist = lldist(*wgc[0], *nwgc[0])

            if dist <= MERGE_DIST_M:
                wgc.reverse()
                if dist < 0.1: wgc.pop()
                merged_way = wgc + nwgc
                break
                
            # Check for trailer
            dist = lldist(*wgc[0], *nwgc[-1])

            if dist <= MERGE_DIST_M:
                if dist < 0.1: nwgc.pop()
                merged_way = nwgc + wgc
                break

            # Check for reversed trailer
            dist = lldist(*wgc[-1], *nwgc[-1])

            if dist <= MERGE_DIST_M:
                wgc.reverse()
                if dist < 0.1: nwgc.pop()
                merged_way = nwgc + wgc
                break

        assert merged_way is not None, "couldn't merge a way"
        new_way["geometry"]["coordinates"] = merged_way

        ways.remove(w)

    return new_way

def add_way(data, way):
    data["features"].append(way)
    
def main(argv):
    ac = AppContext(argv)

    input_data = read_input_file(ac.in_file_name)

    ways = extract_ways(input_data, ac.way_name)

    merged_way = merge_ways(ways)

    add_way(input_data, merged_way)

    if ac.out_file_name is None or ac.out_file_name == "-":
        fp = sys.stdout
    else:
        fp = open(ac.out_file_name, 'w')

    print(json.dumps(input_data, indent=ac.indent_level), file=fp)

if __name__ == "__main__":
    sys.exit(main(sys.argv))

