'''initializes and specifies game constants'''
from enum import Enum

from typing import Optional, List




'''
----------------------
General Game Constants
----------------------
'''

class Team(Enum):
    '''Team names'''

    BLUE = 0  # Moves first
    RED = 1  # Moves second

class GameConstants:
    '''Contains all the game related constants for balancing and finetuning'''

    STARTING_BALANCE = 10  # Starting coins per team
    PASSIVE_COINS_PER_TURN = 1  # Number of coins gained per turn

    INITIAL_TIME_POOL = 10
    ADDITIONAL_TIME_PER_TURN = 0.01

    SELL_HEALTH_PERCENT = 0.75

    BUILDING_SELL_DISCOUNT = 0.5
    UNIT_SELL_DISCOUNT = 0.5

    # Multiplies own/opponent's balance by that amount
    RAT_OWN_FARM_DAMAGE_MULTIPLIER = 0.8
    RAT_OPPONENT_FARM_DAMAGE_MULTIPLIER = 0.9





'''
-------------
Map Constants
-------------
'''


class Tile(Enum):
    '''Tile contains all the tiles types of the map'''

    def __init__(self, tile_id: int, movement_cost: int):
        self.tile_id = tile_id
        self.movement_cost = movement_cost

    #tile id for identification, and movement cost for units that can go on each tile type
    ERROR = (0, 0)
    MOUNTAIN = (1, 2)
    GRASS = (2, 1)
    SAND = (3, 2)
    WATER = (4, 1)
    BRIDGE = (5, 1)




class Direction(Enum):
    '''Directions for movement purposes'''

    def __init__(self, dx: int, dy: int):
        self.dx = dx
        self.dy = dy

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    UP_LEFT = (-1, 1)
    UP_RIGHT = (1, 1)
    DOWN_LEFT = (-1, -1)
    DOWN_RIGHT = (1, -1)

    STAY = (0, 0)





'''
-----------------------------------------
Object Class Starting Stats and Constants
-----------------------------------------
'''


class BuildingType (Enum):

    def __init__(self, health: int, cost: int, attack_range: int, damage_range:int, cooldown: int, damage: int, defense: int, actions_per_turn: int, coins_per_turn: int, spawnable: bool, placeable_tiles: Optional[List[Tile]]):
        self.health = health
        self.cost = cost
        self.attack_range = attack_range
        self.damage_range = damage_range
        self.cooldown = cooldown
        self.damage = damage

        self.defense = defense

        self.actions_per_turn = actions_per_turn

        self.coins_per_turn = coins_per_turn

        self.spawnable = spawnable # Can spawn units if True

        if placeable_tiles is None: #typical land building
            self.placeable_tiles = [Tile.GRASS, Tile.SAND]
        else:
            self.placeable_tiles = placeable_tiles #tiles that it can be placed on


    #in the order of (health, cost, attack_range, damage_range, cooldown, damage, defense, actions_per_turn, coins_per_turn, spawnable, placeable_tiles)

    MAIN_CASTLE = (30, -1, 0, 1, 0, 0, 0, 1, 0, True, None)
    PORT = (20, 25, 0, 1, 0, 0, 0, 1, 0, True, [Tile.WATER, Tile.BRIDGE])
    EXPLORER_BUILDING = (20, 100, 0, 0, 1, 0, 0, 0, 0, False, None)

    FARM_1 = (10, 30, 0, 1, 0, 0, 0, 1, 1, True, None)
    FARM_2 = (15, 60, 0, 1, 0, 0, 0, 1, 2, True, None)
    FARM_3 = (20, 90, 0, 1, 0, 0, 0, 1, 3, True, None)




