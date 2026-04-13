"""
Central configuration for the benchmarkDT project.

Defines hardware resource limits, MQTT connection parameters, and per-broker
HTTP endpoint dictionaries consumed by the benchmark and broker adapter modules.
"""
import os

RAM_LIMIT = "4g"
CPU_LIMIT = "2.0"
MQTT_BROKER = "mosquitto"   # Docker service name of the MQTT broker
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"  # Default topic; overridden per-broker in simulator.py
CONNECTION_ID = "mosquitto_connection"
PROJECT_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Scorpio NGSI-LD broker + IoT Agent endpoints and FIWARE service metadata.
scorpio_config_data = {
    "CBROKER_ADDRESS" : "http://localhost:9090/",
    "IOT_AGENT_ADDRESS" : "http://localhost:4041/",
    "IOT_AGENT_HTTP_ADDRESS" : "http://localhost:7896/",
    "fiware_service" : "tenant-1",
    "fiware_servicepath" : "/",
    "apikey" : "apikey123",
    "default_resource" : "/iot/json",
    "transport" : "MQTT",
    "sensor_entity_type" : "TrafficFlowSensor",
}

# Orion-LD NGSI-LD broker + IoT Agent endpoints. Identical to Scorpio except CBROKER_ADDRESS.
orion_config_data = {
    "CBROKER_ADDRESS" : "http://localhost:1026/",
    "IOT_AGENT_ADDRESS" : "http://localhost:4041/",
    "IOT_AGENT_HTTP_ADDRESS" : "http://localhost:7896/",
    "fiware_service" : "tenant-1",
    "fiware_servicepath" : "/",
    "apikey" : "apikey123",
    "default_resource" : "/iot/json",
    "transport" : "MQTT",
    "sensor_entity_type" : "TrafficFlowSensor",
}

# Eclipse Ditto REST API base URL and credentials.
eclipse_config_data = {
    "DITTO_BASE_URL" : "http://localhost:8080",
    "NAMESPACE" : "my.namespace",
    "USERNAME" : "devops",
    "PASSWORD" : "foobar",
}
