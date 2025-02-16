"""
NOTE: This bot was partially generated using a large language model (LLM).
In compliance with AWAP rules, we disclose and document the usage below:

# LLM Usage
# - Strategy outline
# - Comments explaining the code
# - Some function name suggestions

Please modify this code as needed for your own strategy!
"""

from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import (
    Team,
    Tile,
    GameConstants,
    Direction,
    BuildingType,
    UnitType
)
from src.units import Unit
from src.buildings import Building
import random


class BotPlayer(Player):
    def __init__(self, game_map: Map):
        """
        On initialization, store the map for reference in future turns.
        """
        self.map = game_map

        # We can store relevant IDs or positions from the first turn
        self.ally_castle_id = None
        self.enemy_castle_id = None

        # These thresholds or proportions can be tuned.
        self.MIN_BALANCE_FOR_FARM = 30
        self.MIN_BALANCE_FOR_PORT = 25
        self.FARM_BUILD_RADIUS = 3  # distance from castle to attempt farm building

        # Probability-based spawn distribution for land units:
        self.unit_spawn_choices = [
            (UnitType.KNIGHT, 0.50),
            (UnitType.DEFENDER, 0.20),
            (UnitType.ENGINEER, 0.15),
            (UnitType.LAND_HEALER_1, 0.15),
        ]

    def play_turn(self, rc: RobotController):
        """
        This method is called each turn. Your code here decides what to build,
        what units to spawn, and how to move/attack with them.
        """

        # --- 1. Identify ally/enemy information ---
        team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()

        # On the first turn, record the main castles' IDs (if not already).
        if self.ally_castle_id is None or self.enemy_castle_id is None:
            self._initialize_castles(rc, team, enemy_team)

        # If enemy castle is somehow gone, we can end early this turn.
        if self.enemy_castle_id not in rc.get_building_ids(enemy_team):
            return

        # --- 2. Possibly build farms (or other buildings) near our main castle ---
        self._attempt_build_farms(rc, team)

        # --- 3. Spawn units if we have enough resources ---
        self._attempt_spawn_units(rc, team)

        # --- 4. Move and attack with all allied units ---
        self._command_units(rc, team, enemy_team)

    # --------------------------------------------------------------------------
    #                           HELPER METHODS
    # --------------------------------------------------------------------------

    def _initialize_castles(self, rc: RobotController, team: Team, enemy_team: Team):
        """
        Helper to detect our castle and enemy castle IDs exactly once.
        """
        ally_buildings = rc.get_buildings(team)
        for bldg in ally_buildings:
            if bldg.type == BuildingType.MAIN_CASTLE:
                self.ally_castle_id = rc.get_id_from_building(bldg)[1]
                break

        enemy_buildings = rc.get_buildings(enemy_team)
        for bldg in enemy_buildings:
            if bldg.type == BuildingType.MAIN_CASTLE:
                self.enemy_castle_id = rc.get_id_from_building(bldg)[1]
                break

    def _attempt_build_farms(self, rc: RobotController, team: Team):
        """
        Example strategy: If we have enough balance, try building farms near
        our main castle. This increases passive income. We only build 
        Farm (Tier 1) for simplicity; you can upgrade to Tier 2/3 if you like.
        """

        balance = rc.get_balance(team)
        if balance < self.MIN_BALANCE_FOR_FARM or self.ally_castle_id is None:
            return

        castle_obj = rc.get_building_from_id(self.ally_castle_id)
        if castle_obj is None:
            return

        castle_x, castle_y = castle_obj.x, castle_obj.y
        # Look around the castle in a small radius for valid spots
        coords_to_check = []
        for dx in range(-self.FARM_BUILD_RADIUS, self.FARM_BUILD_RADIUS + 1):
            for dy in range(-self.FARM_BUILD_RADIUS, self.FARM_BUILD_RADIUS + 1):
                x = castle_x + dx
                y = castle_y + dy
                if rc.get_map().in_bounds(x, y):
                    coords_to_check.append((x, y))

        random.shuffle(coords_to_check)

        # Attempt to build a Tier 1 Farm in the first valid location found
        for (x, y) in coords_to_check:
            # Only build on Grass/Sand/Bridge if allowed, etc.
            if rc.can_build_building(BuildingType.FARM_1, x, y):
                rc.build_building(BuildingType.FARM_1, x, y)
                # Build only one farm per turn to save resources for units
                break

    def _attempt_spawn_units(self, rc: RobotController, team: Team):
        """
        Spawns land units from our main castle with certain probabilities.
        (You can expand logic to use other buildings or water units from Ports.)
        """

        if self.ally_castle_id is None:
            return

        # If our castle can spawn, pick a random unit based on the distribution.
        # Example distribution: Knight (50%), Defender (20%), Engineer (15%), 
        # Land Healer (15%).
        roll = random.random()
        cumulative = 0.0
        for (u_type, prob) in self.unit_spawn_choices:
            cumulative += prob
            if roll <= cumulative:
                if rc.can_spawn_unit(u_type, self.ally_castle_id):
                    rc.spawn_unit(u_type, self.ally_castle_id)
                break

    def _command_units(self, rc: RobotController, team: Team, enemy_team: Team):
        """
        Each turn, move our units and try to attack enemy structures or units.
        """
        if self.enemy_castle_id is None:
            return

        enemy_castle = rc.get_building_from_id(self.enemy_castle_id)
        if not enemy_castle:
            return

        # For reference
        enemy_x, enemy_y = enemy_castle.x, enemy_castle.y

        # Gather all our units
        my_unit_ids = rc.get_unit_ids(team)

        # Move and/or attack with each
        for uid in my_unit_ids:
            unit_obj = rc.get_unit_from_id(uid)
            if unit_obj is None:
                continue

            # 1) If we can attack the enemy castle directly, do it
            if rc.can_unit_attack_building(uid, self.enemy_castle_id):
                rc.unit_attack_building(uid, self.enemy_castle_id)
                # If we successfully attacked, no need to move afterwards
                # (but you could do it in whichever order if needed)

            else:
                # 2) Move the unit closer to enemy castle
                move_dirs = rc.unit_possible_move_directions(uid)
                if not move_dirs:
                    continue

                # Sort by how close they get us to the enemy castle
                move_dirs.sort(
                    key=lambda d: rc.get_chebyshev_distance(
                        *rc.new_location(unit_obj.x, unit_obj.y, d),
                        enemy_x, enemy_y
                    )
                )

                best_dir = move_dirs[0]
                if rc.can_move_unit_in_direction(uid, best_dir):
                    rc.move_unit_in_direction(uid, best_dir)

                # 3) (Optional) Attack nearby enemy units after moving
                #    Here’s a simple example of attacking any enemy in range.
                enemy_units_in_range, enemy_bldgs_in_range = rc.sense_objects_within_unit_range(
                    enemy_team, uid
                )

                # Attack any unit if possible
                for enemy_unit in enemy_units_in_range:
                    e_id = rc.get_id_from_unit(enemy_unit)[1]
                    if rc.can_unit_attack_unit(uid, e_id):
                        rc.unit_attack_unit(uid, e_id)
                        # If we want just one attack per turn for this example:
                        break

                # Optionally, we can also do special checks: healing, building bridges, etc.
                if unit_obj.type == UnitType.ENGINEER:
                    # If we can build a bridge at our location, do so:
                    if rc.can_build_bridge(uid):
                        rc.build_bridge(uid)
                elif "HEALER" in unit_obj.type.name:
                    # Randomly try healing an ally if one is in range and damaged
                    allies_in_range, _ = rc.sense_objects_within_unit_range(team, uid)
                    for ally_unit in allies_in_range:
                        ally_unit_id = rc.get_id_from_unit(ally_unit)[1]
                        if rc.can_heal_unit(uid, ally_unit_id):
                            rc.heal_unit(uid, ally_unit_id)
                            break
                # ... Additional special unit logic can go here.


#
# END OF BotPlayer
#
