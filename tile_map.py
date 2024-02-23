import pygame
from sheets import *
from functional import *
from euclidean import *
from constants import *
from random import choice, randint, randrange, shuffle
import heapq

tile_types = ["floor", "wall"] 

def relative_direction(from_xy, to_xy, opposite=False):
    diff = (to_xy[0] - from_xy[0], to_xy[1] - from_xy[1])
    if opposite:
        diff = tuple(map(lambda x: x * -1, diff))
    for k, v in DIRECTIONS.items():
        if v == diff:
            return k
    return "wait"

class Tile:
    def __init__(self, tilemap, xy_tuple, tile_type):
        self.tilemap = tilemap
        self.xy_tuple = xy_tuple
        self.tile_type = tile_type
        self.occupied = False 
        self.seen = False
        self.visible_img = None
        self.foggy_img = None
        self.unseen_img = None

    def walkable(self) -> bool:
        return self.tile_type == "floor"

    def blocks_vision(self) -> bool:
        return self.tile_type == "wall"

    def is_edge(self) -> bool:
        x, y = self.xy_tuple
        w, h = self.tilemap.wh_tuple
        return x == w - 1 or y == h - 1 or x == 0 or y == 0

    def in_bounds(self) -> bool:
        x, y = self.xy_tuple
        w, h = self.tilemap.wh_tuple
        return x >= 0 and y >= 0 and x < h and y < w

class TileMap:
    def __init__(self, scene, wh_tuple):
        self.wh_tuple = wh_tuple
        self.scene = scene
        self.tiles = []
        self.generate_tilemap_test_arena() 
        self.map_surface = self.generate_map_surface() 
        self.mini_map_surface_master = self.map_surface.copy()
        self.mini_map_surface = pygame.transform.scale(self.mini_map_surface_master, MINI_MAP_SIZE)
        self.camera = (0, 0) 

    def update_mini_map_surface(self):
        self.mini_map_surface = pygame.transform.scale(self.mini_map_surface_master, MINI_MAP_SIZE)
        pygame.draw.rect(self.mini_map_surface, "magenta", (0, 0, MINI_MAP_SIZE[0], MINI_MAP_SIZE[1]), 1)

    def reset_seen(self):
        w, h = self.wh_tuple
        for x in range(w):
            for y in range(h):
                self.tiles[x][y] = False

    def make_all_seen(self):
        w, h = self.wh_tuple
        for x in range(w):
            for y in range(h):
                self.tiles[x][y] = True

    def toggle_seen(self, xy_tuple, status):
        x, y = xy_tuple
        self.tiles[x][y].seen = status

    def bresenham_line(self, from_xy, to_xy) -> list:
        # Algorithm pseudocode courtesy of Wikipedia:
        #   https://en.wikipedia.org/wiki/Bresenham%27s_line_algorithm#All_cases
        line = []
        plot_x, plot_y = from_xy
        x, y = to_xy
        dx, dy = abs(x - plot_x), -1 * abs(y - plot_y)
        if plot_x < x:
            sx = 1
        else:
            sx = -1
        if plot_y < y:
            sy = 1
        else:
            sy = -1
        err = dx + dy
        while plot_x != x or plot_y != y:
            line.append((plot_x, plot_y))
            err2 = err * 2
            if err2 >= dy:
                err += dy
                plot_x += sx
            if err2 <= dx:
                err += dx
                plot_y += sy
        return line

    def scroll(self, dx_dy) -> bool:
        w, h = self.wh_tuple
        x1, y1 = dx_dy
        x2, y2 = self.camera
        x3, y3 = x2 + x1, y2 + y1
        if x3 >= 0 and y3 >= 0 and x3 < w and y3 < h:
            self.camera = (x3, y3)
            return True
        return False

    def generate_map_surface(self):
        def placeholder_tile(tile_type):
            surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
            if tile_type == "wall":
                surf.fill((255, 255, 0))
            elif tile_type == "floor":
                surf.fill((110, 110, 110))
            return surf
        w, h = self.wh_tuple
        surf = pygame.Surface((w * CELL_SIZE, h * CELL_SIZE))
        for x in range(w):
            for y in range(h):
                pos = (x * CELL_SIZE, y * CELL_SIZE)
                tile = self.get_tile((x, y))
                visible_img = placeholder_tile(tile.tile_type)
                foggy_img = visible_img.copy()
                foggy_img.blit(self.scene.game.foggy_cell_surf, (0, 0))
                unseen_img = self.scene.game.unseen_cell_surf
                surf.blit(unseen_img, pos)
                tile.visible_img = visible_img
                tile.foggy_img = foggy_img
                tile.unseen_img = unseen_img
        return surf

    def generate_tilemap_test_arena(self): 
        w, h = self.wh_tuple
        for x in range(w):
            self.tiles.append([])
            for y in range(h):
                if self.coordinate_is_edge((x, y)):
                    tile_type = "wall"
                else:
                    tile_type = "floor"
                self.tiles[x].append(Tile(self, (x, y), tile_type))
        # some random walls/pillars for testing, now
        num_pillars = 400
        pillars_placed = 0
        while pillars_placed < num_pillars:
            x, y = randrange(0, w), randrange(0, h)
            if self.tiles[x][y] == "wall":
                continue
            self.tiles[x][y].tile_type = "wall"
            pillars_placed += 1

    def neighbors_of(self, tile_xy) -> list:
        neighbors = []
        for k, v in DIRECTIONS.items():
            if k == "wait":
                continue
            target_xy = (tile_xy[0] + v[0], tile_xy[1] + v[1])
            if self.coordinate_in_bounds(target_xy):
                tile = self.get_tile(target_xy)
                neighbors.append(tile)
        return neighbors

    def coordinate_in_bounds(self, xy_tuple):
        x, y = xy_tuple
        w, h = self.wh_tuple
        return x >= 0 and y >= 0 and x < w and y < h

    def coordinate_is_edge(self, xy_tuple):
        x, y = xy_tuple
        w, h = self.wh_tuple
        return x == 0 or y == 0 or x == w - 1 or y == h - 1

    def set_all_unoccupied(self): # maybe
        for x in range(self.wh_tuple[0]):
            for y in range(self.wh_tuple[1]):
                self.tiles[x][y].occupied = False

    def get_tile(self, xy_tuple) -> Tile:
        return self.tiles[xy_tuple[0]][xy_tuple[1]]

    def all_tiles(self) -> list:
        return flatten(self.tiles)

    def toggle_occupied(self, xy_tuple, status): # maybe
        if self.coordinate_in_bounds(xy_tuple):
            self.tiles[xy_tuple[0]][xy_tuple[1]].occupied = status

    def valid_tiles_in_range_of(self, xy_tuple, d, manhattan=False, walkable_only=False) -> list: 
        x1, y1 = xy_tuple
        w, h = self.wh_tuple
        locs = []
        for x2 in range(x1 - d, x1 + d + 1):
            for y2 in range(y1 - d, y1 + d + 1):
                if manhattan:
                    valid = self.coordinate_in_bounds((x2, y2)) and manhattan_distance((x2, y2), xy_tuple) <= d
                else:
                    valid = self.coordinate_in_bounds((x2, y2)) and chebyshev_distance((x2, y2), xy_tuple) <= d
                if valid:
                    if walkable_only:
                        if self.tiles[x2][y2].walkable() and (x2, y2) != xy_tuple:
                            locs.append(self.tiles[x2][y2])
                    else:
                        locs.append(self.tiles[x2][y2])
        return locs 

