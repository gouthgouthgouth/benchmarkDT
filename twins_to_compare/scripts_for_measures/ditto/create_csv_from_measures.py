import re
import csv
import os
from datetime import datetime

file_datetime = "2025-03-20_17-39-25"
dt = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S")

cpu_ram_logfile = "measures/" + file_datetime + "-cpu_ram"
mosquitto_logfile = "measures/" + file_datetime + "-mosquitto"
things_logfile = "measures/" + file_datetime + "-things"

output_csv_things = f"measures_csv/{file_datetime}-things.csv"
output_csv_mosquitto = f"measures_csv/{file_datetime}-mosquitto.csv"

os.makedirs("measures_csv", exist_ok=True)

occurence = {}

with open(things_logfile, "r") as f, open(output_csv_things, "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["timestamp", "thing_id", "occurence"])
    for line in f:
        if "things.events:attributeModified" in line:
            timestamp = line[:23].replace(" ", "_").replace(":", "-")
            if datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S") > dt:
                thing_id = "my.namespace:RoadSegment" + line.split("RoadSegment")[1].split("/")[0]
                if thing_id in occurence:
                    occurence[thing_id] += 1
                else:
                    occurence[thing_id] = 1
                writer.writerow([timestamp, thing_id, occurence[thing_id]])


occurence = {}

with open(mosquitto_logfile, "r") as f, open(output_csv_mosquitto, "w", newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["timestamp", "thing_id", "occurence"])
    for line in f:
        if "Sending PUBLISH" in line:
            timestamp = line[:23].replace(" ", "_").replace(":", "-")
            if datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S") > dt:
                thing_id = "my.namespace:RoadSegment" + line.split("RoadSegment")[1].split("/")[0]

                if thing_id in occurence:
                    occurence[thing_id] += 1
                else:
                    occurence[thing_id] = 1

                writer.writerow([timestamp, thing_id, occurence[thing_id]])