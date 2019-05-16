import chess.pgn
import os, time, re, hashlib
from neo4j import GraphDatabase

# add options here to either import single file, example game, or directory
if __name__ == "__main__":

    driver = GraphDatabase.driver("bolt://localhost:7687", auth=(os.environ['NEO4J_USER'], os.environ['NEO4J_PASSWORD']))
    print("Enter filename to import games from:")
    filename = input()

    num_games = 0
    start_time = int(time.time())

    with open(filename, encoding="ISO-8859-1") as pgn:

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
                    nodeLabel = player_name.lower().replace(' ', '')
                    nodeLabel = re.sub(r'[^a-zA-Z]', '', nodeLabel)
                    query = "MERGE (%s:Player {name: \"%s\"})" % (nodeLabel, player_name)
                    session.run(query)

                # create game node if it doesn't exist
                event = game.headers["Event"]
                date = game.headers["Date"]
                result = game.headers["Result"]
                nodeLabel = event + date + result
                nodeLabel = re.sub(r'[^a-zA-Z]', '', nodeLabel).lower()

                query = "MERGE (%s:Game {event: \"%s\", date: \"%s\", result: \"%s\"})" % (nodeLabel, event, date, result)
                session.run(query)

                # Here create the relatioship between the players and the game

                board = game.board()
                for move in game.mainline_moves():
                    board.push(move)

                    fen_string = board.fen()
                    # Create position node

                    # add relationship between position node and game

                num_games += 1
                print(white_player + " vs. " + black_player)
                game = chess.pgn.read_game(pgn)

        elapsed = int(time.time()) - start_time
        print(f'{num_games} games added to database in {elapsed}s')
