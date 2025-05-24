# backend/app/core/config.py

# --- Player Configuration ---
PLAYER_INITIAL_HP = 20
PLAYER_INITIAL_MAX_HP = 20
PLAYER_INITIAL_ATTACK = 5
PLAYER_INITIAL_DEFENSE = 2
PLAYER_INITIAL_LEVEL = 1
PLAYER_INITIAL_XP = 0

BASE_XP_TO_LEVEL = 100
XP_SCALAR_PER_LEVEL = 50
HP_GAIN_PER_LEVEL = 10
ATK_GAIN_PER_LEVEL = 1
DEF_GAIN_PER_LEVEL = 1

PLAYER_VIEW_RADIUS = 5

# --- Monster Configuration ---
MONSTER_DATA = {
    "goblin": {
        "hp": 10, "attack": 3, "defense": 1,
        "detection_radius": 6, "move_chance": 0.8, "xp_value": 10, # move_chance used for idle state
        "ai_type": "chaser", 
    },
    "orc": {
        "hp": 18, "attack": 6, "defense": 3,
        "detection_radius": 7, "move_chance": 0.6, "xp_value": 25,
        "ai_type": "chaser",
    },
    "skeleton": {
        "hp": 12, "attack": 4, "defense": 1, 
        "detection_radius": 8, "move_chance": 0.5, "xp_value": 15,
        "ai_type": "ranged_attacker", "attack_range": 5,
    }
}

# --- Item Configuration ---
ITEM_EFFECT_VALUES = {
    "potion_heal_amount": 15,
}
ITEM_BONUSES = {
    "dagger_attack_bonus": 2,
    "leather_armor_defense_bonus": 1,
}

# --- Dungeon Generation Configuration ---
DEFAULT_MAP_WIDTH = 50
DEFAULT_MAP_HEIGHT = 30
DEFAULT_MAX_ROOMS = 10 
DEFAULT_ROOM_MIN_SIZE = 5
DEFAULT_ROOM_MAX_SIZE = 10

DG_ROOM_BUDDING_ATTEMPTS = 20 
DG_ROOM_REQUIRED_EMPTY_RATIO = 0.7 
DG_MAX_DOORS_FOR_BUDDING_CANDIDATE = 2 

DG_ITEMS_MIN_ABS_COUNT = 1
DG_ITEMS_ROOM_DIVISOR_FOR_MIN = 2 
DG_ITEMS_ROOM_DIVISOR_FOR_MAX = 2 
DG_ITEMS_MAX_ADDEND = 3          

DG_MONSTERS_MIN_ABS_COUNT = 1
DG_MONSTERS_ROOM_DIVISOR_FOR_MIN = 2 
DG_MONSTERS_MIN_ADDEND = 1           
DG_MONSTERS_ROOM_DIVISOR_FOR_MAX = 1 
DG_MONSTERS_MAX_ADDEND = 2           

DG_MONSTER_TYPE_DISTRIBUTION = {
    "goblin": 0.40,
    "orc": 0.35,
    "skeleton": 0.25, 
}

# --- AI Configuration ---
MONSTER_LKP_TIMEOUT_TURNS = 5 
AI_RANDOM_MOVE_CHANCE_NO_PATH = 0.75 
AI_DEFAULT_IDLE_MOVE_CHANCE = 0.5 # Default if monster template doesn't specify "move_chance"