from peer import Peer
import time, sys

BOOTSTRAP_LIST= [("127.0.0.1", 5001),("127.0.0.1", 5002), ("127.0.0.1", 5003)]

class Chat_Peer(Peer):
	def __init__(self, port, id, host = "127.0.0.1", bootstrap = True):
		Peer.__init__(self, id, port, host, False, True)
		handlers = {"TEST": self.__handle_test, 
					"PING": self.__handle_ping, 
					"PONG": self.__handle_pong,
					"BROADCAST": self.__handle_broadcast,
					"ADVERTISE": self.__handle_advt_peers,
					"ADVERTISE_REPLY": self.__handle_add_to_peers}
		for h in handlers:
			self.add_handler(h, handlers[h])

		self.recvd_messages = []

		if bootstrap:
			self.bootstrap(BOOTSTRAP_LIST)

	def __handle_test(self, msg, originator, connection, time):
		print('Received TEST : %s from %s' % (msg, originator))

	def __handle_ping(self, msg, originator, connection, time):
		self._debug("%s received ping from %s" % (self.my_id, originator))

		if not originator == self.my_id:
			print("--- %s: connected to %s ---" % (self.my_id, originator))
			self.add_peer(msg[0], msg[1], originator)
			self._send_ping(msg[0], msg[1], True)

	def __handle_pong(self, msg, originator, connection, time):
			print("--- %s: connected to %s ---" % (self.my_id, originator))
			self.add_peer(msg[0], msg[1], originator)

	def __handle_broadcast(self, msg, originator, connection, time):
		if originator == self.my_id:
			return

		if self._message_seen(msg, time):
			return

		print("--- BROADCAST at %s ---" % time)
		print("%s said to all: %s" % (originator, msg))

		for peer_id, address in self.get_peers():
			if not peer_id == originator: 
				self._debug("%s forwarding to %s" % (self.my_id, peer_id))
				host, port = address
				self.connect_and_send(host, port, "BROADCAST", msg, originator = originator, time = time)

	def __handle_advt_peers(self, msg, originator, connection, time):
		self._debug("--- %s advertising list of peers to %s ---" % (self.my_id, originator))
		host, port = self.find_peer(originator)

		for peer in self.get_peers():
			peerid, _ = peer
			if not peerid == originator:
				self.connect_and_send(host, port, "ADVERTISE_REPLY", peer)

	def __handle_add_to_peers(self, msg, originator, connection, time):
		print("--- %s: %s advertised %s as a connected peer ---" % (self.my_id, originator, msg))
		peerid, addr = msg
		host, port = addr

		self._send_ping(host, port)

	def _message_seen(self, msg, time):
		if (msg, time) in self.recvd_messages:
			return True

		self.recvd_messages.append((msg, time))
		if len(self.recvd_messages) > 10:
			self.recvd_messages.pop(0)

		return False

	def _send_ping(self, host, port, is_reply = False):
		if not is_reply:
			print("--- %s pinging %s:%s ---" % (self.my_id, host, port))
			self.connect_and_send(host, port, "PING", self.get_my_addr())
			return
		print("--- %s ponging %s:%s ---" % (self.my_id, host, port))
		self.connect_and_send(host, port, "PONG", self.get_my_addr())

	def join(self, host, port):
		if not host:
			host = "127.0.0.1"
		try:
			port = int(port)
			self._send_ping(host, port)
		except TypeError:
			print("Port number should be a number")
			return

	def broadcast(self, msg):
		broadcast_time = time.ctime()
		for peer_id, address in self.get_peers():
			host, port = address
			self.connect_and_send(host, port, "BROADCAST", msg, time = broadcast_time)

	def get_peers_from(self, peerid):
		try:
			host, port = self.find_peer(peerid)
			self.connect_and_send(host, port, "ADVERTISE", "")
		except ValueError:
			print("\"%s\" not found in list of peers" % peerid)

		return

	def bootstrap(self, list):
		for host, port in list:
			self._send_ping(host, port)



