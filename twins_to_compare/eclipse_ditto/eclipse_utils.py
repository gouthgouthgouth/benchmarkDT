import json
import time
import requests
from configs.config import eclipse_config_data, RAM_LIMIT, CPU_LIMIT
from utils.utils import print_time

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
                "speedLimit": entity.get("speedLimit", {}).get("value", 0)
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

def put_thing(thing, namespace=eclipse_config_data["NAMESPACE"]):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/things/{thing["thingId"]}"
    HEADERS = {
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8=",
        "Content-Type": "application/json"
    }
    params = {"thingId" : thing["thingId"]}
    response = requests.put(url, headers=HEADERS, data=json.dumps(thing), params=params)
    if response.status_code in [200, 201]:
        print_time(f"Thing {thing["thingId"]} created successfully!")
    else:
        print_time(f"Error when creating thing {thing["thingId"]} : {response.text}")

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

#TODO
def delete_thing(thing_id):
    url = f"{eclipse_config_data["DITTO_BASE_URL"]}/api/2/things/{thing_id}"
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization" : "Basic ZGl0dG86ZGl0dG8="
    }
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 200:
        print_time(f"Thing of id {thing_id} deleted successfully!")
    else:
        print_time(f"Error, thing of id {thing_id} couldn't be deleted : {response.text}")