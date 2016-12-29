from chat_peer import Chat_Peer
import time

def example():
	my_port = input("Port number to listen on: ")
	name = input("Enter username: ")
	autoconnect = input("Autoconnect (Y)? ")
	
	if autoconnect == "Y":
		bootstrap = True
	else:
		bootstrap= False

	chat = Chat_Peer(port =  my_port, id = name, bootstrap = bootstrap)

	command = ""
	time.sleep(0.2)
	print("Chat Peer started..")
	print("Available commands are: ")
	print("\tJOIN: connects to a user defined host and port of another chat peer")
	print("\tREQUEST: gets list of peers from another peer and attempts to connect to each of them")
	print("\tBROADCAST: sends a message to all peers on the network")
	print("\tQUIT: shuts down program")
	print("\tLIST: lists connected peers")

	cont = True
	try:
		while cont:	
			try:
				command = input(">")
				if command == "LIST":
					[print(key,value) for key, value in chat.get_peers()]
				elif command == "REQUEST":
					print("from which peer?")
					[print(key) for key, value in chat.get_peers()]
					peer = input("peer name: ")
					chat.get_peers_from(peer)
				elif command == "JOIN":
					host = input("Enter host: ")
					port = input("Enter port: ")
					chat.join(host, port)
				elif command == "QUIT":
					cont = False
				elif command == "BROADCAST":
					data = input("Msg to broadcast: ")
					chat.broadcast(data)
				else:
					print("Command not found. Try again")
			except EOFError:
				time.sleep(0.1)
				print("Empty input. Try again")
	except KeyboardInterrupt:
		print("shutdown initiated")
		chat.shutdown()
		print("chat closed")

if __name__ == '__main__':
	example()
