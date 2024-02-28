import json
from fastapi import FastAPI
from sched import scheduler
from time import time, sleep
from threading import Thread
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


app = FastAPI()
s = scheduler(time, sleep)
observer = Observer()  # Declare the observer here to be accessible at shutdown

method_configs = {}

def load_config_file():
    with open('methods_payload.json', 'r') as f:
        return json.load(f)

# Load the initial configuration
method_configs = load_config_file()


class ConfigFileEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        # Make sure we're only acting on the specific file we're interested in.
        if 'methods_payload.json' in event.src_path:
            global method_configs, s
            print("Detected a change in methods_payload.json. Updating configuration.")
            try:
                method_configs = load_config_file()
                schedule_tasks()
            except Exception as e:
                print(f"Error updating configuration: {e}")

# Lifespan event handler to start and stop the scheduler
@app.on_event("startup")
async def startup_event():
    # Setup the file watcher
    event_handler = ConfigFileEventHandler()
    observer.schedule(event_handler, '.', recursive=False)
    observer.start()
    start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    observer.stop()
    observer.join()

# Define the GET endpoint as an example
# Define the GET endpoint
def get_current_time(params):
    print(f"Current time:, Params: {params}")

# Function to invoke methods via the scheduler
# Function to invoke methods via the scheduler
def invoke_method(method_name):
    # Fetch the latest configuration
    method_config = method_configs.get(method_name, {})
    params = method_config.get("params")
    interval = method_config.get("interval", 3600)  # Default to 1 hour if no interval is specified

    # Invoke the method
    if method_name in globals():
        method = globals()[method_name]
        if callable(method):
            try:
                print(f"Invoking {method_name} with params: {params}")
                method(params=params)
                # Schedule the next invocation
                s.enter(interval, 1, invoke_method, argument=(method_name,))
            except Exception as e:
                print(f"Error invoking {method_name}: {e}")
        else:
            print(f"{method_name} is not callable or not found in globals.")
    else:
        print(f"{method_name} does not exist as a function.")

# Function to schedule tasks based on the intervals specified in the JSON file
# Function to schedule tasks based on the intervals specified in the JSON file
def schedule_tasks():
    global method_configs, s
    if not method_configs:
        print("No configurations found to schedule tasks.")
        return

    # Clear any existing scheduled tasks
    s.queue.clear()

    for method_name in method_configs.keys():
        # Immediately invoke the method to schedule its first run
        invoke_method(method_name)
# Function to run the scheduler tasks
def run_scheduler():
    schedule_tasks()
    s.run()

# Start the scheduler in a separate thread and set it as a daemon
def start_scheduler():
    scheduler_thread = Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)