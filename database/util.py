import os
import sqlite3
from typing import Sequence
from discord import Guild

from auditlog import compact_deleted_messages_table, ensure_deleted_messages_table
from guildsettings import ensure_guild_automod_setting, ensure_settings_table

def get_dbcon() -> sqlite3.Connection:
    # the extra params enable use of timestamp columns and datetime datatypes
    return sqlite3.connect(os.environ['DATABASE'],
                             detect_types=sqlite3.PARSE_DECLTYPES |
                             sqlite3.PARSE_COLNAMES)

def initialize_db(con: sqlite3.Connection, guilds: Sequence[Guild]) -> None:
        ensure_settings_table(con)
        ensure_deleted_messages_table(con)
        compact_deleted_messages_table(con)
        for guild in guilds:
            ensure_guild_automod_setting(con, guild.id)
