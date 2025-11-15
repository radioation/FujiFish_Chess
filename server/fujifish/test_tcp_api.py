import pytest
import socket
import threading
import time
import socketserver

from api.tcp_api import TcpChessHandler

from api.chess_game import ChessGame


@pytest.fixture
def tcp_server():
    server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), TcpChessHandler)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield host, port
    server.shutdown()
    server.server_close()
    thread.join()


def send_cmd(port, line):
    with socket.create_connection(("127.0.0.1", port), timeout=20) as sock:
        # First line is greeting
        greeting = sock.recv(1024).decode().strip()
        sock.sendall((line + "\r").encode())
        data = sock.recv(1024).decode().strip()
        return greeting, data

def test_new_and_state(tcp_server):
    host, port = tcp_server
    greet, resp = send_cmd(port, "N:S:W\n")
    assert greet.startswith("HELO")
    ids = resp.split()[1]
    assert ids[8] == ":"
    assert ids[:8].isalnum() == True
    assert ids[9:-1].isalnum() == True
    gid = ids[:8] 
    # Query state
    greet, resp = send_cmd(port, f"S:{gid}\n")
    assert "TURN w" in resp
    assert "MVNO 0" in resp

def test_new_SW10(tcp_server):
    host, port = tcp_server
    greet, resp = send_cmd(port, "N:S:W:10\n")
    assert greet.startswith("HELO")
    ids = resp.split()[1]
    assert ids[8] == ":"
    assert ids[:8].isalnum() == True
    assert ids[9:-1].isalnum() == True

def test_joingame(tcp_server):
    host, port = tcp_server
    greet, resp = send_cmd(port, "N:S:W\n")
    assert greet.startswith("HELO")
    ids = resp.split()[1]
    gameid = ids[:8]
    playid = ids[9:-1]

    greet, resp = send_cmd(port, "J:\n")
    assert resp == 'ERR invalid'

    greet, resp = send_cmd(port, "J:AAAAAAAA\n")
    assert resp == 'ERR invalid game id'

    greet, resp = send_cmd(port, f"J:{gameid}\n")
    assert resp == 'ERR invalid mode'

    greet, resp = send_cmd(port, "N:D:W\n")
    assert greet.startswith("HELO")
    ids = resp.split()[1]
    gameid = ids[:8]

    greet, resp = send_cmd(port, f"J:{gameid}\n")
    assert resp.startswith("ACK ")
    pid = resp.split()[1]
    assert pid.isalnum() == True


def test_move(tcp_server):
    host, port = tcp_server
    greet, resp = send_cmd(port, "N:S:W\n")
    assert greet.startswith("HELO")
    ids = resp.split()[1]
    gameid = ids[:8]
    playid = ids[9:-1]

    greet, resp = send_cmd(port, "M:------:W-\n")
    assert resp == 'ERR invalid format'

    greet, resp = send_cmd(port, "M:------:W:a\n")
    assert resp == 'ERR invalid format - g'

    greet, resp = send_cmd(port, "M:asdf1234:W:a\n")
    assert resp == 'ERR invalid format - p'

    greet, resp = send_cmd(port, "M:asdf1234:1234asdf:a\n")
    assert resp == 'ERR invalid format - m'

    greet, resp = send_cmd(port, "M:asdf1234:1234asdf:123456\n")
    assert resp == 'ERR invalid format - m'

    greet, resp = send_cmd(port, "M:asdf1234:1234asdf:e2e4\n")
    assert resp == 'ERR invalid game'

    greet, resp = send_cmd(port, "N:S:W\n")
    assert greet.startswith("HELO")
    ids = resp.split()[1]
    gameid = ids[:8]
    playid = ids[9:]
    greet, resp = send_cmd(port, f"M:{gameid}:{playid}:e2e4\n")
    assert resp.startswith("ACK ")
    pid = resp.split()[1]
    assert pid.isalnum() == True


def test_status(tcp_server):
    host, port = tcp_server
    greet, resp = send_cmd(port, "N:D:W\n")
    assert greet.startswith("HELO")
    ids = resp.split()[1].strip()
    gameid = ids[:8]
    playid = ids[9:]

    greet, resp = send_cmd(port, f'J:{gameid}\n')
    assert resp.startswith("ACK ")
    play2id = resp.split(' ')[1].strip()
    assert len(play2id) == 8

    # status
    greet, resp = send_cmd(port, f"S:{gameid}\n")
    assert resp == 'ACK TURN w:LAST -----:MVNO 0'

    greet, resp = send_cmd(port, f'M:{gameid}:{playid}:e2e4\n')
    assert resp.startswith("ACK ")
    

    # status
    greet, resp = send_cmd(port, f"S:{gameid}\n")
    assert resp == 'ACK TURN b:LAST e2e4:MVNO 1'

    greet, resp = send_cmd(port, f'M:{gameid}:{playid}:e2e4\n')
    assert resp == "ERR player 2 turn"

    greet, resp = send_cmd(port, f'M:{gameid}:{playid}:e7e6\n')
    assert resp == "ERR player 2 turn"

    # status
    greet, resp = send_cmd(port, f"S:{gameid}\n")
    assert resp == 'ACK TURN b:LAST e2e4:MVNO 1'



    greet, resp = send_cmd(port, f'M:{gameid}:{playid}:e7e6\n')
    assert resp == "ERR player 2 turn"
    # status
    greet, resp = send_cmd(port, f"S:{gameid}\n")
    assert resp == 'ACK TURN b:LAST e2e4:MVNO 1'


    greet, resp = send_cmd(port, f'M:{gameid}:{play2id}:e7e6\n')
    assert resp.startswith("ACK ")
    # status
    greet, resp = send_cmd(port, f"S:{gameid}\n")
    assert resp == 'ACK TURN w:LAST e7e6:MVNO 2'


def test_mate(tcp_server):
    host, port = tcp_server
    greet, resp = send_cmd(port, "N:D:W\n")
    assert greet.startswith("HELO")
    ids = resp.split()[1].strip()
    gameid = ids[:8]
    playid = ids[9:]

    greet, resp = send_cmd(port, f'J:{gameid}\n')
    assert resp.startswith("ACK ")
    play2id = resp.split(' ')[1].strip()
    assert len(play2id) == 8


    greet, resp = send_cmd(port, f'M:{gameid}:{playid}:f2f3\n')
    greet, resp = send_cmd(port, f'M:{gameid}:{play2id}:e7e5\n')
    greet, resp = send_cmd(port, f'M:{gameid}:{playid}:g2g4\n')
    greet, resp = send_cmd(port, f'M:{gameid}:{play2id}:d8h4\n')
    assert resp == 'ACK legal move Check Mate'
    greet, resp = send_cmd(port, f"S:{gameid}\n")
    assert resp == 'ACK OVER 0-1 1:TURN w:LAST d8h4:MVNO 4'



