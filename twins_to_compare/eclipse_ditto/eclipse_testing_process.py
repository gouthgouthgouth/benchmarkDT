from twins_to_compare.eclipse_ditto.eclipse_utils import transform_jsonld_to_ditto, put_mqtt_connection, send_messages, \
    put_policy, put_thing
from scripts.sensor_measurements_simulator import send_messages

input_file_json = "data/road_segments_from_csv.json"

def eclipse_run_tests(nb_entities, msg_frequency):
    # Création des things
    ditto_things = transform_jsonld_to_ditto(input_file_json, nb_entities)
    put_policy("my.namespace:RoadSegment")
    for thing in ditto_things:
        put_thing(thing, policy="my.namespace:RoadSegment")
    put_mqtt_connection()

    send_messages(ditto_things, msg_frequency)

eclipse_run_tests(nb_entities=500, msg_frequency=1)