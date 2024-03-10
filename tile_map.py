import pygame
from loading_screen import loading_screen
from sheets import *
from functional import *
from euclidean import *
from constants import *
from random import choice, randint, randrange, shuffle
import heapq

tile_types = ["floor", "wall", "outside", "tree"]

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
        self.building_number = None
        self.door = False
        self.door_open = False
        self.door_color = None
        self.outer_wall = False
        self.contiguous = False

    def walkable(self) -> bool:
        return self.tile_type == "floor" or self.tile_type == "outside"

    def blocks_vision(self) -> bool:
        return self.tile_type == "wall" or self.tile_type == "tree" or (self.door and not self.occupied)

    def is_edge(self) -> bool:
        x, y = self.xy_tuple
        w, h = self.tilemap.wh_tuple
        return x == w - 1 or y == h - 1 or x == 0 or y == 0

    def in_bounds(self) -> bool:
        x, y = self.xy_tuple
        w, h = self.tilemap.wh_tuple
        return x >= 0 and y >= 0 and x < h and y < w

    def destructible(self) -> bool:
        return self.tile_type == "wall" or self.tile_type == "tree"

class TileMap:
    def __init__(self, scene, wh_tuple):
        self.wh_tuple = wh_tuple
        self.scene = scene
        self.tiles = []
        self.generate_tilemap_lightly_wooded() 
        loading_screen(self.scene.game.loader, "...generating map surface...")
        self.map_surface = self.generate_map_surface() 
        self.mini_map_surface_master = self.map_surface.copy()
        self.mini_map_surface = pygame.transform.scale(self.mini_map_surface_master, MINI_MAP_SIZE)
        self.camera = (0, 0) 
        loading_screen(self.scene.game.loader, "...map generated! ...")
        self.all_tiles = self.get_all_tiles()

    def destruct_tile(self, xy_tuple):
        tile = self.get_tile(xy_tuple)
        if tile.destructible():
            if tile.tile_type == "wall":
                img = self.scene.game.floor_1_sheet.copy()
                tile.tile_type = "floor"
            elif tile.tile_type == "tree":
                def flippage() -> bool:
                    return randint(0, 1) == 1
                img = pygame.transform.flip(self.scene.game.outside_sheet, flip_x=flippage(), flip_y=flippage())
                tile.tile_type = "outside"
            tile.visible_img = img
            if tile.seen:
                fog_img = img.copy()
                fog_img.blit(self.scene.game.foggy_cell_surf, (0, 0))
                pos = (tile.xy_tuple[0] * CELL_SIZE, tile.xy_tuple[1] * CELL_SIZE) 
                self.map_surface.blit(fog_img, pos)
                self.mini_map_surface_master.blit(img, pos)

    def reset(self):
        self.map_surface.fill("black")
        self.mini_map_surface_master.fill("black")
        self.reset_seen()
        self.set_all_unoccupied()
        self.update_mini_map_surface()

    def update_mini_map_surface(self):
        self.mini_map_surface = pygame.transform.scale(self.mini_map_surface_master, MINI_MAP_SIZE)
        pygame.draw.rect(self.mini_map_surface, "magenta", (0, 0, MINI_MAP_SIZE[0], MINI_MAP_SIZE[1]), 1)

    def reset_seen(self):
        w, h = self.wh_tuple
        for x in range(w):
            for y in range(h):
                self.tiles[x][y].seen = False

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
        line.append((plot_x, plot_y))
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
        def placeholder_tile(tile_type, door_color): 
            if tile_type == "wall":
                img = self.scene.game.pillar_1_sheet
            elif tile_type == "outside":
                def flippage() -> bool:
                    return randint(0, 1) == 1
                img = pygame.transform.flip(self.scene.game.outside_sheet, flip_x=flippage(), flip_y=flippage())
            elif tile_type == "floor":
                img = self.scene.game.floor_1_sheet.copy()
            elif tile_type == "tree":
                img = self.scene.game.tree_1_sheet
            if door_color is not None:
                pygame.draw.rect(img, door_color, (0, 0, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(img, "black", (0, 0, CELL_SIZE, CELL_SIZE), 4)
                vline_start, vline_end = (img.get_width() // 2 - 1, 0), (img.get_width() // 2 - 1, img.get_height() - 1)
                hline_start, hline_end = (0, img.get_height() // 2 - 1), (img.get_width() - 1, img.get_height() // 2 - 1)
                pygame.draw.line(img, "black", vline_start, vline_end, 2)
                pygame.draw.line(img, "black", hline_start, hline_end, 2)
            return img
                
        w, h = self.wh_tuple
        surf = pygame.Surface((w * CELL_SIZE, h * CELL_SIZE))
        for x in range(w):
            for y in range(h):
                pos = (x * CELL_SIZE, y * CELL_SIZE)
                tile = self.get_tile((x, y))
                visible_img = placeholder_tile(tile.tile_type, tile.door_color)
                tile.visible_img = visible_img
        return surf

    def generate_tilemap_lightly_wooded(self): 
        loading_screen(self.scene.game.loader, "...beginning map generation...")
        w, h = self.wh_tuple
        for x in range(w):
            self.tiles.append([])
            for y in range(h):
                tile_type = "outside"
                self.tiles[x].append(Tile(self, (x, y), tile_type))
        self.all_tiles = self.get_all_tiles()
        # place building floors
        loading_screen(self.scene.game.loader, "...placing buildings...")
        num_buildings = 40 
        placed_buildings = 0
        building_size_range = (4, 10) 
        first = True
        while placed_buildings < num_buildings:
            bw = randint(building_size_range[0], building_size_range[1])
            bh = randint(building_size_range[0], building_size_range[1])
            if first:
                bw *= 2
                bh *= 2
                first = False
            origin = (randint(5, w - 5), randint(5, h - 40)) 
            for x in range(origin[0] - bw, origin[0] + bw + 1):
                for y in range(origin[1] - bh, origin[1] + bh + 1):
                    if self.coordinate_in_bounds((x, y)):
                        tile = self.tiles[x][y]
                        tile.tile_type = "floor"
                        tile.building_number = placed_buildings
            placed_buildings += 1
        # place outer walls
        loading_screen(self.scene.game.loader, "...placing outer building walls...")
        for x in range(w):
            for y in range(h):
                tile = self.tiles[x][y]
                nbrs = self.neighbors_of((x, y))
                if tile.tile_type == "floor" and (any(map(lambda t: t.tile_type == "outside", nbrs)) or tile.is_edge()):
                    tile.tile_type = "wall"
                    tile.outer_wall = True
        for bldg in range(num_buildings):
            spots = list(filter(lambda t: t.tile_type == "wall" and t.building_number == bldg and not t.is_edge(), \
                self.all_tiles))
            if len(spots) == 0:
                continue
        # reconciliation of overlapping building numbers
        loading_screen(self.scene.game.loader, "...tagging building zones...")
        def reconcile_overlapping_buildings(bldg_number):
            origins = list(filter(lambda t: t.building_number == bldg_number and t.walkable(), self.all_tiles))
            if len(origins) == 0:
                return
            origin = choice(origins)
            seen_bools = [[False for _ in range(h)] for _ in range(w)]
            seen_bools[origin.xy_tuple[0]][origin.xy_tuple[1]] = True
            seen = []
            start_node = [origin.xy_tuple]
            heapq.heappush(seen, start_node)
            while len(seen) > 0:
                node = heapq.heappop(seen)[0]
                nbrs = self.neighbors_of(node)
                for nbr in nbrs:
                    x, y = nbr.xy_tuple
                    if not seen_bools[x][y] and (nbr.tile_type == "floor" or nbr.tile_type == "wall"):
                        new_node = [(x, y)]
                        seen_bools[x][y] = True
                        heapq.heappush(seen, new_node)
                        self.get_tile((x, y)).building_number = bldg_number
        for bldg in range(num_buildings):
            reconcile_overlapping_buildings(bldg)
        # some happy little trees
        loading_screen(self.scene.game.loader, "...placing happy little trees...")
        num_trees = 600 
        placed_trees = 0
        while placed_trees < num_trees:
            spot = choice(list(filter(lambda t: t.tile_type == "outside", self.all_tiles)))
            spot.tile_type = "tree"
            placed_trees += 1
        # place inner walls  
        loading_screen(self.scene.game.loader, "...placing inner building walls...")
        for building in range(num_buildings):
            outer_walls = list(filter(lambda t: t.building_number == building and t.outer_wall, self.all_tiles))
            if len(outer_walls) == 0:
                continue
            viables = []
            for tile in outer_walls:
                nbrs = self.neighbors_of(tile.xy_tuple)
                num_outside = len(list(filter(lambda t: t.tile_type == "outside", nbrs)))
                num_floors = len(list(filter(lambda t: t.tile_type == "floor", nbrs)))
                if num_outside == num_floors == 3:
                    viables.append(tile)
            pairs = []  
            for tile in viables:
                for end in viables: 
                    vert_end = tile.xy_tuple[0] == end.xy_tuple[0] and tile.xy_tuple[1] != end.xy_tuple[1]
                    horiz_end = tile.xy_tuple[0] != end.xy_tuple[0] and tile.xy_tuple[1] == end.xy_tuple[1]
                    if chebyshev_distance(tile.xy_tuple, end.xy_tuple) == 1:
                        continue
                    if vert_end or horiz_end:
                        line = self.bresenham_line(tile.xy_tuple, end.xy_tuple)
                        valid = True
                        index = 0
                        for xy in line:
                            if not (xy == tile.xy_tuple or xy == end.xy_tuple) and self.get_tile(xy).tile_type == "wall":
                                valid = False
                                break
                            index += 1
                        if valid:
                            pairs.append((tile, end))
            shuffle(pairs)
            max_to_place = len(pairs) // 2
            min_to_place = 4
            if max_to_place <= min_to_place:
                inner_walls_to_place = max_to_place
            else:
                inner_walls_to_place = randint(min_to_place, max_to_place)
            walls_placed = 0
            while walls_placed < inner_walls_to_place and walls_placed < len(pairs):
                for wall in range(inner_walls_to_place):
                    if walls_placed >= len(pairs):
                        break
                    pair = pairs[walls_placed]
                    line = self.bresenham_line(pair[0].xy_tuple, pair[1].xy_tuple)
                    for xy in line:
                        tile = self.get_tile(xy)
                        tile.tile_type = "wall"
                    walls_placed += 1  
        # put a big tunnel maze in the biggest ones
        loading_screen(self.scene.game.loader, "...spicing up biggest buildings ...")
        tunnel_havens = randint(1, 3)
        sizes = []
        for building in range(num_buildings):
            size = len(list(filter(lambda t: t.building_number == building, self.all_tiles)))
            sizes.append((building, size))
        def sort_key(x):
            return x[1]
        sizes.sort(key=sort_key)
        for building in sizes[-tunnel_havens:]:  
            number = building[0]
            for tile in list(filter(lambda t: t.building_number == number, self.all_tiles)):
                tile.tile_type = "wall"
        loading_screen(self.scene.game.loader, "...beginning contiguity check...")
        # final contiguity pass
        def get_unreachable_tiles(first=False) -> list:
            if first:
                origin = choice(list(filter(lambda t: t.xy_tuple[1] == h - 1 and t.walkable(), self.all_tiles)))
            else:
                origin = choice(list(filter(lambda t: t.contiguous, self.all_tiles)))
            seen_bools = [[False for _ in range(h)] for _ in range(w)]
            seen_bools[origin.xy_tuple[0]][origin.xy_tuple[1]] = True
            origin.contiguous = True
            seen = []
            start_node = [origin.xy_tuple]
            heapq.heappush(seen, start_node)
            while len(seen) > 0:
                node = heapq.heappop(seen)[0]
                nbrs = self.neighbors_of(node)
                for nbr in nbrs:
                    x, y = nbr.xy_tuple
                    if not seen_bools[x][y] and nbr.walkable():
                        new_node = [(x, y)]
                        seen_bools[x][y] = True
                        heapq.heappush(seen, new_node)
                        self.get_tile((x, y)).contiguous = True
            return list(filter(lambda t: t.walkable() and not t.contiguous, self.all_tiles))
        unreachable = get_unreachable_tiles(first=True)
        def carve_path_to_contiguous(origin, deep_walls=False):
            goal = choice(list(filter(lambda t: t.contiguous, self.all_tiles)))
            line = self.bresenham_line(origin.xy_tuple, goal.xy_tuple)
            for xy in line:
                tile = self.get_tile(xy)
                if tile.tile_type == "outside":
                    break
                elif tile.tile_type == "floor" and deep_walls:
                    break
                tile.tile_type = "floor"
                tile.contiguous = True
        check = []
        fill_required = False
        starting_unreachable = len(unreachable)
        while len(unreachable) > 0:
            percent_unreachable = 100 - min(int((len(unreachable) / starting_unreachable) * 100), 99)
            loading_screen(self.scene.game.loader, "...reaching unreachable tiles ({}%)...".format(percent_unreachable))
            origin = unreachable[randrange(len(unreachable))]
            carve_path_to_contiguous(origin)
            unreachable = get_unreachable_tiles()
            check.append(len(unreachable))
            if len(check) > 3 and check[-3] == check[-2] == check[-1]:
                fill_required = True
                break
        if fill_required:
            loading_screen(self.scene.game.loader, "...performing fill...")
            for tile in unreachable:
                tile.tile_type = "wall"
        # A little pass to carve interesting passages
        def deep_walls() -> list:
            return list(filter(lambda t: all(map(lambda u: u.tile_type == "wall", self.neighbors_of(t.xy_tuple))) \
                and not t.is_edge(), self.all_tiles))
        deep_wall_sections = deep_walls()
        starting_deep_walls = len(deep_wall_sections)
        loading_screen(self.scene.game.loader, "...carving deep walls out...")
        while len(deep_wall_sections) > 0:
            percent_carved = 100 - min(int((len(deep_wall_sections) / starting_deep_walls) * 100), 99)
            loading_screen(self.scene.game.loader, "...carving tunnels ({}%)...".format(percent_carved))
            origin = choice(deep_wall_sections)
            carve_path_to_contiguous(origin, deep_walls=True)
            deep_wall_sections = deep_walls()
        # doors
        loading_screen(self.scene.game.loader, "...assigning doors...")
        color_index = 0
        for bldg in range(num_buildings):
            potentials = list(filter(lambda t: t.tile_type == "floor" and bldg == t.building_number, self.all_tiles))
            if len(potentials) == 0:
                continue
            doors = []
            for tile in potentials:
                nbrs = self.neighbors_of(tile.xy_tuple)
                if any(map(lambda t: t.tile_type == "outside", nbrs)):
                    doors.append(tile) 
            color = door_colors[color_index]
            color_index = (color_index + 1) % len(door_colors)
            for tile in doors:
                tile.door = True
                tile.door_color = color

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

    def set_all_unoccupied(self): 
        for x in range(self.wh_tuple[0]):
            for y in range(self.wh_tuple[1]):
                self.tiles[x][y].occupied = False

    def get_tile(self, xy_tuple) -> Tile:
        return self.tiles[xy_tuple[0]][xy_tuple[1]]

    def get_all_tiles(self) -> list:
        return flatten(self.tiles)

    def toggle_occupied(self, xy_tuple, status):
        if self.coordinate_in_bounds(xy_tuple):
            self.tiles[xy_tuple[0]][xy_tuple[1]].occupied = status

    def valid_tiles_in_range_of(self, xy_tuple, d, manhattan=False, walkable_only=False) -> list: 
        x1, y1 = xy_tuple
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

