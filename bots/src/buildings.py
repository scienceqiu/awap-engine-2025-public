''' creates building objects (castle, farms, etc) '''
from src.game_constants import GameConstants, BuildingType, Team, BuildingRender

class Building:
    '''
    This is an extensible building class with all the traits of a building.
    The specifications for a building/unit is given in src/game_constants.py
    '''

    #ID for participants to interface through instead of through the actual object for safety
    id_counter = 0
    
    def __init__(self, team: Team, type: BuildingType, x: int, y: int, level: int = 1, spawnable: bool= False):

        self.id = self.increment()

        self.team = team
        self.type = type
        self.x = x
        self.y = y
        
        self.health = type.health
        self.damage = type.damage
        self.defense = type.defense

        self.attack_range = type.attack_range
        self.damage_range = type.damage_range

        #cannot move and cannot act the turn of its spawn
        self.turn_actions_remaining = 0

        self.level = level

        self.spawnable = type.spawnable

        self.placeable_tiles = type.placeable_tiles #tiles that the building can be placed on


    @staticmethod
    def increment() -> int:
        res = Building.id_counter
        Building.id_counter += 1
        return res

    def to_dict(self):
        """
        Converts the building into a dictionary representation for JSON replay files.
        """
        return {
            "id": self.id,
            "team": self.team.name if hasattr(self.team, 'name') else str(self.team),
            "type": self.type.name if hasattr(self.type, 'name') else str(self.type),
            "x": self.x,
            "y": self.y,
            "health": self.health,
            "damage": self.damage,
            "defense": self.defense,
            "attack_range": self.attack_range,
            "damage_range": self.damage_range,
            "turn_actions_remaining": self.turn_actions_remaining,
            "level": self.level
        }

    

