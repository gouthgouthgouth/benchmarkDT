"""
Main entry point for the benchmarkDT benchmark.

Orchestrates a full measurement run: starts the chosen Digital Twin broker via
Docker Compose, provisions entities, sends test traffic, records logs, computes
delays, generates plots, then tears down the broker.

The ``make_measurements`` function can be called with any combination of
statistical arrival laws (uniform, Poisson, Gaussian, MMPP). The ``__main__``
block at the bottom defines the concrete experiment parameters.
"""
import atexit
import os
import signal
import subprocess
import time
from datetime import datetime, timedelta, timezone
from multiprocessing import Process, Queue
from benchmark.simulator import send_messages_uniformlaw, send_messages_poissonlaw, \
    send_messages_gaussianlaw, send_messages_mmpp
from brokers.eclipse_ditto.eclipse_utils import eclipse_create_things, transform_jsonld_to_ditto, print_time
from benchmark.utils import get_road_segments_from_json
from brokers.scorpio.scorpio_utils import scorpio_create_road_segments_and_sensors
from brokers.orion_ld.orion_ld_utils import orion_create_road_segments_and_sensors
from benchmark.get_logs import record_logs_mosquitto, \
    record_logs_cpu_ram_delay
from benchmark.plot import plot_courbe_delay, plot_courbe_cpuram
from benchmark.write_csvs import write_csvs
import numpy as np

tz = timezone(timedelta(hours=2))


def create_entities(dt_solution, entities, nb_attributes, logs=False):
    """Provision the required entities in the running broker.

    Dispatches to the appropriate broker adapter based on ``dt_solution``.
    For Scorpio an extra 60-second wait is inserted to allow the IoT Agent
    to finish initialising.

    Args:
        dt_solution (str): One of ``"ditto"``, ``"scorpio"``, or ``"orion_ld"``.
        entities (list[dict]): Entity/Thing descriptors to create.
        nb_attributes (int): Number of sensor attributes to provision per entity.
        logs (bool): If True, enable verbose logging in the broker adapter.

    Returns:
        bool: True if all entities were created successfully.
    """
    entities_created = False
    print_time("ℹ️ Creating entities...")
    if dt_solution == "ditto":
        entities_created = eclipse_create_things(entities, logs=logs)
    elif dt_solution == "scorpio":
        time.sleep(60)
        entities_created = scorpio_create_road_segments_and_sensors(entities, nb_attributes=nb_attributes, logs=logs)
    elif dt_solution == "orion_ld":
        entities_created = orion_create_road_segments_and_sensors(entities, nb_attributes=nb_attributes, logs=logs)
    return entities_created


def cleanup(pid_list, mosquitto_process):
    """Terminate all background logging processes.

    Registered with ``atexit`` so it runs even if the benchmark is interrupted.

    Args:
        pid_list (tuple[int, int]): PIDs of the broker and CPU/RAM log scripts.
        mosquitto_process (multiprocessing.Process): The MQTT logger process.
    """
    print_time(f"ℹ️ Cleaning up processes {pid_list}, and mosquitto...")
    for pid in pid_list:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
    if mosquitto_process.is_alive():
        mosquitto_process.terminate()
        mosquitto_process.join()
    print_time("✔️ Cleanup done.")


