import signal, sys

import threading, socketserver

from api.http_api import app
from api.tcp_api import TcpChessHandler

tcp_server = None

def start_tcp():
    global tcp_server
    tcp_server = socketserver.ThreadingTCPServer(("0.0.0.0", 55558), TcpChessHandler)
    threading.Thread(target=tcp_server.serve_forever, daemon=True).start()
    print("TCP listening on :55558")

def shutdown( signum, frame ):
    if tcp_server:
        tcp_server.shutdown() # stop it
        tcp_server.server_close()
    sys.exit(0)


if __name__ == "__main__":
    signal.signal( signal.SIGINT, shutdown )
    signal.signal( signal.SIGTERM, shutdown )
    start_tcp()
    app.run(host="0.0.0.0", port=55557)



