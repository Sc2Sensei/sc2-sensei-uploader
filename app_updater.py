import logging
import os
import re
import subprocess
import sys
from tempfile import NamedTemporaryFile
import time

from tufup.client import Client

import updater_app_settings
import webview

from loguru import logger

MIN_UI_SHOW_TIME = 6

logger = logging.getLogger(__name__)
client = None

__version__ = updater_app_settings.APP_VERSION



def progress_hook(bytes_downloaded: int, bytes_expected: int):
	progress_percent = bytes_downloaded / bytes_expected * 100
	logger.info(f'\r{progress_percent:.1f}%', end='')
	if progress_percent >= 100:
		pass


def show_update_progress_ui( func ):
	# Create a pywebview window that loads our page
	window = webview.create_window(
		'Updating Sc2 Sensei', 
		f'processing_update.html', 
		# f'processing_update.html', 
		width=490,
		height=206,
		resizable=False, 
		frameless=True
	)	

	# This sets the renderer, the available options are: 'qt', 'cef', 'gtk', 'edgehtml', 'mshtml'
	webview.start(func, window, http_server=True, gui='edgehtml')


def are_beta_updates_enabled():
	enable_beta_updates_file = f'{os.getcwd()}/beta.enable'
	return os.path.exists(enable_beta_updates_file)


def update():
	# TODO: If we can see the update.lock file, then the latest update was unsuccessful. We should probably write something inside this file to understand what failed about the update, but I'm unsure about how to do that..........
	delete_except_latest(updater_app_settings.TARGET_DIR)

	# Create update client
	global client
	client = Client(
		app_name=updater_app_settings.APP_NAME,
		app_install_dir=updater_app_settings.INSTALL_DIR,
		current_version=updater_app_settings.APP_VERSION,
		metadata_dir=updater_app_settings.METADATA_DIR,
		metadata_base_url=updater_app_settings.METADATA_BASE_URL,
		target_dir=updater_app_settings.TARGET_DIR,
		target_base_url=updater_app_settings.TARGET_BASE_URL,
		refresh_required=False,
	)

	# Perform update
	logger.info('[App Updater] Check for Updates')
	pre_release_channel = None
	if are_beta_updates_enabled():
		logger.info('[App Updater] Beta Release Channel is enabled')
		pre_release_channel = 'b'
	
	new_update = client.check_for_updates(pre=pre_release_channel)
	if new_update:
		logger.info('[App Updater] New Update Found: '+str(new_update.filename))

		# Show Update progress UI while we're downloading
		show_update_progress_ui( download_and_apply_update__thread )

		# Exiting the Python script
		sys.exit(0)

	return False

def download_and_apply_update__thread(ui_window):
	# At this point, the version info from `new_update` could be used to
	# present a custom confirmation dialog, asking the user if they wish
	# to proceed with the download (and installation). However, to keep
	# the example minimal, we simply rely on the built-in command-line
	# confirmation in download_and_apply_update().
	ui_show_time = time.time()

	global client
	client.download_and_apply_update(
		skip_confirmation=True,
		progress_hook=progress_hook,
		# WARNING: Be very careful with `purge_dst_dir=True`, because
		# this will *irreversibly* delete *EVERYTHING* inside the
		# `app_install_dir`, except any paths specified in
		# `exclude_from_purge`. So, *ONLY* use `purge_dst_dir=True` if
		# you are absolutely certain that your `app_install_dir` does not
		# contain any unrelated content.
		purge_dst_dir=False,
		exclude_from_purge=None,
		install=_install_update_win,
		log_file_name='install.log',
	)
	logger.info('[App Updater] Update downloaded and installed')
	
	time_ui_shown = time.time() - ui_show_time
	if time_ui_shown < MIN_UI_SHOW_TIME:
		time_until_min_show_time = MIN_UI_SHOW_TIME - time_ui_shown
		logger.warn(f'[App Updater] Waiting {time_until_min_show_time} until close UI progress window')
		time.sleep(time_until_min_show_time)

	ui_window.destroy()
	sys.exit(0)


def delete_except_latest(folder_path):
	# List all files in the directory
	files = os.listdir(folder_path)
	
	# Pattern to match the files with version numbers
	pattern = re.compile(r'(\d+)\.(\d+)\.')
	
	versioned_files = {}
	
	for file in files:
		match = pattern.search(file)
		if match:
			major, minor = map(int, match.groups())
			versioned_files[(major, minor)] = file
	
	if not versioned_files:
		return
	
	# Find the file with the highest version
	latest_version_file = versioned_files[max(versioned_files.keys())]
	
	# Delete other files
	for file in files:
		if file != latest_version_file:
			logger.info( 'Removing '+ file )
			os.remove(os.path.join(folder_path, file))

	logger.info('[App Updater] Deleted older app tar versions')




# Note that robocopy itself also has an option to create a log file,
# viz. `/log:<filename>`, as well as a `/tee` option, but we want to log *all*
# output from the batch file, not just output from the robocopy command.
WIN_LOG_LINES = """
call :log > "{log_file_path}" 2>&1
:log
"""
WIN_ROBOCOPY_OVERWRITE = (
	'/e',  # include subdirectories, even if empty
	'/move',  # deletes files and dirs from source dir after they've been copied
	'/v',  # verbose (show what is going on)
	'/w:2',  # set retry-timeout (default is 30 seconds)
)
WIN_ROBOCOPY_PURGE = '/purge'  # delete all files and dirs in destination folder
WIN_ROBOCOPY_EXCLUDE_FROM_PURGE = '/xf'  # exclude specified paths from purge
# makes batch file delete itself when done (https://stackoverflow.com/a/20333575)
WIN_BATCH_DELETE_SELF = '(goto) 2>nul & del "%~f0"'

