import glob
import os
import sys
from time import sleep
from flask import Flask, render_template, request, redirect, url_for, make_response

import webbrowser
import requests
from flask_sock import Sock
from check_internet_connection import is_connected
import count_monthly_replays
from jinja_operators import JinjaOperators

from logs import UploadLogs
from settings import Settings

from email_validator import validate_email
from email_validator.exceptions_types import EmailSyntaxError
from replays_uploader import upload

import watchdog_uploader
import Environment_Variables
import subprocess

import os

from loguru import logger

ui_instance_reference = None # Will be set by main thread

MAX_ENTRIES_COUNT = 30

sc2_sensei_url = Environment_Variables.SC2_SENSEI_URL
appdata_directory = Environment_Variables.APPDATA_DIRECTORY

log_handle = UploadLogs(appdata_directory)
settings_handle = Settings(appdata_directory)

app = Flask(__name__)
sock = Sock()
sock.init_app(app)

app.shutdown_flag = False

app.debug = Environment_Variables.DEBUG

app.jinja_env.auto_reload = Environment_Variables.DEBUG
app.config["TEMPLATES_AUTO_RELOAD"] = Environment_Variables.DEBUG
JinjaOperators.register_custom_jinja_operators(app.jinja_env)

new_replay_found = None
should_update_speedmeter = False
shutdown_flag = False

@app.before_request
def check_for_internet():
	if '.' not in request.full_path:
		if not is_connected():
			return render_template('no_internet.html')
		

@sock.route('/update_replays_entries')
def handle_connect(ws):
	while not app.shutdown_flag:
		global new_replay_found
		if new_replay_found != None:
			new_replay_found = None
			# Refresh entries list. HTMX swaps the element with the same id as the one we send in
			logger.info('Add new Replay to UI')
			ws.send( replay_entries() )

		global should_update_speedmeter
		if should_update_speedmeter:
			logger.info('Refresh Speedmeter')
			should_update_speedmeter = False
			try:
				uploaded_replays_this_month, limit = count_monthly_replays.get_uploaded_replays_this_month()
				speedmeter_progress = (uploaded_replays_this_month / limit * 180)

				refresh_speedmeter = render_template(
					'uploader/update_speedmeter_htmx_ws.html',
					uploaded_replays_this_month=uploaded_replays_this_month, 
					speedmeter_progress=speedmeter_progress
				)
				
				ws.send( refresh_speedmeter )
			except requests.exceptions.ConnectionError:
				# There is a special edge case where this method could not be able to reach the website
				# Don't update speedmeter. We can't
				pass
		
		sleep(3)

@app.route('/update_speedmeter')
def update_speedmeter():
	logger.info('Update Speedmeter')
	global should_update_speedmeter
	should_update_speedmeter = True

	return "", 200


@app.route('/')
def index():
	user_id = settings_handle.load().get('user_id', '')
	user_logged_in = user_id != '' # TODO: stronger validation?

	user_logged_in = True ### This line is commented in production

	if user_logged_in:
		return redirect(url_for('uploader'))
	else:
		return render_template('login/login_page.html')


@app.route('/uploader')
def uploader():
	# TODO: If user not logged in, we should not be here. Reopen home page for login procedure

	user_id = settings_handle.load()['user_id']
	replays_list = log_handle.get_last_replays(MAX_ENTRIES_COUNT)

	try:
		uploaded_replays_this_month, limit = count_monthly_replays.get_uploaded_replays_this_month()
	except:
		uploaded_replays_this_month = 1
		limit = 100
		### return render_template('cant_connect_to_sc2sensei.html') ### This line is NOT commented in production

	return render_template('uploader/uploader.html', replay_logs=replays_list, watchdog_paused=(not watchdog_uploader.watchdog_active), user_id=user_id, uploaded_replays_this_month=uploaded_replays_this_month, limit=limit)

@app.route('/replay_entries')
def replay_entries():
	replays_list = log_handle.get_last_replays(MAX_ENTRIES_COUNT)

	
	return render_template('uploader/fragments/replay_entries.html', replay_logs=replays_list)

@app.route('/get_replay_entry/<replay_name>')
def get_replay_entry(replay_name):
	replays_list = log_handle.get_last_replays(MAX_ENTRIES_COUNT)
	replay = next(filter(lambda e: e['name'] == replay_name, replays_list))
	
	if replay['upload_status'] == 'uploading':
		return "No Content", 204
	
	return render_template('uploader/fragments/single_replay_entry.html', replay=replay)


