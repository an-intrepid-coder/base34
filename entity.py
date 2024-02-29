import pygame
from pygame.locals import *
from pygame.math import Vector2
from pygame.sprite import Sprite, Group
from constants import *
from functional import *
from euclidean import *
from sheets import *
from random import randint, choice

class Clickable(Sprite):
    def __init__(self, img, width, height, effect, xy_tuple=(0, 0)):
        Sprite.__init__(self)
        self.image = img 
        self.effect = effect # NOTE: effect fn should always take an xy_tuple
        self.x, self.y = xy_tuple
        self.width = width
        self.height = height
        self.rect = Rect((self.x, self.y, width, height))

    def clicked(self, xy_tuple) -> bool:
        x, y = xy_tuple
        return self.rect.contains((x, y, 0, 0))

class Actor(Clickable):  
    num_actors = 0
    def __init__(self, sheet, width, height, effect, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)): 
        self.id = Actor.num_actors
        Actor.num_actors += 1
        self.tu, self.max_tu = 0, 0 
        self.sheet = sheet
        self.cell_x, self.cell_y = cell_xy_tuple
        self.orientation = "left"
        self.frame = 0
        self.num_frames = len(self.sheet["regular"][self.orientation])
        img = self.sheet["regular"][self.orientation][0]
        self.x, self.y = xy_tuple
        self.width, self.height = (CELL_SIZE, CELL_SIZE)
        self.rect = Rect(self.x, self.y, self.width, self.height)
        self.fov_radius = 0
        self.tiles_can_see = []
        self.player = False
        self.faction = None
        self.tu, self.max_tu = 0, 0
        self.knocked_out = False
        self.dead = False
        self.name = None
        self.building_number = None
        super().__init__(img, width, height, effect)

    def can_be_knocked_out(self) -> bool:
        return not self.knocked_out and not self.dead

    def max_can_move(self):
        return self.tu // TU_MOVEMENT

    def can_see_tile(self, xy_tuple) -> bool:
        for tile in self.tiles_can_see:
            if tile.xy_tuple == xy_tuple:
                return True
        return False

    def change_orientation(self, orientation):
        if orientation == "wait":
            return
        self.image = self.sheet["regular"][orientation][0]
        self.orientation = orientation

    def random_new_orientation(self):
        new_orientation = choice(list(filter(lambda d: d != self.orientation and d != "wait", DIRECTIONS.keys())))
        self.change_orientation(new_orientation)

    def cell_xy(self) -> tuple:
        return (self.cell_x, self.cell_y)

    def update_frame(self): 
        self.frame = (self.frame + 1) % self.num_frames
        self.image = self.sheet["regular"][self.orientation][self.frame]

    def on_screen(self, topleft_cell, screen_wh_cells_tuple) -> bool:
        x1, y1 = topleft_cell
        w, h = screen_wh_cells_tuple
        return self.cell_x >= x1 and self.cell_y >= y1 and self.cell_x < x1 + w and self.cell_y < y1 + h
    
class Loot(Actor):
    def __init__(self, sheet, width, height, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.looted = False

class Player(Actor):
    def __init__(self, sheet, width, height, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)): 
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.tu, self.max_tu = 28, 28
        self.fov_radius = 8
        self.player = True
        self.faction = "player"
        self.name = "PLAYER"
        self.visible_baddies = []
        self.actions_available = []
        self.building_patrol_intels = []

class Baddie(Actor):
    alert_sentinel = False
    num_local_rovers = 0
    num_long_rovers = 0
    num_alert_rovers = 0
    def __init__(self, sheet, width, height, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)): 
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.tu, self.max_tu = 16, 16
        self.fov_radius = 6
        self.patrol_path = None
        self.finished_turn = True
        self.can_see_player = False
        self.investigating = False
        self.long_rover = False
        self.local_rover = False
        self.alert_rover = False
        self.spotter = False
        self.building_number = None
        self.faction = "baddie"
        self.name = "Baddie"

    def set_long_rover(self):
        self.long_rover = True
        Baddie.num_long_rovers += 1

    def set_local_rover(self):
        self.local_rover = True
        Baddie.num_local_rovers += 1

    def set_alert_rover(self):
        self.alert_rover = True
        Baddie.num_alert_rovers += 1

    def un_rover(self):
        if self.long_rover:
            self.long_rover = False
            Baddie.num_long_rovers -= 1
        elif self.local_rover:
            self.local_rover = False
            Baddie.num_local_rovers -= 1
        elif self.alert_rover and not self.investigating:
            self.alert_rover = False
            Baddie.num_alert_rovers -= 1

    def is_rover(self) -> bool:
        return self.long_rover or self.local_rover or self.alert_rover

    def patrol_path_reached(self) -> bool:
        return self.cell_xy() == self.patrol_path[-1]

    def print_debug_info(self):
        print("local: {}".format(self.local_rover))
        print("long: {}".format(self.long_rover))
        print("alert: {}".format(self.alert_rover))
        print("stationary: {}".format(not self.is_rover()))
        if self.patrol_path is not None:
            print("patrol_path len: {}".format(len(self.patrol_path)))
        else:
            print("No patrol path.")

class Mover:
    def __init__(self, actor, path):
        self.actor = actor
        self.path = path
        self.goal_cell_x, self.goal_cell_y = path[-1]
    
    def goal_cell_xy(self) -> tuple:
        return (self.goal_cell_x, self.goal_cell_y)
       
    def goal_reached(self) -> bool:
        return self.actor.cell_xy() == self.goal_cell_xy()

