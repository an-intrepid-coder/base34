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
        self.console = Console(CONSOLE_HEIGHT // HUD_FONT_SIZE)
        pygame.time.set_timer(self.game.GAME_UPDATE_TICK, GAME_UPDATE_TICK_MS)
        if self.debug:
            pygame.time.set_timer(self.game.VISIBLE_MOVER_CHECK, MOVER_TICK_MS_INVISIBLE)
        else:
            pygame.time.set_timer(self.game.VISIBLE_MOVER_CHECK, MOVER_TICK_MS_VISIBLE)
        pygame.time.set_timer(self.game.INVISIBLE_MOVER_CHECK, MOVER_TICK_MS_INVISIBLE)
        pygame.time.set_timer(self.game.PLAYER_TURN_READY_CHECK, PLAYER_TURN_READY_TICK_MS)
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
        self.game_over_group = Group()
        self.win_group = Group()
        def try_again_effect(xy_tuple):
            self.reset_scenario()
        def exit_game_effect(xy_tuple):
            self.game.running = False
        try_again_img = self.game.game_over_button_surf.copy()
        try_again_txt = self.game.title_font.render("Try Again?", True, "white", "black")
        ta_txt_pos = (try_again_img.get_width() // 2 - try_again_txt.get_width() // 2, \
            try_again_img.get_height() // 2 - try_again_txt.get_height() // 2)
        try_again_img.blit(try_again_txt, ta_txt_pos)
        ta_pos = (10, self.game.big_splash_surf.get_height() - try_again_img.get_height() - 10)
        self.game_over_group.add(Clickable(try_again_img, try_again_img.get_width(), try_again_img.get_height(), \
            try_again_effect, ta_pos))
        game_over_img = self.game.game_over_button_surf.copy()
        game_over_txt = self.game.title_font.render("Exit Game", True, "white", "black")
        go_txt_pos = (game_over_img.get_width() // 2 - game_over_txt.get_width() // 2, \
            game_over_img.get_height() // 2 - game_over_txt.get_height() // 2)
        game_over_img.blit(game_over_txt, go_txt_pos)
        go_pos = (self.game.big_splash_surf.get_width() - game_over_img.get_width() - 10, \
            self.game.big_splash_surf.get_height() - game_over_img.get_height() - 10)
        self.game_over_group.add(Clickable(game_over_img, game_over_img.get_width(), game_over_img.get_height(), \
            exit_game_effect, go_pos))
        self.win_group.add(Clickable(game_over_img, game_over_img.get_width(), game_over_img.get_height(), \
            exit_game_effect, go_pos))
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
        self.distance_map_to_player = self.dmap_to_player()
        self.actor_update_fov(self.player)
        self.tilemap.camera = self.player.cell_xy()
        self.tilemap.toggle_occupied(self.player.cell_xy(), True)
        self.actors_group.add(self.player)
        self.selected_tile = None
        self.move_select_to_confirm = False
        self.move_path = None
        self.visible_movers = []
        self.invisible_movers = []
        self.player_turn = True
        self.enemy_los_tiles = []
        self.building_numbers = []
        self.local_bounding_rects = {}
        self.alert_timer = None
        self.alert_zone_rect = None
        self.game_over_mode = False
        self.game_over_mode_draw_sentinel = False
        self.win_mode = False
        self.win_mode_draw_sentinel = False
        self.generate_scenario()

    def reset_scenario(self):
        self.push_to_console("Resetting scenario...")
        self.tilemap.reset()
        self.mini_map.image = self.tilemap.mini_map_surface
        self.game_over_mode = False
        self.draw()
        self.actors_group.empty() 
        self.on_screen_actors_group.empty()
        self.player = self.make_player() 
        self.distance_map_to_player = self.dmap_to_player()
        self.actor_update_fov(self.player)
        self.tilemap.camera = self.player.cell_xy()
        self.tilemap.toggle_occupied(self.player.cell_xy(), True)
        self.actors_group.add(self.player)
        self.selected_tile = None
        self.move_select_to_confirm = False
        self.move_path = None
        self.visible_movers = []
        self.invisible_movers = []
        self.player_turn = True
        self.enemy_los_tiles = []
        self.building_numbers = []
        self.local_bounding_rects = {}
        Baddie.num_long_rovers = 0
        Baddie.num_local_rovers = 0
        Baddie.num_alert_rovers = 0
        self.alert_timer = None
        self.alert_zone_rect = None
        self.game_over_mode_draw_sentinel = False
        self.generate_scenario()
        self.redraw_switches()

    def generate_scenario(self):
        loading_screen(self.game.loader, "...memoizing bounding rects...")
        for tile in self.tilemap.all_tiles():
            if tile.building_number is not None and tile.building_number not in self.building_numbers:
                self.building_numbers.append(tile.building_number)
        if self.debug:
            self.player.building_patrol_intels = self.building_numbers
        for building in self.building_numbers: 
            building_tiles = list(filter(lambda t: t.building_number == building, self.tilemap.all_tiles()))
            min_y, max_y, min_x, max_x = 999, -100, 999, -100
            for tile in building_tiles:
                x, y = tile.xy_tuple
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y
            d = chebyshev_distance((min_x, min_y), (max_x, max_y))
            padded_rect = (max(min_x - 10, 0), max(min_y - 10, 0), d + 21, d + 21) 
            self.local_bounding_rects[building] = padded_rect 
        loading_screen(self.game.loader, "...generating baddies...")
        baddies = []
        for building in self.building_numbers: 
            num_baddies = randint(2, 4) 
            for _ in range(num_baddies):
                baddie = self.make_baddie(building)
                baddies.append(baddie)
        shuffle(baddies)
        self.actors_group.add(baddies) 
        loading_screen(self.game.loader, "...placing loot...")
        loot = []
        macguffin = self.make_macguffin()
        loot.append(macguffin)
        for building in self.building_numbers:
            terminal = self.make_patrol_intel_terminal(building)
            loot.append(terminal)
        self.actors_group.add(loot) # more loot to come
        loading_screen(self.game.loader, "...issuing orders to baddies...")
        self.run_ai_behavior() 
        if self.debug:
            self.actor_update_fov(self.player)

    def dmap_to_player(self, bounded=False) -> list:
        x, y = self.player.cell_xy()
        bounding_rect = (x - ALERT_ZONE_D, y - ALERT_ZONE_D, ALERT_ZONE_D * 2 + 1, ALERT_ZONE_D * 2 + 1)
        if bounded:
            dmap = self.djikstra_map_distance_to((x, y), (x, y), bounding_rect=bounding_rect)
        else:
            dmap = self.djikstra_map_distance_to((x, y), (x, y))
        return dmap

    def tile_in_player_move_range(self, score, tile) -> bool:
        affordable = score * TU_MOVEMENT <= self.player.tu
        return affordable \
            and tile.walkable() \
            and tile in self.player.tiles_can_see \
            and tile.xy_tuple != self.player.cell_xy()

    def actor_interact(self, actor, loot): 
        if loot.name == "patrol intel terminal":
            building_number = loot.building_number
            if isinstance(actor, Player) and building_number not in self.player.building_patrol_intels:
                self.player.building_patrol_intels.append(building_number)
                self.push_to_console("Found intel on baddie patrols, and a small map!")
                self.push_to_console("...mapping...")
                self.redraw_switches()
                self.draw()
                def reveal(tile):
                    self.reveal_tile(tile)
                r = Rect(self.local_bounding_rects[building_number])
                revealed = list(filter(lambda t: r.contains(Rect(t.xy_tuple[0], t.xy_tuple[1], 0, 0)), \
                    self.tilemap.all_tiles()))
                edge_fuzz = []
                edges = list(filter(lambda t: t.xy_tuple[0] == r.x or t.xy_tuple[1] == r.y \
                    or t.xy_tuple[0] == r.x + r.width - 1 or t.xy_tuple[1] == r.y + r.height - 1, revealed))
                for edge in edges:
                    d = randint(4, 6)
                    fuzz = self.tilemap.valid_tiles_in_range_of(edge.xy_tuple, d, manhattan=True)
                    revealed.extend(list(filter(lambda t: t not in revealed, fuzz)))
                apply(reveal, revealed)
                self.tilemap.update_mini_map_surface()
                self.mini_map.image = self.tilemap.mini_map_surface
                loot.looted = True
                self.player.actions_available = self.actor_possible_actions(self.player)
                self.redraw_switches()
            # TODO: Perhaps something here for baddies to notice if terminals have been used
        elif loot.name == "macguffin" and isinstance(actor, Player):
            self.push_to_console("You found the MacGuffin! You won!")
            self.push_to_console("... in the next version, we'll have a more robust victory condition.")
            loot.looted = True
            self.player.actions_available = self.actor_possible_actions(self.player)
            self.draw()
            self.win_mode = True
            self.redraw_switches()

    def actor_update_fov(self, actor):
        x, y = actor.cell_xy() 
        r = actor.fov_radius
        potentials = self.tilemap.valid_tiles_in_range_of(actor.cell_xy(), r)
        if actor.orientation in ["upleft", "downleft", "upright", "downright"]:
            if actor.orientation == "upleft":
                rect = (x - r, y - r, r + 2, r + 2)
                rear = [(x + 1, y + 1), (x, y + 1), (x + 1, y)]
            elif actor.orientation == "upright":
                rect = (x - 1, y - r, r + 2, r + 2)
                rear = [(x - 1, y), (x - 1, y + 1), (x, y + 1)]
            elif actor.orientation == "downleft":
                rect = (x - r, y - 1, r + 2, r + 2)
                rear = [(x, y - 1), (x + 1, y - 1), (x, y + 1)]
            elif actor.orientation == "downright":
                rect = (x - 1, y - 1, r + 2, r + 2)
                rear = [(x - 1, y - 1), (x, y - 1), (x - 1, y)]
            potentials = list(filter(lambda t: t.xy_tuple[0] >= rect[0] and t.xy_tuple[1] >= rect[1] \
                and t.xy_tuple[0] < rect[0] + rect[2] and t.xy_tuple[1] < rect[1] + rect[3] \
                and t.xy_tuple not in rear, potentials))
        elif actor.orientation in ["up", "down", "left", "right"]:
            if actor.orientation == "up":
                origin = (x, y - (r + 1))
                rear = (x, y + 1)
            elif actor.orientation == "down":
                origin = (x, y + r + 1)
                rear = (x, y - 1)
            elif actor.orientation == "left":
                origin = (x - (r + 1), y)
                rear = (x + 1, y)
            elif actor.orientation == "right":
                origin = (x + r + 1, y)
                rear = (x - 1, y)
            in_cone = self.tilemap.valid_tiles_in_range_of(origin, r + 2, manhattan=True)
            potentials = list(filter(lambda t: t in in_cone and t.xy_tuple != rear, potentials))
        visible = []
        for tile in potentials:
            line = self.tilemap.bresenham_line(actor.cell_xy(), tile.xy_tuple)
            unblocked = True
            for xy in line:
                tile = self.tilemap.get_tile(xy)
                if tile not in visible:
                    visible.append(tile)
                if tile.blocks_vision() and tile.xy_tuple != actor.cell_xy():
                    unblocked = False
                    break
        if self.debug and not self.debug_fov_triggered and actor.player:
            visible = self.tilemap.all_tiles()
            self.debug_fov_triggered = True
        actor.tiles_can_see = visible
        if actor.player:
            for tile in visible: 
                self.reveal_tile(tile)
        if actor.player:
            self.update_player_visible_baddies()
            self.tilemap.update_mini_map_surface()
            self.mini_map.image = self.tilemap.mini_map_surface

    def reveal_tile(self, tile):
        if not tile.seen:  
            pos = (tile.xy_tuple[0] * CELL_SIZE, tile.xy_tuple[1] * CELL_SIZE)
            self.tilemap.toggle_seen(tile.xy_tuple, True)
            img = tile.visible_img.copy()
            img.blit(self.game.foggy_cell_surf, (0, 0))
            if self.game.show_bldg_numbers and (tile.tile_type == "floor" or tile.tile_type == "wall"):
                bldg_text = self.game.hud_font.render("{}".format(tile.building_number), True, "white", "black")
                bpos = (img.get_width() // 2 - bldg_text.get_width() // 2, \
                    img.get_height() // 2 - bldg_text.get_height() // 2)
                img.blit(bldg_text, bpos)
            self.tilemap.map_surface.blit(img, pos)
            self.tilemap.mini_map_surface_master.blit(tile.visible_img, pos)

    def run_ai_behavior(self):
        Baddie.alert_sentinel = False
        for actor in list(filter(lambda a: not a.player, self.actors_group)):
            if isinstance(actor, Baddie):
                self.actor_ai_baddie(actor) 
        if self.debug:
            self.push_to_console("<Rovers> Local: {} | Long: {} | Alert: {}".format(Baddie.num_local_rovers, \
                Baddie.num_long_rovers, Baddie.num_alert_rovers))
            self.push_to_console("Stationary: {}".format(len(list(filter(lambda b: not b.is_rover(), \
                self.all_baddies())))))

    def actor_ai_path_to_random_floor_tile(self, actor) -> list:
        target = choice(list(filter(lambda t: t.tile_type == "floor" and not t.occupied \
            and not t.door, self.tilemap.all_tiles())))
        path = self.shortest_path(actor.cell_xy(), target.xy_tuple)
        return path 

    def actor_ai_alert_path(self, actor) -> list:
        if self.alert_zone_rect is None: ###
            self.alert_zone_rect = self.new_alert_zone_rect(actor.cell_xy())
        r = Rect(self.alert_zone_rect)
        target = choice(list(filter(lambda t: t.walkable() and not t.occupied \
            and not t.door and r.contains(Rect(t.xy_tuple[0], t.xy_tuple[1], 0, 0)), self.tilemap.all_tiles())))
        path = self.shortest_path(actor.cell_xy(), target.xy_tuple, bounding_rect=self.alert_zone_rect)
        return path 

    def actor_ai_return_home(self, actor):
        target = choice(list(filter(lambda t: t.walkable() and not t.occupied and not t.door\
            and t.building_number == actor.building_number \
            and chebyshev_distance(t.xy_tuple, actor.cell_xy()) > 2, self.tilemap.all_tiles())))
        path = self.shortest_path(actor.cell_xy(), target.xy_tuple)
        return path

    def actor_ai_path_to_local_floor_tile(self, actor) -> list:
        target = choice(list(filter(lambda t: t.walkable() and not t.occupied and not t.door\
            and t.building_number == actor.building_number \
            and chebyshev_distance(t.xy_tuple, actor.cell_xy()) > 2, self.tilemap.all_tiles())))
        x, y = actor.cell_xy()
        bounding_rect = self.local_bounding_rects[actor.building_number]
        path = self.shortest_path((x, y), target.xy_tuple, bounding_rect=bounding_rect)
        return path  

    def actor_possible_actions(self, actor) -> list: # [(action, target), ...]
        actions = []
        opponents_in_melee_range = list(filter(lambda a: a.faction != actor.faction \
            and chebyshev_distance(actor.cell_xy(), a.cell_xy()) == 1 and a.can_be_knocked_out(), self.actors_group))
        loot_in_range = list(filter(lambda a: isinstance(a, Loot) and chebyshev_distance(actor.cell_xy(), \
            a.cell_xy()) == 1 and not a.looted, self.actors_group))
        for opponent in opponents_in_melee_range:
            tile = self.tilemap.get_tile(opponent.cell_xy())
            if tile in actor.tiles_can_see and actor.tu >= TU_MELEE:
                actions.append(["melee", opponent])
        for loot in loot_in_range:
            tile = self.tilemap.get_tile(loot.cell_xy())
            if tile in actor.tiles_can_see:
                actions.append(["interact", loot])
        return actions

    def actor_take_melee_action(self, actor, action):
        target = action[1]
        target.knocked_out = True
        msg = "{} knocks out {} with some slick CQC!".format(actor.name, target.name)
        self.push_to_console_if_player(msg, [actor, target])
        actor.tu -= TU_MELEE

    def actor_ai_baddie(self, baddie, new_chase=False): 
        actions = self.actor_possible_actions(baddie)
        def take_actions(): 
            melee_actions = list(filter(lambda a: a[0] == "melee", actions))
            if len(melee_actions) > 0 and baddie.tu >= TU_MELEE:
                shuffle(melee_actions)
                self.actor_take_melee_action(baddie, melee_actions[0])
            # TODO: interactive object actions for AI, perhaps
        def add_to_movers():
            visible_mover = first(lambda m: m.actor is baddie, self.visible_movers)
            invisible_mover = first(lambda m: m.actor is baddie, self.invisible_movers) 
            if baddie.cell_xy() in self.player.tiles_can_see:
                if invisible_mover is not None and invisible_mover in self.invisible_movers:
                    self.invisible_movers.remove(invisible_mover)
                self.visible_movers.append(Mover(baddie, [xy for xy in baddie.patrol_path]))
                if baddie not in self.player.visible_baddies:
                    self.player.visible_baddies.append(baddie) 
            elif visible_mover is None:
                self.invisible_movers.append(Mover(baddie, [xy for xy in baddie.patrol_path]))
        def assign_roving_status() -> bool:
            def will_rove() -> bool:
                return randint(0, 1) == 1
            def will_turn() -> bool:
                return randint(1, 10) <= 3
            if self.alert_timer is not None and baddie.alert_rover:
                return True
            if will_rove():
                if Baddie.num_long_rovers < NUM_LONG_ROVERS and not baddie.alert_rover:
                    baddie.set_long_rover() 
                    return True
                elif Baddie.num_local_rovers < NUM_LOCAL_ROVERS and not baddie.alert_rover:
                    baddie.set_local_rover() 
                    return True
                elif will_turn() and baddie.tu >= TU_TURN:
                    valid = list(filter(lambda t: t.walkable(), self.tilemap.neighbors_of(baddie.cell_xy())))
                    orientation = relative_direction(baddie.cell_xy(), choice(valid).xy_tuple)
                    baddie.change_orientation(orientation)
                    baddie.tu -= TU_TURN
                    self.actor_update_fov(baddie)
                return False
            return False
        def assign_patrol_path() -> list:
            if baddie.long_rover:
                baddie.patrol_path = self.actor_ai_path_to_random_floor_tile(baddie)
            elif baddie.local_rover: 
                r = Rect(self.local_bounding_rects[baddie.building_number])
                if not r.contains(Rect(baddie.cell_x, baddie.cell_y, 0, 0)):
                    baddie.patrol_path = self.actor_ai_return_home(baddie)
                    if self.debug:
                        self.push_to_console("Baddie returning home.")
                else:
                    baddie.patrol_path = self.actor_ai_path_to_local_floor_tile(baddie)
            elif baddie.alert_rover:
                baddie.patrol_path = self.actor_ai_alert_path(baddie)
        def spotter_alert_call():
            if baddie.tu >= TU_RADIO_CALL:
                call_made = self.begin_alert()
                if self.tilemap.get_tile(baddie.cell_xy()) in self.player.tiles_can_see and call_made:
                    self.push_to_console("Baddie calls in your position!")
        if baddie.patrol_path is None or baddie.patrol_path_reached():
            baddie.un_rover()
            baddie.patrol_path = None
            assign_roving_status()
            assign_patrol_path()
            if baddie.patrol_path is None:
                if self.debug:
                    self.push_to_console("baddie at bldg #{} path is None".format(baddie.building_number))
                    self.push_to_console("Long Rover: {} | Local Rover: {} | Alert Rover: {}".format(\
                        baddie.long_rover, baddie.local_rover, baddie.alert_rover))
                baddie.finished_turn = True 
            else:
                add_to_movers()
        elif new_chase:
            add_to_movers() 
        if baddie.spotter:
            if not Baddie.alert_sentinel:
                spotter_alert_call()
                baddie.spotter = False  
            if self.debug:
                self.push_to_console("spotter TU remaining: {} | spotter finished turn: {}".format(\
                    baddie.tu, baddie.finished_turn))
        if len(actions) > 0:
            take_actions()
        elif len(actions) == 0 and not baddie.is_rover():
            baddie.finished_turn = True
        finished_investigating = baddie.investigating \
            and self.tilemap.get_tile(self.player.cell_xy()) not in baddie.tiles_can_see \
            and self.alert_timer is None
        if finished_investigating: 
            baddie.investigating = False
            if self.debug:
                self.push_to_console("baddie finished investigating")

    def all_baddies(self) -> list: 
        return list(filter(lambda a: isinstance(a, Baddie), self.actors_group))

    def end_turn(self, xy=None):
        self.game.turn += 1
        self.selected_tile = None
        self.move_select_to_confirm = False
        self.move_path = None
        self.player.tu = self.player.max_tu
        self.player_turn = False
        self.redraw_switches()
        self.update_on_screen_actors()
        self.update_all_baddie_awareness()
        self.draw()
        self.activate_baddies()
        self.run_ai_behavior()
        self.redraw_switches()

    def activate_baddies(self):
        def activate(baddie):
            baddie.tu = baddie.max_tu
            baddie.finished_turn = False
        baddies = self.all_baddies() 
        apply(activate, baddies)

    def make_macguffin(self) -> Actor:
        pos = choice(list(filter(lambda t: t.tile_type == "floor" and not t.occupied and not t.door, \
            self.tilemap.all_tiles()))).xy_tuple
        macguffin = Loot(self.game.entity_sheets[self.game.terminal_sheet], CELL_SIZE, CELL_SIZE, cell_xy_tuple=pos)
        macguffin.name = "macguffin"
        nbrs = self.tilemap.neighbors_of(pos)
        oriented_to = first(lambda t: t.walkable(), nbrs)
        if oriented_to is not None:
            relative_d = relative_direction(pos, oriented_to.xy_tuple)
            macguffin.change_orientation(relative_d)
        self.tilemap.toggle_occupied(pos, True)
        return macguffin

    def make_patrol_intel_terminal(self, building_number) -> Actor:
        pos = choice(list(filter(lambda t: t.tile_type == "floor" and not t.occupied and not t.door \
            and t.building_number == building_number, self.tilemap.all_tiles()))).xy_tuple
        terminal = Loot(self.game.entity_sheets[self.game.terminal_sheet], CELL_SIZE, CELL_SIZE, cell_xy_tuple=pos)
        terminal.name = "patrol intel terminal"
        terminal.building_number = building_number
        nbrs = self.tilemap.neighbors_of(pos)
        oriented_to = first(lambda t: t.walkable(), nbrs)
        if oriented_to is not None:
            relative_d = relative_direction(pos, oriented_to.xy_tuple)
            terminal.change_orientation(relative_d)
        self.tilemap.toggle_occupied(pos, True)
        return terminal

    def make_player(self) -> Actor: 
        pos = choice(list(filter(lambda t: t.xy_tuple[1] == self.tilemap.wh_tuple[1] - 1, \
            self.tilemap.all_tiles()))).xy_tuple
        player = Player(self.game.entity_sheets[self.game.dude_1_sheet], CELL_SIZE, CELL_SIZE, cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        player.change_orientation("up")
        return player

    def make_baddie(self, building_number) -> Actor: 
        pos = choice(list(filter(lambda x: x.walkable() and not x.occupied \
            and manhattan_distance(self.player.cell_xy(), x.xy_tuple) > 20 and x.building_number == building_number \
            and not x.door, self.tilemap.all_tiles()))).xy_tuple
        baddie = Baddie(self.game.entity_sheets[self.game.dude_2_sheet], CELL_SIZE, CELL_SIZE, cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        baddie.building_number = building_number
        return baddie

    def get_topleft_cell(self):
        return (self.tilemap.camera[0] - self.screen_wh_cells_tuple[0] // 2, \
            self.tilemap.camera[1] - self.screen_wh_cells_tuple[1] // 2)

    def input_blocked(self):
        player_moving = self.player in list(map(lambda m: m.actor, self.visible_movers + self.invisible_movers))
        not_player_turn = not self.player_turn
        return player_moving or not_player_turn

    def on_screen_cells_rect(self) -> Rect:
        topleft = self.get_topleft_cell()
        return Rect((topleft[0], topleft[1], self.screen_wh_cells_tuple[0], self.screen_wh_cells_tuple[1]))

    def draw_game_over_mode(self):
        # placeholder for a more complex interaction
        if not self.game_over_mode_draw_sentinel:
            pos = (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2,
                self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
            game_over_surf = self.game.big_splash_surf.copy()
            txt = self.game.game_over_font.render("Game over!", True, "white", "black")
            tpos = (game_over_surf.get_width() // 2 - txt.get_width() // 2, 40)
            game_over_surf.blit(txt, tpos)
            self.game_over_group.draw(game_over_surf)
            self.screen.blit(game_over_surf, pos)
            pygame.display.flip()
            self.game_over_draw_sentinel = True

    def draw_win_mode(self):
        # placeholder for a more complex interaction
        if not self.win_mode_draw_sentinel:
            pos = (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2,
                self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
            win_surf = self.game.big_splash_surf.copy()
            txt = self.game.game_over_font.render("You won!", True, "white", "black")
            tpos = (win_surf.get_width() // 2 - txt.get_width() // 2, 40)
            win_surf.blit(txt, tpos)
            self.win_group.draw(win_surf)
            self.screen.blit(win_surf, pos)
            pygame.display.flip()
            self.win_mode_draw_sentinel = True

    def draw(self): 
        if self.game_over_mode:
            self.draw_game_over_mode()
            return
        elif self.win_mode:
            self.draw_win_mode()
            return
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
            enemy_los_blits = []
            patrol_path_blits = []
            for tile in self.player.tiles_can_see:
                x, y = tile.xy_tuple
                pos = ((x - topleft[0]) * CELL_SIZE, (y - topleft[1]) * CELL_SIZE)
                visible_blits.append((tile.visible_img, pos))
                dscore = self.distance_map_to_player[x][y] 
                if self.tile_in_player_move_range(dscore, tile) and self.player_turn:
                    if self.game.show_move_dscore:
                        msurf = self.game.movement_range_cell_surf.copy()
                        txt = self.game.hud_font.render("{}".format(dscore), True, "white", "black")
                        tpos = (msurf.get_width() // 2 - txt.get_width() // 2, \
                            msurf.get_height() // 2 - txt.get_height() // 2)
                        msurf.blit(txt, tpos)
                        move_range_blits.append((msurf, pos))
                    else:
                        move_range_blits.append((self.game.movement_range_cell_surf, pos))
            for tile in self.enemy_los_tiles:
                x, y = tile.xy_tuple
                pos = ((x - topleft[0]) * CELL_SIZE, (y - topleft[1]) * CELL_SIZE)
                enemy_los_blits.append((self.game.enemy_los_cell_surf, pos))
            self.on_screen_map_surface.blits(visible_blits)
            self.on_screen_map_surface.blits(move_range_blits)
            self.on_screen_map_surface.blits(enemy_los_blits)
            tagged_baddies = self.tagged_baddie_movers()
            for mover in tagged_baddies:
                last = None
                index = 0
                for xy in mover.path: 
                    if last is None:
                        last = relative_direction(mover.actor.cell_xy(), xy)
                    else:
                        last = relative_direction(mover.path[index - 1], xy)
                    if last == "wait" and self.debug:
                        self.push_to_console("Error in patrol paths: last == 'wait'")
                        print("last == 'wait' <this should never happen>")
                        mover.actor.print_debug_info() 
                    index += 1
                    if last != "wait":
                        img = self.game.entity_sheets[self.game.patrol_path_surf]["regular"][last][0]
                        x, y = xy
                        tile = self.tilemap.get_tile(xy)
                        if self.on_screen_cells_rect().contains(Rect(x, y, 0, 0)) and tile.seen:
                            pos = ((x - topleft[0]) * CELL_SIZE, (y - topleft[1]) * CELL_SIZE)
                            if xy == mover.path[-1]:
                                patrol_path_blits.append((self.game.patrol_end_surf, pos))
                            else:
                                patrol_path_blits.append((img, pos))
            self.on_screen_map_surface.blits(patrol_path_blits)
            if self.move_path is not None:
                for xy in self.move_path:
                    x, y = xy
                    pos = (((x - topleft[0]) * CELL_SIZE) + CELL_SIZE // 2, \
                        ((y - topleft[1]) * CELL_SIZE) + CELL_SIZE // 2)
                    pygame.draw.circle(self.on_screen_map_surface, "cyan", pos, 8)
                    if self.move_path is not None and (x, y) == self.move_path[-1]:
                        dscore = self.distance_map_to_player[x][y] 
                        msurf = self.game.movement_range_cell_surf.copy()
                        pygame.draw.rect(msurf, "black", msurf.get_rect(), 2)
                        remaining = self.player.tu - (dscore * TU_MOVEMENT) 
                        txt = self.game.hud_font.render("{}".format(remaining), True, "white", "black")
                        tpos = (msurf.get_width() // 2 - txt.get_width() // 2, \
                            msurf.get_height() // 2 - txt.get_height() // 2)
                        msurf.blit(txt, tpos)
                        self.on_screen_map_surface.blit(msurf, pos)
            self.on_screen_actors_group.draw(self.on_screen_map_surface)  
            for baddie in list(filter(lambda a: isinstance(a, Baddie), self.on_screen_actors_group)):
                if baddie.can_see_player:
                    pos = ((baddie.x + CELL_SIZE // 2) - self.game.alert_base.get_width() // 2, \
                        baddie.y - self.game.alert_base.get_height())
                    self.on_screen_map_surface.blit(self.game.alert_base, pos)
                elif baddie.investigating:
                    pos = ((baddie.x + CELL_SIZE // 2) - self.game.huh_base.get_width() // 2, \
                        baddie.y - self.game.huh_base.get_height())
                    self.on_screen_map_surface.blit(self.game.huh_base, pos)
            for action in self.player.actions_available:
                name = action[0]
                if name == "interact":
                    loot = action[1]
                    self.on_screen_map_surface.blit(self.game.loot_base, (loot.x, loot.y))
            self.screen.blit(self.on_screen_map_surface, (0, 0))
        if self.redraw_side_hud:
            def draw_dynamic_hud_surf(msg, y, fg="white", bg="black"):
                surf = self.game.hud_font.render(msg, True, fg, bg)
                base = pygame.Surface((SIDE_HUD_WIDTH, surf.get_height() + 2))
                base.fill(bg)
                pygame.draw.rect(base, "magenta", base.get_rect(), 1)
                base.blit(surf, (base.get_width() // 2 - surf.get_width() // 2, 1))
                self.side_hud.blit(base, (0, y))
            x = self.screen.get_width() - SIDE_HUD_WIDTH
            self.side_hud_group.draw(self.side_hud)
            draw_mm_view_rect()
            draw_dynamic_hud_surf("Turn: {}".format(self.game.turn), TURN_Y)
            draw_dynamic_hud_surf("TU: {} / {}".format(self.player.tu, self.player.max_tu), TU_REMAINING_Y)
            if self.alert_timer is None:
                alert_txt = "No Alert"
                draw_dynamic_hud_surf(alert_txt, ALERT_Y, fg="white", bg=(0, 120, 0))
            else:
                alert_txt = "Alert! Turns Remaining: {}".format(self.alert_timer)
                draw_dynamic_hud_surf(alert_txt, ALERT_Y, fg="white", bg=COLOR_HUD_RED)
            if self.debug:
                draw_dynamic_hud_surf("FPS: {}".format(int(self.game.clock.get_fps())), self.screen.get_height() - 50)
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
        if not self.player_turn:
            pos = ((self.screen.get_width() - (SIDE_HUD_WIDTH // 2)) - self.game.processing_surf.get_width() // 2, \
                MINI_MAP_SIZE[1] // 2 - self.game.processing_surf.get_height() // 2)
            self.screen.blit(self.game.processing_surf, pos)
        if self.redraw_map or self.redraw_side_hud or self.redraw_console:
            pygame.display.flip()
        if self.redraw_map:
            self.redraw_map = False
        if self.redraw_side_hud:
            self.redraw_side_hud = False
        if self.redraw_console:
            self.redraw_console = False

    def push_to_console_if_player(self, msg, actors, tag=None):
        if any(filter(lambda x: x.player, actors)):
            self.console.push(Message(msg, self.game.turn, tag))
            self.redraw_console = True

    def push_to_console(self, msg, tag=None):
        self.console.push(Message(msg, self.game.turn, tag))
        self.redraw_console = True

    def alert_update(self):
        if self.alert_timer is not None:
            num_can_see_player = len(list(filter(lambda b: b.can_see_player, self.all_baddies())))
            if num_can_see_player == 0:
                self.alert_timer -= 1
                if self.alert_timer == 0:
                    self.alert_timer = None
                    self.alert_zone_rect = None
                    alerted_baddies = list(filter(lambda b: b.alert_rover, self.all_baddies()))
                    for baddie in alerted_baddies:
                        baddie.un_rover() 
            else:
                self.alert_timer = 10

    def tagged_baddie_movers(self):
        return list(filter(lambda m: isinstance(m.actor, Baddie) \
            and m.actor.building_number in self.player.building_patrol_intels, \
            self.visible_movers + self.invisible_movers))

    def update_baddie_los_tiles(self, baddie):
        for tile in baddie.tiles_can_see:
            if tile.seen \
                and tile not in self.enemy_los_tiles \
                and tile.walkable() \
                and self.tilemap.get_tile(baddie.cell_xy()) in self.player.tiles_can_see:
                self.enemy_los_tiles.append(tile)

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
            elif pygame.key.get_pressed()[K_e]:
                self.end_turn()
            elif pygame.key.get_pressed()[K_c]:
                self.tilemap.camera = self.player.cell_xy()
                self.redraw_switches()
            elif pygame.key.get_pressed()[K_SLASH] and self.shift_pressed():
                self.console.push_controls()
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

        def handle_left_click_game_over_mode(): 
            x, y = pygame.mouse.get_pos()
            for entity in self.game_over_group: # clickables are offset 
                if isinstance(entity, Clickable): 
                    x2 = x - (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2)
                    y2 = y - (self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
                    if entity.clicked((x2, y2)):
                        entity.effect((x2, y2))
                        return

        def handle_left_click_win_mode(): 
            x, y = pygame.mouse.get_pos()
            for entity in self.win_group: # clickables are offset 
                if isinstance(entity, Clickable): 
                    x2 = x - (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2)
                    y2 = y - (self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
                    if entity.clicked((x2, y2)):
                        entity.effect((x2, y2))
                        return

        def handle_left_click():
            if self.game_over_mode:
                handle_left_click_game_over_mode()
                return
            elif self.win_mode:
                handle_left_click_win_mode()
                return
            x, y = pygame.mouse.get_pos()
            tile_clicked_xy = tile_clicked((x, y))
            for entity in self.side_hud_group: # clickables are offset 
                if isinstance(entity, Clickable):
                    x2 = x - (self.screen.get_width() - SIDE_HUD_WIDTH)
                    if entity.clicked((x2, y)):
                        entity.effect((x2, y))
                        return
            if tile_clicked_xy is not None:
                tile = self.tilemap.get_tile(tile_clicked_xy)
                tx, ty = tile_clicked_xy
                interact_action_clickable = first(lambda a: a[1].clicked((x, y)) \
                    and a[0] == "interact", self.player.actions_available) 
                if not self.move_select_to_confirm and not tile.occupied:
                    score = self.distance_map_to_player[tx][ty] 
                    if self.tile_in_player_move_range(score, tile):
                        self.selected_tile = tile_clicked_xy
                        self.move_select_to_confirm = True
                        path = self.shortest_path(tile_clicked_xy, self.player.cell_xy(), \
                            pre_dmap=self.distance_map_to_player, reverse=True) 
                        if path is None:  
                            print("Error! No path to click! <this should never happen>")
                            quit()
                        elif path is not None:
                            self.move_path = path
                        self.redraw_switches()
                elif self.move_select_to_confirm and tile_clicked_xy == self.selected_tile:
                    self.tilemap.camera = self.move_path[-1]
                    self.visible_movers.append(Mover(self.player, [xy for xy in self.move_path]))
                    self.selected_tile = None
                    self.move_path = None
                    self.move_select_to_confirm = False
                    self.redraw_switches()
                elif interact_action_clickable is not None:
                    self.actor_interact(self.player, interact_action_clickable[1])
                    self.redraw_switches()
                else:
                    self.move_path = None
                    self.selected_tile = None
                    self.move_select_to_confirm = False
                    self.redraw_switches()

        def handle_middle_click():
            x, y = pygame.mouse.get_pos()
            tile_clicked_xy = tile_clicked((x, y))
            if tile_clicked_xy is not None:
                self.tilemap.camera = tile_clicked_xy
                self.redraw_switches()

        def handle_right_click():
            x, y = pygame.mouse.get_pos()
            tile_clicked_xy = tile_clicked((x, y))
            if tile_clicked_xy is not None \
                and chebyshev_distance(tile_clicked_xy, self.player.cell_xy()) == 1:
                cost = TU_TURN
                if self.player.tu >= cost:
                    self.player.change_orientation(relative_direction(self.player.cell_xy(), tile_clicked_xy))
                    self.player.tu -= cost
                    self.actor_update_fov(self.player)
                    self.distance_map_to_player = self.dmap_to_player(bounded=True)
                    self.redraw_switches()

        def handle_mouse_clicks():
            if pygame.mouse.get_pressed()[0]:
                handle_left_click()
            elif pygame.mouse.get_pressed()[1]:
                handle_middle_click()
            elif pygame.mouse.get_pressed()[2]:
                handle_right_click()

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

        def handle_movers(event_type):  
            if event_type == self.game.VISIBLE_MOVER_CHECK:
                movers = self.visible_movers
            elif event_type == self.game.INVISIBLE_MOVER_CHECK:
                movers = self.invisible_movers
            mover = first(lambda m: m.actor.player or not m.actor.finished_turn, movers)
            def baddie_blocked(m):
                if isinstance(m.actor, Baddie):
                    occupied = self.tilemap.get_tile(to_xy).occupied
                    baddie_surrounded = all(map(lambda t: not t.walkable() or t.occupied, \
                        self.tilemap.neighbors_of(m.actor.cell_xy())))
                    if baddie_surrounded:
                        m.actor.patrol_path = None
                        m.actor.finished_turn = True
                        if m in movers:
                            movers.remove(m)
                        if self.debug:
                            self.push_to_console("baddie surrounded")
                        return True
                    elif occupied: 
                        if m in movers:
                            movers.remove(m)
                        m.actor.patrol_path = None
                        self.actor_ai_baddie(m.actor)
                        if self.debug:
                            self.push_to_console("baddie re-routed")
                        return True
                    return False
            def move_cost(orientation) -> int:
                if orientation in ["upright", "downright", "downleft", "upleft"]:
                    return TU_MOVEMENT * 2
                elif orientation == "wait":
                    return 0
                else:
                    return TU_MOVEMENT
            def baddie_hook(m):
                if isinstance(m.actor, Baddie):
                    if m.actor.tu < TU_CHEAPEST:
                        m.actor.finished_turn = True
                    else:
                        self.actor_ai_baddie(m.actor) 
            def player_hook(m):
                if isinstance(m.actor, Player):
                    xy = self.player.cell_xy()
                    self.distance_map_to_player = self.dmap_to_player(bounded=True)
                    self.player.actions_available = self.actor_possible_actions(self.player)
            if mover is not None:
                if not mover.actor.player and self.player_turn:
                    return
                from_xy = mover.actor.cell_xy()
                to_xy = mover.path[0]
                if baddie_blocked(mover):
                    return
                new_orientation = self.relative_direction(from_xy, to_xy)
                cost = move_cost(new_orientation)
                if cost > mover.actor.tu:
                    if isinstance(mover.actor, Baddie):
                        mover.actor.finished_turn = True
                else:
                    mover.actor.tu -= cost
                    mover.actor.change_orientation(new_orientation)
                    mover.actor.update_frame()
                    mover.actor.cell_x, mover.actor.cell_y = to_xy
                    mover.path = mover.path[1:]
                    self.tilemap.toggle_occupied(from_xy, False)
                    self.tilemap.toggle_occupied(to_xy, True)
                    self.actor_update_fov(mover.actor) 
                    self.redraw_switches()
                    if mover.goal_reached(): 
                        self.remove_from_movers(mover.actor)
                        if self.debug:
                            self.push_to_console("mover reaches goal")
                    baddie_hook(mover)
                    player_hook(mover)
                if event_type == self.game.VISIBLE_MOVER_CHECK:
                    self.visible_movers = movers
                elif event_type == self.game.INVISIBLE_MOVER_CHECK:
                    self.invisible_movers = movers
                self.update_all_baddie_awareness()
                self.update_on_screen_actors()

        def player_turn_ready() -> bool:
            for baddie in self.all_baddies():
                if not baddie.finished_turn:
                    if self.debug:
                        hangers = self.hanging_baddies()
                        print("Baddies with unfinished turns: {}".format(len(hangers)))
                    return False
            self.player.actions_available = self.actor_possible_actions(self.player)
            self.distance_map_to_player = self.dmap_to_player(bounded=True)
            self.alert_update()
            self.game_over_check()
            self.redraw_switches()
            return True

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
            elif event.type == self.game.VISIBLE_MOVER_CHECK or event.type == self.game.INVISIBLE_MOVER_CHECK:
                handle_movers(event.type)
            # end baddie turns / start player turn
            elif event.type == self.game.PLAYER_TURN_READY_CHECK and not self.player_turn:
                self.player_turn = player_turn_ready()
        pygame.event.pump() 

    def hanging_baddies(self) -> list:
        return list(filter(lambda b: not b.finished_turn, self.all_baddies()))

    def game_over_check(self):
        if self.player.knocked_out or self.player.dead:
            self.game_over_mode = True

    def new_alert_zone_rect(self, origin_xy) -> tuple:
        x, y = origin_xy
        return (x - ALERT_ZONE_D, y - ALERT_ZONE_D, ALERT_ZONE_D * 2 + 1, ALERT_ZONE_D * 2 + 1)

    def begin_alert(self) -> bool:
        if not Baddie.alert_sentinel:
            Baddie.alert_sentinel = True
            self.push_to_console("Alert! Stay out of sight to reduce the timer.")
            self.alert_timer = 10
            self.update_all_baddie_awareness()
            x, y = self.player.cell_xy()
            self.alert_zone_rect = self.new_alert_zone_rect((x, y))
            r = Rect(self.alert_zone_rect)
            baddies_alerted = list(filter(lambda b: r.contains(Rect(b.cell_x, b.cell_y, 0, 0)), self.all_baddies()))
            for baddie in baddies_alerted:
                if not baddie.can_see_player and not baddie.spotter:
                    baddie.investigating = True
                    baddie.patrol_path = None
                    self.remove_from_movers(baddie)
                    self.actor_ai_baddie(baddie) 
                baddie.un_rover() 
                if Baddie.num_alert_rovers < NUM_ALERT_ROVERS:
                    baddie.set_alert_rover()
            return True
        return False

    def remove_from_movers(self, actor):
        visible_mover = first(lambda m: m.actor is actor, self.visible_movers)
        invisible_mover = first(lambda m: m.actor is actor, self.invisible_movers)
        if visible_mover is not None and visible_mover in self.visible_movers:
            self.visible_movers.remove(visible_mover)
        elif invisible_mover is not None and invisible_mover in self.invisible_movers:
            self.invisible_movers.remove(invisible_mover)

    def update_all_baddie_awareness(self): 
        def spot(baddie):
            self.remove_from_movers(baddie)
            baddie.can_see_player = True
            baddie.investigating = False
            baddie.patrol_path = self.shortest_path(baddie.cell_xy(), self.player.cell_xy(), \
                pre_dmap=self.distance_map_to_player) 
            baddie.spotter = True
            self.actor_ai_baddie(baddie, new_chase=True)
            if self.debug:
                self.push_to_console("baddie chasing player")
        for baddie in self.all_baddies():
            can_see_player = self.tilemap.get_tile(self.player.cell_xy()) in baddie.tiles_can_see
            if can_see_player and not baddie.can_see_player:
                spot(baddie)
            elif not can_see_player and baddie.can_see_player and not baddie.investigating:
                baddie.can_see_player = False
                baddie.investigating = True
                if self.debug:
                    self.push_to_console("baddie investigating")
            elif baddie.can_see_player and self.player_turn:
                spot(baddie)
            baddie.can_see_player = can_see_player

    def update_on_screen_actors(self):
        invisible = []
        visible = []
        self.on_screen_actors_group.empty()
        topleft = self.get_topleft_cell()
        def actor_visible(actor) -> bool:
            if actor.on_screen(topleft, self.screen_wh_cells_tuple) or self.debug:
                if self.tilemap.get_tile(actor.cell_xy()) in self.player.tiles_can_see or self.debug:
                    return True
                elif (self.tilemap.get_tile(actor.cell_xy()).seen and isinstance(actor, Loot)) or self.debug:
                    return True
            return False
        for actor in self.actors_group:
            if actor_visible(actor):
                actor.x = (actor.cell_x - topleft[0]) * CELL_SIZE
                actor.y = (actor.cell_y - topleft[1]) * CELL_SIZE
                actor.rect = Rect(actor.x, actor.y, actor.width, actor.height) 
                self.on_screen_actors_group.add(actor)
        for mover in self.invisible_movers + self.visible_movers:
            if mover.actor.on_screen(topleft, self.screen_wh_cells_tuple) \
                and self.tilemap.get_tile(mover.actor.cell_xy()) in self.player.tiles_can_see:
                visible.append(mover)
            elif self.debug:
                visible.append(mover)
            else:
                invisible.append(mover)
        self.invisible_movers = invisible
        self.visible_movers = visible
        self.enemy_los_tiles = []
        for baddie in self.all_baddies():
            self.update_baddie_los_tiles(baddie)
        self.do_update_on_screen_actors = False

    def update_player_visible_baddies(self):
        visible_baddies = list(filter(lambda b: self.tilemap.get_tile(b.cell_xy()) in self.player.tiles_can_see,
            self.all_baddies()))
        new_baddie_spotted = False
        for baddie in visible_baddies:
            if baddie not in self.player.visible_baddies:
                new_baddie_spotted = True
                break
        if new_baddie_spotted:
            self.push_to_console("Baddie spotted!")
            self.distance_map_to_player = self.dmap_to_player(bounded=True)
            self.remove_from_movers(self.player)
            self.update_all_baddie_awareness()
            self.redraw_switches()
        self.player.visible_baddies = visible_baddies

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

    def djikstra_map_distance_to(self, from_xy, to_xy, bounding_rect=None) -> list: # or None
        w, h = self.tilemap.wh_tuple
        if bounding_rect is not None:
            bx, by, bw, bh = bounding_rect 
        dmap = [[INVALID_DJIKSTRA_SCORE for _ in range(h)] for _ in range(w)]
        dmap[to_xy[0]][to_xy[1]] = 0
        def loc(node):
            return node[2]
        def score(node):
            return node[0]
        def is_start_or_end(xy) -> bool:
            return xy == from_xy or xy == to_xy
        def blocked(tile) -> bool:
            return tile.occupied and not is_start_or_end(tile.xy_tuple)
        diagonals = ["upleft", "downleft", "upright", "downright"]
        seen_bools = [[False for _ in range(h)] for _ in range(w)]
        seen_bools[to_xy[0]][to_xy[1]] = True
        seen = []
        entry_count = 1
        start_node = [0, 0, to_xy]
        heapq.heappush(seen, start_node)
        while len(seen) > 0:
            node = heapq.heappop(seen)
            nbrs = self.tilemap.neighbors_of(loc(node))
            if bounding_rect is not None:
                nbrs = list(filter(lambda t: t.xy_tuple[0] >= bx and t.xy_tuple[1] >= by \
                    and t.xy_tuple[0] < bx + bw and t.xy_tuple[1] < by + bh, nbrs))
            for nbr in nbrs:
                x, y = nbr.xy_tuple
                if not seen_bools[x][y] and nbr.walkable() and not blocked(nbr):
                    if self.relative_direction(loc(node), (x, y)) in diagonals:
                        nbr_score = score(node) + 2
                    else:
                        nbr_score = score(node) + 1
                    new_node = [nbr_score, entry_count, nbr.xy_tuple]
                    heapq.heappush(seen, new_node)
                    seen_bools[x][y] = True
                    entry_count += 1
                    dmap[x][y] = nbr_score
                elif not nbr.walkable() or blocked(nbr):
                    dmap[x][y] = INVALID_DJIKSTRA_SCORE
        x, y = from_xy
        if not seen_bools[x][y] and from_xy != to_xy:
            return None
        return dmap

    def shortest_path(self, from_xy, to_xy, no_from_in_traceback=True, bounding_rect=None, pre_dmap=None, \
        reverse=False) -> list: # or None
        if pre_dmap is not None:
            dmap = pre_dmap
        else:
            dmap = self.djikstra_map_distance_to(from_xy, to_xy, bounding_rect=bounding_rect)
        w, h = self.tilemap.wh_tuple
        def sort_key(tile):
            return dmap[tile.xy_tuple[0]][tile.xy_tuple[1]]
        def dscore(tile) -> int:
            return dmap[tile.xy_tuple[0]][tile.xy_tuple[1]]
        if dmap is None:
            return None
        via = {}
        current = self.tilemap.get_tile(from_xy) 
        def goal_reached() -> bool:
            return current.xy_tuple == to_xy
        def start_reached() -> bool:
            return current.xy_tuple == from_xy
        seen = []
        seen_bools = [[False for _ in range(h)] for _ in range(w)]
        seen_bools[from_xy[0]][from_xy[1]] = True
        def tile_seen(tile) -> bool:
            return seen_bools[tile.xy_tuple[0]][tile.xy_tuple[1]]
        def all_neighbors_seen(tile) -> bool:
            return all(map(lambda t: seen_bools[t.xy_tuple[0]][t.xy_tuple[1]], self.tilemap.neighbors_of(tile.xy_tuple)))
        def get_traceback() -> list:
            nonlocal current
            traceback = [current.xy_tuple]
            while not start_reached():
                next_via = via[current]
                traceback.append(next_via.xy_tuple)
                current = next_via
            if not reverse:
                traceback.reverse()
            if no_from_in_traceback:
                traceback = traceback[1:]
            return traceback
        origin_score = dmap[from_xy[0]][from_xy[1]]
        entry_count = 1
        origin = [origin_score, 0, current]
        heapq.heappush(seen, origin)
        while len(seen) > 0 and not goal_reached():
            nbrs = list(filter(lambda t: dscore(t) < INVALID_DJIKSTRA_SCORE, \
                self.tilemap.neighbors_of(current.xy_tuple)))
            for nbr in nbrs:
                if not tile_seen(nbr):
                    x, y = nbr.xy_tuple
                    seen_bools[x][y] = True
                    node = [dscore(nbr), entry_count, nbr]
                    heapq.heappush(seen, node)
                    entry_count += 1
                    via[nbr] = current 
            if len(nbrs) == 0:
                next_origin = heapq.heappop(seen)[2]
                if not all_neighbors_seen(next_origin):
                    current = next_origin
            else:
                nbrs.sort(key=sort_key) 
                shortest = nbrs[0] 
                if dscore(shortest) >= dscore(current):
                    next_origin = heapq.heappop(seen)[2]
                    if not all_neighbors_seen(next_origin):
                        current = next_origin
                else:
                    current = shortest
        if goal_reached():
            return get_traceback()
        else:
            return None
        
