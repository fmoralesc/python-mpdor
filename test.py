#!/usr/bin/env python2
import gobject
from mpdor.client import Client
from mpdor.protocol import MPDProtocolClient
try:
    from termcolor import colored
except:
    colored = False

class TestClient(Client):
    def on_player_song_start(self, client, songdata):
        if "artist" in songdata.__dict__:
            if colored:
                print colored(songdata.title, "cyan", attrs=("bold",)) + \
                        " by " + colored(songdata.artist, "yellow", attrs=("bold",))
            else:
                print songdata.title + " by " + songdata.artist
        else:
            if colored:
                print colored(songdata.title, "white", attrs=("bold",))
            else:
                print songdata.title

    def on_idle_change(self, client, event):
        print "mpd event: @" + event
    def on_player_stopped(self, client):
        print "stopped"
    def on_player_paused(self, client):
        print "paused"
    def on_player_unpaused(self, client):
        print "unpaused"
    def on_mixer_change(self, client, vol):
        print "volume:", vol
    def on_player_seeked(self, client, pos):
        print "seeked:", pos
    def on_options_change(self, client, options):
        print options

def callback(source, condition):
    if colored:
        print colored("protocol:", "red", attrs=("bold",)), source._get_response()
    else:
        print "protocol:", source._get_response()
    source.idle()
    return True

if __name__ == "__main__":
    c = TestClient()
    d = MPDProtocolClient()
    d.connect_to_server("localhost", 6600)
    d.idle()
    gobject.io_add_watch(d, gobject.IO_IN, callback)
    gobject.MainLoop().run()
