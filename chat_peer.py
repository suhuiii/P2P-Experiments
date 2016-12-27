from peer import Peer
import time

BOOTSTRAP_LIST= [("127.0.0.1", 5001),("127.0.0.1", 5002), ("127.0.0.1", 5003)]

class Chat_Peer(Peer):
	def __init__(self, port, id, host = "127.0.0.1", bootstrap = True):
		Peer.__init__(self, host = host, port =port , myid = id)
		handlers = {"TEST": self.__handle_test, 
					"PING": self.__handle_ping, 
					"PONG": self.__handle_pong,
					"BROADCAST": self.__handle_broadcast}
		for h in handlers:
			self.add_handler(h, handlers[h])

		self.recvd_messages = []

		if bootstrap:
			self.bootstrap(BOOTSTRAP_LIST)

	def __handle_test(self, msg, originator, connection, time):
		print('Received TEST : %s from %s' % (msg, originator))

	def __handle_ping(self, msg, originator, connection, time):
		if not originator == self.my_id:
			self.add_peer(msg[0], msg[1], originator)
			self._send_ping(msg[0], msg[1], True)

	def __handle_pong(self, msg, originator, connection, time):
			self.add_peer(msg[0], msg[1], originator)

	def __handle_broadcast(self, msg, originator, connection, time):
			if originator == self.my_id:
				return
			if self._message_seen(msg, time):
				return

			print("%s %s said to all: %s" % (time, originator, msg))

			for peer_id, address in self.get_peers():
				if not peer_id == originator: 
					print("%s forwarding to %s" % (self.my_id, peer_id))
					host, port = address
					self.connect_and_send(host, port, "BROADCAST", msg, originator = originator, time = time)

	def _message_seen(self, msg, time):
		if (msg, time) in self.recvd_messages:
			return True

		self.recvd_messages.append((msg, time))
		if len(self.recvd_messages) > 10:
			self.recvd_messages.pop(0)

		return False

	def _send_ping(self, host, port, is_reply = False):
		if not is_reply:
			self.connect_and_send(host, port, "PING", self.get_my_addr())
			return

		self.connect_and_send(host, port, "PONG", self.get_my_addr())

	def broadcast(self, msg):
		broadcast_time = time.ctime()
		for peer_id, address in self.get_peers():
			host, port = address
			self.connect_and_send(host, port, "BROADCAST", msg, time = broadcast_time)

	def bootstrap(self, list):
		for host, port in list:
			self._send_ping(host, port)

if __name__ == '__main__':
	my_port = input("Port number to listen on: ")
	name = input("Enter username: ")
	
	chat = Chat_Peer(port =  my_port, id = name)

	data = ""
	while True:
		try:
			data = input(">")
			if data == "PRINT":
				[print(key,value) for key, value in chat.get_peers()]
			else:
				chat.broadcast(data)
		except KeyboardInterrupt:
			print("exiting...")
			break

	chat.shutdown()