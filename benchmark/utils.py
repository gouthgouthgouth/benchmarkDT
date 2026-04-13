import json
import subprocess
import datetime
import sys
from copy import deepcopy


def print_time(text_to_print, end="\n"):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + ": " + text_to_print, end=end)

def get_road_segments_from_json(input_file, number_required=None):
    with open(input_file, "r") as file:
        road_segments = json.load(file)

    initial_number = len(road_segments)

    if number_required is not None:
        while number_required < len(road_segments):
            road_segments.pop()
        i = 1
        while number_required > len(road_segments):
            road_segment_to_add = deepcopy(road_segments[i - 1])
            road_segment_to_add["id"] = "urn:ngsi-ld:RoadSegment:RoadSegment" + str(initial_number + i)
            road_segments.append(road_segment_to_add)
            i += 1
    return road_segments
