import sys
import json
import uuid
import math

def usage():
    s = "usage: gjsplittrack.py [options] track_name json_file max_points\n" \
        "       --indent indent_level\n" \
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

            elif self.argv[0] == "-v":
                self.verbose = True

            elif self.argv[0] == "--indent":
                self.read_indent_option()

            elif self.argv[0] == "-o":
                self.read_o_option()

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

        if self.track_name is None or \
            self.in_file_name is None or \
            self.max_points is None:

            usage_exit()

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

def extract_track(data, name):
    features = data["features"]

    found_track = None

    for f in features:

        if f["type"] != "Feature":
            continue

        geom_type = get_feature_geom_type(f)

        title = get_feature_title(f)

        if geom_type == "LineString" and title == name:
            found_track = f
            break

    assert found_track is not None, "couldn't find track"

    features.remove(found_track)

    return found_track

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

    if track_points <= max_points:
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

def add_tracks(data, tracks):
    data["features"] += tracks

def main(argv):
    ac = AppContext(argv)

    input_data = read_input_file(ac.in_file_name)

    track = extract_track(input_data, ac.track_name)

    split_tracks = split_track(track, ac.max_points, ac.verbose)

    add_tracks(input_data, split_tracks)

    if ac.out_file_name is None or ac.out_file_name == "-":
        fp = sys.stdout
    else:
        fp = open(ac.out_file_name, 'w')

    print(json.dumps(input_data, indent=ac.indent_level), file=fp)

    fp.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))

