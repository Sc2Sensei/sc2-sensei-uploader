import os
from loguru import logger
from files import JSONHandle, FileHandle
from datetime import datetime

class UploadLogs(JSONHandle):
	def __init__(self, dir_path):
		super().__init__(dir_path)
		self.path = f"{self.logs_path}/uploads.json"
		
		if not os.path.exists(self.path):
			empty = { "replays" : [] }
			self.save(empty)

	def add_replay(self, log):
		new_log = self.load()
		new_log["replays"].append(log)
		self.save(new_log)

	def finish_last_replay(self, parse_response):
		new_log = self.load()
		parse_result = parse_response['result']
		replay_id = parse_response['replay_id']
		
		success = parse_result == 600

		new_log["replays"][-1]["upload_status"] = "success" if success else "failed"
		new_log["replays"][-1]["replay_id"] = replay_id
		
		if 'player_1' in parse_response and 'player_2' in parse_response:
			new_log["replays"][-1]["player_1"] = parse_response['player_1']
			new_log["replays"][-1]["player_2"] = parse_response['player_2']

		if 'error_title' in parse_response and 'error_msg' in parse_response:
			new_log["replays"][-1]["error_title"] = parse_response['error_title']
			new_log["replays"][-1]["error_msg"] = parse_response['error_msg']

		self.save(new_log)

	def get_replay_index(self, replay_name):
		for i, c_replay in reversed(list(enumerate(self.load()['replays']))):
			if c_replay['name'] == replay_name:
				return i
			
		return -1

	def set_replay(self, replay_name, parse_response):
		new_log = self.load()
		
		parse_result = parse_response['result']
		replay_id = parse_response['replay_id']
		
		success = parse_result == 600

		replay_index = self.get_replay_index(replay_name)
		
		if replay_index == -1:
			logger.error('[Error] Replay not found')
			return

		new_log["replays"][replay_index]["upload_status"] = "success" if success else "failed"
		new_log["replays"][replay_index]["replay_id"] = replay_id
		
		if 'player_1' in parse_response and 'player_2' in parse_response:
			new_log["replays"][replay_index]["player_1"] = parse_response['player_1']
			new_log["replays"][replay_index]["player_2"] = parse_response['player_2']

		if 'error_title' in parse_response and 'error_msg' in parse_response:
			new_log["replays"][replay_index]["error_title"] = parse_response['error_title']
			new_log["replays"][replay_index]["error_msg"] = parse_response['error_msg']

		self.save(new_log)

	def get_last_replays(self, quantity=5):
		logs = self.load()
		length = len(logs["replays"])
		
		replays = []
		if quantity > length:
			quantity = length
		
		for i in range(1, quantity+1):
			replays.append(logs["replays"][-i])
		
		logger.info(f"Returned last {quantity} replays from the logs")

		return replays
	
	def set_replay_to_uploading(self, replay_name):
		new_log = self.load()
		replay_index = self.get_replay_index(replay_name)
		
		new_log['replays'][replay_index]['upload_status'] = 'uploading'
		
		self.save(new_log)

class AppLogs(FileHandle):
	def __init__(self, dir_path):
		super().__init__(dir_path)
		self.path = f"{self.logs_path}/logs.txt"

		if not os.path.exists(self.path):
			now = datetime.now()
			date = now.strftime("%d/%m/%Y %H:%M:%S")
			
			with open(self.path, "w") as file:
				file.write(f"[{date}] Created log file")
