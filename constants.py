from os import path
from pygame.locals import *
from random import shuffle

VERSION = "0.0.4"

LOADER_SIZE = (1280, 800)

NUM_LONG_ROVERS = 6
NUM_LOCAL_ROVERS = 20
NUM_ALERT_ROVERS = 12

COLOR_MOVEMENT_RANGE = (0, 220, 20, 90)
COLOR_ENEMY_LOS = (170, 0, 20, 90)
COLOR_FOG = (70, 70, 70, 130)
COLOR_HUD_RED = (180, 0, 0)

FPS = 24

GAME_UPDATE_TICK_MS = 100 
MOVER_TICK_MS_VISIBLE = 240
MOVER_TICK_MS_INVISIBLE = 20
PLAYER_TURN_READY_TICK_MS = 60

# values tentative
TU_MOVEMENT = 4
TU_TURN = 1
TU_RADIO_CALL = 8
TU_MELEE = 6
TU_CHEAPEST = TU_MOVEMENT
TU_RELOAD = 5
TU_EQUIP = 7
TU_LETHAL = 3
TU_THROW = 3

FRAG_RADIUS = 3
SMOKE_RADIUS = 6
SENSOR_DISC_RADIUS = 8

INVALID_DJIKSTRA_SCORE = 99999 
ALERT_ZONE_D = 20
AWARENESS_UPDATE_D = 8

FONT_PATH = path.abspath(path.join(path.dirname(__file__), "./sansation/Sansation-Regular.ttf"))
WINDOW_ICON_PATH = path.abspath(path.join(path.dirname(__file__), "./window_icon.png"))
DUDE_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude1.png"))
DUDE_1_KNIFE_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude1_Knife.png"))
DUDE_1_PISTOL_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude1_Pistol.png"))
DUDE_1_LONGARM_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude1_Longarm.png"))
DUDE_2_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude2.png"))
DUDE_2_KNIFE_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude2_Knife.png"))
DUDE_2_PISTOL_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude2_Pistol.png"))
DUDE_2_LONGARM_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude2_Longarm.png"))
DUDE_2_KO_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude2_Ko.png"))
DUDE_2_DEAD_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude2_Dead.png"))
FOG_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Fog.png"))
PILLAR_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Pillar1.png"))
FLOOR_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Floor1.png"))
OUTSIDE_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Outside.png"))
TREE_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Tree1.png"))
TERMINAL_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Terminal.png"))
PATROL_PATH_PATH = path.abspath(path.join(path.dirname(__file__), "./images/PatrolPath.png"))
KNIFE_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Knife.png"))
PISTOL_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Pistol.png"))
LONGARM_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Longarm.png"))
GRENADE_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Grenade.png"))
GOGGLES_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Goggles.png"))
STIM_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Stim.png"))
AMMO_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Ammo.png"))
ARMOR_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Armor.png"))
SMOKE_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Smoke.png"))
LOOT_BASE_PATH = path.abspath(path.join(path.dirname(__file__), "./images/LootBase.png"))

door_colors = ["yellow", "cyan", "magenta", "red", "blue", "green", "orange", "white", "pink", "brown"]
shuffle(door_colors)

HUD_FONT_SIZE = 20
TITLE_FONT_SIZE = 32 
GAME_OVER_FONT_SIZE = 64

CELL_SIZE = 32

DIRECTIONS = {  
    "up": (0, -1), 
    "down": (0, 1), 
    "left": (-1, 0), 
    "right": (1, 0), 
    "wait": (0, 0),
    "upleft": (-1, -1), 
    "upright": (1, -1), 
    "downleft": (-1, 1), 
    "downright": (1, 1),
}

ACTIONS = [
    "melee",
    "interact",
    # more to come
]

ALPHA_KEY = (249, 249, 249)

MAP_SIZE = (200, 200) 
SIDE_HUD_WIDTH = 256 + (CELL_SIZE * 3)
MINI_MAP_SIZE = (SIDE_HUD_WIDTH, SIDE_HUD_WIDTH)
CONSOLE_HEIGHT = 256
MINI_MAP_Y = 0
TURN_Y = MINI_MAP_SIZE[1]
END_TURN_BUTTON_Y = MINI_MAP_SIZE[1] + HUD_FONT_SIZE + 5
TU_REMAINING_Y = END_TURN_BUTTON_Y + HUD_FONT_SIZE + 4
ALERT_Y = TU_REMAINING_Y + HUD_FONT_SIZE + 4
INVENTORY_Y = ALERT_Y + HUD_FONT_SIZE + 4
WEAPON_Y = INVENTORY_Y + HUD_FONT_SIZE + 4
ARMOR_Y = WEAPON_Y + HUD_FONT_SIZE + 4
HEADGEAR_Y = ARMOR_Y + HUD_FONT_SIZE + 4
OVERWATCH_Y = HEADGEAR_Y + HUD_FONT_SIZE + 4
KEYS_Y = OVERWATCH_Y + HUD_FONT_SIZE + 4

