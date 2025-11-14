import os, sys
import signal
import threading
import copy

from lobby.lobby_client import GameClient, LobbyClient, GamePlayer, get_lobby
import json

from dataclasses import dataclass, asdict, field
from typing import List, Optional, Dict, Any, Tuple, Callable

from flask import Flask, request, Response

from testsvr.testgame import GameTable, GameState, create_table




#######################################################
#
# Flask HTTP interface
#
app = Flask(__name__)



class TableMutex:
    def __init__(self) -> None:
        self._locks: Dict[str, threading.Lock] = {}
        self._guard = threading.Lock()

    def Lock(self, key: str) -> Callable[[], None]:
        # Return an unlock() closure (to mirror Go style)

        with self._guard:
            lock = self._locks.get(key)
            if lock is None:
                lock = threading.Lock()
                self._locks[key] = lock
        lock.acquire()

        unlocked = False

        def unlock() -> None:
            nonlocal unlocked # not part of inner function
            if not unlocked:
                lock.release()
                unlocked = True

        # return unlock() for unlocking.
        return unlock


STATE_MAP: Dict[ str, GameState ] = {}
TABLES : List[GameTable]  = []
table_mutex = TableMutex()


def initialize_tables():
   
    tables_json = os.getenv("GAME_SERVER_TABLES", "" )
    print(tables_json)
    raw_list = json.loads( tables_json )
    for table in raw_list:
        servername = table.get("servername")
        tablename = table.get("table").lower()
        bot_count = int(table.get("bot_count"))
        register_lobby = int(table.get("register_lobby"))
        table_obj, game_state = create_table( servername, tablename, bot_count, register_lobby )
        TABLES.append(table_obj)
        STATE_MAP[ tablename ] = game_state
        game_state.update_lobby()

def get_state( table:str, player:str ) -> Tuple[ Optional[GameState], Callable[ [], None]]:
    tbl = table.lower()
    plyr = ""
    if len(player) > 0:
        plyr = player.lower()

    unlock_fcn = table_mutex.Lock( tbl )

    tmp_state = STATE_MAP.get( tbl )
    if tmp_state is not None:
        state = copy.deepcopy( tmp_state )
        state.set_client_player_by_name( plyr )

    return state, unlock_fcn

def save_state( state: GameState ):
    STATE_MAP[ state.table] = state
  

def cleanup():
    for table, state in STATE_MAP.items():
        try:
            unlock_fcn = table_mutex.Lock( table )
            print("Try delete: " + state.servername )
            state.delete_from_lobby()
            unlock_fcn()
        except Exception as e:
            print(f"[cleanup] failed to delete lobby for table={getattr(gs, 'table', '?')}: {e}")


# Register the handlers
def shutdown_handler( signal_int, frame ):
    print(f"Caught signal: {signal_int}")
    cleanup()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)



@app.get("/view")
def api_view():
    tbl = request.args.get("table")
     
    state, unlock = get_state(tbl, "")
    try:
        if state is not None:
            state = state.create_client_state()
    finally:
        unlock()
    return state.to_json()


@app.post("/state")
def api_state():    
    # potentially use a hash to minimize HTTP traffic

    tbl = request.args.get("table")
    plyr = request.args.get("player")
    print("get state for " + request.args.get('table') )
    state, unlock = get_state(tbl, plyr)

    try:
        if state is not None:
            if state.client_player >= 0:
                state.run_game_logic()
            save_state(state)
            state = state.create_client_state()
        
    finally:
        unlock()
    return state.to_json()




@app.post("/move")
def api_move():
    tbl = request.args.get("table")
    plyr = request.args.get("player")
    move = request.args.get("move")
    print("get state for " + request.args.get('table') )
    state, unlock = get_state(tbl, plyr)

    try:
        if state is not None:
            if state.client_player == state.active_player:
                state.do_move( move )
            save_state(state)
            state = state.create_client_state()
        
    finally:
        unlock()
    return state.to_json()



@app.post("/leave")
def api_leave():
    tbl = request.args.get("table")
    plyr = request.args.get("player")
    state, unlock = get_state(tbl, plyr)
    try:
        if state is not None:
            if state.client_player >= 0:
                state.client_leave()
                state.update_lobby()
                save_state(state)
        
    finally:
        unlock()
    return state.to_json()
    


@app.get("/tables")
def api_tables():
    table_output : List[GameTable]  = []
    for table, state in STATE_MAP.items():
        try:
            unlock_fcn = table_mutex.Lock( table )
            
            state.update_lobby()
            unlock_fcn()
        except Exception as e:
            print(f"[cleanup] failed to delete lobby for table={getattr(gs, 'table', '?')}: {e}")




@app.get("/updateLobby")  
def api_update_lobby():
    for table, state in STATE_MAP.items():
        try:
            unlock_fcn = table_mutex.Lock( table )
            print("Try update: " + state.servername )
            state.update_lobby()
            unlock_fcn()
        except Exception as e:
            print(f"[cleanup] failed to update lobby for table={getattr(gs, 'table', '?')}: {e}")
            return ( { "result": "failed to update lobby"} )

    return ( { "result": "Lobby updated"} )


