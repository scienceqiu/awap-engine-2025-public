from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType
from src.units import Unit
from src.buildings import Building
import random

class BotPlayer(Player):
    # Define a constant heal range for healer units (adjust as needed)
    HEAL_RANGE = 1

    def __init__(self, game_map: Map):
        self.map = game_map
        self.ally_castle_id = None
        self.enemy_castle_id = None
        self.explorer_building_built = False
        self.unit_spawn_distribution = [
            (UnitType.KNIGHT, 0.50),
            (UnitType.DEFENDER, 0.20),
            (UnitType.ENGINEER, 0.15),
            (UnitType.LAND_HEALER_1, 0.15)
        ]

    def play_turn(self, rc: RobotController):
        ally_team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()
        
        # Initialize castles if not done
        if self.ally_castle_id is None or self.enemy_castle_id is None:
            self.initialize_castles(rc, ally_team, enemy_team)
        
        # Skip if castles are invalid
        if self.ally_castle_id is None or self.enemy_castle_id not in rc.get_building_ids(enemy_team):
            return
        
        # Build farms around ally castle
        self.build_farms(rc, ally_team)
        
        # Build explorer building once
        if not self.explorer_building_built:
            self.build_explorer_building(rc, ally_team)
        
        # Spawn units from main castle
        self.spawn_units(rc, ally_team)
        
        # Spawn explorers from explorer building
        self.spawn_explorers(rc, ally_team)
        
        # Process all units
        self.command_units(rc, ally_team, enemy_team)

    def initialize_castles(self, rc: RobotController, ally_team: Team, enemy_team: Team):
        ally_buildings = rc.get_buildings(ally_team)
        for bldg in ally_buildings:
            if bldg.type == BuildingType.MAIN_CASTLE:
                self.ally_castle_id = rc.get_id_from_building(bldg)[1]
                break
        enemy_buildings = rc.get_buildings(enemy_team)
        for bldg in enemy_buildings:
            if bldg.type == BuildingType.MAIN_CASTLE:
                self.enemy_castle_id = rc.get_id_from_building(bldg)[1]
                break

    def build_farms(self, rc: RobotController, ally_team: Team):
        balance = rc.get_balance(ally_team)
        if balance < BuildingType.FARM_1.cost:
            return
        ally_castle = rc.get_building_from_id(self.ally_castle_id)
        if not ally_castle:
            return
        x, y = ally_castle.x, ally_castle.y
        radius = 5
        coords = [(x+dx, y+dy) for dx in range(-radius, radius+1) for dy in range(-radius, radius+1)
                  if rc.get_map().in_bounds(x+dx, y+dy)]
        random.shuffle(coords)
        for (nx, ny) in coords:
            if rc.can_build_building(BuildingType.FARM_1, nx, ny):
                rc.build_building(BuildingType.FARM_1, nx, ny)
                break

    def build_explorer_building(self, rc: RobotController, ally_team: Team):
        balance = rc.get_balance(ally_team)
        if balance < BuildingType.EXPLORER_BUILDING.cost:
            return
        for x in range(self.map.width):
            for y in range(self.map.height):
                if rc.can_build_building(BuildingType.EXPLORER_BUILDING, x, y):
                    rc.build_building(BuildingType.EXPLORER_BUILDING, x, y)
                    self.explorer_building_built = True
                    return

    def spawn_units(self, rc: RobotController, ally_team: Team):
        if not rc.can_spawn_unit(UnitType.KNIGHT, self.ally_castle_id):
            return
        roll = random.random()
        cumulative = 0.0
        for (unit_type, prob) in self.unit_spawn_distribution:
            cumulative += prob
            if roll <= cumulative:
                if rc.can_spawn_unit(unit_type, self.ally_castle_id):
                    rc.spawn_unit(unit_type, self.ally_castle_id)
                break

    def spawn_explorers(self, rc: RobotController, ally_team: Team):
        explorer_buildings = [b for b in rc.get_buildings(ally_team) if b.type == BuildingType.EXPLORER_BUILDING]
        for eb in explorer_buildings:
            eb_id = rc.get_id_from_building(eb)[1]
            if rc.can_spawn_unit(UnitType.EXPLORER, eb_id):
                rc.spawn_unit(UnitType.EXPLORER, eb_id)

    def command_units(self, rc: RobotController, ally_team: Team, enemy_team: Team):
        enemy_castle = rc.get_building_from_id(self.enemy_castle_id)
        if not enemy_castle:
            enemy_buildings = rc.get_buildings(enemy_team)
            if enemy_buildings:
                target = enemy_buildings[0]
            else:
                target = None
        else:
            target = enemy_castle
        
        for uid in rc.get_unit_ids(ally_team):
            unit = rc.get_unit_from_id(uid)
            if not unit:
                continue
            
            # Handle explorers on buildings
            if unit.type == UnitType.EXPLORER:
                nearby_buildings = rc.sense_buildings_within_radius(ally_team, unit.x, unit.y, 0)
                if nearby_buildings and nearby_buildings[0].type == BuildingType.EXPLORER_BUILDING:
                    eb_id = rc.get_id_from_building(nearby_buildings[0])[1]
                    if rc.can_explore(uid, eb_id):
                        rc.explore_for_gold(uid, eb_id)
                continue
            
            # Healer logic using a fixed heal range instead of unit.type.heal_range
            if unit.type in [UnitType.LAND_HEALER_1, UnitType.LAND_HEALER_2, UnitType.LAND_HEALER_3]:
                allies = rc.sense_units_within_radius(ally_team, unit.x, unit.y, BotPlayer.HEAL_RANGE)
                for ally in allies:
                    if ally.health < ally.type.health:
                        ally_id = rc.get_id_from_unit(ally)[1]
                        if rc.can_heal_unit(uid, ally_id):
                            rc.heal_unit(uid, ally_id)
                            break
            
            # Engineer logic: only attempt to build a bridge if on a WATER tile.
            if unit.type == UnitType.ENGINEER:
                current_tile = rc.get_map().tiles[unit.x][unit.y]
                if current_tile == Tile.WATER:
                    if rc.can_build_bridge(uid):
                        rc.build_bridge(uid)
                        continue
            
            # Attack or move towards target
            if target:
                tx, ty = target.x, target.y
                # Check attack if target is a building (assumed enemy castle)
                if isinstance(target, Building):
                    if rc.can_unit_attack_building(uid, self.enemy_castle_id):
                        rc.unit_attack_building(uid, self.enemy_castle_id)
                else:
                    enemies = rc.sense_units_within_radius(enemy_team, unit.x, unit.y, unit.type.attack_range)
                    if enemies:
                        enemy_id = rc.get_id_from_unit(enemies[0])[1]
                        if rc.can_unit_attack_unit(uid, enemy_id):
                            rc.unit_attack_unit(uid, enemy_id)
                
                # Move towards target
                dirs = rc.unit_possible_move_directions(uid)
                if dirs:
                    dirs.sort(key=lambda d: rc.get_chebyshev_distance(
                        *rc.new_location(unit.x, unit.y, d), tx, ty
                    ))
                    best_dir = dirs[0]
                    rc.move_unit_in_direction(uid, best_dir)
