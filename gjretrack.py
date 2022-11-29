#!/usr/bin/env python3

import sys
import json
import uuid
import math

JOIN_MAX_DIST_M = 50
DECIMAL_PLACES = 6

def usage():
    s = "usage: gjretrack.py [options] json_file\n" \
        f"       -d n         decimal places for lat, lon [default {DECIMAL_PLACES}]\n" \
        "       -e           epsilon, smoothing max distance\n" \
        "       --indent n   indent level, spaces\n" \
        "       -j           join tracks of same name\n" \
        f"       --joinmax n  maximum distance to join tracks [default {JOIN_MAX_DIST_M} meters]\n" \
        "       -m n         max points per track\n" \
        "       -o name      output file name\n" \
        "       -v           verbose"

    print(s, file=sys.stderr)

def usage_exit(status=1):
    usage()
    sys.exit(status)

def log(s):
    print(s, file=sys.stderr)

class AppContext:
    def __init__(self, argv):
        self.argv = argv[:]

        self.join_tracks = False
        self.indent_level = None
        self.max_points = None
        self.in_file_name = None
        self.out_file_name = None
        self.verbose = False
        self.epsilon = None
        self.decimal_places = DECIMAL_PLACES
        self.join_max_dist = JOIN_MAX_DIST_M

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

    def read_e_option(self):
        self.consume_option_with_arg()

        try:
            self.epsilon = float(self.argv[0])
        except:
            usage_exit(2)
    
    def read_joinmax_option(self):
        self.consume_option_with_arg()

        try:
            self.joinmax = float(self.argv[0])
        except:
            usage_exit(2)
    
    def read_d_option(self):
        self.consume_option_with_arg()

        try:
            self.decimal_places = int(self.argv[0])
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

            elif self.argv[0] == "-j":
                self.join_tracks = True

            elif self.argv[0] == "--indent":
                self.read_indent_option()

            elif self.argv[0] == "-o":
                self.read_o_option()

            elif self.argv[0] == "-m":
                self.read_m_option()

            elif self.argv[0] == "-e":
                self.read_e_option()

            elif self.argv[0] == "-d":
                self.read_d_option()

            elif self.argv[0] == "--joinmax":
                self.read_joinmax_option()

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

        if self.in_file_name is None:
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

def dist_point_line(point, line0, line1):
    # https://en.wikipedia.org/wiki/Distance_from_a_point_to_a_line

    x0, y0 = point
    x1, y1 = line0
    x2, y2 = line1

    return abs((x2 - x1) * (y1 - y0) - (x1 - x0) * (y2 - y1)) / \
        math.sqrt((x2 - x1)**2 + (y2 - y1)**2)

def dist_point_great_circle(point, line0, line1):
    # https://web.archive.org/web/20171230114759/http://mathforum.org/library/drmath/view/51785.html

    def to_cartesian(lat, lon):
        return [
            math.cos(lat) * math.cos(lon),
            math.cos(lat) * math.sin(lon),
            math.sin(lat)
        ]

    def cross3(v0, v1):
        a1, a2, a3 = v0
        b1, b2, b3 = v1

        return [
            a2 * b3 - a3 * b2,
            a3 * b1 - a1 * b3,
            a1 * b2 - a2 * b1
        ]

    def dot3(v0, v1):
        return \
            v0[0] * v1[0] + \
            v0[1] * v1[1] + \
            v0[2] * v1[2]

    def scale3(v, s):
        v[0] *= s
        v[1] *= s
        v[2] *= s

        return v

    def length3(v):
        return math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)

    def normalize3(v):
        return scale3(v, 1 / length3(v))

    point_r = [math.radians(point[0]), math.radians(point[1])]
    line0_r = [math.radians(line0[0]), math.radians(line0[1])]
    line1_r = [math.radians(line1[0]), math.radians(line1[1])]

    point_3 = to_cartesian(*point_r)
    line0_3 = to_cartesian(*line0_r)
    line1_3 = to_cartesian(*line1_r)

    cp = cross3(line0_3, line1_3)

    normalize3(cp)

    dp = dot3(cp, point_3)

    a = math.pi / 2 - math.acos(dp)

    R = 6.3781e6  # Earth radius in meters

    return abs(a * R)

