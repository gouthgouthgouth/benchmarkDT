from twins_to_compare.eclipse_ditto.eclipse_utils import transform_jsonld_to_ditto, put_mqtt_connection, send_messages

input_file_json = "data/road_segments_from_csv.json"

def eclipse_run_tests(nb_entities, msg_frequency):
    # Création des things
    ditto_things = transform_jsonld_to_ditto(input_file_json, nb_entities)

    # Etablissement de la connection MQTT
    put_mqtt_connection()

    send_messages(ditto_things, msg_frequency)