@app.route('/login', methods=['POST'])
def login():
	post_args = { 
		'user-email' :  request.form['user-email'],
		'user-password': request.form['user-password']
	}
	try:
		result = requests.post(f'REDACTED', json=post_args)
	except requests.exceptions.ConnectionError:
		return render_template(
			'login/fragments/login_form.html',
			user_email=request.form['user-email'], 
			sc2_sensei_unreacheable=True
		)

	if result.json()['login_successful']:
		settings_log = settings_handle.load()
		settings_log['user_id'] = result.json()['user_id']
		settings_handle.save(settings_log)

		response = make_response()
		response.headers['HX-Redirect']=url_for('uploader')
		
		return response
	else:
		# Reload showing error for login
		invalid_email = check_email_is_valid(request.form['user-email']) == False
		if invalid_email == False:
			args = {'user-email' : request.form['user-email']}
			result = requests.post(f'REDACTED', json=args)
			is_user_registered = result.json()
			invalid_email = is_user_registered == False

		return render_template(
			'login/fragments/login_form.html',
			user_email=request.form['user-email'], 
			invalid_password=True,
			invalid_email=invalid_email
		)
	
@app.route('/check_login_credentials', methods=['POST'])
def check_login_credentials():
	if request.values['user-email'] == '':
		return render_template(
			'login/fragments/login_form.html'
		)
	
	sc2_sensei_unreacheable = False
	
	invalid_email = check_email_is_valid(request.values['user-email']) == False
	if invalid_email == False:
		args = {'user-email' : request.values['user-email']}
		try:
			result = requests.post(f'REDACTED', json=args)
			is_user_registered = result.json()
			invalid_email = is_user_registered == False
		except requests.exceptions.ConnectionError:
			# We can't connect to Sc2 Sensei
			sc2_sensei_unreacheable = True
		
	return render_template(
		'login/fragments/login_form.html',
		user_email=request.form['user-email'], 
		invalid_email=invalid_email,
		sc2_sensei_unreacheable=sc2_sensei_unreacheable
	)

@app.route('/logout')
def logout():
	# One of the easiest methods I've ever written
	settings_log = settings_handle.load()
	del settings_log['user_id']
	settings_handle.save(settings_log)
	
	response = make_response()
	response.headers['HX-Redirect'] = '/'
	return response


@app.route('/redirect_to_website_registration')
def redirect_to_website_registration():
	webbrowser.open(sc2_sensei_url, 2)
	logger.info(f"redirect to {sc2_sensei_url}")
	return "", 200

@app.route('/notify_new_replay', methods=['POST'])
def notify_new_replay():
	# TODO: Send replays uploaded count as argument, so we can also update the speedmeter
	logger.info('New replay!')
	
	global new_replay_found
	new_replay_found = request.json['replay_name']
	return "", 200


def find_replay_file(replay_name, replay_creation_date):
	replays_dir = settings_handle.load()['replays_directory']+"/*"
	list_of_replays = glob.glob(replays_dir)
	list_of_replays = list(map(lambda f: f.replace('\\', '/'), list_of_replays))
	
	get_replay_name = lambda path: os.path.splitext(os.path.basename(path))[0]

	replay_file = next(filter(lambda e: get_replay_name(e) == replay_name and os.path.getctime(e) == replay_creation_date, list_of_replays))
	
	return replay_file

@app.route('/retry_upload_replay', methods=['GET'])
def retry_upload_replay():
	replay_name = request.args['replay_name']
	replay_creation_date = float(request.args['creation_date'])
	
	replay_file_path = find_replay_file(replay_name, replay_creation_date)
	if replay_file_path is None:
		logger.error('[Error] Replay not found: it was deleted or renamed')
		return "", 400

	user_id = settings_handle.load()["user_id"]
	log_handle.set_replay_to_uploading(replay_name)
	global new_replay_found
	new_replay_found = replay_name

	upload_rslt = upload(replay_file_path, Environment_Variables.UPLOAD_ENDPOINT, user_id)

	log_handle.set_replay(replay_name, upload_rslt.json())

	return "", 200


@app.route('/open_change_replays_directory_modal')
def get_replay_directory_settings_modal():
	replays_directory = settings_handle.load().get('replays_directory', '')

	return render_template('change_replays_directory_modal.html',
		replays_directory=replays_directory, 
		enable_save_btn=False
	)

