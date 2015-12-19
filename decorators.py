import sqlite3
import constants
from contextlib import contextmanager

@contextmanager
def new_cursor():
    con = sqlite3.connect(constants.DATABASE_FILE)
    con.row_factory = sqlite3.Row
    c = con.cursor()
    try:
        yield c
        con.commit()
        c.close()
    except:
        raise
    finally:
        con.close()