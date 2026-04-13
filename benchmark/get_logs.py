"""
Log recording utilities for MQTT traffic and system resource metrics.

Provides two functions intended to run concurrently with the benchmark:
one captures every MQTT message and its arrival timestamp, the other
launches shell scripts that periodically sample CPU and RAM usage.
"""
import subprocess

import paho.mqtt.client as mqtt
from datetime import datetime
from zoneinfo import ZoneInfo
import os

from config.config import PROJECT_FOLDER


def record_logs_mosquitto(date, dt_solution):
    """Subscribe to all MQTT topics and log each message with its arrival timestamp.

    Runs indefinitely (``loop_forever``). Intended to be started in a separate
    process before the benchmark begins and terminated via ``cleanup()`` afterwards.

    Each line written to the output file has the format:
        ``<ISO-8601 timestamp> <topic>``

    Args:
        date (str): File-datetime string (``%Y-%m-%d_%H-%M-%S``) used to name the
            output file so it matches the other log files for the same run.
        dt_solution (str): One of ``"ditto"``, ``"scorpio"``, or ``"orion_ld"``.
            Used to place the log file under the correct broker subdirectory.
    """
    output_folder = f"{PROJECT_FOLDER}/measures/{dt_solution}/measures/"
    broker = "localhost"
    port = 1883
    os.makedirs("measures_raw", exist_ok=True)
    output_file = output_folder + f"{date}-mosquitto"

    def on_connect(client, userdata, flags, rc):
        client.subscribe("#")

    def on_message(client, userdata, msg):
        now = datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec='milliseconds')
        with open(output_file, "a") as f:
            f.write(f"{now} {msg.topic}\n")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(broker, port, 60)

    print(f"Logging raw MQTT messages with timestamps to {output_file}")
    client.loop_forever()


def record_logs_cpu_ram_delay(date, dt_solution):
    """Launch the broker-specific and CPU/RAM logging shell scripts as background processes.

    The two scripts run concurrently for the duration of the benchmark and are
    terminated by ``cleanup()`` using the PIDs returned here.

    Args:
        date (str): File-datetime string passed as the first argument to both scripts
            so they write output files that match the other logs for the same run.
        dt_solution (str): One of ``"ditto"``, ``"scorpio"``, or ``"orion_ld"``.

    Returns:
        tuple[int, int]: PIDs of the broker log script and the CPU/RAM log script,
            or ``None`` if ``dt_solution`` is invalid.
    """
    if dt_solution not in ["ditto", "scorpio", "orion_ld"]:
        print("Erreur dt_solution mal renseigné")
        return None, None

    base_path = f"./measures/{dt_solution}"
    process1 = subprocess.Popen(["bash", f"{base_path}/{dt_solution}_get_logs.sh", date])
    print(f"Script {dt_solution}_get_logs.sh running in background with PID {process1.pid}")
    process2 = subprocess.Popen(["bash", f"{base_path}/cpu_ram_get_logs.sh", date])
    print(f"Script cpu_ram_get_logs.sh running in background with PID {process2.pid}")

    return process1.pid, process2.pid
