import pygame
from constants import *
from sheets import *
from random import choice, randint

print("...initializing unique loading splash...")

w, h = LOADER_SIZE[0] // CELL_SIZE, LOADER_SIZE[1] // CELL_SIZE
loading_state = [[randint(0, 1) == 1 for _ in range(h)] for _ in range(w)]

def random_orientation():
    return choice(list(filter(lambda d: d != "wait", DIRECTIONS.keys())))

def living_neighbors_of(state, xy) -> list:
    living_neighbors = 0
    for k, v in DIRECTIONS.items():
        if k == "wait":
            continue
        x, y = xy[0] + v[0], xy[1] + v[1]
        if x >= 0 and y >= 0 and x < w and y < h:
            if state[x][y]:
                living_neighbors += 1
    return living_neighbors

def new_loading_state(state) -> list:
    loading_state = []
    for x in range(w):
        loading_state.append([])
        for y in range(h):
            alive = state[x][y]
            living_neighbors = living_neighbors_of(state, (x, y))
            if (alive and (living_neighbors == 2 or living_neighbors == 3)) \
                or (not alive and living_neighbors == 3): 
                loading_state[x].append(True)
            else:
                loading_state[x].append(False)
    return loading_state

generations = 34
for _ in range(generations):
    loading_state = new_loading_state(loading_state)

def loading_screen(bg, msg, fluffers=None, advance_state=True):  
    global w, h, loading_state                                 
    if fluffers is not None:                                    
        mid = pygame.Surface((600, 400), flags=SRCALPHA)
        mid.fill((50, 50, 50, 160))
        pygame.draw.rect(mid, "white", mid.get_rect(), 3)
        pos = (bg.get_width() // 2 - mid.get_width() // 2, bg.get_height() // 2 - mid.get_height() // 2)
        for x in range(w):
            for y in range(h):
                if loading_state[x][y]:
                    sheet = choice(fluffers)
                    img = grab_cell_from_sheet(sheet, 0, random_orientation())
                    bg.blit(img, (x * CELL_SIZE, y * CELL_SIZE))
                pygame.draw.rect(bg, "black", (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)
        bg.blit(mid, pos)
    title_font = pygame.font.Font(FONT_PATH, TITLE_FONT_SIZE)
    subtitle_font = pygame.font.Font(FONT_PATH, HUD_FONT_SIZE)
    desktop_size = pygame.display.get_desktop_sizes()[0]
    dw, dh = desktop_size
    screen = pygame.display.get_surface()
    surf = pygame.Surface(desktop_size)
    bg_final = pygame.transform.scale(bg, desktop_size)
    surf.blit(bg_final, (0, 0))
    lines = [
        title_font.render("BASE 34", True, "white", "black"),
        title_font.render("", True, "white", "black"),
        subtitle_font.render("<version {}>".format(VERSION), True, "white", "black"),
        title_font.render("", True, "white", "black"),
        title_font.render("", True, "white", "black"),
        subtitle_font.render("~-~-~-~-~-~-~-___SECTOR 34 GAMES___~-~-~-~-~-~-~-", True, "white", "black"),
        subtitle_font.render(msg, True, "white", "black"),
        subtitle_font.render("~-~-~-~-<Tactical Espionage Roguelike>~-~-~-~-~-~", True, "white", "black"),
    ]
    y = dh // 2 - ((len(lines) - 1) * lines[1].get_height() + lines[0].get_height()) // 2 
    for line in lines:
        x = dw // 2 - line.get_width() // 2
        surf.blit(line, (x, y))
        if line is lines[0]:
            y += lines[0].get_height()
        else:
            y += lines[1].get_height()
    screen.blit(surf, (0, 0))
    pygame.display.flip()

