import os
import sqlite3

# since our database needs are small, opting for just a simple 2 column lookup table
# as opposed to a wider general purpose settings table with many columns
# don't really want to have to deal with infrastructure around db migrations 

def get_dbcon() -> sqlite3.Connection:
    return sqlite3.connect(os.environ['DATABASE'])

def ensure_settings_table(con: sqlite3.Connection) -> None:
    sql = """
    create table if not exists 
    RepostCleanedMessages (guild_id int primary key, value bit);
    """
    con.execute(sql)

def ensure_guild_automod_setting(con: sqlite3.Connection, guild_id: int) -> None:
    sql = """
    insert into RepostCleanedMessages (GuildId, Value) values (:id, :value)
    where not exists (select 1 from RepostCleanedMessages where GuildId = :id)
    """
    con.execute(sql, {"id": guild_id, "value": False})

def get_automod_setting(con: sqlite3.Connection, guild_id: int) -> bool:
    sql = """
    select coalesce(value, 0) from RepostCleanedMessages
    where id = ?
    """
    con.execute(sql, guild_id)