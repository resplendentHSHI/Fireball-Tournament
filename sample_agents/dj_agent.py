#import random

class Stat:
	def a():
		print("hello")

class Agent:
	def __init__(self):
		self.loads = 0; self.opLoads = 0
		self.mirror = True; self.opMirror = True

		self.names = ["load","shield","fireball","tsunami","mirror"]
		self.base = [
			[0 , 1 , -2, -2, 1 ], #total 0
			[-1, 0 , 1 , -2, 1 ], #total -1
			[2 , -1, 0 , 1 , -2], #total 0
			[2 , 2 , -1, 0 , -2], #total 1
			[-1, -1, 2 , 2 , 0 ]  #total 2
		] 
	def reset(self):
		self.loads = 0; self.opLoads = 0
		self.mirror = True; self.opMirror = True
		
	def impossible(self, move,loads,mirror):
		return (move == 2 and loads < 1) or (move == 3 and loads < 2) or (move == 4 and not mirror)

 
	def play(self, opponent_last_move):
		if opponent_last_move == "mirror": self.opMirror = False
		elif opponent_last_move == "load": self.opLoads += 1
		elif opponent_last_move == "fireball": self.opLoads -= 1
		elif opponent_last_move == "tsunami": self.opLoads -= 2

		#print( self.loads,self.mirror , self.opLoads,self.opMirror )
		weight = []; bestScore = -1; bestMove = -1
		
		for i in range(5):
			if self.impossible( i, self.loads, self.mirror): continue
			sum = 0
			for j in range(5):
				if self.impossible( j, self.opLoads, self.opMirror): continue
				sum += self.base[i][j]

			if sum > bestScore: bestScore = sum; bestMove = self.names[i]
			
			weight.append( (sum,self.names[i]) )
			
		#print(weight, bestMove , bestScore)
		
		if bestMove == "mirror": self.mirror = False
		elif bestMove == "load": self.loads += 1
		elif bestMove == "fireball": self.loads -= 1
		elif bestMove == "tsunami": self.loads -= 2
		
		return bestMove


# Create an instance of the agent
agent = Agent()


# Define the play function for the tournament to use
def play(opponent_last_move):
  return agent.play(opponent_last_move)