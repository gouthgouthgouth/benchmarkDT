import time
from datetime import datetime, UTC

import requests
import paho.mqtt.client as mqtt
import json

from configs.config import fiware_config_data, MQTT_TOPIC, MQTT_PORT, MQTT_BROKER, eclipse_config_data
from scripts.utils import print_time


def create_measurement_ul(device_id, car_traffic_flow, truck_traffic_flow):
    """
    Send a measurement update to the IoT Agent.

    Parameters:
        device_id (str): The ID of the device sending the measurement.
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
        print_time("Measurement sent successfully.")
        return response
    except requests.exceptions.RequestException as e:
        print_time(f"Failed to send measurement: {e}")
        return None

def create_measurement_mqtt(car_traffic_flow, truck_traffic_flow, thing_id):
    MQTT_TOPIC = f"{eclipse_config_data["NAMESPACE"]}/{thing_id.split(":")[-1]}/things/twin/commands/modify"
    sensor_data = {
        "topic": MQTT_TOPIC,
        "path": "/attributes/trafficFlow/value",
        "value": {
            "measuredAt": datetime.now(UTC).isoformat(),
            "carTrafficFlow": car_traffic_flow,
            "truckTrafficFlow": truck_traffic_flow
        }
    }
    client = mqtt.Client()
    client.username_pw_set("devops", "foobar")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    payload = json.dumps(sensor_data)
    client.publish(MQTT_TOPIC, payload)
    print_time(f"📡 Sent: {payload}")
    client.disconnect()

def send_messages(ditto_things, msg_frequency_hz, nb_messages=10000):
    data = {
        "path": "/attributes/trafficFlow/value",
        "value": {
            "measuredAt": datetime.now(UTC).isoformat(),
            "carTrafficFlow": 10,
            "truckTrafficFlow": 10
        }
    }
    next_time = time.perf_counter()
    interval = 1 / (msg_frequency_hz * len(ditto_things))


    client = mqtt.Client()
    client.username_pw_set("devops", "foobar")
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    sent = 0

    try:
        while not sent == nb_messages:
            for thing_id in [thing['thingId'] for thing in ditto_things]:
                data["value"]["measuredAt"] = datetime.now(UTC).isoformat()
                MQTT_TOPIC = f"my.namespace/{thing_id.split(':')[-1]}/things/twin/commands/modify"
                data["topic"] = MQTT_TOPIC
                payload = json.dumps(data)
                client.publish(MQTT_TOPIC, payload)

                # attendre précisément jusqu'au prochain envoi
                next_time += interval
                sleep_time = next_time - time.perf_counter()
                if sleep_time > 0:
                    # print(round(sleep_time/interval, 2))
                    time.sleep(sleep_time)

                sent += 1

                if sent == nb_messages:
                    break
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

    print_time("All messages have been sent")
    return 0