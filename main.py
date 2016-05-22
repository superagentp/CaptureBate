'''
Main file that includes all functions in appropriate order
'''
from config import *
from time import sleep
import connection
from ModelsManager import ModelsManager

if __name__ == '__main__':
	## Main section
	# Set logging
	init_logging()
	# Create directories
	Remove_folder(SCRIPTS_FOLDER)
	Preconditions(SCRIPTS_FOLDER)
	Preconditions(VIDEO_FOLDER)
	Preconditions(TEMP_FOLDER)
	# Instantiate ModelsManager
	mm = ModelsManager()
	
	while True:
	
		mm.update()

		sleep(DELAY)