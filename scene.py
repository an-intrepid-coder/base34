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
        self.game = game
        self.debug = game.debug
        self.debug_fov_triggered = False
        self.screen = game.screen
        self.screen_wh_cells_tuple = game.screen_wh_cells_tuple
        self.tilemap = None
        self.console = Console(CONSOLE_HEIGHT // HUD_FONT_SIZE)
        if self.debug:
            pygame.time.set_timer(self.game.VISIBLE_MOVER_CHECK, MOVER_TICK_MS_INVISIBLE)
        else:
            pygame.time.set_timer(self.game.VISIBLE_MOVER_CHECK, MOVER_TICK_MS_VISIBLE)
        pygame.time.set_timer(self.game.INVISIBLE_MOVER_CHECK, MOVER_TICK_MS_INVISIBLE)
        pygame.time.set_timer(self.game.PLAYER_TURN_READY_CHECK, PLAYER_TURN_READY_TICK_MS)
        self.tilemap = TileMap(self, MAP_SIZE)
        # Side Hud surface
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
        self.inventory_group = Group()
        self.loot_group = Group()
        self.smoke_group = Group()
        self.smoke_redraw_ticker = 0
        self.smoke_redraw_ticker_limit = 4
        self.unresponsive_group = Group()
        def try_again_effect(xy_tuple):
            self.reset_scenario()
        def exit_game_effect(xy_tuple):
            self.game.running = False
        # "try again" game over mode button
        try_again_img = self.game.game_over_button_surf.copy()
        try_again_txt = self.game.title_font.render("Try Again?", True, "white", "black")
        ta_txt_pos = (try_again_img.get_width() // 2 - try_again_txt.get_width() // 2, \
            try_again_img.get_height() // 2 - try_again_txt.get_height() // 2)
        try_again_img.blit(try_again_txt, ta_txt_pos)
        ta_pos = (10, self.game.big_splash_surf.get_height() - try_again_img.get_height() - 10)
        self.game_over_group.add(Clickable(try_again_img, try_again_img.get_width(), try_again_img.get_height(), \
            try_again_effect, ta_pos))
        # "exit game" button
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
        # inventory slots
        self.inventory_slots = []
        self.inventory_page = 0
        self.inventory_slots_per_page = 17
        self.dynamic_slot_start = 28
        for i in range(self.inventory_slots_per_page):
            pos = (self.game.big_splash_surf.get_width() // 2 - self.game.slot_surf.get_width() // 2, \
                self.dynamic_slot_start + (i * self.game.slot_surf.get_height()))
            self.inventory_slots.append(InventorySlot(self.game.slot_surf, self.game.slot_surf.get_width(), \
                self.game.slot_surf.get_height(), i, xy_tuple=pos)) 
        self.inventory_group.add(self.inventory_slots) 
        # page back button
        page_back_img = self.game.game_over_button_surf.copy()
        page_back_txt = self.game.title_font.render("Page <<", True, "white", "black")
        pb_txt_pos = (page_back_img.get_width() // 2 - page_back_txt.get_width() // 2, \
            page_back_img.get_height() // 2 - page_back_txt.get_height() // 2)
        page_back_img.blit(page_back_txt, pb_txt_pos)
        pb_pos = (10, self.game.big_splash_surf.get_height() - page_back_img.get_height() - 10)
        def page_back_effect(xy_tuple): 
            self.inventory_page -= 1
            if self.inventory_page < 0:
                self.inventory_page = 0
            self.redraw_inventory_mode = True
        self.inventory_group.add(Clickable(page_back_img, page_back_img.get_width(), page_back_img.get_height(), \
            page_back_effect, pb_pos))
        # page forward button
        page_forward_img = self.game.game_over_button_surf.copy()
        page_forward_txt = self.game.title_font.render("Page >>", True, "white", "black")
        pf_txt_pos = (page_forward_img.get_width() // 2 - page_forward_txt.get_width() // 2, \
            page_forward_img.get_height() // 2 - page_forward_txt.get_height() // 2)
        page_forward_img.blit(page_forward_txt, pf_txt_pos)
        pf_pos = (20 + page_back_img.get_width(), \
            self.game.big_splash_surf.get_height() - page_forward_img.get_height() - 10)
        def page_forward_effect(xy_tuple): 
            self.inventory_page += 1
            self.redraw_inventory_mode = True
        self.inventory_group.add(Clickable(page_forward_img, page_forward_img.get_width(), \
            page_forward_img.get_height(), page_forward_effect, pf_pos))
        # exit inventory button
        inventory_exit_img = self.game.game_over_button_surf.copy()
        inventory_exit_txt = self.game.title_font.render("Exit", True, "white", "black")
        ie_txt_pos = (inventory_exit_img.get_width() // 2 - inventory_exit_txt.get_width() // 2, \
            inventory_exit_img.get_height() // 2 - inventory_exit_txt.get_height() // 2)
        inventory_exit_img.blit(inventory_exit_txt, ie_txt_pos)
        ie_pos = (self.game.big_splash_surf.get_width() - 10 - inventory_exit_img.get_width(),
            self.game.big_splash_surf.get_height() - inventory_exit_img.get_height() - 10)
        def inventory_exit_effect(xy_tuple): 
            self.inventory_mode = False
            self.inventory_page = 0
            self.redraw_switches()
        self.inventory_group.add(Clickable(inventory_exit_img, inventory_exit_img.get_width(), \
            inventory_exit_img.get_height(), inventory_exit_effect, ie_pos))
        # mini map clickable
        def mini_map_effect(xy_tuple):
            mm_cell_size = MINI_MAP_SIZE[0] / MAP_SIZE[0] 
            x, y = tuple(map(lambda z: z // mm_cell_size, xy_tuple))
            self.tilemap.camera = (x, y)
            self.redraw_switches(rconsole=False)
        self.mini_map = Clickable(self.tilemap.mini_map_surface, MINI_MAP_SIZE[0], \
            MINI_MAP_SIZE[1], mini_map_effect, (0, 0))
        # inventory button
        def inventory_button_effect(xy_tuple):
            self.inventory_mode = True
            self.redraw_inventory_mode = True
        inventory_button = Clickable(self.game.inventory_surf, self.game.inventory_surf.get_width(), \
            self.game.inventory_surf.get_height(), inventory_button_effect, (0, INVENTORY_Y))
        # end turn button
        end_turn_button = Clickable(self.game.end_turn_surf, self.game.end_turn_surf.get_width(), \
            self.game.end_turn_surf.get_height(), self.end_turn, (0, END_TURN_BUTTON_Y))
        self.side_hud_group.add([self.mini_map, end_turn_button, inventory_button]) 
        self.actors_group = Group() 
        self.on_screen_actors_group = Group()
        self.on_screen_smoke_group = Group()
        self.on_screen_loot_group = Group()
        self.on_screen_unresponsive_group = Group()
        self.on_screen_map_surface = pygame.Surface((self.screen_wh_cells_tuple[0] * CELL_SIZE, \
            self.screen_wh_cells_tuple[1] * CELL_SIZE), flags=SRCALPHA)
        self.player = self.make_player() 
        self.distance_map_to_player = self.dmap_to_player()
        self.update_player_fov()
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
        self.inventory_mode = False
        self.redraw_inventory_mode = False
        self.throwing_mode = False
        self.throwing_item = None
        self.animation_lock = False
        self.mover_lock = False
        self.baddies_thumped = 0
        self.baddies_killed = 0
        self.times_alerted = 0
        self.times_shot = 0
        self.times_shot_at = 0
        # NOTE: ^-- These only apply to current run after reset
        self.times_restarted = 0
        self.generate_scenario()

    def stats_lines(self):
        return [
            self.game.hud_font.render("Total Turns: {}".format(self.game.turn), True, "white"),
            self.game.hud_font.render("Total Baddies: {}".format(len(self.all_baddies())), True, "white"),
            self.game.hud_font.render("# KOs against Baddies: {}".format(self.baddies_thumped), True, "white"),
            self.game.hud_font.render("Baddies Killed: {}".format(self.baddies_killed), True, "white"),
            self.game.hud_font.render("Alerts Caused: {}".format(self.times_alerted), True, "white"),
            self.game.hud_font.render("Times Shot: {}".format(self.times_shot), True, "white"),
            self.game.hud_font.render("Times Shot At: {}".format(self.times_shot_at), True, "white"),
            self.game.hud_font.render("# Scenario Restarts: {}".format(self.times_restarted), True, "white"),
        ]

    def reset_stats(self):
        self.baddies_thumped = 0
        self.baddies_killed = 0
        self.times_alerted = 0
        self.times_shot = 0
        self.times_shot_at = 0

    def handle_item_clicks(self, index):
        def refresh_with_msg(msg):
            self.redraw_console = True
            self.redraw_side_hud = True
            self.push_to_console(msg)
            self.draw(inventory_refresh=True)
        real_index = index + self.inventory_page * len(self.inventory_slots)
        if real_index < len(self.player.inventory):
            item = self.player.inventory[real_index]
            if isinstance(item, Weapon):
                if self.ctrl_pressed() and item.name != "knife":
                    ammo = first(lambda i: isinstance(i, Ammo) and i.ammo_type == item.ammo_type, self.player.inventory)
                    can_reload = item.ammo < item.ammo_capacity and ammo is not None and self.player.tu >= TU_RELOAD
                    if can_reload:
                        needs = item.ammo_capacity - item.ammo
                        gets = min(needs, ammo.num_stacked)
                        item.ammo += gets
                        ammo.num_stacked -= gets
                        self.player.tu -= TU_RELOAD
                        refresh_with_msg("Reloaded {}.".format(item.name))
                    elif ammo is None:
                        refresh_with_msg("No ammo!")
                    elif self.player.tu < TU_RELOAD:
                        refresh_with_msg("Reloading requires {} TU!".format(TU_RELOAD))
                else:
                    can_equip = self.player.tu >= TU_EQUIP
                    if not item.equipped and self.player.equipped_weapon is None and can_equip:
                        item.equipped = True 
                        self.player.equipped_weapon = item
                        self.arm_player_with(item.weapon_sheet_type)
                        self.player.tu -= TU_EQUIP
                        refresh_with_msg("Equipped {}.".format(item.name))
                    elif item.equipped and can_equip:
                        item.equipped = False
                        self.player.equipped_weapon = None
                        self.arm_player_with(None)
                        self.player.tu -= TU_EQUIP
                        refresh_with_msg("Unequipped {}.".format(item.name))
                    elif not can_equip:
                        refresh_with_msg("Equip/Unequip requires {} TU!".format(TU_EQUIP))
            elif isinstance(item, Armor):
                can_equip = self.player.tu >= TU_EQUIP
                if not item.equipped and self.player.equipped_armor is None and can_equip:
                    item.equipped = True
                    self.player.equipped_armor = item
                    self.player.tu -= TU_EQUIP
                    if item.num_stacked > 1:
                        reserve = item.num_stacked - 1
                        item.num_stacked = 1
                        armor = Armor(self.game.entity_sheets[self.game.armor_sheet], CELL_SIZE, CELL_SIZE, \
                            "body armor", cell_xy_tuple=(0, 0))
                        armor.num_stacked = reserve
                        self.player.inventory.append(armor)
                    refresh_with_msg("Equipped {}.".format(item.name))
                elif item.equipped and can_equip:
                    item.equipped = False
                    self.player.equipped_armor = None
                    self.player.tu -= TU_EQUIP
                    refresh_with_msg("Unequipped {}.".format(item.name))
                elif not can_equip:
                    refresh_with_msg("Equip/Unequip requires {} TU!".format(TU_EQUIP))
            elif isinstance(item, Headgear):
                can_equip = self.player.tu >= TU_EQUIP
                if not item.equipped and self.player.equipped_headgear is None and can_equip:
                    item.equipped = True
                    self.player.equipped_headgear = item
                    self.player.tu -= TU_EQUIP
                    refresh_with_msg("Equipped {}.".format(item.name))
                    self.update_player_fov()
                elif item.equipped and can_equip:
                    item.equipped = False
                    self.player.equipped_headgear = None
                    self.player.tu -= TU_EQUIP
                    refresh_with_msg("Unequipped {}.".format(item.name))
                elif not can_equip:
                    refresh_with_msg("Equip/Unequip requires {} TU!".format(TU_EQUIP))
            elif isinstance(item, Throwable):
                can_throw = self.player.tu >= TU_THROW
                if can_throw:
                    self.throwing_mode = True
                    self.throwing_item = item
                    self.inventory_mode = False
                    msg = "Throwing {} (right-click to cancel)".format(item.name)
                    if item.name == "frag grenade":
                        msg += " (blast radius is {})".format(FRAG_RADIUS)
                    elif item.name == "smoke grenade":
                        msg += " (smoke radius is {})".format(SMOKE_RADIUS)
                    if item.name == "sensor disc":
                        msg += " (sensor disc vision radius is {})".format(SENSOR_DISC_RADIUS)
                    self.push_to_console(msg)
                    self.redraw_switches()
                elif not can_throw:
                    refresh_with_msg("Throwing requires {} TU!".format(TU_THROW))
            elif isinstance(item, Consumable):
                item.num_stacked -= 1
                if item.name == "speed stim":
                    self.player.tu = self.player.max_tu
                    refresh_with_msg("You feel a rush of energy! (TU restored)")
            if not self.throwing_mode:
                self.player.sort_inventory()
                self.player.actions_available = self.actor_possible_actions(self.player)
                self.redraw_inventory_mode = True

    def reset_scenario(self):
        self.push_to_console("Resetting scenario...")
        self.tilemap.reset()
        self.reset_stats()
        self.times_restarted += 1
        self.mini_map.image = self.tilemap.mini_map_surface
        self.game_over_mode = False
        self.debug_fov_triggered = False
        self.throwing_mode = False
        self.throwing_item = None
        self.animation_lock = False
        self.draw()
        self.actors_group.empty() 
        self.smoke_group.empty()
        self.on_screen_smoke_group.empty()
        self.unresponsive_group.empty()
        self.on_screen_unresponsive_group.empty()
        self.on_screen_actors_group.empty()
        self.loot_group.empty()
        self.on_screen_loot_group.empty()
        self.player = self.make_player() 
        self.distance_map_to_player = self.dmap_to_player()
        self.update_player_fov()
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
            possible_tiles = list(filter(lambda x: x.walkable() and not x.occupied \
                and manhattan_distance(self.player.cell_xy(), x.xy_tuple) > 20 and x.building_number == building \
                and not x.door, self.tilemap.all_tiles()))
            num_baddies = randint(2, 3) + len(possible_tiles) // 100
            for _ in range(num_baddies):
                if randint(0, 1) == 1:
                    starts_outside = True
                else:
                    starts_outside = False
                baddie = self.make_baddie(building, random_starter=starts_outside)
                baddies.append(baddie)
        shuffle(baddies)
        self.actors_group.add(baddies) 
        loading_screen(self.game.loader, "...placing loot...")
        num_armors = 6
        num_revolvers = 6
        num_pistols = 3
        num_rifles = 1
        num_knives = 1 
        num_ammos = 15
        num_grenades = 6
        num_stims = 4
        loots = [  
            self.make_360_goggles(self.nook_tile().xy_tuple),
            self.make_tracker_goggles(self.nook_tile().xy_tuple),
            self.make_sensor_disc(self.nook_tile().xy_tuple, 1),
        ]
        for _ in range(num_armors):
            loots.append(self.make_body_armor(self.nook_tile().xy_tuple))
        for _ in range(num_revolvers):
            loots.append(self.make_revolver(self.nook_tile().xy_tuple))
        for _ in range(num_pistols):
            loots.append(self.make_pistol(self.nook_tile().xy_tuple))
        for _ in range(num_rifles):
            loots.append(self.make_rifle(self.nook_tile().xy_tuple))
        for _ in range(num_knives):
            loots.append(self.make_knife(self.nook_tile().xy_tuple))
        for _ in range(num_ammos):
            loots.append(self.make_revolver_ammo(randint(1, 4), self.nook_tile().xy_tuple))
            loots.append(self.make_pistol_ammo(randint(1, 4), self.nook_tile().xy_tuple))
            loots.append(self.make_rifle_ammo(randint(1, 4), self.nook_tile().xy_tuple))
        for _ in range(num_grenades):
            loots.append(self.make_frag_grenade(self.nook_tile().xy_tuple, 1))
            loots.append(self.make_smoke_grenade(self.nook_tile().xy_tuple, randint(1, 2)))
        for _ in range(num_stims):
            loots.append(self.make_speed_stim(self.nook_tile().xy_tuple, randint(1, 2)))
        loots.append(self.make_macguffin())
        for building in self.building_numbers:
            terminal = self.make_patrol_intel_terminal(building)
            loots.append(terminal)
        self.loot_group.add(loots) # more loot to come
        loading_screen(self.game.loader, "...issuing orders to baddies...")
        for baddie in self.all_baddies():
            self.actor_update_fov(baddie)
        self.update_all_baddie_awareness() 
        self.run_ai_behavior() 
        self.player.actions_available = self.actor_possible_actions(self.player)
        if self.debug:
            self.update_player_fov()

    def uparm_baddie(self, baddie):
        rifle = self.make_rifle((0, 0), for_baddie=True)
        rifle.equipped = True
        rifle.ammo = 30
        baddie.inventory.append(rifle)
        baddie.equipped_weapon = rifle
        self.arm_baddie_with(baddie, "longarm")
        if self.debug:
            self.push_to_console("baddie uparmed with: {}".format(baddie.equipped_weapon.name))

    def nook_tile(self) -> Tile: 
        nooks = list(filter(lambda t: t.walkable() and not t.door and t.tile_type == "floor" and not t.occupied \
            and len(list(filter(lambda u: u.tile_type == "floor", self.tilemap.neighbors_of(t.xy_tuple)))) == 1,
            self.tilemap.all_tiles()))
        if len(nooks) == 0:
            return choice(list(filter(lambda t: t.tile_type == "floor" and not t.door and not t.occupied, \
                self.tilemap.all_tiles())))
        else:
            return choice(nooks)

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
            and not tile.occupied \
            and tile in self.player.tiles_can_see \
            and tile.xy_tuple != self.player.cell_xy()

    def actor_interact(self, actor, loot): 
        if loot.name == "patrol intel terminal":
            building_number = loot.building_number
            if isinstance(actor, Player) and building_number not in self.player.building_patrol_intels:
                self.player.building_patrol_intels.append(building_number)
                self.push_to_console("Found intel on baddie patrols, and a small map!")
                self.push_to_console("...mapping...")
                self.redraw_switches(rmap=False, rhud=False)
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
            self.push_to_console("You found the information which will lead you to Base 34!")
            self.push_to_console("<in the next couple of versions, additional levels will be implemented>.")
            loot.looted = True
            self.player.actions_available = self.actor_possible_actions(self.player)
            self.draw()
            self.win_mode = True
            self.redraw_switches()
        else: # put loot in inventory
            self.push_to_console("You picked up {}".format(loot.name))
            loot.looted = True
            loot.owner = self.player
            self.player.inventory.append(loot)
            if loot in self.loot_group:
                self.loot_group.remove(loot)
            self.tilemap.toggle_occupied(loot.cell_xy(), False)
            loot.cell_x, loot.cell_y = None, None
            self.player.sort_inventory()
            if isinstance(loot, Weapon):
                self.replace_weapons_with_ammo(loot) 
            self.player.actions_available = self.actor_possible_actions(self.player)
            self.distance_map_to_player = self.dmap_to_player()
            self.redraw_switches()

    def replace_weapons_with_ammo(self, loot):
        if loot.ammo_type is not None:
            similar_unlooted = list(filter(lambda b: not b.looted and isinstance(b, Weapon) \
                and b.ammo_type == loot.ammo_type, self.loot_group))
            removed = []
            for similar in similar_unlooted:
                removed.append(similar)
                xy = similar.cell_xy()
                ammo = Ammo(self.game.entity_sheets[self.game.ammo_sheet], CELL_SIZE, CELL_SIZE, loot.ammo_type, \
                    randint(1, 3), cell_xy_tuple=xy)
                self.loot_group.add(ammo)
            saved = list(filter(lambda l: l not in removed, self.loot_group))
            self.loot_group.empty()
            self.loot_group.add(saved) 

    def arm_player_with(self, weapon):
        if weapon == "knife":
            self.player.change_sheet(self.game.entity_sheets[self.game.dude_1_knife_sheet])
        elif weapon == "pistol":
            self.player.change_sheet(self.game.entity_sheets[self.game.dude_1_pistol_sheet])
        elif weapon == "longarm":
            self.player.change_sheet(self.game.entity_sheets[self.game.dude_1_longarm_sheet])
        elif weapon is None:
            self.player.change_sheet(self.game.entity_sheets[self.game.dude_1_sheet])

    def arm_baddie_with(self, baddie, weapon):
        if weapon == "knife":
            baddie.change_sheet(self.game.entity_sheets[self.game.dude_2_knife_sheet])
        elif weapon == "pistol":
            baddie.change_sheet(self.game.entity_sheets[self.game.dude_2_pistol_sheet])
        elif weapon == "longarm":
            baddie.change_sheet(self.game.entity_sheets[self.game.dude_2_longarm_sheet])
        elif weapon is None:
            baddie.change_sheet(self.game.entity_sheets[self.game.dude_2_sheet])

    def ko_baddie(self, baddie):
        baddie.change_sheet(self.game.entity_sheets[self.game.dude_2_ko_sheet])
        self.remove_from_movers(baddie)
        self.tilemap.toggle_occupied(baddie.cell_xy(), False)
        self.actors_group.remove(baddie) 
        self.unresponsive_group.add(baddie) 

    def kill_baddie(self, baddie):
        baddie.change_sheet(self.game.entity_sheets[self.game.dude_2_dead_sheet])
        self.remove_from_movers(baddie)
        self.tilemap.toggle_occupied(baddie.cell_xy(), False)
        self.actors_group.remove(baddie) 
        self.unresponsive_group.add(baddie) 

    def un_ko_baddie(self, baddie):
        baddie.change_sheet(self.game.entity_sheets[self.game.dude_2_sheet])
        baddie.knocked_out = False
        baddie.finished_turn = True 
        self.unresponsive_group.remove(baddie)
        self.actors_group.add(baddie) 
        self.tilemap.toggle_occupied(baddie.cell_xy(), True)
        self.begin_alert("baddie awakes from KO")

    def update_player_fov(self):
        sensor_disc = first(lambda l: l.name == "sensor disc" and l.owner is self.player, self.loot_group)
        self.actor_update_fov(self.player)
        if sensor_disc is not None:
            self.actor_update_fov(sensor_disc, sensor_disc=True)
            for tile in sensor_disc.tiles_can_see:
                if tile not in self.player.tiles_can_see:
                    self.player.tiles_can_see.append(tile)

    def actor_update_fov(self, actor, sensor_disc=False): 
        x, y = actor.cell_xy() 
        r = actor.fov_radius
        potentials = self.tilemap.valid_tiles_in_range_of(actor.cell_xy(), r)
        has_360_goggles = (self.player.equipped_headgear is not None \
            and self.player.equipped_headgear.name == "360 goggles" \
            and isinstance(actor, Player)) \
            or sensor_disc
        if not has_360_goggles:
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
                smoked = first(lambda s: s.cell_xy() == tile.xy_tuple, self.smoke_group) is not None
                if tile not in visible:
                    visible.append(tile)
                if (tile.blocks_vision() or smoked) and tile.xy_tuple != actor.cell_xy():
                    unblocked = False
                    break
        if self.debug and not self.debug_fov_triggered and actor.player:
            visible = self.tilemap.all_tiles()
            self.debug_fov_triggered = True
        actor.tiles_can_see = visible
        if actor.player or sensor_disc:
            for tile in visible: 
                self.reveal_tile(tile)
        if actor.player or sensor_disc:
            self.update_player_visible_baddies()
            self.tilemap.update_mini_map_surface()
            self.mini_map.image = self.tilemap.mini_map_surface

    def reveal_tile(self, tile, forced=False):
        if not tile.seen or forced:  
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
        for baddie in self.all_baddies():
            baddie.tu = baddie.max_tu
            baddie.finished_turn = False
            self.actor_ai_baddie(baddie)  
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
        if self.alert_zone_rect is None: 
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
        melee_range_actors = list(self.actors_group) + list(self.unresponsive_group)
        opponents_in_melee_range = list(filter(lambda a: a.faction != actor.faction \
            and chebyshev_distance(actor.cell_xy(), a.cell_xy()) == 1 and not a.dead, melee_range_actors))
        loot_in_range = list(filter(lambda a: isinstance(a, Loot) and chebyshev_distance(actor.cell_xy(), \
            a.cell_xy()) == 1 and not a.looted, self.loot_group))
        if actor.equipped_weapon is not None:
            if actor.equipped_weapon.name == "knife":
                opponents_in_lethal_range = list(filter(lambda a: a.faction != actor.faction \
                    and chebyshev_distance(actor.cell_xy(), a.cell_xy()) == 1 and a.can_be_killed(), \
                    self.all_actors()))
            else:
                opponents_in_lethal_range = list(filter(lambda a: a.faction != actor.faction \
                    and self.tilemap.get_tile(a.cell_xy()) in actor.tiles_can_see and a.can_be_killed(), \
                    self.all_actors()))
        else:
            opponents_in_lethal_range = []
        for opponent in opponents_in_melee_range:
            tile = self.tilemap.get_tile(opponent.cell_xy())
            if tile in actor.tiles_can_see and actor.tu >= TU_MELEE and opponent.can_be_knocked_out():
                actions.append(["melee", opponent])
            elif tile in actor.tiles_can_see and actor.tu >= TU_LETHAL and opponent.knocked_out:
                actions.append(["lethal", opponent]) 
        for loot in loot_in_range:                  
            tile = self.tilemap.get_tile(loot.cell_xy())
            if tile in actor.tiles_can_see:
                actions.append(["interact", loot])
        if actor.equipped_weapon is not None:
            for opponent in opponents_in_lethal_range:
                tile = self.tilemap.get_tile(opponent.cell_xy())
                if tile in actor.tiles_can_see and actor.tu >= TU_LETHAL and opponent.can_be_killed():
                    if actor.equipped_weapon.name == "knife":
                        actions.append(["lethal", opponent]) 
                    elif actor.equipped_weapon.ammo > 0:
                        actions.append(["lethal", opponent]) 
        return actions

    def all_actors(self) -> list:
        return list(self.actors_group) + list(self.unresponsive_group)

    def actor_take_melee_action(self, actor, action):
        target = action[1]
        if isinstance(actor, Baddie) and isinstance(target, Player) \
            and self.tilemap.get_tile(actor.cell_xy()) in self.player.tiles_can_see:
            miss = randint(0, 1) == 1
        else:
            miss = False
        if not miss:
            target.knocked_out = True
            if isinstance(target, Baddie):
                self.ko_baddie(target)
                target.ko()
            msg = "{} knocks out {} with some slick CQC!".format(actor.name, target.name)
            self.push_to_console_if_player(msg, [actor, target])
            if isinstance(actor, Player):
                self.distance_map_to_player = self.dmap_to_player()
                self.baddies_thumped += 1
            self.redraw_switches()
            actor.tu -= TU_MELEE
        else:
            self.push_to_console("You fight off an attempt to knock you out!")

    def actor_take_lethal_action(self, actor, action, silenced=False):
        target = action[1] 
        coup_de_grace = target.knocked_out and chebyshev_distance(target.cell_xy(), actor.cell_xy()) == 1
        if isinstance(actor, Baddie) and isinstance(target, Player):
            self.times_shot_at += 1
            miss = randint(0, 1) == 1
        else:
            miss = False
        if not miss:
            if isinstance(target, Player):
                self.times_shot += 1
            if target.equipped_armor is None:
                target.dead = True 
                if isinstance(target, Baddie):
                    self.kill_baddie(target)
                    target.kill()
                if coup_de_grace:
                    wep_msg = "bare hands"
                else:
                    wep_msg = actor.equipped_weapon.name
                msg = "{} kills {} with {}!".format(actor.name, target.name, wep_msg)
                self.push_to_console_if_player(msg, [actor, target])
            elif target.equipped_armor is not None:
                target.inventory.remove(target.equipped_armor)
                target.equipped_armor = None
                msg = "{} shoots {} with {} -- but the armor takes the hit (and is now useless)!".format(actor.name, \
                    target.name, actor.equipped_weapon.name)
                self.push_to_console_if_player(msg, [actor, target])
        else:
            self.push_to_console("*whizzing bullets* You're being shot at!")
        self.redraw_switches()
        actor.tu -= TU_LETHAL
        if not coup_de_grace:
            actor.equipped_weapon.ammo -= 1
        else:    
            silenced = True
        if isinstance(actor, Player):
            self.distance_map_to_player = self.dmap_to_player()
            self.baddies_killed += 1
            if not silenced:
                self.begin_alert("you used a loud weapon", player_override=True, code_red=True)

    def add_baddie_to_movers(self, baddie): 
        if baddie.cell_xy() in self.player.tiles_can_see or self.debug:
            exists = first(lambda m: m.actor is baddie, self.visible_movers)
            if exists is None:
                self.visible_movers.append(Mover(baddie, [xy for xy in baddie.patrol_path]))
        else:
            exists = first(lambda m: m.actor is baddie, self.invisible_movers)
            if exists is None:
                self.invisible_movers.append(Mover(baddie, [xy for xy in baddie.patrol_path]))

    def actor_ai_baddie(self, baddie): 
        actions = self.actor_possible_actions(baddie)
        def take_actions():  
            melee_actions = list(filter(lambda a: a[0] == "melee", actions))
            lethal_actions = list(filter(lambda a: a[0] == "lethal", actions))
            if len(lethal_actions) > 0 and baddie.tu >= TU_LETHAL:
                shuffle(lethal_actions)
                action = lethal_actions[0]
                self.animation_lock = True
                self.actor_take_lethal_action(baddie, action)
                self.handle_attack(baddie, action) 
            elif len(melee_actions) > 0 and baddie.tu >= TU_MELEE:
                shuffle(melee_actions)
                action = melee_actions[0]
                self.animation_lock = True
                self.actor_take_melee_action(baddie, action)
                self.handle_attack(baddie, action) 
        def assign_roving_status():
            def will_rove() -> bool:
                return randint(0, 1) == 1
            def will_turn() -> bool:
                return randint(1, 10) <= 3
            if will_rove():
                if Baddie.num_long_rovers < NUM_LONG_ROVERS and not baddie.alert_rover:
                    baddie.set_long_rover() 
                elif Baddie.num_local_rovers < NUM_LOCAL_ROVERS and not baddie.alert_rover:
                    baddie.set_local_rover() 
            elif will_turn() and baddie.tu >= TU_TURN:
                valid = list(filter(lambda t: t.walkable(), self.tilemap.neighbors_of(baddie.cell_xy())))
                orientation = relative_direction(baddie.cell_xy(), choice(valid).xy_tuple)
                baddie.change_orientation(orientation)
                baddie.tu -= TU_TURN
                self.actor_update_fov(baddie)
                self.update_all_baddie_awareness(local_origin=baddie.cell_xy()) 
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
                self.begin_alert("baddie makes a radio call") 
        if baddie.dead:
            baddie.finished_turn = True
            return
        if baddie.knocked_out:
            baddie.ko_timer -= 1
            if baddie.ko_timer == 0:
                self.un_ko_baddie(baddie)
            else:
                baddie.finished_turn = True
                return
        if baddie.patrol_path is None or baddie.patrol_path_reached():
            baddie.un_rover()
            baddie.patrol_path = None
            assign_roving_status()
            assign_patrol_path()
            if baddie.patrol_path is None:
                baddie.finished_turn = True 
            else:
                self.add_baddie_to_movers(baddie)
        if baddie.spotter and not self.player_turn:
            if not Baddie.alert_sentinel:
                spotter_alert_call()
                baddie.spotter = False  
            if self.debug:
                self.push_to_console("spotter TU remaining: {} | spotter finished turn: {}".format(\
                    baddie.tu, baddie.finished_turn))
        nearby_unresponsive = first(lambda b: chebyshev_distance(b.cell_xy(), baddie.cell_xy()) <= 1 \
            and not b.dead, self.unresponsive_baddies())
        def stationary_with_nothing_to_do(actions) -> bool: 
            return len(actions) == 0 and baddie.patrol_path is None 
        if len(actions) > 0 and not self.player_turn:
            take_actions()
        elif nearby_unresponsive is not None and not baddie.finished_turn: 
            baddie.patrol_path = None
            baddie.un_rover()
            baddie.finished_turn = True
            baddie.waking_other_baddie = False
            self.un_ko_baddie(nearby_unresponsive)
            self.actor_ai_baddie(nearby_unresponsive)
            self.update_all_baddie_awareness(local_origin=nearby_unresponsive.cell_xy()) 
        elif stationary_with_nothing_to_do(actions):
            baddie.finished_turn = True
        finished_investigating = baddie.investigating \
            and self.tilemap.get_tile(self.player.cell_xy()) not in baddie.tiles_can_see \
            and self.alert_timer is None
        if finished_investigating: 
            baddie.investigating = False
            if self.debug:
                self.push_to_console("baddie finished investigating")
    
    def unresponsive_baddies(self) -> list:
        return list(filter(lambda b: isinstance(b, Baddie), self.unresponsive_group))

    def all_baddies(self) -> list: 
        return list(filter(lambda a: isinstance(a, Baddie), self.actors_group)) + \
            list(filter(lambda a: isinstance(a, Baddie), self.unresponsive_group)) 

    def end_turn(self, xy=None):
        self.mover_lock = True
        self.update_on_screen_actors()
        self.game.turn += 1
        self.selected_tile = None
        self.move_select_to_confirm = False
        self.move_path = None
        self.player_turn = False 
        self.player.tu = self.player.max_tu
        self.redraw_switches()
        self.draw()                           
        self.run_ai_behavior()
        self.redraw_switches()
        self.mover_lock = False  

    def make_macguffin(self) -> Terminal: 
        pos = choice(list(filter(lambda t: t.tile_type == "floor" and not t.occupied and not t.door, \
            self.tilemap.all_tiles()))).xy_tuple
        macguffin = Terminal(self.game.entity_sheets[self.game.terminal_sheet], CELL_SIZE, CELL_SIZE, cell_xy_tuple=pos)
        macguffin.name = "macguffin"
        nbrs = self.tilemap.neighbors_of(pos)
        oriented_to = first(lambda t: t.walkable(), nbrs)
        if oriented_to is not None:
            relative_d = relative_direction(pos, oriented_to.xy_tuple)
            macguffin.change_orientation(relative_d)
        self.tilemap.toggle_occupied(pos, True)
        return macguffin

    def make_patrol_intel_terminal(self, building_number) -> Terminal:
        pos = choice(list(filter(lambda t: t.tile_type == "floor" and not t.occupied and not t.door \
            and t.building_number == building_number, self.tilemap.all_tiles()))).xy_tuple
        terminal = Terminal(self.game.entity_sheets[self.game.terminal_sheet], CELL_SIZE, CELL_SIZE, cell_xy_tuple=pos)
        terminal.name = "patrol intel terminal"
        terminal.building_number = building_number
        nbrs = self.tilemap.neighbors_of(pos)
        oriented_to = first(lambda t: t.walkable(), nbrs)
        if oriented_to is not None:
            relative_d = relative_direction(pos, oriented_to.xy_tuple)
            terminal.change_orientation(relative_d)
        self.tilemap.toggle_occupied(pos, True)
        return terminal

    def tile_near_player(self) -> Tile:
        return choice(list(filter(lambda t: chebyshev_distance(t.xy_tuple, self.player.cell_xy()) <= 10 \
            and t.walkable() and not t.occupied, self.tilemap.all_tiles())))

    def baddie_loot_tile(self, baddie) -> Tile:
        potentials = list(filter(lambda t: chebyshev_distance(t.xy_tuple, baddie.cell_xy()) <= 10 \
            and t.walkable() and not t.occupied and t.xy_tuple != baddie.cell_xy() and not t.door, \
            self.tilemap.all_tiles()))
        closest = potentials[0]
        for tile in potentials:
            if chebyshev_distance(tile.xy_tuple, self.player.cell_xy()) < chebyshev_distance(closest.xy_tuple, \
                self.player.cell_xy()):
                closest = tile
        return closest

    def baddie_drop_keycard(self, baddie):
        keys_held = list(filter(lambda k: isinstance(k, Keycard), self.player.inventory))
        keys_left = list(filter(lambda c: c not in list(map(lambda k: k.color, keys_held)), door_colors))
        if ((len(keys_left) > 0 and randint(0, 1) == 1) or len(keys_held) == 0) and not baddie.dropped_keycard:
            drop_tile = self.baddie_loot_tile(baddie)
            card = self.make_keycard(drop_tile.xy_tuple, choice(keys_left))
            self.loot_group.add(card) 
            baddie.dropped_keycard = True

    def make_knife(self, pos) -> Weapon: 
        knife = Weapon(self.game.entity_sheets[self.game.knife_sheet], CELL_SIZE, CELL_SIZE, None, 1, "knife", \
            cell_xy_tuple=pos)
        knife.weapon_sheet_type = "knife"
        self.tilemap.toggle_occupied(pos, True)
        return knife 

    def make_revolver(self, pos) -> Weapon: 
        revolver = Weapon(self.game.entity_sheets[self.game.pistol_sheet], CELL_SIZE, CELL_SIZE, "revolver", 8, \
            "revolver", cell_xy_tuple=pos)
        revolver.ammo_capacity = 6
        revolver.weapon_sheet_type = "pistol"
        self.tilemap.toggle_occupied(pos, True)
        return revolver

    def make_pistol(self, pos) -> Weapon: 
        pistol = Weapon(self.game.entity_sheets[self.game.pistol_sheet], CELL_SIZE, CELL_SIZE, "pistol", 8, \
            "pistol", cell_xy_tuple=pos)
        pistol.ammo_capacity = 16
        pistol.weapon_sheet_type = "pistol"
        self.tilemap.toggle_occupied(pos, True)
        return pistol

    def make_frag_grenade(self, pos, amount) -> Throwable:
        frag = Throwable(self.game.entity_sheets[self.game.grenade_sheet], CELL_SIZE, CELL_SIZE, "frag grenade", \
            amount, cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return frag

    def make_keycard(self, pos, color) -> Keycard:
        card = Keycard(self.game.entity_sheets[self.game.keycards[color]], CELL_SIZE, CELL_SIZE, color, \
            cell_xy_tuple=pos)
        card.name = "{} Keycard".format(color.capitalize())
        self.tilemap.toggle_occupied(pos, True)
        return card

    def make_smoke_grenade(self, pos, amount) -> Throwable:
        smoke = Throwable(self.game.entity_sheets[self.game.grenade_sheet], CELL_SIZE, CELL_SIZE, "smoke grenade", \
            amount, cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return smoke

    def make_sensor_disc(self, pos, amount) -> Throwable:
        disc = Throwable(self.game.entity_sheets[self.game.grenade_sheet], CELL_SIZE, CELL_SIZE, "sensor disc", \
            amount, cell_xy_tuple=pos)
        disc.fov_radius = SENSOR_DISC_RADIUS
        self.tilemap.toggle_occupied(pos, True)
        return disc

    def make_rifle(self, pos, for_baddie=False) -> Weapon: 
        rifle = Weapon(self.game.entity_sheets[self.game.longarm_sheet], CELL_SIZE, CELL_SIZE, "rifle", 8, \
            "rifle", cell_xy_tuple=pos)
        rifle.ammo_capacity = 30
        rifle.weapon_sheet_type = "longarm"
        if not for_baddie:
            self.tilemap.toggle_occupied(pos, True)
        return rifle

    def make_speed_stim(self, pos, amount) -> Consumable: 
        stim = Consumable(self.game.entity_sheets[self.game.stim_sheet], CELL_SIZE, CELL_SIZE, "speed stim", \
            amount, cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return stim

    def make_360_goggles(self, pos) -> Headgear:
        goggles = Headgear(self.game.entity_sheets[self.game.goggles_sheet], CELL_SIZE, CELL_SIZE, "360 goggles", \
            cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return goggles

    def make_tracker_goggles(self, pos) -> Headgear:
        goggles = Headgear(self.game.entity_sheets[self.game.goggles_sheet], CELL_SIZE, CELL_SIZE, "tracker goggles", \
            cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return goggles

    def make_body_armor(self, pos) -> Armor:
        armor = Armor(self.game.entity_sheets[self.game.armor_sheet], CELL_SIZE, CELL_SIZE, "body armor", \
            cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return armor

    def make_revolver_ammo(self, amount, pos) -> Ammo:
        ammo = Ammo(self.game.entity_sheets[self.game.ammo_sheet], CELL_SIZE, CELL_SIZE, "revolver", amount, \
            cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return ammo
        
    def make_pistol_ammo(self, amount, pos) -> Ammo:
        ammo = Ammo(self.game.entity_sheets[self.game.ammo_sheet], CELL_SIZE, CELL_SIZE, "pistol", amount, \
            cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return ammo
        
    def make_rifle_ammo(self, amount, pos) -> Ammo:
        ammo = Ammo(self.game.entity_sheets[self.game.ammo_sheet], CELL_SIZE, CELL_SIZE, "rifle", amount, \
            cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        return ammo

    def make_player(self) -> Actor: 
        pos = choice(list(filter(lambda t: t.xy_tuple[1] == self.tilemap.wh_tuple[1] - 1 and t.walkable(), \
            self.tilemap.all_tiles()))).xy_tuple
        player = Player(self.game.entity_sheets[self.game.dude_1_sheet], CELL_SIZE, CELL_SIZE, cell_xy_tuple=pos)
        self.tilemap.toggle_occupied(pos, True)
        player.change_orientation("up")
        return player

    def make_baddie(self, building_number, pos=None, random_starter=False) -> Actor: 
        if pos is None:
            if random_starter:
                pos = choice(list(filter(lambda x: x.walkable() and not x.occupied \
                    and manhattan_distance(self.player.cell_xy(), x.xy_tuple) > 12, \
                    self.tilemap.all_tiles()))).xy_tuple
            else:
                pos = choice(list(filter(lambda x: x.walkable() and not x.occupied \
                    and manhattan_distance(self.player.cell_xy(), x.xy_tuple) > 20 \
                    and x.building_number == building_number \
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
        return (player_moving or not_player_turn) or self.animation_lock

    def on_screen_cells_rect(self) -> Rect:
        topleft = self.get_topleft_cell()
        return Rect((topleft[0], topleft[1], self.screen_wh_cells_tuple[0], self.screen_wh_cells_tuple[1]))

    def draw_game_over_mode(self):
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
        if not self.win_mode_draw_sentinel:
            pos = (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2,
                self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
            win_surf = self.game.big_splash_surf.copy()
            txt = self.game.game_over_font.render("You won!", True, "white", "black")
            tpos = (win_surf.get_width() // 2 - txt.get_width() // 2, 6)
            win_surf.blit(txt, tpos)
            i, y = 0, 8 + GAME_OVER_FONT_SIZE + 2
            for line in self.stats_lines():
                lpos = (win_surf.get_width() // 2 - line.get_width() // 2, y + i * (HUD_FONT_SIZE + 1))
                win_surf.blit(line, lpos)
                i += 1
            self.win_group.draw(win_surf)
            self.screen.blit(win_surf, pos)
            pygame.display.flip()
            self.win_mode_draw_sentinel = True

    def draw_inventory_mode(self):
        if self.redraw_inventory_mode:
            pos = (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2,
                self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
            inventory_surf = self.game.big_splash_surf.copy()
            txt_title = self.game.hud_font.render("Inventory (page {})".format(self.inventory_page + 1), True, \
                "white", "black")
            tpos_title = (inventory_surf.get_width() // 2 - txt_title.get_width() // 2, 1)
            inventory_surf.blit(txt_title, tpos_title)
            index = 0
            for slot in self.inventory_slots:
                img = self.game.slot_surf.copy()
                if index + len(self.inventory_slots) * self.inventory_page < len(self.player.inventory):
                    real_index = index + self.inventory_page * len(self.inventory_slots)
                    item = self.player.inventory[real_index]
                    msg = item.name
                    if isinstance(item, Weapon) and item.name != "knife":
                        msg += " ({}/{})".format(item.ammo, item.ammo_capacity)
                    if item.stackable:
                        msg += "(x{})".format(item.num_stacked)
                    if item.equipped:
                        msg += " (equipped)"
                    slot_txt = self.game.hud_font.render("{}".format(msg), True, "white", "black")
                else:
                    slot_txt = self.game.hud_font.render("< empty >", True, "white", "black") 
                slot_txt_pos = (img.get_width() // 2 - slot_txt.get_width() // 2, \
                    img.get_height() // 2 - slot_txt.get_height() // 2)
                img.blit(slot_txt, slot_txt_pos)
                slot.image = img
                index += 1
            self.inventory_group.draw(inventory_surf)
            self.screen.blit(inventory_surf, pos)
            pygame.display.flip()
        self.redraw_inventory_mode = False

    def draw(self, inventory_refresh=False, no_flip=False): 
        if self.game_over_mode:
            self.draw_game_over_mode()
            return
        elif self.win_mode:
            self.draw_win_mode()
            return
        elif self.inventory_mode and not inventory_refresh:
            self.draw_inventory_mode()
            return
        topleft = self.get_topleft_cell()
        cells_on_screen = self.on_screen_cells_rect()
        def draw_mm_view_rect():
            mm_cell_size = MINI_MAP_SIZE[0] / MAP_SIZE[0] 
            view_w = (((self.screen.get_width() - SIDE_HUD_WIDTH) // CELL_SIZE) + 1) * mm_cell_size
            view_h = (self.screen_wh_cells_tuple[1] + 1) * mm_cell_size
            view = (topleft[0] * mm_cell_size, topleft[1] * mm_cell_size, view_w, view_h)
            pygame.draw.rect(self.side_hud, "white", view, 1)
        drawing_smoke = len(self.on_screen_smoke_group) > 0 \
            and self.smoke_redraw_ticker == self.smoke_redraw_ticker_limit
        if drawing_smoke: 
            self.smoke_redraw_ticker = 0
        elif len(self.on_screen_smoke_group) > 0:
            self.smoke_redraw_ticker += 1
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
                if self.tile_in_player_move_range(dscore, tile) and self.player_turn and not self.throwing_mode:
                    if self.game.show_move_dscore:
                        msurf = self.game.movement_range_cell_surf.copy()
                        txt = self.game.hud_font.render("{}".format(dscore), True, "white", "black")
                        tpos = (msurf.get_width() // 2 - txt.get_width() // 2, \
                            msurf.get_height() // 2 - txt.get_height() // 2)
                        msurf.blit(txt, tpos)
                        move_range_blits.append((msurf, pos))
                    else:
                        move_range_blits.append((self.game.movement_range_cell_surf, pos))
                elif self.throwing_mode and self.player_turn:
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
            self.on_screen_loot_group.draw(self.on_screen_map_surface)
            self.on_screen_unresponsive_group.draw(self.on_screen_map_surface)
            loot_interactions_available = list(filter(lambda a: a[0] == "interact", self.player.actions_available))
            melee_actions_available = list(filter(lambda a: a[0] == "melee", self.player.actions_available))
            lethal_actions_available = list(filter(lambda a: a[0] == "lethal", self.player.actions_available))
            for baddie in list(filter(lambda a: isinstance(a, Baddie), self.on_screen_actors_group)):
                if baddie.can_see_player:        
                    pos = ((baddie.x + CELL_SIZE // 2) - self.game.alert_base.get_width() // 2, \
                        baddie.y - self.game.alert_base.get_height())
                    self.on_screen_map_surface.blit(self.game.alert_base, pos)
                elif baddie.investigating:
                    pos = ((baddie.x + CELL_SIZE // 2) - self.game.huh_base.get_width() // 2, \
                        baddie.y - self.game.huh_base.get_height())
                    self.on_screen_map_surface.blit(self.game.huh_base, pos)
                for action in melee_actions_available: 
                    if baddie is action[1]:
                        pygame.draw.rect(self.on_screen_map_surface, "yellow", baddie.rect, 1)
                for action in lethal_actions_available: 
                    if baddie is action[1]:
                        pygame.draw.rect(self.on_screen_map_surface, "red", baddie.rect, 2)
            for baddie in list(filter(lambda a: isinstance(a, Baddie), self.on_screen_unresponsive_group)):
                if baddie.knocked_out and not baddie.dead:
                    pos = ((baddie.x + CELL_SIZE // 2) - self.game.zzz_base.get_width() // 2, \
                        baddie.y - self.game.zzz_base.get_height())
                    self.on_screen_map_surface.blit(self.game.zzz_base, pos)
                for action in lethal_actions_available: 
                    if baddie is action[1]:
                        pygame.draw.rect(self.on_screen_map_surface, "red", baddie.rect, 2)
            for action in loot_interactions_available: 
                loot = action[1]
                self.on_screen_map_surface.blit(self.game.loot_base, (loot.x, loot.y))
            self.on_screen_actors_group.draw(self.on_screen_map_surface)  
            self.screen.blit(self.on_screen_map_surface, (0, 0))
        if drawing_smoke:  
            self.screen.blit(self.on_screen_map_surface, (0, 0))   
            self.on_screen_smoke_group.draw(self.screen)          
        if self.redraw_side_hud:
            def draw_dynamic_hud_surf(msg, y, fg="white", bg="black"):
                surf = self.game.hud_font.render(msg, True, fg, bg)
                base = pygame.Surface((SIDE_HUD_WIDTH, surf.get_height() + 2))
                base.fill(bg)
                pygame.draw.rect(base, "magenta", base.get_rect(), 1)
                base.blit(surf, (base.get_width() // 2 - surf.get_width() // 2, 1))
                self.side_hud.blit(base, (0, y))
            def draw_acquired_keys():
                base = pygame.Surface((SIDE_HUD_WIDTH, HUD_FONT_SIZE + 2))
                base.fill("black")
                kw = base.get_width() // len(door_colors)
                ky = base.get_height() // 2
                r = kw // 2
                kx = r
                for color in door_colors:
                    kpos = (kx, ky)
                    if self.player_has_key(color):
                        pygame.draw.circle(base, color, kpos, r)
                    kx += kw
                pygame.draw.rect(base, "magenta", base.get_rect(), 1)
                self.side_hud.blit(base, (0, KEYS_Y)) 
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
            weapon = self.player.equipped_weapon
            if weapon is None:
                wep_msg = "No Weapon Equipped"
            elif weapon.name == "knife":
                wep_msg = "Knife"
            else:
                wep_msg = "{} ({}/{})".format(weapon.name, weapon.ammo, weapon.ammo_capacity)
            draw_dynamic_hud_surf(wep_msg, WEAPON_Y, fg="white", bg="black")
            if self.player.equipped_armor is None:
                armor_msg = "No Body Armor Equipped"
            else:
                armor_msg = "Body Armor Equipped"
            draw_dynamic_hud_surf(armor_msg, ARMOR_Y, fg="white", bg="black")
            headgear = self.player.equipped_headgear
            if headgear is None:
                head_msg = "No Headgear Equipped"
            else:
                head_msg = "{} Equipped".format(headgear.name)
            draw_dynamic_hud_surf(head_msg, HEADGEAR_Y, fg="white", bg="black")
            draw_acquired_keys()
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
        if (self.redraw_map or self.redraw_side_hud or self.redraw_console) and not no_flip:
            pygame.display.flip()
        elif drawing_smoke:
            pygame.display.flip()
        if self.redraw_map:
            self.redraw_map = False
        if self.redraw_side_hud:
            self.redraw_side_hud = False
        if self.redraw_console:
            self.redraw_console = False
        if inventory_refresh:
            self.redraw_inventory_mode = True
            self.draw_inventory_mode()

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
        has_tracker_goggles = self.player.equipped_headgear is not None \
            and self.player.equipped_headgear.name == "tracker goggles"
        if has_tracker_goggles:
            return list(filter(lambda m: isinstance(m.actor, Baddie) \
                and (m.actor.building_number in self.player.building_patrol_intels \
                or self.tilemap.get_tile(m.actor.cell_xy()) in self.player.tiles_can_see), \
                self.visible_movers + self.invisible_movers))
        else:
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

    def handle_attack(self, attacker, action): 
        xy = attacker.cell_xy()
        if self.tilemap.get_tile(xy) in self.player.tiles_can_see:
            self.tilemap.camera = xy
            self.update_on_screen_actors()
            self.redraw_map = True
            self.draw()
            topleft = self.get_topleft_cell()
            # TODO: special "noises" for coup de grace, knife, and silenced pistol
            if action[0] == "melee":
                msg = choice(["*pow*", "*bam*", "*whack*", "*bonk*", "*thunk*", "*crunch*"])
            elif action[0] == "lethal":
                msg = choice(["*bang*", "*boom*", "*gat*", "*crack*"])
            txt = self.game.hud_font.render(msg, True, "white", "black")
            pos = ((((xy[0] - topleft[0]) * CELL_SIZE) + CELL_SIZE // 2) - txt.get_width() // 2, \
                ((xy[1] - topleft[1]) * CELL_SIZE) - txt.get_height())
            self.screen.blit(txt, pos)
            pygame.display.flip()
            pygame.time.wait(600) 
        self.animation_lock = False

    def handle_throwable(self, throwing_item, tile): 
        topleft = self.get_topleft_cell()
        throwing_item.speed = 6 
        current = Vector2((self.player.x, self.player.y))
        end = Vector2(((tile.xy_tuple[0] - topleft[0]) * CELL_SIZE, \
            (tile.xy_tuple[1] - topleft[1]) * CELL_SIZE))
        while current != end: 
            current = current.move_towards(end, throwing_item.speed)
            self.redraw_map = True
            self.draw(no_flip=True)
            self.screen.blit(self.game.thrown_surf, (current.x, current.y))
            pygame.display.flip()
        if throwing_item.name == "frag grenade": 
            fragged_tiles = self.tilemap.valid_tiles_in_range_of(tile.xy_tuple, FRAG_RADIUS)
            for ftile in fragged_tiles:
                self.tilemap.destruct_tile(ftile.xy_tuple)
            self.update_player_fov()
            self.tilemap.update_mini_map_surface()
            fragged_actors = list(filter(lambda b: not b.dead and self.tilemap.get_tile(b.cell_xy()) in fragged_tiles, \
                self.all_actors()))
            for actor in fragged_actors:
                if isinstance(actor, Baddie):
                    actor.kill()
                    self.kill_baddie(actor)
                elif isinstance(actor, Player):
                    self.player.dead = True
                    self.push_to_console("...frag grenades have a minimum safe distance...")
            self.begin_alert("you used a frag grenade!", player_override=True, code_red=True)
            self.redraw_switches()
            self.update_on_screen_actors()
            explosion_colors = ["red", "orange", "yellow"]
            frag_frames = 60 
            for i in range(frag_frames):  
                if i % 2 == 0:
                    self.redraw_map = True    
                    self.draw(no_flip=True)  
                    fragging = choice(fragged_tiles).xy_tuple
                    pos = ((fragging[0] - topleft[0]) * CELL_SIZE, (fragging[1] - topleft[1]) * CELL_SIZE)
                    color = choice(explosion_colors)
                    r = randint(12, 20)
                    pygame.draw.circle(self.screen, color, pos, r)
                    pygame.display.flip()
        elif throwing_item.name == "smoke grenade":
            smoked_tiles = self.tilemap.valid_tiles_in_range_of(tile.xy_tuple, SMOKE_RADIUS)
            smokes = []
            for tile in smoked_tiles:
                smoke = Smoke(self.game.entity_sheets[self.game.smoke_sheet], CELL_SIZE, CELL_SIZE, \
                    cell_xy_tuple=tile.xy_tuple)
                smokes.append(smoke)
            self.smoke_group.add(smokes)
            self.update_player_fov()
            self.redraw_switches()
            self.update_on_screen_actors()  
        elif throwing_item.name == "sensor disc": 
            throwing_item.cell_x, throwing_item.cell_y = tile.xy_tuple
            self.loot_group.add(throwing_item)
            self.tilemap.toggle_occupied(tile.xy_tuple, True)
            throwing_item.looted = False  
            self.update_player_fov()
            self.redraw_switches()              
            self.update_on_screen_actors()  
        self.animation_lock = False              

    def player_has_key(self, color) -> bool:
        return first(lambda l: isinstance(l, Keycard) and l.color == color, self.player.inventory) is not None

    def smoke_check(self):
        remaining = []
        for smoke in self.smoke_group:
            smoke.dissipates_in -= 1
            if smoke.dissipates_in > 0:
                remaining.append(smoke)
        self.smoke_group.empty()
        self.smoke_group.add(remaining)

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
                self.redraw_switches(rconsole=False)
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
                self.redraw_switches(rconsole=False)
            elif pygame.key.get_pressed()[K_SLASH] and self.shift_pressed():
                self.console.push_controls()
                console_changed = True
            if console_changed:
                self.redraw_console = True

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
            x2 = x - (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2)
            y2 = y - (self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
            for entity in self.game_over_group: # clickables are offset 
                if isinstance(entity, Clickable): 
                    if entity.clicked((x2, y2)):
                        entity.effect((x2, y2))
                        return

        def handle_left_click_win_mode(): 
            x, y = pygame.mouse.get_pos()
            x2 = x - (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2)
            y2 = y - (self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
            for entity in self.win_group: # clickables are offset 
                if isinstance(entity, Clickable): 
                    if entity.clicked((x2, y2)):
                        entity.effect((x2, y2))
                        return

        def handle_left_click_inventory_mode(): 
            x, y = pygame.mouse.get_pos()
            x2 = x - (self.screen.get_width() // 2 - self.game.big_splash_surf.get_width() // 2)
            y2 = y - (self.screen.get_height() // 2 - self.game.big_splash_surf.get_height() // 2)
            for entity in self.inventory_group: # clickables are offset 
                if isinstance(entity, InventorySlot):
                    if entity.clicked((x2, y2)):
                        self.handle_item_clicks(entity.slot_index)
                        return
                elif isinstance(entity, Clickable): 
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
            elif self.inventory_mode:
                handle_left_click_inventory_mode()
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
                melee_action_clickable = first(lambda a: a[1].clicked((x, y)) \
                    and a[0] == "melee", self.player.actions_available) 
                lethal_action_clickable = first(lambda a: a[1].clicked((x, y)) \
                    and a[0] == "lethal", self.player.actions_available) 
                action_taken = False
                if self.throwing_mode and tile in self.player.tiles_can_see:
                    self.push_to_console("Threw {}!".format(self.throwing_item.name))
                    self.animation_lock = True
                    self.redraw_switches()
                    self.draw()
                    self.handle_throwable(self.throwing_item, tile) 
                    self.throwing_mode = False
                    if self.throwing_item.name != "sensor disc":
                        self.throwing_item.num_stacked -= 1
                    else:
                        self.player.inventory.remove(self.throwing_item)
                    self.throwing_item = None 
                    self.player.sort_inventory()
                    self.player.tu -= TU_THROW
                    self.player.actions_available = self.actor_possible_actions(self.player)
                    self.distance_map_to_player = self.dmap_to_player()
                    self.redraw_switches()
                    if self.player.dead:
                        self.end_turn()
                elif melee_action_clickable is not None and self.shift_pressed():
                    has_tu  = self.player.tu >= TU_MELEE
                    valid_target = melee_action_clickable[1].can_be_knocked_out()
                    if has_tu and valid_target:
                        self.animation_lock = True
                        self.actor_take_melee_action(self.player, melee_action_clickable)
                        self.handle_attack(self.player, melee_action_clickable) 
                        self.baddie_drop_keycard(melee_action_clickable[1])
                        action_taken = True
                    elif not has_tu:
                        self.push_to_console("Melee action requires {} TU!".format(TU_MELEE))
                    elif not valid_target:
                        self.push_to_console("{} already KO'd!".format(melee_action_clickable[1].name))
                    self.redraw_switches()
                elif lethal_action_clickable is not None and self.ctrl_pressed():
                    has_tu = self.player.tu >= TU_LETHAL
                    valid_target = lethal_action_clickable[1].can_be_killed()
                    if has_tu and valid_target: 
                        if self.player.equipped_weapon is None:
                            self.animation_lock = True
                            self.actor_take_lethal_action(self.player, lethal_action_clickable, silenced=True)
                            self.handle_attack(self.player, lethal_action_clickable) 
                            self.baddie_drop_keycard(lethal_action_clickable[1])
                        elif self.player.equipped_weapon.name == "knife" \
                            or self.player.equipped_weapon.name == "silenced pistol": 
                            self.animation_lock = True
                            self.actor_take_lethal_action(self.player, lethal_action_clickable, silenced=True)
                            self.handle_attack(self.player, lethal_action_clickable) 
                            self.baddie_drop_keycard(lethal_action_clickable[1])
                        else:
                            self.animation_lock = True
                            self.actor_take_lethal_action(self.player, lethal_action_clickable)
                            self.handle_attack(self.player, lethal_action_clickable) 
                            self.baddie_drop_keycard(lethal_action_clickable[1])
                        action_taken = True
                    elif not has_tu:
                        self.push_to_console("Lethal action requires {} TU!".format(TU_LETHAL))
                    elif not valid_target:
                        self.push_to_console("{} already dead!".format(melee_action_clickable[1].name))
                    self.redraw_switches()
                elif not self.move_select_to_confirm and not tile.occupied:
                    score = self.distance_map_to_player[tx][ty] 
                    if self.tile_in_player_move_range(score, tile):
                        self.selected_tile = tile_clicked_xy
                        self.move_select_to_confirm = True
                        path = self.shortest_path(tile_clicked_xy, self.player.cell_xy(), \
                            pre_dmap=self.distance_map_to_player, reverse=True) 
                        if path is None:  
                            print("Error! No path to click! <this should never happen>")
                            self.push_to_console("Error! No path to click! <this should never happen>")
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
                    action_taken = True
                    self.redraw_switches()
                else:
                    self.move_path = None
                    self.selected_tile = None
                    self.move_select_to_confirm = False
                    self.redraw_switches()
                if action_taken:
                    self.distance_map_to_player = self.dmap_to_player()
                    self.player.actions_available = self.actor_possible_actions(self.player)

        def handle_middle_click():
            x, y = pygame.mouse.get_pos()
            tile_clicked_xy = tile_clicked((x, y))
            if tile_clicked_xy is not None:
                self.tilemap.camera = tile_clicked_xy
                self.redraw_switches()

        def handle_right_click():
            x, y = pygame.mouse.get_pos()
            tile_clicked_xy = tile_clicked((x, y))
            def click_orientation() -> str: # or None
                tx, ty = tile_clicked_xy
                px, py = self.player.cell_xy()
                if tx < px and py == ty:
                    return "left"
                elif tx > px and py == ty:
                    return "right"
                elif tx == px and ty < py:
                    return "up"
                elif tx == px and ty > py:
                    return "down"
                elif tx < px and ty < py:
                    return "upleft"
                elif tx < px and ty > py:
                    return "downleft"
                elif tx > px and ty < py:
                    return "upright"
                elif tx > px and ty > py:
                    return "downright"
                elif tx == px and ty == py:
                    return None
            if self.throwing_mode:
                self.throwing_mode = False
                self.throwing_item = None
                self.redraw_switches()
            elif tile_clicked_xy is not None \
                and tile_clicked_xy != self.player.cell_xy():
                cost = TU_TURN
                new_orientation = click_orientation()
                if self.player.tu >= cost and new_orientation != self.player.orientation:
                    self.player.change_orientation(new_orientation)
                    self.player.tu -= cost
                    self.update_player_fov()
                    self.player.actions_available = self.actor_possible_actions(self.player)
                    self.distance_map_to_player = self.dmap_to_player(bounded=True)
                    self.selected_tile = None
                    self.move_path = None
                    self.move_select_to_confirm = False
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
                self.redraw_console = True

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
                    self.distance_map_to_player = self.dmap_to_player(bounded=True)
                    self.player.actions_available = self.actor_possible_actions(self.player)
            if mover is not None:
                if not mover.actor.player and self.player_turn:
                    return
                from_xy = mover.actor.cell_xy()
                to_xy = mover.path[0]
                is_door = self.tilemap.get_tile(to_xy).door
                if is_door and isinstance(mover.actor, Player):
                    door_color = self.tilemap.get_tile(to_xy).door_color
                    player_has_key = self.player_has_key(door_color)
                    door_ajar = first(lambda b: b.cell_xy() == to_xy, self.unresponsive_baddies()) is not None 
                    from_inside = self.tilemap.get_tile(from_xy).building_number is not None
                    if not (player_has_key or door_ajar or from_inside): 
                        player_hook(mover)
                        self.remove_from_movers(self.player)
                        self.push_to_console("You need the {} keycard to enter this door!".format(door_color))
                        self.redraw_switches()
                        return
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
                    if isinstance(mover.actor, Player):
                        self.update_player_fov()
                    else:
                        self.actor_update_fov(mover.actor) 
                    if isinstance(mover.actor, Player):
                        self.redraw_switches(rconsole=False)
                    elif movers is self.visible_movers:
                        self.redraw_switches(rconsole=False, rhud=False)
                    if mover.goal_reached(): 
                        self.remove_from_movers(mover.actor)
                        if isinstance(mover.actor, Baddie): 
                            mover.actor.patrol_path = None  
                    baddie_hook(mover)
                    player_hook(mover)
                if event_type == self.game.VISIBLE_MOVER_CHECK and not self.animation_lock:
                    self.visible_movers = movers
                elif event_type == self.game.INVISIBLE_MOVER_CHECK and not self.animation_lock:
                    self.invisible_movers = movers
                self.update_all_baddie_awareness(local_origin=mover.actor.cell_xy()) 
                self.update_on_screen_actors()

        def player_turn_ready() -> bool:
            for baddie in self.all_baddies():
                if not baddie.finished_turn:
                    return False
            self.player.actions_available = self.actor_possible_actions(self.player)
            self.distance_map_to_player = self.dmap_to_player(bounded=True)
            self.alert_update()
            self.smoke_check() 
            self.game_over_check()
            self.redraw_switches()
            return True

        def mover_event(event_type) -> bool:
            return (event.type == self.game.VISIBLE_MOVER_CHECK or event.type == self.game.INVISIBLE_MOVER_CHECK) \
                and not self.mover_lock

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
            elif mover_event(event.type):
                self.mover_lock = True
                handle_movers(event.type)
                self.mover_lock = False
            # end baddie turns / start player turn
            elif event.type == self.game.PLAYER_TURN_READY_CHECK and not self.player_turn:
                self.player_turn = player_turn_ready()
        pygame.event.pump() 

    def hanging_baddies(self) -> list:
        return list(filter(lambda b: not b.finished_turn, self.all_baddies()))

    def on_screen_tiles(self):
        r = self.on_screen_cells_rect()
        return list(filter(lambda t: r.contains(Rect(t.xy_tuple[0], t.xy_tuple[1], 0, 0)), self.tilemap.all_tiles()))

    def reveal_screen(self, move_camera_to=None, with_msg=None):
        if move_camera_to is not None:
            self.tilemap.camera = move_camera_to
        os_tiles = self.on_screen_tiles()
        apply(self.reveal_tile, os_tiles)
        self.player.tiles_can_see = os_tiles
        if with_msg is not None:
            self.push_to_console(with_msg)
        self.redraw_switches()
        self.update_on_screen_actors()
        self.draw()

    def game_over_check(self):
        if self.player.knocked_out or self.player.dead:
            self.reveal_screen(move_camera_to=self.player.cell_xy(), with_msg="...game over...")
            pygame.time.wait(3000) 
            self.game_over_mode = True

    def new_alert_zone_rect(self, origin_xy) -> tuple:
        x, y = origin_xy
        return (x - ALERT_ZONE_D, y - ALERT_ZONE_D, ALERT_ZONE_D * 2 + 1, ALERT_ZONE_D * 2 + 1)

    def all_baddies_within_bound(self, bounding_rect, responsive_only=False):
        x, y, w, h = bounding_rect
        r = Rect((x, y, w, h))
        if responsive_only:
            return list(filter(lambda b: r.contains(Rect((b.cell_x, b.cell_y, 0, 0))) \
                and b.responsive(), self.all_baddies()))
        else:
            return list(filter(lambda b: r.contains(Rect((b.cell_x, b.cell_y, 0, 0))), self.all_baddies()))

    def begin_alert(self, msg, player_override=False, code_red=False):
        baddies_to_uparm = randint(0, 1)
        if not Baddie.alert_sentinel and (not self.player_turn or player_override):
            self.times_alerted += 1
            Baddie.alert_sentinel = True
            self.push_to_console("Alert ({})! Stay out of sight to reduce the timer.".format(msg))
            self.alert_timer = 10
            x, y = self.player.cell_xy()
            self.alert_zone_rect = self.new_alert_zone_rect((x, y))
            r = Rect(self.alert_zone_rect)
            baddies_alerted = list(filter(lambda b: r.contains(Rect(b.cell_x, b.cell_y, 0, 0)) \
                and b.responsive(), self.all_baddies()))
            baddies_uparmed = 0
            for baddie in baddies_alerted:
                alert_room = Baddie.num_alert_rovers < NUM_ALERT_ROVERS
                not_chasing_player = not baddie.can_see_player and not baddie.spotter 
                if alert_room and not_chasing_player and not baddie.alert_rover:
                    will_uparm = baddie.equipped_weapon is None and (code_red or baddies_uparmed < baddies_to_uparm)
                    if will_uparm:
                        self.uparm_baddie(baddie)
                        baddies_uparmed += 1
                    baddie.investigating = True
                    baddie.patrol_path = None
                    self.remove_from_movers(baddie)
                    baddie.un_rover() 
                    baddie.set_alert_rover()
                    self.actor_ai_baddie(baddie) 

    def remove_from_movers(self, actor):
        visible_mover = first(lambda m: m.actor is actor, self.visible_movers)
        invisible_mover = first(lambda m: m.actor is actor, self.invisible_movers)
        if visible_mover is not None and visible_mover in self.visible_movers:
            self.visible_movers.remove(visible_mover)
        elif invisible_mover is not None and invisible_mover in self.invisible_movers:
            self.invisible_movers.remove(invisible_mover)

    def update_all_baddie_awareness(self, local_origin=None): 
        def spot(baddie):
            path = self.shortest_path(baddie.cell_xy(), self.player.cell_xy(), pre_dmap=self.distance_map_to_player) 
            if path is not None:
                self.remove_from_movers(baddie)
                baddie.patrol_path = self.shortest_path(baddie.cell_xy(), self.player.cell_xy(), \
                    pre_dmap=self.distance_map_to_player) 
                self.add_baddie_to_movers(baddie)
                if self.debug:
                    self.push_to_console("baddie chasing player")
            baddie.can_see_player = True
            baddie.investigating = False
            baddie.spotter = True
            self.actor_ai_baddie(baddie) 

        if local_origin is not None:
            x, y = local_origin
            d = AWARENESS_UPDATE_D
            bounding_rect = Rect((x - d, y - d, d * 2, d * 2)) 
            baddies_to_update = self.all_baddies_within_bound(bounding_rect, responsive_only=True)
        else: 
            baddies_to_update = list(filter(lambda b: b.responsive(), self.all_baddies()))

        for baddie in baddies_to_update:
            can_see_player = self.tilemap.get_tile(self.player.cell_xy()) in baddie.tiles_can_see
            unresponsive = first(lambda b: self.tilemap.get_tile(b.cell_xy()) in baddie.tiles_can_see \
                and not b.dead, self.unresponsive_baddies())
            undiscovered_body = first(lambda b: self.tilemap.get_tile(b.cell_xy()) in baddie.tiles_can_see \
                and b.dead and not b.body_discovered, self.unresponsive_baddies())
            if can_see_player and not baddie.can_see_player:
                spot(baddie)
            elif not can_see_player and baddie.can_see_player and not baddie.investigating:
                baddie.can_see_player = False
                baddie.investigating = True
                if self.debug:
                    self.push_to_console("baddie investigating")
            elif baddie.can_see_player and self.player_turn: 
                spot(baddie)
            elif undiscovered_body is not None and not can_see_player:
                undiscovered_body.body_discovered = True
                self.begin_alert("dead body discovered", code_red=True)
            elif not baddie.waking_other_baddie and unresponsive is not None and not can_see_player:
                target = choice(list(filter(lambda t: t.walkable() and not t.occupied, \
                    self.tilemap.neighbors_of(unresponsive.cell_xy()))))
                path = self.shortest_path(baddie.cell_xy(), target.xy_tuple) 
                if path is not None: 
                    baddie.waking_other_baddie = True  
                    self.remove_from_movers(baddie)    
                    baddie.un_rover()
                    baddie.patrol_path = path
                    self.add_baddie_to_movers(baddie)
                    self.actor_ai_baddie(baddie)  
                
            baddie.can_see_player = can_see_player

    def update_on_screen_actors(self):
        invisible = []
        visible = []
        self.on_screen_actors_group.empty()
        self.on_screen_loot_group.empty()
        self.on_screen_unresponsive_group.empty()
        self.on_screen_smoke_group.empty()
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
        for loot in self.loot_group:
            if actor_visible(loot):
                loot.x = (loot.cell_x - topleft[0]) * CELL_SIZE
                loot.y = (loot.cell_y - topleft[1]) * CELL_SIZE
                loot.rect = Rect(loot.x, loot.y, loot.width, loot.height) 
                self.on_screen_loot_group.add(loot)
        for corpse in self.unresponsive_group:
            if actor_visible(corpse):
                corpse.x = (corpse.cell_x - topleft[0]) * CELL_SIZE
                corpse.y = (corpse.cell_y - topleft[1]) * CELL_SIZE
                corpse.rect = Rect(corpse.x, corpse.y, corpse.width, corpse.height) 
                self.on_screen_unresponsive_group.add(corpse)
        for smoke in self.smoke_group:
            if actor_visible(smoke):
                smoke.x = (smoke.cell_x - topleft[0]) * CELL_SIZE
                smoke.y = (smoke.cell_y - topleft[1]) * CELL_SIZE
                smoke.rect = Rect(smoke.x, smoke.y, smoke.width, smoke.height) 
                self.on_screen_smoke_group.add(smoke)
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
            if baddie not in self.player.visible_baddies and baddie.responsive():
                new_baddie_spotted = True
                break
        if new_baddie_spotted:
            self.push_to_console("Baddie spotted!")
            self.distance_map_to_player = self.dmap_to_player(bounded=True)
            self.remove_from_movers(self.player)
            self.update_all_baddie_awareness(local_origin=self.player.cell_xy()) 
            self.redraw_switches()
        self.player.visible_baddies = visible_baddies

    def redraw_switches(self, rmap=True, rhud=True, rconsole=True):
        if rmap:
            self.redraw_map = True
            self.do_update_on_screen_actors = True
        if rhud:
            self.redraw_side_hud = True
        if rconsole:
            self.redraw_console = True

    def update(self):
        self.handle_events()
        if self.do_update_on_screen_actors:
            self.update_on_screen_actors()
        self.on_screen_smoke_group.update() 

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
        
