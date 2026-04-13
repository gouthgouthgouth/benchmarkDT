import json
import time

import requests

from config.config import orion_config_data
from benchmark.utils import print_time
from brokers.fiware_utils import generate_compact_attributes

def add_road_segments(road_segments, fiware_service, fiware_servicepath, logs=False, tentative=3):
    url = orion_config_data["CBROKER_ADDRESS"] + "ngsi-ld/v1/entities/"

    for segment in road_segments:
        try:
            headers = {
                "Content-Type": "application/ld+json",
                "fiware-service": fiware_service,
                "fiware-servicepath": fiware_servicepath
            }
            response = requests.post(url, headers=headers, json=segment)

            if response.status_code == 201:
                if logs:
                    print_time(f"✔️ Entity {segment['id']} created successfully.")
            else:
                if logs:
                    print_time(f"✖️ Failed to create {segment['id']}: {response.status_code}, {response.text}")
                    if tentative > 0:
                        time.sleep(10)
                        return add_road_segments(road_segments, fiware_service, fiware_servicepath, logs=False, tentative=tentative-1)
                return False
        except Exception as e:
            if logs:
                print_time(f"✖️ Error sending {segment['id']}: {e}")
                if tentative > 0:
                    time.sleep(10)
                    return add_road_segments(road_segments, fiware_service, fiware_servicepath, logs=False,
                                             tentative=tentative - 1)
            return False
    return True

def create_iot_service(apikey, entity_type, resource, fiware_service, fiware_servicepath, logs=False, tentative=3):
    url = orion_config_data["IOT_AGENT_ADDRESS"] + "iot/services"

    headers = {
        "Content-Type": "application/json",
        "fiware-service": fiware_service,
        "fiware-servicepath": fiware_servicepath
    }
    payload = {
        "services": [
            {
                "apikey": apikey,
                "cbroker": orion_config_data["CBROKER_ADDRESS"],
                "entity_type": entity_type,
                "resource": resource
            }
        ]
    }

    try:
        if logs:
            print_time(f"ℹ️ Creating service {fiware_service}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        if logs:
            print_time("✔️ Service created successfully.")
        return response
    except requests.exceptions.RequestException as e:
        if logs:
            print_time(f"✖️ Failed to create service: {e}")
        if tentative > 0:
            print_time(f"ℹ️ Trying again...")
            return create_iot_service(apikey, entity_type, resource, fiware_service, fiware_servicepath, logs=False, tentative=tentative-1)
        return False


def create_iot_device(id, entity_type, apikey, transport, attributes, static_attributes,
                      fiware_service, fiware_servicepath, logs=False, tentative=3):
    url = orion_config_data["IOT_AGENT_ADDRESS"] + "iot/devices"

    headers = {
        "Content-Type": "application/json",
        "fiware-service": fiware_service,
        "fiware-servicepath": fiware_servicepath
    }
    payload = {
        "devices": [
            {
                "device_id": entity_type + str(id),
                "entity_name": entity_type + str(id),
                "entity_type": entity_type,
                "apikey": apikey,
                "transport": transport
            }
        ]
    }

    if attributes is not None:
        payload["devices"][0]["attributes"] = attributes
    if static_attributes is not None:
        payload["devices"][0]["static_attributes"] = static_attributes

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        if logs:
            print_time(f"✔️ Device {entity_type}{str(id)} created successfully.")
        return response
    except requests.exceptions.RequestException as e:
        if logs:
            print_time(f"✖️ Failed to create device {entity_type}{str(id)} due to error: {e}")
        if tentative > 0:
            print_time(f"ℹ️ Trying again...")
            return create_iot_device(id, entity_type, apikey, transport, attributes, static_attributes,
                      fiware_service, fiware_servicepath, logs=False, tentative=tentative - 1)
        return False


def orion_create_road_segments_and_sensors(road_segments, nb_attributes, logs=False):


    segments_created = add_road_segments(road_segments,
                      fiware_service=orion_config_data["fiware_service"],
                      fiware_servicepath=orion_config_data["fiware_servicepath"], logs=logs, tentative=3
                      )

    service_created = create_iot_service(apikey=orion_config_data["apikey"],
                       entity_type=orion_config_data["sensor_entity_type"],
                       resource=orion_config_data["default_resource"],
                       fiware_service=orion_config_data["fiware_service"],
                       fiware_servicepath=orion_config_data["fiware_servicepath"], logs=logs, tentative=3)

    sensor_id_counter = 0
    devices_created = 0
    if logs:
        print_time("ℹ️ Creating devices...")
    for segment in road_segments:
        sensor_id_counter += 1
        trafficFlowSensor_attributes = generate_compact_attributes(nb_attributes)
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
                    "attributes": [att["name"] for att in trafficFlowSensor_attributes],
                    "name": "providedBy",
                    "type": "RoadSegment"
                }
            }
        ]

        if create_iot_device(id=sensor_id_counter,
                          entity_type=orion_config_data["sensor_entity_type"],
                          apikey=orion_config_data["apikey"],
                          transport=orion_config_data["transport"],
                          attributes=trafficFlowSensor_attributes,
                          static_attributes=static_attributes,
                          fiware_service=orion_config_data["fiware_service"],
                          fiware_servicepath=orion_config_data["fiware_servicepath"], logs=logs):
            devices_created += 1

    if segments_created and service_created and devices_created == len(road_segments):
        return True
    return False
