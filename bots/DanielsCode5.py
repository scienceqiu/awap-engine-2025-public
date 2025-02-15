from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType
from src.units import Unit
import random

class BotPlayer(Player):
    def __init__(self, game_map: Map):
        self.map = game_map
        self.enemy_team = None
        self.prev_spawn = True



    def update_globals(self, rc):
        self.ally_team = rc.get_ally_team()
        self.enemy_team = rc.get_enemy_team()
        ally_buildings = rc.get_buildings(self.ally_team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                self.main_castle_id = rc.get_id_from_building(building)[1]
                self.main_castle = building
                break
        enemy_castles = [b for b in rc.get_buildings(self.enemy_team) if b.type == BuildingType.MAIN_CASTLE]
        self.enemy_castle = enemy_castles[0]
        self.enemy_castle_id = rc.get_id_from_building(self.enemy_castle)[1]
    def attack(self, rc, unit):
        unit_id = rc.get_id_from_unit(unit)[1]
        enemydist = 10000
        best_id = 0
        best_health = 10000
        enemy_units= rc.get_units(self.enemy_team)

        for enemyunit in enemy_units:
            curdist= rc.get_chebyshev_distance(unit.x, unit.y, enemyunit.x, enemyunit.y)
            target_id = rc.get_id_from_unit(enemyunit)[1]
            ishealer = 1 if enemyunit.type == UnitType.LAND_HEALER_1 else 0
            if curdist<=min(4, unit.type.attack_range) and enemyunit.health-2*ishealer<best_health and enemyunit.health>0:
                best_health = enemyunit.health
                enemydist = curdist
                best_id = target_id

        enemy_buildings= rc.get_buildings(self.enemy_team)
        for enemybuilding in enemy_buildings:
            curdist= rc.get_chebyshev_distance(unit.x, unit.y, enemyunit.x, enemyunit.y)
            target_id = rc.get_id_from_unit(enemyunit)[1]
            if curdist<=min(4, unit.type.attack_range) and enemyunit.health-3<best_health and enemyunit.health>0:
                best_health = enemyunit.health
                enemydist = curdist
                best_id = target_id



        distance = rc.get_chebyshev_distance(unit.x, unit.y, self.enemy_castle.x, self.enemy_castle.y)
        if distance <= min(4, unit.type.attack_range) and rc.can_unit_attack_building(unit_id,self.enemy_castle_id):
            # Use rc.get_id_from_building for consistency
            rc.unit_attack_building(unit_id, self.enemy_castle_id)
        elif enemydist<=min(4, unit.type.attack_range) and rc.can_unit_attack_building(unit_id, best_id):
            rc.unit_attack_building(unit_id, target_id)
        elif enemydist<=min(4, unit.type.attack_range) and rc.can_unit_attack_unit(unit_id, best_id):
            rc.unit_attack_unit(unit_id, best_id)
    def calculate_closest_healer():
        pass
    def calculate_closest_nonhealer():
        pass
    def heal(self, rc, unit):
        unit_id = rc.get_id_from_unit(unit)[1]
        ally_units = rc.get_units(self.ally_team)
        allydist = 10000
        best_id = 0
        best_health = 1000
        for allyunit in ally_units:
            curdist= rc.get_chebyshev_distance(unit.x, unit.y, allyunit.x, allyunit.y)
            target_id = rc.get_id_from_unit(allyunit)[1]
            if curdist<=unit.type.attack_range and allyunit.health<best_health and allyunit.health<10:
                best_health = allyunit.health
                best_id = target_id
                allydist = curdist
        if allydist<1000: # todo, try to improve healer movement
            if rc.can_heal_unit(unit_id, best_id):
                # print("YAYAYAYA")
                rc.heal_unit(unit_id, best_id)
    def find_nearest_healer(self, rc: RobotController, unit_id: int) -> Unit:
        """Find the nearest healer unit to the specified unit"""
        team = rc.get_ally_team()
        current_unit = rc.get_unit_from_id(unit_id)
        if not current_unit:
            return None
            
        healers = []
        for unit in rc.get_units(team):
            # Skip self and non-healers
            if unit.id == unit_id:
                continue
            if unit.type in [UnitType.LAND_HEALER_1, UnitType.LAND_HEALER_2, UnitType.LAND_HEALER_3,
                            UnitType.WATER_HEALER_1, UnitType.WATER_HEALER_2, UnitType.WATER_HEALER_3]:
                healers.append(unit)
        
        # Find closest by Chebyshev distance
        closest = None
        min_dist = float('inf')
        for healer in healers:
            dist = rc.get_chebyshev_distance(current_unit.x, current_unit.y, healer.x, healer.y)
            if dist < min_dist:
                min_dist = dist
                closest = healer
        return closest
    def moveattacker(self, rc, unit):
        unit_id = rc.get_id_from_unit(unit)[1]
        possible_dirs = rc.unit_possible_move_directions(unit_id)
        if possible_dirs:
            cur_targ = (self.enemy_castle.x, self.enemy_castle.y)
            if unit.health<4:
                # closest_healer = self.find_nearest_healer(rc, unit_id)
                # if rc.get_chebyshev_distance(unit.x, unit.y, closest_healer.x, closest_healer.y)<2 or rc.get_chebyshev_distance(unit.x, unit.y, closest_healer.x, closest_healer.y)>7:
                    # cur_targ = (self.enemy_castle.x, self.enemy_castle.y)
                # elif closest_healer:
                    # cur_targ = (closest_healer.x, closest_healer.y)
                cur_targ = (self.main_castle.x, self.main_castle.y)
            sorted_dirs = sorted(
                possible_dirs,
                key=lambda d: rc.get_chebyshev_distance(
                    *rc.new_location(unit.x, unit.y, d), cur_targ[0], cur_targ[1]
                )
            )
            best_dir = sorted_dirs[0]
            new_loc = rc.new_location(unit.x, unit.y, best_dir)
            if rc.get_chebyshev_distance(new_loc[0], new_loc[1], cur_targ[0], cur_targ[1]) <=rc.get_chebyshev_distance(unit.x, unit.y, cur_targ[0], cur_targ[1]):
                rc.move_unit_in_direction(unit_id, best_dir)
    def movehealer(self, rc, unit):
        unit_id = rc.get_id_from_unit(unit)[1]
        possible_dirs = rc.unit_possible_move_directions(unit_id)
        if possible_dirs:
            cur_targ = (self.enemy_castle.x, self.enemy_castle.y)
            if unit.health<4 or (rc.get_chebyshev_distance(self.enemy_castle.x, self.enemy_castle.y, unit.x, unit.y)<4  and rc.get_chebyshev_distance(self.main_castle.x, self.main_castle.y, unit.x, unit.y)>4):
                cur_targ = (self.main_castle.x, self.main_castle.y)
            sorted_dirs = sorted(
                possible_dirs,
                key=lambda d: rc.get_chebyshev_distance(
                    *rc.new_location(unit.x, unit.y, d), cur_targ[0], cur_targ[1]
                )
            )
            best_dir = sorted_dirs[0]
            new_loc = rc.new_location(unit.x, unit.y, best_dir)
            if rc.get_chebyshev_distance(new_loc[0], new_loc[1], cur_targ[0], cur_targ[1]) <=rc.get_chebyshev_distance(unit.x, unit.y, cur_targ[0], cur_targ[1]):
                rc.move_unit_in_direction(unit_id, best_dir)
    # possible todo:, improve movement micro

    def spawnStuff(self, rc):
        balance = rc.get_balance(self.ally_team)
        # Always fetch the current balance from rc instead of relying solely on a local variable.
        print(balance)

        rng = random.randint(0, 1);
        if not self.prev_spawn and rng==0:
            if balance>=3: # this is sus, idk if its good
                healer_cost= UnitType.LAND_HEALER_1.cost
                while balance >= healer_cost:
                    if rc.can_spawn_unit(UnitType.LAND_HEALER_1, self.main_castle_id):
                        rc.spawn_unit(UnitType.LAND_HEALER_1, self.main_castle_id)
                        balance -= healer_cost
                        self.prev_spawn = not self.prev_spawn
                    else:
                        break
        else:
            if balance>=2:
                warrior_cost = UnitType.WARRIOR.cost
                while balance >= warrior_cost:
                    if rc.can_spawn_unit(UnitType.WARRIOR, self.main_castle_id):
                        rc.spawn_unit(UnitType.WARRIOR, self.main_castle_id)
                        balance -= warrior_cost
                        self.prev_spawn = not self.prev_spawn
                    else:
                        break
            else:
                warrior_cost = UnitType.KNIGHT.cost
                while balance >= warrior_cost:
                    if rc.can_spawn_unit(UnitType.KNIGHT, self.main_castle_id):
                        rc.spawn_unit(UnitType.KNIGHT, self.main_castle_id)
                        balance -= warrior_cost
                        self.prev_spawn = not self.prev_spawn
                    else:
                        break

    def play_turn(self, rc: RobotController):

        self.update_globals(rc)



        ally_units = rc.get_units(self.ally_team)
        for unit in ally_units:
            if unit.type==UnitType.WARRIOR or unit.type == UnitType.KNIGHT:
                self.attack(rc, unit)
                self.moveattacker(rc, unit)
                self.attack(rc, unit)
            else:
                self.heal(rc, unit)
                self.movehealer(rc, unit)
                self.heal(rc, unit)
            # self.move(rc, unit)
        self.spawnStuff(rc)
