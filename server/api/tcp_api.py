# tcp_protocol.py
import socketserver, threading
from api.chess_game import new_game, get_game, get_two_player_games
import re


class TcpChessHandler(socketserver.StreamRequestHandler):
    def handle(self):
        print("connected")
        self.wfile.write(b"HELO\n")
        for line in self.rfile:
            print("pre-strip: ", end="" )
            print(line)
            line = line.decode("utf-8").strip()
            print("POST-strip: " + line)
            if not line:
                continue
            response = self.dispatch(line)
            print(response)
            self.wfile.write((response + "\n").encode("utf-8"))

    def dispatch(self, line: str) -> str:
        try:
            if line.startswith("N:"):
                mode = 'S'
                player_1_side = 'W'
                level = 3
                parts = line.split(":")
                if len(parts) > 1 :
                    mode = parts[1].strip()
                if len(parts) > 2 :
                    player_1_side = parts[2].strip()
                if len(parts) > 3 :
                    level = int(parts[3].strip())

                g = new_game(mode, player_1_side, level )

                return f"ACK {g.id}:{g.player_1_id}\n"
            elif line.startswith("J:"):
                parts = line.split(":")
                if len(parts) < 2:
                    return "ERR invalid\n"
                gid = parts[1]
                if len(gid) == 0:
                    return "ERR invalid\n"
                game = get_game(gid)
                if game is None: 
                    return "ERR invalid game id\n"
                if game.mode == 'D':
                    game.join_game()
                    return f"ACK {game.player_2_id}\n"
                else:
                    return "ERR invalid mode\n"
            elif line.startswith("M:"):
                parts = line.split(":")
                if len(parts) < 4: return "ERR invalid format\n"

                gid, pid, uci_move = parts[1], parts[2], parts[3]
                if not gid.isalnum() or ( gid.isalnum() and  len(gid) != 8 ):
                    return "ERR invalid format - g\n"
                if not pid.isalnum() or ( pid.isalnum() and  len(pid) != 8 ):
                    return "ERR invalid format - p\n"
                if not uci_move.isalnum() or len(uci_move) > 5 or len(uci_move) < 4:
                    return "ERR invalid format - m\n"

                game = get_game(gid)
                if game is None:
                    return "ERR invalid game\n"
                movetime_ts = 300
                move_result = game.do_move( pid, uci_move, movetime_ts)
                print( move_result )
                if move_result['valid'] == True:
                    #if 'engine_move' in move_result:
                    #    res = "ACK " + move_result['engine_move']
                    #else:
                    res = "ACK " + move_result['message']
                else:
                    res = "ERR " + move_result['message']
                return res  
            elif line.startswith("B:"):
                gid = line.split(":",1)[1]
                game = get_game(gid)
                sboard = str(game.board)
                print( sboard )
                
                strboard = "ACK " + re.sub(r"[\n\t\s]*", "", sboard)
                print( strboard )

                return strboard
            elif line.startswith("T:"):
                gid = line.split(":")[1]
                game = get_game(gid)
                ret = "ACK " +  game.settings_str()
                return ret

            elif line.startswith("S:"):
                gid = line.split(":")[1]
                game = get_game(gid)
                ret = "ACK " +  game.state_line()
                return ret
            elif line.startswith("L:"):
                game_ids = get_two_player_games()
                print( game_ids )
                ret = "ACK "
                for gid in game_ids:
                    ret += gid +":"
                return ret[:-1]
            else:
                return "ERR unknown"
        except Exception as e:
            return f"ERR {e}"


