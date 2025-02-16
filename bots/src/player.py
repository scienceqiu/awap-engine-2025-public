''' specifies a player object that the player can write to, which runs their code '''


from src.robot_controller import RobotController
from src.map import Map


class Player:
	'''
	Players will write a child class of the Player class, specifically writing the play_turn method
	'''
	def __init__(self, map: Map):
		pass


	def play_turn(self, rc: RobotController):
		raise NotImplementedError()
