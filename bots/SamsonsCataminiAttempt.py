from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType
from src.units import Unit
from src.buildings import Building

# This version forces any CATAPULT in the spawn area (castle tile and its 8 neighbors)
# to move away so that new catapults can spawn.
class BotPlayer(Player):
    def __init__(self, map: Map):
        self.map = map

    def play_turn(self, rc: RobotController):
        ally_team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()
        
        # --- Identify Our Main Castle ---
        ally_castle = None
        ally_castle_id = None
        for b in rc.get_buildings(ally_team):
            if b.type == BuildingType.MAIN_CASTLE:
                ally_castle = b
                ally_castle_id = rc.get_id_from_building(b)[1]
                break
        if ally_castle is None or ally_castle_id is None:
            return
        
        castle_x, castle_y = ally_castle.x, ally_castle.y
        
        # Define spawn area: castle tile plus adjacent 8 tiles.
        spawn_area = set()
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                spawn_area.add((castle_x + dx, castle_y + dy))
        
        # --- Identify the Enemy Main Castle ---
        enemy_castle = None
        enemy_castle_id = None
        for b in rc.get_buildings(enemy_team):
            if b.type == BuildingType.MAIN_CASTLE:
                enemy_castle = b
                enemy_castle_id = rc.get_id_from_building(b)[1]
                break
        if enemy_castle is None or enemy_castle_id is None:
            return

        # --- Movement Phase ---
        # For every CATAPULT, allow up to two moves in this turn.
        for unit_id in rc.get_unit_ids(ally_team):
            unit = rc.get_unit_from_id(unit_id)
            if unit is None or unit.type != UnitType.CATAPULT:
                continue
            
            moves_made = 0
            while moves_made < 2:
                # Refresh unit state in case it has moved.
                unit = rc.get_unit_from_id(unit_id)
                if unit is None:
                    break

                # If the unit is NOT in the spawn area and enemy castle is in attack range, attack.
                if (unit.x, unit.y) not in spawn_area:
                    if rc.can_unit_attack_building(unit_id, enemy_castle_id):
                        rc.unit_attack_building(unit_id, enemy_castle_id)
                        break  # Stop moving after attacking.
                
                # Determine movement vector:
                # If unit is in the spawn area, force move using the vector from the castle;
                # otherwise, use the vector from the unit's current position.
                if (unit.x, unit.y) in spawn_area:
                    dx = enemy_castle.x - castle_x
                    dy = enemy_castle.y - castle_y
                else:
                    dx = enemy_castle.x - unit.x
                    dy = enemy_castle.y - unit.y

                # Determine horizontal and vertical directions.
                horiz = Direction.RIGHT if dx > 0 else (Direction.LEFT if dx < 0 else None)
                vert = Direction.UP if dy > 0 else (Direction.DOWN if dy < 0 else None)
                
                # Build list of preferred movement directions.
                preferred = []
                if horiz and vert:
                    if horiz == Direction.RIGHT and vert == Direction.UP:
                        preferred = [Direction.UP_RIGHT, Direction.RIGHT, Direction.UP]
                    elif horiz == Direction.RIGHT and vert == Direction.DOWN:
                        preferred = [Direction.DOWN_RIGHT, Direction.RIGHT, Direction.DOWN]
                    elif horiz == Direction.LEFT and vert == Direction.UP:
                        preferred = [Direction.UP_LEFT, Direction.LEFT, Direction.UP]
                    elif horiz == Direction.LEFT and vert == Direction.DOWN:
                        preferred = [Direction.DOWN_LEFT, Direction.LEFT, Direction.DOWN]
                elif horiz:
                    preferred = [horiz]
                elif vert:
                    preferred = [vert]
                else:
                    preferred = [Direction.STAY]
                
                moved = False
                # Try moving in one of the preferred directions.
                for d in preferred:
                    if rc.can_move_unit_in_direction(unit_id, d):
                        rc.move_unit_in_direction(unit_id, d)
                        moves_made += 1
                        moved = True
                        break
                # Fallback: try any valid move if no preferred direction worked.
                if not moved:
                    for d in rc.unit_possible_move_directions(unit_id):
                        if rc.can_move_unit_in_direction(unit_id, d):
                            rc.move_unit_in_direction(unit_id, d)
                            moves_made += 1
                            moved = True
                            break
                    # If no move is available, exit.
                    if not moved:
                        break

        # --- Spawn Phase ---
        # After moving catapults (especially from the spawn area), try to spawn a new CATAPULT.
        if rc.can_spawn_unit(UnitType.CATAPULT, ally_castle_id):
            rc.spawn_unit(UnitType.CATAPULT, ally_castle_id)
            
        return
