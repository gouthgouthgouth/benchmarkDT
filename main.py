import pprint

from scripts.sensor_measurements_simulator import create_measurement_mqtt
from twins_to_compare.fiware.fiware_utils import create_road_segments_and_sensors
from twins_to_compare.eclipse_ditto.eclipse_utils import *
from scripts.utils import get_road_segments_from_json

input_file_json = "data/road_segments_from_csv.json"
road_segments_fiware = get_road_segments_from_json(input_file_json)

if __name__ == "__main__":

    # create_road_segments_and_sensors(input_file_json, 200)
    # ditto_things = transform_jsonld_to_ditto(input_file_json)

    # put_policy("my.namespace:RoadSegment")
    # for thing in ditto_things:
    #     put_thing(thing, policy="my.namespace:RoadSegment")
    # put_mqtt_connection()
    
    create_measurement_mqtt(car_traffic_flow=1, truck_traffic_flow=1, thing_id='my.namespace:RoadSegment1')
    # pprint.pprint(get_thing("my.namespace:RoadSegment1"))