@app.route('/open_replays_directory_picker')
def open_replays_directory_picker():
	chosen_dir = ui_instance_reference.pick_folder()

	if chosen_dir == None:
		chosen_dir = 'Click to Select a Directory'
		enable_save_btn = False
	else:
		enable_save_btn = chosen_dir != settings_handle.load().get('replays_directory', '')

	return render_template('change_replays_directory_modal.html', 
		replays_directory=chosen_dir, 
		enable_save_btn=enable_save_btn
	)

@app.route('/update_replays_directory')
def update_replays_directory():
	replay_path = request.values['selected_replays_directory_path']
		
	if replay_path != None and os.path.isdir(replay_path):
		settings_log = settings_handle.load()
		settings_log['replays_directory'] = replay_path
		settings_handle.save(settings_log)
	
	watchdog_uploader.stop()
	sleep(1)
	watchdog_uploader.start()

	return uploader()



@app.route('/set_start_with_windows', methods=['GET'])
def set_start_with_windows():
	start_with_windows = 'start_with_windows' in request.values

	settings = settings_handle.load()
	settings['start_with_windows'] = start_with_windows
	settings_handle.save(settings)

	shortcut_file_path = os.path.expandvars("%AppData%\Microsoft\Windows\Start Menu\Programs\Startup\SC2Sensei.lnk")

	if start_with_windows:
		add_sc2sensei_to_startup_folder_as_shortcut(shortcut_file_path)
	else:
		if os.path.exists(shortcut_file_path):
			os.remove(shortcut_file_path)
			logger.info('[App] Removing Shortcut')

	return "", 200	

def add_sc2sensei_to_startup_folder_as_shortcut(destination):
	# Define the source and destination paths
	source = f"{os.getcwd()}/sc2_sensei_uploader.exe"
	
	logger.info(f'[APP] Adding Shortcut of file {source} at {destination}')
	# Create the PowerShell script
	script = f"""
	$WshShell = New-Object -comObject WScript.Shell
	$Shortcut = $WshShell.CreateShortcut("{destination}")
	$Shortcut.TargetPath = "{source}"
	$Shortcut.WorkingDirectory = "{os.getcwd()}"
	$Shortcut.Save()
	"""

	# Invoke the PowerShell script
	startupinfo = subprocess.STARTUPINFO()
	startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
	startupinfo.wShowWindow = subprocess.SW_HIDE
	
	subprocess.run(["powershell", "-Command", script], startupinfo=startupinfo)
	logger.info(f'[APP] Adding Shortcut Complete')


@app.route('/remove_element')
def remove_element():
	resp = make_response("")
	resp.cache_control.immutable = True
	resp.cache_control.max_age = 31536000
	return resp

@app.route('/pause_watchdog')
def pause_watchdog():
	# TODO: Even though it's called pause, we actually want to stop/terminate the watchdog 
	watchdog_uploader.stop()
	return render_template('uploader/fragments/watchdog_controls.html', watchdog_paused=True)

@app.route('/restart_watchdog')
def restart_watchdog():
	# TODO: Find a way to restart the watchdog
	watchdog_uploader.start()
	return render_template('uploader/fragments/watchdog_controls.html', watchdog_paused=False)

def check_email_is_valid(user_email):
	try:
		rslt = validate_email(user_email, check_deliverability=False)
		return True
	except EmailSyntaxError:
		return False


def shutdown_server():
	logger.info('Shutting Down Server')
	app.shutdown_flag = True
	raise RuntimeError("Shutdown")
	
@app.get('/shutdown')
def shutdown():
	shutdown_server()
	return 'Server shutting down...'


@app.get('/processing_update')
def debug_processing_update():
	return render_template('processing_update.html')


## To start the server from outside this file
def run_flask_server(ui_instance):
	global ui_instance_reference
	ui_instance_reference = ui_instance
	
	try:
		app.run(port=Environment_Variables.FLASK_RUN_PORT, threaded=True, use_reloader=False)
	except RuntimeError:
		sys.exit(0)




# if __name__ == '__main__':
	# from livereload import Server

	# server = Server(app.wsgi_app)
	# server.watch("templates/*.*")
	# server.serve(port=Environment_Variables.FLASK_RUN_PORT)
	# logger.info('Running Livereload Dev version')