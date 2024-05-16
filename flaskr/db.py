import psycopg2
from psycopg2 import extras

from flask import current_app, g
import click

def get_db():
    if 'conn' not in g:
        g.conn = psycopg2.connect(
            host='localhost',
            dbname='neighborchat',
            user='postgres',
            password='tzuyi',
            port=5432
        )

    if 'cur' not in g:
        g.cur = g.conn.cursor(cursor_factory = extras.RealDictCursor)

    return g.cur

def get_conn():
    if 'conn' not in g:
        get_db()

    return g.conn

def fetch_one(sql, params):
    cur = get_db()
    cur.execute(sql, params)
    result = cur.fetchone()

    return result

def fetch_all(sql, params):
    cur = get_db()
    cur.execute(sql, params)
    result = cur.fetchall()
    
    return result

def execute(sql, params):
    cur = get_db()
    cur.execute(sql, params)
    get_conn().commit()

def close_db(e=None):
    cur = g.pop('cur', None)
    conn = g.pop('conn', None)

    if cur is not None:
        cur.close()
    if conn is not None:
        conn.close()

def init_db():
    cur = get_db()

    with current_app.open_resource('sql/schema.sql') as f:
        cur.execute(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')

def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
