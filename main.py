from twins_to_compare.fiware.fiware_testing_process import create_road_segments_and_sensors
from utils.utils import get_road_segments_from_json

input_file_json = "data/road_segments_from_csv.json"
road_segments = get_road_segments_from_json(input_file_json)

if __name__ == "__main__":
    create_road_segments_and_sensors(input_file_json, 200)
