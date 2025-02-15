from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType
from src.units import Unit
from src.buildings import Building
import random

# LLM ASSIST: The following bot code was generated with the assistance of an LLM,
# which helped us design a multi-pronged strategy for unit spawning, movement,
# attacking, and special unit handling.

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        # LLM ASSIST: Strategic heuristics were incorporated into the play_turn function.

    def play_turn(self, rc: RobotController):
        team = rc.get_ally_team()
        enemy = rc.get_enemy_team()

        # Identify our main castle
        ally_castles = [b for b in rc.get_buildings(team) if b.type == BuildingType.MAIN_CASTLE]
        if not ally_castles:
            return
        ally_castle = ally_castles[0]
        ally_castle_id = rc.get_id_from_building(ally_castle)[1]

        # Identify enemy main castle
        enemy_castle = None
        enemy_castle_id = None
        for b in rc.get_buildings(enemy):
            if b.type == BuildingType.MAIN_CASTLE:
                enemy_castle = b
                enemy_castle_id = rc.get_id_from_building(b)[1]
                break
        if enemy_castle is None:
            return

        # ===============================
        # Spawn Units Based on Balance
        # ===============================
        current_balance = rc.get_balance(team)
        # If we have enough coins, choose from available unit types
        if current_balance >= 10:
            spawnable_units = []
            if rc.can_spawn_unit(UnitType.KNIGHT, ally_castle_id):
                spawnable_units.append(UnitType.KNIGHT)
            if rc.can_spawn_unit(UnitType.WARRIOR, ally_castle_id):
                spawnable_units.append(UnitType.WARRIOR)
            if rc.can_spawn_unit(UnitType.EXPLORER, ally_castle_id):
                spawnable_units.append(UnitType.EXPLORER)
            if rc.can_spawn_unit(UnitType.ENGINEER, ally_castle_id):
                spawnable_units.append(UnitType.ENGINEER)
            if rc.can_spawn_unit(UnitType.LAND_HEALER_1, ally_castle_id):
                spawnable_units.append(UnitType.LAND_HEALER_1)
            if spawnable_units:
                chosen_unit = random.choice(spawnable_units)
                rc.spawn_unit(chosen_unit, ally_castle_id)

        # ===============================
        # Build a Farm for Extra Coins
        # ===============================
        # Attempt to build a FARM_1 adjacent to our main castle
        base_x, base_y = ally_castle.x, ally_castle.y
        directions = [
            Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT,
            Direction.UP_LEFT, Direction.UP_RIGHT, Direction.DOWN_LEFT, Direction.DOWN_RIGHT
        ]
        for d in directions:
            new_x, new_y = rc.new_location(base_x, base_y, d)
            if rc.can_build_building(BuildingType.FARM_1, new_x, new_y):
                rc.build_building(BuildingType.FARM_1, new_x, new_y)
                break  # Build only one farm per turn

        # ===============================
        # Process All Units for Actions
        # ===============================
        my_unit_ids = rc.get_unit_ids(team)
        for unit_id in my_unit_ids:
            unit = rc.get_unit_from_id(unit_id)
            if unit is None:
                continue

            # Attack enemy castle if in range
            if rc.can_unit_attack_building(unit_id, enemy_castle_id):
                rc.unit_attack_building(unit_id, enemy_castle_id)
                continue  # Skip other actions for this unit

            # Special Unit Actions
            if unit.type == UnitType.ENGINEER:
                # Engineers build bridges if possible to help traverse water tiles.
                if rc.can_build_bridge(unit_id):
                    rc.build_bridge(unit_id)
                    continue
            elif unit.type == UnitType.EXPLORER:
                # Explorers perform a gold exploration when near an explorer building.
                nearby_buildings = rc.sense_buildings_within_radius(team, unit.x, unit.y, 1)
                for b in nearby_buildings:
                    if b.type == BuildingType.EXPLORER_BUILDING:
                        building_id = rc.get_id_from_building(b)[1]
                        if rc.can_explore(unit_id, building_id):
                            rc.explore_for_gold(unit_id, building_id)
                            break

            # Healer Logic: if this unit is a healer, try to mend wounded allies.
            if unit.type in [
                UnitType.LAND_HEALER_1, UnitType.LAND_HEALER_2, UnitType.LAND_HEALER_3,
                UnitType.WATER_HEALER_1, UnitType.WATER_HEALER_2, UnitType.WATER_HEALER_3
            ]:
                for ally in rc.get_units(team):
                    ally_id = rc.get_id_from_unit(ally)[1]
                    # Assume the maximum health can be accessed via ally.type.health; otherwise use a default.
                    max_health = ally.type.health if hasattr(ally.type, 'health') else 10
                    if ally.health < 0.7 * max_health:
                        if rc.can_heal_unit(unit_id, ally_id):
                            rc.heal_unit(unit_id, ally_id)
                            break  # Heal one unit per healer per turn

            # ===============================
            # Movement: Advance Toward Enemy Castle
            # ===============================
            possible_dirs = rc.unit_possible_move_directions(unit_id)
            best_dir = None
            best_distance = float('inf')
            for d in possible_dirs:
                nx, ny = rc.new_location(unit.x, unit.y, d)
                distance = rc.get_chebyshev_distance(nx, ny, enemy_castle.x, enemy_castle.y)
                if distance < best_distance:
                    best_distance = distance
                    best_dir = d
            if best_dir and rc.can_move_unit_in_direction(unit_id, best_dir):
                rc.move_unit_in_direction(unit_id, best_dir)

        # ===============================
        # Use Buildings to Attack if Possible
        # ===============================
        my_building_ids = rc.get_building_ids(team)
        for b_id in my_building_ids:
            if rc.can_building_attack_location(b_id, enemy_castle.x, enemy_castle.y):
                rc.building_attack_location(b_id, enemy_castle.x, enemy_castle.y)

        return
