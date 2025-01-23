DISCORD_TOKEN: str
with open("/run/secrets/discord_token", encoding="UTF-8") as secret:
    DISCORD_TOKEN = secret.readline().rstrip("\n")
