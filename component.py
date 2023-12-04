import time
from modules.base_module import Module
import utils.bot_common
from modules.location import refresh_avatar
from modules.location import gen_plr

class_name = "Component"

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Component(Module):
    prefix = "cp"

    def __init__(self, server):
        self.server = server
        self.commands = {"cht": self.chat, "m": self.moderation,
                         "ms": self.message}
        self.privileges = self.server.parser.parse_privileges()
        self.mute = {}

    def chat(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "sm":  # send message
            msg.pop(0)
            if client.uid in self.mute:
                time_left = self.mute[client.uid]-time.time()
                if time_left > 0:
                    client.send(["cp.ms.rsm", {"txt": "У вас мут ещё на "
                                                      f"{int(time_left)} "
                                                      "секунд"}])
                    return
                else:
                    del self.mute[client.uid]
            if msg[1]["msg"]["cid"]:
                for uid in msg[1]["msg"]["cid"].split("_"):
                    for tmp in self.server.online.copy():
                        if tmp.uid != uid:
                            continue
                        tmp.send(msg)
                        break
            else:
                if "msg" in msg[1]["msg"] and \
                   msg[1]["msg"]["msg"].startswith("!"):
                    return self.system_command(msg[1]["msg"]["msg"], client)
                for tmp in self.server.online.copy():
                    if tmp.room == msg[1]["rid"]:
                        tmp.send(msg)

    def moderation(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "ar":  # access request
            user_data = self.server.get_user_data(client.uid)
            if user_data["role"] >= self.privileges[msg[2]["pvlg"]]:
                success = True
            else:
                success = False
            client.send(["cp.m.ar", {"pvlg": msg[2]["pvlg"],
                                     "sccss": success}])
        elif subcommand == "bu":
            uid = msg[2]["uid"]
            return self.ban_user(uid, client)

    def ban_user(self, uid, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["AVATAR_BAN"]:
            return
        uid_user_data = self.server.get_user_data(uid)
        if uid_user_data["role"] > 2:
            return
        redis = self.server.redis
        banned = redis.get(f"uid{uid}:banned")
        if banned:
            client.send(["cp.ms.rsm", {"txt": f"У UID {uid} уже есть бан"
                                              f"от администратора {banned}"}])
            return
        redis.set(f"uid:{uid}:banned", client.uid)
        ban_time = int(time.time()*1000)
        redis.set(f"uid:{uid}:ban_time", ban_time)
        for tmp in self.server.online.copy():
            if tmp.uid != uid:
                continue
            tmp.send([10, "User is banned",
                      {"duration": 999999, "banTime": ban_time,
                       "notes": "", "reviewerId": client.uid, "reasonId": 0,
                       "unbanType": "none", "leftTime": 0, "id": None,
                       "reviewState": 1, "userId": uid,
                       "moderatorId": client.uid}], type_=2)
            tmp.connection.shutdown(2)
            break
        client.send(["cp.ms.rsm", {"txt": f"UID {uid} получил бан"}])

    def unban_user(self, uid, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["AVATAR_BAN"]:
            return
        redis = self.server.redis
        banned = redis.get(f"uid:{uid}:banned")
        if not banned:
            client.send(["cp.ms.rsm", {"txt": f"У UID {uid} нет бана"}])
            return
        redis.delete(f"uid:{uid}:banned")
        redis.delete(f"uid:{uid}:ban_time")
        client.send(["cp.ms.rsm", {"txt": f"Снят бан UID {uid} от "
                                          f"администратора {banned}"}])

    def message(self, msg, client):
        subcommand = msg[1].split(".")[2]
        if subcommand == "smm":  # send moderator message
            user_data = self.server.get_user_data(client.uid)
            if user_data["role"] < self.privileges["MESSAGE_TO_USER"]:
                return
            uid = msg[2]["rcpnts"]
            message = msg[2]["txt"]
            sccss = False
            for tmp in self.server.online.copy():
                if tmp.uid == uid:
                    tmp.send(["cp.ms.rmm", {"sndr": client.uid,
                                           "txt": message}])
                    sccss = True
                    break
            client.send(["cp.ms.smm", {"sccss": sccss}])

    def system_command(self, msg, client):
        command = msg[1:]
        if " " in command:
            command = command.split(" ")[0]
        if command == "ssm":
            return self.send_system_message(msg, client)
        elif command == "mute":
            return self.mute_player(msg, client)
        elif command == "ban":
            uid = msg.split()[1]
            return self.ban_user(uid, client)
        elif command == "unban":
            uid = msg.split()[1]
            return self.unban_user(uid, client)
        elif command == "reset":
            uid = msg.split()[1]
            return self.reset_user(uid, client)
        elif command == "lvl":
            lvl = msg.split()[1]
            return self.change_level(lvl, client)
        elif command == "ник":
            name = msg.split()[1]
            return self.change_name(name, client)  
        elif command == "имидж":
            crt = msg.split()[1]
            return self.change_crt(crt, client)
        elif command == "блят":
            mut = msg.split()[1]
            return self.mute_yes(mut, client)
        elif command == "золото":
            gld = msg.split()[1]
            return self.change_gld(gld, client) 
        elif command == "серебро":
            slvr = msg.split()[1]
            return self.change_slvr(slvr, client)

    def change_level(self, lvl, client):
        level = int(lvl) - 1
        expSum = 0
        k = 0
        while int(level) > int(k):
            k += 1
            expSum += k * 50      
        exp = expSum
        self.server.redis.set(f"uid:{client.uid}:exp", exp)
        client.send(["q.nwlv", {"lv": lvl}]) 
        ci = gen_plr(client.uid, self.server)["ci"]
        client.send(["ntf.ci", {"ci": ci}])   
        refresh_avatar(client, self.server)

    def change_slvr(self, slvr, client):
        user_data = self.server.get_user_data(client.uid)
        self.server.redis.set(f"uid:{client.uid}:slvr", int(slvr))
        res = {"gld": user_data["gld"],
               "slvr": int(slvr),
               "enrg": user_data["enrg"], "emd": user_data["emd"]}
        client.send(["ntf.res", {"res": res}]) 

    def change_gld(self, gld, client):
        user_data = self.server.get_user_data(client.uid)
        self.server.redis.set(f"uid:{client.uid}:gld", int(gld))
        res = {"gld": int(gld),
               "slvr": user_data["slvr"],
               "enrg": user_data["enrg"], "emd": user_data["emd"]}
        client.send(["ntf.res", {"res": res}])        

    def change_crt(self, crt, client):
        self.server.redis.set(f"uid:{client.uid}:crt", int(crt))
        ci = gen_plr(client.uid, self.server)["ci"]
        client.send(["ntf.ci", {"ci": ci}])   
        refresh_avatar(client, self.server)

    def mute_yes(self, msg, client):
            user_data = self.server.get_user_data(client.uid)
            self.mute[uid] = time.time()+1*60
            client.send(["cp.ms.rsm", {"txt": "Игрок не найден"}])
            tmp.send(["cp.m.bccu", {"bcu": {"notes": "", "reviewerId": "0",
                                            "mid": "0", "id": None,
                                            "reviewState": 1, "userId": user_data,
                                            "mbt": int(time.time()*1000),
                                            "mbd": 60,
                                            "categoryId": 14}}])
        refresh_avatar(client, self.server)

    def change_name(self, name, client):
        new_name = str(name)
        user_data = self.server.get_user_data(client.uid)
        self.server.redis.lset(f"uid:{client.uid}:appearance", 0, new_name)    
        client.send(["a.apprnc.rnn", {"res": {"slvr": user_data["slvr"],
                                                  "enrg": user_data["enrg"],
                                                  "emd": user_data["emd"],
                                                  "gld": user_data["gld"]},
                                          "unm": new_name}])

    def send_system_message(self, msg, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["SEND_SYSTEM_MESSAGE"]:
            return self.no_permission(client)
        message = msg.split("!ssm ")[1]
        for tmp in self.server.online.copy():
            tmp.send(["cp.ms.rsm", {"txt": message}])

    def mute_player(self, msg, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < self.privileges["CHAT_BAN"]:
            return self.no_permission(client)
        uid = msg.split()[1]
        minutes = int(msg.split()[2])
        apprnc = self.server.get_appearance(uid)
        if not apprnc:
            client.send(["cp.ms.rsm", {"txt": "Игрок не найден"}])
            return
        self.mute[uid] = time.time()+minutes*60
        for tmp in self.server.online.copy():
            if tmp.uid != uid:
                continue
            tmp.send(["cp.m.bccu", {"bcu": {"notes": "", "reviewerId": "0",
                                            "mid": "0", "id": None,
                                            "reviewState": 1, "userId": uid,
                                            "mbt": int(time.time()*1000),
                                            "mbd": minutes,
                                            "categoryId": 14}}])
            break
        client.send(["cp.ms.rsm", {"txt": f"Игроку {apprnc['n']} выдан мут "
                                          f"на {minutes} минут"}])

    def reset_user(self, uid, client):
        user_data = self.server.get_user_data(client.uid)
        if user_data["role"] < 5:
            return self.no_permission(client)
        apprnc = self.server.get_appearance(uid)
        if not apprnc:
            client.send(["cp.ms.rsm", {"txt": "Аккаунт и так сброшен"}])
            return
        for tmp in self.server.online.copy():
            if tmp.uid != uid:
                continue
            tmp.connection.shutdown(2)
            break
        utils.bot_common.reset_account(self.server.redis, uid)
        client.send(["cp.ms.rsm", {"txt": f"Аккаунт {uid} был сброшен"}])

    def no_permission(self, client):
        client.send(["cp.ms.rsm", {"txt": "У вас недостаточно прав, чтобы "
                                          "выполнить эту команду"}])
