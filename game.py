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
        self.debug = False
        self.show_bldg_numbers = False
        self.show_move_dscore = False
        self.movement_range_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.movement_range_cell_surf.set_colorkey(ALPHA_KEY)
        self.movement_range_cell_surf.fill(ALPHA_KEY)
        self.movement_range_cell_surf.fill(COLOR_MOVEMENT_RANGE)
        pygame.draw.rect(self.movement_range_cell_surf, "green", self.movement_range_cell_surf.get_rect(), 1)
        alert_txt = self.title_font.render("!", True, "yellow") 
        self.alert_base = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.alert_base.set_colorkey(ALPHA_KEY)
        self.alert_base.fill(ALPHA_KEY)
        self.alert_base.blit(alert_txt, (self.alert_base.get_width() // 2 - alert_txt.get_width() // 2, 1))
        huh_txt = self.title_font.render("?", True, "yellow") 
        self.huh_base = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.huh_base.set_colorkey(ALPHA_KEY)
        self.huh_base.fill(ALPHA_KEY)
        self.huh_base.blit(huh_txt, (self.huh_base.get_width() // 2 - huh_txt.get_width() // 2, 1))
        loot_txt = self.title_font.render("$", True, "yellow") 
        self.loot_base = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.loot_base.set_colorkey(ALPHA_KEY)
        self.loot_base.fill(ALPHA_KEY)
        self.loot_base.blit(loot_txt, (self.loot_base.get_width() // 2 - loot_txt.get_width() // 2, 1))
        self.patrol_path_surf = pygame.image.load(PATROL_PATH_PATH)
        self.patrol_path_surf.convert_alpha()
        self.patrol_end_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.patrol_end_surf.fill((200, 0, 0, 120))
        pygame.draw.rect(self.patrol_end_surf, "red", self.patrol_path_surf.get_rect(), 1)
        self.enemy_los_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.enemy_los_cell_surf.set_colorkey(ALPHA_KEY)
        self.enemy_los_cell_surf.fill(ALPHA_KEY)
        self.enemy_los_cell_surf.fill(COLOR_ENEMY_LOS)
        self.foggy_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.foggy_cell_surf.set_colorkey(ALPHA_KEY)
        self.foggy_cell_surf.fill(ALPHA_KEY)
        self.foggy_cell_surf.fill(COLOR_FOG)
        self.unseen_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.unseen_cell_surf.set_colorkey(ALPHA_KEY)
        self.end_turn_surf = pygame.Surface((SIDE_HUD_WIDTH, HUD_FONT_SIZE + 2), flags=SRCALPHA)
        self.end_turn_surf.fill(COLOR_HUD_RED)
        pygame.draw.rect(self.end_turn_surf, "magenta", self.end_turn_surf.get_rect(), 1)
        self.big_splash_surf = pygame.Surface((800, 600), flags=SRCALPHA)
        self.big_splash_surf.fill("black")
        pygame.draw.rect(self.big_splash_surf, "magenta", self.big_splash_surf.get_rect(), 1)
        self.game_over_button_surf = pygame.Surface((200, 80), flags=SRCALPHA)
        self.game_over_button_surf.fill("black")
        pygame.draw.rect(self.game_over_button_surf, "magenta", self.game_over_button_surf.get_rect(), 1)
        end_turn_txt = self.hud_font.render("END TURN", True, "white")
        self.end_turn_surf.blit(end_turn_txt, \
                ((self.end_turn_surf.get_width() // 2 - end_turn_txt.get_width() // 2) + 1, 1))
        self.processing_surf = self.hud_font.render("...processing...", True, "green", "black")
        self.dude_1_sheet = pygame.image.load(DUDE_1_PATH)
        self.dude_1_sheet.convert_alpha()
        self.dude_2_sheet = pygame.image.load(DUDE_2_PATH)
        self.dude_2_sheet.convert_alpha()
        self.fog_sheet = pygame.image.load(FOG_PATH)
        self.fog_sheet.convert_alpha()
        self.pillar_1_sheet = pygame.image.load(PILLAR_1_PATH)
        self.pillar_1_sheet.convert_alpha()
        self.terminal_sheet = pygame.image.load(TERMINAL_PATH)
        self.terminal_sheet.convert_alpha()
        self.floor_1_sheet = pygame.image.load(FLOOR_1_PATH)
        self.floor_1_sheet.convert_alpha()
        self.tree_1_sheet = pygame.image.load(TREE_1_PATH)
        self.tree_1_sheet.convert_alpha()
        self.outside_sheet = pygame.image.load(OUTSIDE_PATH)
        self.outside_sheet.convert_alpha()
        self.entity_sheets = { 
            self.dude_1_sheet: {"frames": 4, "regular": {}}, 
            self.dude_2_sheet: {"frames": 4, "regular": {}}, 
            self.terminal_sheet: {"frames": 1, "regular": {}},
            self.patrol_path_surf: {"frames": 1, "regular": {}},
        }
        for sheet in self.entity_sheets.keys():
            for direction in list(filter(lambda x: x != "wait", DIRECTIONS.keys())):
                frames = []
                for index in range(self.entity_sheets[sheet]["frames"]):
                    frames.append(grab_cell_from_sheet(sheet, index, direction))
                self.entity_sheets[sheet]["regular"][direction] = frames
        self.turn = 0
        self.fluffers = [
            self.dude_1_sheet,
            self.dude_2_sheet,
            self.alert_base,
            self.huh_base,
            self.terminal_sheet,
        ]
        loading_screen(self.loader, "...initializing game...", fluffers=self.fluffers)
        self.main_scene = Scene(self)
        self.current_scene = self.main_scene

    def game_loop(self):
        while self.running: 
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

