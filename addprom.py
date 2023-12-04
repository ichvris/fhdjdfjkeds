import redis

r = redis.Redis(decode_responses=True)

# cls - одежда
# frn - мебель
# gm - игровое
# res - ресурсы

promocode = "pr_avaimptop" # Промокод
r.sadd(f"offers:promocodes", promocode) # Добавить промокод в базу данных
r.set(f"offers:promocodes:{promocode}:promocode_title", "Награда") # Название окошечка
r.set(f"offers:promocodes:{promocode}:promocode_message", "Хах, ты опять повёлся на мои уловки!") # Сообщение при активации
r.set(f"offers:promocodes:{promocode}:promocode_item", "res:gold:1")  # Награда за промокод
print("Success")                       
