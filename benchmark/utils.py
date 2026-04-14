"""
Shared utility functions used across the benchmark and broker adapter modules.

Also provides the project-wide logging configuration. Call ``configure_logging``
once at application startup (in ``main.py`` or at the top of a standalone
analysis script) before any other module emits log messages.
"""
import json
import logging
from copy import deepcopy


_LOG_FORMAT = "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s"
_LOG_DATEFMT = "%Y-%m-%d %H:%M:%S"


def configure_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with the project's unified format.

    Sets up a single ``StreamHandler`` on the root logger so that every module
    logger propagates to the same output with a consistent timestamp, level,
    and message layout.  Safe to call multiple times; ``basicConfig`` is a
    no-op if the root logger already has handlers.

    Args:
        level (int): Minimum logging level (e.g. ``logging.DEBUG``). Defaults
            to ``logging.INFO``.
    """
    logging.basicConfig(
        level=level,
        format=_LOG_FORMAT,
        datefmt=_LOG_DATEFMT,
    )


def get_road_segments_from_json(input_file: str, number_required: int = None) -> list:
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
