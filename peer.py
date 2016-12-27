import socket
from socket import *
import threading, sys, time, json
from peerconnection import PeerConnection

class Peer(object):
	def __init__(self, host, port, myid, debug = False, autostart = True):
		self.host = host
		self.listening_port = int(port)
		self.my_id = myid

		self.peers = {}
		self.handlers = {}
		self.threads = []

		self.debug = debug

		self.listening_thread = PeerListenerThread(target = self.listen_for_connections)

		if autostart:
			self.start_listening()

	def start_listening(self):
		self.serversocket = self.make_server_socket()
		self._debug('Server started on %s:%d' % (self.host, self.listening_port))

		self.listening_thread.start()

	def get_my_id(self):
		return self.my_id

	def get_my_addr(self):
		return (self.host, self.listening_port)

	def _debug(self, msg):
		if self.debug:
			print(msg)

	def shutdown(self):
		self.listening_thread.kill = True
		# print("killed")
		# print(self.listening_thread.is_alive())
		if self.listening_thread.is_alive():
			self.listening_thread.join()
		# print("killed again")
		[thread.join() for thread in self.threads if thread is not None or thread.is_alive()]
		
		self.serversocket.close()

	def make_server_socket(self):
		# set up TCP socket
		s = socket(AF_INET, SOCK_STREAM)
		# allow for reuse of ports before timeout
		s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		s.bind((self.host, self.listening_port))
		# number of backlog
		s.listen(5)
		s.settimeout(1)
		return s

	def connect_and_send(self, host, port, msg_type, msg, originator = None, time = None):
		reply = ''
		if originator is None:
			originator = self.my_id

		try: 
			connection = PeerConnection(host, port, self.debug)
			connection.send_data(self.build_json(msg_type, msg, originator, time))
			connection.close()
		except:
			self._debug("something went wrong sending data to %s:%d - %s"%(host, port, sys.exc_info()))

	def listen_for_connections(self):
		try:
			client_socket, client_addr = self.serversocket.accept()
			client_socket.settimeout(None)
			t = threading.Thread(target = self.__handle_connections, args= [client_socket, client_addr])
			t.start()
			self.threads.append(t)
		except:
			pass

	def __handle_connections(self, clientsock, client_addr):
		host, port = client_addr
		connection = PeerConnection(host, port, self.debug, clientsock)

		data = connection.recv_data()
		msg_type, msg, originator, time = self.extract_json(data)

		self._debug('Received %s : %s from %s' % (msg_type, msg, originator))

		self._handle_msg(msg_type, msg, originator, connection, time)
		connection.close()

	def extract_json(self, json_data):
		return (json_data['msg_type'], json_data['msg'], json_data['originator'], json_data['time'])

	def build_json(self, msg_type, msg, originator, time_recvd):
		# print(time)
		if time_recvd:
			return json.dumps({'msg_type':msg_type, 'msg': msg, 'originator': originator, 'time': time_recvd})
		return json.dumps({'msg_type':msg_type, 'msg': msg, 'originator': originator, 'time': time.ctime()})

	def add_peer(self, host, port, peer_id):
		if peer_id not in self.peers:
			self.peers[peer_id] = (host, int(port))
			self._debug('%s added to list of peers' % peer_id)
			return True
		self._debug('%s already in list of peers' % peer_id)
		return False

	def get_peers(self):
		return self.peers.items()

	def add_handler(self, msg_type, handler):
		self.handlers[msg_type] = handler

	def _handle_msg(self, msg_type, msg, originator, connection, time):
		if msg_type in self.handlers:
			self.handlers[msg_type](msg, originator, connection, time)
		else:
			self._debug("%s from %s not handled: %s" % (msg_type, originator, msg))

class PeerListenerThread(threading.Thread):
	def __init__(self, target):
		super(PeerListenerThread, self).__init__(target = target)
		self.kill = False

	def run(self):
		while not self.kill:
			self._target()
