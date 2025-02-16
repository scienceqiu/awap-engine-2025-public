from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

class BotPlayer(Player):
    def __init__(self, game_map: Map):
        self.map = game_map
        self.main_castle_id = None
        self.enemy_team = None

    def play_turn(self, rc: RobotController):
        ally_team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()
        self.enemy_team = enemy_team

        # Locate main castle once
        if self.main_castle_id is None:
            ally_buildings = rc.get_buildings(ally_team)
            for building in ally_buildings:
                if building.type == BuildingType.MAIN_CASTLE:
                    self.main_castle_id = rc.get_id_from_building(building)[1]
                    break

        # If main castle is destroyed, exit
        if self.main_castle_id is None:
            return

        # Always fetch the current balance from rc instead of relying solely on a local variable.
        balance = rc.get_balance(ally_team)

        # Build farms to maximize income
        farm_cost = BuildingType.FARM_1.cost
        for x in range(self.map.width):
            for y in range(self.map.height):
                # Update balance from the game engine if needed
                if balance < farm_cost:
                    break
                if rc.can_build_building(BuildingType.FARM_1, x, y):
                    if rc.build_building(BuildingType.FARM_1, x, y):
                        # Optionally update balance here or re-fetch it later.
                        balance -= farm_cost

        # Spawn as many catapults as possible
        catapult_cost = UnitType.CATAPULT.cost
        while balance >= catapult_cost:
            if rc.can_spawn_unit(UnitType.CATAPULT, self.main_castle_id):
                rc.spawn_unit(UnitType.CATAPULT, self.main_castle_id)
                balance -= catapult_cost
            else:
                break

        # Spawn engineers with remaining balance
        engineer_cost = UnitType.ENGINEER.cost
        if balance >= engineer_cost:
            if rc.can_spawn_unit(UnitType.ENGINEER, self.main_castle_id):
                rc.spawn_unit(UnitType.ENGINEER, self.main_castle_id)

        # Process units
        enemy_castles = [b for b in rc.get_buildings(enemy_team) if b.type == BuildingType.MAIN_CASTLE]
        ally_units = rc.get_units(ally_team)
        for unit in ally_units:
            unit_id = rc.get_id_from_unit(unit)[1]
            if unit.type == UnitType.CATAPULT:
                if not enemy_castles:
                    continue
                # Find closest enemy castle
                closest_castle = min(enemy_castles, key=lambda c: rc.get_chebyshev_distance(unit.x, unit.y, c.x, c.y))
                distance = rc.get_chebyshev_distance(unit.x, unit.y, closest_castle.x, closest_castle.y)
                if distance <= unit.type.attack_range:
                    # Use rc.get_id_from_building for consistency
                    target_id = rc.get_id_from_building(closest_castle)[1]
                    if rc.can_unit_attack_building(unit_id, target_id):
                        rc.unit_attack_building(unit_id, target_id)
                else:
                    possible_dirs = rc.unit_possible_move_directions(unit_id)
                    if possible_dirs:
                        sorted_dirs = sorted(
                            possible_dirs,
                            key=lambda d: rc.get_chebyshev_distance(
                                *rc.new_location(unit.x, unit.y, d), closest_castle.x, closest_castle.y
                            )
                        )
                        best_dir = sorted_dirs[0]
                        rc.move_unit_in_direction(unit_id, best_dir)
            elif unit.type == UnitType.ENGINEER:
                if rc.can_build_bridge(unit_id):
                    rc.build_bridge(unit_id)
                else:
                    if enemy_castles:
                        closest_castle = min(enemy_castles, key=lambda c: rc.get_chebyshev_distance(unit.x, unit.y, c.x, c.y))
                        possible_dirs = rc.unit_possible_move_directions(unit_id)
                        if possible_dirs:
                            sorted_dirs = sorted(
                                possible_dirs,
                                key=lambda d: rc.get_chebyshev_distance(
                                    *rc.new_location(unit.x, unit.y, d), closest_castle.x, closest_castle.y
                                )
                            )
                            best_dir = sorted_dirs[0]
                            rc.move_unit_in_direction(unit_id, best_dir)
