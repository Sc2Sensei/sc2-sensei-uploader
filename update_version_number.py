import argparse
import re

def is_valid_version(version):
	return bool(re.match(r"^\d+\.\d+b*$", version))

	
def update_app_version(file_path, new_version):
	with open(file_path, "r") as f:
		lines = f.readlines()

	with open(file_path, "w") as f:
		for line in lines:
			if "APP_VERSION = " in line:
				f.write(f"APP_VERSION = '{new_version}'\n")
			else:
				f.write(line)

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description='Update APP_VERSION in a file.')
	parser.add_argument('new_version', type=str, help='New value for APP_VERSION')

	args = parser.parse_args()
	cli_arg = args.new_version

	if not is_valid_version(cli_arg):
		print(f"Invalid version format: {cli_arg}. Expected format is x.y where x and y are natural numbers.")
		exit(1)

	file_path = "updater_app_settings.py"  # Replace this with your actual file path

	update_app_version(file_path, cli_arg)
