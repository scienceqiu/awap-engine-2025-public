from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

class BotPlayer(Player):
    def __init__(self, game_map: Map):
        self.map = game_map
        self.enemy_team = None
        self.num_warriors = 0



    def update_globals(self, rc):
        self.ally_team = rc.get_ally_team()
        self.enemy_team = rc.get_enemy_team()
        ally_buildings = rc.get_buildings(self.ally_team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                self.main_castle_id = rc.get_id_from_building(building)[1]
                break
        enemy_castles = [b for b in rc.get_buildings(self.enemy_team) if b.type == BuildingType.MAIN_CASTLE]
        self.enemy_castle = enemy_castles[0]
    def attack(self, rc, unit):
        unit_id = rc.get_id_from_unit(unit)[1]
        enemydist = 10000
        best_id = 0
        best_health = 10000
        enemy_units= rc.get_units(self.enemy_team)

        for enemyunit in enemy_units:
            curdist= rc.get_chebyshev_distance(unit.x, unit.y, enemyunit.x, enemyunit.y)
            target_id = rc.get_id_from_unit(enemyunit)[1]
            if curdist<=min(4, unit.type.attack_range) and enemyunit.health<best_health and enemyunit.health>0:
                best_health = enemyunit.health
                enemydist = curdist
                best_id = target_id

        enemy_units = rc.get_units(self.enemy_team)


        distance = rc.get_chebyshev_distance(unit.x, unit.y, self.enemy_castle.x, self.enemy_castle.y)
        if distance <= min(4, unit.type.attack_range):
            # Use rc.get_id_from_building for consistency
            target_id = rc.get_id_from_building(self.enemy_castle)[1]
            if rc.can_unit_attack_building(unit_id, target_id):
                rc.unit_attack_building(unit_id, target_id)
        elif enemydist<=min(4, unit.type.attack_range) and rc.can_unit_attack_unit(unit_id, best_id):
            rc.unit_attack_unit(unit_id, best_id)


    def move(self, rc, unit):
        unit_id = rc.get_id_from_unit(unit)[1]
        possible_dirs = rc.unit_possible_move_directions(unit_id)
        if possible_dirs:
            sorted_dirs = sorted(
                possible_dirs,
                key=lambda d: rc.get_chebyshev_distance(
                    *rc.new_location(unit.x, unit.y, d), self.enemy_castle.x, self.enemy_castle.y
                )
            )
            best_dir = sorted_dirs[0]
            new_loc = rc.new_location(unit.x, unit.y, best_dir)
            if rc.get_chebyshev_distance(new_loc[0], new_loc[1], self.enemy_castle.x, self.enemy_castle.y) <=rc.get_chebyshev_distance(unit.x, unit.y, self.enemy_castle.x, self.enemy_castle.y):
                rc.move_unit_in_direction(unit_id, best_dir)
    # possible todo:, improve movement micro

    def spawnStuff(self, rc):
        balance = rc.get_balance(self.ally_team)
        # Always fetch the current balance from rc instead of relying solely on a local variable.
        print(balance)

        warrior_cost = UnitType.WARRIOR.cost
        while balance >= warrior_cost:
            if rc.can_spawn_unit(UnitType.WARRIOR, self.main_castle_id):
                rc.spawn_unit(UnitType.WARRIOR, self.main_castle_id)
                balance -= warrior_cost
                self.num_warriors+= 1
            else:
                break
        catapult_cost = UnitType.CATAPULT.cost
        while balance >= catapult_cost:
            if rc.can_spawn_unit(UnitType.CATAPULT, self.main_castle_id):
                rc.spawn_unit(UnitType.CATAPULT, self.main_castle_id)
                balance -= catapult_cost
            else:
                break

    def play_turn(self, rc: RobotController):

        self.update_globals(rc)
        self.spawnStuff(rc)



        ally_units = rc.get_units(self.ally_team)
        for unit in ally_units:
            self.attack(rc, unit)
            self.move(rc, unit)
