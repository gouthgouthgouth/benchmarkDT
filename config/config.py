import os

RAM_LIMIT="4g"
CPU_LIMIT="2.0"
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"
CONNECTION_ID = "mosquitto_connection"
PROJECT_FOLDER = "/home/pc-lrt-oaibox/PycharmProjects/benchmarkDT"

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

eclipse_config_data = {
    "DITTO_BASE_URL" : "http://localhost:8080",
    "NAMESPACE" : "my.namespace",
    "USERNAME" : "devops",
    "PASSWORD" : "foobar",
}