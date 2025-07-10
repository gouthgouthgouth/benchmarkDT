import json
import requests

from configs.config import stellio_config_data
from scripts.utils import print_time

def stellio_delete_road_segments_and_sensors(entities):
    pass


def add_road_segments(road_segments):
    url = stellio_config_data["CBROKER_ADDRESS"] + "ngsi-ld/v1/entities/"

    for segment in road_segments:

        segment["carTrafficFlow"] = {
            "value": 999,
            "type": "Property",
            "providedBy": {
                "type": "Relationship",
                "object": "urn:ngsi-ld:TrafficFlowSensor:TrafficFlowSensor2"
            }
        },
        segment["truckTrafficFlow"] = {
            "value": 999,
            "type": "Property",
            "providedBy": {
                "type": "Relationship",
                "object": "urn:ngsi-ld:TrafficFlowSensor:TrafficFlowSensor2"
            }
        }

        try:
            headers = {"Content-Type": "application/ld+json"}
            response = requests.post(url, headers=headers, json=segment)

            if response.status_code == 201:
                print_time(f"Entity {segment['id']} created successfully.")
            else:
                print_time(f"Failed to create {segment['id']}: {response.status_code}, {response.text}")
        except Exception as e:
            print_time(f"Error sending {segment['id']}: {e}")


def create_iot_service(apikey, entity_type, resource, fiware_service, fiware_servicepath):
    url = stellio_config_data["IOT_AGENT_ADDRESS"] + "iot/services"

    headers = {
        "Content-Type": "application/json",
        "fiware-service": fiware_service,
        "fiware-servicepath": fiware_servicepath
    }
    payload = {
        "services": [
            {
                "apikey": apikey,
                "cbroker": stellio_config_data["CBROKER_ADDRESS"],
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


def create_iot_device(id, entity_type, apikey, transport, attributes, static_attributes,
                      fiware_service, fiware_servicepath, protocol="PDI-IoTA-UltraLight"):
    url = stellio_config_data["IOT_AGENT_ADDRESS"] + "iot/devices"

    headers = {
        "Content-Type": "application/json",
        # "NGSILD-Tenant": fiware_service,
        "fiware-service": fiware_service,
        "fiware-servicepath": fiware_servicepath
    }
    payload = {
        "devices": [
            {
                "device_id": "urn:ngsi-ld:" + entity_type + str(id),
                "entity_name": entity_type + str(id),
                "entity_type": entity_type,
                "apikey": apikey,
                "protocol": protocol,
                "transport": transport,
                "lazy": [{"object_id": "a", "name": "test", "type": "Property"}]
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
        print_time(f"Failed to create device {entity_type}{str(id)} due to error: {e}")
        return None


def stellio_create_road_segments_and_sensors(road_segments):
    add_road_segments(road_segments)

    create_iot_service(apikey=stellio_config_data["apikey"],
                       entity_type=stellio_config_data["sensor_entity_type"],
                       resource=stellio_config_data["default_resource"],
                       fiware_service=stellio_config_data["fiware_service"],
                       fiware_servicepath=stellio_config_data["fiware_servicepath"])

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
                          entity_type=stellio_config_data["sensor_entity_type"],
                          apikey=stellio_config_data["apikey"],
                          transport=stellio_config_data["transport"],
                          attributes=stellio_config_data["trafficFlowSensor_attributes"],
                          static_attributes=static_attributes,
                          fiware_service=stellio_config_data["fiware_service"],
                          fiware_servicepath=stellio_config_data["fiware_servicepath"],
                          protocol="PDI-IoTA-UltraLight")


def stellio_subscribe_notifications():
    subscription = {
        "type": "Subscription",
        "entities": [{"type": "RoadSegment"}],
        "notification": {
            "endpoint": {
                "uri": "http://localhost:3000/notify",
                "accept": "application/ld+json"
            }
        }
    }

    headers = {
        "Content-Type": "application/ld+json"
    }

    response = requests.post(
        "http://localhost:8080/ngsi-ld/v1/subscriptions",
        headers=headers,
        data=json.dumps(subscription)
    )
    return response.status_code, response.text