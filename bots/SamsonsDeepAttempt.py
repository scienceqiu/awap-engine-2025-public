from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType
from src.units import Unit
from src.buildings import Building

class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map
        self.enemy_castle_loc = None  # Track enemy's main location

    def play_turn(self, rc: RobotController):
        ally_team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()
        balance = rc.get_balance(ally_team)

        # Step 1: Build Farms to boost economy
        if BuildingType.FARM_1.cost <= balance:
            for x in range(self.map.width):
                for y in range(self.map.height):
                    if rc.can_build_building(BuildingType.FARM_1, x, y):
                        rc.build_building(BuildingType.FARM_1, x, y)
                        break  # Build one farm per turn to spread out

        # Step 2: Build Explorer Building once affordable
        ally_buildings = rc.get_buildings(ally_team)
        explorer_building_exists = any(b.type == BuildingType.EXPLORER_BUILDING for b in ally_buildings)
        if not explorer_building_exists and balance >= BuildingType.EXPLORER_BUILDING.cost:
            for x in range(self.map.width):
                for y in range(self.map.height):
                    if rc.can_build_building(BuildingType.EXPLORER_BUILDING, x, y):
                        rc.build_building(BuildingType.EXPLORER_BUILDING, x, y)
                        break

        # Step 3: Spawn Units from Main Castle
        ally_castle = next((b for b in ally_buildings if b.type == BuildingType.MAIN_CASTLE), None)
        if ally_castle:
            ally_castle_id = rc.get_id_from_building(ally_castle)[1]
            # Determine unit composition (60% Knight, 30% Healer, 10% Engineer)
            units = rc.get_units(ally_team)
            knight_count = sum(1 for u in units if u.type == UnitType.KNIGHT)
            healer_count = sum(1 for u in units if u.type in [UnitType.LAND_HEALER_1, UnitType.LAND_HEALER_2, UnitType.LAND_HEALER_3])
            engineer_count = sum(1 for u in units if u.type == UnitType.ENGINEER)
            total_units = len(units)

            if total_units == 0:
                if rc.can_spawn_unit(UnitType.KNIGHT, ally_castle_id):
                    rc.spawn_unit(UnitType.KNIGHT, ally_castle_id)
            else:
                desired_knights = int(total_units * 0.6)
                desired_healers = int(total_units * 0.3)
                desired_engineers = int(total_units * 0.1)

                if knight_count < desired_knights and rc.can_spawn_unit(UnitType.KNIGHT, ally_castle_id):
                    rc.spawn_unit(UnitType.KNIGHT, ally_castle_id)
                elif healer_count < desired_healers and rc.can_spawn_unit(UnitType.LAND_HEALER_1, ally_castle_id):
                    rc.spawn_unit(UnitType.LAND_HEALER_1, ally_castle_id)
                elif engineer_count < desired_engineers and rc.can_spawn_unit(UnitType.ENGINEER, ally_castle_id):
                    rc.spawn_unit(UnitType.ENGINEER, ally_castle_id)
                elif rc.can_spawn_unit(UnitType.KNIGHT, ally_castle_id):
                    rc.spawn_unit(UnitType.KNIGHT, ally_castle_id)

        # Step 4: Spawn Explorers from Explorer Building
        explorer_building = next((b for b in ally_buildings if b.type == BuildingType.EXPLORER_BUILDING), None)
        if explorer_building:
            eb_id = rc.get_id_from_building(explorer_building)[1]
            if rc.can_spawn_unit(UnitType.EXPLORER, eb_id):
                rc.spawn_unit(UnitType.EXPLORER, eb_id)

        # Step 5: Perform Gold Explorations
        explorers = [u for u in rc.get_units(ally_team) if u.type == UnitType.EXPLORER]
        for explorer in explorers:
            ex_id = rc.get_id_from_unit(explorer)[1]
            # Check if explorer is on the explorer building
            buildings_here = rc.sense_buildings_within_radius(ally_team, explorer.x, explorer.y, 0)
            if buildings_here and buildings_here[0].type == BuildingType.EXPLORER_BUILDING:
                eb_id = rc.get_id_from_building(buildings_here[0])[1]
                if rc.can_explore(ex_id, eb_id):
                    rc.explore_for_gold(ex_id, eb_id)

        # Step 6: Update Enemy Castle Location
        enemy_castle = next((b for b in rc.get_buildings(enemy_team) if b.type == BuildingType.MAIN_CASTLE), None)
        if enemy_castle:
            self.enemy_castle_loc = (enemy_castle.x, enemy_castle.y)
        else:
            # Target remaining buildings or units if castle is destroyed
            enemy_buildings = rc.get_buildings(enemy_team)
            if enemy_buildings:
                self.enemy_castle_loc = (enemy_buildings[0].x, enemy_buildings[0].y)
            else:
                enemy_units = rc.get_units(enemy_team)
                if enemy_units:
                    self.enemy_castle_loc = (enemy_units[0].x, enemy_units[0].y)
                else:
                    self.enemy_castle_loc = None

        # Step 7: Move Units and Attack
        ally_units = rc.get_units(ally_team)
        for unit in ally_units:
            unit_id = rc.get_id_from_unit(unit)[1]
            if self.enemy_castle_loc:
                ex, ey = self.enemy_castle_loc
                # Attack enemies in range
                enemy_units_near = rc.sense_units_within_radius(enemy_team, unit.x, unit.y, unit.type.attack_range)
                enemy_buildings_near = rc.sense_buildings_within_radius(enemy_team, unit.x, unit.y, unit.type.attack_range)
                attacked = False
                if enemy_units_near:
                    target_id = rc.get_id_from_unit(enemy_units_near[0])[1]
                    if rc.can_unit_attack_unit(unit_id, target_id):
                        rc.unit_attack_unit(unit_id, target_id)
                        attacked = True
                elif enemy_buildings_near:
                    target_id = rc.get_id_from_building(enemy_buildings_near[0])[1]
                    if rc.can_unit_attack_building(unit_id, target_id):
                        rc.unit_attack_building(unit_id, target_id)
                        attacked = True
                # Move towards enemy if not attacked
                if not attacked:
                    possible_dirs = rc.unit_possible_move_directions(unit_id)
                    if possible_dirs and self.enemy_castle_loc:
                        possible_dirs.sort(key=lambda d: rc.get_chebyshev_distance(*rc.new_location(unit.x, unit.y, d), ex, ey))
                        best_dir = possible_dirs[0]
                        if rc.can_move_unit_in_direction(unit_id, best_dir):
                            rc.move_unit_in_direction(unit_id, best_dir)

        # Step 8: Heal Injured Units
        healers = [u for u in ally_units if u.type in [UnitType.LAND_HEALER_1, UnitType.LAND_HEALER_2, UnitType.LAND_HEALER_3]]
        for healer in healers:
            healer_id = rc.get_id_from_unit(healer)[1]
            # Find injured allies in range
            injured_allies = []
            allies_in_range = rc.sense_units_within_radius(ally_team, healer.x, healer.y, healer.type.attack_range)
            for ally in allies_in_range:
                if ally.health < ally.type.health:
                    injured_allies.append(ally)
            if injured_allies:
                # Heal the most injured
                injured_allies.sort(key=lambda a: a.health)
                target_id = rc.get_id_from_unit(injured_allies[0])[1]
                if rc.can_heal_unit(healer_id, target_id):
                    rc.heal_unit(healer_id, target_id)

        # Step 9: Engineers Build Bridges
        engineers = [u for u in ally_units if u.type == UnitType.ENGINEER]
        for eng in engineers:
            eng_id = rc.get_id_from_unit(eng)[1]
            if rc.can_build_bridge(eng_id):
                rc.build_bridge(eng_id)
            else:
                # Move towards enemy castle
                if self.enemy_castle_loc:
                    ex, ey = self.enemy_castle_loc
                    possible_dirs = rc.unit_possible_move_directions(eng_id)
                    if possible_dirs:
                        possible_dirs.sort(key=lambda d: rc.get_chebyshev_distance(*rc.new_location(eng.x, eng.y, d), ex, ey))
                        best_dir = possible_dirs[0]
                        if rc.can_move_unit_in_direction(eng_id, best_dir):
                            rc.move_unit_in_direction(eng_id, best_dir)