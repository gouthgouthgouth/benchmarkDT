from configs.config import *
import time
from utils.utils import clean_environment, start_container, print_time, check_container, run_command

if __name__ == "__main__":
    print_time("Cleaning docker environment")
    clean_environment()
    print_time("Starting Fiware...")
    start_container(fiware_config_data["CONTAINER_NAME"], fiware_config_data["IMAGE_NAME"], RAM_LIMIT, CPU_LIMIT)

    check_container()
