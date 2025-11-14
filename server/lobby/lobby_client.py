import os
import json
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

#######################################################
#
# Lobby values
#

# don't use the real for now
LOBBY_ENDPOINT_UPSERT = "http://irata.greggallardo.com:8080/server"
#LOBBY_ENDPOINT_UPSERT = "http://127.0.0.1:8080/server"
LOBBY_QA_ENDPOINT_UPSERT = "http://irata.greggallardo.com:8080/server"


#######################################################
#
# Lobby Data models
#

@dataclass
class GameClient:
    platform: str      # name of the platform specific client (Required. Printable ASCII chars)
    url: str           # Platform specific URL of the game client (Required. Valid URL. 64 URL chars max)

    def to_dict(self) -> Dict[str, Any]:
        return {"platform": self.platform, "url": self.url}


def load_game_clients_from_json(json_str: str) -> List[GameClient]:
    """
    Expected JSON shape:
    [
      {"platform": "atari", "url": "tnfs://..."},
      {"platform": "msdos","url": "tnfs://..."},
      ...
    ]
    """
    raw_list = json.loads(json_str)

    clients: List[GameClient] = []
    for item in raw_list:
        # allow either "platform"/"url" or "Platform"/"Url" just in case
        platform = item.get("platform") or item.get("Platform")
        url = item.get("url") or item.get("Url")

        if platform is None or url is None:
            raise ValueError(f"Missing platform or url in item: {item}")

        clients.append(GameClient(platform=platform, url=url))

    return clients


@dataclass
class GamePlayer:
    name: str
    winner: bool
    type: str  # "bot" | "human"
    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "winner": self.winner, "type": self.type}


@dataclass
class GameResult:
    players: List[GamePlayer] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"players": [p.to_dict() for p in self.players]}


@dataclass
class GameServer:
    #  http://fujinet.online:8080/docs

    game: str         # Name of game to be shown by the game client to the user ( Required. 2-16 chars)
    appkey: int       # Registered ID of Game ( Required.  https://github.com/FujiNetWIFI/fujinet-firmware/wiki/SIO-Command-%24DC-Open-App-Key )
    server: str       # Name & version of the game server used ( Required. Printable ASCII chars. 32 chars max)
    region: str       # Region where the server is hosted  ( Required. Printable ASCII characters. 2 chars max)
    serverurl: str    # URL of the server where the game client will connect (must be valid URL. 64 chars max )
    status: str       # Status of the game server: required  "online" | "offline" 
    maxplayers: int   # Maximum number of players the server can accept (Required. integer >=0 )
    curplayers: int   # current number of players connect to the server (Required. integer >=0 && <= maxplayers
    clients: List[GameClient] = field(default_factory=list)
    game_result: Optional[GameResult] = None  #

    @classmethod
    def from_defaults(
        cls,
        game: str,
        region: str,
        base_url: str,
        server_name: str,
        *,
        appkey: int = os.getenv("LOBBY_CLIENT_APP_KEY" ),
        maxplayers: int = 0,
        curplayers: int = 0,
        status: str = "offline",
        clients: Optional[List[GameClient]] = None,
        
    ) -> "GameServer":
        return cls(
            game=game,
            appkey=appkey,
            server=server_name,
            region=region,
            serverurl=base_url.rstrip("/"),
            status=status,
            maxplayers=maxplayers,
            curplayers=curplayers,
            clients=clients or [],
        )


    @classmethod
    def from_env(cls,
        *,
        server_name: str,
        is_online: bool,
        max_players: Optional[int] = None, 
        cur_players: Optional[int] = None, 
        game_result: Optional[GameResult] = None
        ) -> "GameServer":

        # Max should be up to game logic: go with 0 here
        env_maxplayers=0,
        env_curplayers=0, 
        
        # override as needed
        final_maxplayers = max_players if max_players is not None else  env_maxplayers 
        final_curplayers = cur_players if cur_players is not None else  env_curplayers 
        temp_appkey=os.getenv("LOBBY_CLIENT_APP_KEY" )
        if temp_appkey is None:
            raise ValueError( f"LOBBY_CLIENT_APP_KEY is required!" )

        final_appkey=int(os.getenv("LOBBY_CLIENT_APP_KEY" ))
         
        return cls(
            appkey=int(final_appkey),        # default appkey from env
            game=os.getenv("GAME_NAME",""),  # default name from env
            region=os.getenv("SERVER_REGION", 'us'),  # default region from env
            serverurl=os.getenv("GAME_SERVER_URL", "https://irata.greggallardo.com"), # default server url 
            server=server_name,
            status= "online" if is_online else "offline",
            maxplayers=final_maxplayers,
            curplayers=final_curplayers,
            clients=load_game_clients_from_json( os.getenv("GAME_CLIENT_PLATFORMS" ) ),
            game_result = game_result,
            
        )


    def to_dict(self) -> Dict[str, Any]:
        """
        
        """
        payload = {
            "game": self.game,
            "appkey": self.appkey,
            "server": self.server,
            "region": self.region,
            "serverurl": self.serverurl,
            "status": self.status,
            "maxplayers": self.maxplayers,
            "curplayers": self.curplayers,
            "clients": [c.to_dict() for c in self.clients],
        }
        if self.game_result is not None:
            payload["game_result"] = self.game_result.to_dict()
        return payload


    def set_online(self) -> None:
        self.status = "online"

    def set_offline(self) -> None:
        self.status = "offline"

    def set_players(self, cur: int, maxp: Optional[int] = None) -> None:
        self.curplayers = cur
        if maxp is not None:
            self.maxplayers = maxp

    def set_game_result(self, result: Optional[GameResult]) -> None:
        self.game_result = result


