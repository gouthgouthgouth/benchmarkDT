import atexit
import os
import signal
from datetime import datetime, timezone, timedelta
from multiprocessing import Process
from scripts.sensor_measurements_simulator import send_messages_uniformlaw
from twins_to_compare.eclipse_ditto.eclipse_utils import *
from scripts.utils import get_road_segments_from_json
from twins_to_compare.fiware.fiware_utils import (create_road_segments_and_sensors)
from twins_to_compare.scripts_for_measures.get_logs import record_logs_mosquitto, \
    record_logs_cpu_ram_delay
from twins_to_compare.scripts_for_measures.plot import plot_courbe_delay, plot_courbe_cpuram
from twins_to_compare.scripts_for_measures.write_csvs import write_csvs

# Nombre d'entités
nb_entities = 50
# Durée des mesures
nb_seconds = 1
# Fréquence d'envoi des messages MQTT
average_frequency = 1

#Loading entities
input_file_json = "data/road_segments_from_csv.json"
road_segments_fiware = get_road_segments_from_json(input_file_json, number_required=nb_entities)
ditto_things = transform_jsonld_to_ditto(input_file_json, number_required=nb_entities)

def create_entities(dt_solution, entities):
    if dt_solution == "ditto":
        print_time("Creating things...")
        eclipse_create_things(entities)
        print_time("Things created.")
    elif dt_solution == "scorpio":
        print_time("Creating entities...")
        create_road_segments_and_sensors(entities)
        print_time("Entities created.")


def cleanup(pid_list, mosquitto_process):
    print_time(f"Cleaning up processes {pid_list}, and mosquitto...")
    for pid in pid_list:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    if mosquitto_process.is_alive():
        mosquitto_process.terminate()
        mosquitto_process.join()
    print_time("Cleanup done.")


if __name__ == "__main__":
    # dt_solution = "ditto"
    # entities = ditto_things
    dt_solution = "scorpio"
    entities = road_segments_fiware

    # Creating entities
    # create_entities(dt_solution=dt_solution, entities=entities)

    # Starting to record logs for context broker and mosquitto
    file_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    pid_list = record_logs_cpu_ram_delay(file_datetime, dt_solution=dt_solution)
    mosquitto_process = Process(target=record_logs_mosquitto, args=(file_datetime, "scorpio"))
    mosquitto_process.start()
    atexit.register(cleanup, pid_list, mosquitto_process)

    print_time("Running tests...")
    start_time = datetime.now(timezone.utc) + timedelta(seconds=5)
    # p1, p2, p3 = None, None, None
    p1 = Process(target=send_messages_uniformlaw,
                 kwargs={"devices": entities,
                         "dt_solution": dt_solution,
                         "nb_entities": nb_entities,
                         "msg_frequency_hz": average_frequency,
                         "nb_seconds": nb_seconds,
                         "start_time": start_time})
    # p2 = Process(target=send_messages_poissonlaw,
    #              kwargs={"things": ditto_things, "poisson_lambda": average_frequency, "nb_seconds": nb_seconds,
    #                      "start_time": start_time})
    # p3 = Process(target=send_messages_gaussianlaw,
    #              kwargs={"things": ditto_things, "nb_messages": average_frequency * nb_seconds,
    #                      "nb_seconds": nb_seconds, "center_ratio": 0.5, "sigma_ratio": 0.1, "start_time": start_time})


    p1.start()
    # p2.start()
    # p3.start()
    p1.join()
    # p2.join()
    # p3.join()
    time.sleep(1)

    print_time("Writing csvs and doing plots...")
    write_csvs(file_datetime, dt_solution=dt_solution)
    plot_courbe_delay(file_datetime, beginning=start_time, dt_solution=dt_solution)
    plot_courbe_cpuram(file_datetime, beginning=start_time, dt_solution=dt_solution)