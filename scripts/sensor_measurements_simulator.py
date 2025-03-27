import time
from datetime import datetime, UTC, timezone

import numpy as np
import requests
import paho.mqtt.client as mqtt
import json

from configs.config import scorpio_config_data, MQTT_TOPIC, MQTT_PORT, MQTT_BROKER, eclipse_config_data
from scripts.utils import print_time

def create_measurement_http(device_id, car_traffic_flow, truck_traffic_flow):
    """
    Send a measurement update to the IoT Agent.

    Parameters:
        device_id (str): The ID of the device sending the measurement.
        car_traffic_flow (int): Value for car traffic flow (e.g., 50).
        truck_traffic_flow (int): Value for truck traffic flow (e.g., 30).

    Returns:
        Response: The response object from the HTTP request.
    """

    url = scorpio_config_data["IOT_AGENT_HTTP_ADDRESS"] + "iot/json"
    headers = {
        "Content-Type": "text/plain",
        "scorpio-service": scorpio_config_data["fiware_service"],
        "scorpio-servicepath": scorpio_config_data["fiware_servicepath"]
    }
    params = {
        "k": scorpio_config_data["apikey"],
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

def send_messages_uniformlaw(devices, dt_solution, msg_frequency_hz, nb_seconds, start_time):
    client = mqtt.Client()
    if dt_solution == "scorpio":
        device_ids = [device["id"].split(":")[-1] for device in devices]
        data = f"c|10|t|10"
        MQTT_BROKER = "localhost"
    elif dt_solution == "ditto":
        device_ids = [thing['thingId'].split(":")[-1] for thing in devices]
        payload = {
            "path": "/attributes/trafficFlow/value",
            "value": {
                "measuredAt": datetime.now(UTC).isoformat(),
                "carTrafficFlow": 10,
                "truckTrafficFlow": 10
            }
        }
        client.username_pw_set("devops", "foobar")
        MQTT_BROKER = "localhost"


    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    interval = 1 / (msg_frequency_hz)
    nb_messages = nb_seconds * msg_frequency_hz
    sent = 0
    i = 0
    sleep_time = (start_time - datetime.now(timezone.utc)).total_seconds()
    time.sleep(sleep_time)

    next_time = time.perf_counter()
    print_time("Sending messages...")

    try:
        while not sent >= nb_messages:
            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(UTC).isoformat()
                MQTT_TOPIC = f"my.namespace/{device_ids[i]}/things/twin/commands/modify"
                payload["topic"] = MQTT_TOPIC
                data = json.dumps(payload)
            elif dt_solution == "scorpio":
                MQTT_TOPIC = f"/ul/{scorpio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            client.publish(MQTT_TOPIC, data)

            # attendre précisément jusqu'au prochain envoi
            next_time += interval
            sleep_time = next_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            sent += 1
            if i < len(device_ids) - 1:
                i += 1
            else:
                i = 0

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

    print_time("All messages have been sent")

def send_messages_poissonlaw(devices, dt_solution, poisson_lambda, nb_seconds, start_time):
    client = mqtt.Client()
    if dt_solution == "scorpio":
        device_ids = [device["id"].split(":")[-1] for device in devices]
        data = f"c|10|t|10"
        MQTT_BROKER = "localhost"
    elif dt_solution == "ditto":
        device_ids = [thing['thingId'].split(":")[-1] for thing in devices]
        payload = {
            "path": "/attributes/trafficFlow/value",
            "value": {
                "measuredAt": datetime.now(UTC).isoformat(),
                "carTrafficFlow": 10,
                "truckTrafficFlow": 10
            }
        }
        client.username_pw_set("devops", "foobar")
        MQTT_BROKER = "localhost"

    sent = 0

    print_time("Sending messages with Poisson intervals...")
    t0 = time.time()
    i = 0

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    sleep_time = (start_time - datetime.now(timezone.utc)).total_seconds()
    time.sleep(sleep_time)

    try:
        while time.time() - t0 < nb_seconds:
            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(UTC).isoformat()
                MQTT_TOPIC = f"my.namespace/{device_ids[i]}/things/twin/commands/modify"
                payload["topic"] = MQTT_TOPIC
                data = json.dumps(payload)
            elif dt_solution == "scorpio":
                MQTT_TOPIC = f"/ul/{scorpio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            client.publish(MQTT_TOPIC, data)

            interval = np.random.exponential(1 / poisson_lambda)
            time.sleep(interval)
            if i < len(device_ids) - 1:
                i += 1
            else:
                i = 0
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

    print_time("All Poisson-distributed messages have been sent")

def send_messages_gaussianlaw(devices, dt_solution, nb_messages, nb_seconds, start_time, center_ratio=0.5, sigma_ratio=0.1):
    client = mqtt.Client()
    if dt_solution == "scorpio":
        device_ids = [device["id"].split(":")[-1] for device in devices]
        data = f"c|10|t|10"
        MQTT_BROKER = "localhost"
    elif dt_solution == "ditto":
        device_ids = [thing['thingId'].split(":")[-1] for thing in devices]
        payload = {
            "path": "/attributes/trafficFlow/value",
            "value": {
                "measuredAt": datetime.now(UTC).isoformat(),
                "carTrafficFlow": 10,
                "truckTrafficFlow": 10
            }
        }
        client.username_pw_set("devops", "foobar")
        MQTT_BROKER = "localhost"
    center_time = nb_seconds * center_ratio
    sigma = nb_seconds * sigma_ratio

    # Générer les instants d’envoi
    send_times = np.random.normal(loc=center_time, scale=sigma, size=nb_messages)
    send_times = send_times[(send_times >= 0) & (send_times <= nb_seconds)]  # Garder ceux dans la fenêtre
    send_times.sort()

    i = 0
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    sleep_time = (start_time - datetime.now(timezone.utc)).total_seconds()
    time.sleep(sleep_time)

    print_time("Sending messages with gaussian time distribution...")

    start_perf = time.perf_counter()
    try:
        for send_time_point in send_times:
            now_perf = time.perf_counter() - start_perf
            sleep_time = send_time_point - now_perf
            if sleep_time > 0:
                time.sleep(sleep_time)

            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(UTC).isoformat()
                MQTT_TOPIC = f"my.namespace/{device_ids[i]}/things/twin/commands/modify"
                payload["topic"] = MQTT_TOPIC
                data = json.dumps(payload)
            elif dt_solution == "scorpio":
                MQTT_TOPIC = f"/ul/{scorpio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            client.publish(MQTT_TOPIC, data)

            if i < len(device_ids) - 1:
                i += 1
            else:
                i = 0

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

    print_time("All gaussian-distributed messages have been sent")
    return start_time
