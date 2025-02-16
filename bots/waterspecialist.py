from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType
from typing import List, Tuple
import heapq

class EngineerLogic:
    def __init__(self, rc: RobotController, map: Map, ally_team: Team):
        self.rc = rc
        self.map = map
        self.ally_team = ally_team
        self.enemy_team = Team.RED if ally_team == Team.BLUE else Team.BLUE
        self.engineers = []  # List of engineer unit IDs
        self.bridge_path = []  # Path of tiles where bridges need to be built
        self.bridge_index = 0  # Index in the bridge_path to build the next bridge

    def should_build_engineer(self) -> bool:
        self.update_engineers(self.ally_team)
        # Check if there is already a path between the castles
        if self._path_exists_between_castles():
            return False  # No need to build engineers if a path already exists

        # If no path exists, calculate the bridge path using Dijkstra
        if(not(self.bridge_path)):
            self.bridge_path = self._calculate_bridge_path()
            self.bridge_path.pop()

        # If no engineers are alive and the turn is at least 5, build an engineer
        if len(self.bridge_path)-self.bridge_index-len(self.engineers)>0:
            return True

        return False

    def update_engineers(self,team: Team):
        self.engineers=[]
        allies = self.rc.get_units(team)
        for troops in allies:
            if troops.type == UnitType.ENGINEER:
                self.engineers+=[troops.id]

    def play_engineers(self):
        for engineer_id in self.engineers:
            if self.bridge_index >= len(self.bridge_path):
                continue  # No more bridges to build

            target_x, target_y = self.bridge_path[self.bridge_index]

            self._move_towards(engineer_id, target_x, target_y)

            if self.rc.can_build_bridge(engineer_id):
                self.rc.build_bridge(engineer_id)
                self.bridge_index += 1  # Move to the next bridge in the path

    def _path_exists_between_castles(self) -> bool:
        # Get the positions of the ally and enemy castles
        ally_castle = self._find_castle(self.ally_team)
        enemy_castle = self._find_castle(self.enemy_team)

        if not ally_castle or not enemy_castle:
            return False  # No castles found, should not happen

        # Use BFS to check if a path exists between the castles
        visited = set()
        queue = [(ally_castle[0], ally_castle[1])]

        while queue:
            x, y = queue.pop(0)
            if (x, y) == enemy_castle:
                return True  # Path exists

            if (x, y) in visited:
                continue
            visited.add((x, y))

            # Explore all 8 possible directions (Chebyshev movement)
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1),
                           (0, -1),          (0, 1),
                           (1, -1),  (1, 0), (1, 1)]:
                new_x, new_y = x + dx, y + dy
                if self.map.in_bounds(new_x, new_y) and self.map.is_tile_type(new_x, new_y, Tile.GRASS):
                    queue.append((new_x, new_y))

        return False  # No path found

    def _calculate_bridge_path(self) -> List[Tuple[int, int]]:
        # Get the positions of the ally and enemy castles
        ally_castle = self._find_castle(self.ally_team)
        enemy_castle = self._find_castle(self.enemy_team)

        if not ally_castle or not enemy_castle:
            return []  # No castles found, should not happen

        # Dijkstra's algorithm to find the path with the minimum number of rivers
        heap = [(0, ally_castle[0], ally_castle[1], [])]  # (number of rivers, x, y, path)
        visited = set()

        while heap:
            rivers, x, y, path = heapq.heappop(heap)
            if (x, y) == enemy_castle:
                return path  # Return the path with the minimum number of rivers

            if (x, y) in visited:
                continue
            visited.add((x, y))

            # Explore all 8 possible directions (Chebyshev movement)
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1),
                           (0, -1),          (0, 1),
                           (1, -1),  (1, 0), (1, 1)]:
                new_x, new_y = x + dx, y + dy
                if not self.map.in_bounds(new_x, new_y):
                    continue

                # Calculate the number of rivers in the new path
                new_rivers = rivers
                if self.map.is_tile_type(new_x, new_y, Tile.WATER):
                    new_rivers += 1

                heapq.heappush(heap, (new_rivers, new_x, new_y, path + [(new_x, new_y)]))

        return []  # No path found

    def _find_castle(self, team: Team) -> Tuple[int, int]:
        ally_buildings = self.rc.get_buildings(team)
        for building in ally_buildings:
            if building.type == BuildingType.MAIN_CASTLE:
                return (building.x,building.y)


    def _move_towards(self, unit_id: int, target_x: int, target_y: int) -> bool:
        possible_dirs = self.rc.unit_possible_move_directions(unit_id)
        unit = self.rc.get_unit_from_id(unit_id)
        if possible_dirs:
            sorted_dirs = sorted(possible_dirs,key=lambda d: self.rc.get_chebyshev_distance(*self.rc.new_location(unit.x, unit.y, d), target_x,target_y))
            best_dir = sorted_dirs[0]
            self.rc.move_unit_in_direction(unit_id, best_dir)


class BotPlayer(Player):
    def __init__(self, game_map: Map):
        self.map = game_map
        self.main_castle_id = None
        self.enemy_team = None
        self.engineer = 0

    def play_turn(self, rc: RobotController):
        if(self.engineer==0):
            self.engineer=EngineerLogic(rc,self.map,rc.get_ally_team())
        self.engineer.rc=rc
        ally_team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()
        self.enemy_team = enemy_team

        # Always fetch the current balance from rc instead of relying solely on a local variable.
        balance = rc.get_balance(ally_team)

        # Locate main castle once
        if self.main_castle_id is None:
            ally_buildings = rc.get_buildings(ally_team)
            for building in ally_buildings:
                if building.type == BuildingType.MAIN_CASTLE:
                    self.main_castle_id = rc.get_id_from_building(building)[1]
                    break

        self.engineer.play_engineers()
        # Spawn engineers with remaining balance
        if(self.engineer.should_build_engineer()):
            engineer_cost = UnitType.ENGINEER.cost
            if balance >= engineer_cost:
                if rc.can_spawn_unit(UnitType.ENGINEER, self.main_castle_id):
                    rc.spawn_unit(UnitType.ENGINEER, self.main_castle_id)

        # If main castle is destroyed, exit
        if self.main_castle_id is None:
            return

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

        if(not(self.engineer.should_build_engineer())):
            # Spawn as many catapults as possible
            catapult_cost = UnitType.CATAPULT.cost
            while balance >= catapult_cost:
                if rc.can_spawn_unit(UnitType.CATAPULT, self.main_castle_id):
                    rc.spawn_unit(UnitType.CATAPULT, self.main_castle_id)
                    balance -= catapult_cost
                else:
                    break

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
