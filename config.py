'''
Config functions such as read settings from file, logging, etc.
'''
import logging
from logging.handlers import TimedRotatingFileHandler
import shutil
import os, sys
from ConfigParser import SafeConfigParser
import ast

def Config_file(section, option):
	config = SafeConfigParser()
	config.read('config.conf')
	try:
		value = config.get(section, option)
	except Exception, e:
		logging.error('Error reading config.conf file!')
		logging.error(e)
		sys.exit(1)
	return value

def Credentials_file(section, option):
	config = SafeConfigParser()
	config.read('credentials.conf')
	try:
		value = config.get(section, option)
	except Exception, e:
		logging.error('Error reading credentials.conf file!')
		logging.error(e)
		sys.exit(1)
	return value

def init_logging():
	if DEBUGGING:
		Logging_level = logging.DEBUG
	else:
		Logging_level = logging.INFO
		# set logging level of requests  to warning (so higher than info), to prevent cluttering our output file
		logging.getLogger('requests').setLevel(logging.WARNING)
		logging.getLogger('urllib3').setLevel(logging.WARNING)
		
	logHandler = TimedRotatingFileHandler(LOG_FILE, when="midnight")
	logFormatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s', "%Y-%m-%d %H:%M:%S")
	logHandler.setFormatter(logFormatter)
#	logging.basicConfig(filename=LOG_FILE,level=Logging_level, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%d/%m/%Y %I:%M:%S %p')
	logger = logging.getLogger()
	logger.addHandler(logHandler)
	logger.setLevel(Logging_level)
	logging.info('*** Starting application: version %s ***' %VERSION)
	
def Remove_folder(folder):
    if (os.path.exists(folder) == True):
        try:
            shutil.rmtree(folder)
            logging.debug("Removing folder: " + folder)
        except IOError as e:
            logging.error(e)

def Preconditions(folder):
	if (os.path.exists(folder) == False):
		try:
			os.mkdir(folder)
			logging.debug("Creating folder: " + folder)
		except IOError as e:
			logging.error(e)

def Wanted():
	# Wishlist has a list of models that should be recorded
    try:
        with open(WANTED_FILE, 'r') as f:
                data = [line.strip() for line in f]
        f.close()
    except IOError, e:
        logging.info("Error: %s file does not appear to exist." % WANTED_FILE)
        logging.debug(e)
        sys.exit(1)
    return data

def Store_Debug(lines, filename):
	# Store html to debug.log file
	if (os.path.exists(DEBUG_FOLDER) == False):
		try:
			os.mkdir(DEBUG_FOLDER)
			logging.debug("Creating folder: debug")
		except IOError as e:
			logging.error(e)
	try:
		f = open(DEBUG_FOLDER + '/' + filename, 'a')
		for line in lines:
			f.write(line.encode("utf-8"))
		f.close()
	except IOError, e:
		logging.info("Error: debug.log file does not appear to exist.")

def Password_hash(string):
    #replace special chars for unix shell! \$ and \/ and \= mostly
    string = string.replace("\u003D","\=")
    string = string.replace("$", "\$")
    string = string.replace("/", "\/")
    return string
	
# Setup options
URL = Config_file('url','URL')
URL_FOLLOWED = Config_file('url', 'URL_FOLLOWED')
URL_SPY_SHOWS = Config_file('url', 'URL_SPY_SHOWS')
USER = Credentials_file('credentials','USER')
PASS = Credentials_file('credentials','PASS')
OUTPUT_FOLDER = Config_file('folders', 'OUTPUT_FOLDER')
VIDEO_FOLDER = OUTPUT_FOLDER + Config_file('folders','VIDEO_FOLDER')
TEMP_FOLDER = VIDEO_FOLDER + '/temp'
SCRIPTS_FOLDER = OUTPUT_FOLDER + Config_file('folders','SCRIPTS_FOLDER')
DEBUG_FOLDER = OUTPUT_FOLDER + Config_file('folders','DEBUG_FOLDER')
LOG_FILE = OUTPUT_FOLDER + Config_file('files','LOG_FILE')
WANTED_FILE = OUTPUT_FOLDER + Config_file('files','WANTED_FILE')
DELAY = int(Config_file('delays','DELAY'))
VERSION = Config_file('version','VERSION')
RTMPDUMP = Config_file('advanced','RTMPDUMP')
# Enable storing html to debug.log file + set logging level
DEBUGGING = ast.literal_eval(Config_file('debug','DEBUGGING'))
MINIMAL_RECORDING_SIZE_IN_MB = int(float(Config_file('advanced','MINIMAL_RECORDING_SIZE_IN_MB')))
# Constants
REC_START = 'R+'
REC_STOP = 'R-'
MODEL_ADD = 'M+'
MODEL_DEL = 'M-'
