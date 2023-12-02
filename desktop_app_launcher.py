import os
import shutil
import psutil
import sys
import tkinter as tk
import sc2_sensei_uploader_app
import app_updater as app_updater
import updater_app_settings

from loguru import logger

def ensure_tufup_folders_exist():
	for dir_path in [updater_app_settings.INSTALL_DIR, updater_app_settings.METADATA_DIR, updater_app_settings.TARGET_DIR]:
		dir_path.mkdir(exist_ok=True, parents=True)

	# The app must be shipped with a trusted "root.json" metadata file,
	# which is created using the tufup.repo tools. The app must ensure
	# this file can be found in the specified metadata_dir. The root metadata
	# file lists all trusted keys and TUF roles.
	if not updater_app_settings.TRUSTED_ROOT_DST.exists():
		shutil.copy(src=updater_app_settings.TRUSTED_ROOT_SRC, dst=updater_app_settings.TRUSTED_ROOT_DST)
		logger.info('Trusted root metadata copied to cache.')
	
def is_app_in_correct_path():
	exe = sys.executable
	exe_dir = os.path.dirname(exe)

	return os.path.samefile(exe_dir, updater_app_settings.INSTALL_DIR)


def is_app_already_running():
	application_name = os.path.basename(sys.argv[0])

	# Iterate over all running processes
	running_instances_count = 0
	for process in psutil.process_iter(['pid', 'name']):
		# Check if process name matches your application's name
		if process.info['name'] == application_name:
			running_instances_count += 1
	
	return running_instances_count >= 2


def show_warning_message():
	root = tk.Tk()
	root.withdraw()  # Hide the main window
	tk.messagebox.showinfo("Application Already Running", "App is already running. It can be located in the system tray.")
	root.destroy()


def show_location_error_message():
	logger.error('[Error] App is not in correct path')
	root = tk.Tk()
	root.withdraw()  # Hide the main window
	tk.messagebox.showerror("Error", "App is not in correct path. It should be located at \n" + str(updater_app_settings.INSTALL_DIR))
	root.destroy()



def main(cmd_args):
	if updater_app_settings.FROZEN:
		if is_app_in_correct_path() == False:
			show_location_error_message()
			sys.exit(0)

		if is_app_already_running():
			show_warning_message()
			sys.exit(0)  # Exit the second instance


	# The app must ensure dirs exist
	ensure_tufup_folders_exist()

	app_updater.update()
	
	sc2_sensei_uploader_app.run()