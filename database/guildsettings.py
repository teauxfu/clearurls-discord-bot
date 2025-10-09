
import sqlite3

def ensure_settings_table(con: sqlite3.Connection) -> None:
    sql = """
    create table if not exists 
    GuildSettings_DeleteAndRepostDirtyMessages (guild_id int primary key, is_enabled bit);
    """
    cur = con.cursor()
    cur.execute(sql)
    cur.close()

def ensure_guild_automod_setting(con: sqlite3.Connection, guild_id: int) -> None:
    sql = """
    insert into GuildSettings_DeleteAndRepostDirtyMessages (guild_id, is_enabled) 
    select :id, :is_enabled
    where not exists (
        select 1 from GuildSettings_DeleteAndRepostDirtyMessages
        where guild_id = :id
    )
    """
    cur = con.cursor()
    cur.execute(sql, {"id": guild_id, "is_enabled": False})
    cur.close()

def get_automod_setting(con: sqlite3.Connection, guild_id: int) -> bool:
    sql = """
    select coalesce(is_enabled, 0) from GuildSettings_DeleteAndRepostDirtyMessages
    where guild_id = :id
    """
    cur = con.cursor()
    res = cur.execute(sql, {"id": guild_id})
    return res.fetchone() == (1,)

def set_automod_setting(con: sqlite3.Connection, guild_id: int, enabled: bool):
    sql = """
    update GuildSettings_DeleteAndRepostDirtyMessages 
    set is_enabled = :enabled
    where guild_id = :id
    """
    cur = con.cursor()
    cur.execute(sql, {"enabled": enabled, "id": guild_id})
    cur.close()

