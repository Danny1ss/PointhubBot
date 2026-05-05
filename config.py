import os

# ======================
# BOT CONFIG
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ======================
# ADMIN CONFIG
# ======================
ADMIN_IDS = [
    8637717184
]

# ======================
# SYSTEM SETTINGS
# ======================
START_BONUS = 10
REFERRAL_BONUS = 5

# VIP SETTINGS
VIP_LEVELS = {
    1: {"name": "VIP 1", "bonus": 1.2},
    2: {"name": "VIP 2", "bonus": 1.5},
    3: {"name": "VIP 3", "bonus": 2.0},
}
