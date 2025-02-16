''' helper geometry functions to help with maps '''

from src.map import Map
from typing import Optional
import ast
from src.game_constants import Tile

def process_map(file_name: str) -> Optional[Map]:

    with open(file_name, 'r') as f:
        arrAsStr = f.readline()

    arr = ast.literal_eval(arrAsStr)

    height = len(arr)
    width = len(arr[0])

    blue_castle_loc = (-1, -1)
    red_castle_loc = (-1, -1)

    for i in range(height): 
        for j in range(width):
            if arr[i][j] == 'BLUE CASTLE':
                blue_castle_loc = (i, j)
                arr[i][j] = 'GRASS'

            if arr[i][j] == 'RED CASTLE':
                red_castle_loc = (i, j)
                arr[i][j] = 'GRASS'

    tiles = list(map(lambda row : list(map(lambda x: string_to_tile(x), row)), arr))

    return Map(width, height, tiles, blue_castle_loc, red_castle_loc)

    


def string_to_tile(tile_str : str) -> Tile:

    if tile_str == "GRASS":
        return Tile.GRASS

    if tile_str == "MOUNTAIN":
        return Tile.MOUNTAIN

    if tile_str == "SAND":
        return Tile.SAND

    if tile_str == "WATER":
        return Tile.WATER

    if tile_str == "BRIDGE":
        return Tile.BRIDGE

    return Tile.ERROR