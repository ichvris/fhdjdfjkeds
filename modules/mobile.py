from modules.base_module import Module

class_name = "Mobile"

MESSAGE_AD_PRICE = int(3)

class Mobile(Module):
    prefix = "mb"

    def __init__(self, server):
        self.server = server
        self.commands = {"mkslf": self.make_selfie,
                         "smad": self.send_mobile_ad,
                         "sma": self.save_mobile_appearance}

    async def make_selfie(self, msg, client):
        amount = 1
        if msg[2]["stg"]:
            amount += 1
        if not await self.server.inv[client.uid].take_item("film", amount):
            return
        cnt = await self.server.redis.lindex(f"uid:{client.uid}:items:film", 1)
        if cnt:
            cnt = int(cnt)
        else:
            cnt = 0
        await client.send(["ntf.inv", {"it": {"c": cnt, "lid": "",
                                              "tid": "film"}}])
        await client.send(["mb.mkslf", {"sow": client.uid,
                                        "stg": msg[2]["stg"],
                                        "zm": msg[2]["zm"]}])
        if msg[2]["stg"]:
            if msg[2]["stg"] in self.server.online:
                tmp = self.server.online[msg[2]["stg"]]
                await tmp.send(["mb.mkslf", {"sow": client.uid, "stg": tmp.uid,
                                             "zm": msg[2]["zm"]}])

    async def send_mobile_ad(self, msg, client):
        user_data = await self.server.get_user_data(client.uid)
        if user_data["gld"] < MESSAGE_AD_PRICE:
            await client.send(["err", {"code": 101, "message": "", "params": {}}])
            return
        await self.server.redis.decrby(f"uid:{client.uid}:gld", MESSAGE_AD_PRICE)
        await client.send(["ntf.res", {"res": {"gld": user_data["gld"] - MESSAGE_AD_PRICE,
                                         "slvr": user_data["slvr"],
                                         "enrg": user_data["enrg"],
                                         "emd": user_data["emd"]}}])
        await client.send(["mb.smad", {"uid": client.uid, "mad": msg[2]["mad"]}])

    async def save_mobile_appearance(self, msg, client):
        skin = msg[2]["mb"]["sk"]
        accessory = msg[2]["mb"]["ac"]
        ringtone = msg[2]["mb"]["rt"]
        if skin not in self.server.game_items["game"]:
            return
        if accessory not in self.server.game_items["game"]:
            await self.server.redis.delete(f"uid:{client.uid}:mobile_ac")
        else:
            if not await self.server.inv[client.uid].get_item(accessory):
                shop = self.server.modules["sh"]
                if not await shop.buy(client, accessory):
                    return
            await self.server.redis.set(f"uid:{client.uid}:mobile_ac",
                                        accessory)
        if ringtone not in self.server.game_items["game"]:
            await self.server.redis.delete(f"uid:{client.uid}:mobile_rt")
        else:
            if not await self.server.inv[client.uid].get_item(ringtone):
                shop = self.server.modules["sh"]
                if not await shop.buy(client, ringtone):
                    return
            await self.server.redis.set(f"uid:{client.uid}:mobile_rt",
                                        ringtone)
        if not await self.server.inv[client.uid].get_item(skin):
            shop = self.server.modules["sh"]
            if not await shop.buy(client, skin):
                return
        await self.server.redis.set(f"uid:{client.uid}:mobile_skin", skin)
        await client.send(["ntf.mbm", {"mb": {"ac": accessory, "rt": ringtone,
                                              "sk": skin, "nmc": 0}}])
        await client.send(["mb.sma", {}])
