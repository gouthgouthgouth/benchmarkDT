import atexit
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta, timezone
from multiprocessing import Process
from scripts.sensor_measurements_simulator import send_messages_uniformlaw, send_messages_poissonlaw, \
    send_messages_gaussianlaw
from twins_to_compare.eclipse_ditto.eclipse_utils import *
from scripts.utils import get_road_segments_from_json
from twins_to_compare.scorpio.scorpio_utils import scorpio_create_road_segments_and_sensors, scorpio_delete_road_segments_and_sensors, scorpio_subscribe_notifications
from twins_to_compare.orion_ld.orion_ld_utils import orion_create_road_segments_and_sensors, orion_delete_road_segments_and_sensors, orion_subscribe_notifications
from twins_to_compare.stellio.stellio_utils import stellio_create_road_segments_and_sensors, stellio_delete_road_segments_and_sensors, stellio_subscribe_notifications
from twins_to_compare.scripts_for_measures.get_logs import record_logs_mosquitto, \
    record_logs_cpu_ram_delay
from twins_to_compare.scripts_for_measures.plot import plot_courbe_delay, plot_courbe_cpuram
from twins_to_compare.scripts_for_measures.write_csvs import write_csvs, write_csvs_scorpio, write_csvs_ditto, \
    log_not_captured_in_csv

tz = timezone(timedelta(hours=2))

def create_entities(dt_solution, entities, nb_attributes):
    if dt_solution == "ditto":
        print_time("Creating things...")
        eclipse_create_things(entities)
        print_time("Things created.")
    elif dt_solution == "scorpio":
        print_time("Creating entities...")
        scorpio_create_road_segments_and_sensors(entities, nb_attributes=nb_attributes)
        print_time("Entities created.")
    elif dt_solution == "orion_ld":
        print_time("Creating entities...")
        orion_create_road_segments_and_sensors(entities, nb_attributes=nb_attributes)
        print_time("Entities created.")
    elif dt_solution == "stellio":
        print_time("Creating entities...")
        stellio_create_road_segments_and_sensors(entities)
        print_time("Entities created.")

def subscribe_notifications(dt_solution, entities):
    if dt_solution == "ditto":
        print_time("Subscribing to notifications...")
        eclipse_subscribe_notifications(entities)
        print_time("Subscribed.")
    elif dt_solution == "scorpio":
        print_time("Subscribing to notifications...")
        scorpio_subscribe_notifications()
        print_time("Subscribed.")
    elif dt_solution == "orion_ld":
        print_time("Subscribing to notifications...")
        orion_subscribe_notifications()
        print_time("Subscribed.")
    elif dt_solution == "stellio":
        print_time("Subscribing to notifications...")
        stellio_subscribe_notifications()
        print_time("Subscribed.")

def delete_entities(dt_solution, entities):
    if dt_solution == "ditto":
        print_time("Deleting things...")
        eclipse_delete_things(entities)
        print_time("Things deleted.")
    elif dt_solution == "scorpio":
        print_time("Deleting entities...")
        scorpio_delete_road_segments_and_sensors(entities)
        print_time("Entities deleted.")
    elif dt_solution == "orion_ld":
        print_time("Deleting entities...")
        orion_delete_road_segments_and_sensors(entities)
        print_time("Entities deleted.")
    elif dt_solution == "stellio":
        print_time("Deleting entities...")
        stellio_delete_road_segments_and_sensors(entities)
        print_time("Entities deleted.")


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

def stop_dt_solution():
    print_time("Stopping containers...")
    for script_path in ["twins_to_compare/eclipse_ditto/cleardocker.sh", "twins_to_compare/scorpio/cleardocker.sh", "twins_to_compare/orion_ld/cleardocker.sh"]:
        subprocess.run(["bash", script_path], check=True)
    print_time("Containers stopped.")

