
RAM_LIMIT="2g"
CPU_LIMIT="2.0"
MQTT_BROKER = "mosquitto"
MQTT_PORT = 1883
MQTT_TOPIC = "sensor/data"
CONNECTION_ID = "mosquitto_connection"

scorpio_config_data = {
    "CONTAINER_NAME" : "fiware-scorpio",
    "IMAGE_NAME" : "fiware/scorpio",
    "CBROKER_ADDRESS" : "http://localhost:9090/",
    "IOT_AGENT_ADDRESS" : "http://localhost:4041/",
    "IOT_AGENT_HTTP_ADDRESS" : "http://localhost:7896/",
    "fiware_service" : "tenant-1",
    "fiware_servicepath" : "/",
    "apikey" : "apikey123",
    "default_resource" : "/iot/json",
    "transport" : "MQTT",
    "sensor_entity_type" : "TrafficFlowSensor",
    "trafficFlowSensor_attributes" : [
        {"object_id": "c", "name": "carTrafficFlow", "type": "Integer"},
        {"object_id": "t", "name": "truckTrafficFlow", "type": "Integer"}
    ],
}

eclipse_config_data = {
    "DITTO_BASE_URL" : "http://localhost:8080",
    "NAMESPACE" : "my.namespace",
    "USERNAME" : "devops",
    "PASSWORD" : "foobar",
}