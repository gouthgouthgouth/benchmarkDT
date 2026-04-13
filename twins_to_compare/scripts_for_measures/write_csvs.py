import re
import csv
import os
from datetime import datetime, timedelta


def write_csvs(file_datetime, dt_solution, file_name, lambdas_list):
    if lambdas_list is not None:
        write_csv_lambdas(file_datetime, dt_solution, file_name, lambdas_list)

    if dt_solution == "ditto":
        csv_filename = write_csvs_ditto(file_datetime, file_name)
    elif dt_solution == "scorpio":
        csv_filename = write_csvs_scorpio(file_datetime, file_name)
    elif dt_solution == "orion_ld":
        csv_filename = write_csvs_orion(file_datetime, file_name)
    else:
        return None
    return csv_filename

def write_csvs_ditto(file_datetime, file_name):
    dt = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S")

    cpu_ram_logfile = "twins_to_compare/scripts_for_measures/ditto/measures/" + file_datetime + "-cpu_ram"
    mosquitto_logfile = "twins_to_compare/scripts_for_measures/ditto/measures/" + file_datetime + "-mosquitto"
    things_logfile = "twins_to_compare/scripts_for_measures/ditto/measures/" + file_datetime + "-things"
    output_csv_things = f"twins_to_compare/scripts_for_measures/ditto/measures_csv/{file_name}-things.csv"
    output_csv_mosquitto = f"twins_to_compare/scripts_for_measures/ditto/measures_csv/{file_name}-mosquitto.csv"
    result_file = "twins_to_compare/scripts_for_measures/ditto/results/" + file_name + "-delays.csv"

    os.makedirs("twins_to_compare/scripts_for_measures/ditto/measures_csv", exist_ok=True)

    occurence = {}

    with open(things_logfile, "r") as f, open(output_csv_things, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurence"])
        for line in f:
            if "things.events:attributeModified" in line or "things.events:attributeCreated" in line:
                try:
                    timestamp = line[:23].replace(" ", "_").replace(":", "-")
                    if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
                        thing_id = "my.namespace:RoadSegment" + line.split("RoadSegment")[1].split("/")[0]
                        if thing_id in occurence:
                            occurence[thing_id] += 1
                        else:
                            occurence[thing_id] = 1
                        writer.writerow([timestamp, thing_id, occurence[thing_id]])
                except:
                    pass


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
    return result_file


def write_csvs_scorpio(file_datetime, file_name):
    dt = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S")

    cpu_ram_logfile = "twins_to_compare/scripts_for_measures/scorpio/measures/" + file_datetime + "-cpu_ram"
    mosquitto_logfile = "twins_to_compare/scripts_for_measures/scorpio/measures/" + file_datetime + "-mosquitto"
    things_logfile = "twins_to_compare/scripts_for_measures/scorpio/measures/" + file_datetime + "-entities"
    output_csv_things = f"twins_to_compare/scripts_for_measures/scorpio/measures_csv/{file_name}-entities.csv"
    output_csv_mosquitto = f"twins_to_compare/scripts_for_measures/scorpio/measures_csv/{file_name}-mosquitto.csv"
    result_file = "twins_to_compare/scripts_for_measures/scorpio/results/" + file_name + "-delays.csv"

    os.makedirs("twins_to_compare/scripts_for_measures/scorpio/measures_csv", exist_ok=True)

    occurence = {}

    with open(things_logfile, "r") as f, open(output_csv_things, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurence"])
        for line in f:
            if "with apiKey apikey123 successfully updated" in line:
                try:
                    timestamp = line[5:28].replace("T", "_").replace(":", "-")
                    ts = datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S.%f") + timedelta(hours=2)
                    timestamp = ts.strftime("%Y-%m-%d_%H-%M-%S.%f")
                    if ts >= dt:
                        thing_id = "urn:ngsi-ld:RoadSegment:RoadSegment" + line.split("TrafficFlowSensor")[1].split(" ")[0]
                        if thing_id in occurence:
                            occurence[thing_id] += 1
                        else:
                            occurence[thing_id] = 1
                        writer.writerow([timestamp, thing_id, occurence[thing_id]])
                except:
                    print(line)


    occurence = {}

    with open(mosquitto_logfile, "r") as f, open(output_csv_mosquitto, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurence"])
        for line in f:
            if "/json/apikey123/TrafficFlowSensor" in line:
                timestamp = line[:23].replace("T", "_").replace(":", "-")
                if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
                    thing_id = "urn:ngsi-ld:RoadSegment:RoadSegment" + line.split("TrafficFlowSensor")[1].split("/")[0]

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
    return result_file

def write_csvs_orion(file_datetime, file_name):
    dt = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S")

    cpu_ram_logfile = "twins_to_compare/scripts_for_measures/orion_ld/measures/" + file_datetime + "-cpu_ram"
    mosquitto_logfile = "twins_to_compare/scripts_for_measures/orion_ld/measures/" + file_datetime + "-mosquitto"
    things_logfile = "twins_to_compare/scripts_for_measures/orion_ld/measures/" + file_datetime + "-entities"
    output_csv_things = f"twins_to_compare/scripts_for_measures/orion_ld/measures_csv/{file_name}-entities.csv"
    output_csv_mosquitto = f"twins_to_compare/scripts_for_measures/orion_ld/measures_csv/{file_name}-mosquitto.csv"
    result_file = "twins_to_compare/scripts_for_measures/orion_ld/results/" + file_name + "-delays.csv"

    os.makedirs("twins_to_compare/scripts_for_measures/orion_ld/measures_csv", exist_ok=True)

    occurence = {}

    with open(things_logfile, "r") as f, open(output_csv_things, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurence"])
        for line in f:
            if "with apiKey apikey123 successfully updated" in line:
                timestamp = line[5:28].replace("T", "_").replace(":", "-")
                ts = datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S.%f") + timedelta(hours=2)
                timestamp = ts.strftime("%Y-%m-%d_%H-%M-%S.%f")
                if ts >= dt:
                    thing_id = "urn:ngsi-ld:RoadSegment:RoadSegment" + line.split("TrafficFlowSensor")[1].split(" ")[0]
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
            if "/json/apikey123/TrafficFlowSensor" in line:
                timestamp = line[:23].replace("T", "_").replace(":", "-")
                if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
                    thing_id = "urn:ngsi-ld:RoadSegment:RoadSegment" + line.split("TrafficFlowSensor")[1].split("/")[0]

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
                    (thing_id, occurence)]).total_seconds() - 3600, 3)
                delays.append(delay)
            else:
                delay = "Error, msg not received or log wasn't captured."
            writer.writerow([mosquitto_messages[(thing_id, occurence)], message_id, delay])
    return result_file

def log_not_captured_in_csv(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        for line in f:
            if "Error, msg not received or log wasn't captured" in line:
                return True
    return False

def write_csv_lambdas(file_datetime, dt_solution, file_name, lambdas_list):
    result_file = "twins_to_compare/scripts_for_measures/" + dt_solution + "/results/" + file_name + "-lambdas_list.csv"
    with open(result_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["change_timestamp", "lambda"])
        for line in lambdas_list:
            writer.writerow(line)