'''Helper class for pygame rendering'''

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" #stop the command line pygame printout
import pygame
import pygame.font as font

from src.map import Map
from src.game_constants import Team, MapRender, BuildingRender, UnitRender
from src.buildings import Building
from src.units import Unit

class Renderer:
    '''Contains helper functions that draws in pygame what is required'''

    def __init__(self, map: Map):

        self.map = map

        self.width = map.width
        self.height = map.height


    def get_screen_coords(self, x: int, y: int) -> tuple[tuple[int, int], tuple[int, int]]:
        '''
        Helper unction to get screen coordinates of each map tile in the form ((left, top), (width, height))
        '''

        left = x * MapRender.TILE_SIZE
        top = (self.height - 1 - y) * MapRender.TILE_SIZE
        return ((left, top), (MapRender.TILE_SIZE, MapRender.TILE_SIZE))


    def init_render(self):
        '''Initializes the pygame window'''
        pygame.init()
        pygame.display.set_caption("Game State Visualizer")
        self.screen = pygame.display.set_mode((self.width * MapRender.TILE_SIZE, self.height * MapRender.TILE_SIZE + 50)) #+50 for the text at the bottom

    def map_render(self):
        '''Renders the map background'''

        #all of the background is white
        self.screen.fill((255, 255, 255))

        #draw tiles and map
        for x in range(self.width):
            for y in range(self.height):

                color = self.map.get_tile_color(x, y)
                pygame.draw.rect(self.screen, color, self.get_screen_coords(x, y))

        #draw vertical lines for grid
        for x in range(self.map.width+1):
            bottom = (x*MapRender.TILE_SIZE, 0)
            top = (x*MapRender.TILE_SIZE, self.height*MapRender.TILE_SIZE)

            pygame.draw.line(self.screen, MapRender.BORDER_COLOR, bottom, top)

        #draw horizontal lines for grid
        for y in range(self.map.height+1):
            left = (0, y*MapRender.TILE_SIZE)
            right = (self.width*MapRender.TILE_SIZE, y*MapRender.TILE_SIZE)
            pygame.draw.line(self.screen, MapRender.BORDER_COLOR, left, right)


    def building_render(self, building: Building):
        '''Renders a building on the screen'''

        render_text = BuildingRender.text[building.type]
        render_color = BuildingRender.BUILDING_COLOR[building.team]

        text = font.SysFont('Comic Sans MS', 10).render(render_text, True, render_color)

        (x1, y1), area = self.get_screen_coords(building.x, building.y)

        self.screen.blit(text, ((x1 + MapRender.TILE_SIZE//4, y1 + MapRender.TILE_SIZE//4), area))


    def unit_render(self, unit: Unit):
        '''Renders a unit on the screen'''

        render_text = UnitRender.text[unit.type]
        render_color = UnitRender.UNIT_COLOR[unit.team]

        text = font.SysFont('Comic Sans MS', 10).render(render_text, True, render_color)

        (x1, y1), area = self.get_screen_coords(unit.x, unit.y)

        self.screen.blit(text, ((x1 + MapRender.TILE_SIZE//4, y1 + MapRender.TILE_SIZE//4), area))
        

    

