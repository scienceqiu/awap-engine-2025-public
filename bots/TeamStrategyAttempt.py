from src.player import Player
from src.map import Map
from src.robot_controller import RobotController
from src.game_constants import Team, Tile, GameConstants, Direction, BuildingType, UnitType

class BotPlayer(Player):
    def __init__(self, game_map: Map):
        self.map = game_map
        self.main_castle_id = None
        self.enemy_team = None


    def should_deploy_rat(my_balance: int, enemy_balance: int) -> bool:
        """Determine if deploying a Rat is currently profitable."""
        if my_balance < UnitType.RAT.cost:  # Rat costs 10 coins
            return False
        my_loss = 0.2 * (my_balance - UnitType.RAT.cost) + UnitType.RAT.cost
        enemy_loss = 0.1 * enemy_balance
        return enemy_loss > my_loss

    def manage_rats(rc: RobotController):
        """Handle Rat deployment, movement, and activation logic."""
        ally_team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()
        my_balance = rc.get_balance(ally_team)
        enemy_balance = rc.get_balance(enemy_team)
        
        # Get relevant game objects
        farms = [b for b in rc.get_buildings(ally_team) 
                if b.type in (BuildingType.FARM_1, BuildingType.FARM_2, BuildingType.FARM_3)]
        rats = [u for u in rc.get_units(ally_team) if u.type == UnitType.RAT]

        # Process existing rats
        for rat in rats:
            rat_id = rc.get_id_from_unit(rat)[1]
            x, y = rat.x, rat.y
            
            # Check if rat is on a farm
            on_farm = any(
                rc.chebyshev_distance_valid(x, y, farm.x, farm.y, 0)
                for farm in farms
            )
            
            if on_farm:
                # Check if activation is currently profitable
                if (0.1 * enemy_balance) > (0.2 * my_balance):
                    if rc.can_harm_farm(rat_id):
                        rc.harm_farm(rat_id)
            else:
                # Pathfind to nearest farm
                if farms:
                    nearest_farm = min(
                        farms,
                        key=lambda f: rc.get_chebyshev_distance(x, y, f.x, f.y)
                    )
                    possible_dirs = rc.unit_possible_move_directions(rat_id)
                    if possible_dirs:
                        best_dir = min(
                            possible_dirs,
                            key=lambda d: rc.get_chebyshev_distance(
                                *rc.new_location(x, y, d),
                                nearest_farm.x,
                                nearest_farm.y
                            )
                        )
                        rc.move_unit_in_direction(rat_id, best_dir)

        # Deploy new rats if conditions met
        if farms and should_deploy_rat(my_balance, enemy_balance):
            # Find spawn points (main castle)
            spawn_buildings = [b for b in rc.get_buildings(ally_team)
                            if b.type == BuildingType.MAIN_CASTLE]
            
            for building in spawn_buildings:
                bid = rc.get_id_from_building(building)[1]
                if rc.can_spawn_unit(UnitType.RAT, bid):
                    rc.spawn_unit(UnitType.RAT, bid)
                    break  # Only spawn one per turn

    def play_turn(self, rc: RobotController):
        ally_team = rc.get_ally_team()
        enemy_team = rc.get_enemy_team()

        our_balance = rc.get_balance(ally_team)
        enemy_balance = rc.get_balance(enemy_team)

        if(should_deploy_rat(our_balance,enemy_balance)):
