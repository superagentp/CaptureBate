from config import *

from bs4 import BeautifulSoup
import re
import time, datetime
import os, signal
import subprocess
import connection

class Model:

	def __init__(self, id):
		self._id = id
		self._online = False
		self._private = False
		self._client = None
		self._script_process = None
		self._pid = -1			# Recording script pid, note that the actual rtmpdump pid will be self._pid + 1
		self._flv = None		# The file we're rtmpdump-ing the recording to
		self._error = False		# self._error == True is something is wrong w/ this model's page
		
	def init(self):			
		self._client = connection.Connection()
		self._online = self.is_online()
		self._private = self.is_private()
		
		if self._error:
			logging.debug('[Model.init] ' + self._id + ' does not exist on site')
			return

		status_string = ''
		if DEBUGGING:
			status_string = '[Model.init]\t'
		status_string = status_string + "online:" + str(self._online) + " | private:" + str(self._private) + " -> model initialized"
		
		if self._online and not self._private:
			self.write_log(status_string + " and starting recording", REC_START)
			self._start_recording()
		else:
			self.write_log(status_string)
			
	def write_log(self, message, status = '  '):
		model_string = self._id
		id_length = len(model_string)

		if id_length < 8:
			model_string = model_string + '\t\t'
		elif id_length < 16:
			model_string = model_string + '\t'
		else:
			model_string = model_string + ' '

		logging.info(status + ' ' + model_string + message)
	
	def get_id(self):
		return self._id
		
	def set_client(self, client):
		self._client = client

	def is_recording(self):
		return self._pid != -1
		
	def is_online(self):
		# to be fixed: doesn't return False when model_id does not exist
		model_url = "https://chaturbate.com/" + self._id + "/"
		try:
			if DEBUGGING:
				logging.debug("[Model.is_online] Redirecting to " + model_url)
			response = self._client.get(model_url)
		except Exception, e:
			logging.debug('Some error during connecting to ' + URL)
			logging.error(e)
		soup = BeautifulSoup(response.text)
		if DEBUGGING:
			Store_Debug(soup, "debug_" + self._id + "_source.log")

		if response.status_code == 404:
			# response is "404", so self._id does not exist
			logging.error("[Model.is_online] " + model_url + " returned 404, so model does not exist")
			self._error = True
			return False
		else:
			logging.debug("[Model.is_online] " + model_url + " did not return 404, so model exists")
			
		offline_div = soup.find('div', class_="offline_tipping")
		if offline_div == None:
			# bs4 couldn't find the offline_tipping div, so model is online
			logging.debug("[Model.is_online] " + self._id + ": offline_div not found, so model is online")
			return True
		else:
			logging.debug("[Model.is_online] " + self._id + ": offline_div found, so model is offline")
			return False
	
	def is_private(self):
		if self._online:
			try:
				logging.debug("[Model.is_private] Redirecting to " + URL_SPY_SHOWS)
				response = self._client.get(URL_SPY_SHOWS)
				if DEBUGGING:
					Store_Debug('Page Source for ' + URL_SPY_SHOWS + '\n' + response.text, "url_spy_shows.source.log")
				soup = BeautifulSoup(response.text)
			except Exception, e:
				logging.error('Some error during connecting to '+ URL_SPY_SHOWS)
				logging.error(e)
			
			select_model_id_on_spy_shows = soup.select('a[href*="' + self._id + '"]')
			if select_model_id_on_spy_shows == []:
				logging.debug('[Model.is_private] ' + self._id + ' is online and not private')
				return False
			else:
				logging.debug('[Model.is_private] ' + self._id + ' is online and private')
				return True
		else:
			logging.debug('[Model.is_private] ' + self._id + ' is not online')
			return False
			
	def _is_still_recording(self):
		try: 
			# Check if rtmpdump pid is still active (sending kill -s 0)
			os.kill(self._pid + 1, 0) 
			return True
		except Exception, e:
			logging.debug('[Model._is_still_recording] pid ' + str(self._pid + 1) + ' not active, so rtmpdump must have died unplanned')
			logging.debug(e)
			return False

	def _update_status(self, new_online, new_private):
		self._online = new_online
		self._private = new_private

	def update(self):
		if self._error:
			return
			
		self._client = connection.Connection()
		new_online = self.is_online()
		new_private = self.is_private()
				 
		status_update = "online:" + str(self._online) + "->" + str(new_online) + " | private:" + str(self._private) + "->" + str(new_private)
		
		logging.debug('[Model.update]' + status_update)
		
