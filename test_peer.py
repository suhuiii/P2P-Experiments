from peer import Peer
from chat_peer import Chat_Peer
from peerconnection import PeerConnection
import pytest, socket, threading, time, json


@pytest.fixture(scope = 'function')
def peer():
	newpeer = Peer("Able","5000", "127.0.0.1", True, False)
	return newpeer

@pytest.fixture
def listening_socket():
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	return sock

@pytest.fixture(scope = 'function')
def chatpeer5001():
	return Chat_Peer("5001", "Baker", bootstrap = False)

@pytest.fixture
def chatpeer5002():
	return Chat_Peer("5002", "Charlie", bootstrap = False)

@pytest.fixture
def chatpeer5003():
	return Chat_Peer("5003", "Delta", bootstrap = False)

def test_setup_peer(peer):
	assert peer.get_my_id() == "Able"
	host, port = peer.get_my_addr()
	assert host == "127.0.0.1"
	assert port == 5000

def test_server_port_is_live(peer, listening_socket):
	server = peer.make_server_socket()
	result = listening_socket.connect_ex(("127.0.0.1", 5000))
	# returns 0 if okay

	server.close()
	listening_socket.close()

	if result:
		assert False
	else:
		assert True 

def test_peerconnection_can_send_and_receive(peer):
	test_data = {'msg_type': 'TEST', 'msg': 'test', 'originator': 'test_originator', 'time': time.time()}
	server = peer.make_server_socket()
	sending_socket = PeerConnection("127.0.0.1", 5000) 
	sending_socket.send_data(json.dumps(test_data))

	client_socket, client_addr = server.accept()
	connection = PeerConnection(client_addr[0], client_addr[1], client_socket)
	data = connection.recv_data()

	sending_socket.close()
	server.close()
	connection.close()

	assert data ==  test_data
	assert data['msg_type'] == "TEST"
	assert data['msg'] == "test"
	assert data['originator'] == "test_originator"
	assert data['time'] != '0'

def test_server_listening_thread_is_processing_data(peer, capfd):
	peer.start_listening()
	sending_socket = PeerConnection("127.0.0.1", 5000) 
	sending_socket.send_data(json.dumps({'msg_type': 'TEST', 'msg': 'test', 'originator': 'test_originator', 'time': time.time()}))
	sending_socket.close()
	peer.shutdown()

	out,err = capfd.readouterr()

	assert "Received TEST : test from test_originator" in out

def test_server_sends_data_to_itself(peer, capfd):
	peer.start_listening()
	peer.connect_and_send('127.0.0.1', 5000, "TEST", "test")
	peer.shutdown()

	out, err = capfd.readouterr()

	assert "Received TEST : test from Able" in out

def test_chatPeer__test_handler(chatpeer5001, capfd):
	chatpeer5001.connect_and_send('127.0.0.1', 5001, "TEST", "test")
	chatpeer5001.shutdown()

	out, err = capfd.readouterr()
	assert "Received TEST : test from Baker" in out

def test_chatPeer_pings_added_to_destination_peers(chatpeer5001, chatpeer5002):
	chatpeer5001._send_ping("127.0.0.1", 5002)

	peerlist = chatpeer5002.get_peers()
	chatpeer5001.shutdown()
	chatpeer5002.shutdown()
	assert ('Baker', ('127.0.0.1', 5001)) in peerlist

def test_chatPeer_pongs_complete_handshake(chatpeer5001, chatpeer5002):
	chatpeer5001.join("127.0.0.1", 5002)

	peerlist = chatpeer5001.get_peers()
	chatpeer5001.shutdown()
	chatpeer5002.shutdown()

	assert ('Charlie', ('127.0.0.1', 5002)) in peerlist

def test_chatPeer_test_broadcast_2_peers(chatpeer5001, chatpeer5002, capfd):
	chatpeer5001.join("127.0.0.1", 5002)

	# wait for a short while to ensure that peers are connected
	time.sleep(0.1)

	chatpeer5001.broadcast("Hello world")

	chatpeer5001.shutdown()
	chatpeer5002.shutdown()

	out, err = capfd.readouterr()

	assert out.count("Baker said to all: Hello world") is 1

