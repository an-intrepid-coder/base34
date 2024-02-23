import pygame
from pygame.locals import *
from pygame.math import Vector2
from pygame.sprite import Sprite, Group
from constants import *
from functional import *
from euclidean import *
from sheets import *
from random import randint

class Clickable(Sprite):
    def __init__(self, img, width, height, effect, xy_tuple=(0, 0)):
        Sprite.__init__(self)
        self.image = img 
        self.effect = effect # should always take an xy_tuple
        self.x, self.y = xy_tuple
        self.width = width
        self.height = height
        self.rect = Rect((self.x, self.y, width, height))

    def clicked(self, xy_tuple) -> bool:
        x, y = xy_tuple
        return self.rect.contains((x, y, 0, 0))

class Actor(Clickable): 
    def __init__(self, sheet, width, height, effect, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)): 
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
        self.fov_radius = 8
        self.tiles_can_see = []
        self.player = False
        super().__init__(img, width, height, effect)

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

    def cell_xy(self) -> tuple:
        return (self.cell_x, self.cell_y)

    def update_frame(self): 
        self.frame = (self.frame + 1) % self.num_frames
        self.image = self.sheet["regular"][self.orientation][self.frame]

    def on_screen(self, topleft_cell, screen_wh_cells_tuple) -> bool:
        x1, y1 = topleft_cell
        w, h = screen_wh_cells_tuple
        return self.cell_x >= x1 and self.cell_y >= y1 and self.cell_x < x1 + w and self.cell_y < y1 + h
    
    def update(self):
        pass ### TODO

class Mover:
    def __init__(self, actor, path):
        self.actor = actor
        self.path = path
        self.goal = path[-1]

