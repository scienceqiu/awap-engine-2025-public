from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

from src.units import Unit
from src.buildings import Building

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map

    def play_turn(self, rc: RobotController):

        team = rc.get_ally_team()
        ally_castle_id = -1

        ally_buildings = rc.get_buildings(team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                ally_castle_id = rc.get_id_from_building(building)[1]
                break


        enemy = rc.get_enemy_team()
        enemy_castle_id = -1

        enemy_buildings = rc.get_buildings(enemy)
        for building in enemy_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                enemy_castle_id = rc.get_id_from_building(building)[1]
                break

        enemy_castle = rc.get_building_from_id(enemy_castle_id)
        if enemy_castle is None:
            return


        #Idea: when rushing we want to get the unit with highest attack possible
        if(rc.get_turn()==1):
            if rc.can_spawn_unit(UnitType.SWORDSMAN, ally_castle_id):
                rc.spawn_unit(UnitType.SWORDSMAN, ally_castle_id)
        if rc.can_spawn_unit(UnitType.WARRIOR, ally_castle_id):
            rc.spawn_unit(UnitType.WARRIOR, ally_castle_id)
        if rc.can_spawn_unit(UnitType.KNIGHT, ally_castle_id):
            rc.spawn_unit(UnitType.KNIGHT, ally_castle_id)


        # loop through all the units
        for unit_id in rc.get_unit_ids(team):

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


