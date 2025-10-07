from dataclasses import dataclass

@dataclass
class GuildSettings: 
    guild_id: int
    repost_cleaned_messages: bool 
    