class UnitType (Enum):

    def __init__(self, health: int, cost: int, attack_range: int, cooldown: int, damage: int, defense: int, actions_per_turn: int, move_range: int, damage_range: int, heal_amount: int, spawnable_buildings: Optional[List[BuildingType]], walkable_tiles: Optional[List[Tile]]):
        self.health = health
        self.cost = cost
        self.attack_range = attack_range # how far a unit can reach to attack
        self.cooldown = cooldown
        self.damage = damage
        self.defense = defense
        self.actions_per_turn = actions_per_turn
        self.move_range = move_range
        self.damage_range = damage_range # 1 is single target, 2+ is area
        self.spawnable_buildings = spawnable_buildings # None means all buildings

        self.heal_amount = heal_amount

        if walkable_tiles is None:
            self.walkable_tiles = [Tile.GRASS, Tile.SAND, Tile.BRIDGE]
        else:
            self.walkable_tiles = walkable_tiles


    #in the order of (health, cost, attack range, cooldown, damage, defense, actions_per_turn, move_range, damage range, heal_amount, [spawnable buildings])

    # Land meele tier 1
    KNIGHT = (10, 1, 1, 1, 1, 1, 1, 1, 0, 0, None, None)
    # Land meele tier 2
    WARRIOR = (10, 2, 1, 1, 2, 2, 1, 1, 0, 0, None, None)
    # Land meele tier 3
    SWORDSMAN = (10, 4, 1, 1, 3, 3, 1, 1, 0, 0, None, None)
    # Land meele, high health and defense
    DEFENDER = (15, 3, 1, 1, 1, 2, 1, 1, 0, 0, None, None)
    # The catapult, large ranged attack (6) unit that deals small damage
    CATAPULT = (10, 4, 4, 1, 1, 1, 1, 1, 0, 0, None, None)

    # Water meele tier 1
    SAILOR = (10, 1, 1, 1, 1, 1, 1, 1, 0, 0, [BuildingType.PORT], [Tile.WATER, Tile.BRIDGE])
    # Water meele tier 2
    RAIDER = (10, 2, 1, 1, 2, 2, 1, 1, 0, 0, [BuildingType.PORT], [Tile.WATER, Tile.BRIDGE])
    # Water meele tier 3
    CAPTAIN = (10, 4, 1, 1, 3, 3, 1, 1, 0, 0, [BuildingType.PORT], [Tile.WATER, Tile.BRIDGE])




    GALLEY = (15, 3, 1, 1, 1, 2, 1, 1, 0, 0, [BuildingType.PORT], [Tile.WATER, Tile.BRIDGE])

    EXPLORER = (1, 10, 0, 1, 0, 0, 1, 2, 0, 0, [BuildingType.MAIN_CASTLE], [Tile.GRASS, Tile.SAND, Tile.BRIDGE, Tile.MOUNTAIN, Tile.WATER])

    ENGINEER = (5, 2, 0, 0, 0, 0, 1, 1, 0, 0, None, [Tile.GRASS, Tile.SAND, Tile.BRIDGE, Tile.WATER])

    # Tier 1
    LAND_HEALER_1 = (10, 3, 2, 1, 0, 1, 1, 2, 1, 5, None, None)
    WATER_HEALER_1 = (10, 3, 2, 1, 0, 1, 1, 2, 1, 5, [BuildingType.PORT], [Tile.WATER, Tile.BRIDGE])
    # Tier 2
    LAND_HEALER_2 = (10, 4, 2, 1, 0, 1, 1, 2, 1, 6, None, None)
    WATER_HEALER_2 = (10, 4, 2, 1, 0, 1, 1, 2, 1, 6, [BuildingType.PORT], [Tile.WATER, Tile.BRIDGE])
    # Tier 3
    LAND_HEALER_3 = (10, 5, 2, 1, 0, 1, 1, 2, 1, 7, None, None)
    WATER_HEALER_3 = (10, 5, 2, 1, 0, 1, 1, 2, 1, 7, [BuildingType.PORT], [Tile.WATER, Tile.BRIDGE])


    RAT = (5, 10, 0, 1, 0, 0, 1, 2, 0, 0, [BuildingType.MAIN_CASTLE], [Tile.GRASS, Tile.SAND, Tile.BRIDGE, Tile.MOUNTAIN])






'''
-----------------------
Pygame Render Constants

NOTE: Not for player use
-----------------------
'''

class MapRender: 

    BORDER_COLOR = (0, 0, 0) # black
    TILE_SIZE = 20 # Can change


class TileColors:
    '''Tile colors for visualization in pygame

    Note: no black, as that is error
    '''

    #dict for easy access
    colors = {
        Tile.ERROR : (0, 0, 0), #white
        Tile.MOUNTAIN : (128, 128, 128), #gray
        Tile.GRASS : (0, 128, 0), #green
        Tile.SAND : (186, 142, 35), #yellow
        Tile.WATER : (173, 216, 230), #light blue
        Tile.BRIDGE : (222, 184, 135), #brown
    }



class BuildingRender:
    
    text = {
        BuildingType.MAIN_CASTLE : 'M',
        BuildingType.PORT: 'P',
        BuildingType.EXPLORER_BUILDING: 'E',
        BuildingType.FARM_1 : 'F',
        BuildingType.FARM_2 : 'F',
        BuildingType.FARM_3 : 'F',
    }

    BUILDING_COLOR = {
        Team.RED : (255, 127, 127), #light red
        Team.BLUE : (173, 216, 230) # light blue
    }

class UnitRender:
    
    text = {
        UnitType.KNIGHT : 'K',
        UnitType.ENGINEER: 'N',
        UnitType.EXPLORER: 'X',
        UnitType.LAND_HEALER_1: 'H',
        UnitType.LAND_HEALER_2: 'H',
        UnitType.LAND_HEALER_3: 'H',
        UnitType.SAILOR: 'S',
        UnitType.GALLEY: 'G',
        UnitType.WATER_HEALER_1: 'H',
        UnitType.WATER_HEALER_2: 'H',
        UnitType.WATER_HEALER_3: 'H',
        UnitType.WARRIOR: 'W',
        UnitType.SWORDSMAN: 'M',
        UnitType.DEFENDER: 'D',
        UnitType.CATAPULT: 'C',
        UnitType.RAIDER: 'R',
        UnitType.CAPTAIN: 'P',
    }

    UNIT_COLOR = {
        Team.RED : (139, 0, 0), # dark red
        Team.BLUE : (0, 0, 132) # dark blue
    }