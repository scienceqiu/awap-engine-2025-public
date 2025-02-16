''' contains unit classes (soldiers, farmers, builders, etc.) '''

from src.game_constants import GameConstants, UnitType, Team, UnitRender

class Unit:
    '''
    This is an extensible unit class with all the traits of a building.
    The specifications for a building/unit is given in src/game_constants.py
    '''

    #ID for participants to interface through instead of through the actual object for safety
    id_counter = 0
    
    def __init__(self, team: Team, type: UnitType, x: int, y: int, level: int = 1):

        self.id = self.increment()

        self.team = team
        self.type = type
        self.x = x
        self.y = y

        #cannot move and cannot act the turn of its spawn
        self.turn_actions_remaining = 0
        self.turn_movement_remaining = 0

        self.attack_range = type.attack_range

        self.health = self.type.health
        self.damage = self.type.damage
        self.defense = type.defense
        self.damage_range = self.type.damage_range

        self.level = level

        self.walkable_tiles = self.type.walkable_tiles

    @staticmethod
    def increment() -> int:
        res = Unit.id_counter
        Unit.id_counter += 1
        return res

    def to_dict(self):
        """
        Converts the unit into a dictionary representation.
        """
        return {
            "id": self.id,
            "team": self.team.name if hasattr(self.team, 'name') else str(self.team),
            "type": self.type.name if hasattr(self.type, 'name') else str(self.type),
            "x": self.x,
            "y": self.y,
            "turn_actions_remaining": self.turn_actions_remaining,
            "turn_movement_remaining": self.turn_movement_remaining,
            "attack_range": self.attack_range,
            "health": self.health,
            "damage": self.damage,
            "defense": self.defense,
            "damage_range": self.damage_range,
            "level": self.level
        }