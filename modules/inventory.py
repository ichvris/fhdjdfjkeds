import json
from modules.base_module import Module
from modules.location import get_city_info
from modules.location import refresh_avatar
import random
import modules.notify as notify
import const

with open("gifts.json", "r") as f:
    gifts = json.load(f)


class_name = "Inventory"


class Inventory(Module):
    prefix = "tr"

    def __init__(self, server):
        self.server = server
        self.commands = {"sale": self.sale_item, "opgft": self.openGift, "offer": self.apply_internal_offer}

    async def sale_item(self, msg, client):
        items = self.server.game_items["game"]
        tpid = msg[2]["tpid"]
        cnt = msg[2]["cnt"]
        if tpid not in items or "saleSilver" not in items[tpid]:
            return
        if not await self.server.inv[client.uid].take_item(tpid, cnt):
            return
        price = items[tpid]["saleSilver"]
        user_data = await self.server.get_user_data(client.uid)
        redis = self.server.redis
        await redis.set(f"uid:{client.uid}:slvr", user_data["slvr"]+price*cnt)
        ci = await get_city_info(client.uid, self.server)
        await client.send(["ntf.ci", {"ci": ci}])
        inv = self.server.inv[client.uid].get()
        await client.send(["ntf.inv", {"inv": inv}])
        await notify.update_resources(client, self.server)

    async def apply_internal_offer(self, msg, client):
        r = self.server.redis
        promocode = msg[2]["ioid"]
        promocodes = await r.smembers(f"offers:promocodes")
        promocode_title = None
        promocode_message = None
        promocode_item = None              
        promocode_used_ids = []
        if promocode in promocodes:
            promocode_title = await r.get(f"offers:promocodes:{promocode}:promocode_title") 
            promocode_message = await r.get(f"offers:promocodes:{promocode}:promocode_message")
            promocode_item = await r.get(f"offers:promocodes:{promocode}:promocode_item")               
            promocode_used_ids = await r.smembers(f"offers:promocodes:{promocode}:promocode_used_ids")        
        else:
            return await client.send(["tr.offer", {"ioar": 0}])
        if client.uid in promocode_used_ids:
            return await client.send(["tr.offer", {"ioar": 3}])
        if promocode_item: 
            gift_type = promocode_item.split(":")[0]        
            gift_type_id = promocode_item.split(":")[1]
            gift_count = promocode_item.split(":")[2]
            self.add_promocode_gift(client, gift_type, gift_type_id, gift_count)
            await r.sadd(f"offers:promocodes:{promocode}:promocode_used_ids", client.uid)
            return client.send(["tr.offer", {"ioar": 1, "offer": {"id": promocode, "tt": promocode_title, "msg": promocode_message,
                                                                  "itm": gift_type_id, "cnt": gift_count, "als": "", "rptid": ""}}])  

    async def add_promocode_gift(self, client, gift_type, gift_type_id, gift_count):    
        r = self.server.redis    
        if gift_type_id == "gold" and gift_type == "res":
            await r.incrby(f"uid:{client.uid}:gld", gift_count)
        elif gift_type_id == "silver" and gift_type == "res":
            await r.incrby(f"uid:{client.uid}:slvr", gift_count)
        elif gift_type_id == "energy" and gift_type == "res":
            await r.incrby(f"uid:{client.uid}:enrg", gift_count)
        elif gift_type == "cls":
            await self.server.inv[client.uid].add_item(gift_type_id, "cls", gift_count) 
        elif gift_type == "frn":
            await self.server.inv[client.uid].add_item(gift_type_id, "frn", gift_count)   
        elif gift_type == "gm":
            await self.server.inv[client.uid].add_item(gift_type_id, "gm", gift_count)    
        user_data = await self.server.get_user_data(client.uid)
        await notify.update_resources(client, self.server)
        inv = self.server.inv[client.uid].get()
        await client.send(["ntf.inv", {"inv": inv}])

    async def openGift(self, msg, client):
        tpid = msg[2]["tpid"]

        if (tpid not in gifts):
            return
        
        if not await self.server.inv[client.uid].take_item(tpid, 1):
            return

        gift = gifts[tpid]

        res = {
            "gld": 0,
            "slvr": 0,
            "enrg": 0
        }

        userApprnc = await self.server.get_appearance(client.uid)

        count = await self.server.inv[client.uid].get_item(tpid)

        await client.send([
            "ntf.inv",
            {
                "it": {
                    "c": count,
                    "iid": "",
                    "tid": tpid
                }
            }
        ])

        if ("silver" in gift):
            res["slvr"] = random.randint(gift["silver"][0], gift["silver"][1])

        if ("gold" in gift):
            res["gld"] = random.randint(gift["gold"][0], gift["gold"][1])

        if ("energy" in gift):
            res["enrg"] = random.randint(gift["energy"][0], gift["energy"][1])

        winItems = []

        for item in gift["items"]:
            giftItems = []

            id = item["id"]
            it = item["it"]

            for loot in it:
                if ("gender" in item):
                    gender = "girl"
                    
                    if (userApprnc["g"] == 2):
                        gender = "boy"

                    if (gender != item["gender"]):
                        continue

                giftItems.append(loot)

            winItem = random.choice(giftItems)

            winItems.append({
                "tid": winItem["name"],
                "iid": "",
                "c": random.randint(winItem["minCount"], winItem["maxCount"]),
                "atr": { "bt": 0 },
                "id": id
            })

        await client.send([
            "tr.opgft",
            {
                "lt": { "id": "lt", "it": winItems },
                "res": res,
                "ctid": "personalGifts"
            }
        ])

        userData = await self.server.get_user_data(client.uid)

        await self.server.redis.set(f"uid:{client.uid}:gld", userData["gld"] + res["gld"])
        await self.server.redis.set(f"uid:{client.uid}:enrg", userData["enrg"] + res["enrg"])
        await self.server.redis.set(f"uid:{client.uid}:slvr", userData["slvr"] + res["slvr"])

        userData = await self.server.get_user_data(client.uid)

        await client.send([
            "ntf.res",
            {
                "res": {
                    "gld": userData["gld"],
                    "slvr": userData["slvr"],
                    "enrg": userData["enrg"]
                }
            }
        ])

        for item in winItems:
            await self.server.inv[client.uid].add_item(item["tid"], item["id"], item["c"])

        await client.send([
            "ntf.inv",
            {
                "inv": self.server.inv[client.uid].inv
            }
        ])
