import json, sys
from socket import *

class PeerConnection(object):
	def __init__(self, host, port, sock = None, debug = False, ):
		self.debug = debug
		self.host = host
		self.port = port

		try:
			if sock:
				self.socket = sock
			else:
				self.socket = socket(AF_INET, SOCK_STREAM)
				self.socket.connect((host, port))

			self._debug('connected to %s:%d' % (host, port))
		except:
			self._debug('Unable to initialize connection to %s:%d - %s' %(host, port, sys.exc_info()))

	def recv_data(self):
		try:
			data = self.socket.recv(2048)
			json_data = json.loads(data.decode())
			if data:
				return json_data
			else:
				self._debug("Remote user has terminated the session.")
				return (None, None, None)
		except KeyboardInterrupt:
			raise
		except:
			pass

	def send_data(self, json_data):
		self.socket.send(json_data.encode())

	def close(self):
		self.socket.close()
		self.socket = None

	def _debug(self, msg):
		if self.debug:
			print(msg)

