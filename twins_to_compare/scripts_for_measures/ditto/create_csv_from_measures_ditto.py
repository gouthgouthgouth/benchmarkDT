import re
import csv
import os
from datetime import datetime

def write_csvs_ditto(file_datetime):
    dt = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S")

    cpu_ram_logfile = "twins_to_compare/scripts_for_measures/ditto/measures/" + file_datetime + "-cpu_ram"
    mosquitto_logfile = "twins_to_compare/scripts_for_measures/ditto/measures/" + file_datetime + "-mosquitto"
    things_logfile = "twins_to_compare/scripts_for_measures/ditto/measures/" + file_datetime + "-things"
    output_csv_things = f"twins_to_compare/scripts_for_measures/ditto/measures_csv/{file_datetime}-things.csv"
    output_csv_mosquitto = f"twins_to_compare/scripts_for_measures/ditto/measures_csv/{file_datetime}-mosquitto.csv"
    result_file = "twins_to_compare/scripts_for_measures/ditto/results/" + file_datetime + "-delays.csv"

    os.makedirs("twins_to_compare/scripts_for_measures/ditto/measures_csv", exist_ok=True)

    occurence = {}

    with open(things_logfile, "r") as f, open(output_csv_things, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurence"])
        for line in f:
            if "things.events:attributeModified" in line:
                timestamp = line[:23].replace(" ", "_").replace(":", "-")
                if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
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
            if "things/twin/commands/modify" in line:
                timestamp = line[:23].replace("T", "_").replace(":", "-")
                if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
                    thing_id = "my.namespace:RoadSegment" + line.split("RoadSegment")[1].split("/")[0]

                    if thing_id in occurence:
                        occurence[thing_id] += 1
                    else:
                        occurence[thing_id] = 1

                    writer.writerow([timestamp, thing_id, occurence[thing_id]])

    def parse_time(t):
        dt_part, ms_part = t.split(',') if "," in t else t.split('.')
        dt_str = dt_part.replace('_', ' ')
        return datetime.strptime(f"{dt_str}.{ms_part}", "%Y-%m-%d %H-%M-%S.%f")

    # Charger Mosquitto (envoi)
    mosquitto_messages = {}
    with open(output_csv_mosquitto, newline='') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            sent_time, thing_id, occurence = row[0], row[1], int(row[2])
            mosquitto_messages[(thing_id, occurence)] = parse_time(sent_time)

    # Charger Things (envoi)
    things_messages = {}
    with open(output_csv_things, newline='') as f:
        reader = csv.reader(f)
        next(reader)  # skip header
        for row in reader:
            sent_time, thing_id, occurence = row[0], row[1], int(row[2])
            things_messages[(thing_id, occurence)] = parse_time(sent_time)

    delays = []

    with open(result_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["sent_timestamp", "message_id", "delay (s)"])

        for (thing_id, occurence) in mosquitto_messages:
            message_id = str(occurence) + "_" + thing_id
            if (thing_id, occurence) in things_messages:
                delay = round((things_messages[(thing_id, occurence)] - mosquitto_messages[
                    (thing_id, occurence)]).total_seconds(), 3)
                delays.append(delay)
            else:
                delay = "Error, msg not received or log wasn't captured."
            writer.writerow([mosquitto_messages[(thing_id, occurence)], message_id, delay])