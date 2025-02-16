''' Details the map '''

from src.exceptions import GameException

from src.game_constants import Tile, TileColors, Team
from typing import List, Tuple

class Map:
    '''
    Is a map that details the environment

    Convention: bottom-left is [0][0], top-right is [width-1][height-1]

    self.tiles[x][y]
                    y == height  ----->
    x == width    [[# # # # # # # #],
        |          [# # # # # # # #],
        |          [# # # # # # # #],
        |          [# # # # # # # #],
        v          [# # # # # # # #]]

    The actual map is rotated counterclockwise, note for rendering

       ^           # # # # #
       |           # # # # #
       |           # # # # #
    y == height    # # # # #
                   # # # # #
                   # # # # #
                   # # # # #
                   # # # # #

                   x == width -->


    '''

    def __init__(self, width=50, height=50, tiles: List[List[Tile]]=None, blue_castle_loc: Tuple[int, int]= (-1, -1), red_castle_loc: Tuple[int, int]= (-1, -1)):
        self.width = width
        self.height = height
        
        # hardcoded map for now
        self.tiles = tiles
        if self.tiles is None:
            self.tiles = [[Tile.GRASS for y in range(self.height)] for x in range(self.width)]

        self.blue_castle_loc = blue_castle_loc
        self.red_castle_loc = red_castle_loc
        self.castle_locs = {
            Team.RED : red_castle_loc,
            Team.BLUE : blue_castle_loc,
        }

        if not self.in_bounds(*blue_castle_loc) or not self.in_bounds(*red_castle_loc):
            raise GameException('Given main castle locations invalid')

    def in_bounds(self, x: int, y: int) -> bool:
        '''
        checks if self.tiles[x][y] is in bounds,
        noting that x is "width" and y is "height"
        '''
        return 0 <= x and x < self.width \
           and 0 <= y and y < self.height

    def is_tile_type(self, x: int, y: int, tile_type: Tile) -> bool:
        '''checks if location (x, y) on the map is of a certain tile_type'''
        
        if not self.in_bounds(x, y):
            return False
        
        return self.tiles[x][y] == tile_type

    def get_tile_color(self, x, y) -> Tuple[int, int, int]:
        '''Accesses the dict defined in Tile_Colors, and gets the tile colors'''

        tile_type = self.tiles[x][y]

        #error checking
        if tile_type not in TileColors.colors:
            return (255, 255, 255)
        
        return TileColors.colors[tile_type]
    
    def to_dict(self):
        """
        Converts the map into a dictionary representation, for json replay file
        """
        return {
            "width": self.width,
            "height": self.height,
            "tiles": [[tile.name if hasattr(tile, 'name') else str(tile) for tile in row] for row in self.tiles],
            # "blue_castle_loc": self.blue_castle_loc,
            # "red_castle_loc": self.red_castle_loc
        }
    
    def to_2d_list(self):
        """
        Converts the map into a 2D list of tile names.
        """
        return [[tile.name if hasattr(tile, 'name') else str(tile) for tile in row] for row in self.tiles]