def stop_dt_solution(logs=False):
    """Stop all Docker containers using the infrastructure teardown script.

    Args:
        logs (bool): If True, print container output to stdout.
    """
    print_time("ℹ️ Stopping containers...")
    script_path = "infrastructure/cleardocker.sh"
    if logs:
        subprocess.run(["bash", script_path], check=True)
    else:
        subprocess.run(
            ["bash", script_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    print_time("✔️ Containers stopped.")


def start_dt_solution(dt_solution, logs=False):
    """Start the broker's Docker Compose stack and wait until it is healthy.

    Reads stdout from the startup script line by line and stops waiting as soon
    as the "All containers are running." sentinel is detected.

    Args:
        dt_solution (str): One of ``"ditto"``, ``"scorpio"``, or ``"orion_ld"``.
        logs (bool): If True, show stderr output from the startup script.
    """
    if dt_solution == "ditto":
        script_path = "brokers/eclipse_ditto/run_ditto.sh"
    elif dt_solution == "scorpio":
        script_path = "brokers/scorpio/run_scorpio.sh"
    elif dt_solution == "orion_ld":
        script_path = "brokers/orion_ld/run_orion_ld.sh"
    print_time("ℹ️ starting " + dt_solution + "...")
    if logs:
        proc = subprocess.Popen(
            ["bash", script_path],
            stdout=subprocess.PIPE,
            text=True
        )
    else:
        proc = subprocess.Popen(
            ["bash", script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
    time.sleep(1)
    for line in proc.stdout:
        if "All containers are running." in line:
            print_time("✔️ Containers are up, continuing in 5s...")
            break
        elif "is now healthy" in line:
            print_time("✔️ " + line, end="")
    time.sleep(10)


def make_measurements(dt_solution, nb_entities, create_entities_before_measures=False, nb_seconds=60,

                      # Parameters for sending messages with various laws
                      uniform_law_enabled=False, unif_frequency=10,
                      mmpp_enabled=False, lambdas=[0.1, 1, 3], P=np.array([[0.99, 0.01, 0.0], [0.005, 0.99, 0.005], [0.0, 0.01, 0.99]]),
                      poisson_law_enabled=False, poisson_lambda=10,
                      gaussianlaw_enabled=False, gauss_nbmessages=100, center_ratio=0.5, sigma_ratio=0.1,

                      nb_attributes=2, bytes_per_attribute=5, logs=False):
    """Run a complete benchmark measurement cycle for a single configuration.

    Lifecycle:
    1. Stop any running containers, start the target broker.
    2. Optionally provision entities.
    3. Send a short warm-up burst via the uniform law.
    4. Start background log recorders (MQTT + CPU/RAM).
    5. Launch the requested arrival-law processes in parallel.
    6. Wait for all senders to finish, then write CSVs and generate plots.
    7. Stop the broker.

    At least one of the ``*_enabled`` flags must be True for any traffic to be
    sent during the measurement window.

    Args:
        dt_solution (str): Broker to benchmark (``"ditto"``, ``"scorpio"``, or ``"orion_ld"``).
        nb_entities (int): Number of entities to create or target.
        create_entities_before_measures (bool): If True, provision entities at the start.
        nb_seconds (int): Duration of the measurement window in seconds.
        uniform_law_enabled (bool): Enable uniform-rate sender.
        unif_frequency (float): Send rate in Hz for the uniform law.
        mmpp_enabled (bool): Enable MMPP sender.
        lambdas (list[float]): Arrival rates for each MMPP Markov state.
        P (np.ndarray): MMPP transition matrix.
        poisson_law_enabled (bool): Enable Poisson sender.
        poisson_lambda (float): Mean arrival rate for the Poisson law.
        gaussianlaw_enabled (bool): Enable Gaussian sender.
        gauss_nbmessages (int): Number of messages to schedule for the Gaussian law.
        center_ratio (float): Gaussian centre as a fraction of ``nb_seconds``.
        sigma_ratio (float): Gaussian sigma as a fraction of ``nb_seconds``.
        nb_attributes (int): Number of attributes per entity payload.
        bytes_per_attribute (int): Byte size of each attribute value.
        logs (bool): If True, enable verbose logging throughout.

    Returns:
        str | None: Path to the ``-delays.csv`` result file.
    """
    stop_dt_solution(logs=False)
    start_dt_solution(dt_solution, logs=logs)

    input_file_json = "data/road_segments_from_csv.json"
    entities = []
    if dt_solution == "ditto":
        entities = transform_jsonld_to_ditto(input_file_json, number_required=nb_entities)
    elif dt_solution == "scorpio" or dt_solution == "orion_ld":
        entities = get_road_segments_from_json(input_file_json, number_required=nb_entities)

    if create_entities_before_measures:
        entities_created = create_entities(dt_solution=dt_solution, entities=entities, nb_attributes=nb_attributes, logs=logs)
    else:
        entities_created = True

    if not entities_created:
        raise RuntimeError("✖️ Entities not created")
    else:
        print_time("✔️ Entities created")

    # Send a short warm-up burst so the broker is fully active before measurements start.
    print_time("ℹ️ Running tests...")
    send_messages_uniformlaw(entities, dt_solution, msg_frequency_hz=6, nb_seconds=round(len(entities)/5) + 10, start_time=datetime.now(tz=tz) + timedelta(seconds=1), nb_attributes=nb_attributes, bytes_per_attribute=bytes_per_attribute)
    time.sleep(5)

    # Start background log recorders; their PIDs are saved for cleanup.
    file_datetime = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    print_time("ℹ️ File datetime : " + file_datetime)
    pid_list = record_logs_cpu_ram_delay(file_datetime, dt_solution=dt_solution)
    mosquitto_process = Process(target=record_logs_mosquitto, args=(file_datetime, dt_solution))
    mosquitto_process.start()
    atexit.register(cleanup, pid_list, mosquitto_process)

    # Schedule the measurement window to start 5 seconds from now.
    start_time = datetime.now(tz=tz) + timedelta(seconds=5)
    print_time(f"ℹ️ Starting the measurements")
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
    if mmpp_enabled:
        q = Queue()
        p1 = Process(target=send_messages_mmpp,
                     kwargs={"devices": entities,
                             "dt_solution": dt_solution,
                             "lambdas": lambdas,
                             "P": P,
                             "nb_seconds": nb_seconds,
                             "start_time": start_time,
                             "nb_attributes": nb_attributes,
                             "bytes_per_attribute": bytes_per_attribute,
                             "queue": q})
        processes.append(p1)
    if poisson_law_enabled:
        p2 = Process(target=send_messages_poissonlaw,
                     kwargs={"devices": entities,
                             "dt_solution": dt_solution,
                             "poisson_lambda": poisson_lambda,
                             "nb_seconds": nb_seconds,
                             "start_time": start_time,
                             "nb_attributes": nb_attributes,
                             "bytes_per_attribute": bytes_per_attribute})
        processes.append(p2)
    if gaussianlaw_enabled:
        p3 = Process(target=send_messages_gaussianlaw,
                     kwargs={"devices": entities,
                             "dt_solution": dt_solution,
                             "nb_messages": gauss_nbmessages,
                             "nb_seconds": nb_seconds,
                             "start_time": start_time,
                             "nb_attributes": nb_attributes,
                             "bytes_per_attribute": bytes_per_attribute,
                             "center_ratio": center_ratio,
                             "sigma_ratio": sigma_ratio})
        processes.append(p3)

    for p in processes:
        p.start()
    for p in processes:
        p.join()

    if mmpp_enabled:
        lambdas_list = q.get()
        print("lambdas_list :", lambdas_list)
    else:
        lambdas_list = None

    time.sleep(10)

    # Build a descriptive file stem that encodes all experiment parameters.
    file_name = f"{file_datetime}_{dt_solution}_{nb_entities}entities_{nb_seconds}seconds_{nb_attributes}attr_{bytes_per_attribute}bpa"
    if uniform_law_enabled:
        file_name += f"_uniformlaw_frequency{unif_frequency}"
    if poisson_law_enabled:
        file_name += f"_poissonlaw_lambda{poisson_lambda}"
    if gaussianlaw_enabled:
        file_name += f"_gausslaw_{gauss_nbmessages}nbmessages_center{center_ratio}_sigma{sigma_ratio}"
    if mmpp_enabled:
        file_name += "_mmpp_lambdas_"
        lambdas_str = ""
        for lambdas_val in lambdas:
            lambdas_str += f"{lambdas_val}-"
        lambdas_str = lambdas_str[:-1]
        file_name += lambdas_str

    print_time("ℹ️ Writing csvs and doing plots...")
    csv_files = write_csvs(file_datetime, dt_solution=dt_solution, file_name=file_name, lambdas_list=lambdas_list)
    plot_courbe_delay(file_name, beginning=start_time, dt_solution=dt_solution)
    plot_courbe_cpuram(file_datetime, file_name, beginning=start_time, dt_solution=dt_solution)
    stop_dt_solution(logs=logs)
    return csv_files


if __name__ == "__main__":
    # Experiment parameters
    nb_seconds = 3600 * 5
    frequency = 1
    num_attributes = 5
    bytes_per_attribute = 5

    # Sweep over brokers, entity counts, and MMPP lambda sets.
    for dt_solution in ["ditto", "orion_ld"]:
        for num_entities in [5]:
            for lambdas_set in ([5, 10, 20], [10, 20, 40], [20, 40, 80]):
                try:
                    csv_delay_files = make_measurements(dt_solution,
                                                           create_entities_before_measures=True,
                                                           nb_entities=num_entities,
                                                           nb_seconds=nb_seconds,
                                                           mmpp_enabled=True,
                                                           lambdas=lambdas_set,
                                                           P=np.array([[0.998, 0.002, 0],
                                                                   [0.001, 0.998, 0.001],
                                                                   [0, 0.002, 0.998]]),
                                                           nb_attributes=num_attributes,
                                                           bytes_per_attribute=bytes_per_attribute,
                                                           logs=False)
                except:
                    # Retry with a tighter transition matrix if the first attempt fails.
                    try:
                        csv_delay_files = make_measurements(dt_solution,
                                                           create_entities_before_measures=True,
                                                           nb_entities=num_entities,
                                                           nb_seconds=nb_seconds,
                                                           mmpp_enabled=True,
                                                           lambdas=lambdas_set,
                                                           P=np.array([[0.999, 0.001, 0],
                                                                   [0.0005, 0.999, 0.0005],
                                                                   [0, 0.001, 0.999]]),
                                                           nb_attributes=num_attributes,
                                                           bytes_per_attribute=bytes_per_attribute,
                                                           logs=False)
                    except:
                        pass
