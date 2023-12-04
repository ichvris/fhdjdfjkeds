import asyncio
import base64
import configparser
import redis
from aiohttp import web
import aiohttp_session
import aiohttp_jinja2
import jinja2
from cryptography import fernet
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from utils import bot_common
from utils import bot_common_sync
import utils.bot_common
import utils.bot_common_sync
import aiohttp

routes = web.RouteTableDef()
routes.static("/files", "files")
xml = """<?xml version="1.0" ?>
<cross-domain-policy>
    <allow-access-from domain="*" />
</cross-domain-policy>"""
config = configparser.ConfigParser()
config.read("web.ini")
if config["webserver"]["allow_reg"].lower() == "true":
    registation = True
else:
    registation = False


def get_level(exp):
    expSum = 0
    i = 0
    while expSum < exp:
        i += 1
        expSum += i * 50
    return i

@routes.get("/reset")
async def reset(request):
    session = await aiohttp_session.get_session(request)
    if "auth_key" not in session:
        raise web.HTTPFound("/")
    key = session["auth_key"]
    userId = app["redis"].get(f"auth:{key}")
    bot_common_sync.reset_account(app["redis"], userId)
    raise web.HTTPFound("/")

@routes.get("/vkAuth")
async def vkAuth(request):
    if request.query:
        if "code" not in request.query:
            raise web.HTTPUnauthorized()
        authCode = request.query["code"]
        url = "https://oauth.vk.com/access_token?client_id=7739815&display=page&redirect_uri=https://avastar.tk/vkAuth&client_secret=wOZRD4hNOBkuQB0DFY11&code={0}".format(authCode)
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                authRequestInfo = await resp.json()
        if not authRequestInfo:
            raise web.HTTPUnauthorized()
        print(authRequestInfo)
        vkUserId = authRequestInfo["user_id"]
        access_token = authRequestInfo["access_token"]
        token_expire = int(authRequestInfo["expires_in"])
        password = app["redis"].get(f"vk:{vkUserId}")
        if not password:
            uid, password = await bot_common.new_account(app["redis"])
            app["redis"].set(f"vk:{vkUserId}", password)
            app["redis"].set(f"uid:{uid}:sid", vkUserId)
        uid = app["redis"].get(f"auth:{password}")
        app["redis"].setex(f"uid:{uid}:token", token_expire, access_token)
        session = await aiohttp_session.new_session(request)
        session["sid"] = vkUserId
        session["access_token"] = access_token
        session["auth_key"] = password
        raise web.HTTPFound("/")
        
@routes.post("/method/{name}")
async def method(request):
    data = await request.post()
    name = request.match_info["name"]
    if name == "friends.getAppUsers":
        return web.json_response({"response": []})
    elif name == "friends.get":
        return web.json_response({"response": {"count": 0, "items": []}})
    elif name == "users.get":
        if data["user_ids"]:
            sid = int(data["user_ids"])
            return web.json_response({"response": [{"id": sid, "sex": 2,
                                                    "first_name": "Павел",
                                                    "last_name": "Дуров",
                                                    "bdate": "10.10.1984"}]})
        return web.json_response({"response": []})
    return web.json_response({"error": {"error_code": 3,
                                        "error_msg": "Method not found"}})


@routes.post("/wall_upload")
async def wall_upload(request):
    return web.json_response({"server": 1, "photo": [{"photo": "darova",
                                                      "sizes": []}],
                              "hash": "darova"})


@routes.get("/play")
async def play(request):
    session = await aiohttp_session.get_session(request)
    context = {}
    if "access_token" not in session:
        raise web.HTTPFound("/")
        context["logged_in"] = False
    else:
        context["logged_in"] = True
        context["sid"] = session["sid"]
        context["access_token"] = session["access_token"]
        context["auth_key"] = session["auth_key"]
        context["logged_in"] = True
        context["access_token"] = session["access_token"]
        context["update_time"] = config["webserver"]["update_time"]
        context["sid"] = session["sid"]
        social_uid = int(session["sid"])
        passwd = app["redis"].get(f"vk:{social_uid}")
        user_uid = app["redis"].get(f"auth:{passwd}")
        nameav = str(app["redis"].lrange(f"uid:{user_uid}:appearance", 0, 0))
        crt = str(app["redis"].get(f"uid:{user_uid}:crt"))
        hrt = str(app["redis"].get(f"uid:{user_uid}:hrt"))
        gld = str(app["redis"].get(f"uid:{user_uid}:gld"))
        ip = str(app["redis"].get(f"uid:{user_uid}:ip"))
        vip = str(app["redis"].get(f"uid:{user_uid}:premium"))
        slvr = str(app["redis"].get(f"uid:{user_uid}:slvr"))
        frst = "Игрок"
        exp = int(app["redis"].get(f"uid:{user_uid}:exp"))
        role = str(app["redis"].get(f"uid:{user_uid}:role"))
        nameav = nameav.replace('[', '')
        nameav = nameav.replace(']', '')
        nameav = nameav.replace("'", '')
        ip = ip.replace('None', '127.0.0.1')
        vip = vip.replace('None', 'не активен')
        vip = vip.replace('0', 'активен')
        vip = vip.replace('1', 'активен')
        vip = vip.replace('3', 'активен')
        vip = vip.replace('4', 'активен')
        vip = vip.replace("5", 'активен')
        role = role.replace('None', 'Пользователь')
        role = role.replace('1', 'Мл. Модератор')
        role = role.replace('2', 'Ст. Модератор')
        role = role.replace('3', 'Модератор')
        role = role.replace('4', 'Администратор')
        role = role.replace("5", 'Разработчик') 
        context["vkName"] = frst
        context["vip"] = vip
        context["role"] = role
        context["nameav"] = nameav
        context["uid"] = user_uid
        context["gld"] = gld
        context["ip"] = ip
        context["crt"] = crt
        context["hrt"] = hrt
        context["slvr"] = slvr
        context["lvl"] = get_level(exp)
        context["update_time"] = config["webserver"]["update_time"]
    return aiohttp_jinja2.render_template("play.html", request,
                                          context=context)


