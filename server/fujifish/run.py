import signal, sys, os

from dotenv import load_dotenv

import threading, socketserver

from fujifish.http_api import app, initialize_tables
from lobby.lobby_client import init_lobby



if __name__ == "__main__":

    # get environment from .env files
    load_dotenv()    

    server_host = os.getenv('SERVER_HOST', "0.0.0.0")
    server_port = int(os.getenv('SERVER_PORT', 8080))
    lobby_endpoint = os.getenv('LOBBY_ENDPOINT_UPSERT')
    init_lobby( lobby_endpoint )
    

    initialize_tables()

    app.run(host=server_host, port=server_port)


