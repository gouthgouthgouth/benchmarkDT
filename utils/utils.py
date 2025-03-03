import subprocess
import time
import datetime

def print_time(text_to_print):
    print(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + ": " + text_to_print)

def run_command(command):
    """Execute a shell command and return the output."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        print("❌ Error executing command:", result.stderr)

    return result.stdout.strip()

def clean_environment():
    print_time("Cleaning Docker environment...")
    run_command("docker system prune -a --volumes -f")
    print_time("Docker environment cleaned.")

def start_container(CONTAINER_NAME, IMAGE_NAME, RAM_LIMIT, CPU_LIMIT):
    """Start the Digital Twin container with resource limits."""
    print_time(f"🚀 Starting container {CONTAINER_NAME}...")
    run_command(f"""
    docker run -d --name {CONTAINER_NAME} \
    --memory="{RAM_LIMIT}" --cpus="{CPU_LIMIT}" \
    -p 1026:1026 {IMAGE_NAME}
    """)

def check_container():
    """Check if the container is running."""
    print_time("🔍 Checking running containers...")
    print(run_command("docker ps"))