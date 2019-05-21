import chess.pgn
import os, time, re, hashlib
from neo4j import GraphDatabase

def create_id_from_strings(string_list):
    CHARS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']
    hash = hashlib.sha256()
    for s in string_list:
        hash.update(s.encode())
    hex = hash.hexdigest()
    long_integer = int(hex, 16)
    long_string = str(long_integer)
    result = ""
    for digit in long_string:
        result += CHARS[int(digit)]
    return result

# add options here to either import single file, example game, or directory
if __name__ == "__main__":

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    print("Enter filename to import games from:")
    filename = input()
    print("Enter encoding (leave blank if unsure):")
    encoding = input()
    if len(encoding) < 1:
        encoding="utf-8"

    num_games = 0
    start_time = int(time.time())

    with open(filename, encoding=encoding) as pgn:

        with driver.session() as session:

            game = chess.pgn.read_game(pgn)
            while game is not None:

                # add player nodes if they don't exist
                players = []
                white_player = game.headers["White"]
                black_player = game.headers["Black"]
                players.append(white_player)
                players.append(black_player)

                for player_name in players:
                    query = "MERGE (%s:Player {name: \"%s\"})" % (create_id_from_strings([player_name]), player_name)
                    result = session.run(query)

                # create game node if they don't exist
                event = game.headers["Event"]
                date = game.headers["Date"]
                result = game.headers["Result"]
                game_id = create_id_from_strings([event, date, result, black_player, white_player])

                query = "MERGE (%s:Game {event: \"%s\", date: \"%s\", result: \"%s\", game_id: \"%s\"})" % (game_id, event, date, result, game_id)
                session.run(query)

                # Here create the relationship between the players and the game
                query = "MATCH (a:Player), (b:Game) WHERE a.name = \"%s\" AND b.game_id = \"%s\" CREATE (a)-[:PLAYED_WHITE_IN]->(b)" % (white_player, game_id)
                session.run(query)
                query = "MATCH (a:Player), (b:Game) WHERE a.name = \"%s\" AND b.game_id = \"%s\" CREATE (a)-[:PLAYED_BLACK_IN]->(b)" % (black_player, game_id)
                session.run(query)

                board = game.board()
                for move in game.mainline_moves():
                    board.push(move)

                    fen_string = board.fen()
                    # Create position node
                    query = "MERGE (a:Position {FEN: \"%s\"})" % (fen_string)
                    session.run(query)

                    # add relationship between position node and game
                    query = "MATCH (a:Position), (b:Game) WHERE a.FEN = \"%s\" AND b.game_id = \"%s\" CREATE (b)-[:HAD_POSITION]->(a)" % (fen_string, game_id)
                    session.run(query)

                num_games += 1
                print(white_player + " vs. " + black_player)
                game = chess.pgn.read_game(pgn)

        elapsed = int(time.time()) - start_time
        print(f'{num_games} games added to database in {elapsed}s')
