"""
MQTT message simulator for the benchmarkDT benchmark.

Provides four functions that send sensor payloads to an MQTT broker following
different statistical arrival processes:

- Uniform (constant frequency)
- Poisson (exponentially distributed inter-arrival times)
- Gaussian (messages clustered around a centre point in time)
- MMPP – Markov Modulated Poisson Process (time-varying Poisson rate driven
  by a discrete-time Markov chain)

All four functions share the same MQTT topic scheme and payload format, which
are factored out into the private helpers ``_build_mqtt_topic`` and
``_extract_device_ids``.
"""
import logging
import random
import time
from datetime import datetime, timezone, timedelta
import string
from itertools import product, islice

import numpy as np
import paho.mqtt.client as mqtt
import json

from config.config import scorpio_config_data, MQTT_PORT, orion_config_data

logger = logging.getLogger(__name__)

# UTC+2 timezone used for all send timestamps embedded in Ditto payloads.
tz = timezone(timedelta(hours=2))


def gen_ids(n):
    """Generate n short unique string identifiers drawn from the lowercase alphabet.

    Uses single letters first (a–z), then two-letter combinations (aa, ab, …)
    to keep IDs as short as possible.

    Args:
        n (int): Number of identifiers to generate.

    Returns:
        list[str]: List of n unique string IDs.
    """
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
    """Build a broker-specific MQTT payload with randomised attribute values.

    For FIWARE brokers (Scorpio, Orion-LD) the payload is a flat dict of
    attribute key → random string value. For Ditto the payload wraps the
    attributes inside the twin-modify command envelope and includes a
    ``measuredAt`` timestamp.

    Args:
        dt_solution (str): One of ``"orion_ld"``, ``"scorpio"``, or ``"ditto"``.
        nb_attributes (int): Number of attributes to include in the payload.
        bytes_per_attr (int): Length of the random string value for each attribute.
        tz (timezone): Timezone used for the Ditto ``measuredAt`` timestamp.

    Returns:
        dict: JSON-serialisable payload dictionary.

    Raises:
        ValueError: If ``dt_solution`` is not a recognised broker name.
    """
    attr_ids = gen_ids(nb_attributes)
    letters = "abcdefghij"

    def random_str(length):
        return ''.join(random.choices(letters, k=length))

    if dt_solution in {"orion_ld", "scorpio"}:
        return {id_: random_str(bytes_per_attr) for id_ in attr_ids}

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


def _extract_device_ids(devices, dt_solution, client):
    """Extract the short device identifier from each entity dict.

    For Ditto things the ID is the part after the namespace colon in
    ``thingId``; for FIWARE entities it is the last ``:`-separated segment
    of the NGSI-LD ``id``. Also sets MQTT credentials on ``client`` for Ditto.

    Args:
        devices (list[dict]): Entity or thing dictionaries as returned by the
            entity creation helpers.
        dt_solution (str): Broker name.
        client (mqtt.Client): MQTT client instance; credentials are set in place
            for Ditto.

    Returns:
        list[str]: Short device ID strings used to build MQTT topics.
    """
    if dt_solution == "scorpio" or dt_solution == "orion_ld":
        return [device["id"].split(":")[-1] for device in devices]
    elif dt_solution == "ditto":
        client.username_pw_set("devops", "foobar")
        return [thing['thingId'].split(":")[-1] for thing in devices]


def _build_mqtt_topic(dt_solution, device_ids, i):
    """Build the MQTT topic string for the i-th device.

    Args:
        dt_solution (str): Broker name.
        device_ids (list[str]): Short device ID strings.
        i (int): Index of the current device in the round-robin cycle.

    Returns:
        str: MQTT topic to publish to.
    """
    if dt_solution == "ditto":
        return f"my.namespace/{device_ids[i]}/things/twin/commands/modify"
    elif dt_solution == "scorpio":
        return f"/json/{scorpio_config_data['apikey']}/TrafficFlowSensor{i + 1}/attrs"
    elif dt_solution == "orion_ld":
        return f"/json/{orion_config_data['apikey']}/TrafficFlowSensor{i + 1}/attrs"


