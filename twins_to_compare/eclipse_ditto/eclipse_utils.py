import json
import time
from copy import deepcopy

import requests
from requests.auth import HTTPBasicAuth
from configs.config import eclipse_config_data
from scripts.utils import print_time

def eclipse_create_things(ditto_things, logs=False):
    policy_Id = "my.namespace:RoadSegment"
    policy_created = put_policy(policy_id=policy_Id, logs=logs, tentative=5)
    things_created = 0
    for thing in ditto_things:
        if put_thing(thing, policy_id=policy_Id, logs=logs):
            things_created += 1
    if things_created == len(ditto_things):
        print_time("✔️ Things created successfully!")
    mqtt_connection_established = put_mqtt_connection()
    time.sleep(1)
    if things_created == len(ditto_things) and policy_created and mqtt_connection_established:
        return True
    else:
        return False

def transform_jsonld_to_ditto(input_file, number_required=None):
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
    url = f"{eclipse_config_data['DITTO_BASE_URL']}/api/2/things/{thing['thingId']}"
    params = {"thingId" : thing["thingId"]}
    if policy_id is not None:
        thing["policyId"] = policy_id
    response = requests.put(url, data=json.dumps(thing), params=params, auth=HTTPBasicAuth('devops', 'foobar'))
    if response.status_code in [200, 201]:
        if logs:
            print_time(f"✔️ Thing {thing['thingId']} created successfully!")
        return True
    else:
        if logs:
            print_time(f"✖️ Error when creating thing {thing['thingId']} : {response.text}.")
        return False

def put_policy(policy_id, logs=False, tentative=5):
    url = f"{eclipse_config_data['DITTO_BASE_URL']}/api/2/policies/{policy_id}"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    params = {"policyId" : f"{policy_id}"}
    policy_definition = {
        "policyId": f"{policy_id}",
        "entries": {
            "DEFAULT": {
                "importable": "implicit",
                "subjects": {
                    "nginx:ditto": { "type": "generated" },
                    "nginx:devops": { "type": "generated" }
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
    response = requests.put(url, headers=HEADERS, params=params, data=data, auth=HTTPBasicAuth('devops', 'foobar'))
    if response.status_code == 201:
        print_time(f"✔️ Policy of id {policy_id} created successfully!")
        return True
    else:
        print_time(f"✖️ Error, policy of id {policy_id} couldn't be created : {response.text}")
        if tentative > 0:
            print_time(f"ℹ️ Trying again to publish policy in 60 seconds...")
            time.sleep(60)
            return put_policy(policy_id, logs=logs, tentative=tentative-1)
        return False

def put_mqtt_connection():
    url = f"{eclipse_config_data['DITTO_BASE_URL']}/api/2/connections/mqtt_connection"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization" : "Basic ZGV2b3BzOmZvb2Jhcg=="
    }
    mqtt_connection = {
        "name": "Mosquitto",
        "connectionType": "mqtt",
        "connectionStatus": "open",
        "failoverEnabled": True,
        "uri": "tcp://mosquitto:1883",  # ✅ Ensure broker is reachable
        "sources": [
            {
                "addresses": ["my.namespace/#"],  # ✅ Subscribe to correct topic
                "authorizationContext": ["nginx:devops"],
                "qos": 1
            }
        ]
    }

    response = requests.put(url, headers=HEADERS, data=json.dumps(mqtt_connection))

    if response.status_code in [200, 201, 204]:
        print_time("✔️ MQTT Connection configured successfully!")
        return True
    else:
        print_time(f"✖️ Error configuring MQTT connection: {response.text}")
        return False
