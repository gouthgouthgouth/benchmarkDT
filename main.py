import pprint

from twins_to_compare.fiware.fiware_utils import create_road_segments_and_sensors
from twins_to_compare.eclipse_ditto.eclipse_utils import *
from utils.utils import get_road_segments_from_json

input_file_json = "data/road_segments_from_csv.json"
road_segments_fiware = get_road_segments_from_json(input_file_json)

if __name__ == "__main__":
    # create_road_segments_and_sensors(input_file_json, 200)
    ditto_things = transform_jsonld_to_ditto(input_file_json)
    for key in ditto_things:
        thing = ditto_things[key]
        THING_ID = thing["thingId"]
        post_thing(thing)
        # t = get_thing(thing_id=THING_ID)
        # pprint.pprint(t)