def start_dt_solution(dt_solution):
    if dt_solution == "ditto":
        script_path = "twins_to_compare/eclipse_ditto/run_ditto.sh"
    elif dt_solution == "scorpio":
        script_path = "twins_to_compare/scorpio/run_scorpio.sh"
    elif dt_solution == "orion_ld":
        script_path = "twins_to_compare/orion_ld/run_orion_ld.sh"
    print_time("starting " + dt_solution + "...")
    subprocess.Popen(["bash", script_path])
    time.sleep(300)

def make_measurements(dt_solution, nb_entities, create_entities_before_measures=False, nb_seconds=60, uniform_law_enabled=False, unif_frequency=10,
                      poisson_law_enabled=False, poisson_lambda=10, gaussianlaw_enabled=False, gauss_nbmessages=100,
                      center_ratio=0.5, sigma_ratio=0.1, nb_attributes=2, bytes_per_attribute=5, send_notification=False):
    stop_dt_solution()
    start_dt_solution(dt_solution)
    input_file_json = "data/road_segments_from_csv.json"
    entities = []
    if dt_solution == "ditto":
        entities = transform_jsonld_to_ditto(input_file_json, number_required=nb_entities)
    elif dt_solution == "scorpio" or dt_solution == "orion_ld" or dt_solution == "stellio":
        entities = get_road_segments_from_json(input_file_json, number_required=nb_entities)
    if create_entities_before_measures:
        create_entities(dt_solution=dt_solution, entities=entities, nb_attributes=nb_attributes)

    if send_notification:
        subscribe_notifications(dt_solution=dt_solution, entities=entities)

    # sending test messages
    print_time("Running tests...")
    send_messages_uniformlaw(entities, dt_solution, msg_frequency_hz=6, nb_seconds=round(len(entities)/5) + 10, start_time=datetime.now(tz=tz) + timedelta(seconds=1), nb_attributes=nb_attributes, bytes_per_attribute=bytes_per_attribute)
    time.sleep(5)
    # Starting to record logs for context broker and mosquitto
    file_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    print_time("File datetime : " + file_datetime)
    pid_list = record_logs_cpu_ram_delay(file_datetime, dt_solution=dt_solution)
    mosquitto_process = Process(target=record_logs_mosquitto, args=(file_datetime, dt_solution))
    mosquitto_process.start()
    atexit.register(cleanup, pid_list, mosquitto_process)

    start_time = datetime.now(tz=tz) + timedelta(seconds=5)
    print_time(f"Starting the measurements : {nb_entities} entities, {unif_frequency} frequency, {nb_attributes} attributes, {bytes_per_attribute} bytes per attribute.")
    processes = []

    if uniform_law_enabled:
        p1 = Process(target=send_messages_uniformlaw,
                     kwargs={"devices": entities,
                             "dt_solution": dt_solution,
                             "msg_frequency_hz": unif_frequency,
                             "nb_seconds": nb_seconds,
                             "start_time": start_time,
                             "nb_attributes": nb_attributes,
                             "bytes_per_attribute": bytes_per_attribute})
        processes.append(p1)
    # if poisson_law_enabled:
    #     p2 = Process(target=send_messages_poissonlaw,
    #                  kwargs={"devices": entities,
    #                          "dt_solution": dt_solution,
    #                          "poisson_lambda": poisson_lambda,
    #                          "nb_seconds": nb_seconds,
    #                          "start_time": start_time,
    #                          "nb_attributes": nb_attributes,
    #                          "bytes_per_attribute": bytes_per_attribute})
    #     processes.append(p2)
    # if gaussianlaw_enabled:
    #     p3 = Process(target=send_messages_gaussianlaw,
    #                  kwargs={"devices": entities,
    #                          "dt_solution": dt_solution,
    #                          "nb_messages": gauss_nbmessages,
    #                          "nb_seconds": nb_seconds,
    #                          "start_time": start_time,
    #                          "nb_attributes": nb_attributes,
    #                          "bytes_per_attribute": bytes_per_attribute,
    #                          "center_ratio": center_ratio,
    #                          "sigma_ratio": sigma_ratio})
    #     processes.append(p3)
    # if fullbufferlaw_enabled:
    #     p4 = Process(target=send_messages_fullbufferlaw,
    #                  kwargs={"devices": entities,
    #                          "dt_solution": dt_solution,
    #                          "nb_messages": gauss_nbmessages,
    #                          "nb_seconds": nb_seconds,
    #                          "start_time": start_time,
    #                          "center_ratio": center_ratio,
    #                          "sigma_ratio": sigma_ratio})
    #     processes.append(p4)

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    time.sleep(10)

    file_name = f"{file_datetime}_{dt_solution}_{nb_entities}entities_{nb_seconds}seconds_{nb_attributes}attr_{bytes_per_attribute}bpa"

    if uniform_law_enabled:
        file_name += f"_uniformlaw_frequency{unif_frequency}"
    if poisson_law_enabled:
        file_name += f"_poissonlaw_lambda{poisson_lambda}"
    if gaussianlaw_enabled:
        file_name += f"_gausslaw_{gauss_nbmessages}nbmessages_center{center_ratio}_sigma{sigma_ratio}"

    # file_datetime = "2025-04-02_10-13-01"
    # start_time = datetime.strptime(file_datetime, "%Y-%m-%d_%H-%M-%S").replace(tzinfo=tz) + timedelta(seconds=60)
    # # start_time.replace(tzinfo=tz)
    # file_name = f"{file_datetime}_{dt_solution}_{nb_entities}entities_{nb_seconds}seconds"

    print_time("Writing csvs and doing plots...")
    csv_delay_file = write_csvs(file_datetime, dt_solution=dt_solution, file_name=file_name)
    plot_courbe_delay(file_name, beginning=start_time, dt_solution=dt_solution)
    # plot_courbe_cpuram(file_datetime, file_name, beginning=start_time, dt_solution=dt_solution)
    delete_entities(dt_solution, entities)
    stop_dt_solution()
    return csv_delay_file


