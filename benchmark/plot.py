"""
Plotting utilities for benchmark results.

Generates time-series plots of message end-to-end delays, CPU usage, and RAM
usage from the CSV files produced by ``write_csvs``. Plots are saved as PNG
files alongside the result CSVs.
"""
import pandas as pd
import matplotlib.pyplot as plt

from config.config import PROJECT_FOLDER


def plot_courbe_delay(file_datetime, beginning, dt_solution):
    """Plot message end-to-end delay over time and save the figure as a PNG.

    Reads the ``-delays.csv`` result file, aligns timestamps relative to the
    measurement start, and plots delay (in seconds) against elapsed time.

    Args:
        file_datetime (str): The result file stem (without the ``-delays.csv`` suffix).
        beginning (datetime): Timezone-aware datetime marking the start of the
            measurement window; used as the time origin on the X axis.
        dt_solution (str): Broker name (``"ditto"``, ``"scorpio"``, or ``"orion_ld"``).
            Used to locate the result file in the correct subdirectory.
    """
    result_file = f"{PROJECT_FOLDER}/measures/{dt_solution}/results/" + file_datetime + "-delays.csv"
    plt.close(fig='all')

    df = pd.read_csv(result_file)
    delays = df["delay (s)"].dropna()

    # Convert timestamps to timezone-aware datetimes, then shift to UTC+0 for
    # consistent arithmetic against the ``beginning`` reference point.
    df["sent_timestamp"] = pd.to_datetime(df["sent_timestamp"], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce', utc=True)
    df["sent_timestamp"] = df["sent_timestamp"] - pd.Timedelta(hours=2)
    df["sent_timestamp_seconds"] = (df["sent_timestamp"] - beginning).dt.total_seconds()

    df = df.dropna(subset=["delay (s)", "sent_timestamp"])

    plt.figure(figsize=(12, 6))
    plt.plot(df["sent_timestamp_seconds"], df["delay (s)"], marker='.', linestyle='-', label="Delays (s)")
    plt.xlabel("Message sent time")
    plt.ylabel("Delay (seconds)")
    plt.title("Delays of messages (thing reception - mosquitto send)")
    plt.grid(True)
    plt.legend()
    plt.gcf().autofmt_xdate()
    plt.savefig(f"{PROJECT_FOLDER}/measures/{dt_solution}/results/{file_datetime}-delays-plot.png")
    print(f"Plot saved as {dt_solution}/results/{file_datetime}-delays-plot.png")
    plt.close()


def plot_courbe_cpuram(file_datetime, file_name, beginning, dt_solution):
    """Plot CPU and RAM usage over time and save both figures as PNGs.

    Reads the ``-cpu_ram_sum`` log file produced by the resource monitoring
    script, aligns timestamps relative to the measurement start, and creates
    separate plots for CPU percentage and memory usage in MiB.

    Args:
        file_datetime (str): Date-time prefix used to locate the raw CPU/RAM log file.
        file_name (str): Full result file stem used to name the output PNG files.
        beginning (datetime): Timezone-aware datetime marking the start of the
            measurement window.
        dt_solution (str): Broker name used to locate files in the correct subdirectory.
    """
    result_file = f"{PROJECT_FOLDER}/measures/{dt_solution}/measures/{file_datetime}-cpu_ram_sum"

    df = pd.read_csv(result_file)

    # Align timestamps to UTC+0 and convert to seconds elapsed since measurement start.
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce', utc=True)
    df["Timestamp"] = df["Timestamp"] - pd.Timedelta(hours=2)
    df["timestamp_seconds"] = (df["Timestamp"] - beginning).dt.total_seconds()
    # Discard samples recorded before the measurement window started.
    df = df[df["timestamp_seconds"] > 0]

    plt.figure(figsize=(12, 6))
    plt.plot(df["timestamp_seconds"], df[" CPU%"], marker='.', linestyle='-', label="CPU%")
    plt.xlabel("Time (s)")
    plt.ylabel("CPU %")
    plt.title("CPU usage over time")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{PROJECT_FOLDER}/measures/{dt_solution}/results/{file_name}-cpu-plot.png")
    print(f"CPU plot saved as {dt_solution}/{file_name}-cpu-plot.png")

    plt.figure(figsize=(12, 6))
    plt.plot(df["timestamp_seconds"], df[" MemUsageMiB"], marker='.', linestyle='-', label="Memory usage (MiB)")
    plt.xlabel("Time (s)")
    plt.ylabel("Memory usage (MiB)")
    plt.title("RAM usage over time")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"{PROJECT_FOLDER}/measures/{dt_solution}/results/{file_name}-ram-plot.png")
    print(f"RAM plot saved as {dt_solution}/{file_name}-ram-plot.png")
    plt.close()
