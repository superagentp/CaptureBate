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
		self._pid = -1			# Recording script pid, note that the actual rtmp pid will be self._pid + 1
		self._flv = None
		
	def get_id(self):
		return self._id
		
	def init(self):
		self._client = connection.Connection()
		self._online = self.is_online()
		self._private = self.is_private()
		
		status_string = "init model: " + self._id + " online:" + str(self._online) + " | private:" + str(self._private) + " -> model initialized"
		
		if self._online == True and self._private == False:
			logging.info(status_string + " and starting recording")
			self._start_recording()
		else:
			logging.info(status_string)
							
	def is_online(self):
		# to be fixed: doesn't return False when model_id does not exist
		model_url = "https://chaturbate.com/" + self._id + "/"
		try:
#			logging.info("Redirecting to " + model_url)
			response = self._client.get(model_url)
		except Exception, e:
			logging.error('Some error during connecting to '+URL)
			logging.error(e)
		soup = BeautifulSoup(response.text)
#		script_list =  soup.findAll('script')
		#logging.debug('[Get_links] Script Source for ' + "https://chaturbate.com/" + self._id + "/\n" + str(script_list))
#		page_source = '[Get_links] Script Source for ' + "https://chaturbate.com/" + self._id + "/\n" + str(script_list)
		if DEBUGGING == True:
#			Store_Debug(page_source, "/mnt/capturebate/debug_" + self._id + "_source.log")
			Store_Debug(soup, "debug_" + self._id + "_source.log")
		
#		print "\n" + self._id + "==================================\n"
#		body = soup.find('div', class_="content_body")
#		if not body == []:
#			logging.info(self._id + ": HTTP 404")
#			return False
		offline_div = soup.find('div', class_="offline_tipping")
		if offline_div == None:
			# bs4 couldn't find the offline_tipping div, so model is online
#			logging.info(self._id + ": offline_div not found")
			return True
		else:
#			logging.info(self._id + ": offline_div found")
			return False
	
	def is_private(self):
		if self._online:
			try:
#				logging.info("Redirecting to " + URL_SPY_SHOWS)
				response = self._client.get(URL_SPY_SHOWS)
			except Exception, e:
				logging.error('Some error during connecting to '+URL_SPY_SHOWS)
				logging.error(e)
			soup = BeautifulSoup(response.text)
			#logging.debug('Page Source for ' + URL_SPY_SHOWS + '\n' + response.text)
			page_source = 'Page Source for ' + URL_SPY_SHOWS + '\n' + response.text
			if DEBUGGING == True:
				Store_Debug(soup.prettify(), "url_spy_shows.log")
			
			select_model_id_on_spy_shows = soup.select('a[href*="' + self._id + '"]')
			if select_model_id_on_spy_shows == []:
#				print self._id + " online, and not found on private page"
				return False
			else:
#				print self._id + " online, but found on private page"
				return True
		else:
#			print self._id + " not online, so not on private page"
			return False

	def _update_status(self, new_online, new_private):
		self._online = new_online
		self._private = new_private

	def update(self):
		self._client = connection.Connection()
		new_online = self.is_online()
		new_private = self.is_private()
				 
		status_update = "update status: " + self._id + " online:" + str(self._online) + "->" + str(new_online) + " | private:" + str(self._private) + "->" + str(new_private)
		
		if self._private == False:
			# model was not in a private room
			if new_private == True:
				# model went into a private room
				if self._online == True:
					# stop recording
					logging.info(status_update + " | model went private, so stopping recording")
					self._stop_recording()
					self._update_status(new_online, new_private)
					return
					
		if (new_private == False) and (new_online == True):
			# new status is public and online
			if not ((self._private == False) and (self._online == True)):
				logging.info(status_update + " | model came online, so starting recording")
				self._start_recording()

		self._update_status(new_online, new_private)
				
	def _start_recording(self):
		r3 = self._client.get("https://chaturbate.com/"+self._id+"/")
		soup = BeautifulSoup(r3.text)
		script_list =  soup.findAll('script')
		#logging.debug('[Get_links] Script Source for ' + "https://chaturbate.com/" + self._id + "/\n" + str(script_list))
		page_source = '[Get_links] Script Source for ' + "https://chaturbate.com/" + self._id + "/\n" + str(script_list)
		if DEBUGGING == True:
			Store_Debug(page_source, self._id + "_source.log")
		## Put model_page_source in the temporary file
		regex = re.compile(r""".*EmbedViewerSwf""", re.VERBOSE)

		#print str(script_list).splitlines()
		script_list_lines = str(script_list).splitlines()

		for i,line in enumerate(script_list_lines):
			match = regex.match(line)
			pw_match = re.search(r"password:\s'(pbkdf2_sha256.*[\\u003D|=])", line)
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
				self._flv = VIDEO_FOLDER + '/' + self._id + '_' + st + '_chaturbate.flv'
				form_dict = {
					"rtmp_bin" : RTMPDUMP,
					"stream_server": stream_server,
					"model_name": model_name,
					"username": USER.lower(),
					"flash_ver": "2.645",
					"pw_hash": pw,
					"video_folder": VIDEO_FOLDER,
					"date_string": st,
					"flv": self._flv,
				}
				flinks.write('%(rtmp_bin)s --quiet --live --rtmp "rtmp://%(stream_server)s/live-edge" --pageUrl "http://chaturbate.com/%(model_name)s" --conn S:%(username)s --conn S:%(model_name)s --conn S:%(flash_ver)s --conn S:%(pw_hash)s --token "m9z#$dO0qe34Rxe@sMYxx" --playpath "playpath" --flv "%(flv)s"' % form_dict)
				flinks.write('\n')
				flinks.close()
				os.chmod(SCRIPTS_FOLDER+'/'+self._id+'.sh', 0777)
#				logging.info('[Get_links] ' + self._id +'.sh is created')
				# shell = False to get the correct pid. Might have to change the path of the script to the absolute path.
#				self._pid = subprocess.Popen('./'+script_name, cwd='Scripts/')
#				script = '/home/robert/CaptureBate-master/'+script_name
#				script = '%(rtmp_bin)s --quiet --live --rtmp "rtmp://%(stream_server)s/live-edge" --pageUrl "http://chaturbate.com/%(model_name)s" --conn S:%(username)s --conn S:%(model_name)s --conn S:%(flash_ver)s --conn S:%(pw_hash)s --token "m9z#$dO0qe34Rxe@sMYxx" --playpath "playpath" --flv "%(video_folder)s/%(model_name)s_%(date_string)s_chaturbate.flv"' % form_dict
#				print script
				self._script_process = subprocess.Popen(script_name)
				self._pid = self._script_process.pid
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
		logging.info('Stopping recording: ' + self._id+ 'with pid ' + str(self._pid))
		# Terminating self._pid + 1, since that is the actual rtmp process spawned by the recording script
#		result = os.kill(self._pid + 1, signal.SIGKILL) # signal.SIGTERM
		os.kill(self._pid + 1, signal.SIGTERM) # or signal.SIGKILL
		self._script_process.communicate()

		# Make the recording read- and writeable to the world
		os.chmod(self._flv, 0666)
		
		self._flv = None
		self._script_process = None
		self._pid = -1
#		os.kill(self._pid, signal.SIGTERM) # or signal.SIGKILL
#		logging.info('Terminated rtmpdump process')
		
	def destroy(self):
		if self._pid != -1:
			self._stop_recording()
		self._online = False
		self._private = False
		
	def set_client(self, client):
		self._client = client