def send_messages_uniformlaw(devices, dt_solution, msg_frequency_hz, nb_seconds, start_time, nb_attributes, bytes_per_attribute):
    """Send messages at a constant rate (uniform inter-arrival times).

    Uses ``time.perf_counter`` for precise pacing: each iteration calculates
    the exact time the next message should be sent and sleeps only for the
    remaining fraction. Messages are distributed across all devices in a
    round-robin fashion.

    Args:
        devices (list[dict]): Entity dictionaries.
        dt_solution (str): Broker name.
        msg_frequency_hz (float): Target send rate in messages per second.
        nb_seconds (int): Duration of the experiment in seconds.
        start_time (datetime): Timezone-aware datetime at which sending begins.
        nb_attributes (int): Number of attributes per payload.
        bytes_per_attribute (int): Size in bytes of each attribute value.
    """
    client = mqtt.Client()
    device_ids = _extract_device_ids(devices, dt_solution, client)

    mqtt_broker = "localhost"
    payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)

    client.connect(mqtt_broker, MQTT_PORT, keepalive=60)
    interval = 1 / (msg_frequency_hz)
    nb_messages = nb_seconds * msg_frequency_hz
    sent = 0
    i = 0

    # Wait until the scheduled start time before sending the first message.
    sleep_time = (start_time - datetime.now(tz=tz)).total_seconds()
    time.sleep(sleep_time)

    next_time = time.perf_counter()
    logger.info("Sending messages (uniform law)...")

    try:
        while not sent >= nb_messages:
            mqtt_topic = _build_mqtt_topic(dt_solution, device_ids, i)
            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(tz=tz).isoformat()
                payload["topic"] = mqtt_topic
            data = json.dumps(payload)
            client.publish(mqtt_topic, data)
            payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)

            # Advance the target time by one interval and sleep for the remainder.
            next_time += interval
            sleep_time = next_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            sent += 1

            # Round-robin over devices.
            if i < len(device_ids) - 1:
                i += 1
            else:
                i = 0

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

    logger.info("All uniform-law messages have been sent.")


def send_messages_poissonlaw(devices, dt_solution, poisson_lambda, nb_seconds, start_time, nb_attributes, bytes_per_attribute):
    """Send messages with Poisson-distributed inter-arrival times.

    Inter-arrival times are drawn from an exponential distribution with rate
    ``poisson_lambda``. Sending continues until ``nb_seconds`` have elapsed.

    Args:
        devices (list[dict]): Entity dictionaries.
        dt_solution (str): Broker name.
        poisson_lambda (float): Average number of messages per second (rate λ).
        nb_seconds (int): Duration of the experiment in seconds.
        start_time (datetime): Timezone-aware datetime at which sending begins.
        nb_attributes (int): Number of attributes per payload.
        bytes_per_attribute (int): Size in bytes of each attribute value.
    """
    client = mqtt.Client()
    device_ids = _extract_device_ids(devices, dt_solution, client)

    mqtt_broker = "localhost"
    payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)

    logger.info("Sending messages (Poisson law)...")
    t0 = time.time()
    i = 0

    client.connect(mqtt_broker, MQTT_PORT, keepalive=60)
    sleep_time = (start_time - datetime.now(tz=tz)).total_seconds()
    time.sleep(sleep_time)

    try:
        while time.time() - t0 < nb_seconds:
            mqtt_topic = _build_mqtt_topic(dt_solution, device_ids, i)
            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(tz=tz).isoformat()
                payload["topic"] = mqtt_topic
            data = json.dumps(payload)
            client.publish(mqtt_topic, data)

            # Draw the next inter-arrival time from Exp(λ).
            interval = np.random.exponential(1 / poisson_lambda)
            time.sleep(interval)

            if i < len(device_ids) - 1:
                i += 1
            else:
                i = 0
    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

    logger.info("All Poisson-law messages have been sent.")


def send_messages_gaussianlaw(devices, dt_solution, nb_messages, nb_seconds, start_time, nb_attributes, bytes_per_attribute, center_ratio=0.5, sigma_ratio=0.1):
    """Send messages whose send times follow a Gaussian distribution within the window.

    All send timestamps are pre-computed before the experiment starts: they are
    sampled from N(center, σ²), filtered to the ``[0, nb_seconds]`` window,
    and sorted so they can be replayed in order.

    Args:
        devices (list[dict]): Entity dictionaries.
        dt_solution (str): Broker name.
        nb_messages (int): Total number of messages to send (before filtering
            out-of-window samples).
        nb_seconds (int): Duration of the experiment window in seconds.
        start_time (datetime): Timezone-aware datetime at which the window begins.
        nb_attributes (int): Number of attributes per payload.
        bytes_per_attribute (int): Size in bytes of each attribute value.
        center_ratio (float): Centre of the Gaussian as a fraction of ``nb_seconds``.
        sigma_ratio (float): Standard deviation as a fraction of ``nb_seconds``.

    Returns:
        datetime: ``start_time`` (passed through for caller convenience).
    """
    client = mqtt.Client()
    device_ids = _extract_device_ids(devices, dt_solution, client)

    mqtt_broker = "localhost"
    payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)

    center_time = nb_seconds * center_ratio
    sigma = nb_seconds * sigma_ratio

    # Pre-compute all send offsets (in seconds from start) and sort them.
    send_times = np.random.normal(loc=center_time, scale=sigma, size=nb_messages)
    send_times = send_times[(send_times >= 0) & (send_times <= nb_seconds)]
    send_times.sort()

    i = 0
    client.connect(mqtt_broker, MQTT_PORT, keepalive=60)

    sleep_time = (start_time - datetime.now(tz=tz)).total_seconds()
    time.sleep(sleep_time)

    logger.info("Sending messages (Gaussian law)...")

    start_perf = time.perf_counter()
    try:
        for send_time_point in send_times:
            # Sleep until the pre-scheduled offset relative to start_perf.
            now_perf = time.perf_counter() - start_perf
            sleep_time = send_time_point - now_perf
            if sleep_time > 0:
                time.sleep(sleep_time)

            mqtt_topic = _build_mqtt_topic(dt_solution, device_ids, i)
            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(tz=tz).isoformat()
                payload["topic"] = mqtt_topic
            data = json.dumps(payload)
            client.publish(mqtt_topic, data)

            if i < len(device_ids) - 1:
                i += 1
            else:
                i = 0

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

    logger.info("All Gaussian-law messages have been sent.")
    return start_time


