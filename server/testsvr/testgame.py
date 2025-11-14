import os 
import threading
import copy
from lobby.lobby_client import GameClient, LobbyClient, GamePlayer, get_lobby 
from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any
import json

MAX_PLAYERS = 2
MIN_PLAYERS = 1

BOT_NAME = "marvin" # "Life! Don't talk to me about life..."

@dataclass
class GameTable:
    table: str      # descript  name with spaces
    name: str       # short name (3 char) 
    current_players: int = 0
    max_players: int = 0




# This game basically doesn't do anything but get move strings
# from alternating players and store them in an array

@dataclass
class Player:
    name: str
    move: str
    is_bot: bool

@dataclass
class GameState:
    active_player: int
    players: List[Player]
    client_player: int
    table: str
    servername: str
    register_lobby: bool
    max_players: int
    moves: List[str]
    lobby: LobbyClient
    hash: str = ""

    def __init__( self, table: str, servername: str, use_bot: bool, register_lobby: bool ):
        self.active_player = -1 
        self.players = []
        self.table = table
        self.servername = servername
        self.register_lobby = register_lobby
        self.max_players = int( os.getenv("GAME_MAX_PLAYERS", '2' ) )
        self.moves = []
        self.lobby = get_lobby()
        if use_bot:
            self.add_player(BOT_NAME, True)
        

    def add_player( self, player : str, is_bot:bool ) -> None:
        print(f'adding player {player} to array of size {len(self.players)}')
        if len(self.players) == self.max_players:
            return
        new_player = Player( name = player, move = '', is_bot = is_bot )
        self.players.append(new_player)
        if len(self.players) == self.max_players:
            self.active_player = 0 

    def set_client_player_by_name( self, player:str ) -> None:
        # no name, just a viewer 
        if len( player ) == 0 :
            self.client_player = -1
            return
        # has a name, so probably has an index in players list
        for index, item in enumerate( self.players ):
            if item.name == player:
                break
        else:
            index = -1
        self.client_player = index

        if self.client_player < 0 and len( self.players ) < self.max_players :
            self.add_player( player, False )
            self.client_player = len( self.players) - 1
            self.update_lobby()
             

    # nothing special here. every can see everything (just player names and move),
    # so the 5 card stud client perspective is not needed.
    def create_client_state(self ) -> 'GameState':
        state_copy = copy.deepcopy( self ) 
        return state_copy


    # --- JSON helpers ---
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)  
        d.pop("lobby", None )
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

   
    def run_game_logic(self) -> None:
        # no real logic, just here for example purposes.
        return 

    def do_move(self, move:str) -> None:
        # record move
        self.moves.append( move )

        # change active player
        self.active_player += 1
        if self.active_player >= self.max_players:
            self.active_player = 0
            
    def client_leave(self) -> None:
        # not an actual game, so no logic to really check.
        if self.client_player < 0:
            return 

        del( self.players[ self.client_player ] )

    def update_lobby(self) -> None:
        if not self.register_lobby :
            return
        human_player_slots, human_player_count = self.get_human_player_count_info()
        self.lobby.send_state_to_lobby( human_player_slots, human_player_count, True, self.servername, "?table=" + self.table )


    def delete_from_lobby(self) -> None:
        if not self.register_lobby :  
            # not in lobby, so nothing to do
            return
        self.lobby.delete_from_lobby( self.servername, "?table=" + self.table )


    def get_human_player_count_info(self) -> (int, int):
        human_available_slots = int( os.getenv( "GAME_SERVER_MAX_PLAYERS", "2" ) )
        human_player_count = 0
        
        for player in self.players:
            if player.is_bot:
                human_available_slots -= 1
            else:
                human_player_count += 1  # real game should check last ping from human

        return human_available_slots, human_player_count

def create_table( server_name: str, table: str, bot_count: int, register_lobby: bool ) -> (GameTable, GameState) :
    
    state = GameState( table, server_name, bot_count > 0, register_lobby )

    table_obj = GameTable( name = server_name, table = table )

    return table_obj, state


    # trying to be "simple" here. 
    #if do_lobby_updates:  # only send data if true?
    #    time.Sleep ( time.Milisend # give it a second?

   

 
