import time
from fiware.main import fiware_initialize_containers, add_road_segments, fiware_start_orion

input_file_json = "data/road_segments_from_csv.json"

if __name__ == "__main__":
    # clean_environment()
    # fiware_start_orion()
    add_road_segments(input_file_json)
