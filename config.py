import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [8637717184]

START_BONUS = 10
REFERRAL_BONUS = 5
DAILY_BONUS = 3

VIP_LEVELS = {
    0: {"name": "Free", "bonus": 1},
    1: {"name": "VIP 1", "bonus": 1.2},
    2: {"name": "VIP 2", "bonus": 1.5},
    3: {"name": "VIP 3", "bonus": 2},
}
