import os
import sqlite3

from database.guildsettings import ensure_settings_table

def get_dbcon() -> sqlite3.Connection:
    # the extra params enable use of timestamp columns and datetime datatypes
    return sqlite3.connect(os.environ['DATABASE'],
                             detect_types=sqlite3.PARSE_DECLTYPES |
                             sqlite3.PARSE_COLNAMES)

def initialize_db(con: sqlite3.Connection) -> None:
        ensure_settings_table(con)
