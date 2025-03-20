from scripts.sensor_measurements_simulator import send_messages
from twins_to_compare.eclipse_ditto.eclipse_utils import *
from scripts.utils import get_road_segments_from_json

input_file_json = "data/road_segments_from_csv.json"
road_segments_fiware = get_road_segments_from_json(input_file_json)



input_file_json = "data/road_segments_from_csv.json"

def eclipse_run_tests(nb_entities=500, msg_frequency=1, nb_messages=10000, create_things=True):
    ditto_things = transform_jsonld_to_ditto(input_file_json, nb_entities)

    if create_things:
        # Création des things
        ditto_things = transform_jsonld_to_ditto(input_file_json, nb_entities)
        put_policy("my.namespace:RoadSegment")
        for thing in ditto_things:
            put_thing(thing, policy="my.namespace:RoadSegment")
        put_mqtt_connection()

    # Envoi des messages
    send_messages(ditto_things, msg_frequency, nb_messages=10000)

if __name__ == "__main__":
    eclipse_run_tests(nb_entities=1000, msg_frequency=1, nb_messages=10000, create_things=False)