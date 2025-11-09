import pandas as pd
import matplotlib.pyplot as plt

def plot_courbe_delay(file_datetime, beginning, dt_solution):
    result_file = f"/home/pc-lrt-oaibox/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/{dt_solution}/results/" + file_datetime + "-delays.csv"
    plt.close(fig='all')
    # Charger le CSV
    df = pd.read_csv(result_file)

    # Si la colonne s'appelle "delay" et qu'il y a un message_id que vous ne voulez pas afficher
    delays = df["delay (s)"].dropna()
    df["sent_timestamp"] = pd.to_datetime(df["sent_timestamp"], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce', utc=True)
    df["sent_timestamp"] = df["sent_timestamp"] - pd.Timedelta(hours=2)
    df["sent_timestamp_seconds"] = (df["sent_timestamp"] - beginning).dt.total_seconds()

    df = df.dropna(subset=["delay (s)", "sent_timestamp"])

    # Tracer
    plt.figure(figsize=(12, 6))
    plt.plot(df["sent_timestamp_seconds"], df["delay (s)"], marker='.', linestyle='-', label="Delays (s)")
    plt.xlabel("Message sent time")
    plt.ylabel("Delay (seconds)")
    plt.title("Delays of messages (thing reception - mosquitto send)")
    plt.grid(True)
    plt.legend()
    plt.gcf().autofmt_xdate()
    plt.savefig(f"/home/pc-lrt-oaibox/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/{dt_solution}/results/{file_datetime}-delays-plot.png")
    print(f"Plot saved as {dt_solution}/results/{file_datetime}-delays-plot.png")
    plt.close()

def plot_courbe_cpuram(file_datetime, file_name, beginning, dt_solution):
    result_file = f"/home/pc-lrt-oaibox/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/{dt_solution}/measures/{file_datetime}-cpu_ram_sum"

    # Charger le CSV
    df = pd.read_csv(result_file)

    # Convertir Timestamp en datetime et ajuster
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format='%Y-%m-%d %H:%M:%S.%f', errors='coerce', utc=True)
    df["Timestamp"] = df["Timestamp"] - pd.Timedelta(hours=2)
    df["timestamp_seconds"] = (df["Timestamp"] - beginning).dt.total_seconds()
    df = df[df["timestamp_seconds"] > 0]

    # Tracer CPU
    plt.figure(figsize=(12, 6))
    plt.plot(df["timestamp_seconds"], df[" CPU%"], marker='.', linestyle='-', label="CPU%")
    plt.xlabel("Time (s)")
    plt.ylabel("CPU %")
    plt.title("CPU usage over time")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"/home/pc-lrt-oaibox/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/{dt_solution}/results/{file_name}-cpu-plot.png")
    print(f"CPU plot saved as {dt_solution}/{file_name}-cpu-plot.png")

    # Tracer RAM
    plt.figure(figsize=(12, 6))
    plt.plot(df["timestamp_seconds"], df[" MemUsageMiB"], marker='.', linestyle='-', label="Memory usage (MiB)")
    plt.xlabel("Time (s)")
    plt.ylabel("Memory usage (MiB)")
    plt.title("RAM usage over time")
    plt.grid(True)
    plt.legend()
    plt.savefig(f"/home/pc-lrt-oaibox/PycharmProjects/benchmarkDT/twins_to_compare/scripts_for_measures/{dt_solution}/results/{file_name}-ram-plot.png")
    print(f"RAM plot saved as {dt_solution}/{file_name}-ram-plot.png")
    plt.close()