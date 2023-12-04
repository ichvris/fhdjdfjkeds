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
# download_url = "http://static-test-avataria.tortugasocial.com/"
with open("update.json", "r") as f:
    config = json.load(f)
with open("files/versions.json", "r") as f:
    versions = json.load(f)


async def main():
    print("Processing config")
    await process_config(versions["data/config_all_ru.zip"])


async def process_config(version):
    directory = "config_all_ru"
    z = zipfile.ZipFile("files/data/config_all_ru.zip", mode="w")
    for root, dirs, files in os.walk(directory):
        for file in files:
            z.write(os.path.join(root, file),
                    arcname=os.path.join(root,
                                         file).split("config_all_ru/")[1])
    z.close()
    with open("files/data/config_all_ru.zip", mode="rb") as f:
        hash_ = hashlib.md5(f.read()).hexdigest()
    os.rename("files/data/config_all_ru.zip",
              f"files/data/config_all_ru_{hash_}.zip")
    versions["data/config_all_ru.zip"] = hash_
    with open("files/versions.json", "w") as f:
        f.write(json.dumps(versions))

futures = [main()]
loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.wait(futures))