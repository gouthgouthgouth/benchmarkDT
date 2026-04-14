"""
Scorpio NGSI-LD broker adapter.

Provisions road segment entities and FIWARE IoT Agent services/devices required
by the benchmark. Unlike the Orion-LD adapter, HTTP requests here are
fire-and-forget with no built-in retry logic.
"""
import json
import logging
import time

import requests

from config.config import scorpio_config_data
from brokers.fiware_utils import generate_compact_attributes

logger = logging.getLogger(__name__)


def add_road_segments(road_segments, fiware_service, fiware_servicepath, logs=False):
    """POST each road segment entity to the Scorpio NGSI-LD context broker.

    Args:
        road_segments (list[dict]): NGSI-LD entity dicts to create.
        fiware_service (str): FIWARE tenant header value.
        fiware_servicepath (str): FIWARE service path header value.
        logs (bool): If True, print the outcome of each request.

    Returns:
        bool: True if every entity was created (HTTP 201); False otherwise.
    """
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
                    logger.debug("Entity %s created successfully.", segment['id'])
            else:
                if logs:
                    logger.error("Failed to create entity %s: %s %s", segment['id'], response.status_code, response.text)
        except Exception as e:
            logger.error("Error sending entity %s: %s", segment['id'], e)

    return segments_created == len(road_segments)


def create_iot_service(apikey, entity_type, resource, fiware_service, fiware_servicepath, logs=False):
    """Register an IoT Agent service group for MQTT-to-NGSI-LD message translation.

    Args:
        apikey (str): API key that devices will include in their MQTT topics.
        entity_type (str): Default NGSI-LD entity type for devices in this group.
        resource (str): IoT Agent resource path (e.g. ``/iot/json``).
        fiware_service (str): FIWARE tenant header value.
        fiware_servicepath (str): FIWARE service path header value.
        logs (bool): If True, print the outcome of the request.

    Returns:
        requests.Response | bool: Response object on success; False on failure.
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
        logger.info("Creating IoT service %s...", fiware_service)
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        if logs:
            logger.info("IoT service created successfully.")
        return response
    except requests.exceptions.RequestException as e:
        logger.error("Failed to create IoT service: %s", e)
        return False


def create_iot_device(id, entity_type, apikey, transport, attributes, static_attributes,
                      fiware_service, fiware_servicepath, logs=False):
    """Register a single IoT device in the FIWARE IoT Agent.

    Args:
        id (int): Numeric suffix appended to ``entity_type`` to form the device ID
            (e.g. ``entity_type=TrafficFlowSensor``, ``id=3`` → ``TrafficFlowSensor3``).
        entity_type (str): NGSI-LD entity type for the device.
        apikey (str): API key associated with the device's service group.
        transport (str): Transport protocol (``"MQTT"``).
        attributes (list[dict] | None): Dynamic attribute mappings
            (``object_id``, ``name``, ``type``).
        static_attributes (list[dict] | None): Static attribute values
            (``name``, ``type``, ``value``).
        fiware_service (str): FIWARE tenant header value.
        fiware_servicepath (str): FIWARE service path header value.
        logs (bool): If True, print the outcome of the request.

    Returns:
        requests.Response | bool: Response object on success; False on failure.
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
            logger.debug("Creating device %s%s...", entity_type, id)
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()
        if logs:
            logger.debug("Device %s%s created successfully.", entity_type, id)
        return response
    except requests.exceptions.RequestException as e:
        if logs:
            logger.error("Failed to create device %s%s: %s", entity_type, id, e)
        return False


def scorpio_create_road_segments_and_sensors(road_segments, nb_attributes, logs=False):
    """Provision the full set of Scorpio entities required for one benchmark run.

    Creates all road segment entities, registers one IoT service group, then
    provisions one sensor device per road segment, each with ``nb_attributes``
    dynamic attributes and two static attributes (location and controlledAsset).

    Args:
        road_segments (list[dict]): NGSI-LD road segment entity dicts.
        nb_attributes (int): Number of dynamic attributes to provision per sensor.
        logs (bool): If True, enable verbose logging throughout.

    Returns:
        bool: True if segments, service, and all devices were created successfully.
    """
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
        logger.info("Creating IoT devices...")

    for segment in road_segments:
        sensor_id_counter += 1
        trafficFlowSensor_attributes = generate_compact_attributes(nb_attributes)

        # Static attributes link the sensor back to its parent road segment.
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

    return segments_created and service_created and devices_created == len(road_segments)
