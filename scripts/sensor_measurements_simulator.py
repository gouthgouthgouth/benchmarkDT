import random
import time
from datetime import datetime, timezone, timedelta
import string
from itertools import product, islice

import numpy as np
import requests
import paho.mqtt.client as mqtt
import json

from configs.config import scorpio_config_data, MQTT_PORT, orion_config_data, stellio_config_data
from scripts.utils import print_time

tz = timezone(timedelta(hours=2))

def gen_ids(n):
    alphabet = string.ascii_lowercase
    result = []
    length = 1
    while len(result) < n:
        remaining = n - len(result)
        result.extend(
            map(lambda t: ''.join(t),
                islice(product(alphabet, repeat=length), remaining))
        )
        length += 1
    return result

def generate_payload(dt_solution, nb_attributes, bytes_per_attr=10, tz=tz):

    attr_ids = gen_ids(nb_attributes)
    letters = "abcdefghij"

    def random_str(length):
        return ''.join(random.choices(letters, k=length))

    if dt_solution in {"orion_ld", "scorpio", "stellio"}:
        payload = {id_: random_str(bytes_per_attr) for id_ in attr_ids}
        return payload

    elif dt_solution == "ditto":
        value = {}
        if tz:
            value["measuredAt"] = datetime.now(tz=tz).isoformat()
        for id_ in attr_ids:
            value[id_] = random_str(bytes_per_attr)
        return {
            "path": "/attributes/trafficFlow/value",
            "value": value
        }
    else:
        raise ValueError(f"Unsupported dt_solution: {dt_solution}")

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
        "fiware-service": scorpio_config_data["fiware_service"],
        "fiware-servicepath": scorpio_config_data["fiware_servicepath"]
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

def send_messages_uniformlaw(devices, dt_solution, msg_frequency_hz, nb_seconds, start_time, nb_attributes, bytes_per_attribute):
    client = mqtt.Client()
    if dt_solution == "scorpio" or dt_solution == "orion_ld" or dt_solution == "stellio":
        device_ids = [device["id"].split(":")[-1] for device in devices]
    elif dt_solution == "ditto":
        device_ids = [thing['thingId'].split(":")[-1] for thing in devices]
        client.username_pw_set("devops", "foobar")

    MQTT_BROKER = "localhost"
    payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    interval = 1 / (msg_frequency_hz)
    nb_messages = nb_seconds * msg_frequency_hz
    sent = 0
    i = 0
    sleep_time = (start_time - datetime.now(tz=tz)).total_seconds()
    time.sleep(sleep_time)

    next_time = time.perf_counter()
    print_time("Sending messages...")

    try:
        while not sent >= nb_messages:
            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(tz=tz).isoformat()
                MQTT_TOPIC = f"my.namespace/{device_ids[i]}/things/twin/commands/modify"
                payload["topic"] = MQTT_TOPIC
            elif dt_solution == "scorpio":
                MQTT_TOPIC = f"/json/{scorpio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            elif dt_solution == "orion_ld":
                MQTT_TOPIC = f"/json/{orion_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            elif dt_solution == "stellio":
                MQTT_TOPIC = f"/json/{stellio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            data = json.dumps(payload)
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

def send_messages_poissonlaw(devices, dt_solution, poisson_lambda, nb_seconds, start_time, nb_attributes, bytes_per_attribute):
    client = mqtt.Client()
    if dt_solution == "scorpio" or dt_solution == "orion_ld" or dt_solution == "stellio":
        device_ids = [device["id"].split(":")[-1] for device in devices]
    elif dt_solution == "ditto":
        device_ids = [thing['thingId'].split(":")[-1] for thing in devices]
        client.username_pw_set("devops", "foobar")

    MQTT_BROKER = "localhost"
    payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)

    print_time("Sending messages with Poisson intervals...")
    t0 = time.time()
    i = 0

    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    sleep_time = (start_time - datetime.now(tz=tz)).total_seconds()
    time.sleep(sleep_time)

    try:
        while time.time() - t0 < nb_seconds:
            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(tz=tz).isoformat()
                MQTT_TOPIC = f"my.namespace/{device_ids[i]}/things/twin/commands/modify"
                payload["topic"] = MQTT_TOPIC
            elif dt_solution == "scorpio":
                MQTT_TOPIC = f"/json/{scorpio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            elif dt_solution == "orion_ld":
                MQTT_TOPIC = f"/json/{orion_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            elif dt_solution == "stellio":
                MQTT_TOPIC = f"/json/{stellio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            data = json.dumps(payload)
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

def send_messages_gaussianlaw(devices, dt_solution, nb_messages, nb_seconds, start_time, nb_attributes, bytes_per_attribute, center_ratio=0.5, sigma_ratio=0.1):
    client = mqtt.Client()
    if dt_solution == "scorpio" or dt_solution == "orion_ld" or dt_solution == "stellio":
        device_ids = [device["id"].split(":")[-1] for device in devices]
    elif dt_solution == "ditto":
        device_ids = [thing['thingId'].split(":")[-1] for thing in devices]
        client.username_pw_set("devops", "foobar")

    MQTT_BROKER = "localhost"
    payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)

    center_time = nb_seconds * center_ratio
    sigma = nb_seconds * sigma_ratio

    # Générer les instants d’envoi
    send_times = np.random.normal(loc=center_time, scale=sigma, size=nb_messages)
    send_times = send_times[(send_times >= 0) & (send_times <= nb_seconds)]  # Garder ceux dans la fenêtre
    send_times.sort()

    i = 0
    client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)

    sleep_time = (start_time - datetime.now(tz=tz)).total_seconds()
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
                payload["value"]["measuredAt"] = datetime.now(tz=tz).isoformat()
                MQTT_TOPIC = f"my.namespace/{device_ids[i]}/things/twin/commands/modify"
                payload["topic"] = MQTT_TOPIC
            elif dt_solution == "scorpio":
                MQTT_TOPIC = f"/json/{scorpio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            elif dt_solution == "orion_ld":
                MQTT_TOPIC = f"/json/{orion_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            elif dt_solution == "stellio":
                MQTT_TOPIC = f"/json/{stellio_config_data["apikey"]}/TrafficFlowSensor{i + 1}/attrs"
            data = json.dumps(payload)
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