#######################################################
#
# Actual Lobby Client to connect to a Lobby
#



class LobbyClient:
   
    
    def __init__(self, lobby_endpoint: str = LOBBY_ENDPOINT_UPSERT, *, timeout_connect: float = 3.0, timeout_read: float = 10.0):
        print("---------------------------------")
        env_lobby_endpoint = os.getenv("LOBBY_ENDPOINT_UPSERT" )
        print( env_lobby_endpoint)
        if env_lobby_endpoint is None:
            self.lobby_endpoint = lobby_endpoint
        else:
            self.lobby_endpoint = env_lobby_endpoint
        self._timeout = (timeout_connect, timeout_read)
        print("---------------------------------")

    def do_upsert(self, server: GameServer) -> requests.Response:
        payload = server.to_dict()
        print("Upsert %s to Lobby: %s"  % (payload, self.lobby_endpoint))
        resp = requests.post(self.lobby_endpoint, json=payload, timeout=self._timeout)
        # Log errors verbosely
        if resp.status_code >= 300:
            snippet = resp.text[:512]
            print("Lobby Response %s: %s", resp.status_code, snippet)
        else:
            print("Lobby Response %s", resp.status_code)
        resp.raise_for_status()
        return resp

    def send_state_to_lobby(self,  max_players: int, cur_players: int, is_online: bool, server: str, instance_url_suffix: str, game_result: GameResult = None ) -> requests.Response:
        server_details = GameServer.from_env(
            server_name = server,
            is_online =  "online" if is_online else "offline",
            max_players = max_players,  
            cur_players = cur_players,  
            game_result = game_result,
        )
        server_details.serverurl += instance_url_suffix
        
        self.do_upsert( server_details ) 


    def delete_from_lobby(self,  server: str, instance_url_suffix: str ) -> requests.Response:
        server_details = GameServer.from_env(
            server_name = server,
            is_online = "offline",
        )
        server_details.serverurl += instance_url_suffix
        payload = server_details.to_dict()
        print("Delete from Lobby: %s", payload)
        resp = requests.delete(self.lobby_endpoint, json=payload, timeout=self._timeout)

        # Log errors verbosely
        if resp.status_code >= 300:
            snippet = resp.text[:512]
            print("Lobby Response %s: %s", resp.status_code, snippet)
        else:
            print("Lobby Response %s", resp.status_code)
        resp.raise_for_status()
        
        return resp




_lobby: Optional[LobbyClient] = None

def init_lobby( lobby_endpoint: Optional[str] = None ) -> None:
    global _lobby 
    if _lobby is not None:
        return

    lobby_endpoint = lobby_endpoint or LOBBY_ENDPOINT_UPSERT
    _lobby = LobbyClient( lobby_endpoint = lobby_endpoint )

def get_lobby() -> LobbyClient:
    if _lobby is None:
        raise RuntimeError("Lobby not initialized; call init_lobby() first")
    return _lobby


