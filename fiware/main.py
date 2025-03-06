import json
import requests

from configs.config import *
from utils.utils import run_container, print_time, check_containers, run_command, stop_container, \
    start_container, check_images

def fiware_initialize_containers():
    container_name = fiware_config_data["CONTAINER_NAME"]
    container_image = fiware_config_data["IMAGE_NAME"]
    run_container(container_name, container_image, RAM_LIMIT, CPU_LIMIT)
    run_container(
        container_name="mongo-db",
        image_name="mongo",
        ram_limit=RAM_LIMIT,
        cpu_limit=CPU_LIMIT,
        port_mapping="27017:27017",
        volume_mapping=f"{container_name}-data:/data/db"
    )

def fiware_start_orion():
    start_container(fiware_config_data["CONTAINER_NAME"])

def fiware_stop_and_clean_containers():
    container_name = fiware_config_data["CONTAINER_NAME"]
    stop_container(container_name)
    stop_container("mongo-db")

def add_road_segments(input_file):
    url = fiware_config_data["API_URL"]

    with open(input_file, "r") as file:
        road_segments = json.load(file)

    for segment in road_segments:
        try:
            headers = {"Content-Type": "application/ld+json"}
            response = requests.post(url, headers=headers, json=segment)

            if response.status_code == 201:
                print(f"Entité {segment['id']} créée avec succès.")
            else:
                print(f"Échec de la création de {segment['id']}: {response.status_code}, {response.text}")
        except Exception as e:
            print(f"Erreur lors de l'envoi de {segment['id']}: {e}")

