from modules.base_module import Module
import time
import asyncio
from lxml import etree

class_name = "SpringDay2019"

class SpringDay2019(Module):
	prefix = "sd19"

	def __init__(self, server):
		self.server = server
		self.commands = {"mph": self.make_photo, "sw": self.set_wishes, "tw": self.take_wish, "cc": self.collect_coins}
		self.clothes_items = self.parse_clothes_items()
		self.wishes = {}
		
	async def collect_coins(self, msg, client):
		await client.send(["sd19.cc", {}])
		
	def parse_clothes_items(self):
		clothes = {}
		for filename in ["boyClothes.xml", "girlClothes.xml"]:
			for item in etree.parse("config_all_ru/inventory/"+filename,parser=etree.XMLParser(remove_comments=True)).getroot().findall(".//item[@id]"):
				itemId = item.attrib["id"]
				clothes[itemId] = itemId
		return clothes
		
	async def take_wish(self, msg, client):
		del self.wishes[client.uid][msg[2]["wshid"]]
		await client.send(["sd19.ui", {"inf": {"wshs": self.wishes[client.uid], "cntlcnt": "999999", "cncrcnt": "999999", "cnfncnt": "999999", "stckrrcvd": True, "evstrtd": True}}])
		await self.give_item(msg, client)
		
	async def give_item(self, msg, client):
		itId = msg[2]["wshtp"]
		if itId in self.server.game_items["game"]:
			type_ = "gm"
		elif itId in self.server.game_items["loot"]:
			type_ = "lt"
		elif itId in self.server.modules["frn"].frn_list:
			type_ = "frn"
		elif itId in self.clothes_items:
			type_ = "cls"
		else:
			return
		await self.server.inv[client.uid].add_item(itId, type_, 1)
		await client.send(["ntf.inv", {"it": {"c": await self.server.inv[client.uid].get_item(itId), "lid": "", "tid": itId}}])  
		
	async def set_wishes(self, msg, client):
		await client.send(["sd19.wa", {"wshid": "colorWheel"}])
		self.wishes[client.uid] = msg[2]["wshs"]
		
	async def make_photo(self, msg, client):
		amount = 5
		if not await self.server.inv[client.uid].take_item("film", amount):
			return
		cnt = await self.server.redis.lindex(f"uid:{client.uid}:items:film", 1)
		if cnt:
			cnt = int(cnt)
		else:
			cnt = 0
		await client.send(["ntf.inv", {"it": {"c": cnt, "lid": "", "tid": "film"}}])
		await client.send(["sd19.mph", {}])