def douglas_peucker(track, epsilon, verbose):
    # https://en.wikipedia.org/wiki/Ramer%E2%80%93Douglas%E2%80%93Peucker_algorithm

    def dpr(points):
        max_dist = 0
        max_dist_index = None

        for i in range(1, len(points) - 1):
            #pdist = dist_point_line(points[i], points[0], points[-1])
            gcdist = dist_point_great_circle(points[i], points[0], points[-1])

            if gcdist > max_dist:
                max_dist = gcdist
                max_dist_index = i

        if max_dist > epsilon:
            left = dpr(points[:max_dist_index+1])
            right = dpr(points[max_dist_index:])

            left.pop()

            result = left + right
        else:
            result = [points[0], points[-1]]

        return result

    coords = track["geometry"]["coordinates"]

    coord_count_before = len(coords)

    simplified_coords = dpr(coords)
    track["geometry"]["coordinates"] = simplified_coords
    
    coord_count_after = len(simplified_coords)

    if verbose:
       log(f'{track["properties"]["title"]}: simplifying: ' \
            "coord count after/before " \
            f"{coord_count_after}/{coord_count_before}, " \
            f"{coord_count_after/coord_count_before*100:.1f}%")

    return track

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
        return [track]

    segment_count = math.ceil(track_points / max_points)
    points_per_segment = track_points / segment_count

    if verbose:
        title = track['properties']['title']
        log(f"{title}: split: total track points: {track_points}")
        log(f"{title}: split: segment count: {segment_count}")
        log(f"{title}: split: points per segment: " \
            f"{int(points_per_segment+0.5)}")

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
        segment['properties']['title'] += f"-{i+1}"
        segment['id'] = str(uuid.uuid4())

        segment["geometry"]["coordinates"] = tgc[start_coord:end_coord+1]

        new_tracks.append(segment)

    return new_tracks

def extract_track(data, do_join_tracks, join_max_dist, verbose):
    features = data["features"]
    tracks = []

    track_name = None

    for f in features:

        if f["type"] != "Feature":
            continue

        geom_type = get_feature_geom_type(f)

        if geom_type != "LineString":
            continue

        title = get_feature_title(f)

        if track_name is None:
            if verbose:
                log(f"{title}: extracting track")

            track_name = title

        if do_join_tracks:
            if track_name == title:
                tracks.append(f)

        else:
            tracks.append(f)
            break

    # No more tracks left?

    if tracks == []:
        return None

    # Delete those tracks from the original object

    for t in tracks:
        features.remove(t)

    # Join tracks if necessary

    if do_join_tracks:
        if verbose and len(tracks) > 1:
            log(f"{track_name}: joining: {len(tracks)} segments")

        extracted_track = join_tracks(tracks, join_max_dist)
    else:
        assert len(tracks) == 1, "too many non-joined tracks extracted"
        extracted_track = tracks[0]

    return extracted_track

def join_tracks(tracks, max_dist):
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

            if dist <= max_dist:
                if dist < 0.1: wgc.pop()
                merged_track = wgc + nwgc
                break
                
            # Check for reversed leader
            dist = lldist(*wgc[0], *nwgc[0])

            if dist <= max_dist:
                wgc.reverse()
                if dist < 0.1: wgc.pop()
                merged_track = wgc + nwgc
                break
                
            # Check for trailer
            dist = lldist(*wgc[0], *nwgc[-1])

            if dist <= max_dist:
                if dist < 0.1: nwgc.pop()
                merged_track = nwgc + wgc
                break

            # Check for reversed trailer
            dist = lldist(*wgc[-1], *nwgc[-1])

            if dist <= max_dist:
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

def round_floats(o, p=6):
    # https://stackoverflow.com/a/53798633
    if isinstance(o, float): return round(o, p)
    if isinstance(o, dict): return {k: round_floats(v, p) for k, v in o.items()}
    if isinstance(o, (list, tuple)): return [round_floats(x, p) for x in o]

    return o

def main(argv):
    ac = AppContext(argv)

    input_data = read_input_file(ac.in_file_name)

    new_tracks = []

    while True:
        track = extract_track(input_data, ac.join_tracks, \
            ac.join_max_dist, ac.verbose)

        if track is None:
            break

        if ac.epsilon is not None:
            douglas_peucker(track, ac.epsilon, ac.verbose)

        split_tracks = split_track(track, ac.max_points, ac.verbose)

        new_tracks += split_tracks

    add_tracks(input_data, new_tracks)

    if ac.out_file_name is None or ac.out_file_name == "-":
        fp = sys.stdout
    else:
        fp = open(ac.out_file_name, 'w')

    print(json.dumps(round_floats(input_data, ac.decimal_places), \
        indent=ac.indent_level), file=fp)

    fp.close()

if __name__ == "__main__":
    sys.exit(main(sys.argv))

