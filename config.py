from os import getenv

from dotenv import load_dotenv

load_dotenv()

API_ID = "6435225"
# -------------------------------------------------------------
API_HASH = "4e984ea35f854762dcde906dce426c2d"
# --------------------------------------------------------------
BOT_TOKEN = getenv("BOT_TOKEN", None)
STRING1 = getenv("STRING_SESSION", None)
MONGO_URL = getenv("MONGO_URL", None)
OWNER_ID = int(getenv("OWNER_ID", "1808943146"))
UPSTREAM_REPO = getenv("UPSTREAM_REPO", "https://github.com/THE-VIP-BOY-OP/VIP-CHATBOT")
SUPPORT_GRP = "TG_FRIENDSS"
UPDATE_CHNL = "VIP_CREATORS"
OWNER_USERNAME = "THE_VIP_BOY"
