# Sc2 Sensei Uploader

## Aim of the Repository

This repository is intended to provide visibility into the code of the *Sc2 Sensei Uploader* application, allowing users and developers alike to verify its safety and integrity.  



## App Description

Sc2 Sensei Uploader is an companion application designed to integrate with the Sc2 Sensei website by uploading Starcraft 2 replay files. It features an automatic reaction to file creation by monitoring the folder where the Starcraft 2 game saves replays. This makes the process of uploading to Sc2 Sensei seamless and completely automatized.


## Features

- **Automatic File Upload**: Automatically uploads files to Sc2 Sensei upon their creation in the watched folder.
- **Folder Watching**: Uses a file watchdog to monitor a designated folder for new files.
- **User-friendly Interface**: Simple and intuitive interface written with HTML/CSS/JS, displayed using an internal chromium webengine served by a flask localhost server.


--------

## Running the Code

### Structure
The application requires communication with the Sc2 Sensei website for user validation and replay uploads, accomplished through POST requests

The website handles the parsing and analysis of replays, leaving the app responsible solely for detecting and uploading these files. Additionally, the website manages connections to the production DB, where parsed data is stored and associated with the respective user profiles.

For security reasons, the url endpoints used by the public website have been redacted from the code.  
I have also added a line to skip the login procedure by setting the *app.py:user_logged_in* variable to True.   
The rest of the code was unaltered.  
In practice, the app will work as intented, but replays will always result to the *failed* status, because the app doesn't have parsing capabilities.  

### Executing

1. Clone the repository to your local machine.
2. Install necessary dependencies using the requirements.txt file.
	```
	pip install -r requirements.txt
	```
3. Run main.py

### Usage

1. Open the application.
2. Set the folder you want to watch.
3. Press the 'Play' button to start the application. The button will turn green, indicating that the app is actively monitoring the folder.
4. Any new files added to this folder will automatically be uploaded to Sc2 Sensei.

### Code

The entry point to run the app is the *main.py* file.  

The app's main components are:

1) TUFUP, used to handle app updates (*app_updater.py*)
2) A Watchdog, used to detect and react to new files (*watchdog_uploader.py*)
3) A Flask localhost server, used to control the UI (*app.py*)
4) A Pywebview, used to draw the UI window in an integrated web-browser window (*ui_window.py*)

---------

## Demo

Check out the file *sc2_sensei_uploader.gif* for a small video demo, or this [reddit post](https://www.reddit.com/r/starcraft/comments/1890rwk/introducing_the_sc2_sensei_uploader_no_more/) for more info  


## Contributing

Contributions to the Sc2 Sensei Uploader are welcome! If you have suggestions for improvements or bug fixes, please feel free to submit a pull request.

## Contact

For any queries or feedback, please contact us at sc2sensei@gmail.com.  


## Acknowledgments

Special thanks to GalloTarallo, Mens, Lorimbo, and all of my Starcraft 2 comrades who have contributed to the development and testing of this app.