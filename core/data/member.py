from __future__ import annotations
import discord
from contextlib import closing
from core import DataObjectFactory, DataObject, ServiceRegistry
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services import DCSServerBot


@dataclass
@DataObjectFactory.register("Member")
class Member(DataObject):
    member: discord.Member
    ucids: dict[str] = field(default_factory=dict, init=False)

    def __post_init__(self):
        super().__post_init__()
        self.bot: DCSServerBot = ServiceRegistry.get("Bot")
        with self.pool.connection() as conn:
            for row in conn.execute('SELECT ucid, manual FROM players WHERE discord_id = %s',
                                    (self.member.id, )).fetchall():
                self.ucids[row[0]] = row[1]

    @property
    def verified(self):
        for verified in self.ucids.values():
            if not verified:
                return False
        return True

    @verified.setter
    def verified(self, flag: bool):
        with self.pool.connection() as conn:
            with conn.transaction():
                with closing(conn.cursor()) as cursor:
                    ucids = list(self.ucids.keys())
                    for ucid in ucids:
                        cursor.execute('UPDATE players SET manual = %s WHERE ucid = %s', (flag, ucid))
                        self.ucids[ucid] = flag

    def link(self, ucid: str, validated: bool = True):
        self.ucids[ucid] = validated
        with self.pool.connection() as conn:
            with conn.transaction():
                conn.execute('UPDATE players SET discord_id = %s, manual = %s WHERE ucid = %s',
                             (self.member.id, validated, ucid))

    def unlink(self, ucid):
        if ucid not in self.ucids:
            return
        del self.ucids[ucid]
        with self.pool.connection() as conn:
            with conn.transaction():
                conn.execute('UPDATE players SET discord_id = -1, manual = FALSE WHERE ucid = %s', (ucid, ))

    @property
    def banned(self) -> bool:
        for server in self.bot.servers.values():
            for ucid in self.ucids:
                if server.is_banned(ucid):
                    return True
        return False
