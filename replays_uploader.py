import requests
from settings import Settings
from logs import UploadLogs
import os
import count_monthly_replays
import Environment_Variables
from loguru import logger

class Replay_Upload_Limit_Reached_Exception(Exception):
	pass

appdata_directory = Environment_Variables.APPDATA_DIRECTORY

gui_server = f"http://127.0.0.1:{Environment_Variables.FLASK_RUN_PORT}/"

def upload_file_on_created(event):
	replay_path = event.src_path
	replay_name = os.path.splitext(os.path.basename(replay_path))[0]
	post_args = {'replay_name' : replay_name}

	requests.post(f"{gui_server}/notify_new_replay", json=post_args)

	settings_handle = Settings(appdata_directory)
	logs_handle = UploadLogs(appdata_directory)
	

	log = init_log(replay_path)
	log['upload_status'] = 'uploading'
	logs_handle.add_replay(log)

	user_id = settings_handle.load()["user_id"]
	try:
		try:
			response = upload(replay_path, Environment_Variables.UPLOAD_ENDPOINT, user_id)
			logs_handle.finish_last_replay(response.json())
			if response.json()['result'] == 600:
				requests.get(f"http://127.0.0.1:5078/update_speedmeter")
				
		except:
			logs_handle.finish_last_replay({'result': 404, 'replay_id':None })

	except Replay_Upload_Limit_Reached_Exception:
		logger.info('Replay Upload Failed - Limit Reached')
		new_log = logs_handle.load()
		
		new_log["replays"][-1]["upload_status"] = 'monthly-limit-reached'
		logs_handle.save(new_log)
	except requests.exceptions.ConnectionError:
		logger.info("Can't connect to Sc2 Sensei")
		new_log = logs_handle.load()
		
		new_log["replays"][-1]["upload_status"] = 'no-internet'
		logs_handle.save(new_log)


def upload(replay_path, endpoint, user_id):
	uploaded_replays_this_month, limit = count_monthly_replays.get_uploaded_replays_this_month()
	
	if uploaded_replays_this_month >= limit:
		raise Replay_Upload_Limit_Reached_Exception	
	
	with open(replay_path, "rb") as file:
		replay = { "file" : file }
		post_args = { "user-id": user_id }

		# TODO: handle connection exceptions?
		result = requests.post(endpoint, data=post_args, files=replay)

		return result

def init_log(replay_path):
	log = {
		"name" : os.path.splitext(os.path.basename(replay_path))[0],
		"replay_id" : "",
		"creation_date" : os.path.getctime(replay_path),
		"upload_status" : ""
	}
	return log