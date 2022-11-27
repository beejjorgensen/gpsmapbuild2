import sys
import json
import math

from math import asin, sin, cos, sqrt

MERGE_DIST_M = 50

def usage():
    s = "usage: gjjointrack.py [options] track_name json_file\n" \
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
        self.track_name = None
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

            elif self.track_name is None:
                self.track_name = self.argv[0]

            elif self.in_file_name is None:
                self.in_file_name = self.argv[0]

            else:
                usage_exit()

            self.argv.pop(0)

        if self.track_name is None or self.in_file_name is None:
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

def extract_tracks(data, name):
    features = data["features"]
    tracks = []

    # Inventory tracks of name "name"

    for f in features:

        if f["type"] != "Feature":
            continue

        geom_type = get_feature_geom_type(f)

        title = get_feature_title(f)

        if geom_type == "LineString" and title == name:
            tracks.append(f)

    # Delete those tracks from the original object

    for t in tracks:
        features.remove(t)

    return tracks

def copy_track_props(new_track, old_track):
    new_track["type"] = old_track["type"]
    new_track["id"] = old_track["id"]
    new_track["properties"] = old_track["properties"]
    new_track["geometry"] = old_track["geometry"]


def merge_tracks(tracks):
    new_track = {}

    # The new track can take on the properties of the last old one
    copy_track_props(new_track, tracks.pop(0))

    # Go through all remaining tracks and see if they're leaders or
    # trailers of the current track

    while tracks != []:
        merged_track = None

        for t in tracks:
            wgc = t["geometry"]["coordinates"]
            nwgc = new_track["geometry"]["coordinates"]

            # Check for leader
            dist = lldist(*wgc[-1], *nwgc[0])

            if dist <= MERGE_DIST_M:
                if dist < 0.1: wgc.pop()
                merged_track = wgc + nwgc
                break
                
            # Check for reversed leader
            dist = lldist(*wgc[0], *nwgc[0])

            if dist <= MERGE_DIST_M:
                wgc.reverse()
                if dist < 0.1: wgc.pop()
                merged_track = wgc + nwgc
                break
                
            # Check for trailer
            dist = lldist(*wgc[0], *nwgc[-1])

            if dist <= MERGE_DIST_M:
                if dist < 0.1: nwgc.pop()
                merged_track = nwgc + wgc
                break

            # Check for reversed trailer
            dist = lldist(*wgc[-1], *nwgc[-1])

            if dist <= MERGE_DIST_M:
                wgc.reverse()
                if dist < 0.1: nwgc.pop()
                merged_track = nwgc + wgc
                break

        assert merged_track is not None, "couldn't merge a track"
        new_track["geometry"]["coordinates"] = merged_track

        tracks.remove(t)

    return new_track

def add_track(data, track):
    data["features"].append(track)
    
def main(argv):
    ac = AppContext(argv)

    input_data = read_input_file(ac.in_file_name)

    tracks = extract_tracks(input_data, ac.track_name)

    merged_track = merge_tracks(tracks)

    add_track(input_data, merged_track)

    if ac.out_file_name is None or ac.out_file_name == "-":
        fp = sys.stdout
    else:
        fp = open(ac.out_file_name, 'w')

    print(json.dumps(input_data, indent=ac.indent_level), file=fp)

if __name__ == "__main__":
    sys.exit(main(sys.argv))

