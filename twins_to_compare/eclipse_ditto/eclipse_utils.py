import json
import time
import requests
from configs.config import eclipse_config_data, RAM_LIMIT, CPU_LIMIT, MQTT_PORT, MQTT_TOPIC, MQTT_BROKER, CONNECTION_ID
from scripts.utils import print_time

def transform_jsonld_to_ditto(jsonld_file):
    with open(jsonld_file, "r", encoding="utf-8") as f:
        jsonld_data = json.load(f)

    ditto_things = {}

    for entity in jsonld_data:
        thing_id = f"{eclipse_config_data["NAMESPACE"]}:{entity["id"].split(":")[-1]}"
        thing = {
            "thingId": thing_id,
            "attributes": {
                "type": entity.get("type", "Unknown"),
                "location": entity.get("location", {}).get("value", {}),
                "elevations": entity.get("elevations", {}).get("value", []),
                "length": entity.get("length", {}).get("value", 0),
                "totalLaneNumber": entity.get("totalLaneNumber", {}).get("value", 0),
                "speedLimit": entity.get("speedLimit", {}).get("value", 0),
                "carTrafficFlow": 50,
                "truckTrafficFlow": 20
            }
        }

        ditto_things[thing_id] = thing

    return ditto_things

def post_thing(thing, namespace=eclipse_config_data["NAMESPACE"]):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/things"
    thing.pop("thingId")
    HEADERS = {
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8=",
        "Content-Type": "application/json"
    }
    params = {"namespace" : namespace}
    response = requests.post(url, headers=HEADERS, data=json.dumps(thing), params=params)
    if response.status_code in [200, 201]:
        print_time("Thing created successfully!")
    else:
        print_time(f"Error: {response.text}")

def put_thing(thing, policy=None):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/things/{thing["thingId"]}"
    HEADERS = {
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8=",
        "Content-Type": "application/json"
    }
    params = {"thingId" : thing["thingId"]}
    if policy is not None:
        thing["policyId"] = policy
    response = requests.put(url, headers=HEADERS, data=json.dumps(thing), params=params)
    if response.status_code in [200, 201]:
        print_time(f"Thing {thing["thingId"]} created successfully!")
    else:
        print_time(f"Error when creating thing {thing["thingId"]} : {response.text}.")

def get_thing(thing_id):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/things/{thing_id}"
    HEADERS = {
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8=",
        "Content-Type": "application/json"
    }
    params = {"thingId" : f"{thing_id}"}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print_time(f"Error: {response.text}")

#TODO
def update_feature(thing_id, feature_to_update, value):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/things/{thing_id}/features/{feature_to_update}/properties/value"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8="
    }
    data = json.dumps({"value": value})
    response = requests.put(url, headers=HEADERS, data=data)
    if response.status_code == 200:
        print_time(f"Feature updated successfully on thing of id {thing_id}")
    else:
        print_time(f"Error, couldn't update feature {feature_to_update} on thing {thing_id} : {response.text}")

def delete_thing(thing_id, delete_policy_as_well=False):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/things/{thing_id}"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8="
    }
    params = {"thingId" : f"{thing_id}"}
    response = requests.delete(url, headers=HEADERS, params=params)
    if response.status_code == 204:
        print_time(f"Thing of id {thing_id} deleted successfully!")
    else:
        print_time(f"Error, thing of id {thing_id} couldn't be deleted : {response.text}")
    if delete_policy_as_well:
        delete_policy(thing_id)

# TODO
def put_policy(policy_id):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/policies/{policy_id}"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8="
    }
    params = {"policyId" : f"{policy_id}"}
    policy_definition = {
        "policyId": f"{policy_id}",
        "entries": {
            "devops": {
                "subjects": {
                    "nginx:devops": {"type": "nginx-basic"}
                },
                "resources": {
                    "things:/": {"grant": ["READ", "WRITE", "CREATE"], "revoke": []},
                    "policy:/": {"grant": ["CREATE", "READ", "WRITE"], "revoke": []},
                    "policies:/": {"grant": ["CREATE", "READ", "WRITE"], "revoke": []}
                }
            }
        }
    }
    data = json.dumps(policy_definition)
    response = requests.put(url, headers=HEADERS, params=params, data=data)
    if response.status_code == 201:
        print_time(f"Policy of id {policy_id} created successfully!")
    else:
        print_time(f"Error, policy of id {policy_id} couldn't be created : {response.text}")

def get_policy(policy_id):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/policies/{policy_id}"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8="
    }
    params = {"policyId" : f"{policy_id}"}
    response = requests.get(url, headers=HEADERS, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print_time(f"Error: {response.text}")

def delete_policy(policy_id):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/policies/{policy_id}"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8="
    }
    params = {"policyId" : f"{policy_id}"}
    response = requests.delete(url, headers=HEADERS, params=params)
    if response.status_code == 204:
        print_time(f"Policy of id {policy_id} deleted successfully!")
    else:
        print_time(f"Error, policy of id {policy_id} couldn't be deleted : {response.text}")

def put_mqtt_connection():
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/connections/mqtt_connection"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization" : "Basic ZGV2b3BzOmZvb2Jhcg=="
    }
    mqtt_connection = {
        "connectionType": "mqtt",
        "connectionStatus": "open",
        "failoverEnabled": True,
        "uri": f"tcp://{MQTT_BROKER}:{MQTT_PORT}",  # ✅ Fix: Correctly using "uri" instead of "address"

        # === MQTT Source: Listening for Sensor Data ===
        "sources": [
            {
                "addresses": [
                    "traffic/road_segment/#"  # ✅ Subscribes to all road segments
                ],
                "authorizationContext": ["nginx:devops"],  # ✅ Uses correct auth context
                "qos": 1,  # ✅ At least once delivery
                "filters": []
            }
        ],

        # === MQTT Target: Sending Processed Data Back to MQTT Broker ===
        "targets": [
            {
                "address": "traffic/processed/{{ thing:id }}",
                "topics": [
                    "_/_/things/twin/events",
                    "_/_/things/live/messages"
                ],
                "authorizationContext": ["nginx:devops"],
                "qos": 1  # ✅ Ensure reliable message delivery
            }
        ],

        # === Specific MQTT Configuration ===
        "specificConfig": {
            "clientId": "ditto-mqtt-client",
            "cleanSession": True,
            "keepAlive": 60,
            "lastWillTopic": "traffic/last_will",
            "lastWillQos": 1,
            "lastWillRetain": False,
            "lastWillMessage": "Ditto MQTT connection lost"
        }
    }

    response = requests.put(url, headers=HEADERS, data=json.dumps(mqtt_connection))

    if response.status_code in [200, 201, 204]:
        print_time("✅ MQTT Connection configured successfully!")
    else:
        print_time(f"❌ Error configuring MQTT connection: {response.text}")