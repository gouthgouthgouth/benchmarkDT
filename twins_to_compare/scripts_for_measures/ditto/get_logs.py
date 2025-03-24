import subprocess

import paho.mqtt.client as mqtt
from datetime import datetime
from zoneinfo import ZoneInfo
import os

def record_logs_mosquitto(date):
    BROKER = "localhost"
    PORT = 1883
    os.makedirs("measures_raw", exist_ok=True)
    output_file = f"/home/gauthier-le-tat/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/ditto/measures/{date}-mosquitto"

    def on_connect(client, userdata, flags, rc):
        client.subscribe("#")

    def on_message(client, userdata, msg):
        now = datetime.now(ZoneInfo("Europe/Paris")).isoformat(timespec='milliseconds')
        with open(output_file, "a") as f:
            f.write(f"{now} {msg.topic} {msg.payload.decode(errors='ignore')}\n")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT, 60)

    print(f"Logging raw MQTT messages with timestamps to {output_file}")
    client.loop_forever()

def record_logs_ditto(date):
    process1 = subprocess.Popen(["bash", "./twins_to_compare/scripts_for_measures/ditto/ditto_get_logs.sh", date])
    print(f"Script ditto_get_logs.sh running in background with PID {process1.pid}")
    process2 = subprocess.Popen(["bash", "./twins_to_compare/scripts_for_measures/ditto/cpu_ram_get_logs.sh", date])
    print(f"Script cpu_ram_get_logs.sh running in background with PID {process2.pid}")
    return process1.pid, process2.pid