import atexit
import os
import signal
import time
from datetime import datetime, timedelta, timezone
from multiprocessing import Process
from scripts.sensor_measurements_simulator import send_messages_uniformlaw, send_messages_poissonlaw, \
    send_messages_gaussianlaw
from twins_to_compare.eclipse_ditto.eclipse_utils import *
from scripts.utils import get_road_segments_from_json
from twins_to_compare.scorpio.scorpio_utils import scorpio_create_road_segments_and_sensors
from twins_to_compare.orion_ld.orion_ld_utils import orion_create_road_segments_and_sensors
from twins_to_compare.stellio.stellio_utils import stellio_create_road_segments_and_sensors
from twins_to_compare.scripts_for_measures.get_logs import record_logs_mosquitto, \
    record_logs_cpu_ram_delay
from twins_to_compare.scripts_for_measures.plot import plot_courbe_delay, plot_courbe_cpuram
from twins_to_compare.scripts_for_measures.write_csvs import write_csvs, write_csvs_scorpio, write_csvs_ditto

tz = timezone(timedelta(hours=2))

def create_entities(dt_solution, entities):
    if dt_solution == "ditto":
        print_time("Creating things...")
        eclipse_create_things(entities)
        print_time("Things created.")
    elif dt_solution == "scorpio":
        print_time("Creating entities...")
        scorpio_create_road_segments_and_sensors(entities)
        print_time("Entities created.")
    elif dt_solution == "orion_ld":
        print_time("Creating entities...")
        orion_create_road_segments_and_sensors(entities)
        print_time("Entities created.")
    elif dt_solution == "stellio":
        print_time("Creating entities...")
        stellio_create_road_segments_and_sensors(entities)
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

def make_measurements(dt_solution, nb_entities, create_entities_before_measures=False, nb_seconds=60, uniform_law_enabled=False, unif_frequency=10,
                      poisson_law_enabled=False, poisson_lambda=10, gaussianlaw_enabled=False, gauss_nbmessages=100,
                      center_ratio=0.5, sigma_ratio=0.1):
    input_file_json = "data/road_segments_from_csv.json"
    entities = []
    if dt_solution == "ditto":
        entities = transform_jsonld_to_ditto(input_file_json, number_required=nb_entities)
    elif dt_solution == "scorpio" or dt_solution == "orion_ld" or dt_solution == "stellio":
        entities = get_road_segments_from_json(input_file_json, number_required=nb_entities)
    if create_entities_before_measures:
        create_entities(dt_solution=dt_solution, entities=entities)

    # sending test messages
    send_messages_uniformlaw(entities, dt_solution, msg_frequency_hz=6, nb_seconds=round(len(entities)/5) + 5, start_time=datetime.now(tz=tz) + timedelta(seconds=1))
    time.sleep(10)
    # Starting to record logs for context broker and mosquitto
    file_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    print_time("File datetime : " + file_datetime)
    pid_list = record_logs_cpu_ram_delay(file_datetime, dt_solution=dt_solution)
    mosquitto_process = Process(target=record_logs_mosquitto, args=(file_datetime, dt_solution))
    mosquitto_process.start()
    atexit.register(cleanup, pid_list, mosquitto_process)

    print_time("Running tests...")
    start_time = datetime.now(tz=tz) + timedelta(seconds=5)

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

    if unif_frequency > 20:
        time.sleep(unif_frequency * nb_seconds / 10)
    else:
        time.sleep(10)

    file_name = f"{file_datetime}_{dt_solution}_{nb_entities}entities_{nb_seconds}seconds"

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
    write_csvs(file_datetime, dt_solution=dt_solution, file_name=file_name)
    plot_courbe_delay(file_name, beginning=start_time, dt_solution=dt_solution)
    plot_courbe_cpuram(file_datetime, file_name, beginning=start_time, dt_solution=dt_solution)



if __name__ == "__main__":
    dt_solution = "ditto"
    # dt_solution = "scorpio"
    # dt_solution = "orion_ld"
    # dt_solution = "stellio"

    # Nombre d'entités
    # nb_entities = 10
    # Durée des mesures
    nb_seconds = 300

    time.sleep(120)


    for nb_entities in range(35, 101, 5):

        f = nb_entities

        make_measurements(dt_solution,
                          create_entities_before_measures=True,
                          nb_entities=nb_entities,
                          nb_seconds=nb_seconds,
                          uniform_law_enabled=True,
                          unif_frequency=f)


    # make_measurements(dt_solution,
    #                   create_entities_before_measures=False,
    #                   nb_seconds=nb_seconds,
    #
    #                   uniform_law_enabled=True,
    #                   unif_frequency=50,
    #
    #                   poisson_law_enabled=False,
    #                   poisson_lambda=10,
    #
    #                   gaussianlaw_enabled=True,
    #                   gauss_nbmessages=2000,
    #                   center_ratio=0.5,
    #                   sigma_ratio=0.1)
