import docker
import measurements
import threading
client=docker.from_env()
measurements_thread=threading.Thread(target=measurements.get_measurements, args=(client,), name="docker_measurements")
measurements_thread.start()
