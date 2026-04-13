"""
Post-processing module that converts raw log files into structured CSV results.

For each broker, a pair of raw log files (MQTT send events and broker receive
events) is parsed to extract per-message timestamps. The two streams are joined
on a ``(entity_id, occurrence_number)`` key to compute end-to-end delays and
write a final ``-delays.csv`` result file.
"""
import re
import csv
import os
from datetime import datetime, timedelta


def parse_time(t):
    """Parse a timestamp string that may use either a comma or a dot as the
    milliseconds separator.

    Expected formats after normalisation:
        ``YYYY-MM-DD_HH-MM-SS.ffffff``
        ``YYYY-MM-DD_HH-MM-SS,ffffff``

    Args:
        t (str): Timestamp string as written in the intermediate CSV files.

    Returns:
        datetime: Parsed datetime object.
    """
    dt_part, ms_part = t.split(',') if "," in t else t.split('.')
    dt_str = dt_part.replace('_', ' ')
    return datetime.strptime(f"{dt_str}.{ms_part}", "%Y-%m-%d %H-%M-%S.%f")


def write_csvs(file_datetime, dt_solution, file_name, lambdas_list):
    """Dispatch CSV writing to the broker-specific implementation.

    Also writes the MMPP lambda change log when the experiment used an MMPP
    arrival process.

    Args:
        file_datetime (str): Date-time string (``%Y-%m-%d_%H-%M-%S``) that
            identifies the raw log files to read.
        dt_solution (str): One of ``"ditto"``, ``"scorpio"``, or ``"orion_ld"``.
        file_name (str): Base name for the output CSV files.
        lambdas_list (list[tuple] | None): MMPP lambda change events as returned
            by ``generate_mmpp_lambda_timestamps``, or ``None`` for other laws.

    Returns:
        str | None: Path to the ``-delays.csv`` result file, or ``None`` if
            ``dt_solution`` is not recognised.
    """
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
    """Parse Ditto log files and compute per-message delays.

    Reads the raw ``-things`` (receive) and ``-mosquitto`` (send) log files,
    writes intermediate CSVs, then joins them on ``(thing_id, occurrence)``
    to produce the final ``-delays.csv`` file.

    Ditto timestamps in the things log are already in local time.
    Mosquitto timestamps use ISO-8601 with a 'T' separator.

    Args:
        file_datetime (str): Date-time prefix identifying the raw log files.
        file_name (str): Base name used for all output files.

    Returns:
        str: Path to the written ``-delays.csv`` file.
    """
    dt = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S")

    mosquitto_logfile = "measures/ditto/measures/" + file_datetime + "-mosquitto"
    things_logfile = "measures/ditto/measures/" + file_datetime + "-things"
    output_csv_things = f"measures/ditto/measures_csv/{file_name}-things.csv"
    output_csv_mosquitto = f"measures/ditto/measures_csv/{file_name}-mosquitto.csv"
    result_file = "measures/ditto/results/" + file_name + "-delays.csv"

    os.makedirs("measures/ditto/measures_csv", exist_ok=True)

    # --- Parse the Ditto things log (broker receive events) ---
    # Each relevant line contains "attributeModified" or "attributeCreated" and
    # encodes the thing ID in the form "RoadSegment<N>/...".
    occurrence = {}
    with open(things_logfile, "r") as f, open(output_csv_things, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurrence"])
        for line in f:
            if "things.events:attributeModified" in line or "things.events:attributeCreated" in line:
                try:
                    timestamp = line[:23].replace(" ", "_").replace(":", "-")
                    if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
                        thing_id = "my.namespace:RoadSegment" + line.split("RoadSegment")[1].split("/")[0]
                        occurrence[thing_id] = occurrence.get(thing_id, 0) + 1
                        writer.writerow([timestamp, thing_id, occurrence[thing_id]])
                except:
                    pass

    # --- Parse the Mosquitto log (MQTT send events) ---
    # Each relevant line contains "things/twin/commands/modify".
    occurrence = {}
    with open(mosquitto_logfile, "r") as f, open(output_csv_mosquitto, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurrence"])
        for line in f:
            if "things/twin/commands/modify" in line:
                timestamp = line[:23].replace("T", "_").replace(":", "-")
                if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
                    thing_id = "my.namespace:RoadSegment" + line.split("RoadSegment")[1].split("/")[0]
                    occurrence[thing_id] = occurrence.get(thing_id, 0) + 1
                    writer.writerow([timestamp, thing_id, occurrence[thing_id]])

    # --- Load both intermediate CSVs into dictionaries keyed by (thing_id, occurrence) ---
    mosquitto_messages = {}
    with open(output_csv_mosquitto, newline='') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sent_time, thing_id, occurrence = row[0], row[1], int(row[2])
            mosquitto_messages[(thing_id, occurrence)] = parse_time(sent_time)

    things_messages = {}
    with open(output_csv_things, newline='') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sent_time, thing_id, occurrence = row[0], row[1], int(row[2])
            things_messages[(thing_id, occurrence)] = parse_time(sent_time)

    # --- Join on (thing_id, occurrence) and write the delay for each message ---
    delays = []
    with open(result_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["sent_timestamp", "message_id", "delay (s)"])

        for (thing_id, occurrence) in mosquitto_messages:
            message_id = str(occurrence) + "_" + thing_id
            if (thing_id, occurrence) in things_messages:
                delay = round((things_messages[(thing_id, occurrence)] - mosquitto_messages[
                    (thing_id, occurrence)]).total_seconds(), 3)
                delays.append(delay)
            else:
                delay = "Error, msg not received or log wasn't captured."
            writer.writerow([mosquitto_messages[(thing_id, occurrence)], message_id, delay])

    return result_file


def write_csvs_scorpio(file_datetime, file_name):
    """Parse Scorpio log files and compute per-message delays.

    Scorpio timestamps in the entities log are in UTC and must be shifted by
    +2 hours to match the local timezone used by the Mosquitto logger.

    Args:
        file_datetime (str): Date-time prefix identifying the raw log files.
        file_name (str): Base name used for all output files.

    Returns:
        str: Path to the written ``-delays.csv`` file.
    """
    dt = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S")

    mosquitto_logfile = "measures/scorpio/measures/" + file_datetime + "-mosquitto"
    things_logfile = "measures/scorpio/measures/" + file_datetime + "-entities"
    output_csv_things = f"measures/scorpio/measures_csv/{file_name}-entities.csv"
    output_csv_mosquitto = f"measures/scorpio/measures_csv/{file_name}-mosquitto.csv"
    result_file = "measures/scorpio/results/" + file_name + "-delays.csv"

    os.makedirs("measures/scorpio/measures_csv", exist_ok=True)

    # --- Parse the Scorpio entities log (broker receive events) ---
    # Relevant lines contain "with apiKey apikey123 successfully updated".
    # Timestamps start at position 5 and are in UTC; +2h offset is applied.
    occurrence = {}
    with open(things_logfile, "r") as f, open(output_csv_things, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurrence"])
        for line in f:
            if "with apiKey apikey123 successfully updated" in line:
                try:
                    timestamp = line[5:28].replace("T", "_").replace(":", "-")
                    ts = datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S.%f") + timedelta(hours=2)
                    timestamp = ts.strftime("%Y-%m-%d_%H-%M-%S.%f")
                    if ts >= dt:
                        thing_id = "urn:ngsi-ld:RoadSegment:RoadSegment" + line.split("TrafficFlowSensor")[1].split(" ")[0]
                        occurrence[thing_id] = occurrence.get(thing_id, 0) + 1
                        writer.writerow([timestamp, thing_id, occurrence[thing_id]])
                except:
                    print(line)

    # --- Parse the Mosquitto log (MQTT send events) ---
    # Relevant lines contain the FIWARE IoT Agent MQTT topic pattern.
    occurrence = {}
    with open(mosquitto_logfile, "r") as f, open(output_csv_mosquitto, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurrence"])
        for line in f:
            if "/json/apikey123/TrafficFlowSensor" in line:
                timestamp = line[:23].replace("T", "_").replace(":", "-")
                if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
                    thing_id = "urn:ngsi-ld:RoadSegment:RoadSegment" + line.split("TrafficFlowSensor")[1].split("/")[0]
                    occurrence[thing_id] = occurrence.get(thing_id, 0) + 1
                    writer.writerow([timestamp, thing_id, occurrence[thing_id]])

    mosquitto_messages = {}
    with open(output_csv_mosquitto, newline='') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sent_time, thing_id, occurrence = row[0], row[1], int(row[2])
            mosquitto_messages[(thing_id, occurrence)] = parse_time(sent_time)

    things_messages = {}
    with open(output_csv_things, newline='') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sent_time, thing_id, occurrence = row[0], row[1], int(row[2])
            things_messages[(thing_id, occurrence)] = parse_time(sent_time)

    delays = []
    with open(result_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["sent_timestamp", "message_id", "delay (s)"])

        for (thing_id, occurrence) in mosquitto_messages:
            message_id = str(occurrence) + "_" + thing_id
            if (thing_id, occurrence) in things_messages:
                delay = round((things_messages[(thing_id, occurrence)] - mosquitto_messages[
                    (thing_id, occurrence)]).total_seconds(), 3)
                delays.append(delay)
            else:
                delay = "Error, msg not received or log wasn't captured."
            writer.writerow([mosquitto_messages[(thing_id, occurrence)], message_id, delay])

    return result_file


def write_csvs_orion(file_datetime, file_name):
    """Parse Orion-LD log files and compute per-message delays.

    Identical structure to ``write_csvs_scorpio`` except that the final delay
    computation subtracts 3600 seconds to correct for an additional one-hour
    timestamp discrepancy specific to the Orion-LD log format.

    Args:
        file_datetime (str): Date-time prefix identifying the raw log files.
        file_name (str): Base name used for all output files.

    Returns:
        str: Path to the written ``-delays.csv`` file.
    """
    dt = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S")

    mosquitto_logfile = "measures/orion_ld/measures/" + file_datetime + "-mosquitto"
    things_logfile = "measures/orion_ld/measures/" + file_datetime + "-entities"
    output_csv_things = f"measures/orion_ld/measures_csv/{file_name}-entities.csv"
    output_csv_mosquitto = f"measures/orion_ld/measures_csv/{file_name}-mosquitto.csv"
    result_file = "measures/orion_ld/results/" + file_name + "-delays.csv"

    os.makedirs("measures/orion_ld/measures_csv", exist_ok=True)

    # --- Parse the Orion-LD entities log (broker receive events) ---
    occurrence = {}
    with open(things_logfile, "r") as f, open(output_csv_things, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurrence"])
        for line in f:
            if "with apiKey apikey123 successfully updated" in line:
                timestamp = line[5:28].replace("T", "_").replace(":", "-")
                ts = datetime.strptime(timestamp, "%Y-%m-%d_%H-%M-%S.%f") + timedelta(hours=2)
                timestamp = ts.strftime("%Y-%m-%d_%H-%M-%S.%f")
                if ts >= dt:
                    thing_id = "urn:ngsi-ld:RoadSegment:RoadSegment" + line.split("TrafficFlowSensor")[1].split(" ")[0]
                    occurrence[thing_id] = occurrence.get(thing_id, 0) + 1
                    writer.writerow([timestamp, thing_id, occurrence[thing_id]])

    # --- Parse the Mosquitto log (MQTT send events) ---
    occurrence = {}
    with open(mosquitto_logfile, "r") as f, open(output_csv_mosquitto, "w", newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["timestamp", "thing_id", "occurrence"])
        for line in f:
            if "/json/apikey123/TrafficFlowSensor" in line:
                timestamp = line[:23].replace("T", "_").replace(":", "-")
                if datetime.strptime(timestamp[:19], "%Y-%m-%d_%H-%M-%S") >= dt:
                    thing_id = "urn:ngsi-ld:RoadSegment:RoadSegment" + line.split("TrafficFlowSensor")[1].split(" ")[0]
                    occurrence[thing_id] = occurrence.get(thing_id, 0) + 1
                    writer.writerow([timestamp, thing_id, occurrence[thing_id]])

    mosquitto_messages = {}
    with open(output_csv_mosquitto, newline='') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sent_time, thing_id, occurrence = row[0], row[1], int(row[2])
            mosquitto_messages[(thing_id, occurrence)] = parse_time(sent_time)

    things_messages = {}
    with open(output_csv_things, newline='') as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            sent_time, thing_id, occurrence = row[0], row[1], int(row[2])
            things_messages[(thing_id, occurrence)] = parse_time(sent_time)

    delays = []
    with open(result_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["sent_timestamp", "message_id", "delay (s)"])

        for (thing_id, occurrence) in mosquitto_messages:
            message_id = str(occurrence) + "_" + thing_id
            if (thing_id, occurrence) in things_messages:
                # Subtract 3600 s to correct for the extra hour offset in Orion-LD timestamps.
                delay = round((things_messages[(thing_id, occurrence)] - mosquitto_messages[
                    (thing_id, occurrence)]).total_seconds() - 3600, 3)
                delays.append(delay)
            else:
                delay = "Error, msg not received or log wasn't captured."
            writer.writerow([mosquitto_messages[(thing_id, occurrence)], message_id, delay])

    return result_file


def write_csv_lambdas(file_datetime, dt_solution, file_name, lambdas_list):
    """Write the MMPP lambda change log to a CSV file.

    Each row records the second at which the MMPP transitioned to a new state
    and the lambda (arrival rate) of that new state.

    Args:
        file_datetime (str): Unused; kept for API consistency.
        dt_solution (str): Broker name, used to build the output path.
        file_name (str): Base name for the output file.
        lambdas_list (list[tuple[int, float]]): List of ``(second, lambda)``
            tuples as returned by ``generate_mmpp_lambda_timestamps``.
    """
    result_file = "measures/" + dt_solution + "/results/" + file_name + "-lambdas_list.csv"
    with open(result_file, "w") as f:
        writer = csv.writer(f)
        writer.writerow(["change_timestamp", "lambda"])
        for line in lambdas_list:
            writer.writerow(line)
