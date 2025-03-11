import pprint

from twins_to_compare.fiware.fiware_utils import create_road_segments_and_sensors
from twins_to_compare.eclipse_ditto.eclipse_utils import *
from utils.utils import get_road_segments_from_json

input_file_json = "data/road_segments_from_csv.json"
road_segments_fiware = get_road_segments_from_json(input_file_json)

if __name__ == "__main__":
    # create_road_segments_and_sensors(input_file_json, 200)
    ditto_things = transform_jsonld_to_ditto(input_file_json)
    for thing_id in ditto_things:
        thing = ditto_things[thing_id]
        # post_thing(thing)
        # put_thing(thing, policy=None)
        # t = get_thing(thing_id=thing_id)
        put_policy(thing_id)
        # delete_policy(thing_id)
        # p = get_policy(thing_id)
        # pprint.pprint(t)
        # pprint.pprint(p)
        # if t != None:
        #     t = delete_thing(thing_id=thing_id, delete_policy_as_well=True)
        #     pprint.pprint(t)
        # update_feature(thing_id, feature_to_update, value)
