'''
This file contains all the functions that a player can call in their bot
'''

import copy, math
from typing import List, Optional, Dict, Tuple

from src.exceptions import GameException

from src.game_constants import Team, UnitType, BuildingType, Direction, Tile
from src.map import Map

from src.units import Unit
from src.buildings import Building
from src.game_constants import GameConstants
from src.game_state import GameState


class RobotController:
    
    def __init__(self, team: Team, game_state: GameState):

        self.__team = team # Red team or Blue team
        self.__game_state = game_state # The shared game state


    '''
    ------------------------------------------
    General state information access functions
    ------------------------------------------
    '''

    def get_turn(self) -> int:
        '''Gets the current turn of the game'''
        return self.__game_state.turn

    def get_ally_team(self) -> Team:
        '''Gets player's team, returning either Team.RED or Team.BLUE'''
        return self.__team
    
    def get_enemy_team(self) -> Team:
        '''
        Returns opponent's team, returning either Team.RED or Team.BLUE
        Opponent's team will be the opposite of player's team
        '''
        return self.__game_state.get_opposite_team(self.__team)
    

    def get_map(self) -> Map:
        '''Returns a deep copy of the current map instance'''
        return copy.deepcopy(self.__game_state.map)
    

    def get_units(self, team: Team) -> List[Unit]:
        '''Gets a list of the specified team's available units'''
        return copy.deepcopy(list(self.__game_state.units[team].values()))
    
    def get_unit_ids(self, team: Team) -> List[int]:
        '''Gets a list of the specified team's available unit ids'''
        return list(self.__game_state.units[team].keys())


    def get_buildings(self, team: Team) -> List[Building]:
        '''Gets a list of the specified team's available buildings'''
        return copy.deepcopy(list(self.__game_state.buildings[team].values()))
    
    def get_building_ids(self, team: Team) -> List[Building]:
        '''Gets a list of the specified team's available building ids'''
        return list(self.__game_state.buildings[team].keys())
    

    def get_unit_placeable_map(self) -> List[List[bool]]:
        '''Returns a 2D boolean map that is True if an arbitrary unit can move to (x, y) and False if not'''
        return copy.deepcopy(self.__game_state.unit_placeable_map)


    def get_building_placeable_map(self) -> List[List[bool]]:
        '''Returns a 2D boolean map that is True if an arbitrary building can be placed on (x, y) and False if not'''
        return copy.deepcopy(self.__game_state.building_placeable_map)


    def get_balance(self, team: Team) -> int:
        '''Gets the gold balance of a certain team'''
        return self.__game_state.balance[team]
    

    def get_team_of_unit(self, unit_id: int) -> Optional[Team]:
        '''
        Gets the team that a unit belongs to
        Returns either Team.RED or Team.BLUE if unit_id is valid; None if not valid
        '''
        return self.__game_state.get_team_of_unit(unit_id)
    

    def get_team_of_building(self, building_id: int) -> Optional[Team]:
        '''
        Gets the team that a building belongs to
        Returns either Team.RED or Team.BLUE if unit_id is valid; None if not valid
        '''
        return self.__game_state.get_team_of_building(building_id)
    

    '''
    ------------------------------------------
    Object class manipulation helper functions
    ------------------------------------------
    '''

    def get_unit_from_id(self, unit_id: int) -> Optional[Unit]:
        '''
        Returns a copy of the unit given by its id
        '''
        return copy.deepcopy(self.__game_state.get_unit_from_id(unit_id))
    

    def get_building_from_id(self, building_id: int) -> Optional[Building]:
        '''
        Returns a copy of the building given by its id
        '''
        return copy.deepcopy(self.__game_state.get_building_from_id(building_id))
    

    def get_id_from_unit(self, unit: Unit) -> Tuple[Team, int]:
        '''
        Returns (unit team, unit ID) from a given unit
        '''
        return unit.team, unit.id
    
    def get_id_from_building(self, building: Building) -> Tuple[Team, int]:
        '''
        Returns the (building ID, building team) from a given building
        '''
        return building.team, building.id

        

    '''
    -------------------------
    Distance Helper Functions

    NOTE: we are using chessboard/chebyshev distance
    -------------------------
    '''

    def get_chebyshev_distance(self, x1: int, y1: int, x2: int, y2: int) -> int:
        '''
        Returns the chebyshev (chessboard) distance between (x1, y1) and (x2, y2)
        
        Chebyshev distance between two points is the maximum lateral distance along an axis.
        It is also the minimum number of moves in chess that a king needs to move from (x1, y1) to (x2, y2)
        '''

        return max(abs(x1 - x2), abs(y1 - y2))

    def chebyshev_distance_valid(self, x1: int, y1: int, x2: int, y2: int, radius: int) -> bool:
        ''' 
        Returns True if the chebyshev (chessboard) distance between (x1, y1) and (x2, y2) <= radius 
        '''
        
        if self.get_chebyshev_distance(x1, y1, x2, y2) <= radius:
            return True
        
        return False
    


    '''
    ------------------------------------------------------
    Sensing helper functions for unit/building maneuvering
    ------------------------------------------------------
    '''


    def sense_units_within_radius(self, team: Team, x: int, y: int, radius: int) -> List[Unit]:
        '''
        Returns a list of units of a given team within a certain radius from (x, y)

        Distance is calculated such that the chessboard/chebyshev distance between the unit and the point must be less than or equal to radius
        '''

        if radius < 0:
            raise GameException("Radius must be non-negative")

        in_range: List[Unit] = []

        for unit in self.__game_state.units[team].values():
            #if chebyshev distance between unit and (x, y) <= radius, then valid
            if self.chebyshev_distance_valid(unit.x, unit.y, x, y, radius):
                in_range.append(copy.deepcopy(unit))

        return in_range



    def sense_buildings_within_radius(self, team: Team, x: int, y: int, radius: int) -> List[Building]:
        '''
        Returns a list of buildings of a given team within a certain radius from (x, y)

        Distance is calculated such that the chessboard/chebyshev distance between the unit and the point must be less than or equal to radius
        '''

        if radius < 0:
            raise GameException("Radius must be non-negative")
        
        in_range: List[Building] = []

        for building in self.__game_state.buildings[team].values():
            #if chebyshev distance between building and (x, y) <= radius, then valid
            if self.chebyshev_distance_valid(building.x, building.y, x, y, radius):
                in_range.append(copy.deepcopy(building))

        return in_range

    def sense_objects_within_radius(self, team: Team, x: int, y: int, radius: int) -> Tuple[List[Unit], List[Building]]:
        '''
        Returns a tuple of ([given team's units within radius], [given team's buildings within radius]) within a certain radius from (x, y)
        
        Distance is calculated such that the euclidian distance between the object and the point must be less than or equal to radius
        '''
        return self.sense_units_within_radius(team, x, y, radius), self.sense_buildings_within_radius(team, x, y, radius)


    def sense_objects_within_unit_range(self, team: Team, unit_id: int) -> Tuple[List[Unit], List[Building]]:
        '''
        Returns a tuple of ([given team's units within radius], [given team's buildings within radius]) within the unit's range
        
        Distance is calculated such that the euclidian distance between the object and the point must be less than or equal to radius
        '''

        if unit_id not in self.__game_state.units[team]:
            print("sense_objects_within_unit_range(): Not valid unit_id")
            return ([], []) # returns nothing if unit_id is invalid
        
        unit = self.__game_state.units[team][unit_id]
        return self.sense_objects_within_radius(team, unit.x, unit.y, unit.range)


    def sense_objects_within_building_range(self, team: Team, building_id: int) -> Tuple[List[Unit], List[Building]]:
        '''
        Returns a tuple of ([given team's units within radius], [given team's buildings within radius]) within the building's range
        
        Distance is calculated such that the euclidian distance between the object and the point must be less than or equal to radius
        '''
        if building_id not in self.__game_state.buildings[team]:
            print("sense_objects_within_building_range(): Not valid building id")
            return ([], []) # returns nothing if building_id is invalid
        
        unit = self.__game_state.units[team][building_id]
        return self.sense_objects_within_radius(team, unit.x, unit.y, unit.range)


    '''
    ----------------------
    Spawn Functionalities
    ----------------------
    '''

    def can_spawn_unit(self, unit_type: UnitType, building_id: int) -> bool:
        '''
        Returns True if all are satisfied:
          - unit_type can be spawned from building
          - does not spawn on top of another unit
          - has sufficient funds to spawn unit
        False otherwise
        '''

        # get actual building object from game_state or raise exception if not available
        building = self.__game_state.get_building_from_id(building_id)

        # basic validity
        if building is None:
            print('can_spawn_unit(): invalid building id')
            return False

        #check if building's team is correct
        if building.team != self.__team:
            return False

        #checks if building can spawn unit_type (farms can spawn most ground units)
        if unit_type.spawnable_buildings is not None and building.type not in unit_type.spawnable_buildings:
            return False
        
        #checks for building spawnable
        if not building.spawnable:
            return False

        #checks for other units and if the position is valid for unit to be on
        if not self.__game_state.is_unit_placeable(unit_type, building.x, building.y):
            return False
        
        #checks for enough funds
        if self.__game_state.balance[self.__team] < unit_type.cost:
            return False
        
        return True

    def can_build_building(self, building_type: BuildingType, x: int, y: int) -> bool:
        '''
        Returns True if all are satisfied:
          - building_type can be placed on tile
          - is not placed on top of another building
          - has sufficient funds to place building
        False otherwise
        '''

        #checks if (x, y) are valid coordinates
        if not self.__game_state.map.in_bounds(x, y):
            print('can_build_building(): (x, y) given are out of bounds')
            return False

        #checks if building can be built
        if building_type.placeable_tiles is not None and self.__game_state.map.tiles[x][y] not in building_type.placeable_tiles:
            return False

        #checks for other units and tile type
        if not self.__game_state.is_building_placeable(building_type, x, y):
            return False
        
        #checks for enough funds
        if self.__game_state.balance[self.__team] < building_type.cost:
            return False
        
        #explorer building must be built 10 blocks away from main castle
        if building_type == BuildingType.EXPLORER_BUILDING and self.get_chebyshev_distance(x, y, self.__game_state.map.castle_locs[self.__team][0], self.__game_state.map.castle_locs[self.__team][1]) <= 10:
            return False
        
        return True


    def spawn_unit(self, unit_type: UnitType, building_id: int) -> bool:
        '''
        Attempts to spawn unit_type from building specified by building_id
        Returns True if successful spawn, else return False
        '''
    
        #check validity
        if not self.can_spawn_unit(unit_type, building_id):
            print("spawn_unit() called but can_spawn_unit() returned False")
            return False
        
        #spawn unit
        if not self.__game_state.spawn_unit(self.__team, unit_type, building_id):
            print("unit failed to spawn")
            return False
        
        # decrease balance
        self.__game_state.balance[self.__team] -= unit_type.cost

        return True


    def build_building(self, building_type: BuildingType, x: int, y: int) -> bool:
        
        #check validity
        if not self.can_build_building(building_type, x, y):
            print("build_building() called but can_build_building() returned False")
            return False
        
        #build building
        if not self.__game_state.place_building(self.__team, building_type, x, y):
            print("building failed to place because another building on tile or built on wrong tile type")
            return False

        #decrease balance
        self.__game_state.balance[self.__team] -= building_type.cost
        
        return True



    '''
    --------------------
    Sell Functionalities
    --------------------
    '''

    def sell_unit(self, unit_id: int) -> bool:
        '''
        Sells a unit for a discounted price
        Unit must be at least a certain level of health
        '''

        return self.__game_state.sell_unit(self.__team, unit_id)


    def sell_building(self, building_id: int) -> bool:
        '''
        Sells a buliding for a discounted price
        Building must be above a certain level of health
        '''

        return self.__game_state.sell_building(self.__team, building_id)



    def disband_unit(self, unit_id: int) -> bool:
        '''
        Deletes a unit from the game. The player does not gain any coins from this action. 

        Returns True for successful delete. False otherwise
        '''

        if unit_id not in self.__game_state.units[self.__team]:
            print('disband_unit(): Invalid unit_id')
            return False
        
        self.__game_state.delete_unit(self.__team, unit_id)
        return True
    

    def destroy_building(self, building_id: int) -> bool:
        '''
        Deletes a building from the game. The player does not gain any coins from this action.

        Returns True for successful delete. False otherwise
        '''

        if building_id not in self.__game_state.buildings[self.__team]:
            print('destroy_building(): Invalid building_id')
            return False
        
        if building_id == self.__game_state.main_castle_ids[self.__team]:
            print('You cannot destroy your own main castle!')
            return False
        
        self.__game_state.delete_building(self.__team, building_id)
        return True


    '''
    ----------------------
    Attack Functionalities

    NOTE: game mechanic that buildings cannot attack each other
    Buildings are primarily used for utility or defense, instead of offense

    NOTE: units gets 1 movement action and 1 attack action per turn
    ----------------------
    '''

    def can_unit_attack_unit(self, attacking_unit_id: int, target_unit_id: int) -> bool:
        '''
        Returns true if it is valid for the attacking unit to attack the target unit or at the target unit's location

        Attacking unit must be from player's team, and target unit must be from opponent's team
        '''

        # are ids valid?
        if attacking_unit_id not in self.__game_state.units[self.__team]:
            print("can_unit_attack_unit(): invalid attacking_unit_id")
            return False
        
        if target_unit_id not in self.__game_state.units[self.get_enemy_team()]:
            print("can_unit_attack_unit(): invalid target_unit_id")
            return False


        attacking_unit = self.__game_state.get_unit_from_id(attacking_unit_id)
        target_unit = self.__game_state.get_unit_from_id(target_unit_id)

        # basic validity
        if attacking_unit is None:
            print('can_unit_attack_unit(): invalid attacking unit id')
            return False
        
        if target_unit is None:
            print('can_unit_attack_unit(): invalid target unit id')
            return False


        # has unit attacked this turn?
        if attacking_unit.turn_actions_remaining <= 0:
            return False #cannot attack again


        # is target unit in range of attacking unit?
        if not self.chebyshev_distance_valid(attacking_unit.x, attacking_unit.y, target_unit.x, target_unit.y, attacking_unit.attack_range):
            return False

        return True

    
    def can_unit_attack_building(self, attacking_unit_id: int, target_building_id: int) -> bool:
        '''
        Returns True if a unit can attack a building

        Attacking unit must be from player's team, and target building must be from opponent's team
        '''

        # are ids valid?
        if attacking_unit_id not in self.__game_state.units[self.__team]:
            print("can_unit_attack_building(): invalid attacking_unit_id")
            return False
        
        if target_building_id not in self.__game_state.buildings[self.get_enemy_team()]:
            print("can_unit_attack_building(): invalid target_building_id")
            return False


        attacking_unit = self.__game_state.get_unit_from_id(attacking_unit_id)
        target_building = self.__game_state.get_building_from_id(target_building_id)


        # basic validity
        if attacking_unit is None:
            print('can_spawn_unit(): invalid attacking unit id')
            return False

        if target_building is None:
            print('can_unit_attack_building(): invalid target building id')
            return False

        # has unit attacked this turn?
        if attacking_unit.turn_actions_remaining <= 0:
            return False #cannot attack 2+ times a turn


        # is target building in range of attacking unit?
        if not self.chebyshev_distance_valid(attacking_unit.x, attacking_unit.y, target_building.x, target_building.y, attacking_unit.attack_range):
            return False

        return True
    
    def can_unit_attack_location(self, attacking_unit_id: int, x: int, y: int) -> bool:
        '''
        Returns True if a unit can attack a location

        This is mainly for area attacks. Single target attacks will target buildings first then units
        Attacking unit must be from player's team, and (x, y) must be valid
        '''

        # are ids valid?
        if attacking_unit_id not in self.__game_state.units[self.__team]:
            print("can_unit_attack_building(): invalid attacking_unit_id")
            return False
        
        # are locations valid?
        if not self.__game_state.map.in_bounds(x, y):
            print('can_unit_attack_location(): invalid (x, y) given')
            return False
        
        attacking_unit = self.__game_state.get_unit_from_id(attacking_unit_id)

        # basic validity
        if attacking_unit is None:
            print('can_unit_attack_location(): invalid attacking unit id')
            return False

        # has unit attacked this turn?
        if attacking_unit.turn_actions_remaining <= 0:
            return False #cannot attack 2+ times a turn

        # is target location in range of attacking unit?
        if not self.chebyshev_distance_valid(attacking_unit.x, attacking_unit.y, x, y, attacking_unit.attack_range):
            return False

        return True
    


    def can_building_attack_unit(self, attacking_building_id: int, target_unit_id: int) -> bool:
        '''
        Returns True if a building can attack a unit

        Attacking building must be from player's team, and target unit must be from opponent's team
        '''
        # are ids valid?
        if attacking_building_id not in self.__game_state.buildings[self.__team]:
            print("can_building_attack_unit(): invalid attacking_building_id")
            return False
        
        if target_unit_id not in self.__game_state.units[self.get_enemy_team()]:
            print("can_building_attack_unit(): invalid target_unit_id")
            return False


        attacking_building = self.__game_state.get_building_from_id(attacking_building_id)
        target_unit = self.__game_state.get_unit_from_id(target_unit_id)

        # basic validity
        if attacking_building is None:
            print('can_building_attack_unit(): invalid attacking building id')
            return False

        if target_unit is None:
            print('can_building_attack_unit(): invalid target unit id')
            return False

        # has unit attacked this turn?
        if attacking_building.turn_actions_remaining <= 0:
            return False #cannot attack again


        # is target unit in range of attacking unit?
        if not self.chebyshev_distance_valid(attacking_building.x, attacking_building.y, target_unit.x, target_unit.y, attacking_building.attack_range):
            return False

        return True


    def can_building_attack_location(self, attacking_building_id: int, x: int, y: int) -> bool:
        '''
        Returns True if a building can attack a location

        This is mainly for area attacks. Single target attacks will only target other units if available
        Attacking building must be from player's team, and target location (x, y) must be in range
        '''

        # are ids valid?
        if attacking_building_id not in self.__game_state.buildings[self.__team]:
            print("can_building_attack_location(): invalid attacking_building_id")
            return False
        
        if not self.__game_state.map.in_bounds(x, y):
            print('can_unit_attack_location(): invalid (x, y) given')
            return False


        attacking_building = self.__game_state.get_building_from_id(attacking_building_id)

        # basic validity
        if attacking_building is None:
            print('can_building_attack_location(): invalid attacking building id')
            return False

        # has unit attacked this turn?
        if attacking_building.turn_actions_remaining <= 0:
            return False #cannot attack again


        # is target unit in range of attacking unit?
        if not self.chebyshev_distance_valid(attacking_building.x, attacking_building.y, x, y, attacking_building.attack_range):
            return False

        return True


    def unit_attack_location(self, attacking_unit_id: int, x: int, y: int) -> bool:
        '''
        Unit from player's team attacks location
        
        There is no friendly fire, so 0 damage will be taken if attacking friendly units.
        Enemy units will deal [UnitType.defense] damage in retaliation if unit is in range.

        Will attack both enemy units and buildings within damage range

        Returns True if attack is successful, False otherwise
        '''
        #does nothing if single target/ranged attacks attacks an empty location

        #check attack validity
        if not self.can_unit_attack_location(attacking_unit_id, x, y):
            return False

        enemy_team = self.get_enemy_team()
        attacking_unit = self.__game_state.get_unit_from_id(attacking_unit_id)

        # basic validity
        if attacking_unit is None: 
            return False


        # get all opponents within damage range
        #list of ids
        opponent_units_hit: List[int] = []
        opponent_buildings_hit: List[int] = []


        #sense all opponents hit
        for unit in self.__game_state.units[enemy_team].values():
            #if chebyshev distance between unit and target <= damage range, then hit
            if self.chebyshev_distance_valid(unit.x, unit.y, x, y, attacking_unit.damage_range):
                opponent_units_hit.append(unit.id)

        for building in self.__game_state.buildings[enemy_team].values():
            #if chebyshev distance between unit and target <= damage range, then hit
            if self.chebyshev_distance_valid(building.x, building.y, x, y, attacking_unit.damage_range):
                opponent_buildings_hit.append(building.id)

        #unit actions per turn decrement
        attacking_unit.turn_actions_remaining -= 1

        #damage opponent's units
        dead_units = [] #indices to delete
        for i in range(len(opponent_units_hit)):
            unit_id_hit = opponent_units_hit[i]
            #if opponent unit killed, then delete it from the list because they cannot retaliate
            if self.__game_state.damage_unit(unit_id_hit, attacking_unit.damage):
                dead_units.append(i) #delete it here to not mess up the indexing

        for i in dead_units:
            del opponent_units_hit[i]


        #damage opponent's buildings
        dead_buildings = [] #indices to delete
        for i in range(len(opponent_buildings_hit)):
            building_id_hit = opponent_buildings_hit[i]
            #if opponent building defeated, then delete from the list because they cannot retaliate
            if self.__game_state.damage_building(building_id_hit, attacking_unit.damage):
                dead_buildings.append(i)

        for i in dead_buildings:
            del opponent_buildings_hit[i]



        #retaliation: damage player's unit if opponent is not killed and player in range
        for enemy_unit_id in opponent_units_hit:
            enemy_unit = self.__game_state.get_unit_from_id(enemy_unit_id)

            # basic validity
            if enemy_unit is None:
                print('unit_attack_location(): invalid enemy unit id')
                return False

            if self.__game_state.damage_unit(attacking_unit_id, enemy_unit.defense):
                return True #if killed, then simply return
            
        
        for enemy_building_id in opponent_buildings_hit:
            enemy_building = self.__game_state.get_building_from_id(enemy_building_id)

            # basic validity
            if enemy_building is None:
                print('unit_attack_location(): invalid enemy building id')
                return False

            if self.__game_state.damage_unit(attacking_unit_id, enemy_building.defense):
                return True #if killed, then simply return

        return True


    def unit_attack_unit(self, attacking_unit_id: int, target_unit_id: int) -> bool:
        '''
        Unit from player's team attacks unit from opponent's team.

        There is no friendly fire, so 0 damage will be taken if attacking friendly units.
        Enemy units will deal [UnitType.defense] damage in retaliation if unit is in range.

        Will attack both enemy units and buildings within damage range

        Returns True if attack is successful, False otherwise
        '''
        #check attack validity
        if not self.can_unit_attack_unit(attacking_unit_id, target_unit_id):
            return False

        enemy_team = self.get_enemy_team()
        target_unit = self.__game_state.get_unit_from_id(target_unit_id)

        #basic validity
        if target_unit is None: 
            return False

        return self.unit_attack_location(attacking_unit_id, target_unit.x, target_unit.y)


    def unit_attack_building(self, attacking_unit_id: int, target_building_id: int) -> bool:
        '''
        Unit from player's team attacks building from opponent's team.

        There is no friendly fire, so 0 damage will be taken if attacking friendly units.
        Enemy units will deal [UnitType.defense] damage in retaliation if unit is in range.

        Will attack both enemy units and buildings within damage range

        Returns True if attack is successful, False otherwise
        '''

        #check attack validity
        if not self.can_unit_attack_building(attacking_unit_id, target_building_id):
            return False
        
        enemy_team = self.get_enemy_team()
        target_building = self.__game_state.get_building_from_id(target_building_id)

        #basic validity
        if target_building is None: 
            return False

        return self.unit_attack_location(attacking_unit_id, target_building.x, target_building.y)



    def building_attack_location(self, attacking_building_id: int, x: int, y: int):
        '''
        Building from player's team attacks location specified by (x, y)

        There is no friendly fire, so 0 damage will be taken if attacking friendly units.
        Enemy units will not retaliate in terms of damage

        Will attack only enemy units within damage range

        Returns True if attack is successful, False otherwise
        '''
        
        #check validity
        if not self.can_building_attack_location(attacking_building_id, x, y):
            return False
        

        enemy_team = self.get_enemy_team()
        attacking_building = self.__game_state.get_building_from_id(attacking_building_id)

        #basic validity
        if attacking_building is None: 
            return False


        # get all opponents within damage range
        #list of ids
        opponent_units_hit: List[int] = []

        #sense all opponents (only units) hit
        for unit in self.__game_state.units[enemy_team].values():
            #if chebyshev distance between unit and target <= damage range, then hit
            if self.chebyshev_distance_valid(unit.x, unit.y, x, y, attacking_building.damage_range):
                opponent_units_hit.append(unit.id)


        #buliding actions per turn decrement
        attacking_building.turn_actions_remaining -= 1

        #damage opponent's units
        for i in range(len(opponent_units_hit)):
            unit_id_hit = opponent_units_hit[i]
            #if opponent unit killed, then delete it from the list because they cannot retaliate
            if self.__game_state.damage_unit(unit_id_hit, attacking_building.damage):
                del opponent_units_hit[i]


        #no retaliation damage taken for buildings

        return True


    def building_attack_unit(self, attacking_building_id: int, target_unit_id: int) -> bool:
        '''
        Building from player's team attacks enemy unit

        There is no friendly fire, so 0 damage will be taken if attacking friendly units.
        Enemy units will not retaliate in terms of damage

        Will attack only enemy units within damage range

        Returns True if attack is successful, False otherwise
        '''

        if not self.can_building_attack_unit(attacking_building_id, target_unit_id):
            return False
        
        enemy_team = self.get_enemy_team()
        target_unit = self.__game_state.get_unit_from_id(target_unit_id)

        #basic validity
        if target_unit is None: 
            return False 

        return self.building_attack_location(attacking_building_id, target_unit.x, target_unit.y)



    def unit_auto_attack(self):
        pass

    def building_auto_attack(self):
        pass



    '''
    ---------------------------------------------------------------
    Move Functionalities

    NOTE: units gets 1 movement action and 1 attack action per turn
    ---------------------------------------------------------------
    '''


    def new_location(self, x: int, y: int, direction: Direction) -> Tuple[int, int]:
        '''
        Moves from (x, y) in direction. Does not perform error checking.

        Returns (x', y'), the new direction
        '''

        return (x + direction.dx, y + direction.dy)
    

    def unit_possible_move_directions(self, unit_id: int) -> list[Direction]:
        '''
        Given an ALLY unit id (and thus its location), return a list of valid directions that the unit can move in
        '''

        res = []

        #check each direction
        for dir in Direction:
            if self.can_move_unit_in_direction(unit_id, dir):
                res.append(dir)
        
        return res
        


    def can_move_unit_in_direction(self, unit_id: int, direction: Direction) -> bool:
        '''
        Check if it is possible to move a unit given by its id in a given direction by 1 square
        Units move similar to a king in chess

        Returns True if valid, False otherwise
        '''
        
        # is id valid?
        if unit_id not in self.__game_state.units[self.__team]:
            print("can_move_unit_in_direction(): invalid ally unit_id")
            return False


        unit = self.__game_state.get_unit_from_id(unit_id)
        
        #basic validity
        if unit is None:
            return False
        

        #check if the ending position is valid
        dest_x, dest_y = self.new_location(unit.x, unit.y, direction)

        if not self.__game_state.map.in_bounds(dest_x, dest_y):
            # print(f'Destination ({dest_x}, {dest_y}) out of bounds')
            return False
        
        #check if unit can walk on tile
        dest_tile: Tile = self.__game_state.map.tiles[dest_x][dest_y]
        if dest_tile not in unit.walkable_tiles:
            return False
        
        # if another unit is occupying the new space (that isn't the one that it is occupying right now), return false
        if direction != Direction.STAY and not self.__game_state.unit_placeable_map[dest_x][dest_y]:
            return False

        #check unit's movement range left for the turn
        if unit.turn_movement_remaining - dest_tile.movement_cost < 0:
            # print(f'{unit_id} has no movement left on its turn')
            return False

        return True


    def move_unit_in_direction(self, unit_id: int, direction: Direction) -> bool:
        '''
        Moves unit given by unit_id in the given direction by 1 square
        Units move similar to a king in chess

        Returns True if move is successful, False otherwise
        '''

        if not self.can_move_unit_in_direction(unit_id, direction):
            return False
        
        unit = self.__game_state.get_unit_from_id(unit_id)
        
        #basic validity
        if unit is None:
            return False
        
        dest_x, dest_y = self.new_location(unit.x, unit.y, direction)

        #reduce unit movements
        dest_tile: Tile = self.__game_state.map.tiles[dest_x][dest_y]
        unit.turn_movement_remaining -= dest_tile.movement_cost

        # update unit_pleaceable map (old is now free)
        self.__game_state.unit_placeable_map[unit.x][unit.y] = True

        #update location
        unit.x = dest_x
        unit.y = dest_y

        # update unit_pleaceable map (new is now taken)
        self.__game_state.unit_placeable_map[unit.x][unit.y] = False

        return True
    

    '''
    ---------------------------
    Exploration functionalities
    ---------------------------
    '''

    def can_explore(self, explorer_unit_id: int, explore_building_id: int) -> bool:
        '''Returns True if unit is an explorer on an exploration building, False otherwise'''

        if explorer_unit_id not in self.__game_state.units[self.__team]:
            print("can_explore(): invalid explorer_unit_id")
            return False

        explorer = self.__game_state.get_unit_from_id(explorer_unit_id)
        
        #basic validity
        if explorer is None:
            return False
        
        if explorer.type != UnitType.EXPLORER:
            return False
        
        # get actual building object from game_state or raise exception if not available
        building = self.__game_state.get_building_from_id(explore_building_id)

        # basic validity
        if building is None:
            print('can_explore(): invalid building id')
            return False
        
        if building.type != BuildingType.EXPLORER_BUILDING:
            return False
        

        #Explorer must be in the same location as building
        if not (explorer.x == building.x and explorer.y == building.y):
            return False
        
        
        return True
        


    def explore_for_gold(self, explorer_unit_id: int, explore_building_id: int) -> bool:
        '''
        Gains 50% of current balance
        
        True if success, False otherwise
        '''
        
        if not self.can_explore(explorer_unit_id, explore_building_id):
            return False
        
        if not self.disband_unit(explorer_unit_id):
            return False
        
        self.__game_state.balance[self.__team] += self.__game_state.balance[self.__team] // 2

        return True

    def explore_for_health(self, explorer_unit_id: int, explore_building_id: int, target_unit_id: int):
        '''
        Heals target unit to 150% of max health
        
        True if success, False otherwise
        '''
        if not self.can_explore(explorer_unit_id, explore_building_id):
            return False
        
        if not self.disband_unit(explorer_unit_id):
            return False
        

        if target_unit_id not in self.__game_state.units[self.__team]:
            print("explore_for_health(): invalid target_unit_id")
            return False

        unit = self.__game_state.get_unit_from_id(target_unit_id)
        
        #basic validity
        if unit is None:
            return False
        
        unit.health = math.ceil(unit.type.health * 1.5)

        return True
        


    def explore_for_attack(self, explorer_unit_id: int, explore_building_id: int, target_unit_id: int):
        '''
        Increases target unit strength by 2 (including those that originally has damage of 0)
        
        True if success, False otherwise
        '''
        if not self.can_explore(explorer_unit_id, explore_building_id):
            return False
        
        if not self.disband_unit(explorer_unit_id):
            return False
        

        if target_unit_id not in self.__game_state.units[self.__team]:
            print("explore_for_health(): invalid target_unit_id")
            return False

        unit = self.__game_state.get_unit_from_id(target_unit_id)
        
        #basic validity
        if unit is None:
            return False
        
        unit.damage += 2

        return True

    def explore_for_defense(self, explorer_unit_id: int, explore_building_id: int, target_unit_id: int):
        '''
        Increases defense by 2
        
        True if success, False otherwise
        '''
        if not self.can_explore(explorer_unit_id, explore_building_id):
            return False
        
        if not self.disband_unit(explorer_unit_id):
            return False
        

        if target_unit_id not in self.__game_state.units[self.__team]:
            print("explore_for_health(): invalid target_unit_id")
            return False

        unit = self.__game_state.get_unit_from_id(target_unit_id)
        
        #basic validity
        if unit is None:
            return False
        
        unit.defense += 2

        return True


    '''
    --------------------------------------------
    Engineer and Bridge Building Functionalities
    --------------------------------------------
    '''

    def can_build_bridge(self, engineer_id: int) -> bool:
        """
        Checks if the engineer unit can build a bridge at its own coordinates
        """
        # Ensure unit ID is valid and of type Engineer
        # are ids valid?
        if engineer_id not in self.__game_state.units[self.__team]:
            print("can_build_bridge(): invalid engineer_id")
            return False
        
        engineer = self.__game_state.get_unit_from_id(engineer_id)

        # basic validity
        if engineer is None:
            print('can_build_bridge(): invalid attacking unit id')
            return False
        
        if engineer.type != UnitType.ENGINEER:
            print('can_build_bridge(): unit is not an engineer')
            return False

        # Check if the target tile is a WATER tile
        if not self.__game_state.map.is_tile_type(engineer.x, engineer.y, Tile.WATER):
            print("can_build_bridge(): Target tile is not WATER")
            return False

        return True

    def build_bridge(self, engineer_id: int) -> bool:
        """
        Builds a bridge on a WATER tile at the specified location and disbands the engineer.
        """
        if not self.can_build_bridge(engineer_id):
            return False
        
        engineer = self.__game_state.get_unit_from_id(engineer_id)

        # Change the tile to BRIDGE
        self.__game_state.map.tiles[engineer.x][engineer.y] = Tile.BRIDGE

        # Record the map change
        self.__game_state.changed_maps.append(self.__game_state.map.to_2d_list())
        self.__game_state.changed_turns.append(self.__game_state.turn)

        # Disband the engineer
        if not self.disband_unit(engineer_id):
            print("build_bridge(): Failed to disband engineer")
            return False

        # print(f"Bridge successfully built at ({x}, {y}) by Engineer {engineer_id}")
        return True
    

    '''
    -----------------------
    Healing Functionalities
    -----------------------
    '''

    def can_heal_unit(self, healer_id: int, target_unit_id: int) -> bool:
        '''
        Return True if healer_id is a healer and if target is in range
        '''

        # are ids valid?
        if healer_id not in self.__game_state.units[self.__team]:
            print("can_heal_unit(): invalid attacking_unit_id")
            return False
        
        if target_unit_id not in self.__game_state.units[self.get_enemy_team()]:
            print("can_heal_unit(): invalid target_unit_id")
            return False


        healer_unit = self.__game_state.get_unit_from_id(healer_id)
        target_unit = self.__game_state.get_unit_from_id(target_unit_id)

        # basic validity
        if healer_unit is None:
            print('can_heal_unit(): invalid attacking unit id')
            return False
        
        if target_unit is None:
            print('can_heal_unit(): invalid target unit id')
            return False
        
        #is the healer_unit a healer?
        if healer_unit.type != UnitType.LAND_HEALER and healer_unit.type != UnitType.WATER_HEALER:
            return False


        # has unit attacked this turn?
        if healer_unit.turn_actions_remaining <= 0:
            return False #cannot attack again


        # is target unit in range of attacking unit?
        if not self.chebyshev_distance_valid(healer_unit.x, healer_unit.y, target_unit.x, target_unit.y, healer_unit.attack_range):
            return False

        return True

    def heal_unit(self, healer_id: int, target_unit_id: int) -> bool:
        '''
        Healer heals the target unit by amount specified by its type

        Returns True if heal is successful, False otherwise
        '''
        
        # are ids valid?
        if healer_id not in self.__game_state.units[self.__team]:
            print("can_heal_unit(): invalid attacking_unit_id")
            return False
        
        if target_unit_id not in self.__game_state.units[self.get_enemy_team()]:
            print("can_heal_unit(): invalid target_unit_id")
            return False


        healer_unit = self.__game_state.get_unit_from_id(healer_id)
        target_unit = self.__game_state.get_unit_from_id(target_unit_id)

        # basic validity
        if healer_unit is None:
            print('can_heal_unit(): invalid attacking unit id')
            return False
        
        if target_unit is None:
            print('can_heal_unit(): invalid target unit id')
            return False
        
        #unit actions per turn decrement
        healer_unit.turn_actions_remaining -= 1

        #heal
        target_unit.health = max(target_unit.type.health, target_unit.health + healer_unit.type.heal_amount)
    

    '''
    -----------------------
    Rat Functionalities
    -----------------------
    '''
    def can_harm_farm(self, rat_id: int, farm_id: int) -> bool:
        '''
        Checks if the specified unit is a Rat and if it can harm farming resources.
        Checks if the ally farm_id is specified
        '''
        if rat_id not in self.__game_state.units[self.__team]:
            print("can_harm_farm(): invalid rat_id")
            return False

        rat_unit = self.__game_state.get_unit_from_id(rat_id)

        farm_building = self.get_building_from_id(farm_id)
        if farm_building is None:
            print('can_harm_farm(): farm_id is not a valid farm')
            return False
        
        if farm_building.type not in self.__game_state.FARMS:
            print('can_harm_farm(): farm_id is not a valid farm')
            return False
        
        if farm_building.team != self.__team:
            print('can_harm_farm(): can only harm when on an ally farm')

        if rat_unit is None or rat_unit.type != UnitType.RAT:
            print("can_harm_farm(): unit is not a Rat")
            return False
        
        if not (rat_unit.x == farm_building.x and rat_unit.y == farm_building.y):
            print("can_harm_farm(): target building is not an ally farm")
            return False

        return True

    def harm_farm(self, rat_id: int, farm_id: int) -> bool:
        '''
        Applies Rat's farming penalties to both teams. Rat must be on an ally farm
        '''
        #checks if rat is valid, given enemy farm is valid
        if not self.can_harm_farm(rat_id, farm_id):
            return False

        # Apply penalties
        self.__game_state.balance[self.get_enemy_team()] *= GameConstants.RAT_OPPONENT_FARM_DAMAGE_MULTIPLIER
        self.__game_state.balance[self.__team] *= GameConstants.RAT_OWN_FARM_DAMAGE_MULTIPLIER

        # Disband the Rat after effect is applied
        self.disband_unit(rat_id)
        return True
