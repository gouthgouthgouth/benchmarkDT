import json
import requests

from configs.config import *
from utils.utils import run_container, print_time, check_containers, run_command, stop_container, \
    start_container, check_images

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