# _install_update_win makes sure the following variables are available for
# batch templates:
# {log_lines}, {src_dir}, {dst_dir}, {robocopy_options}, {delete_self}
WIN_BATCH_TEMPLATE = """@echo off
{log_lines}
echo Moving app files...
robocopy "{src_dir}" "{dst_dir}" {robocopy_options}
echo Done.
{delete_self}
"""
WIN_BATCH_PREFIX = 'tufup'
WIN_BATCH_SUFFIX = '.bat'


WIN_BATCH_RESTART_APP = f"""
@echo off
SET "batch_pid=%1"
SET "py_pid=%2"

:wait_batch
REM Check if the batch update process is still running
tasklist | findstr /C:"%batch_pid%" >nul
IF NOT ERRORLEVEL 1 (
	REM If the batch process is still running, wait a bit
	timeout /t 1 >nul
	goto wait_batch
)

:wait_python
REM Check if the Python process is still running
tasklist | findstr /C:"%py_pid%" >nul
IF NOT ERRORLEVEL 1 (
	REM If the Python process is still running, wait a bit
	timeout /t 1 >nul
	goto wait_python
)


REM Start the application if both the batch and Python processes have terminated
start "" "./sc2_sensei_uploader.exe"
REM Delete the restart script if needed
del "%~f0"

"""

from typing import List, Optional, Union
import pathlib
def _install_update_win(
		src_dir: Union[pathlib.Path, str],
		dst_dir: Union[pathlib.Path, str],
		purge_dst_dir: bool,
		exclude_from_purge: List[Union[pathlib.Path, str]],
		as_admin: bool = False,
		batch_template: str = WIN_BATCH_TEMPLATE,
		batch_template_extra_kwargs: Optional[dict] = None,
		log_file_name: Optional[str] = None,
		robocopy_options_override: Optional[List[str]] = None,
):
	"""
	Create a batch script that moves files from src to dst, then run the
	script in a new console, and exit the current process.

	The script is created in a default temporary directory, and deletes
	itself when done.

	The `as_admin` options allows installation as admin (opens UAC dialog).

	The `batch_template` option allows specification of custom batch-file
	content. This may be in the form of a template string, as in the default
	`WIN_BATCH_TEMPLATE`, or it may be a ready-made string without any
	template variables. The following default template variables are
	available for use in the custom template, although their use is optional:
	{log_lines}, {src_dir}, {dst_dir}, {robocopy_options}, {delete_self}.
	Custom template variables can be used as well, in which case you'll need
	to specify `batch_template_extra_kwargs`.

	The `batch_template_extra_kwargs` options allows specification of
	*custom* template variables (in addition to the default ones, which are
	always available). It accepts a dict, with keys matching the *custom*
	template variable names specified in the `batch_template`.

	The `log_file_name` option will log the output of the install script to a
	file in the `dst_dir`.

	The `robocopy_options_override` option allows options for [robocopy][1]
	to be overridden completely. It accepts a list of option strings. This
	will cause the purge arguments to be ignored as well.

	[1]: https://docs.microsoft.com/en-us/windows-server/administration/windows-commands/robocopy
	"""
	if batch_template_extra_kwargs is None:
		batch_template_extra_kwargs = dict()
	# collect robocopy options
	if robocopy_options_override is None:
		robocopy_options = list(WIN_ROBOCOPY_OVERWRITE)
		if purge_dst_dir:
			robocopy_options.append(WIN_ROBOCOPY_PURGE)
			if exclude_from_purge:
				robocopy_options.append(WIN_ROBOCOPY_EXCLUDE_FROM_PURGE)
				robocopy_options.extend(exclude_from_purge)
	else:
		# empty list [] simply clears all options
		robocopy_options = robocopy_options_override
	options_str = ' '.join(robocopy_options)
	# handle batch file output logging
	log_lines = ''
	if log_file_name:
		log_file_path = pathlib.Path(dst_dir) / log_file_name
		log_lines = WIN_LOG_LINES.format(log_file_path=log_file_path)
		logger.info(f'logging install script output to {log_file_path}')
	# write temporary batch file (NOTE: The file is placed in the system
	# default temporary dir, but the file is not removed automatically. So,
	# either the batch file should self-delete when done, or it should be
	# deleted by some other means, because windows does not clean the temp
	# dir automatically.)
	script_content = batch_template.format(
		src_dir=src_dir,
		dst_dir=dst_dir,
		robocopy_options=options_str,
		log_lines=log_lines,
		delete_self=WIN_BATCH_DELETE_SELF,
		**batch_template_extra_kwargs,
	)
	logger.debug(f'writing windows batch script:\n{script_content}')
	with NamedTemporaryFile(
			mode='w', prefix=WIN_BATCH_PREFIX, suffix=WIN_BATCH_SUFFIX, delete=False
	) as temp_file:
		temp_file.write(script_content)
	logger.debug(f'temporary batch script created: {temp_file.name}')
	script_path = pathlib.Path(temp_file.name).resolve()
	logger.debug(f'starting script in new console: {script_path}')
	# start the script in a separate process, non-blocking
	# we use Popen() instead of run(), because the latter blocks execution
	# Start the batch update process
	update_process = subprocess.Popen([script_path], shell=True)

	# Write the restart script
	restart_script_path = 'restart_app.bat'
	with open(restart_script_path, 'w') as restart_script:
		restart_script.write(WIN_BATCH_RESTART_APP)  # Use the content from the batch script above

	# Start the restart script detached from the Python process, passing in the PIDs
	subprocess.Popen(['cmd', '/c', 'start', '/b', restart_script_path, str(update_process.pid), str(os.getpid())], shell=True)

	logger.debug('Restart script initiated.')



