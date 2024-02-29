from os import path
from pygame.locals import *

VERSION = "0.0.2"

LOADER_SIZE = (1280, 800)

NUM_LONG_ROVERS = 3
NUM_LOCAL_ROVERS = 20
NUM_ALERT_ROVERS = 8

COLOR_MOVEMENT_RANGE = (0, 220, 20, 90)
COLOR_ENEMY_LOS = (170, 0, 20, 90)
COLOR_FOG = (70, 70, 70, 130)
COLOR_HUD_RED = (180, 0, 0)

FPS = 60

GAME_UPDATE_TICK_MS = 100 
MOVER_TICK_MS_VISIBLE = 240
MOVER_TICK_MS_INVISIBLE = 10
PLAYER_TURN_READY_TICK_MS = 60

TU_MOVEMENT = 4
TU_TURN = 1
TU_RADIO_CALL = 8
TU_MELEE = 6
TU_CHEAPEST = TU_MOVEMENT

INVALID_DJIKSTRA_SCORE = 99999 
ALERT_ZONE_D = 25

FONT_PATH = path.abspath(path.join(path.dirname(__file__), "./sansation/Sansation-Regular.ttf"))
WINDOW_ICON_PATH = path.abspath(path.join(path.dirname(__file__), "./window_icon.png"))
DUDE_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude1.png"))
DUDE_2_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude2.png"))
FOG_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Fog.png"))
PILLAR_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Pillar1.png"))
FLOOR_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Floor1.png"))
OUTSIDE_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Outside.png"))
TREE_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Tree1.png"))
TERMINAL_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Terminal.png"))
PATROL_PATH_PATH = path.abspath(path.join(path.dirname(__file__), "./images/PatrolPath.png"))

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

