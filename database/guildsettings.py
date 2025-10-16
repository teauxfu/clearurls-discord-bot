
import sqlite3

def ensure_settings_table(con: sqlite3.Connection) -> None:
    sql = """
    create table if not exists 
    guild_settings (guild_id int primary key, replace_messages bit);
    """
    cur = con.cursor()
    cur.execute(sql)
    cur.close()

def get_automod_setting(con: sqlite3.Connection, guild_id: int) -> bool:
    sql = """
    select coalesce(replace_messages, 0) from guild_settings
    where guild_id = :id
    """
    cur = con.cursor()
    res = cur.execute(sql, {"id": guild_id})
    return res.fetchone() == (1,)

def set_automod_setting(con: sqlite3.Connection, guild_id: int, replace_messages: bool) -> None:
    # https://www.sqlite.org/draft/lang_UPSERT.html
    sql_upsert = """
    insert into guild_settings (guild_id, replace_messages) 
    values (:guild_id, :replace_messages)

    on conflict(guild_id)
    do 
        update set replace_messages = :replace_messages
        where guild_id = :guild_id
    """

    cur = con.cursor()
    param = {"replace_messages": replace_messages, "guild_id": guild_id}
    cur.execute(sql_upsert, param)
    cur.close()

