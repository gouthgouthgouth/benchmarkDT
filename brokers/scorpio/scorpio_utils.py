import json
import time

import requests
import string
from itertools import product, islice

from config.config import scorpio_config_data
from benchmark.utils import print_time

def generate_compact_attributes(n):
    alphabet = string.ascii_lowercase
    ids = map(lambda t: ''.join(t), islice(product(alphabet, repeat=1), n)) if n <= 26 else \
        map(lambda t: ''.join(t), islice(product(alphabet, repeat=2), n))

    return [
        {
            "object_id": id_,
            "name": f"attribute_{id_}",
            "type": "String"
        }
        for id_ in ids
    ]

def add_road_segments(road_segments, fiware_service, fiware_servicepath, logs=False):
    url = scorpio_config_data["CBROKER_ADDRESS"] + "ngsi-ld/v1/entities/"

    segments_created = 0
    for segment in road_segments:
        try:
            headers = {
                "Content-Type": "application/ld+json",
                "fiware-service": fiware_service,
                "fiware-servicepath": fiware_servicepath
            }
            response = requests.post(url, headers=headers, json=segment)

            if response.status_code == 201:
                segments_created += 1
                if logs:
                    print_time(f"✔️ Entité {segment['id']} créée avec succès.")
            else:
                if logs:
                    print_time(f"✖️ Échec de la création de {segment['id']}: {response.status_code}, {response.text}")
        except Exception as e:
            print_time(f"✖️ Erreur lors de l'envoi de {segment['id']}: {e}")

    if segments_created == len(road_segments):
        return True
    else:
        return False

def create_iot_service(apikey, entity_type, resource, fiware_service, fiware_servicepath, logs=False):
    """
    Create an IoT service in the FIWARE IoT Agent.

    Parameters:
        apikey (str): The API key for the service.
        entity_type (str): The default entity type for the service.
        resource (str): The resource path for devices.
        fiware_service (str): The FIWARE service (tenant).
        fiware_servicepath (str): The FIWARE service path.

    Returns:
        Response: The response object from the HTTP request.
    """

    url = scorpio_config_data["IOT_AGENT_ADDRESS"] + "iot/services"

    headers = {
        "Content-Type": "application/json",
        "fiware-service": fiware_service,
        "fiware-servicepath": fiware_servicepath
    }
    payload = {
        "services": [
            {
                "apikey": apikey,
                "cbroker": scorpio_config_data["CBROKER_ADDRESS"],
                "entity_type": entity_type,
                "resource": resource
            }
        ]
    }

    try:
        print_time(f"ℹ️ Creating service {fiware_service}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        if logs:
            print_time("✔️ Service created successfully.")
        return response
    except requests.exceptions.RequestException as e:
        print_time(f"✖️ Failed to create service: {e}")
        return False


def create_iot_device(id, entity_type, apikey, transport, attributes, static_attributes,
                      fiware_service, fiware_servicepath, logs=False):
    """
    Create an IoT device in the FIWARE IoT Agent.

    Parameters:
        id (int): The unique ID for the device.
        entity_type (str): The entity type for the device.
        apikey (str): The API key for the device.
        transport (str): The transport protocol (e.g., HTTP).
        attributes (list or None): A list of attributes with object_id, name, and type.
        static_attributes (list or None): A list of static attributes with name, type, and value.
        fiware_service (str): The FIWARE service (tenant).
        fiware_servicepath (str): The FIWARE service path.

    Returns:
        Response: The response object from the HTTP request.
    """

    url = scorpio_config_data["IOT_AGENT_ADDRESS"] + "iot/devices"

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
        if logs:
            print_time(f"ℹ️ Creating device {entity_type}{str(id)}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        if logs:
            print_time(f"✔️ Device {entity_type}{str(id)} created successfully.")
        return response
    except requests.exceptions.RequestException as e:
        if logs:
            print_time(f"✖️ Failed to create device {entity_type}{str(id)} because of error : {e}")
        return False

def scorpio_create_road_segments_and_sensors(road_segments, nb_attributes, logs=False):
    segments_created = add_road_segments(road_segments,
                      fiware_service=scorpio_config_data["fiware_service"],
                      fiware_servicepath=scorpio_config_data["fiware_servicepath"],
                      logs=logs
                      )

    service_created = create_iot_service(apikey=scorpio_config_data["apikey"],
                                  entity_type=scorpio_config_data["sensor_entity_type"],
                                  resource=scorpio_config_data["default_resource"],
                                  fiware_service=scorpio_config_data["fiware_service"],
                                  fiware_servicepath=scorpio_config_data["fiware_servicepath"],
                                  logs=logs)
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
                          entity_type=scorpio_config_data["sensor_entity_type"],
                          apikey=scorpio_config_data["apikey"],
                          transport=scorpio_config_data["transport"],
                          attributes=trafficFlowSensor_attributes,
                          static_attributes=static_attributes,
                          fiware_service=scorpio_config_data["fiware_service"],
                          fiware_servicepath=scorpio_config_data["fiware_servicepath"],
                          logs=logs):
            devices_created += 1

    if segments_created and service_created and devices_created == len(road_segments):
        return True
    return False
