import json
import subprocess
import datetime
from copy import deepcopy


def print_time(text_to_print):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + ": " + text_to_print)


def run_command(command_list):
    """Execute a shell command safely and return the output."""
    result = subprocess.run(command_list, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"❌ Error executing command: {result.stderr}")

    return result.stdout.strip()


def clean_environment():
    print_time("⚠️ WARNING: This will delete all unused Docker images, containers, and volumes!")
    confirmation = input("Do you really want to proceed? (yes/no): ")

    if confirmation.lower() == "yes":
        print_time("🧹 Cleaning Docker environment...")
        run_command(["docker", "system", "prune", "-a", "--volumes", "-f"])
        print_time("✅ Docker environment cleaned.")
    else:
        print_time("❌ Cleaning cancelled.")


def run_container(container_name, image_name, ram_limit="512m", cpu_limit="1", port_mapping="1026:1026",
                  volume_mapping=None):
    """Run a container with resource limits and optional volume mapping."""
    print_time(f"🚀 Running container {container_name} with {ram_limit} RAM and {cpu_limit} CPU(s)...")

    command = [
        "docker", "run", "-d", "--name", container_name,
        "--memory", ram_limit, "--cpus", cpu_limit,
        "-p", port_mapping
    ]

    if volume_mapping:
        command.extend(["-v", volume_mapping])

    command.append(image_name)

    result = run_command(command)

    if result:
        print_time(f"✅ Container {container_name} started successfully.")
    else:
        print_time(f"❌ Failed to start {container_name}. Check logs.")

def stop_container(container_name):
    """Stop a running Docker container."""
    print_time(f"🛑 Stopping container {container_name}...")
    result = run_command(["docker", "stop", container_name])
    if result:
        print_time(f"✅ Container {container_name} stopped successfully.")
    else:
        print_time(f"❌ Failed to stop {container_name}. Check logs.")


def start_container(container_name):
    """Start a stopped Docker container."""
    print_time(f"▶️ Starting stopped container {container_name}...")
    result = run_command(["docker", "start", container_name])

    if result:
        print_time(f"✅ Container {container_name} started successfully.")
    else:
        print_time(f"❌ Failed to start {container_name}. Check logs.")

def check_containers():
    """Check running containers."""
    print_time("🔍 Checking running containers...")
    print(run_command(["docker", "ps"]))

def check_images():
    """Check docker images."""
    print_time("🔍 Checking images...")
    print(run_command(["docker", "images"]))

def get_road_segments_from_json(input_file, number_required=None):
    with open(input_file, "r") as file:
        road_segments = json.load(file)

    initial_number = len(road_segments)

    if number_required is not None:
        while number_required < len(road_segments):
            road_segments.pop()
        i = 1
        while number_required > len(road_segments):
            road_segment_to_add = deepcopy(road_segments[i - 1])
            road_segment_to_add["id"] = "urn:ngsi-ld:RoadSegment:RoadSegment" + str(initial_number + i)
            road_segments.append(road_segment_to_add)
            i += 1
    return road_segments
