from modules.base_module import Module
from lxml import etree
import binascii
import struct
import protocol

class_name = "Descriptor"

class Descriptor(Module):
    prefix = "dscr"

    def __init__(self, server):
        self.server = server
        self.commands = {"init": self.init_descriptors, "load": self.load_descriptors}
        self.outsideLocations = self.parse_outside_locations_descriptor()

    async def load_descriptors(self, msg, client):
        await client.send(['dscr.ldd', {"init": False}])
        
    def parse_outside_locations_descriptor(self):
        root = etree.parse("files/outsideLocations.xml").getroot()
        locations = []
        for location in root.findall(".//location"):
            locationConfig = {}
            locationConfig["id"] = location.attrib["id"]
            locationConfig["zid"] = location.attrib["zoneId"]
            locationConfig["drid"] = location.attrib["defaultRoomId"]
            locationConfig["ldc"] = location.attrib["loadingContent"]
            rooms = []
            for room in location.findall(".//room"):
                roomConfig = {"vip": False, "ml": 0}
                roomConfig["id"] = room.attrib["id"]
                roomConfig["uc"] = room.attrib["map"]
                roomConfig["bgs"] = room.attrib["backgroundSound"]
                roomConfig["dc"] = room.attrib["dresscode"]
                rooms.append(roomConfig)
            locationConfig["rms"] = rooms
            locations.append(locationConfig)
        return locations 

    async def init_descriptors(self, msg, client):
        await client.send(self.message())
            
    def message(self):
        return ['dscr.ldd', {"init": True, "outsideLocations": self.outsideLocations}]