if __name__ == "__main__":
    #TODO Ajouter mesure à la sortie de l'IOT Agent

    # dt_solution = "ditto"
    # dt_solution = "scorpio"
    # dt_solution = "orion_ld"
    # dt_solution = "stellio"

    # Nombre d'entités
    nbe = 5
    # Durée des mesures
    nb_seconds = 10
    # Frequency
    frequency = 1
    # Number of attributes per entity
    nba = 5
    # Number of bytes per attribute
    bytes_per_attribute = 5

    for dt_solution in ["orion_ld"]:
        csv_delay_file = make_measurements(dt_solution,
                                           create_entities_before_measures=True,
                                           nb_entities=nbe,
                                           nb_seconds=nb_seconds,
                                           uniform_law_enabled=True,
                                           unif_frequency=nbe * frequency,
                                           nb_attributes=nba,
                                           bytes_per_attribute=bytes_per_attribute,
                                           send_notification=True)

    # nb_seconds = 300
    # for dt_solution in ["scorpio"]:
    #     try:
    #         current_step = 8000
    #         wanted_step = 1000
    #         found = False
    #         bytes_per_attribute = 60000
    #         while not found:
    #             csv_delay_file = make_measurements(dt_solution,
    #                                                create_entities_before_measures=True,
    #                                                nb_entities=nbe,
    #                                                nb_seconds=nb_seconds,
    #                                                uniform_law_enabled=True,
    #                                                unif_frequency=nbe * frequency,
    #                                                nb_attributes=nba,
    #                                                bytes_per_attribute=bytes_per_attribute)
    #             if log_not_captured_in_csv(csv_delay_file):
    #                 if current_step == wanted_step:
    #                     found = True
    #                 else:
    #                     bytes_per_attribute = bytes_per_attribute - current_step
    #                     if current_step // 2 <= wanted_step:
    #                         current_step = wanted_step
    #                     else:
    #                         current_step = current_step // 2
    #
    #             bytes_per_attribute = bytes_per_attribute + current_step
    #     except:
    #         pass
