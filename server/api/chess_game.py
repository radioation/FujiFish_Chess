import os
import uuid
import chess
import chess.engine

import threading


class ChessGame:
    def __init__(self, mode = 'S', player_1_side = 'W', level = 3):
        self.id = str(uuid.uuid4())[:8].upper()
        self.board = chess.Board()      
        self.engine_moves = []          # list of chess engine moves
        self.mode = mode                # single player 'S' or double player 'D'
        self.player_1_side = player_1_side  # for single player, which side is the player
                                        # that created the game: 'W', 'B'
        self.player_1_id = str(uuid.uuid4())[:8].upper()
        self.player_2_id = "NA"
        self.curr_player = 1
        if self.mode == 'D' and  player_1_side == 'B':
            self.curr_player = 2

        # Map skill level 1-10 to Stockfish config.
        self.skill_level = max(1, min(10, level))
        if level == 10:
            # Full strength
            self.engine_config = {"UCI_LimitStrength": False}
        else:
            elo_min, elo_max = 1320, 3190
            step = (elo_max - elo_min) / 9  # 9 intervals (levels 1–9)
            target_elo = int(elo_min + (level - 1) * step)
            self.engine_config ={"UCI_LimitStrength": True, "UCI_Elo": target_elo}


    def join_game( self ):
        if self.mode == 'D': 
            self.player_2_id = str(uuid.uuid4())[:8].upper()
        return self.player_2_id

    def do_move( self, pid, uci, movetime_ms ):
        # single player mode, player 2 should NEVER be able to move
        if self.mode == 'S' and pid == self.player_2_id:
            return ( { "valid": False, "message":"player 1 turn" } )

        # single player mode before p2 joins, don't allow
        if self.mode == 'D' and self.player_2_id == 'NA':
            return ( { "valid": False, "message":"game not started" } )
        
        if self.curr_player == 1 and pid != self.player_1_id:
            return ( { "valid": False, "message":"player 1 turn" } )
        if self.curr_player == 2 and pid != self.player_2_id:
            return ( { "valid": False, "message":"player 2 turn" } )
            
        try:
             mv = chess.Move.from_uci(uci)
        except ValueError:
            return ( { "valid": False, "message":"illegal move" } )

        if mv not in self.board.legal_moves:
            return ( { "valid": False, "message":"illegal move" } )

        # if we're here, save the move
        self.board.push(mv)
    
        if self.board.is_checkmate():
            return ( { "valid": True, "message":"legal move Check Mate" } )
        if self.board.is_stalemate():
            return ( { "valid": True, "message":"legal move Stale Mate" } )
        if self.board.is_insufficient_material():
            return ( { "valid": True, "message":"legal move Draw" } )

            
        # get reply from stockfish.
        with chess.engine.SimpleEngine.popen_uci(os.environ['ENGINE_PATH']) as eng:
            if self.mode == 'S':
                # potentially make dumb moves for single player.
                print( self.engine_config )
                eng.configure( self.engine_config )

            res = eng.play(self.board, chess.engine.Limit(time=movetime_ms/1000.0))
            if res.move is None:
                # No legal engine reply (mate/stalemate)
                if self.board.is_checkmate():
                    return ( { "valid": True, "message":"legal move Check Mate" } )
                if self.board.is_stalemate():
                    return ( { "valid": True, "message":"legal move Stale Mate" } )
                if self.board.is_insufficient_material():
                    return ( { "valid": True, "message":"legal move Draw" } )
                return ( { "valid": False, "message":"None" } )

            # compute best move
            best = res.move.uci()
            print("BEST: " +best)

            if self.mode == 'D':
                self.curr_player = 2 if self.curr_player == 1 else 1
                self.engine_moves.append(res.move)
            if self.mode == 'S':
                self.board.push(res.move)
            
            return ( { "valid": True, "message":"legal move", "engine_move":best } )

    def settings_str(self):
        return f"mode {self.mode}:p1side {self.player_1_side}:level {self.skill_level}:curr_player {self.curr_player}\n"

    def state_line(self):
        if self.mode == 'D' and self.player_2_id == "NA":
            return f"TURN -:LAST -----:MVNO 0"
        if self.board.outcome() == None:
            return f"TURN {'w' if self.board.turn else 'b'}:LAST {self.board.move_stack[-1] if self.board.move_stack else '-----'}:MVNO {len(self.board.move_stack)}"
        return f"OVER {self.board.outcome().result()} {self.board.outcome().termination.value}:TURN {'w' if self.board.turn else 'b'}:LAST {self.board.move_stack[-1] if self.board.move_stack else '-----'}:MVNO {len(self.board.move_stack)}"
         




GAMES = {}
GAMES_LOCK = threading.Lock()

def new_game(mode,side,level) -> ChessGame:
    g = ChessGame(mode,side,level)
    GAMES[g.id] = g
    return g

def get_game(gid: str) -> ChessGame | None:
    return GAMES.get(gid)


def get_two_player_games():
    two_player_games = [ key for key, value in GAMES.items() if value.mode == "D"]
    return two_player_games




