from twins_to_compare.fiware.fiware_utils import create_road_segments_and_sensors

input_file_json = "data/road_segments_from_csv.json"

def fiware_run_tests(nb_entities, msg_frequency):
    create_road_segments_and_sensors(input_file_json, nb_entities)
