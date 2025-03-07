
RAM_LIMIT="2g"
CPU_LIMIT="2.0"

fiware_config_data = {
    "CONTAINER_NAME" : "fiware-scorpio",
    "IMAGE_NAME" : "fiware/scorpio",
    "CBROKER_ADDRESS" : "http://localhost:9090/",
    "IOT_AGENT_ADDRESS" : "http://localhost:4041/",
    "IOT_AGENT_HTTP_ADDRESS" : "http://localhost:7896/",
    "fiware_service" : "tenant-1",
    "fiware_servicepath" : "/",
    "apikey" : "apikey123",
    "default_resource" : "/iot/json",
    "transport" : "HTTP",
    "sensor_entity_type" : "TrafficFlowSensor",
    "trafficFlowSensor_attributes" : [
        {"object_id": "c", "name": "carTrafficFlow", "type": "Integer"},
        {"object_id": "t", "name": "truckTrafficFlow", "type": "Integer"}
    ],
}
