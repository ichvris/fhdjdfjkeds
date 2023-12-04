import hashlib
import string
import random


def random_string(string_length=20):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for i in range(string_length))


async def new_account(redis):
    print(3)
    redis.incr("uids", 1)
    uid = redis.get("uids")
    print(4)
    passwd = random_string()
    m = hashlib.sha256()
    print(5)
    m.update(f"{uid}_{passwd}".encode())
    hash_ = m.hexdigest()
    print(6)
    redis.set(f"auth:{hash_}", uid)
    redis.set(f"uid:{uid}:lvt", 0)
    print(7)
    redis.sadd(f"rooms:{uid}", "livingroom")
    redis.rpush(f"rooms:{uid}:livingroom", "#livingRoom", 1)
    print(8)
    for i in range(1, 6):
        redis.sadd(f"rooms:{uid}", f"room{i}")
        redis.rpush(f"rooms:{uid}:room{i}", f"Комната {i}", 2)
    return hash_


async def reset_account(redis, uid):
    pipe = redis.pipeline()
    pipe.set(f"uid:{uid}:slvr", 1000)
    pipe.set(f"uid:{uid}:gld", 6)
    pipe.set(f"uid:{uid}:enrg", 100)
    pipe.delete(f"uid:{uid}:trid")
    pipe.delete(f"uid:{uid}:crt")
    pipe.delete(f"uid:{uid}:hrt")
    pipe.delete(f"uid:{uid}:wearing")
    for item in ["casual", "club", "official", "swimwear",
                 "underdress"]:
        pipe.delete(f"uid:{uid}:{item}")
    pipe.delete(f"uid:{uid}:appearance")
    for item in await redis.smembers(f"uid:{uid}:items"):
        pipe.delete(f"uid:{uid}:items:{item}")
    pipe.delete(f"uid:{uid}:items")
    for room in await redis.smembers(f"rooms:{uid}"):
        for item in await redis.smembers(f"rooms:{uid}:{room}:items"):
            pipe.delete(f"rooms:{uid}:{room}:items:{item}")
        pipe.delete(f"rooms:{uid}:{room}:items")
        pipe.delete(f"rooms:{uid}:{room}")
    pipe.delete(f"rooms:{uid}")
    pipe.sadd(f"uid:{uid}:items", "blackMobileSkin")
    pipe.rpush(f"uid:{uid}:items:blackMobileSkin", "gm", 1)
    pipe.sadd(f"rooms:{uid}", "livingroom")
    pipe.rpush(f"rooms:{uid}:livingroom", "#livingRoom", 1)
    for i in range(1, 6):
        pipe.sadd(f"rooms:{uid}", f"room{i}")
        pipe.rpush(f"rooms:{uid}:room{i}", f"Комната {i}", 2)
    await pipe.execute()
