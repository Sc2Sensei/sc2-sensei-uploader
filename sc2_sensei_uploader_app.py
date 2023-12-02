import threading

from app import run_flask_server
from logs import UploadLogs
from loguru import logger
from ui_window import Sc2Sensei_UI_Pywebview

import watchdog_uploader
import webview
from functools import partial
import Environment_Variables


def fix_upload_entries_stuck_on_uploading():
	logs = UploadLogs(Environment_Variables.APPDATA_DIRECTORY)
	replays_log = logs.load()
	for c_replay in replays_log['replays']:
		if c_replay['upload_status'] == 'uploading':
			logger.warning('Found entry stuck as Uploading state. This should not happen. Setting to failed ')
			
			c_replay['upload_status'] = 'failed'
			c_replay['error_title'] = 'Upload Failed'
			c_replay['error_msg'] = 'Unknown Error'
	
	logs.save(replays_log)

def run():
	print('[App] Running')

	fix_upload_entries_stuck_on_uploading()

	global ui
	ui = Sc2Sensei_UI_Pywebview()

	ui.setup_tray()
	tray_thread = threading.Thread(target=ui.tray_icon.run)
	tray_thread.start()

	watchdog_uploader.on_watchdog_started = lambda: ui.change_tray_icon(Environment_Variables.SC2SENSEI_ICON_PATH_GREEN)
	watchdog_uploader.on_watchdog_stopped = lambda: ui.change_tray_icon(Environment_Variables.SC2SENSEI_ICON_PATH_RED)
	
	watchdog_thread = watchdog_uploader.start()

	run_flask_server_fn = partial(run_flask_server, ui_instance=ui)
	flask_server_process = threading.Thread(target=run_flask_server_fn, daemon=True)
	flask_server_process.start()
	
	webview.start(debug=Environment_Variables.DEBUG)	
	
	print('[App] Closing')