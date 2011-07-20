import socket

HELLO_PREFIX = "OK MPD "
ERROR_PREFIX = "ACK "
SUCCESS = "OK"
NEXT = "list_OK"

class MPDError(Exception): pass
class ConnectionError(MPDError): pass
class ProtocolError(MPDError): pass
class CommandError(MPDError): pass
class CommandListError(MPDError): pass
class PendingCommandError(MPDError): pass
class IteratingError(MPDError): pass

class _NotConnected(object):
	def __getattr__(self, attr):
		return self._dummy

	def _dummy(*args):
		raise ConnectionError("Not connected")

class MPDProtocolClient(object):
	def __init__(self):
		self._reset()
    
	def _write_line(self, line):
		self._wfile.write("%s\n" % line)
		self._wfile.flush()

	def _read_line(self):
		line = self._rfile.readline()
		if not line.endswith("\n"):
			raise ConnectionError("Connection lost while reading line")
		line = line.rstrip("\n")
		if line.startswith(ERROR_PREFIX):
			error = line[len(ERROR_PREFIX):].strip()
			raise CommandError(error)
		if self._command_list is not None:
			if line == NEXT:
				return
			if line == SUCCESS:
				raise ProtocolError("Got unexpected '%s'" % SUCCESS)
		elif line == SUCCESS:
			return
		return line

	def _get_response(self):
		lines = []
		line = self._read_line()
		while line != None:
			lines.append(line)
			line = self._read_line()
		if len(lines) == 0:
			return
		else:
			return lines
	
	def _execute(self, *args):
		line = " ".join([args[0], " ".join([str(i) for i in args[1]])]).strip()
		if not self._pending:
			self._write_line(line)
			if self._command_list is not None:
				self._command_list.append(line)
			else:
				return self._get_response()
		else:
			raise PendingCommandError("Can't execute commands while other commands are pending")

	def _create_executor(self, command):
		return lambda *args: self._execute(command, args)

	def _get_commands(self):
		self._write_line("commands")
		available_commands = [com.split(":")[1].strip() for com in self._get_response()]
		for command in available_commands:
			if command != "idle":
				self.__dict__[command] = self._create_executor(command)

	def _hello(self):
		line = self._rfile.readline()
		if not line.endswith("\n"):
			raise ConnectionError("Connection lost while reading MPD hello")
		line = line.rstrip("\n")
		if not line.startswith(HELLO_PREFIX):
			raise ProtocolError("Got invalid MPD hello: '%s'" % line)
		self.mpd_version = line[len(HELLO_PREFIX):].strip()
		self._get_commands()

	def _reset(self):
		self.mpd_version = None
		self._pending = False
		self._command_list = None
		self._sock = None
		self._rfile = _NotConnected()
		self._wfile = _NotConnected()

	def _connect_unix(self, path):
		if not hasattr(socket, "AF_UNIX"):
			raise ConnectionError("Unix domain sockets not support"
			"on this platform")
		sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
		sock.connect(path)
		return sock

	def _connect_tcp(self, host, port):
		try:
			flags = socket.AI_ADDRCONFIG
		except AttributeError:
			flags = 0
		err = None
		for res in socket.getaddrinfo(host, port, socket.AF_UNSPEC,
									socket.SOCK_STREAM, socket.IPPROTO_TCP,
									flags):
			af, socktype, proto, canonname, sa = res
			sock = None
			try:
				sock = socket.socket(af, socktype, proto)
				sock.connect(sa)
				return sock
			except socket.error, err:
				if sock is not None:
					sock.close()
		if err is not None:
			raise err
		else:
			raise ConnectionError("getaddrinfo returns an empty list")

	def connect(self, host, port):
		if self._sock is not None:
			raise ConnectionError("Already connected")
		if host.startswith("/"):
			self._sock = self._connect_unix(host)
		else:
			self._sock = self._connect_tcp(host, port)
		self._rfile = self._sock.makefile("rb")
		self._wfile = self._sock.makefile("wb")
		try:
			self._hello()
		except:
			self.disconnect()
			raise

	def disconnect(self):
		self._rfile.close()
		self._wfile.close()
		self._sock.close()
		self._reset()

	def fileno(self):
		if self._sock is None:
			raise ConnectionError("Not connected")
		return self._sock.fileno()

	def command_list_ok_begin(self):
		if self._command_list is not None:
			raise CommandListError("Already in command list")
		self._write_line("command_list_ok_begin")
		self._command_list = []

	def command_list_end(self):
		if self._command_list is None:
			raise CommandListError("Not in command list")
		self._write_line("command_list_end")
		self._command_list = None
		return self._get_response()
	
	def idle(self, *subsystem):
		if self._pending == False:
			self._pending = True
			line = "idle " + " ".join(subsystem)
			self._write_line(line.strip())

	def noidle(self, *args):
		if self._pending == True:
			self._pending = False
			self._execute("noidle", args)