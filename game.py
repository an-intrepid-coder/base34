import pygame
from scene import *
from entity import *
from constants import *

class Game: 
    def __init__(self):
        self.hud_font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
        self.GAME_UPDATE_TICK = pygame.event.custom_type()
        self.MOVER_CHECK = pygame.event.custom_type()
        self.running = True
        self.screen = pygame.display.get_surface() 
        self.MAP_DISPLAY_SIZE = (self.screen.get_width() - SIDE_HUD_WIDTH, self.screen.get_height() - CONSOLE_HEIGHT)
        self.screen_wh_cells_tuple = (self.MAP_DISPLAY_SIZE[0] // CELL_SIZE, self.MAP_DISPLAY_SIZE[1] // CELL_SIZE)
        self.screen.set_colorkey(ALPHA_KEY)
        self.clock = pygame.time.Clock()
        self.debug = False
        self.movement_range_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.movement_range_cell_surf.set_colorkey(ALPHA_KEY)
        self.movement_range_cell_surf.fill(ALPHA_KEY)
        pygame.draw.rect(self.movement_range_cell_surf, COLOR_MOVEMENT_RANGE, self.movement_range_cell_surf.get_rect(), 1)
        self.foggy_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.foggy_cell_surf.set_colorkey(ALPHA_KEY)
        self.foggy_cell_surf.fill(ALPHA_KEY)
        self.foggy_cell_surf.fill((60, 60, 60))
        self.unseen_cell_surf = pygame.Surface((CELL_SIZE, CELL_SIZE), flags=SRCALPHA)
        self.unseen_cell_surf.set_colorkey(ALPHA_KEY)
        self.end_turn_surf = pygame.Surface((SIDE_HUD_WIDTH, HUD_FONT_SIZE + 2), flags=SRCALPHA)
        self.end_turn_surf.fill((180, 0, 0))
        pygame.draw.rect(self.end_turn_surf, "magenta", self.end_turn_surf.get_rect(), 1)
        end_turn_txt = self.hud_font.render("END TURN", True, "white")
        self.end_turn_surf.blit(end_turn_txt, \
                ((self.end_turn_surf.get_width() // 2 - end_turn_txt.get_width() // 2) + 1, 1))
        self.dude_1_sheet = pygame.image.load(DUDE_1_PATH)
        self.dude_1_sheet.convert_alpha()
        self.entity_sheets = { 
            self.dude_1_sheet: {"frames": 2, "regular": {}}, # maybe something for weapons and such later TODO
        }
        for sheet in self.entity_sheets.keys():
            for direction in list(filter(lambda x: x != "wait", DIRECTIONS.keys())):
                frames = []
                for index in range(self.entity_sheets[sheet]["frames"]):
                    frames.append(grab_cell_from_sheet(sheet, index, direction))
                self.entity_sheets[sheet]["regular"][direction] = frames
        self.main_scene = Scene(self)
        self.current_scene = self.main_scene
        self.turn = 0

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

