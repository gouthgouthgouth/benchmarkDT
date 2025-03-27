import atexit
import os
import signal
import time
from datetime import datetime, timezone, timedelta
from multiprocessing import Process
from scripts.sensor_measurements_simulator import send_messages_uniformlaw, send_messages_poissonlaw, \
    send_messages_gaussianlaw
from twins_to_compare.eclipse_ditto.eclipse_utils import *
from scripts.utils import get_road_segments_from_json
from twins_to_compare.scorpio.scorpio_utils import (create_road_segments_and_sensors)
from twins_to_compare.scripts_for_measures.get_logs import record_logs_mosquitto, \
    record_logs_cpu_ram_delay
from twins_to_compare.scripts_for_measures.plot import plot_courbe_delay, plot_courbe_cpuram
from twins_to_compare.scripts_for_measures.write_csvs import write_csvs

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

def make_measurements(dt_solution, create_entities_before_measures=False, nb_seconds=60, uniform_law_enabled=False, unif_frequency=10,
                      poisson_law_enabled=False, poisson_lambda=10, gaussianlaw_enabled=False, gauss_nbmessages=100,
                      center_ratio=0.5, sigma_ratio=0.1):
    input_file_json = "data/road_segments_from_csv.json"
    entities = []
    if dt_solution == "ditto":
        entities = transform_jsonld_to_ditto(input_file_json, number_required=nb_entities)
    elif dt_solution == "scorpio":
        entities = get_road_segments_from_json(input_file_json, number_required=nb_entities)
    if create_entities_before_measures:
        create_entities(dt_solution=dt_solution, entities=entities)

    # Starting to record logs for context broker and mosquitto
    file_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    pid_list = record_logs_cpu_ram_delay(file_datetime, dt_solution=dt_solution)
    mosquitto_process = Process(target=record_logs_mosquitto, args=(file_datetime, dt_solution))
    mosquitto_process.start()
    atexit.register(cleanup, pid_list, mosquitto_process)

    print_time("Running tests...")
    start_time = datetime.now(timezone.utc) + timedelta(seconds=60)

    processes = []

    if uniform_law_enabled:
        p1 = Process(target=send_messages_uniformlaw,
                     kwargs={"devices": entities,
                             "dt_solution": dt_solution,
                             "msg_frequency_hz": unif_frequency,
                             "nb_seconds": nb_seconds,
                             "start_time": start_time})
        processes.append(p1)
    if poisson_law_enabled:
        p2 = Process(target=send_messages_poissonlaw,
                     kwargs={"devices": entities,
                             "dt_solution": dt_solution,
                             "poisson_lambda": poisson_lambda,
                             "nb_seconds": nb_seconds,
                             "start_time": start_time})
        processes.append(p2)
    if gaussianlaw_enabled:
        p3 = Process(target=send_messages_gaussianlaw,
                     kwargs={"devices": entities,
                             "dt_solution": dt_solution,
                             "nb_messages": gauss_nbmessages,
                             "nb_seconds": nb_seconds,
                             "start_time": start_time,
                             "center_ratio": center_ratio,
                             "sigma_ratio": sigma_ratio})
        processes.append(p3)

    for p in processes:
        p.start()
    for p in processes:
        p.join()
    time.sleep(60)

    file_name = f"{file_datetime}_{dt_solution}_{nb_entities}entities_{nb_seconds}seconds"

    if uniform_law_enabled:
        file_name += f"_poissonlaw_frequency{unif_frequency}"
    if poisson_law_enabled:
        file_name += f"_poissonlaw_lambda{poisson_lambda}"
    if gaussianlaw_enabled:
        file_name += f"_gausslaw_{gauss_nbmessages}nbmessages_center{center_ratio}_sigma{sigma_ratio}"

    print_time("Writing csvs and doing plots...")
    write_csvs(file_datetime, dt_solution=dt_solution, file_name=file_name)
    plot_courbe_delay(file_name, beginning=start_time, dt_solution=dt_solution)
    plot_courbe_cpuram(file_name, beginning=start_time, dt_solution=dt_solution)



if __name__ == "__main__":
    dt_solution = "ditto"
    # dt_solution = "scorpio"

    # Nombre d'entités
    nb_entities = 500
    # Durée des mesures
    nb_seconds = 60

    time.sleep(120)

    make_measurements(dt_solution,
                      create_entities_before_measures=False,
                      nb_seconds=nb_seconds,

                      uniform_law_enabled=True,
                      unif_frequency=10,

                      poisson_law_enabled=False,
                      poisson_lambda=10,

                      gaussianlaw_enabled=False,
                      gauss_nbmessages=100,
                      center_ratio=0.5,
                      sigma_ratio=0.1)

    time.sleep(10)

    make_measurements(dt_solution,
                      create_entities_before_measures=False,
                      nb_seconds=nb_seconds,

                      uniform_law_enabled=True,
                      unif_frequency=20,

                      poisson_law_enabled=False,
                      poisson_lambda=10,

                      gaussianlaw_enabled=False,
                      gauss_nbmessages=100,
                      center_ratio=0.5,
                      sigma_ratio=0.1)

    time.sleep(10)

    make_measurements(dt_solution,
                      create_entities_before_measures=False,
                      nb_seconds=nb_seconds,

                      uniform_law_enabled=True,
                      unif_frequency=30,

                      poisson_law_enabled=False,
                      poisson_lambda=10,

                      gaussianlaw_enabled=False,
                      gauss_nbmessages=100,
                      center_ratio=0.5,
                      sigma_ratio=0.1)
