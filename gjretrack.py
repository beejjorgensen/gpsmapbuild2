import sys
import json
import uuid
import math

MERGE_DIST_M = 50

def usage():
    s = "usage: gjretrack.py [options] track_name json_file\n" \
        "       --indent indent_level\n" \
        "       -m max_points" \
        "       -v verbose\n" \
        "       -o outfile"

    print(s, file=sys.stderr)

def usage_exit(status=1):
    usage()
    sys.exit(status)

class AppContext:
    def __init__(self, argv):
        self.argv = argv[:]

        self.indent_level = None
        self.max_points = None
        self.track_name = None
        self.in_file_name = None
        self.out_file_name = None
        self.verbose = False

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
    
    def read_m_option(self):
        self.consume_option_with_arg()

        try:
            self.max_points = int(self.argv[0])
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

            elif self.argv[0] == "-v":
                self.verbose = True

            elif self.argv[0] == "--indent":
                self.read_indent_option()

            elif self.argv[0] == "-o":
                self.read_o_option()

            elif self.argv[0] == "-m":
                self.read_m_option()

            elif self.track_name is None:
                self.track_name = self.argv[0]

            elif self.in_file_name is None:
                self.in_file_name = self.argv[0]

            elif self.max_points is None:
                try:
                    self.max_points = int(self.argv[0])
                except ValueError:
                    usage_exit()

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

def get_feature_geom_coordinates(f):
    try:
        return f["geometry"]["coordinates"]
    except KeyError:
        return None

def copy_track_props(new_track, old_track, copy_coords=False):
    new_track["type"] = old_track["type"]
    new_track["id"] = old_track["id"]
    new_track["properties"] = old_track["properties"].copy()
    new_track["geometry"] = {}
    new_track["geometry"]["type"] = old_track["geometry"]["type"]

    if copy_coords:
        new_track["geometry"]["coordinates"] = \
            old_track["geometry"]["coordinates"].copy()
    else:
        new_track["geometry"]["coordinates"] = []

def split_track(track, max_points, verbose=False):
    new_tracks = []

    track_coords = get_feature_geom_coordinates(track)
    track_points = len(track_coords)

    if max_points is None or track_points <= max_points:
        if verbose:
            print("no splitting required")
        return [track]

    segment_count = math.ceil(track_points / max_points)
    points_per_segment = track_points / segment_count

    if verbose:
        print(f"total track points: {track_points}")
        print(f"segment count:      {segment_count}")
        print(f"points per segment: {int(points_per_segment+0.5)} " \
            f"({max_points} requested)")

    tgc = track["geometry"]["coordinates"]

    for i in range(segment_count):
        start_coord = int(i * points_per_segment)

        if i == segment_count - 1:
            # Special case for the last segment to force it to the end.
            # Actually one less than the end, since we have a +1 below.
            end_coord = track_points - 1
        else:
            end_coord = int((i+1) * points_per_segment)

        segment = {}
        copy_track_props(segment, track)
        segment['properties']['title'] += f" {i+1}"
        segment['id'] = str(uuid.uuid4())

        segment["geometry"]["coordinates"] = tgc[start_coord:end_coord+1]

        new_tracks.append(segment)

    return new_tracks

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

def merge_tracks(tracks):
    new_track = {}

    # The new track can take on the properties of the last old one
    copy_track_props(new_track, tracks.pop(0), copy_coords=True)

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

def add_tracks(data, tracks):
    data["features"] += tracks

def main(argv):
    ac = AppContext(argv)

    input_data = read_input_file(ac.in_file_name)

    tracks = extract_tracks(input_data, ac.track_name)

    merged_track = merge_tracks(tracks)

    split_tracks = split_track(merged_track, ac.max_points, ac.verbose)

    add_tracks(input_data, split_tracks)

    if ac.out_file_name is None or ac.out_file_name == "-":
        fp = sys.stdout
    else:
        fp = open(ac.out_file_name, 'w')

    print(json.dumps(input_data, indent=ac.indent_level), file=fp)

    fp.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))

