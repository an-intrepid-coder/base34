from tile_map import *
from entity import *
from euclidean import *
from random import choice, randint, shuffle, randrange
from functional import *
from sheets import *
from console import *
from pygame.math import Vector2
from pygame import Rect
from pygame.event import Event
import heapq

class Scene:
    def __init__(self, game):
        self.speed = GAME_UPDATE_TICK_MS 
        self.game = game
        self.debug = game.debug
        self.debug_fov_triggered = False
        self.screen = game.screen
        self.screen_wh_cells_tuple = game.screen_wh_cells_tuple
        self.tilemap = None
        self.displaying_hud = True 
        self.paused = True
        self.console = Console(CONSOLE_HEIGHT // HUD_FONT_SIZE)
        pygame.time.set_timer(self.game.GAME_UPDATE_TICK, GAME_UPDATE_TICK_MS)
        pygame.time.set_timer(self.game.MOVER_CHECK, MOVER_TICK_MS)
        self.tilemap = TileMap(self, MAP_SIZE)
        self.side_hud = pygame.Surface((SIDE_HUD_WIDTH, self.screen.get_height()))
        self.side_hud.fill("dark gray")
        self.side_hud_splash_base = pygame.Surface((SIDE_HUD_WIDTH, HUD_FONT_SIZE + 3))
        pygame.draw.rect(self.side_hud_splash_base, "magenta", self.side_hud_splash_base.get_rect(), 1)
        self.redraw_map = True
        self.redraw_side_hud = True
        self.redraw_console = True
        self.do_update_on_screen_actors = True
        self.side_hud_group = Group()
        def mini_map_effect(xy_tuple):
            mm_cell_size = MINI_MAP_SIZE[0] / MAP_SIZE[0] 
            x, y = tuple(map(lambda z: z // mm_cell_size, xy_tuple))
            self.tilemap.camera = (x, y)
            self.redraw_switches()
        self.mini_map = Clickable(self.tilemap.mini_map_surface, MINI_MAP_SIZE[0], \
            MINI_MAP_SIZE[1], mini_map_effect, (0, 0))
        end_turn_button = Clickable(self.game.end_turn_surf, self.game.end_turn_surf.get_width(), \
            self.game.end_turn_surf.get_height(), self.end_turn, (0, END_TURN_BUTTON_Y))
        self.side_hud_group.add([self.mini_map, end_turn_button]) 
        self.actors_group = Group() 
        self.on_screen_actors_group = Group()
        self.on_screen_map_surface = pygame.Surface((self.screen_wh_cells_tuple[0] * CELL_SIZE, \
            self.screen_wh_cells_tuple[1] * CELL_SIZE), flags=SRCALPHA)
        self.player = self.make_player() 
        self.distance_map_to_player = self.djikstra_map_distance_to(self.player.cell_xy())
        self.actor_update_fov(self.player)
        self.tilemap.camera = self.player.cell_xy()
        self.tilemap.toggle_occupied(self.player.cell_xy(), True)
        self.actors_group.add(self.player)
        self.selected_tile = None
        self.move_select_to_confirm = False
        self.move_path = None
        self.movers = []

    def actor_update_fov(self, actor):
        potentials = self.tilemap.valid_tiles_in_range_of(actor.cell_xy(), actor.fov_radius)
        visible = []
        for tile in potentials:
            line = self.tilemap.bresenham_line(actor.cell_xy(), tile.xy_tuple)
            unblocked = True
            for xy in line:
                tile = self.tilemap.get_tile(xy)
                visible.append(tile)
                if tile.blocks_vision():
                    unblocked = False
                    break
        if self.debug and not self.debug_fov_triggered and actor.player:
            visible = self.tilemap.all_tiles()
            self.debug_fov_triggered = True
        actor.tiles_can_see = visible
        for tile in visible: 
            if not tile.seen:  
                pos = (tile.xy_tuple[0] * CELL_SIZE, tile.xy_tuple[1] * CELL_SIZE)
                self.tilemap.toggle_seen(tile.xy_tuple, True)
                if actor.player:
                    self.tilemap.map_surface.blit(tile.foggy_img, pos)
                    self.tilemap.mini_map_surface_master.blit(tile.visible_img, pos)
        if actor.player:
            self.tilemap.update_mini_map_surface()
            self.mini_map.image = self.tilemap.mini_map_surface

    def end_turn(self, xy=None):
        self.game.turn += 1
        self.selected_tile = None
        self.move_select_to_confirm = False
        self.move_path = None
        self.player.tu = self.player.max_tu
        self.redraw_switches()

    def make_player(self) -> Actor: ### NOTE: starting position a placeholder
        pos = choice(list(filter(lambda x: x.tile_type == "floor", self.tilemap.all_tiles()))).xy_tuple
        player = Actor(self.game.entity_sheets[self.game.dude_1_sheet], CELL_SIZE, CELL_SIZE, None, cell_xy_tuple=pos)
        player.tu, player.max_tu = 28, 28
        player.player = True
        return player

    def get_topleft_cell(self):
        return (self.tilemap.camera[0] - self.screen_wh_cells_tuple[0] // 2, \
            self.tilemap.camera[1] - self.screen_wh_cells_tuple[1] // 2)

    def input_blocked(self):
        return len(self.movers) > 0

    def on_screen_cells_rect(self) -> Rect:
        topleft = self.get_topleft_cell()
        return Rect((topleft[0], topleft[1], self.screen_wh_cells_tuple[0], self.screen_wh_cells_tuple[1]))

    def draw(self): 
        topleft = self.get_topleft_cell()
        cells_on_screen = self.on_screen_cells_rect()
        def draw_mm_view_rect():
            mm_cell_size = MINI_MAP_SIZE[0] / MAP_SIZE[0] 
            view_w = (((self.screen.get_width() - SIDE_HUD_WIDTH) // CELL_SIZE) + 1) * mm_cell_size
            view_h = (self.screen_wh_cells_tuple[1] + 1) * mm_cell_size
            view = (topleft[0] * mm_cell_size, topleft[1] * mm_cell_size, view_w, view_h)
            pygame.draw.rect(self.side_hud, "white", view, 1)
        if self.redraw_map:
            self.on_screen_map_surface.fill("black")
            area_rect = (topleft[0] * CELL_SIZE, topleft[1] * CELL_SIZE, self.screen_wh_cells_tuple[0] * CELL_SIZE, \
                self.screen_wh_cells_tuple[1] * CELL_SIZE)
            self.on_screen_map_surface.blit(self.tilemap.map_surface, (0, 0), area=area_rect)
            visible_blits = []
            move_range_blits = []
            for tile in self.player.tiles_can_see:
                x, y = tile.xy_tuple
                pos = ((x - topleft[0]) * CELL_SIZE, (y - topleft[1]) * CELL_SIZE)
                visible_blits.append((tile.visible_img, pos))
                dscore = self.distance_map_to_player[x][y]
                valid_score = dscore * TU_MOVEMENT <= self.player.tu
                if tile.walkable() and valid_score:
                    move_range_blits.append((self.game.movement_range_cell_surf, pos))
            for tile in list(filter(lambda x: x not in self.player.tiles_can_see, \
                self.tilemap.valid_tiles_in_range_of(self.player.cell_xy(), \
                (self.game.MAP_DISPLAY_SIZE[0] // 2) // CELL_SIZE))):
                dscore = self.distance_map_to_player[x][y]
                valid_score = dscore * TU_MOVEMENT <= self.player.tu
                if tile.walkable() and valid_score:
                    move_range_blits.append((self.game.movement_range_cell_surf, pos))
            self.on_screen_map_surface.blits(visible_blits)
            self.on_screen_map_surface.blits(move_range_blits)
            if self.move_path is not None:
                for xy in self.move_path:
                    x, y = xy
                    pos = (((x - topleft[0]) * CELL_SIZE) + CELL_SIZE // 2, \
                        ((y - topleft[1]) * CELL_SIZE) + CELL_SIZE // 2)
                    pygame.draw.circle(self.on_screen_map_surface, "cyan", pos, 8)
            self.on_screen_actors_group.draw(self.on_screen_map_surface)  ## TODO: visible actors group
            self.screen.blit(self.on_screen_map_surface, (0, 0))
        if self.redraw_side_hud:
            def draw_dynamic_hud_surf(msg, y):
                surf = self.game.hud_font.render(msg, True, "white", "black")
                base = pygame.Surface((SIDE_HUD_WIDTH, surf.get_height() + 2))
                pygame.draw.rect(base, "magenta", base.get_rect(), 1)
                base.blit(surf, (base.get_width() // 2 - surf.get_width() // 2, 1))
                self.side_hud.blit(base, (0, y))
            x = self.screen.get_width() - SIDE_HUD_WIDTH
            self.side_hud_group.draw(self.side_hud)
            draw_mm_view_rect()
            draw_dynamic_hud_surf("Turn: {}".format(self.game.turn), TURN_Y)
            draw_dynamic_hud_surf("TU: {} / {}".format(self.player.tu, self.player.max_tu), TU_REMAINING_Y)
            self.screen.blit(self.side_hud, (x, 0))
        if self.redraw_console:
            console_surf = pygame.Surface((self.screen.get_width() - SIDE_HUD_WIDTH, CONSOLE_HEIGHT))
            pygame.draw.rect(console_surf, "magenta", console_surf.get_rect(), 1)
            line_height = HUD_FONT_SIZE + 1
            num_lines = self.console.lines
            last = len(self.console.messages) - 1
            msgs = []
            for line in range(num_lines):
                index = last - line - self.console.scrolled_up_by
                if index >= 0 and index < len(self.console.messages):
                    msg = self.console.messages[index]
                    txt = "[{}] {}".format(msg.turn, msg.msg)
                    msgs.append(txt)
            msgs.reverse() 
            for line in range(len(msgs)):
                line_surface = self.game.hud_font.render(msgs[line], True, "white")
                console_surf.blit(line_surface, (0, line * line_height))
            self.screen.blit(console_surf, (0, self.screen.get_height() - CONSOLE_HEIGHT))
        if self.redraw_map or self.redraw_side_hud:
            pygame.display.flip()
        if self.redraw_map:
            self.redraw_map = False
        if self.redraw_side_hud:
            self.redraw_side_hud = False

    def push_to_console_if_player(self, msg, actors, tag=None):
        if any(filter(lambda x: x.player, actors)):
            self.console.push(Message(msg, self.game.turn, tag))
            self.redraw_console = True

    def push_to_console(self, msg, tag=None):
        self.console.push(Message(msg, self.game.turn, tag))
        self.redraw_console = True

    def handle_events(self):
        def handle_keyboard_events():
            screen_scrolled = [False for _ in range(4)]
            if pygame.key.get_pressed()[K_w]: 
                screen_scrolled[0] = self.tilemap.scroll((0, -1))
            if pygame.key.get_pressed()[K_a]:
                screen_scrolled[1] = self.tilemap.scroll((-1, 0))
            if pygame.key.get_pressed()[K_s]:
                screen_scrolled[2] = self.tilemap.scroll((0, 1))
            if pygame.key.get_pressed()[K_d]:
                screen_scrolled[3] = self.tilemap.scroll((1, 0))
            if any(screen_scrolled):
                self.redraw_switches()
            console_changed = False
            if pygame.key.get_pressed()[K_LEFTBRACKET]:
                self.console.scroll("up")
                console_changed = True
            elif pygame.key.get_pressed()[K_RIGHTBRACKET]:
                self.console.scroll("down")
                console_changed = True
            elif pygame.key.get_pressed()[K_HOME]:
                self.console.reset()
                console_changed = True
            if console_changed:
                self.redraw_switches()

        def tile_clicked(xy_tuple) -> tuple: # or None
            x, y = xy_tuple
            w, h = self.tilemap.wh_tuple
            if x >= self.screen.get_width() - SIDE_HUD_WIDTH:
                return None
            topleft = self.get_topleft_cell()
            tx, ty = (x // CELL_SIZE + topleft[0], y // CELL_SIZE + topleft[1])
            if tx < 0 or ty < 0 or tx >= w or ty >= h:
                return None
            return (int(tx), int(ty))

        def handle_left_click():
            x, y = pygame.mouse.get_pos()
            for entity in self.side_hud_group: # clickables are offset 
                if isinstance(entity, Clickable):
                    x2 = x - (self.screen.get_width() - SIDE_HUD_WIDTH)
                    if entity.clicked((x2, y)):
                        entity.effect((x2, y))
            tile_clicked_xy = tile_clicked((x, y))
            if tile_clicked_xy is not None:
                tile = self.tilemap.get_tile(tile_clicked_xy)
                tx, ty = tile_clicked_xy
                if not self.move_select_to_confirm and not tile.occupied:
                    cost = self.distance_map_to_player[tx][ty] * TU_MOVEMENT 
                    if cost <= self.player.tu and tile.walkable() and tile.seen: 
                        self.selected_tile = tile_clicked_xy
                        self.move_select_to_confirm = True
                        dmap = self.djikstra_map_distance_to(tile_clicked_xy)
                        self.move_path = self.shortest_path(self.player.cell_xy(), tile_clicked_xy, dmap)
                        self.redraw_switches()
                elif self.move_select_to_confirm and tile_clicked_xy == self.selected_tile:
                    cost = self.distance_map_to_player[tx][ty] * TU_MOVEMENT 
                    self.player.tu -= cost
                    self.tilemap.camera = self.move_path[-1]
                    self.movers.append(Mover(self.player, [xy for xy in self.move_path]))
                    self.distance_map_to_player = self.djikstra_map_distance_to(self.move_path[-1])
                    self.selected_tile = None
                    self.move_path = None
                    self.move_select_to_confirm = False
                    self.redraw_switches()
                else:
                    self.move_path = None
                    self.selected_tile = None
                    self.move_select_to_confirm = False
                    self.redraw_switches()
            # TODO: cases of clicking on visible actors

        def handle_middle_click():
            x, y = pygame.mouse.get_pos()
            tile_clicked_xy = tile_clicked((x, y))
            if tile_clicked_xy is not None:
                self.tilemap.camera = tile_clicked_xy
                self.redraw_switches()

        def handle_mouse_clicks():
            if pygame.mouse.get_pressed()[0]:
                handle_left_click()
            elif pygame.mouse.get_pressed()[1]:
                handle_middle_click()
            elif pygame.mouse.get_pressed()[2]:
                pass # TODO: right-click context menus

        def handle_mousewheel_scroll(y):
            pos = pygame.mouse.get_pos()
            rect = Rect((0, self.screen.get_height() - CONSOLE_HEIGHT, self.screen.get_width() - SIDE_HUD_WIDTH, \
                CONSOLE_HEIGHT))
            if rect.contains((pos[0], pos[1], 0, 0)):
                for _ in range(abs(y)):
                    if y < 0:
                        self.console.scroll("down")
                    else:
                        self.console.scroll("up")
                self.redraw_switches()

        def handle_movers():
            removed = []
            for mover in self.movers:
                from_xy = mover.actor.cell_xy()
                to_xy = mover.path[0]
                new_orientation = self.relative_direction(from_xy, to_xy)
                mover.actor.change_orientation(new_orientation)
                mover.actor.update_frame()
                mover.actor.cell_x, mover.actor.cell_y = to_xy
                mover.path = mover.path[1:]
                self.actor_update_fov(mover.actor) ###
                self.redraw_switches()
                if mover.actor.cell_xy() == mover.goal:
                    removed.append(mover)
            self.movers = list(filter(lambda x: x not in removed, self.movers))

        for event in pygame.event.get():
            # quit game:
            if event.type == QUIT:
                self.game.running = False
            # Keyboard Buttons:
            elif event.type == KEYDOWN and not self.input_blocked():
                handle_keyboard_events()
            # Mouse Events:
            elif event.type == MOUSEBUTTONDOWN and not self.input_blocked():
                handle_mouse_clicks()
            elif event.type == MOUSEWHEEL and not self.input_blocked():
                handle_mousewheel_scroll(event.y)
            # movers
            elif event.type == self.game.MOVER_CHECK:
                handle_movers()
        pygame.event.pump() 

    def update_on_screen_actors(self):
        self.on_screen_actors_group = Group()
        topleft = self.get_topleft_cell()
        for actor in self.actors_group:
            if actor.on_screen(topleft, self.screen_wh_cells_tuple):
                actor.x = (actor.cell_x - topleft[0]) * CELL_SIZE
                actor.y = (actor.cell_y - topleft[1]) * CELL_SIZE
                actor.rect = Rect(actor.x, actor.y, actor.width, actor.height) 
                self.on_screen_actors_group.add(actor)
        self.do_update_on_screen_actors = False

    def redraw_switches(self):
        self.redraw_map = True
        self.redraw_side_hud = True
        self.redraw_console = True
        self.do_update_on_screen_actors = True

    def update(self):
        self.handle_events()
        if self.do_update_on_screen_actors:
            self.update_on_screen_actors()

    def relative_direction(self, from_xy, to_xy, opposite=False):
        diff = (to_xy[0] - from_xy[0], to_xy[1] - from_xy[1])
        if opposite:
            diff = tuple(map(lambda x: x * -1, diff))
        for k, v in DIRECTIONS.items():
            if v == diff:
                return k
        return "wait"

    def shift_pressed(self) -> bool:
        return pygame.key.get_pressed()[K_RSHIFT] or pygame.key.get_pressed()[K_LSHIFT]

    def ctrl_pressed(self) -> bool:
        return pygame.key.get_pressed()[K_RCTRL] or pygame.key.get_pressed()[K_LCTRL]

    def djikstra_map_distance_to(self, xy_tuple) -> list:
        w, h = self.tilemap.wh_tuple
        dmap = [[0 for _ in range(h)] for _ in range(w)]
        def loc(node):
            return node[2]
        def score(node):
            return node[0]
        diagonals = ["upleft", "downleft", "upright", "downright"]
        seen_bools = [[False for _ in range(h)] for _ in range(w)]
        seen_bools[xy_tuple[0]][xy_tuple[1]] = True
        seen = []
        entry_count = 1
        start_node = [0, 0, xy_tuple]
        heapq.heappush(seen, start_node)
        while len(seen) > 0:
            node = heapq.heappop(seen)
            nbrs = self.tilemap.neighbors_of(loc(node))
            for nbr in nbrs:
                x, y = nbr.xy_tuple
                if not seen_bools[x][y] and nbr.walkable():
                    if self.relative_direction(loc(node), (x, y)) in diagonals:
                        nbr_score = score(node) + 2
                    else:
                        nbr_score = score(node) + 1
                    new_node = [nbr_score, entry_count, nbr.xy_tuple]
                    heapq.heappush(seen, new_node)
                    seen_bools[x][y] = True
                    entry_count += 1
                    dmap[nbr.xy_tuple[0]][nbr.xy_tuple[1]] = nbr_score
                elif not nbr.walkable():
                    dmap[nbr.xy_tuple[0]][nbr.xy_tuple[1]] = INVALID_DJIKSTRA_SCORE
        return dmap

    def shortest_path(self, start_xy, end_xy, dmap) -> list:
        # NOTE: Available path always assured before calling.
        def sort_key(tile):
            return dmap[tile.xy_tuple[0]][tile.xy_tuple[1]]
        traceback = [start_xy]
        current = start_xy
        while current != end_xy:
            nbrs = self.tilemap.neighbors_of(current)
            nbrs.sort(key=sort_key) 
            x, y = nbrs[0].xy_tuple
            if len(nbrs) == 0 or dmap[x][y] >= INVALID_DJIKSTRA_SCORE:
                return None 
            shortest = (x, y)
            traceback.append(shortest)
            current = shortest
        return traceback
        