def test_chatPeer_test_broadcast_3_peers(chatpeer5001, chatpeer5002, chatpeer5003, capfd):
	# create a network where 5002 is connected to both 5001 and 5003, 5001 and 5003 are not connected
	chatpeer5001._send_ping("127.0.0.1", 5002)
	chatpeer5002._send_ping("127.0.0.1", 5003)

	# give enough time to setup network
	time.sleep(0.1)

	# checks to ensure network is properly setup
	peerlist = chatpeer5001.get_peers()
	assert ('Charlie', ('127.0.0.1', 5002)) in peerlist

	peerlist = chatpeer5002.get_peers()
	assert ('Baker', ('127.0.0.1', 5001)) in peerlist
	assert ('Delta', ('127.0.0.1', 5003)) in peerlist

	# now test broadcast
	chatpeer5001.broadcast("Hello world")

	chatpeer5001.shutdown()
	chatpeer5002.shutdown()
	chatpeer5003.shutdown()

	out, err = capfd.readouterr()

	assert out.count("Baker said to all: Hello world") is 2
	assert err is ''

def test_chatPeer_test_broadcast_should_not_be_repeated_when_received_twice(chatpeer5001, chatpeer5002, chatpeer5003, capfd):
	# create a network where all peers are connected to each other
	chatpeer5001.bootstrap([("127.0.0.1", 5002),("127.0.0.1", 5003)])
	chatpeer5002._send_ping("127.0.0.1", 5003)

	time.sleep(0.1)

	peerlist = chatpeer5001.get_peers()
	assert ('Charlie', ('127.0.0.1', 5002)) in peerlist
	assert ('Delta', ('127.0.0.1', 5003)) in peerlist

	peerlist = chatpeer5002.get_peers()
	assert ('Baker', ('127.0.0.1', 5001)) in peerlist
	assert ('Delta', ('127.0.0.1', 5003)) in peerlist

	chatpeer5001.broadcast("Hello world")

	chatpeer5001.shutdown()
	chatpeer5002.shutdown()
	chatpeer5003.shutdown()

	out, err = capfd.readouterr()
	assert out.count("Baker said to all: Hello world") is 2
	assert err is ''

def test_chatPeer_advertises_peers(chatpeer5001, chatpeer5002, chatpeer5003, capfd):
	chatpeer5001.bootstrap([("127.0.0.1", 5002),("127.0.0.1", 5003)])
	time.sleep(0.1)

	chatpeer5002.connect_and_send("127.0.0.1", 5001, "ADVERTISE", "")
	time.sleep(0.1)

	out, err = capfd.readouterr()
	chatpeer5001.shutdown()
	chatpeer5002.shutdown()
	chatpeer5003.shutdown()
	assert "Baker advertised [\'Delta\', [\'127.0.0.1\', 5003]] as a connected peer" in out
	assert err is ''

def test_chatPeer_connects_to_advertised_peers(chatpeer5001, chatpeer5002, chatpeer5003):
	chatpeer5001.bootstrap([("127.0.0.1", 5002),("127.0.0.1", 5003)])
	time.sleep(0.1)

	peerlist = chatpeer5002.get_peers()
	assert ('Baker', ('127.0.0.1', 5001)) in peerlist
	assert not ('Delta', ('127.0.0.1', 5003)) in peerlist

	chatpeer5002.get_peers_from("Baker")
	time.sleep(0.1)

	peerlist = chatpeer5002.get_peers()
	chatpeer5001.shutdown()
	chatpeer5002.shutdown()
	chatpeer5003.shutdown()
	assert ('Baker', ('127.0.0.1', 5001)) in peerlist
	assert ('Delta', ('127.0.0.1', 5003)) in peerlist

def test_peer_does_not_exist(chatpeer5001, capfd):
	chatpeer5001.get_peers_from("A random name")
	out, err = capfd.readouterr()

	chatpeer5001.shutdown()

	assert "\"A random name\" not found in list of peers" in out

