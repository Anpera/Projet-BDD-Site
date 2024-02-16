import psycopg2
import psycopg2.extras

def connect():
	conn = psycopg2.connect(
		dbname = 'postgres',
		user = 'postgres',
		password = '1303',
		cursor_factory = psycopg2.extras.NamedTupleCursor
	)
	conn.autocommit = True
	return conn	