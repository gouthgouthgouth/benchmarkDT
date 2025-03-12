import json
import time

import requests

from configs.config import fiware_config_data, RAM_LIMIT, CPU_LIMIT
from scripts.sensor_measurements_simulator import create_measurement_ul
from scripts.utils import run_container, print_time, stop_container, start_container, get_road_segments_from_json


def fiware_initialize_containers():
    container_name = fiware_config_data["CONTAINER_NAME"]
    container_image = fiware_config_data["IMAGE_NAME"]
    run_container(container_name, container_image, RAM_LIMIT, CPU_LIMIT)
    run_container(
        container_name="mongo-db",
        image_name="mongo",
        ram_limit=RAM_LIMIT,
        cpu_limit=CPU_LIMIT,
        port_mapping="27017:27017",
        volume_mapping=f"{container_name}-data:/data/db"
    )

def fiware_start_cbroker():
    start_container(fiware_config_data["CONTAINER_NAME"])

def fiware_stop_and_clean_containers():
    container_name = fiware_config_data["CONTAINER_NAME"]
    stop_container(container_name)
    stop_container("mongo-db")

def add_road_segments(road_segments):
    url = fiware_config_data["CBROKER_ADDRESS"] + "ngsi-ld/v1/entities/"

    for segment in road_segments:
        try:
            headers = {"Content-Type": "application/ld+json"}
            response = requests.post(url, headers=headers, json=segment)

            if response.status_code == 201:
                print_time(f"Entité {segment['id']} créée avec succès.")
            else:
                print_time(f"Échec de la création de {segment['id']}: {response.status_code}, {response.text}")
        except Exception as e:
            print_time(f"Erreur lors de l'envoi de {segment['id']}: {e}")

def create_iot_service(apikey, entity_type, resource, fiware_service, fiware_servicepath):
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

    url = fiware_config_data["IOT_AGENT_ADDRESS"] + "iot/services"

    headers = {
        "Content-Type": "application/json",
        "fiware-service": fiware_service,
        "fiware-servicepath": fiware_servicepath
    }
    payload = {
        "services": [
            {
                "apikey": apikey,
                "cbroker": fiware_config_data["CBROKER_ADDRESS"],
                "entity_type": entity_type,
                "resource": resource
            }
        ]
    }

    try:
        print_time(f"Creating service {fiware_service}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print_time("Service created successfully.")
        return response
    except requests.exceptions.RequestException as e:
        print_time(f"Failed to create service: {e}")
        return None


def create_iot_device(id, entity_type, apikey, transport, attributes, static_attributes, fiware_service, fiware_servicepath, protocol="PDI-IoTA-UltraLight"):
    """
    Create an IoT device in the FIWARE IoT Agent.

    Parameters:
        id (int): The unique ID for the device.
        entity_type (str): The entity type for the device.
        apikey (str): The API key for the device.
        protocol (str): The communication protocol (e.g., PDI-IoTA-UltraLight).
        transport (str): The transport protocol (e.g., HTTP).
        attributes (list or None): A list of attributes with object_id, name, and type.
        static_attributes (list or None): A list of static attributes with name, type, and value.
        fiware_service (str): The FIWARE service (tenant).
        fiware_servicepath (str): The FIWARE service path.

    Returns:
        Response: The response object from the HTTP request.
    """

    url = fiware_config_data["IOT_AGENT_ADDRESS"] + "iot/devices"

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
                "protocol": protocol,
                "transport": transport
            }
        ]
    }

    if attributes is not None:
        payload["devices"][0]["attributes"] = attributes
    if static_attributes is not None:
        payload["devices"][0]["static_attributes"] = static_attributes

    try:
        print_time(f"Creating device {entity_type}{str(id)}...")
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        print_time(f"Device {entity_type}{str(id)} created successfully.")
        return response
    except requests.exceptions.RequestException as e:
        print_time(f"Failed to create device {entity_type}{str(id)} because of error : {e}")
        return None

def get_entity(entity_id, entity_type, fiware_service=fiware_config_data["fiware_service"], key_values_only=False):
    """
    Get an entity from the FIWARE Context Broker.

    Parameters:
        entity_id (str): The ID of the entity to retrieve.
        fiware_service (str, optional): The FIWARE service (tenant).

    Returns:
        Response: The response object from the HTTP request.
    """
    url = fiware_config_data["CBROKER_ADDRESS"] + f"ngsi-ld/v1/entities/urn:ngsi-ld:{entity_type}:{entity_id}"
    headers = {
        "NGSILD-Path": "/",
        'Accept': 'application/ld+json'
    }
    params = {}
    payload = {
        "attrs=truckTrafficFlow"
    }

    if key_values_only:
        params["options"] = "keyValues"

    if fiware_service:
        headers["NGSILD-Tenant"] = fiware_service

    try:
        response = requests.get(url, params=params, headers=headers, data=payload)
        response.raise_for_status()
        print("Entity retrieved successfully.")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve entity: {e}")
        return None

def create_traffic_flow_measurement(device_id, car_traffic_flow, truck_traffic_flow):
    """
    Send a measurement update to the IoT Agent.

    Parameters:
        device_id (str): The ID of the device sending the measurement (e.g., TrafficFlowSensor1).
        car_traffic_flow (int): Value for car traffic flow (e.g., 50).
        truck_traffic_flow (int): Value for truck traffic flow (e.g., 30).

    Returns:
        Response: The response object from the HTTP request.
    """
    url = fiware_config_data["IOT_AGENT_HTTP_ADDRESS"] + "iot/json"
    headers = {
        "Content-Type": "text/plain",
        "fiware-service": fiware_config_data["fiware_service"],
        "fiware-servicepath": fiware_config_data["fiware_servicepath"]
    }
    params = {
        "k": fiware_config_data["apikey"],
        "i": str(device_id)
    }
    payload = f"c|{car_traffic_flow}|t|{truck_traffic_flow}"

    try:
        response = requests.post(url, headers=headers, params=params, data=payload)
        response.raise_for_status()
        print("Measurement sent successfully.")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Failed to send measurement: {e}")
        return None

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