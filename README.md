# DB Builder

This is the database builder for the OCB (OpenChessBrowser).

## Dependencies

You need neo4j installed and running for this to work. For instructions installing neo4j go [here](https://neo4j.com/download).

To install all required dependencies for the script run:

	$ pip3 install -r requirements.txt

## Running

To fill the database with chess games from a PGN run:

	$ python3 main.py <input_file>
