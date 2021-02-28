from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass

from typing import Dict, List, Union, Optional

from src.utils import get_config


class GameUser:
    def __init__(self, con: sqlite3.Connection, userid: str) -> None:
        self.id: str = userid
        self.con = con
        self.cur = con.cursor()

        self.money: int = 0
        self.join_time: float = 0
        self.check_time: float = 0
        self.stock: Dict[str, List[int]] = {}

        self.load()

    @staticmethod
    def exist_user(con: sqlite3.Connection, userid: str) -> bool:
        cur = con.cursor()

        cur.execute("SELECT * FROM users WHERE id=?", (userid,))

        if cur.fetchone():
            return True

        return False

    @staticmethod
    def join(con: sqlite3.Connection, userid: str, gift: int = 10000) -> GameUser:
        cur = con.cursor()
        cur.execute(
            "INSERT INTO users VALUES (?, ?, ?, '0.0', '{}')",
            (userid, str(gift), str(time.time())),
        )
        con.commit()
        return GameUser(con, userid)

    def remove(self) -> None:
        self.cur.execute("DELETE FROM users WHERE id=?", (self.id,))
        self.con.commit()
        self.money = None

    def load(self) -> None:
        self.cur.execute("SELECT * FROM users WHERE id=?", (self.id,))
        data = self.cur.fetchone()

        if data:
            self.money = int(data[1])
            self.join_time = float(data[2])
            self.check_time = float(data[3])
            self.stock = json.loads(data[4])

    def commit(self):
        self.cur.execute(
            "UPDATE users SET money=?, check_time=?, stock=? WHERE id=?",
            (
                str(self.money),
                str(self.check_time),
                json.dumps(self.stock, ensure_ascii=False),
                self.id,
            ),
        )
        self.con.commit()


@dataclass
class Item:
    id: int
    name: str
    description: str
    price: int
    effect: str

    @staticmethod
    def get(query: Union[int, str]) -> Optional[Item]:
        if isinstance(query, int):
            search: List[Item] = list(filter(lambda x: x.id == int(query), Items))
            if len(search) > 0:
                return search[0]
        elif isinstance(query, str):
            search: List[Item] = list(filter(lambda x: x.name == str(query), Items))
            if len(search) > 0:
                return search[0]
        else:
            raise TypeError
        return

    @staticmethod
    def to_flag(items: List[Item]) -> int:
        flag: int = 0
        for item in items:
            flag = flag >> item.id
        return flag

    @staticmethod
    def to_list(flag: int) -> List[Item]:
        items: List[Item] = []
        for item in Items:
            if 1 << item.id & flag:
                items.append(item)
        return items


Items: List[Item] = []

config = get_config()
for i in config["game"]["items"]:
    Items.append(
        Item(
            config["game"]["items"].index(i),
            i.get("name"),
            i.get("description"),
            i.get("price"),
            i.get("effect"),
        )
    )
