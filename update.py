import os
import json
import time
import shutil
import asyncio
import zipfile
import hashlib
import configparser
import aiohttp
from lxml import etree

download_url = "http://cdn-sp.tortugasocial.com/avataria-ru/"

with open("update.json", "r") as f:
    config = json.load(f)
with open("files/versions_new1.json", "r") as f:
    versions = json.load(f)
data = versions
while True:
    ...

with open(f"files/versions_new1.json", "w") as f:
    g = {}
    for key in data:
        if "swf/" in key:
            if not os.path.exists(f"files/{key[:-4]+'_'+data[key]+'.swf'}"):
                link = "files/swf"+ '/'.join(key.split("/")[1:-1])
                try:
                    files = os.listdir(link)
                except FileNotFoundError:
                    link = "files/swf/" + key.split("/")[1:-1][0]
                    files = os.listdir(link)
                replaced = ""
                for file in files:
                    if file.split("_")[0] == key.split("/")[-1][:-4]:
                        replaced = file
                        break
                print(key, replaced.split("_"))
                try:
                    g[key] = replaced.split("_")[1][:-4]
                except IndexError:
                    g[key] = ""
            else:
                g[key] = data[key]
        else:
            g[key] = data[key]
                
            
    f.write(str(g))
    
while True:
    ...


async def main():
    print("Got versions.json")
    tasks = []
    loop = asyncio.get_event_loop()
    async with aiohttp.ClientSession() as session:
        for item in data:
            print(item)
            if data[item] in item or "island" in item.lower():
                continue
            if item in config["ignore"] or "_md5" in item or "_sub" in item:
                continue
            tasks.append(loop.create_task(download_file(item, data[item],
                                                        session)))
        await asyncio.wait(tasks)
    print("Processing config")
    if "data/config_all_ru.zip" not in versions:
        print("Error - config_all_ru.zip not found")
    else:
        await process_config(versions["data/config_all_ru.zip"])


async def process_config(version):
    directory = "config_all_ru"
    if os.path.exists(directory):
        shutil.rmtree(directory)
    os.makedirs(directory)
    file = f"files/data/config_all_ru_{version}.zip"
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(directory)
    doc = etree.parse(f"{directory}/avatarAppearance/appearance.xml")
    root = doc.getroot()
    for el in root.findall(".//item[@kind]"):
        if "clanOnly" in el.attrib:
            del el.attrib["clanOnly"]
        if "canBuy" in el.attrib:
            del el.attrib["canBuy"]
        if "module" in el.attrib:
            del el.attrib["module"]
        if "theme" in el.attrib:
            del el.attrib["theme"]
        if "level" in el.attrib:
            del el.attrib["level"]
    string = etree.tostring(root, pretty_print=True,
                            xml_declaration=True).decode()
    with open(f"{directory}/avatarAppearance/appearance.xml", "w") as f:
        f.write(string)
    for filename in ["furniture", "kitchen", "bathroom", "decor",
                     "roomLayout", "clanFurniture"]:
        doc = etree.parse(f"{directory}/inventory/{filename}.xml")
        root = doc.getroot()
        for el in root.xpath("//item[@holiday]"):
            del el.attrib["holiday"]
        for el in root.xpath("//item[@vipOnly]"):
            del el.attrib["vipOnly"]
        for el in root.findall(".//item[@canBuy='0']"):
            del el.attrib["canBuy"]
        for el in root.findall(".//item[@id]"):
            if "sd16" in el.attrib["id"]:
                el.attrib["canBuy"] = "0"
        string = etree.tostring(root, pretty_print=True,
                                xml_declaration=True).decode()
        with open(f"{directory}/inventory/{filename}.xml", "w") as f:
            f.write(string)
        tasks = []
        loop = asyncio.get_event_loop()
        async with aiohttp.ClientSession() as session:
            for el in root.findall(".//item"):
                name = el.attrib["name"]
                folder = filename
                if folder == "roomLayout":
                    if name == "RoomBase":
                        continue
                    folder = "house"
                elif folder == "decor":
                    parent = el.getparent()
                    if parent.attrib["id"] == "achievementsDecor":
                        continue
                if "library" in el.attrib:
                    folder = el.attrib["library"]
                elif "icon" in el.attrib and "@" in el.attrib["icon"]:
                    folder = el.attrib["icon"].split("@")[-1]
                url = f"{download_url}swf/furniture/{folder}/{name}.swf"
                tasks.append(loop.create_task(download_furniture(url,
                                                                 session)))
            await asyncio.wait(tasks)
    doc = etree.parse(f"{directory}/modules/acl.xml")
    root = doc.getroot()
    for el in root.findall(".//privilege[@minAuthority='5']"):
        el.attrib["minAuthority"] = "4"
    string = etree.tostring(root, pretty_print=True,
                            xml_declaration=True).decode()
    with open(f"{directory}/modules/acl.xml", "w") as f:
        f.write(string)
    shutil.copyfile("files/avacity_ru.xml",
                    "config_all_ru/translation/avacity_ru.xml")
    with open("files/data/config_all_ru.zip", mode="rb") as f:
        hash_ = hashlib.md5(f.read()).hexdigest()
    os.rename("files/data/config_all_ru.zip",
              f"files/data/config_all_ru_{hash_}.zip")
    versions["data/config_all_ru.zip"] = hash_
    with open("files/versions.json", "w") as f:
        f.write(json.dumps(versions))


async def download_file(filename, version, session):
    if "music" in filename:
        final = filename
    else:
        final = filename.split(".")[0] + f"_{version}." + filename.split(".")[1]
    if os.path.exists("files/" + final):
        if "music" not in filename:
            versions[filename] = version
        return
    async with session.get(download_url + final) as resp:
        if resp.status != 200:
            return
        content = await resp.read()
    tmp = filename.split("/")
    tmp.pop()
    folder = "/".join(tmp)
    os.makedirs("files/" + folder, exist_ok=True)
    with open("files/" + final, "wb") as f:
        f.write(content)
    if "music" not in filename:
        versions[filename] = version
    print(f"Got {final}")


async def download_furniture(url, session):
    folder = url.split("/")[-2]
    final = f"swf/furniture/{folder}/{url.split('/')[-1]}"
    if os.path.exists("files/" + final):
        return
    async with session.get(url) as resp:
        if resp.status != 200:
            return
        content = await resp.read()
    os.makedirs(f"files/swf/furniture/{folder}", exist_ok=True)
    with open("files/" + final, "wb") as f:
        f.write(content)
    print(f"Got {folder}/{url.split('/')[-1]}")


futures = [main()]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(futures))