#		if self._online and (not self._private):
#			# model was not in a private room and online
#			if (not new_online):
#				logging.info('R-\t' + self._id + '\twent offline while public, so stopping recording')
#				self._stop_recording()
#			elif new_private:
#				# model went into a private room, so stop recording
#				logging.info('R-\t' + self._id + '\twent private, so stopping recording')
#				self._stop_recording()
#			self._update_status(new_online, new_private)
#			return
#			
#		if (not new_private) and new_online:
#			# new status is public and online
#			if not ((not self._private) and self._online):
#				logging.info('R+\t' + self._id + ' went online or public, so starting recording')
#				self._start_recording()
#				
#		if new_online and self._online:
#			if (not new_private) and (not self._private):
#				# Should still be recording
#				if not self._is_still_recording():
#					# Recording died, so clean up recording script and restart recording
#					logging.info('R+\t' + self._id + '\trecording died, so restarting recording')
#					self._stop_recording()
#					self._start_recording()

		if self._online:
			# model was online
			if (not self._private):
				# model was online and not in a private room
				if new_online:
					# model stayed online
					if new_private:
						# model went into a private room, so stop recording
						self.write_log('went private, so stopping recording', REC_STOP)
						self._stop_recording()
					else:
						# model stayed public (not in private room)
						if not self._is_still_recording():
							# Recording died, so clean up recording script and restart recording
							self.write_log('recording died, so restarting recording', REC_START)
							self._stop_recording()
							self._start_recording()					
				else:
					# new_online == False, so model went offline
					self.write_log('went offline, so stopping recording', REC_STOP)
					self._stop_recording()
			else:
				# model was in a private room
				if (not new_private) and new_online:
					# model went public and stayed online
					self.write_log('left private room, so starting recording', REC_START)
					self._start_recording()
		else:
			# model was offline
			if new_online and (not new_private):
				self.write_log('went online, so starting recording', REC_START)
				self._start_recording()

		self._update_status(new_online, new_private)
				
	def _start_recording(self):
		logging.debug('[Model._start_recording] Starting recording for ' + self._id)
		model_url = "https://chaturbate.com/" + self._id + "/"
		r3 = self._client.get(model_url)
		soup = BeautifulSoup(r3.text)
		script_list =  soup.findAll('script')
		if DEBUGGING:
			logging.debug('[Model._start_recording] Script Source for ' + model_url + "\n" + str(script_list))
			page_source = '[Get_links] Script Source for ' + model_url + "\n" + str(script_list)
			Store_Debug(page_source, self._id + "_source.log")
		# Put model_page_source in the temporary file
		regex = re.compile(r""".*EmbedViewerSwf""", re.VERBOSE)

		script_list_lines = str(script_list).splitlines()

		for i,line in enumerate(script_list_lines):
			match = regex.match(line)
#			pw_match = re.search(r"password:\s'(pbkdf2_sha256.*[\\u003D|=])", line)
			pw_match = re.search(r"password:\s'(.*?.{120,})'", line)
			if pw_match:
				logging.debug('[Get_Links] found hashed password: %s' % pw_match.group(1))
				pw = Password_hash(pw_match.group(1))

			if match:
				flash_pl_ver = re.sub(',', '', re.sub(' ', '', re.sub('"', '', script_list_lines[i+1])))
				model_name = re.sub('\'', '', re.sub(',', '', re.sub(' ', '', re.sub('"', '', script_list_lines[i+2]))))
				stream_server = re.sub('\'', '', re.sub(',', '', re.sub(' ', '', re.sub('"', '', script_list_lines[i+3]))))
				logging.debug('Extracted:\n'+flash_pl_ver+'\n'+model_name+'\n'+stream_server)
				# write models rtmpdump string to file
				script_name = SCRIPTS_FOLDER+'/'+self._id+'.sh'
				flinks = open(script_name, 'w')
				flinks.write('#!/bin/sh\n')
				ts = time.time()
				st = datetime.datetime.fromtimestamp(ts).strftime('%Y.%m.%d_%H.%M')
				self._flv = st + '_' + self._id + '_chaturbate.flv'
				form_dict = {
					"rtmp_bin" : RTMPDUMP,
					"stream_server": stream_server,
					"model_name": model_name,
					"username": USER.lower(),
					"flash_ver": "2.645",
					"pw_hash": pw,
					"video_folder": VIDEO_FOLDER,
					"date_string": st,
					"flv": TEMP_FOLDER + '/' + self._flv,
				}
				rtmpdump_string = '%(rtmp_bin)s --quiet --live --rtmp "rtmp://%(stream_server)s/live-edge" --pageUrl "http://chaturbate.com/%(model_name)s" --conn S:%(username)s --conn S:%(model_name)s --conn S:%(flash_ver)s --conn S:%(pw_hash)s --token "m9z#$dO0qe34Rxe@sMYxx" --playpath "playpath" --flv "%(flv)s"' % form_dict
				flinks.write(rtmpdump_string)
				logging.debug('[Model._start_recording] rtmpdump_string: ' + rtmpdump_string)
				flinks.write('\n')
				flinks.close()
				os.chmod(SCRIPTS_FOLDER + '/' + self._id + '.sh', 0777)
