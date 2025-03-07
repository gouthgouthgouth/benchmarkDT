import json

def transform_jsonld_to_ditto(jsonld_file):
    with open(jsonld_file, "r", encoding="utf-8") as f:
        jsonld_data = json.load(f)

    ditto_things = {}

    for entity in jsonld_data:
        thing_id = entity["id"].replace("urn:ngsi-ld:", "")
        thing = {
            "thingId": f"namespace:{thing_id}",
            "policyId": "namespace:policy",
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
