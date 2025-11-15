# Running the server

1. setup python the way you would on your distro

```bash
sudo dnf install python3 python3-pip pytest

python3 -m venv env
. env/bin/activate
```


2.  install python-chess

```bash
pip3 install flask python-chess

```

3.  I'm using stockfish as the engine behind python-chess


```bash
cd ${YOUR_PATH_FOR_STOCKFISH}
wget https://github.com/official-stockfish/Stockfish/releases/latest/download/stockfish-ubuntu-x86-64-avx2.tar
tar -xvf stockfish-ubuntu-x86-64-avx2.tar
```

4. Run server with 

```bash
ENGINE_PATH = "/path/to/stockfish/stockfish-ubuntu-x86-64-avx2"
python3 run.py
```


You can also run the automated tests with

```bash
ENGINE_PATH = "/path/to/stockfish/stockfish-ubuntu-x86-64-avx2"
pytest test_http_api.y
pytest test_tcp_api.y
```

# Trying the interface 

HTTP with CURL
```bash

$  curl -X POST "http://localhost:55557/newgame" -d $'D\nW\n1\n'
9f8765a0:d2c9f9ba
$  curl -X POST "http://localhost:55557/joingame" -d $'9f8765a0\n'
3c8c6a97
$ curl -X POST "http://localhost:55557/move" -d $'9f8765a0\n3c8c6a97\ne2ef\n'
illegal move: player 1 turn
$ curl -X POST "http://localhost:55557/move" -d $'9f8765a0\nd2c9f9ba\ne2ef\n'
illegal move
$ curl -X POST "http://localhost:55557/move" -d $'9f8765a0\nd2c9f9ba\ne2e4\n'
c7c5
$ curl -X POST "http://localhost:55557/move" -d $'9f8765a0\nd2c9f9ba\ne7e5\n'
illegal move: player 2 turn
$ curl -X POST "http://localhost:55557/move" -d $'9f8765a0\n3c8c6a97\ne7e5\n'
d2d4
$ curl -X GET "http://localhost:55557/status?gid=9f8765a0"
TURN w:MVNO 2:LAST e7e5
$
```




$ curl -X POST "http://localhost:55557/newgame" -d $'S\nW\n1\n'
fd77aff0:e3061270
$ curl -X POST "http://localhost:55557/move" -d $'fd77aff0\ne3061270\ne2e4\n'
e7e6
$ curl -X POST "http://localhost:55557/move" -d $'fd77aff0\ne3061270\ne1e4\n'
illegal move
$ curl -X POST "http://localhost:55557/move" -d $'fd77aff0\ne3061270\nd2d3\n'
d7d5
$ curl -X GET "http://localhost:55557/board?gid=fd77aff0"
r n b q k b n r
p p p . . p p p
. . . . p . . .
. . . p . . . .
. . . . P . . .
. . . P . . . .
P P P . . P P P
R N B Q K B N R

curl -X GET "http://localhost:55557/status?gid=6918d8bc"

```
TCP with telnet

```bash
$ telnet 127.0.0.1 55558
Trying 127.0.0.1...
Connected to 127.0.0.1.
Escape character is '^]'.
HELO
N:S:W:1
ACK e78c2852:b6dc3dda

S:e78c2852
ACK mode:S p1side:W level:1 curr_player:1
TURN w:LAST -----:MVNO 0 
M:e78c2852:b6dc3dda
ERR:bad format
M:e78c2852:b6dc3dda:d2d3
ACK d7d5
S:e78c2852
ACK mode:S p1side:W level:1 curr_player:1

TURN w:LAST -----:MVNO 0 
M:e78c2852:b6dc3dda:d1d3
ACK illegal move
M:e78c2852:b6dc3dda:e2e4
ACK e7e6
B:e78c2852
ACK rnbqkbnrppp..ppp....p......p........P......P....PPP..PPPRNBQKBNR


HELO
N:S:W:1
ACK 0F673352:2CACA131

S:0F673352
ACK TURN w:LAST -----:MVNO 0

M:0F673352:2CACA131:AAAA
ERR illegal move

M:0F673352:2CACA131:e2e4
ACK legal move

S:0F673352
ACK TURN w:LAST e7e5:MVNO 2

M:0F673352:2CACA131:d2d3
ACK legal move

S:0F673352
ACK TURN w:LAST d7d6:MVNO 4

B:0F673352
ACK rnbqkbnrppp..ppp...p........p.......P......P....PPP..PPPRNBQKBNR


```




