''' file that contains the game state at a given instnace; can change the game state through functions (attack function, spawn function) '''

from src.map import Map
from src.game_constants import Team, GameConstants, UnitType, BuildingType, MapRender
from src.buildings import Building
from src.units import Unit

from src.exceptions import GameException

from src.renderer import Renderer

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide" #stop the command line pygame printout
import pygame
import pygame.font as font

from typing import Dict, Optional


class GameState:
    ''' 
    This class details the game state of the game. It stores units, towers, farms, health, time step, the map, etc.

    The game state has helper functions to help change the game state with respect to player actions;
    these are the core atomic environmental features. The Robot Controller class will have more details of what the players can change.

    It has turn mechanics for each.

    It also includes a render functionality for rendering.
    '''

    def __init__(self, map: Map):
        self.map = map # a discretized grid map

        self.balance = {Team.BLUE: GameConstants.STARTING_BALANCE, Team.RED: GameConstants.STARTING_BALANCE}

        self.turn = 0

        self.has_rendered = False #if the pygame has been initialized
        self.tile_size = -1

        self.buildings: Dict[Team, Dict[int, Building]] = {Team.BLUE: {}, Team.RED: {}}
        self.units: Dict[Team, Dict[int, Unit]] = {Team.BLUE: {}, Team.RED: {}}

        #get main castle to buildings; add players' main castle given by map into buildings
        red_main_castle = Building(Team.RED, BuildingType.MAIN_CASTLE, self.map.red_castle_loc[0], self.map.red_castle_loc[1], spawnable= True)
        blue_main_castle = Building(Team.BLUE, BuildingType.MAIN_CASTLE, self.map.blue_castle_loc[0], self.map.blue_castle_loc[1], spawnable= True)
        #this is to know when we deleted the building (ie when the game ends)

        self.building_placeable_map = [[True for y in range(self.map.height)] for x in range(self.map.width)]
        self.unit_placeable_map = [[True for y in range(self.map.height)] for x in range(self.map.width)]
        #set building_placeable
        self.building_placeable_map[self.map.red_castle_loc[0]][self.map.red_castle_loc[1]] = False
        self.building_placeable_map[self.map.blue_castle_loc[0]][self.map.blue_castle_loc[1]] = False


        self.main_castle_ids: Dict[Team, int] = {Team.RED: red_main_castle.id, Team.BLUE: blue_main_castle.id}

        self.red_main_castle_id = self.main_castle_ids[Team.RED]
        self.blue_main_castle_id = self.main_castle_ids[Team.BLUE]

        #add to buildings
        self.buildings[Team.BLUE][blue_main_castle.id] = blue_main_castle
        self.buildings[Team.RED][red_main_castle.id] = red_main_castle


        self.time_remaining = {Team.BLUE: GameConstants.INITIAL_TIME_POOL, Team.RED: GameConstants.INITIAL_TIME_POOL}

        self.renderer = Renderer(self.map)

        self.FARMS = [BuildingType.FARM_1, BuildingType.FARM_2, BuildingType.FARM_3]

        self.previousBuildingsRed = None
        
        self.previousBuildingsBlue = None 

        self.changed_turns = [] # turn numbers where map was changed
        self.changed_maps = [] # changed map on that turn, list of 2D maps

    
    '''
    -----------------------
    Simple helper functions
    -----------------------
    '''

    def get_opposite_team(self, team: Team) -> Team:
        return Team.RED if team == Team.BLUE else Team.BLUE
    

    def get_team_of_unit(self, unit_id: int) -> Optional[Team]:
        '''
        Gets the team that a unit belongs to
        Returns either Team.RED or Team.BLUE if unit_id is valid; raises error if not valid
        '''
        #check validity and get unit's team
        if unit_id in self.units[Team.RED]:
            return Team.RED
        elif unit_id in self.units[Team.BLUE]:
            return Team.BLUE
        else:
            return None

    
    def get_team_of_building(self, building_id: int) -> Optional[Team]:
        '''
        Gets the team that a unit belongs to
        Returns either Team.RED or Team.BLUE if unit_id is valid; raises error if not valid
        '''

        #check validity and get unit's team
        if building_id in self.buildings[Team.RED]:
            return Team.RED
        elif building_id in self.buildings[Team.BLUE]:
            return Team.BLUE
        else:
            return None



    def get_unit_from_id(self, unit_id: int) -> Optional[Unit]:
        '''
        Gets the actual unit object from its id
        '''
        team = self.get_team_of_unit(unit_id)

        if team is None:
            return None

        return self.units[team][unit_id]



    def get_building_from_id(self, building_id: int) -> Optional[Building]:
        '''
        Gets the actual building object from its id
        '''
        team = self.get_team_of_building(building_id)

        # basic validity
        if team is None:
            return None

        return self.buildings[team][building_id]


    '''
    --------------------------------------
    Unit and Building Placeable Map access
    --------------------------------------
    '''


    def is_building_placeable(self, building_type: BuildingType, x: int, y: int) -> bool:
        '''At most one building per tile and building must be allowed to be placed on tile'''

        if not self.map.in_bounds(x, y):
            return False
        

        if not self.building_placeable_map[x][y]:
            return False
        
        if self.map.tiles[x][y] not in building_type.placeable_tiles:
            return False

        return True
    

    def is_unit_placeable(self, unit_type: UnitType, x: int, y: int) -> bool:
        '''At most one unit per tile'''
        if not self.map.in_bounds(x, y):
            return False
        
        if not self.unit_placeable_map[x][y]:
            return False
        
        if self.map.tiles[x][y] not in unit_type.walkable_tiles:
            return False

        return True
    

    '''
    -------------------------
    Object Creation Functions
    -------------------------
    '''

    def place_unit(self, team: Team, unit_type: UnitType, x: int, y: int, level: int= 1) -> bool:
        '''Places a unit on the map generally'''

        if not self.is_unit_placeable(unit_type, x, y):
            print('unit failed to place')
            return False
        
        new_unit = Unit(team, unit_type, x, y, level)

        self.units[team][new_unit.id] = new_unit
        self.unit_placeable_map[x][y] = False
        return True


    def spawn_unit(self, team: Team, unit_type: UnitType, spawn_building_id: int, level: int= 1) -> bool:
        '''Spawns a unit from a building; functionality used in robot controller'''

        spawn_building = self.get_building_from_id(spawn_building_id)

        # basic validity
        if spawn_building is None:
            return False

        x, y = spawn_building.x, spawn_building.y
        return self.place_unit(team, unit_type, x, y, level)
    

    def place_building(self, team: Team, building_type: BuildingType, x: int, y: int, level: int= 1) -> bool:
        '''Place a building on the map generally'''

        if building_type == BuildingType.MAIN_CASTLE:
            print('Cannot build Main Castle')
            return False

        if not self.is_building_placeable(building_type, x, y):
            print('building failed to place')
            return False
        
        new_building = Building(team, building_type, x, y, level)

        self.buildings[team][new_building.id] = new_building
        self.building_placeable_map[x][y] = False
        return True


    '''
    -------------------------
    Object Movement functions
    -------------------------
    '''

    def move_unit(self, unit_id: int, dest_x: int, dest_y: int) -> bool:
        '''
        Moves a unit to dest_x and dest_y if possible given map constraints (ie in bounds)
        (NO unit move range constraints)
        Returns True if moved, False otherwise or bad destination.
        '''
        
        #check in bounds
        if not self.map.in_bounds(dest_x, dest_y):
            return False
        
        #check validity and get unit's team
        team = self.get_team_of_unit(unit_id)

        #basic validity
        if team is None:
            return False

        unit = self.units[team][unit_id]

        #change placeable map configurations
        self.unit_placeable_map[unit.x][unit.y] = True #can now place unit in old location
        self.unit_placeable_map[dest_x][dest_y] = False #can't place unit in new location

        #change unit state
        unit.x = dest_x
        unit.y = dest_y


    '''
    ----------------------------------------------------------
    Object Damage and Removal Functions (delete, damage, sell)
    ----------------------------------------------------------
    '''


    def delete_unit(self, team: Team, unit_id: int):
        '''
        Removes unit from game procedurally
        Precondition of safety for team/unit_id
        '''
        #can place another unit at that location
        self.unit_placeable_map[self.units[team][unit_id].x][self.units[team][unit_id].y] = True
        #delete from units list
        del self.units[team][unit_id]

    def delete_building(self, team: Team, building_id: int):
        '''
        Removes building from game procedurally
        Precondition of safety for team/building_id
        '''
        #can place another building at that location
        self.building_placeable_map[self.buildings[team][building_id].x][self.buildings[team][building_id].y] = True #can now place
        #delete from buildings list
        del self.buildings[team][building_id]
        


    def damage_unit(self, unit_id: int, dmg: int) -> bool:
        '''
        Damages a unit by a non-negative damage, and deletes it if killed
        Return True if killed, False otherwise (including error)
        '''
        if dmg < 0:
            raise GameException('damage must be non-negative')
        
        #check validity and get unit's team
        team = self.get_team_of_unit(unit_id)

        # basic validity
        if team is None:
            return False

        self.units[team][unit_id].health -= dmg

        #if unit is destroyed
        if self.units[team][unit_id].health <= 0:
            #remove unit from game
            self.delete_unit(team, unit_id)


    def damage_building(self, building_id: int, dmg: int) -> bool:
        '''
        Damages a building, and changes sides if defeated
        Return True if defeated, False otherwise
        '''
        if dmg < 0:
            raise GameException('damage must be non-negative')
        
        #check validity and get unit's team
        team = self.get_team_of_building(building_id)

        if team is None: #no action is taken
            return False

        self.buildings[team][building_id].health -= dmg

        #if building is destroyed
        if self.buildings[team][building_id].health <= 0:
            #remove from game
            self.delete_building(team, building_id)
            return True
        
        return False
            

    def sell_unit(self, team: Team, unit_id: int) -> bool:
        '''Sells a unit for a discounted price; unit must be at least a certain level of health'''

        #check unit validity
        if unit_id not in self.units[team]:
            raise GameException("unit_id not valid")
        
        #check if it passes health threshhold
        unit = self.units[team][unit_id]

        if unit.health < GameConstants.SELL_HEALTH_PERCENT * unit.type.health:
            print(f'Cannot sell unit with unit_id {unit_id} as is it below health threshhold')
            return False

        #add to balance
        self.balance[team] += unit.type.cost * GameConstants.UNIT_SELL_DISCOUNT

        #remove from units list
        self.delete_unit(team, unit_id)

        return True


    def sell_building(self, team: Team, building_id: int) -> bool:
        '''Sells a buliding for a discounted price; building must be above a certain level of health'''

        #check unit validity
        if building_id not in self.buildings[team]:
            raise GameException("building_id not valid")
        
        #check if it passes health threshhold
        building = self.buildings[team][building_id]

        if building.health < GameConstants.SELL_HEALTH_PERCENT * building.type.health:
            print(f'Cannot sell unit with building_id {building_id} as is it below health threshhold')
            return False

        #add to balance
        self.balance[team] += building.type.cost * GameConstants.UNIT_SELL_DISCOUNT

        #remove from units list
        self.delete_building(team, building_id)

        return True


    '''
    --------------
    Turn Mechanics
    --------------
    '''

    def start_turn(self):
        '''
        Procedurally start the next turn by resetting unit/building turn values among other mechanics
        '''

        self.turn += 1

        # reset all units' actions and movement remaining this turn
        for team_units in self.units.values():
            for curr_unit in team_units.values():
                curr_unit.turn_actions_remaining = curr_unit.type.actions_per_turn
                curr_unit.turn_movement_remaining = curr_unit.type.move_range

        #reset all buildings' actions remaining this turn
        for team_buildings in self.buildings.values():
            for curr_building in team_buildings.values():
                curr_building.turn_actions_remaining = curr_building.type.actions_per_turn


        # add passive income to balance
        self.balance[Team.RED] += GameConstants.PASSIVE_COINS_PER_TURN
        self.balance[Team.BLUE] += GameConstants.PASSIVE_COINS_PER_TURN

        # add farm's income to balance
        for team in [Team.RED, Team.BLUE]:
            for building in self.buildings[team].values():
                if building.type in self.FARMS:
                    self.balance[team] += building.type.coins_per_turn




    '''
    -----------------------------
    Pygame Render Helper Function
    -----------------------------
    '''

    def render(self):
        '''Pygame rendering with Render class'''

        if not self.has_rendered:
            self.has_rendered = True
            self.renderer.init_render()
        
        # For performance
        pygame.event.get()

        self.renderer.map_render()

        #render red buildings
        for building in self.buildings[Team.RED].values():
            self.renderer.building_render(building)
            

        #render blue buildings
        for building in self.buildings[Team.BLUE].values():
            self.renderer.building_render(building)

        #render red units
        for unit in self.units[Team.RED].values():
            self.renderer.unit_render(unit)

        #render blue units
        for unit in self.units[Team.BLUE].values():
            self.renderer.unit_render(unit)

        #render game_state (turn, balance, etc.)
        BLACK = (0, 0, 0)
        turn_text = font.SysFont('Comic Sans MS', 10).render(f'Turn: {self.turn}', True, BLACK)
        blue_balance_text = font.SysFont('Comic Sans MS', 10).render(f'Blue balance: {self.balance[Team.BLUE]}', True, BLACK)
        red_balance_text = font.SysFont('Comic Sans MS', 10).render(f'Red balance: {self.balance[Team.RED]}', True, BLACK)
        self.renderer.screen.blit(turn_text, ((5, self.renderer.height * MapRender.TILE_SIZE + 5), (20, 10)))
        self.renderer.screen.blit(blue_balance_text, ((5, self.renderer.height * MapRender.TILE_SIZE + 20), (20, 10)))
        self.renderer.screen.blit(red_balance_text, ((5, self.renderer.height * MapRender.TILE_SIZE + 35), (20, 10)))

        pygame.display.update()

    def save_previous_state(self, blueBuildings, redBuildings):
        '''Saves the previous state of buildings to prevent export of empty list into json'''
        self.previousBuildingsRed = redBuildings
        self.previousBuildingsBlue = blueBuildings

    def get_previous_state(self, team_lost: Team):
        '''Right before using the previous buildings to export to json, set the health to 0'''
        if team_lost == Team.RED:
            for dictionary in self.previousBuildingsRed:
                dictionary["health"] = 0

        if team_lost == Team.BLUE:
            for dictionary in self.previousBuildingsBlue:
                dictionary["health"] = 0

    def to_dict(self):
        """
        Converts the game state into a dictionary representation, for json replay file.
        """
        
        blueBuildings = [building.to_dict() for building in self.buildings[Team.BLUE].values()]
        redBuildings = [building.to_dict() for building in self.buildings[Team.RED].values()]    

        if redBuildings == []: #if red loses
            self.get_previous_state(Team.RED) #set health == 0
            redBuildings = self.previousBuildingsRed
        else:
            self.save_previous_state(blueBuildings, redBuildings)

        if blueBuildings == []: #if blue loses
            self.get_previous_state(Team.BLUE) #set health == 0
            blueBuildings = self.previousBuildingsBlue
        else:
            self.save_previous_state(blueBuildings, redBuildings)
        return {
            "balance": {team.name: balance for team, balance in self.balance.items()},
            "turn": self.turn,
            "tile_size": self.tile_size,
            "buildings": {
            Team.BLUE.name: blueBuildings,
            Team.RED.name: redBuildings
            },
            "units": {
                Team.BLUE.name: [unit.to_dict() for unit in self.units[Team.BLUE].values()],
                Team.RED.name: [unit.to_dict() for unit in self.units[Team.RED].values()]
            },
            "red_main_castle_id": self.red_main_castle_id,
            "blue_main_castle_id": self.blue_main_castle_id,
            "time_remaining": {team.name: time for team, time in self.time_remaining.items()},
        }


    
