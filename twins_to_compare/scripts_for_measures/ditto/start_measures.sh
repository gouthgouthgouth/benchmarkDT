#!/bin/bash

./cpu_ram_get_logs.sh &
./ditto_get_logs.sh &
./mosquitto_get_logs.sh &