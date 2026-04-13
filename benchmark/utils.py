"""
Shared utility functions used across the benchmark and broker adapter modules.
"""
import json
import subprocess
import datetime
import sys
from copy import deepcopy


def print_time(text_to_print, end="\n"):
    """Print a message prefixed with the current timestamp (millisecond precision).

    Args:
        text_to_print (str): The message to display.
        end (str): Line terminator passed to print(). Defaults to newline.
    """
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + ": " + text_to_print, end=end)


def get_road_segments_from_json(input_file, number_required=None):
    """Load road segment entities from a JSON file and adjust the list size.

    If ``number_required`` is smaller than the number of entities in the file,
    the list is truncated. If it is larger, existing segments are deep-copied
    and assigned new sequential IDs until the target count is reached.

    Args:
        input_file (str): Path to the JSON file containing NGSI-LD road segment entities.
        number_required (int, optional): Desired number of entities. If None, all
            entities in the file are returned.

    Returns:
        list[dict]: List of road segment entity dictionaries.
    """
    with open(input_file, "r") as file:
        road_segments = json.load(file)

    initial_number = len(road_segments)

    if number_required is not None:
        # Shrink: drop entities from the end until we reach the target count.
        while number_required < len(road_segments):
            road_segments.pop()

        # Grow: clone existing segments with new IDs to reach the target count.
        i = 1
        while number_required > len(road_segments):
            road_segment_to_add = deepcopy(road_segments[i - 1])
            road_segment_to_add["id"] = "urn:ngsi-ld:RoadSegment:RoadSegment" + str(initial_number + i)
            road_segments.append(road_segment_to_add)
            i += 1

    return road_segments