#				logging.info('[Get_links] ' + self._id +'.sh is created')
				# shell = False to get the correct pid. Might have to change the path of the script to the absolute path.
#				self._pid = subprocess.Popen('./'+script_name, cwd='Scripts/')
#				script = '/home/robert/CaptureBate-master/'+script_name
#				script = '%(rtmp_bin)s --quiet --live --rtmp "rtmp://%(stream_server)s/live-edge" --pageUrl "http://chaturbate.com/%(model_name)s" --conn S:%(username)s --conn S:%(model_name)s --conn S:%(flash_ver)s --conn S:%(pw_hash)s --token "m9z#$dO0qe34Rxe@sMYxx" --playpath "playpath" --flv "%(video_folder)s/%(model_name)s_%(date_string)s_chaturbate.flv"' % form_dict
#				print script
				self._script_process = subprocess.Popen(script_name)
				self._pid = self._script_process.pid
				logging.debug('[Model._start_recording] Recording for ' + self._id + ' started with pid: ' + str(self._pid))
#				self._pid = subprocess.Popen(script_name).pid
#				flash_version = "2.645"
#				date_string = st				
#				script2 = []
#				script2.append(RTMPDUMP)
#				script2.append("--quiet")
#				script2.append("--live")
#				script2.append("--rtmp")
#				script2.append("rtmp://" + stream_server + "/live-edge")
#				script2.append("--pageUrl")
#				script2.append('"http://chaturbate.com/'+ model_name + '"')
#				script2.append('--conn')
#				script2.append('S:')
#				script2.append(USER.lower())
#				script2.append('--conn')
#				script2.append('S:')
#				script2.append(model_name)
#				script2.append('--conn')
#				script2.append('S:')
#				script2.append(flash_version)
#				script2.append('--conn')
#				script2.append('S:')
#				script2.append(pw)
#				script2.append('--token')
#				script2.append('"m9z#$dO0qe34Rxe@sMYxx"')
#				script2.append('--playpath')
#				script2.append('"playpath"')
#				script2.append('--flv')
#				script2.append('"' + VIDEO_FOLDER + '/' + model_name + '_' + date_string + '_chaturbate.flv' + '"')
#				script2.append('"/mnt/capturebate/Captured/test.flv"')
#				script2.append('"' + model_name + '_' + date_string + '_chaturbate.flv"')
#				self._pid = subprocess.call(script2)
#				logging.info('Started recording: ' + self._id + '.sh is running with pid ' + str(self._pid))
#				print 'Started ' + flv + ' with pid ' + str(self._pid)
				
	def _stop_recording(self):
		logging.debug('[Mode._stop_recording] Stopping recording: ' + self._id+ ' with pid ' + str(self._pid))
		# Terminating self._pid + 1, since that is the actual rtmp process spawned by the recording script
#		result = os.kill(self._pid + 1, signal.SIGKILL) # signal.SIGTERM
		try: 
			os.kill(self._pid + 1, signal.SIGTERM) # or signal.SIGKILL
		except Exception, e:
			logging.debug('[Model._stop_recording] kill ' + str(self._pid + 1) + ' failed')
			logging.debug(e)
			return
		
		self._script_process.communicate()
		
		# Check if the recording is at least MINIMAL_RECORDING_SIZE_IN_MB big
		if (os.path.getsize(TEMP_FOLDER + '/' + self._flv) >> 20) < MINIMAL_RECORDING_SIZE_IN_MB:
			# recording is smaller than the minimal recording size, so delete file

			# Deleting the recording, since it is too small
			logging.debug('[Model._stop_recording] Deleting temp recording ' + self._flv + ' since it is too small')
			os.remove(TEMP_FOLDER + '/' + self._flv)

		else:
			# recording is at least the minimal recording size, so move it to the saved folder
			# Make the recording read- and writeable to the world
			logging.debug('[Model._stop_recording] Making recording ' + self._flv + ' world read- and writeable')
			os.chmod(TEMP_FOLDER + '/' + self._flv, 0666)

			# Moving the recording
			logging.debug('[Model._stop_recording] Moving recording ' + self._flv + ' to ' + VIDEO_FOLDER)
			os.rename(TEMP_FOLDER + '/' + self._flv, VIDEO_FOLDER + '/' + self._flv)			
			
		# Clean up
		self._flv = None
		self._script_process = None
		self._pid = -1
	#		os.kill(self._pid, signal.SIGTERM) # or signal.SIGKILL
		logging.debug('[Model._stop_recording] Stopped recording: ' + self._id+ ' with pid ' + str(self._pid))
		
	def destroy(self):
		logging.debug('[Model.destroy] Starting cleanup of ' + self._id)
		if self._pid != -1:
			self._stop_recording()
		self._online = False
		self._private = False
		logging.debug('[Model.destroy] Completed cleanup of ' + self._id)
		
