from loguru import logger
import threading
import time
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from settings import Settings
from replays_uploader import upload_file_on_created
import Environment_Variables

watchdog_active = False
watchdog_thread = None

on_watchdog_started = None
on_watchdog_stopped = None

def start_watchdog():
	patterns = ["*.SC2Replay"]

	ignore_patterns = None
	ignore_directories = False
	case_sensitive = False
	my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
	my_event_handler.on_created = upload_file_on_created

	appdata_directory = Environment_Variables.APPDATA_DIRECTORY

	settings = Settings(appdata_directory)
	path = settings.load().get('replays_directory', '')
	if path == '':
		global watchdog_active
		watchdog_active = False
		logger.warning("[Warning] Abort Start Watchdog: replays directory is not defined")
		return

	go_recursively = False
	replays_watchdog = Observer()
	replays_watchdog.schedule(my_event_handler, path, recursive=go_recursively)

	logger.info('[Watchdog] Start\n\t Watching '+path)

	replays_watchdog.start()
	
	while watchdog_active: # Watch Polling File Changes 
		time.sleep(3)
		print('...')
	
	replays_watchdog.stop()
	replays_watchdog.join()
	logger.info('[Watchdog] Stopped')


def start():
	global watchdog_thread
	global watchdog_active
	if not watchdog_thread or not watchdog_thread.is_alive():
		watchdog_active = True
		watchdog_thread = threading.Thread(target=start_watchdog, daemon=True)
		watchdog_thread.start()
		if on_watchdog_started is not None:
			on_watchdog_started()

		return watchdog_thread
	else:
		logger.warn("[Warning] Watchdog already running. start() was ignored")
		return None
	

def stop():
	global watchdog_thread
	global watchdog_active
	if watchdog_thread:
		watchdog_active = False
		watchdog_thread.join()
		watchdog_thread = None
		if on_watchdog_stopped is not None:
			on_watchdog_stopped()