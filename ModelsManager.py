
from bs4 import BeautifulSoup
import re
import time, datetime
import os, signal

from config import *
from Model import Model
import connection

class ModelsManager:

	def __init__(self):
#		self._client = client
#		self._followed = []		# contains a list of model id's (followed on chaturbate)
#		self._online = []		# contains a list of online model id's (followed on chaturbate)
		self._wanted = []		# contains a list of model id's (from the wanted file)
#		self._recording = []	# contains a list of model id's who are wanted and online
		self._models = []		# contains a list of Model objects (only those from the wanted file)
		return
		
	def get_model(self, model_id):
		for model in self._models:
			if model.get_id() == model_id:
				return model
				
	def update_wanted(self):
		# Post: self._wanted is a list of model_ids that should be recorded
		#		self._models is the list of models to be recorded (if they're online)
		try:
			with open(WANTED_FILE, 'r') as f:
					new_wanted_list = [line.strip() for line in f]
			f.close()
			for old_wanted in self._wanted:
				if not old_wanted in new_wanted_list:
					# User removed a model id from the wanted list
					logging.info("removing " + old_wanted)
					self._wanted.remove(old_wanted)
					model = self.get_model(old_wanted)
					model.destroy()
					self._models.remove(model)
			for new_wanted in new_wanted_list:
				if not new_wanted in self._wanted:
					# User added a model id to the wanted list
					logging.info("adding " + new_wanted)
					self._wanted.append(new_wanted)
					model = Model(new_wanted)
					model.init()
#					model.update()
					self._models.append(model)
		except IOError, e:
			logging.info("Error: %s file does not appear to exist." % WANTED_FILE)
			logging.debug(e)
			sys.exit(1)
		return
		
	def update_models(self):
		client = connection.Connection()
		for model in self._models:
			model.set_client(client)
			model.update()
		
	def update(self):
		self.update_wanted()
		self.update_models()
#		self.output_debug()
		
	def output_debug(self):
		data = "[DEBUG]_wanted:"
		for model_id in self._wanted:
			data = data + " " + model_id
		logging.info(data)
		
		data = "[DEBUG]_online:"
		for model_id in self._online:
			data = data + " " + model_id
		logging.info(data)
		
		data = "[DEBUG]_recording:"
		for model_id in self._recording:
			data = data + " " + model_id
		logging.info(data)
		
	