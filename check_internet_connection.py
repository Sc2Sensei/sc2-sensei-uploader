import socket

from functools import wraps
from flask import render_template

def is_connected():
	try:
		# Connect to Google's DNS server (8.8.8.8) on port 53 (DNS port)
		socket.create_connection(("8.8.8.8", 53))
		return True
	except OSError:
		pass
	return False
