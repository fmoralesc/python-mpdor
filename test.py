#!/usr/bin/env python2
import gobject
from mpdor.client import Client
try:
	from termcolor import colored
except:
	colored = False

class TestClient(Client):
	def on_idle_change(self, client, event):
		print "mpd event: @" + event

	def on_player_song_start(self, client):
		csong = self.currentsong()
		if colored:
			print colored(csong["title"], "white", attrs=("bold",)) + \
					" by " + colored(csong["artist"], "yellow", attrs=("bold",))
		else:
			print csong["title"] + " by " + csong["artist"]

	def on_player_stopped(self, client): print "stopped"
	def on_player_paused(self, client): print "paused"
	def on_player_unpaused(self, client): print "unpaused"
	def on_player_seeked(self, client): print "seeked"

if __name__ == "__main__":
	c = TestClient()
	gobject.MainLoop().run()
