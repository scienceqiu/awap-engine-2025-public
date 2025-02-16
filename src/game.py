''' Execution of the actual game; starts the game; keeps track of state informations'''

from typing import Optional

import importlib.util
import uuid

import sys
import os
from threading import Thread
import time
import copy
from typing import List, Dict
import json

from src.game_state import GameState
from src.game_constants import Team, GameConstants
from src.robot_controller import RobotController
from src.player import Player

from src.map_processor import process_map


def import_file(module_name, file_path):
    '''
    Imports a file given its full address
    This is used to import player modules from given files
    '''

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    sys.modules[module_name] = module
    return module



class Game:
    def __init__(self, blue_path: str, red_path: str, map_path: str, output_path: str, render= False):
        
        self.map = process_map(map_path)
        self.game_state = GameState(map=self.map)

        self.render = render
        self.output_path = output_path
        os.makedirs(os.path.dirname(output_path), exist_ok=True)


        #initialize players
        # NOTE: BotPlayer is the name of the class that the players input
        self.blue_failed_init = False
        try:
            blue_bot_name = os.path.basename(blue_path).split(".")[0]
            self.blue_player: Player = import_file(blue_bot_name, blue_path).BotPlayer(copy.deepcopy(self.map))
        except:
            blue_bot_name = "blue"
            self.blue_failed_init = True


        self.red_failed_init = False
        try:
            red_bot_name = os.path.basename(red_path).split(".")[0]
            self.red_player: Player = import_file(red_bot_name, red_path).BotPlayer(copy.deepcopy(self.map))
        except:
            red_bot_name = "red"
            self.red_failed_init = True


        #initialize controller
        self.blue_controller = RobotController(Team.BLUE, self.game_state)
        self.red_controller = RobotController(Team.RED, self.game_state)
        self.replay = []  # To store turn-by-turn replay information
        self.map = self.game_state.map.to_dict()

        self.turn_limit = 3000
        self.winner = None 

    def record_turn(self, turn_data: Dict):
        """Record data of the current turn into the replay."""
        # print(f'turn_data: {turn_data['game_state']['buildings']}')
        self.replay.append(turn_data)

    def export_replay(self, filename: str):
        self.replay.pop()
        """Export the replay object to a JSON file with the winner at the top level."""
        replay_data = {
            "ID": str(uuid.uuid4()),
            "map": self.map,
            "map-changes": {
                "changed-turns": self.game_state.changed_turns,
                "changed-maps": self.game_state.changed_maps
            },
            "winner_color": self.winner, 
            "replay": self.replay
        }
        with open(filename, 'w') as f:
            json.dump(replay_data, f, indent=4)


    def call_player_code(self, team: Team):
        '''Calls the player code of a given team'''

        player: Player = self.blue_player if team == Team.BLUE else self.red_player
        controller = self.blue_controller if team == Team.BLUE else self.red_controller

        # Create a thread that runs player.play_turn.
        # This function might not exist if the player code is broken, so we need to handle that.
        try:
            thread = Thread(target=player.play_turn, args=[controller], daemon=True)
        except:
            print(f"Failed to call player code for {team}. Are you inheriting the Player class?")
            return False

        # Run in separate thread with time limit
        func_time = time.time()
        thread.start()
        thread.join(self.game_state.time_remaining[team])
        func_time = time.time() - func_time

        # Check if thread timed out
        if thread.is_alive() or func_time > self.game_state.time_remaining[team]:
            self.game_state.time_remaining[team] = 0
            return False
        
        self.game_state.time_remaining[team] -= func_time
        return True
            
    
    def calculate_winner(self) -> Team:
        '''Win and tie breaking mechanics'''

        blue_lose = self.game_state.blue_main_castle_id not in self.game_state.buildings[Team.BLUE]  # blue castle destroyed
        red_lose = self.game_state.red_main_castle_id not in self.game_state.buildings[Team.RED]  # red castle destroyed

        # record last turn for replay file (health of one should be 0)
        turn_data = {
            "turn_number": len(self.replay)+1, 
            "game_state": self.game_state.to_dict(),  
        }

        self.record_turn(turn_data)


        # check if one main castle is destroyed while the other is not (definitive win)
        if blue_lose and not red_lose:
            print('RED WINS')
            self.winner = "RED"
            
            return Team.RED  # Red main castle still standing
        elif red_lose and not blue_lose:
            print('BLUE WINS')
            self.winner = "BLUE"
            return Team.BLUE  # Blue main castle still standing

        # turn limit reached case:
        # check if one main castle has more health than the other when they are both not destroyed
        if not blue_lose and not red_lose:
            blue_castle_health = self.game_state.buildings[Team.BLUE][self.game_state.blue_main_castle_id].health
            red_castle_health = self.game_state.buildings[Team.RED][self.game_state.red_main_castle_id].health

            if blue_castle_health != red_castle_health:
                # winner by castle health
                winner = Team.BLUE if blue_castle_health > red_castle_health else Team.RED
                winner_color = "BLUE" if winner == Team.BLUE else "RED"
                print(f'{winner_color} WINS')
                self.winner  = winner_color
                return winner

        # breaks tie by highest (total balance + tower cost + unit cost)
        total_balance = {
            Team.BLUE: self.game_state.balance[Team.BLUE],
            Team.RED: self.game_state.balance[Team.RED]
        }

        for team in Team:
            # add unit costs
            for unit in self.game_state.units[team].values():
                total_balance[team] += unit.type.cost
            # add building costs
            for building in self.game_state.buildings[team].values():
                total_balance[team] += building.type.cost

        if total_balance[Team.BLUE] > total_balance[Team.RED]:
            print('BLUE WINS')
            self.winner  = "BLUE"
            return Team.BLUE  # highest balance wins
        elif total_balance[Team.BLUE] < total_balance[Team.RED]:
            print('RED WINS')
            self.winner  = "RED"
            return Team.RED  # highest balance wins

        # Red arbitrarily wins because Red always moves second
        print('RED WINS')
        self.winner  = "RED"
        return Team.RED





    def run_turn(self) -> Optional[Team]:
        '''Runs the turn by running passive changes on game_state, and calls player turns'''


        #procedurally start the turn
        self.game_state.start_turn()

        #add time to each player
        self.game_state.time_remaining[Team.BLUE] += GameConstants.ADDITIONAL_TIME_PER_TURN
        self.game_state.time_remaining[Team.RED] += GameConstants.ADDITIONAL_TIME_PER_TURN


        #run player code, blue goes first then red
        blue_success = self.call_player_code(Team.BLUE)
        red_success = self.call_player_code(Team.RED)

        if not blue_success and not red_success:  # Both failed
            return self.calculate_winner()
        
        if not blue_success: # Blue failed
            print('RED WINS')
            self.winner = "RED"
            return Team.RED
        if not red_success: # Red failed
            print('BLUE WINS')
            self.winner = "BLUE"
            return Team.BLUE
        
        
        #check if game is over after the moves
        if (
            self.game_state.blue_main_castle_id not in self.game_state.buildings[Team.BLUE] 
            or self.game_state.red_main_castle_id not in self.game_state.buildings[Team.RED]
            ):
            return self.calculate_winner()
        

        turn_data = {
            "turn_number": len(self.replay) + 1, # Removed + 1 because the map now takes up one spot
            "game_state": self.game_state.to_dict(),  
        }

        self.record_turn(turn_data)

        return None

    def run_game(self) -> Optional[Team]:
        '''Initializes the bots and runs the game. Exports the JSON when finished'''

        # Check if we initialized players successfully
        if self.blue_failed_init and self.red_failed_init:
            print('Both blue and red failed to initialize. Nobody wins.')
            return None
        elif self.blue_failed_init:
            print("Blue failed to initialize. Red wins.")
            return Team.RED
        elif self.red_failed_init:
            print("Red failed to initialize. Blue wins.")
            return Team.BLUE


        for _ in range(self.turn_limit):
            if self.render:
                self.game_state.render()
                time.sleep(.1)

            winner = self.run_turn()

            if winner is not None:
                self.export_replay(self.output_path) 

                if self.render:
                    self.game_state.render()

                return winner
            

        self.export_replay(self.output_path)

        if self.render:
            self.game_state.render()
            
        return self.calculate_winner()
            