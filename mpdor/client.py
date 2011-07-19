import gobject
import mpd
import mpdor.info

class Client(gobject.GObject):
	__gsignals__ = {
			"database-change":  (gobject.SIGNAL_RUN_LAST, None, ()),
			"idle-change": (gobject.SIGNAL_RUN_LAST, None, (str,)),
			"message-change": (gobject.SIGNAL_RUN_LAST, None, ()),
			"mixer-change": (gobject.SIGNAL_RUN_LAST, None, (int,)),
			"options-change": (gobject.SIGNAL_RUN_LAST, None, (mpdor.info.MPDOptions,)),
			"output-change": (gobject.SIGNAL_RUN_LAST, None, ()),
			"player-change": (gobject.SIGNAL_RUN_LAST, None, (str,)),
			"player-paused": (gobject.SIGNAL_RUN_LAST, None, ()),
			"player-seeked": (gobject.SIGNAL_RUN_LAST, None, (float,)),
			"player-song-start": (gobject.SIGNAL_RUN_LAST, None, (mpdor.info.SongData,)),
			"player-stopped": (gobject.SIGNAL_RUN_LAST, None, ()),
			"player-unpaused": (gobject.SIGNAL_RUN_LAST, None, ()),
			"playlist-change": (gobject.SIGNAL_RUN_LAST, None, ()),
			"playlist-cleared": (gobject.SIGNAL_RUN_LAST, None, ()),
			"sticker-change": (gobject.SIGNAL_RUN_LAST, None, ()),
			"stored-playlist-change": (gobject.SIGNAL_RUN_LAST, None, ()),
			"subscription-change": (gobject.SIGNAL_RUN_LAST, None, ()),
			"update-change": (gobject.SIGNAL_RUN_LAST, None, ())
			}

	def __init__(self, host="localhost", port=6600, password="", connect_signals=True):
		gobject.GObject.__init__(self)
		
		self.set_server(host, port, password)		
		self.connect_to_server(connect_signals)

	def set_server(self, host, port, password):
		self.__host, self.__port, self.__password = host, port, password

	def connect_to_server(self, connect_signals=True):	
		# for commands
		self.__client = mpd.MPDClient()
		self.__client.connect(self.__host, self.__port)
		if self.__password not in ("", None):
			self.__client.password(self.__password)
		# we add the MPDClient methods to our client
		for command in self.__client.__dict__["_commands"]:
			if command.split()[0] in self.__client.commands():
				# for some reason, adding the methods directly doesn't work, so we use eval
				self.__dict__["_".join(command.split())] = \
						eval("self._Client__client." + "_".join(command.split()))
		self.command_list_ok_begin = self.__client.command_list_ok_begin
		self.command_list_end = self.__client.command_list_end
		self.mpd_version = self.__client.mpd_version
		
		# for signals, we create a secondary client, which will use the idle mechanism to handle events
		self.__notification_client = mpd.MPDClient()
		self.__notification_client.connect(self.__host, self.__port)
		if self.__password not in ("", None):
			self.__notification_client.password(self.__password)

		self.__paused = "pause" == self.__notification_client.status()["state"]
		self.__stopped = "stop" == self.__notification_client.status()["state"]
		self.__last_song = self.__notification_client.currentsong()

		self.__notification_client.send_idle()
		self.__notification_source = gobject.io_add_watch(self.__notification_client, \
				gobject.IO_IN, self.notify)

		if connect_signals:
			self.connect_signals()

	def disconnect_from_server(self):
		self.__client.disconnect()
		# we must clean the methods we added to the client
		for command in [com for com in self.__dict__ if com[0] != "_"]:
			if command != "mpd_version":
				del self.__dict__[command]
		
		self.__notification_client.disconnect()
		# we remove the event watcher
		gobject.source_remove(self.__notification_source)
	
	def notify(self, source, condition):
		changes = self.__notification_client.fetch_idle()
		self.emit("idle-change", ";".join(changes))

		status = self.__notification_client.status()
		
		for change in changes:
			if change == "mixer":
				self.emit("mixer-change", int(status["volume"]))
			
			elif change == "player":
				state = status["state"]
				self.emit("player-change", state)
				if state == "stop":
					self.emit("player-stopped")
					self.__stopped = True
				elif state == "pause":
					self.emit("player-paused")
					self.__paused = True
				else:
					current_song = self.__notification_client.currentsong()
					songdata = mpdor.info.SongData(current_song)
					if self.__paused == True:
						if current_song != self.__last_song:
							self.emit("player-song-start", songdata)
							self.__last_song = current_song
						self.emit("player-unpaused")
						self.__paused = False
					elif self.__stopped == True:
						self.emit("player-song-start", songdata)
						self.__stopped = False
					else:
						if current_song != self.__last_song:
							self.emit("player-song-start", songdata)
							self.__last_song = current_song
						else:
							self.emit("player-seeked", float(status["elapsed"]))
			
			elif change == "playlist":
				playlist = self.__notification_client.playlist()
				if len(playlist) < 1:
					self.emit("playlist-cleared")
				self.emit("playlist-change")
			
			elif change == "stored_playlist":
				self.emit("stored-playlist-change")
			
			elif change == "options":
				status["replay_gain_status"] = self.replay_gain_status()
				options = mpdor.info.MPDOptions(status)
				self.emit("options-change", options)
			
			else:
				self.emit(change+"-change")
		
		self.__notification_client.send_idle()
		return True
	
	def connect_signals(self):
		self.connect("database-change", self.on_database_change)
		self.connect("idle-change", self.on_idle_change)
		self.connect("message-change", self.on_message_change)
		self.connect("mixer-change", self.on_mixer_change)
		self.connect("options-change", self.on_options_change)
		self.connect("output-change", self.on_output_change)
		self.connect("player-change", self.on_player_change)
		self.connect("player-paused", self.on_player_paused)
		self.connect("player-seeked", self.on_player_seeked)
		self.connect("player-song-start", self.on_player_song_start)
		self.connect("player-stopped", self.on_player_stopped)
		self.connect("player-unpaused", self.on_player_unpaused)
		self.connect("playlist-change", self.on_playlist_change)
		self.connect("playlist-cleared", self.on_playlist_cleared)
		self.connect("sticker-change", self.on_sticker_change)
		self.connect("stored-playlist-change", self.on_stored_playlist_change)
		self.connect("subscription-change", self.on_subscription_change)
		self.connect("update-change", self.on_update_change)
	
	# Signal methods signatures
	def on_database_change(self, client): pass
	def on_idle_change(self, client, event): pass
	def on_message_change(self, client): pass
	def on_mixer_change(self, client, volume): pass
	def on_options_change(self, client, options): pass
	def on_output_change(self, client): pass
	def on_player_change(self, client, state): pass
	def on_player_paused(self, client): pass
	def on_player_seeked(self, client, pos): pass
	def on_player_song_start(self, client, songdata): pass
	def on_player_stopped(self, client): pass
	def on_player_unpaused(self, client): pass
	def on_playlist_change(self, client): pass
	def on_playlist_cleared(self, client): pass
	def on_sticker_change(self, client): pass
	def on_stored_playlist_change(self, client): pass
	def on_subscription_change(self, client): pass
	def on_update_change(self, client): pass
