# benchmarkDT

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-required-2496ED.svg)](https://www.docker.com/)

A performance benchmarking framework for Digital Twin and IoT brokers.
Compares **Eclipse Ditto**, **FIWARE Orion-LD**, and **Scorpio Broker** under
realistic, statistically-diverse MQTT workloads and measures end-to-end message
delay, CPU usage, and RAM consumption.

---

## Overview

`benchmarkDT` orchestrates a full measurement campaign from a single Python
entry point. For each experiment configuration it:

1. Starts the target broker stack via Docker Compose.
2. Provisions Digital Twin entities (road segments and traffic-flow sensors)
   through each broker's REST API.
3. Injects synthetic MQTT traffic following one of four configurable arrival
   laws (Uniform, Poisson, Gaussian, or MMPP).
4. Concurrently records every MQTT message timestamp and samples CPU / RAM
   usage across all broker containers.
5. Joins the send and receive timestamps to produce per-message end-to-end
   delay measurements, writes them to CSV files, and generates PNG plots.
6. Tears down all containers and volumes cleanly before the next run.

A separate `analysis/` layer provides scripts to aggregate results across
multiple runs and produce publication-ready comparison plots (CCDF curves,
line plots, histograms).

---

## Features

- **Three broker backends** — Eclipse Ditto (EPL-2.0), FIWARE Orion-LD
  (AGPL-3.0), and Scorpio Broker (BSD-3-Clause), each with its own Docker
  Compose stack and Python adapter.
- **Four arrival laws** — Uniform (constant frequency), Poisson (exponential
  inter-arrivals), Gaussian (time-concentrated burst), and MMPP
  (Markov-Modulated Poisson Process for time-varying load).
- **Automated warm-up** — a short uniform-rate burst is sent before each
  measurement window to ensure the broker is fully active.
- **Parallel log recorders** — MQTT messages and Docker container
  CPU/RAM stats are captured in dedicated background processes throughout
  every run.
- **Parameterised entity model** — number of entities, number of attributes
  per payload, and attribute byte size are all configurable.
- **Structured CSV results** — delay files encode all experiment parameters
  in their filename for unambiguous identification and aggregation.
- **Unified logging** — all output uses Python's `logging` module with a
  consistent timestamp-and-level format.
- **Analysis suite** — CCDF curves, line plots (delay vs. frequency, entity
  count, attribute count), histograms, and cross-run merge utilities.

---

## Prerequisites

| Requirement | Tested version | Notes |
|---|---|---|
| **Docker Engine** | 24.0+ | Must be running before any benchmark |
| **Docker Compose V2** | plugin (uses `docker compose`) | Not the legacy `docker-compose` binary |
| **Python** | 3.10+ | `zoneinfo` and union type hints require ≥ 3.9/3.10 |
| **`bc`** | any | Used by the CPU/RAM shell scripts for arithmetic |
| **Eclipse Ditto deployment** | 3.x | See [Installation](#installation) |

> **Platform note:** The infrastructure scripts (startup, log capture, teardown)
> are written for Linux. Running on macOS may require minor path adjustments;
> Windows (without WSL 2) is not supported.

---

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd benchmarkDT
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Obtain the Eclipse Ditto Docker deployment

Ditto's startup script (`brokers/eclipse_ditto/run_ditto.sh`) expects the
official Ditto Docker Compose files to be present at
`brokers/eclipse_ditto/ditto/deployment/docker/`. Clone the Ditto repository
there:

```bash
git clone https://github.com/eclipse-ditto/ditto.git \
    brokers/eclipse_ditto/ditto
```

### 4. (optional) Prepare the output directories

The benchmark writes raw logs, intermediate CSVs, and final results under
`measures/`. The required subdirectories are created automatically at runtime,
but you can create them in advance if needed:

```bash
mkdir -p measures/{ditto,orion_ld,scorpio}/{measures,measures_csv,results}
```

---

## Usage

All commands below must be run from the **project root** directory so that
relative paths in the scripts resolve correctly.

### Running a benchmark campaign

Open `main.py` and edit the `__main__` block to set your experiment parameters:

```python
if __name__ == "__main__":
    nb_seconds       = 3600 * 5   # measurement window duration (seconds)
    num_attributes   = 5          # attributes per entity payload
    bytes_per_attribute = 5       # byte size of each attribute value

    for dt_solution in ["ditto", "orion_ld"]:          # brokers to test
        for num_entities in [5]:                        # entity counts to test
            for lambdas_set in ([5, 10, 20], ...):     # MMPP lambda sets
                make_measurements(
                    dt_solution,
                    create_entities_before_measures=True,
                    nb_entities=num_entities,
                    nb_seconds=nb_seconds,
                    mmpp_enabled=True,
                    lambdas=lambdas_set,
                    ...
                )
```

Then launch it:

```bash
python main.py
```

`main.py` handles the full lifecycle automatically: starting Docker stacks,
provisioning entities, running the simulator, recording logs, computing delays,
generating plots, and tearing down containers. Each run produces files under
`measures/<broker>/` named with a timestamp and all experiment parameters.

### Selecting an arrival law

Pass the corresponding flag to `make_measurements()`:

| Arrival law | Flag | Key parameter |
|---|---|---|
| Uniform (constant rate) | `uniform_law_enabled=True` | `unif_frequency` (Hz) |
| Poisson | `poisson_law_enabled=True` | `poisson_lambda` (mean msg/s) |
| Gaussian (burst) | `gaussianlaw_enabled=True` | `gauss_nbmessages`, `center_ratio`, `sigma_ratio` |
| MMPP (time-varying) | `mmpp_enabled=True` | `lambdas` (list), `P` (transition matrix) |

### Running the broker stacks manually

Each broker has a dedicated startup script. Run them from the project root:

```bash
# Eclipse Ditto
bash brokers/eclipse_ditto/run_ditto.sh

# FIWARE Orion-LD
bash brokers/orion_ld/run_orion_ld.sh

# Scorpio Broker
bash brokers/scorpio/run_scorpio.sh
```

The scripts create a shared Docker bridge network (`external_network`), start
all required containers (broker, database, IoT Agent, Mosquitto), and wait
until every container is healthy before returning.

To tear everything down:

```bash
bash infrastructure/cleardocker.sh
```

> **Warning:** `cleardocker.sh` stops and removes **all** Docker containers,
> images, and volumes on the host. Use it only on a machine dedicated to this
> benchmark.

### Analysing results

The `analysis/` scripts operate on the CSV files produced by completed runs.
Each script is standalone; set the filter parameters at the top of the file
and execute it directly:

```bash
# CCDF curves: delay vs. MMPP lambda sets
python -m analysis.time_distribution_curve_lambdas

# CCDF curves: delay vs. number of entities
python -m analysis.time_distribution_curves_nbentities

# CCDF curves: delay vs. attribute count
python -m analysis.time_distribution_curves_nbattributes

# CCDF curves: delay vs. bytes per attribute
python -m analysis.time_distribution_curves_bpa

# Line plot: mean delay vs. message frequency
python -m analysis.compare_solutions_frequency

# Line plot: mean delay vs. number of entities
python -m analysis.compare_solutions_nbentities

# Line plot: mean delay vs. attribute count
python -m analysis.compare_solutions_nbattributes

# Histogram: delay distribution across brokers
python -m analysis.histogram_plot

# Merge multiple runs of the same configuration into one CSV
python -m analysis.merge_measurements
```

Output PNG files are written to `measures/analysis/comparison results/plots/`
or the path configured at the top of each script.

---

## Project Structure

```
benchmarkDT/
│
├── analysis/                    # Post-experiment analysis and comparison plots
│   ├── common.py                #   Shared CSV loading and percentile utilities
│   ├── compare_solutions_frequency.py
│   ├── compare_solutions_nbattributes.py
│   ├── compare_solutions_nbentities.py
│   ├── histogram_plot.py
│   ├── merge_measurements.py
│   ├── time_distribution_curve_lambdas.py
│   ├── time_distribution_curves_bpa.py
│   ├── time_distribution_curves_nbattributes.py
│   └── time_distribution_curves_nbentities.py
│
├── benchmark/                   # Core benchmark engine
│   ├── get_logs.py              #   MQTT and CPU/RAM log recorders
│   ├── plot.py                  #   Delay and resource-usage plot generators
│   ├── simulator.py             #   MQTT senders for all four arrival laws
│   ├── utils.py                 #   Logging configuration and JSON helpers
│   └── write_csvs.py            #   Raw-log → delay CSV post-processor
│
├── brokers/                     # Broker-specific Docker stacks and adapters
│   ├── eclipse_ditto/
│   │   ├── ditto/               #   Eclipse Ditto repo (cloned separately)
│   │   ├── eclipse_utils.py     #   Ditto REST API adapter
│   │   └── run_ditto.sh         #   Starts the Ditto + Mosquitto stack
│   ├── orion_ld/
│   │   ├── docker-compose.yml   #   Orion-LD + IoT Agent + MongoDB stack
│   │   ├── orion_ld_utils.py    #   Orion-LD REST API adapter
│   │   └── run_orion_ld.sh
│   ├── scorpio/
│   │   ├── docker-compose.yml   #   Scorpio + IoT Agent + PostgreSQL + MongoDB
│   │   ├── scorpio_utils.py     #   Scorpio REST API adapter
│   │   └── run_scorpio.sh
│   └── fiware_utils.py          #   Shared FIWARE IoT Agent helpers
│
├── config/
│   └── config.py                # Centralised endpoint, port, and credential settings
│
├── data/
│   └── road_segments_from_csv.json   # Input entity definitions (road segments)
│
├── infrastructure/
│   ├── cleardocker.sh           # Stops and removes all containers and volumes
│   └── mosquitto/               # Shared MQTT broker Docker stack
│       └── docker-compose.yml
│
├── measures/                    # Runtime output (created automatically)
│   ├── ditto/
│   │   ├── measures/            #   Raw MQTT and things logs
│   │   ├── measures_csv/        #   Intermediate per-side CSVs
│   │   └── results/             #   Final delay CSVs and PNG plots
│   ├── orion_ld/                #   (same structure)
│   └── scorpio/                 #   (same structure)
│
├── LICENSE                      # MIT License
├── THIRD-PARTY-NOTICES.md       # Licenses of all third-party dependencies
├── main.py                      # Orchestrates full benchmark runs
└── requirements.txt
```

---

## License and Acknowledgments

### This project

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE)
file for the full text.

### Third-party software

This project interacts at runtime with several third-party tools via network
APIs and Docker containers. **These tools are not bundled in this repository
and are governed by their own licenses**, which are independent of and
unaffected by the MIT License of this project:

| Tool | License | Notes |
|---|---|---|
| Eclipse Ditto | EPL-2.0 | Weak copyleft |
| FIWARE Orion-LD | AGPL-3.0-only | Network copyleft |
| FIWARE IoT Agent for JSON | AGPL-3.0-only | Network copyleft |
| Scorpio Broker | BSD-3-Clause | Permissive |
| Eclipse Mosquitto | EPL-2.0 OR BSD-3-Clause | Dual-licensed |
| MongoDB 4.4 | SSPL-1.0 | Not OSI-approved |
| PostGIS | GPL-2.0-or-later | Copyleft |

The Python dependencies (`matplotlib`, `numpy`, `paho-mqtt`, `pandas`,
`requests`, `seaborn`) are used as libraries and carry their own licenses
(BSD-3-Clause, Apache-2.0, EPL-2.0/EDL-1.0, and a PSF-compatible license
for matplotlib).

For complete license texts, copyright holders, and repository references for
all of the above, see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
