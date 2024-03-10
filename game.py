import pygame
from scene import *
from entity import *
from constants import *
from loading_screen import loading_screen

class Game: 
    def __init__(self):
        self.hud_font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
        self.title_font = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
        self.game_over_font = pygame.font.Font(FONT_PATH, GAME_OVER_FONT_SIZE)
        self.loader = pygame.Surface(LOADER_SIZE, flags=SRCALPHA)
        self.loader.fill((30, 50, 30))
        self.GAME_UPDATE_TICK = pygame.event.custom_type()
        self.VISIBLE_MOVER_CHECK = pygame.event.custom_type()
        self.INVISIBLE_MOVER_CHECK = pygame.event.custom_type()
        self.PLAYER_TURN_READY_CHECK = pygame.event.custom_type()
        self.running = True
        self.screen = pygame.display.get_surface() 
        self.MAP_DISPLAY_SIZE = (self.screen.get_width() - SIDE_HUD_WIDTH, self.screen.get_height() - CONSOLE_HEIGHT)
        self.screen_wh_cells_tuple = (self.MAP_DISPLAY_SIZE[0] // CELL_SIZE, self.MAP_DISPLAY_SIZE[1] // CELL_SIZE)
        self.screen.set_colorkey(ALPHA_KEY)
        self.clock = pygame.time.Clock()
        self.show_fps = False
        self.show_all_actors = False
        self.reveal_map_at_start = False
        self.debug_hangers = False
        self.give_player_all_tracking_info = False
        self.show_bldg_numbers = False
        self.show_move_dscore = False
        self.move_all_actors_quickly = False
        # loot base surf
        self.loot_base_surf = pygame.image.load(LOOT_BASE_PATH)
        self.loot_base_surf.convert_alpha()
        # keycard surfaces
        self.keycards = {}
        for color in door_colors:
            self.keycards[color] = self.loot_base_surf.copy()
            card_surf = pygame.Surface((30, 20), flags=SRCALPHA)
            card_surf.fill(color)
            pygame.draw.rect(card_surf, "black", card_surf.get_rect(), 3)
            pos = (self.loot_base_surf.get_width() // 2 - card_surf.get_width () // 2, \
                self.loot_base_surf.get_height() // 2 - card_surf.get_height() // 2)
            self.keycards[color].blit(card_surf, pos)
        # movement range surf
        self.movement_range_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.movement_range_cell_surf.set_colorkey(ALPHA_KEY)
        self.movement_range_cell_surf.fill(ALPHA_KEY)
        self.movement_range_cell_surf.fill(COLOR_MOVEMENT_RANGE)
        pygame.draw.rect(self.movement_range_cell_surf, "green", self.movement_range_cell_surf.get_rect(), 1)
        # alert surf
        alert_txt = self.title_font.render("!", True, "yellow") 
        self.alert_base = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.alert_base.set_colorkey(ALPHA_KEY)
        self.alert_base.fill(ALPHA_KEY)
        self.alert_base.blit(alert_txt, (self.alert_base.get_width() // 2 - alert_txt.get_width() // 2, 1))
        # huh surf
        huh_txt = self.title_font.render("?", True, "yellow") 
        self.huh_base = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.huh_base.set_colorkey(ALPHA_KEY)
        self.huh_base.fill(ALPHA_KEY)
        self.huh_base.blit(huh_txt, (self.huh_base.get_width() // 2 - huh_txt.get_width() // 2, 1))
        # zzz sheet 
        zzz_txt = self.hud_font.render("zzz", True, "yellow")  
        self.zzz_base = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.zzz_base.set_colorkey(ALPHA_KEY)
        self.zzz_base.fill(ALPHA_KEY)
        self.zzz_base.blit(zzz_txt, (self.zzz_base.get_width() // 2 - zzz_txt.get_width() // 2, 1))
        # loot surf
        loot_txt = self.title_font.render("$", True, "yellow") 
        self.loot_base = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.loot_base.set_colorkey(ALPHA_KEY)
        self.loot_base.fill(ALPHA_KEY)
        self.loot_base.blit(loot_txt, (self.loot_base.get_width() // 2 - loot_txt.get_width() // 2, 1))
        # patrol path surf
        self.patrol_path_surf = pygame.image.load(PATROL_PATH_PATH)
        self.patrol_path_surf.convert_alpha()
        # thrown surf
        self.thrown_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.thrown_surf.set_colorkey(ALPHA_KEY)
        self.thrown_surf.fill(ALPHA_KEY)
        pos = (self.thrown_surf.get_width() // 2, self.thrown_surf.get_height() // 2)
        pygame.draw.circle(self.thrown_surf, "black", pos, 4)
        # patrol end surf
        self.patrol_end_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.patrol_end_surf.fill((200, 0, 0, 120))
        pygame.draw.rect(self.patrol_end_surf, "red", self.patrol_path_surf.get_rect(), 1)
        # enemy LoS surf
        self.enemy_los_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.enemy_los_cell_surf.set_colorkey(ALPHA_KEY)
        self.enemy_los_cell_surf.fill(ALPHA_KEY)
        self.enemy_los_cell_surf.fill(COLOR_ENEMY_LOS)
        # fog surf
        self.foggy_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.foggy_cell_surf.set_colorkey(ALPHA_KEY)
        self.foggy_cell_surf.fill(ALPHA_KEY)
        self.foggy_cell_surf.fill(COLOR_FOG)
        # smoke sheet
        self.smoke_sheet = pygame.image.load(SMOKE_PATH)
        self.smoke_sheet.convert_alpha()
        # end turn button surf
        self.end_turn_surf = pygame.Surface((SIDE_HUD_WIDTH, HUD_FONT_SIZE + 2), flags=SRCALPHA)
        self.end_turn_surf.fill(COLOR_HUD_RED)
        end_turn_txt = self.hud_font.render("END TURN", True, "white")
        self.end_turn_surf.blit(end_turn_txt, \
                ((self.end_turn_surf.get_width() // 2 - end_turn_txt.get_width() // 2) + 1, 1))
        pygame.draw.rect(self.end_turn_surf, "magenta", self.end_turn_surf.get_rect(), 1)
        # inventory button surf
        self.inventory_surf = pygame.Surface((SIDE_HUD_WIDTH, HUD_FONT_SIZE + 3), flags=SRCALPHA)
        self.inventory_surf.fill((0, 0, 120))
        pygame.draw.rect(self.inventory_surf, "magenta", self.inventory_surf.get_rect(), 1)
        inventory_txt = self.hud_font.render("Inventory", True, "white")
        self.inventory_surf.blit(inventory_txt, \
                ((self.inventory_surf.get_width() // 2 - inventory_txt.get_width() // 2) + 1, 1))
        # big splash surf
        self.big_splash_surf = pygame.Surface((800, 600), flags=SRCALPHA)
        self.big_splash_surf.fill("black")
        pygame.draw.rect(self.big_splash_surf, "magenta", self.big_splash_surf.get_rect(), 1)
        # game over button surf
        self.game_over_button_surf = pygame.Surface((200, 80), flags=SRCALPHA)
        self.game_over_button_surf.fill("black") 
        pygame.draw.rect(self.game_over_button_surf, "magenta", self.game_over_button_surf.get_rect(), 1)
        # processing surf
        self.processing_surf = self.hud_font.render("...processing...", True, "green", "black")
        # inventory slot surf
        self.slot_surf = pygame.Surface((700, HUD_FONT_SIZE + 8), flags=SRCALPHA)
        self.slot_surf.fill("black")
        pygame.draw.rect(self.slot_surf, "magenta", self.slot_surf.get_rect(), 1)
        # dude 1 sheets
        self.dude_1_sheet = pygame.image.load(DUDE_1_PATH)
        self.dude_1_sheet.convert_alpha()
        self.dude_1_knife_sheet = pygame.image.load(DUDE_1_KNIFE_PATH)
        self.dude_1_knife_sheet.convert_alpha()
        self.dude_1_pistol_sheet = pygame.image.load(DUDE_1_PISTOL_PATH)
        self.dude_1_pistol_sheet.convert_alpha()
        self.dude_1_longarm_sheet = pygame.image.load(DUDE_1_LONGARM_PATH)
        self.dude_1_longarm_sheet.convert_alpha()
        # dude 2 sheets
        self.dude_2_sheet = pygame.image.load(DUDE_2_PATH)
        self.dude_2_sheet.convert_alpha()
        self.dude_2_knife_sheet = pygame.image.load(DUDE_2_KNIFE_PATH)
        self.dude_2_knife_sheet.convert_alpha()
        self.dude_2_pistol_sheet = pygame.image.load(DUDE_2_PISTOL_PATH)
        self.dude_2_pistol_sheet.convert_alpha()
        self.dude_2_longarm_sheet = pygame.image.load(DUDE_2_LONGARM_PATH)
        self.dude_2_longarm_sheet.convert_alpha()
        self.dude_2_ko_sheet = pygame.image.load(DUDE_2_KO_PATH)
        self.dude_2_ko_sheet.convert_alpha()
        self.dude_2_dead_sheet = pygame.image.load(DUDE_2_DEAD_PATH)
        self.dude_2_dead_sheet.convert_alpha()
        # pillar 1 sheet
        self.pillar_1_sheet = pygame.image.load(PILLAR_1_PATH)
        self.pillar_1_sheet.convert_alpha()
        # terminal sheet
        self.terminal_sheet = pygame.image.load(TERMINAL_PATH)
        self.terminal_sheet.convert_alpha()
        # floor 1 sheet
        self.floor_1_sheet = pygame.image.load(FLOOR_1_PATH)
        self.floor_1_sheet.convert_alpha()
        # tree 1 sheet
        self.tree_1_sheet = pygame.image.load(TREE_1_PATH)
        self.tree_1_sheet.convert_alpha()
        # outside sheet
        self.outside_sheet = pygame.image.load(OUTSIDE_PATH)
        self.outside_sheet.convert_alpha()
        # knife sheet
        self.knife_sheet = pygame.image.load(KNIFE_PATH)
        self.knife_sheet.convert_alpha()
        # pistol sheet
        self.pistol_sheet = pygame.image.load(PISTOL_PATH)
        self.pistol_sheet.convert_alpha()
        # longarm sheet
        self.longarm_sheet = pygame.image.load(LONGARM_PATH)
        self.longarm_sheet.convert_alpha()
        # grenade sheet
        self.grenade_sheet = pygame.image.load(GRENADE_PATH)
        self.grenade_sheet.convert_alpha()
        # goggles sheet
        self.goggles_sheet = pygame.image.load(GOGGLES_PATH)
        self.goggles_sheet.convert_alpha()
        # stim sheet
        self.stim_sheet = pygame.image.load(STIM_PATH)
        self.stim_sheet.convert_alpha()
        # ammo sheet
        self.ammo_sheet = pygame.image.load(AMMO_PATH)
        self.ammo_sheet.convert_alpha()
        # armor sheet
        self.armor_sheet = pygame.image.load(ARMOR_PATH)
        self.armor_sheet.convert_alpha()
        # entity sheets
        self.entity_sheets = { 
            self.dude_1_sheet: {"frames": 4, "regular": {}}, 
            self.dude_1_knife_sheet: {"frames": 4, "regular": {}}, 
            self.dude_1_pistol_sheet: {"frames": 4, "regular": {}}, 
            self.dude_1_longarm_sheet: {"frames": 1, "regular": {}}, 
            self.dude_2_sheet: {"frames": 4, "regular": {}}, 
            self.dude_2_knife_sheet: {"frames": 4, "regular": {}}, 
            self.dude_2_pistol_sheet: {"frames": 4, "regular": {}}, 
            self.dude_2_longarm_sheet: {"frames": 1, "regular": {}}, 
            self.dude_2_ko_sheet: {"frames": 1, "regular": {}}, 
            self.dude_2_dead_sheet: {"frames": 1, "regular": {}}, 
            self.terminal_sheet: {"frames": 1, "regular": {}},
            self.patrol_path_surf: {"frames": 1, "regular": {}},
            self.knife_sheet: {"frames": 1, "regular": {}},
            self.pistol_sheet: {"frames": 1, "regular": {}},
            self.longarm_sheet: {"frames": 1, "regular": {}},
            self.grenade_sheet: {"frames": 1, "regular": {}},
            self.goggles_sheet: {"frames": 1, "regular": {}},
            self.stim_sheet: {"frames": 1, "regular": {}},
            self.ammo_sheet: {"frames": 1, "regular": {}},
            self.armor_sheet: {"frames": 1, "regular": {}},
            self.smoke_sheet: {"frames": 6, "regular": {}},
        }
        for _, v in self.keycards.items():
            self.entity_sheets[v] = {"frames": 1, "regular": {}}
        for sheet in self.entity_sheets.keys():
            for direction in list(filter(lambda x: x != "wait", DIRECTIONS.keys())):
                frames = []
                for index in range(self.entity_sheets[sheet]["frames"]):
                    frames.append(grab_cell_from_sheet(sheet, index, direction))
                self.entity_sheets[sheet]["regular"][direction] = frames
        self.turn = 0
        # loading screen fluffers
        self.fluffers = [sheet for sheet in self.entity_sheets.keys()]
        loading_screen(self.loader, "...initializing game...", fluffers=self.fluffers)
        self.main_scene = Scene(self)
        self.current_scene = self.main_scene

    def game_loop(self):
        while self.running: 
            if not self.current_scene.animation_lock:
                self.current_scene.update()
                self.current_scene.draw()
            self.clock.tick(FPS)

if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption("Base 34 <version {}>".format(VERSION))
    icon = pygame.image.load(WINDOW_ICON_PATH)
    pygame.display.set_icon(icon)
    flags = pygame.FULLSCREEN
    desktop_size = pygame.display.get_desktop_sizes()[0]
    pygame.display.set_mode((desktop_size[0], desktop_size[1]), flags) 
    pygame.mixer.quit()
    pygame.key.set_repeat(100) 
    game = Game()
    game.game_loop()
    pygame.quit()

