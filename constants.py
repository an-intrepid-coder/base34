from os import path
from pygame.locals import *

VERSION = "0.0.1"

COLOR_MOVEMENT_RANGE = (0, 240, 20, 90)
COLOR_FOG = (70, 70, 70, 130)

FPS = 60

GAME_UPDATE_TICK_MS = 100 
MOVER_TICK_MS = 240

TU_MOVEMENT = 4

INVALID_DJIKSTRA_SCORE = 99999 

FONT_PATH = path.abspath(path.join(path.dirname(__file__), "./sansation/Sansation-Regular.ttf"))
BOLD_FONT_PATH = path.abspath(path.join(path.dirname(__file__), "./sansation/Sansation-Bold.ttf"))
WINDOW_ICON_PATH = path.abspath(path.join(path.dirname(__file__), "./window_icon.png"))
DUDE_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Dude1.png"))
FOG_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Fog.png"))
PILLAR_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Pillar1.png"))
FLOOR_1_PATH = path.abspath(path.join(path.dirname(__file__), "./images/Floor1.png"))

HUD_FONT_SIZE = 20
TITLE_FONT_SIZE = 32 # TODO: title/loading screens

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

ALPHA_KEY = (249, 249, 249)

MAP_SIZE = (100, 100) 
SIDE_HUD_WIDTH = 256 + (CELL_SIZE * 3)
MINI_MAP_SIZE = (SIDE_HUD_WIDTH, SIDE_HUD_WIDTH)
CONSOLE_HEIGHT = 256
MINI_MAP_Y = 0
TURN_Y = MINI_MAP_SIZE[1]
END_TURN_BUTTON_Y = MINI_MAP_SIZE[1] + HUD_FONT_SIZE + 5
TU_REMAINING_Y = END_TURN_BUTTON_Y + HUD_FONT_SIZE + 4