@routes.get("/")
async def index(request):
    session = await aiohttp_session.get_session(request)
    context = {}
    if "access_token" not in session:
        context["logged_in"] = False
    else:
        context["logged_in"] = True
        context["sid"] = session["sid"]
        context["access_token"] = session["access_token"]
        context["auth_key"] = session["auth_key"]
        context["update_time"] = config["webserver"]["update_time"]
    return aiohttp_jinja2.render_template("index.html", request,
                                          context=context)


@routes.post("/login")
async def login(request):
    session = await aiohttp_session.new_session(request)
    data = await request.post()
    auth_key = data["password"]
    uid = app["redis"].get(f"auth:{auth_key}")
    if uid == data["login"]:
        session["uid"] = uid
        session["auth_key"] = auth_key
    raise web.HTTPFound("/play")


@routes.get("/profile")
async def profile(request):
    session = await aiohttp_session.get_session(request)
    context = {}
    if "access_token" not in session:
        context["logged_in"] = False
        raise web.HTTPFound("/")
    else:
        context["logged_in"] = True
        context["access_token"] = session["access_token"]
        context["update_time"] = config["webserver"]["update_time"]
        context["sid"] = session["sid"]
        social_uid = int(session["sid"])
        passwd = app["redis"].get(f"vk:{social_uid}")
        user_uid = app["redis"].get(f"auth:{passwd}")
        nameav = str(app["redis"].lrange(f"uid:{user_uid}:appearance", 0, 0))
        crt = str(app["redis"].get(f"uid:{user_uid}:crt"))
        hrt = str(app["redis"].get(f"uid:{user_uid}:hrt"))
        gld = str(app["redis"].get(f"uid:{user_uid}:gld"))
        ip = str(app["redis"].get(f"uid:{user_uid}:ip"))
        vip = str(app["redis"].get(f"uid:{user_uid}:premium"))
        slvr = str(app["redis"].get(f"uid:{user_uid}:slvr"))
        frst = "Игрок"
        exp = int(app["redis"].get(f"uid:{user_uid}:exp"))
        role = str(app["redis"].get(f"uid:{user_uid}:role"))
        nameav = nameav.replace('[', '')
        nameav = nameav.replace(']', '')
        nameav = nameav.replace("'", '')
        ip = ip.replace('None', '127.0.0.1')
        vip = vip.replace('None', 'не активен')
        vip = vip.replace('0', 'активен')
        vip = vip.replace('1', 'активен')
        vip = vip.replace('3', 'активен')
        vip = vip.replace('4', 'активен')
        vip = vip.replace("5", 'активен')
        role = role.replace('None', 'Пользователь')
        role = role.replace('1', 'Мл. Модератор')
        role = role.replace('2', 'Ст. Модератор')
        role = role.replace('3', 'Модератор')
        role = role.replace('4', 'Администратор')
        role = role.replace("5", 'Разработчик') 
        context["vkName"] = frst
        context["vip"] = vip
        context["role"] = role
        context["nameav"] = nameav
        context["uid"] = user_uid
        context["gld"] = gld
        context["ip"] = ip
        context["crt"] = crt
        context["hrt"] = hrt
        context["slvr"] = slvr
        context["lvl"] = get_level(exp)
    return aiohttp_jinja2.render_template("profile.html", request,
                                          context=context)


@routes.get("/logout")
async def logout(request):
    session = await aiohttp_session.get_session(request)
    if "access_token" in session:
        del session["sid"]
        del session["access_token"]
        del session["auth_key"]
    raise web.HTTPFound("/")

@routes.get("/prelogin")
async def prelogin(request):
    return web.json_response({"user": {"bannerNetworkId": None, "reg": 0,
                                       "paymentGroup": "",
                                       "preloginModuleIds": "", "id": 99,
                                       "avatariaLevel": 999}})

@routes.post("/auth")
async def auth(request):
    data = await request.json()
    return web.json_response({"jsonrpc": "2.0", "id": 1,
                              "result": data["params"][2]["auth_key"]})

@routes.get("/appconfig.xml")
async def appconfig(request):
    session = await aiohttp_session.get_session(request)
    if "access_token" not in session:
        raise web.HTTPFound("/")
    else:
        context = {"address": config["webserver"]["web_address"]}
    return aiohttp_jinja2.render_template("appconfig.xml", request,
                                          context=context)


@routes.get("/crossdomain.xml")
async def crossdomain(requst):
    return web.Response(text=xml)


async def main():
    global app
    app = web.Application()
    app.add_routes(routes)
    app["redis"] = redis.Redis(decode_responses=True)
    fernet_key = fernet.Fernet.generate_key()
    secret_key = base64.urlsafe_b64decode(fernet_key)
    aiohttp_session.setup(app, EncryptedCookieStorage(secret_key))
    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader("templates"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", int(config["webserver"]["web_port"]))
    await site.start()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    loop.run_forever()
