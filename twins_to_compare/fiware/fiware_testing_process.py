import time

from configs.config import fiware_config_data
from twins_to_compare.fiware.fiware_utils import add_road_segments, create_iot_service, create_iot_device, get_entity
from twins_to_compare.fiware.sensor_measurements_simulator import create_measurement
from utils.utils import get_road_segments_from_json, print_time

def create_road_segments_and_sensors(input_file_json, nb_required=100):

    road_segments = get_road_segments_from_json(input_file_json, number_required=nb_required)
    add_road_segments(road_segments)

    create_iot_service(apikey=fiware_config_data["apikey"],
                                  entity_type=fiware_config_data["sensor_entity_type"],
                                  resource=fiware_config_data["default_resource"],
                                  fiware_service=fiware_config_data["fiware_service"],
                                  fiware_servicepath=fiware_config_data["fiware_servicepath"])
    sensor_id_counter = 0
    for segment in road_segments:
        sensor_id_counter += 1
        static_attributes = [
            {
                "name": "location",
                "type": "geo:point",
                "value": str(segment["location"]["value"]["coordinates"][0][1]) + "," + str(segment["location"]["value"]["coordinates"][0][0])
            },
            {
                "name": "controlledAsset",
                "type": "Relationship",
                "value": segment["id"],
                "link": {
                    "attributes": ["carTrafficFlow", "truckTrafficFlow"],
                    "name": "providedBy",
                    "type": "RoadSegment"
                }
            }
        ]

        create_iot_device(id=sensor_id_counter,
                          entity_type=fiware_config_data["sensor_entity_type"],
                          apikey=fiware_config_data["apikey"],
                          transport=fiware_config_data["transport"],
                          attributes=fiware_config_data["trafficFlowSensor_attributes"],
                          static_attributes=static_attributes,
                          fiware_service=fiware_config_data["fiware_service"],
                          fiware_servicepath=fiware_config_data["fiware_servicepath"],
                          protocol="PDI-IoTA-UltraLight")


def create_measures_ultralight():
    t0 = time.time()
    for i in range(1, 45):
        device_id = fiware_config_data["sensor_entity_type"] + str(i)
        car_traffic_flow = 1
        truck_traffic_flow = 1
        create_measurement(device_id, car_traffic_flow, truck_traffic_flow)

    response = get_entity(entity_id="RoadSegment3", entity_type="RoadSegment")
    print_time(response.text)
    print_time("Temps total d'envoi des mesures : " + str(round(time.time() - t0, 2)) + "s")