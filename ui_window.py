import glob
from threading import Thread
import webview
import Environment_Variables
from tkinter import filedialog, Tk
import requests
from loguru import logger

from pystray import Icon as TrayIcon, Menu as TrayMenu, MenuItem as TrayMenuItem
from PIL import Image
import os

import pygetwindow as gw
import watchdog_uploader

class Sc2Sensei_UI_Pywebview():

	def __init__(self):
		# Create the window
		self.window = webview.create_window(
			'Sc2 Sensei Uploader', 
			f"http://127.0.0.1:{Environment_Variables.FLASK_RUN_PORT}/", 
			width=655, height=530, resizable=True, 
			js_api=self
		)
		self.window.min_size = (520, 200)
		self.window.events.closing += self.on_closing


	def change_tray_icon(self, icon_path):
		self.window.icon = icon_path
		image = Image.open(icon_path)
		self.tray_icon.icon = image

	def show_window(self):
		self.window.hide()
		self.window.show()

		window_title = "Sc2 Sensei Uploader"
		window = gw.getWindowsWithTitle(window_title)[0]
		if window:
			window.activate()

	def on_closing(self):
		t = Thread(target=self.hide_window)
		t.start()
		return False

	def hide_window(self):
		self.window.hide()

	def stop_threads(self):
		self.tray_icon.stop()  
		watchdog_uploader.stop() 
		self.window.events.closing -= self.on_closing
		self.window.destroy()
		resp = requests.get(f'http://127.0.0.1:{Environment_Variables.FLASK_RUN_PORT}/shutdown')
		

	def pick_folder(self):
		root = Tk()
		root.withdraw()  # Hide the main window

		initial_path = self.find_last_created_replay()
		if initial_path == None:
			initial_path = os.path.join(os.environ['USERPROFILE'], 'Documents', 'Starcraft II', 'Accounts')
		
		logger.info('initialdir is '+initial_path)

		# folder_selected = filedialog.askdirectory(initialdir=initial_path)
		# return folder_selected
		options = {
			'initialdir': initial_path, # I'm honestly not sure if this line does something
			'filetypes': [('', '*.Sc2Replay')],
			'title': 'Select Any Replay from your Replays Directory'
		}
		# Open the dialog
		filename = filedialog.askopenfilename(**options)

		root.destroy()
		if filename:
			directory = os.path.dirname(filename)
		else:
			directory = None  # User cancelled the dialog
		return directory

	def find_last_created_replay(self):
		initial_path = os.path.join(os.environ['USERPROFILE'], 'Documents', 'Starcraft II', 'Accounts')
		
		# Create a list of all .SC2Replay files within the initial_path, including subdirectories
		replay_files = glob.glob(os.path.join(initial_path, '**', '*.SC2Replay'), recursive=True)
		
		if len(replay_files) == 0:
			return None
		
		# Find the file with the latest creation time using max()
		latest_file = max(replay_files, key=os.path.getctime)
		
		return latest_file

	def setup_tray(self):
		
		image = Image.open(Environment_Variables.SC2SENSEI_ICON_PATH_RED)

		# Define the tray menu items
		menu = TrayMenu(
			TrayMenuItem("Show UI", self.show_window, default=True),
			TrayMenuItem("Exit", self.stop_threads)
		)

		# Create the tray icon
		self.tray_icon = TrayIcon("Sc2 Sensei Uploader", image, "Sc2 Sensei Uploader", menu)
