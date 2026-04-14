"""
Eclipse Ditto broker adapter.

Provides functions to provision Ditto Things, a shared policy, and an MQTT
connection via the Ditto REST API, as well as a helper to convert NGSI-LD
road segment entities into the Ditto Thing format.
"""
import json
import logging
import time
from copy import deepcopy

import requests
from requests.auth import HTTPBasicAuth
from config.config import eclipse_config_data

logger = logging.getLogger(__name__)


def eclipse_create_things(ditto_things, logs=False):
    """Create a policy, provision all Things, and open the MQTT connection.

    Args:
        ditto_things (list[dict]): Thing descriptors as returned by
            ``transform_jsonld_to_ditto``.
        logs (bool): If True, log each successful Thing creation.

    Returns:
        bool: True if the policy, all Things, and the MQTT connection were
            created successfully; False otherwise.
    """
    policy_id = "my.namespace:RoadSegment"
    policy_created = put_policy(policy_id=policy_id, logs=logs, tentative=5)

    things_created = 0
    for thing in ditto_things:
        if put_thing(thing, policy_id=policy_id, logs=logs):
            things_created += 1
    if things_created == len(ditto_things):
        logger.info("Things created successfully.")

    mqtt_connection_established = put_mqtt_connection()
    time.sleep(1)

    return things_created == len(ditto_things) and policy_created and mqtt_connection_established


def transform_jsonld_to_ditto(input_file, number_required=None):
    """Convert NGSI-LD road segment entities to the Ditto Thing format.

    Reads the JSON-LD file, maps each entity to a Ditto Thing dict, and
    adjusts the list length to ``number_required`` using the same
    shrink/clone strategy as ``get_road_segments_from_json``.

    Args:
        input_file (str): Path to the JSON-LD file containing road segment entities.
        number_required (int, optional): Desired number of Things. If None, all
            entities in the file are converted.

    Returns:
        list[dict]: List of Ditto Thing dicts, each with ``thingId`` and ``attributes``.
    """
    with open(input_file, "r", encoding="utf-8") as f:
        jsonld_data = json.load(f)

    ditto_things = []
    for entity in jsonld_data:
        thing_id = f"{eclipse_config_data['NAMESPACE']}:{entity['id'].split(':')[-1]}"
        thing = {
            "thingId": thing_id,
            "attributes": {
                "type": entity.get("type", "Unknown"),
                "location": entity.get("location", {}).get("value", {}),
                "elevations": entity.get("elevations", {}).get("value", []),
                "length": entity.get("length", {}).get("value", 0),
                "totalLaneNumber": entity.get("totalLaneNumber", {}).get("value", 0),
                "speedLimit": entity.get("speedLimit", {}).get("value", 0),
            }
        }
        ditto_things.append(thing)

    initial_number = len(ditto_things)

    if number_required is not None:
        while number_required < len(ditto_things):
            ditto_things.pop()
        i = 1
        while number_required > len(ditto_things):
            road_segment_to_add = deepcopy(ditto_things[i - 1])
            road_segment_to_add["thingId"] = f"{eclipse_config_data['NAMESPACE']}:{road_segment_to_add['attributes']['type']}{initial_number + i}"
            ditto_things.append(road_segment_to_add)
            i += 1

    return ditto_things


def put_thing(thing, policy_id=None, logs=False):
    """Create or update a single Ditto Thing via HTTP PUT.

    Args:
        thing (dict): Thing descriptor with at least a ``thingId`` key.
        policy_id (str, optional): Policy to attach to the Thing.
        logs (bool): If True, log the outcome.

    Returns:
        bool: True if the server returned 200 or 201; False otherwise.
    """
    url = f"{eclipse_config_data['DITTO_BASE_URL']}/api/2/things/{thing['thingId']}"
    params = {"thingId": thing["thingId"]}
    if policy_id is not None:
        thing["policyId"] = policy_id
    response = requests.put(url, data=json.dumps(thing), params=params, auth=HTTPBasicAuth('devops', 'foobar'))
    if response.status_code in [200, 201]:
        if logs:
            logger.debug("Thing %s created successfully.", thing['thingId'])
        return True
    else:
        if logs:
            logger.error("Failed to create thing %s: %s", thing['thingId'], response.text)
        return False


def put_policy(policy_id, logs=False, tentative=5):
    """Create or update a Ditto policy granting full READ/WRITE access.

    Retries up to ``tentative`` times with a 60-second delay between attempts
    to handle slow Ditto startup.

    Args:
        policy_id (str): Full policy ID in the form ``<namespace>:<name>``.
        logs (bool): Unused; kept for API consistency.
        tentative (int): Maximum number of attempts.

    Returns:
        bool: True if the policy was created (HTTP 201); False if all attempts failed.
    """
    url = f"{eclipse_config_data['DITTO_BASE_URL']}/api/2/policies/{policy_id}"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    params = {"policyId": f"{policy_id}"}
    policy_definition = {
        "policyId": f"{policy_id}",
        "entries": {
            "DEFAULT": {
                "importable": "implicit",
                "subjects": {
                    "nginx:ditto": {"type": "generated"},
                    "nginx:devops": {"type": "generated"}
                },
                "resources": {
                    "thing:/": {"grant": ["READ", "WRITE", "CREATE"], "revoke": []},
                    "policy:/": {"grant": ["CREATE", "READ", "WRITE"], "revoke": []},
                    "message:/": {"grant": ["CREATE", "READ", "WRITE"], "revoke": []}
                }
            }
        }
    }
    data = json.dumps(policy_definition)
    response = requests.put(url, headers=headers, params=params, data=data, auth=HTTPBasicAuth('devops', 'foobar'))
    if response.status_code == 201:
        logger.info("Policy %s created successfully.", policy_id)
        return True
    else:
        logger.error("Failed to create policy %s: %s", policy_id, response.text)
        if tentative > 0:
            logger.warning("Retrying policy creation in 60 seconds...")
            time.sleep(60)
            return put_policy(policy_id, logs=logs, tentative=tentative - 1)
        return False


def put_mqtt_connection():
    """Register the Mosquitto MQTT connection in Ditto via HTTP PUT.

    The connection subscribes to all topics under the configured namespace so
    that Ditto can process incoming twin-modify commands from the simulator.

    Returns:
        bool: True if Ditto accepted the connection (200, 201, or 204); False otherwise.
    """
    url = f"{eclipse_config_data['DITTO_BASE_URL']}/api/2/connections/mqtt_connection"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": "Basic ZGV2b3BzOmZvb2Jhcg=="
    }
    mqtt_connection = {
        "name": "Mosquitto",
        "connectionType": "mqtt",
        "connectionStatus": "open",
        "failoverEnabled": True,
        "uri": "tcp://mosquitto:1883",
        "sources": [
            {
                "addresses": ["my.namespace/#"],
                "authorizationContext": ["nginx:devops"],
                "qos": 1
            }
        ]
    }

    response = requests.put(url, headers=headers, data=json.dumps(mqtt_connection))

    if response.status_code in [200, 201, 204]:
        logger.info("MQTT connection configured successfully.")
        return True
    else:
        logger.error("Failed to configure MQTT connection: %s", response.text)
        return False
