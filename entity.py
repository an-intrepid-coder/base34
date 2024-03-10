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

class InventorySlot(Clickable):
    def __init__(self, img, width, height, slot_index, effect=None, xy_tuple=(0, 0)):
        super().__init__(img, width, height, effect, xy_tuple)
        self.slot_index = slot_index

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
        self.ko_timer = 0
        self.dead = False
        self.name = None
        self.building_number = None
        self.inventory = []
        self.equipped_weapon = None
        self.equipped_armor = None
        self.equipped_headgear = None
        self.animation_throttle_ticker = 0
        self.animation_throttle_limit = 0
        super().__init__(img, width, height, effect)

    def change_sheet(self, sheet):
        self.sheet = sheet
        self.frame = 0
        self.num_frames = len(self.sheet["regular"][self.orientation])
        img = self.sheet["regular"][self.orientation][0]
        self.image = img 

    def can_be_knocked_out(self) -> bool:
        return not self.knocked_out and not self.dead

    def can_be_killed(self) -> bool:
        return not self.dead

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
                                                                        
    def update(self):
        if self.animation_throttle_ticker == self.animation_throttle_limit: 
            self.update_frame()
            self.animation_throttle_ticker = 0
        else:
            self.animation_throttle_ticker += 1

    def on_screen(self, topleft_cell, screen_wh_cells_tuple) -> bool:
        x1, y1 = topleft_cell
        w, h = screen_wh_cells_tuple
        return self.cell_x >= x1 and self.cell_y >= y1 and self.cell_x < x1 + w and self.cell_y < y1 + h

class Smoke(Actor):
    def __init__(self, sheet, width, height, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)): 
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.dissipates_in = randint(3, 6)
        self.animation_throttle_limit = 6
    
class Loot(Actor):
    def __init__(self, sheet, width, height, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.looted = False
        self.stackable = False
        self.num_stacked = 1
        self.owner = None
        self.equipped = False

    def adjust_stack(self, amt): 
        if self.stackable:
            self.num_stacked += amt

class Keycard(Loot): 
    def __init__(self, sheet, width, height, color, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.color = color

class Ammo(Loot):
    def __init__(self, sheet, width, height, ammo_type, amount, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.stackable = True
        self.num_stacked = amount
        self.ammo_type = ammo_type
        self.name = "{} ammo".format(ammo_type)

class Consumable(Loot):
    def __init__(self, sheet, width, height, name, amount, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.stackable = True
        self.num_stacked = amount
        self.name = name

class Throwable(Loot):
    def __init__(self, sheet, width, height, name, amount, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.stackable = True
        self.num_stacked = amount
        self.name = name

class Armor(Loot):
    def __init__(self, sheet, width, height, name, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.name = name
        self.stackable = True
        self.num_stacked = 1

class Headgear(Loot):
    def __init__(self, sheet, width, height, name, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.name = name

class Weapon(Loot): 
    def __init__(self, sheet, width, height, ammo_type, wep_range, name, \
        ammo=0, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        self.ammo_type = ammo_type
        self.ammo = ammo
        self.wep_range = wep_range 
        self.ammo_capacity = None   
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.name = name
        self.weapon_sheet_type = None

class Terminal(Loot):
    def __init__(self, sheet, width, height, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)):
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)

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
        self.melee_overwatch = False 
        self.lethal_overwatch = False

    def sort_inventory(self):
        equipped = []
        stackables = []
        keys = []
        other = []
        for item in self.inventory:
            if item.equipped:
                equipped.append(item)
            elif isinstance(item, Keycard):
                keys.append(item)
            elif item.stackable and item.num_stacked > 0: 
                similar = first(lambda i: i.name == item.name, stackables)
                if similar is None:
                    stackables.append(item)
                else:
                    similar.num_stacked += item.num_stacked
            elif item.num_stacked > 0:
                other.append(item)
        equipped.extend(other)
        equipped.extend(stackables)
        equipped.extend(keys)
        self.inventory = equipped

class Baddie(Actor):
    alert_sentinel = False
    num_local_rovers = 0
    num_long_rovers = 0
    num_alert_rovers = 0
    def __init__(self, sheet, width, height, effect=None, xy_tuple=(0, 0), cell_xy_tuple=(0, 0)): 
        super().__init__(sheet, width, height, effect, xy_tuple, cell_xy_tuple)
        self.body_discovered = False
        self.tu, self.max_tu = 16, 16
        self.fov_radius = 6
        self.patrol_path = None
        self.finished_turn = True
        self.dropped_keycard = False
        self.can_see_player = False
        self.investigating = False
        self.waking_other_baddie = False
        self.spotter = False
        self.long_rover = False
        self.local_rover = False
        self.alert_rover = False
        self.building_number = None
        self.blurbed_this_turn = False
        self.faction = "baddie"
        self.name = "Baddie"

    def spot_blurb(self) -> str:
        return choice(["'halt!'", "'hey!'", "'stop right there!'", "'don't move!'"])

    def got_em_blurb(self) -> str:
        return choice(["'hah, he wasn't so tough...'", "'that'll teach you!'", "'whew, got 'em...'"])

    def random_blurb(self) -> str:
        blurbs = [
            "*hums to self*",
            "*whistles*",
            "*checks shoe*",
            "*indistinct radio noises*",
        ]
        if self.patrol_path is None:
            blurbs.extend([
                "*twiddles thumbs*",
                "*does a little dance*",
                "*smokes a cigarette*",
            ])
        if self.investigating:
            blurbs.extend([
                "'...around here somewhere...'",
                "*looks around*",
                "'wonder where he went...'",
                "'won't let him get me!'",
                "'gotta find that guy'",
                "'they said he was around here...'",
            ])
        if self.equipped_weapon is not None:
            blurbs.extend([
                "*checks ammo*", 
                "*flips safety on and off*", 
                "*aims at nothing in particular*"
            ])
        return choice(blurbs)

    def set_long_rover(self):
        self.long_rover = True
        Baddie.num_long_rovers += 1

    def set_local_rover(self):
        self.local_rover = True
        Baddie.num_local_rovers += 1

    def set_alert_rover(self):
        self.alert_rover = True
        Baddie.num_alert_rovers += 1

    def responsive(self) -> bool:
        return not self.knocked_out and not self.dead

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

    def ko(self):
        self.knocked_out = True
        self.un_rover()
        self.patrol_path = None
        self.investigating = False
        self.can_see_player = False
        self.tiles_can_see = []
        self.ko_timer = randint(20, 40)

    def kill(self):
        self.dead = True
        self.un_rover()
        self.patrol_path = None
        self.investigating = False
        self.can_see_player = False
        self.tiles_can_see = []

    def is_rover(self) -> bool:
        return self.long_rover or self.local_rover or self.alert_rover

    def patrol_path_reached(self) -> bool:
        return self.cell_xy() == self.patrol_path[-1]

    def print_debug_info(self):
        print("local: {}".format(self.local_rover))
        print("long: {}".format(self.long_rover))
        print("alert: {}".format(self.alert_rover))
        print("stationary: {}".format(not self.is_rover()))
        print("can_see_player: {}".format(self.can_see_player))
        print("investigating: {}".format(self.investigating))
        print("waking_other_baddie: {}".format(self.waking_other_baddie))
        print("spotter: {}".format(self.spotter))
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

