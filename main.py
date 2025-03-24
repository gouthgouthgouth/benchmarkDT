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
from twins_to_compare.scripts_for_measures.ditto.create_csv_from_measures import write_csvs
from twins_to_compare.scripts_for_measures.ditto.get_logs import record_logs_ditto, record_logs_mosquitto
from twins_to_compare.scripts_for_measures.ditto.plot import plot_courbe_delay, plot_courbe_cpuram

input_file_json = "data/road_segments_from_csv.json"
road_segments_fiware = get_road_segments_from_json(input_file_json)

def cleanup(pid1, pid2, mosquitto_process):
    print(f"Cleaning up processes {pid1}, {pid2}, and mosquitto...")
    try:
        os.kill(pid1, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        os.kill(pid2, signal.SIGTERM)
    except ProcessLookupError:
        pass
    if mosquitto_process.is_alive():
        mosquitto_process.terminate()
        mosquitto_process.join()
    print("Cleanup done.")

if __name__ == "__main__":

    # Nombre d'entités
    nb_entities = 50
    # Durée des mesures
    nb_seconds = 50
    # Fréquence d'envoi des messages MQTT
    average_frequency = 20

    file_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    ditto_things = transform_jsonld_to_ditto(input_file_json, number_required=nb_entities)

    # print("Creating things...")
    # eclipse_create_things(ditto_things)
    # time.sleep(1)

    print("Recording...")
    pid1, pid2 = record_logs_ditto(file_datetime)
    mosquitto_process = Process(target=record_logs_mosquitto, args=(file_datetime,))
    mosquitto_process.start()
    time.sleep(1)

    # Enregistrer la fonction de nettoyage
    atexit.register(cleanup, pid1, pid2, mosquitto_process)

    print("Running tests...")

    start_time = datetime.now(timezone.utc) + timedelta(seconds=1)

    p1 = Process(target=send_messages_uniformlaw,
                 kwargs={"things": ditto_things, "msg_frequency_hz": average_frequency/2, "nb_seconds": nb_seconds,
                         "start_time": start_time})
    # p2 = Process(target=send_messages_poissonlaw,
    #              kwargs={"things": ditto_things, "poisson_lambda": average_frequency, "nb_seconds": nb_seconds,
    #                      "start_time": start_time})
    p3 = Process(target=send_messages_gaussianlaw,
                 kwargs={"things": ditto_things, "nb_messages": average_frequency * nb_seconds,
                         "nb_seconds": nb_seconds, "center_ratio": 0.5, "sigma_ratio": 0.1, "start_time": start_time})

    p1.start()
    # p2.start()
    p3.start()

    p1.join()
    # p2.join()
    p3.join()


    # input("entrez quand logs terminés")
    time.sleep(30)

    print("Writing csvs and doing plots...")

    write_csvs(file_datetime)
    plot_courbe_delay(file_datetime, beginning=start_time)
    plot_courbe_cpuram(file_datetime, beginning=start_time)