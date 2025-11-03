
import pytest
import json
from api.http_api import app
from api.chess_game import ChessGame


def test_newgame_SW():
    client = app.test_client()

    # create a newgame
    resp = client.post("/newgame", data="S\nW\n")
    assert resp.status_code == 200
    assert len(resp.data) == 18   # plus 
    ids = resp.data.decode("utf-8")
    assert ids[8] == ":"
    assert ids[:8].isalnum() == True
    assert ids[9:-1].isalnum() == True

    # check status
    gameid =  ids[:8]
    resp = client.get(f"/status?gid={gameid}")
    assert resp.data.decode('utf-8') == 'TURN w:LAST -----:MVNO 0\n'
    assert resp.status_code == 200


def test_newgame_SW10():
    client = app.test_client()

    # create a newgame
    resp = client.post("/newgame", data="S\nW\n10\n")
    assert resp.status_code == 200
    assert len(resp.data) == 18   # plus 
    ids = resp.data.decode("utf-8")

    assert ids[8] == ":"
    assert ids[:8].isalnum() == True
    assert ids[9:-1].isalnum() == True


def test_joingame():
    client = app.test_client()

    # create a newgame
    resp = client.post("/newgame", data="S\nW\n")
    ids = resp.data.decode("utf-8")
    gameid =  ids[:8]
    playid = ids[9:-1]

    resp = client.post("/joingame")
    assert resp.data.decode('utf-8') == 'invalid\n'
    assert resp.status_code == 400


    resp = client.post("/joingame", data="AAAAAAAA\n")
    assert resp.data.decode('utf-8') == 'invalid gid\n'
    assert resp.status_code == 404

    resp = client.post("/joingame", data=f"{gameid}\n")
    assert resp.data.decode('utf-8') == 'invalid mode\n'
    assert resp.status_code == 400

    resp = client.post("/newgame", data="D\nW\n")
    ids = resp.data.decode("utf-8")
    gameid =  ids[:8]
    
    resp = client.post("/joingame", data=f"{gameid}\n")
    assert resp.data.decode('utf-8').strip().isalnum() == True
    assert resp.status_code == 200


    
def test_move():
    client = app.test_client()

    # check post data
    resp = client.post("/move", data="S\nW\n")
    assert resp.data.decode('utf-8') == "invalid format\n"
    assert resp.status_code == 400

    resp = client.post("/move", data="-----\nW\na\n")
    assert resp.data.decode('utf-8') == "invalid format - g\n"
    assert resp.status_code == 400

    resp = client.post("/move", data="abcd1234\nW\na\n")
    assert resp.data.decode('utf-8') == "invalid format - p\n"
    assert resp.status_code == 400

    resp = client.post("/move", data="abcd1234\n1234asdf\na\n")
    assert resp.data.decode('utf-8') == "invalid format - m\n"
    assert resp.status_code == 400

    resp = client.post("/move", data="abcd1234\n1234asdf\n123456\n")
    assert resp.data.decode('utf-8') == "invalid format - m\n"
    assert resp.status_code == 400

    resp = client.post("/move", data="abcd1234\n1234asdf\ne2e4\n")
    assert resp.data.decode('utf-8') == "invalid game\n"
    assert resp.status_code == 404

    resp = client.post("/move", data="abcd1234\n1234asdf\ne2e4\naaa\n")
    assert resp.data.decode('utf-8') == "invalid format - t\n"
    assert resp.status_code == 400

    resp = client.post("/move", data="abcd1234\n1234asdf\ne2e4\n350\n")
    assert resp.data.decode('utf-8') == "invalid game\n"
    assert resp.status_code == 404


    # create a newgame
    resp = client.post("/newgame", data="S\nW\n")
    ids = resp.data.decode("utf-8")
    gameid =  ids[:8]
    playid = ids[9:]

    resp = client.post("/move", data=f"{gameid}\n{playid}\ne2e4\n")
    assert resp.status_code == 200


def test_state():
    client = app.test_client()
    # create a newgame
    resp = client.post("/newgame", data="D\nW\n")
    ids = resp.data.decode("utf-8")
    gameid =  ids[:8]
    playid = ids[9:-1]
    client2 = app.test_client()
    resp = client2.post("/joingame", data=f"{gameid}\n")
    assert resp.status_code == 200
    play2id = resp.data.decode("utf-8").strip()
    assert len(play2id) == 8

    # status 
    resp = client.get(f"/status?gid={gameid}")
    assert resp.data.decode('utf-8') == 'TURN w:LAST -----:MVNO 0\n'
    assert resp.status_code == 200

    resp = client.post("/move", data=f"{gameid}\n{playid}\ne2e4\n")
    assert resp.status_code == 200

    # status 
    resp = client.get(f"/status?gid={gameid}")
    assert resp.data.decode('utf-8') == 'TURN b:LAST e2e4:MVNO 1\n'
    assert resp.status_code == 200

    resp = client.post("/move", data=f"{gameid}\n{playid}\ne2e4\n")
    assert resp.data.decode('utf-8') == 'player 2 turn'
    assert resp.status_code == 400

    resp = client.post("/move", data=f"{gameid}\n{playid}\ne7e6\n")
    assert resp.data.decode('utf-8') == 'player 2 turn'
    assert resp.status_code == 400

    # status 
    resp = client.get(f"/status?gid={gameid}")
    assert resp.data.decode('utf-8') == 'TURN b:LAST e2e4:MVNO 1\n'
    assert resp.status_code == 200



    resp = client2.post("/move", data=f"{gameid}\n{playid}\ne7e6\n")
    assert resp.data.decode('utf-8') == 'player 2 turn'
    assert resp.status_code == 400
    # status 
    resp = client.get(f"/status?gid={gameid}")
    assert resp.data.decode('utf-8') == 'TURN b:LAST e2e4:MVNO 1\n'
    assert resp.status_code == 200

    resp = client2.post("/move", data=f"{gameid}\n{play2id}\ne7e6\n")
    assert resp.status_code == 200
    # status 
    resp = client.get(f"/status?gid={gameid}")
    assert resp.data.decode('utf-8') == 'TURN w:LAST e7e6:MVNO 2\n'
    assert resp.status_code == 200



def test_mate():
    client = app.test_client()
    # create a newgame
    resp = client.post("/newgame", data="D\nW\n")
    ids = resp.data.decode("utf-8")
    gameid =  ids[:8]
    playid = ids[9:-1]
    client2 = app.test_client()
    resp = client2.post("/joingame", data=f"{gameid}\n")
    assert resp.status_code == 200
    play2id = resp.data.decode("utf-8").strip()
    assert len(play2id) == 8

    resp = client.post("/move", data=f"{gameid}\n{playid}\nf2f3\n")
    assert resp.data.decode('utf-8') == 'legal move'
    assert resp.status_code == 200

    resp = client2.post("/move", data=f"{gameid}\n{play2id}\ne7e5\n")
    assert resp.data.decode('utf-8') == 'legal move'
    assert resp.status_code == 200

    resp = client.post("/move", data=f"{gameid}\n{playid}\ng2g4\n")
    assert resp.data.decode('utf-8') == 'legal move'
    assert resp.status_code == 200

    resp = client2.post("/move", data=f"{gameid}\n{play2id}\nd8h4\n")
    assert resp.data.decode('utf-8') == 'legal move Check Mate'
    assert resp.status_code == 200

    # status 
    resp = client.get(f"/status?gid={gameid}")
    assert resp.data.decode('utf-8') == 'OVER 0-1 1:TURN w:LAST d8h4:MVNO 4\n'
    assert resp.status_code == 200



