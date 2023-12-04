from modules.base_module import Module
import binascii
import struct
import protocol
import asyncio
import random

class_name = "NewYear2021"

class NewYear2021(Module):
	prefix = "ny21"

	def __init__(self, server):
		self.server = server
		self.commands = {"ts": self.throw, "cf": self.fireball, "ci": self.iceball}
		self.info_data = None
		self.initInfoData()

	async def send_info(self, client):
		if client.drop:
			return
		try:
			client.writer.write(self.info_data)
			await client.writer.drain()
		except (BrokenPipeError, ConnectionResetError, AssertionError,
				TimeoutError, OSError, AttributeError):
			client.writer.close()
			
	def initInfoData(self):
		self.info_data = struct.pack(">b", 34)
		self.info_data += protocol.encodeArray(["ny21.ui", {"if": {"stcp": True, "mtct": 999999, "lmpt": 1606654102, "sbct": 999999, "sfcnt": 999999, "lps": 999999, "ishc": 999999, "spct": 999999,
				"sftlct": 999999, "sfhmct": 999999, "sfvnct": 999999, "shldct": 999999, "cstlv": 999999, "cstct": 999999, "brnchct": 999999, "lbftm": 1606654102}}])
		self.info_data = self._make_header(self.info_data) + self.info_data
		
	def _make_header(self, msg):
		header_length = 1
		mask = 0
		mask |= (1 << 3)
		header_length += 4
		buf = struct.pack(">i", len(msg)+header_length)
		buf += struct.pack(">B", mask)
		buf += struct.pack(">I", binascii.crc32(msg))
		return buf
		
	async def iceball(self, msg, client):
		online = self.server.online
		loop = asyncio.get_event_loop()
		room = self.server.rooms[client.room].copy()
		anim = random.choice(["Protect", "Freezing"])
		for uid in room:
			try:
				tmp = online[uid]
			except KeyError:
				continue
			loop.create_task(tmp.send(["o.r.ny21.ci", {"ui": client.uid, "to": msg[2]["to"], "ai": anim}]))  
		
	async def fireball(self, msg, client):
		online = self.server.online
		loop = asyncio.get_event_loop()
		room = self.server.rooms[client.room].copy()
		for uid in room:
			try:
				tmp = online[uid]
			except KeyError:
				continue
			loop.create_task(tmp.send(["o.r.ny21.cf", {"ui": client.uid, "to": msg[2]["to"]}]))  
		
	async def throw(self, msg, client):
		online = self.server.online
		loop = asyncio.get_event_loop()
		room = self.server.rooms[client.room].copy()
		for uid in room:
			try:
				tmp = online[uid]
			except KeyError:
				continue
			loop.create_task(tmp.send(["ny21.ts", {"ui": client.uid, "ti": msg[2]["ti"]}]))  