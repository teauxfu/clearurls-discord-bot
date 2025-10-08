import sqlite3
import discord

def ensure_deleted_messages_table(con: sqlite3.Connection) -> None:
    sql = """
    create table if not exists 
    AuditLog_MessagesDeletedForRepost (
        message_id int primary key,
        user_id int,
        created_at timestamp
    );
    """
    cur = con.cursor()
    cur.execute(sql)
    cur.close()

def compact_deleted_messages_table(con: sqlite3.Connection) -> None:
    sql = """
    delete from AuditLog_MessagesDeletedForRepost 
    where date(created_at) <= date('now', '-14 day');
    """
    cur = con.cursor()
    cur.execute(sql)
    cur.close()

def insert_deleted_message(con: sqlite3.Connection, message: discord.Message) -> None:
    sql = """
    insert into AuditLog_MessagesDeletedForRepost (message_id, user_id, created_at)
    select :message_id, :user_id, :created_at
    where not exists (
        select 1 from AuditLog_MessagesDeletedForRepost 
        where message_id = :message_id
    )
    """
    cur = con.cursor()
    cur.execute(sql, {"message_id": message.id, "user_id": message.author.id, "created_at": message.created_at})
    cur.close()

def get_deleted_message_author(con: sqlite3.Connection, message_id: int) -> int | None:
    sql = """
    select user_id from AuditLog_MessagesDeletedForRepost 
    where message_id = :message_id 
    """
    cur = con.cursor()
    cur.execute(sql, {"message_id": message_id})
    res = cur.fetchone()
    if res is None:
        return None
    else:
        return res[0]

def get_reactor_is_original_message_author(con: sqlite3.Connection, message_id: int, user_id: int) -> bool:
    sql = """
    select 1 from AuditLog_MessagesDeletedForRepost 
    where message_id = :message_id and user_id = :user_id 
    """
    cur = con.cursor()
    cur.execute(sql, {"message_id": message_id, "user_id": user_id})
    return cur.fetchone() == (1,)