def generate_mmpp_lambda_timestamps(lambdas, nb_seconds,
                             P = np.array([[0.99, 0.01, 0.0], [0.005, 0.99, 0.005], [0.0, 0.01, 0.99]])):
    """Simulate the state sequence of a discrete-time Markov chain and record state transitions.

    Each second, the chain either stays in the current state or transitions to a
    new one according to the row of the transition matrix P corresponding to the
    current state. Only state *changes* are recorded.

    Args:
        lambdas (list[float]): Arrival rate λ for each Markov state.
        nb_seconds (int): Number of time steps (seconds) to simulate.
        P (np.ndarray): Square row-stochastic transition matrix of shape
            ``(len(lambdas), len(lambdas))``.

    Returns:
        list[tuple[int, float]]: List of ``(second, lambda)`` pairs marking each
            state transition. The first entry is always ``(0, lambdas[0])``.
    """
    state = 0
    lambdas_time = [(0, lambdas[0])]

    for i in range(1, nb_seconds):
        new_state = np.random.choice(len(lambdas), p=P[state])
        if new_state != state:
            lambdas_time.append((i, lambdas[new_state]))
            state = new_state

    return lambdas_time


def send_messages_mmpp(devices, dt_solution, lambdas, P, nb_seconds, start_time, nb_attributes, bytes_per_attribute, queue):
    """Send messages according to a Markov Modulated Poisson Process (MMPP).

    The MMPP arrival rate λ varies over time according to a Markov chain.
    The state sequence (and therefore the λ schedule) is pre-computed via
    ``generate_mmpp_lambda_timestamps`` and passed back to the caller through
    ``queue`` so it can be persisted alongside the delay results.

    At each step the next inter-arrival time is drawn from Exp(λ_current), and
    the current λ is updated whenever a scheduled state transition is reached.

    Args:
        devices (list[dict]): Entity dictionaries.
        dt_solution (str): Broker name.
        lambdas (list[float]): Arrival rates for each Markov state.
        P (np.ndarray): Row-stochastic transition matrix.
        nb_seconds (int): Duration of the experiment in seconds.
        start_time (datetime): Timezone-aware datetime at which sending begins.
        nb_attributes (int): Number of attributes per payload.
        bytes_per_attribute (int): Size in bytes of each attribute value.
        queue (multiprocessing.Queue): Queue used to return ``lambdas_time`` to
            the parent process.
    """
    client = mqtt.Client()
    device_ids = _extract_device_ids(devices, dt_solution, client)

    mqtt_broker = "localhost"
    payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)
    data = json.dumps(payload)

    # Pre-compute the full lambda schedule and share it with the parent process.
    lambdas_time = generate_mmpp_lambda_timestamps(lambdas=lambdas,
                                                   nb_seconds=nb_seconds,
                                                   P=P)
    queue.put(lambdas_time)

    poisson_lambda = lambdas_time[0][1]
    logger.info("Sending messages (MMPP law)...")
    t0 = time.time()
    i, lambda_index = 0, 0

    client.connect(mqtt_broker, MQTT_PORT, keepalive=60)
    sleep_time = (start_time - datetime.now(tz=tz)).total_seconds()
    time.sleep(sleep_time)

    try:
        time_since_start = time.time() - t0
        while time_since_start < nb_seconds:
            current_time = time.time()

            # Advance to the next scheduled lambda transition if its time has come.
            if len(lambdas) > 1 and lambda_index < len(lambdas_time) - 1:
                if time_since_start >= lambdas_time[lambda_index + 1][0]:
                    poisson_lambda = poisson_lambda = lambdas_time[lambda_index + 1][1]
                    lambda_index += 1

            # Draw the next inter-arrival time from the current Poisson rate.
            interval = np.random.exponential(1 / poisson_lambda)

            mqtt_topic = _build_mqtt_topic(dt_solution, device_ids, i)
            if dt_solution == "ditto":
                payload["value"]["measuredAt"] = datetime.now(tz=tz).isoformat()
                payload["topic"] = mqtt_topic

            data = json.dumps(payload)
            client.publish(mqtt_topic, data)
            payload = generate_payload(dt_solution, nb_attributes, bytes_per_attr=bytes_per_attribute, tz=tz)

            if i < len(device_ids) - 1:
                i += 1
            else:
                i = 0

            # Sleep for the remainder of the inter-arrival interval; if the
            # publish already took longer than the interval, skip the sleep.
            try:
                time.sleep(interval - time.time() + current_time)
            except:
                pass

            time_since_start = time.time() - t0

    except KeyboardInterrupt:
        client.loop_stop()
        client.disconnect()

    logger.info("All MMPP-law messages have been sent.")
