from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building
import random

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
    
    def play_turn(self, rc: RobotController):
        team = rc.get_ally_team()
        
        # build all the buildings possible from top down
        # spam farm strat?
        for i in range(self.map.width):
            for j in range(self.map.height):
                if self.map.is_tile_type(i, j, Tile.WATER) or self.map.is_tile_type(i, j, Tile.BRIDGE):
                    build_type = random.randint(1, 2)
                    if build_type == 2:
                        if rc.can_build_building(BuildingType.PORT, i, j):
                            rc.build_building(BuildingType.PORT, i, j)
                else:
                    build_type = random.randint(1, 2)
                    if build_type == 2:
                        if rc.can_build_building(BuildingType.EXPLORER_BUILDING, i, j):
                            rc.build_building(BuildingType.EXPLORER_BUILDING, i, j)
                    if build_type == 1:
                        if rc.can_build_building(BuildingType.FARM_1, i, j):
                            rc.build_building(BuildingType.FARM_1, i, j)

        # building as many units as possible
        ally_buildings = rc.get_buildings(team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                ally_castle_id = rc.get_id_from_building(building)[1]
                unit_type = random.randint(1, 4)
                if unit_type == 1:
                    if rc.can_spawn_unit(UnitType.KNIGHT, ally_castle_id):
                        rc.spawn_unit(UnitType.KNIGHT, ally_castle_id)
                if unit_type == 2:
                    if rc.can_spawn_unit(UnitType.EXPLORER, ally_castle_id):
                        rc.spawn_unit(UnitType.EXPLORER, ally_castle_id)
                if unit_type == 3:
                    if rc.can_spawn_unit(UnitType.ENGINEER, ally_castle_id):
                        rc.spawn_unit(UnitType.ENGINEER, ally_castle_id)
                if unit_type == 4:
                    if rc.can_spawn_unit(UnitType.LAND_HEALER_1, ally_castle_id):
                        rc.spawn_unit(UnitType.LAND_HEALER_1, ally_castle_id)
            if building.type == BuildingType.PORT:
                ally_castle_id = rc.get_id_from_building(building)[1]
                unit_type = random.randint(1, 3)
                if unit_type == 1:
                    if rc.can_spawn_unit(UnitType.SAILOR, ally_castle_id):
                        rc.spawn_unit(UnitType.SAILOR, ally_castle_id)
                if unit_type == 2:
                    if rc.can_spawn_unit(UnitType.GALLEY, ally_castle_id):
                        rc.spawn_unit(UnitType.GALLEY, ally_castle_id)
                if unit_type == 3:
                    if rc.can_spawn_unit(UnitType.WATER_HEALER_1, ally_castle_id):
                        rc.spawn_unit(UnitType.WATER_HEALER_1, ally_castle_id)


        my_units = rc.get_unit_ids(team)
        enemy = rc.get_enemy_team()
        enemy_castle_id = -1

        # like attack bot, attack all buildings
        enemy_buildings = rc.get_buildings(enemy)
        for building in enemy_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                enemy_castle_id = rc.get_id_from_building(building)[1]
                enemy_castle = rc.get_building_from_id(enemy_castle_id)
                if enemy_castle is None: 
                    continue
                # loop through all the units
                for unit_id in my_units:

                    # if castle still stands and can attack castle, attack castle
                    if enemy_castle_id in rc.get_building_ids(enemy) and rc.can_unit_attack_building(unit_id, enemy_castle_id):
                        rc.unit_attack_building(unit_id, enemy_castle_id)

                    # if can move towards castle, move towards castle
                    unit = rc.get_unit_from_id(unit_id)
                    if unit is None:
                        return
                    
                    possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                    possible_move_dirs.sort(key= lambda dir: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, dir), enemy_castle.x, enemy_castle.y))

                    best_dir = possible_move_dirs[0] if len(possible_move_dirs) > 0 else Direction.STAY #least chebyshev dist direction

                    if rc.can_move_unit_in_direction(unit_id, best_dir):
                        rc.move_unit_in_direction(unit_id, best_dir)
        
        
        enemy_unit_id = -1

        # similar, attack all units
        enemy_units = rc.get_units(enemy)
        for e_unit in enemy_units:
            enemy_unit_id = rc.get_id_from_unit(e_unit)[0]
            enemy_unit = rc.get_building_from_id(enemy_unit_id)
            if enemy_unit is None: 
                continue
            # loop through all the units
            for unit_id in my_units:

                # if castle still stands and can attack castle, attack castle
                if enemy_unit_id in rc.get_unit_ids(enemy) and rc.can_unit_attack_unit(unit_id, enemy_unit_id):
                    rc.unit_attack_unit(unit_id, enemy_unit_id)

                # if can move towards castle, move towards castle
                unit = rc.get_unit_from_id(unit_id)
                if unit is None:
                    return
                
                possible_move_dirs = rc.unit_possible_move_directions(unit_id)
                possible_move_dirs.sort(key= lambda dir: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, dir), enemy_unit.x, enemy_unit.y))

                best_dir = possible_move_dirs[0] if len(possible_move_dirs) > 0 else Direction.STAY #least chebyshev dist direction

                if rc.can_move_unit_in_direction(unit_id, best_dir):
                    rc.move_unit_in_direction(unit_id, best_dir)

        return