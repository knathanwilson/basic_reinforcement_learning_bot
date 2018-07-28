#import dependencies
import pygame		#for input events, and drawing
import time			#for time functionality
import random		#for random functionality
import numpy as np	#for mathematical arrays and functions

#optimization
dont_go_back = False
global_reward = False
dropout = .2

#seed random
random.seed = time.time()	#this allows the "random" to be different on every use

#general settings
datatype = np.float32

tile_size = (24, 24)		#the size of the visible colors
x_tiles = 6				#the number of horizontal tiles
y_tiles = 6				#the number of vertical tiles

UP = 0; RIGHT = 1; DOWN = 2; LEFT = 3	#the available actions
actions = [UP, RIGHT, DOWN, LEFT]
action_details = [(UP, DOWN, 0, 1), (RIGHT, LEFT, 1, 0), (DOWN, UP, 0, -1), (LEFT, RIGHT, -1, 0)]
action_size = len(actions)

#variables
app_running = True
restart = True
tile_w, tile_h = tile_size
cur_dropout = 0.0
node_count = x_tiles * y_tiles * action_size

#learning
timestep = 1
learning_rate = 1
score = 1

#agent
'''
The agent is what is learning to navigate its way through our world.
The agent can move in four different directions: up, right, down left.
The agent will have a matrix containing each of these actions to choose from.
The values will start off random (to ensure the algorithm works in dynamic
situations. The values will morph and change or "learn", as the agent navigates
its way through the world.
'''

	#has all available actions to the agent
agent_matrix = np.ones((x_tiles, y_tiles, action_size), dtype=datatype) * .1

agent_color = (255, 165, 0)	#color of the agent on the screen
agent_start_color = (230, 230, 230)

agent_start = (random.randint(0, x_tiles - 1), random.randint(0, y_tiles - 1))
agent_location = agent_start

steps_taken = []

def get_max_action (coords):
	'returns the max action at a specific location in the agent matrix'
	
	global agent_matrix, x_tiles, y_tiles
	global UP, RIGHT, DOWN, LEFT, action_size
	global agent_location, actions, dropout, node_count
	
	'''
	if dropout:
		places_dropped = []
		matrix = np.copy(agent_matrix)
		for count in range(int(dropout * node_count)):
			place = matrix[random.randint(
	else: matrix = agent_matrix
	'''
	matrix = agent_matrix
	
	x, y = coords
	
	type = UP
	value = min(matrix[x][y])
	
	for action in actions:
		current = matrix[x][y][action]
		if current > value:
			type = action
			value = current
			
	return type

def increase_action (coords, action, reward, discount, value):
	global agent_matrix, timestep
	x, y = coords
	agent_matrix[x][y][action] = reward * learning_rate

last_step = agent_location
def move_agent (action):
	global action_details, agent_location, agent_matrix, wall
	global score, world_matrix, restart, x_tiles, y_tiles
	global last_step, dropout
	
	last_x, last_y = agent_location
	
	for type, op_type, x_move, y_move in action_details:
		if type == action:
			
			#change the coords
			x = last_x + x_move
			y = last_y + y_move
			
			#check if agent can move this way
			if x < 0 or x >= x_tiles: return False
			if y < 0 or y >= y_tiles: return False
			if (x, y) in walls: return False
			if dont_go_back:
				if (x, y) == last_step: return False
			
			#get the value of the tile the agent is moving to
			value = world_matrix[x][y]
			
			#apply the value of the next step to the last step
			reward = -score
			score += value
			reward += score
			
			increase_action(agent_location, action, reward, .9, value)
			
			#check if special location
			for group, text in [(goals, 'Success: {0}'), (fails, 'Fail: {0}')]:
				for group_x, group_y in group:
					if x == group_x and y == group_y:
						restart = True
						
						if global_reward:
							#reward all steps that got us to this point
							apply_score = world_matrix[group_x][group_y]
							deduce = apply_score / len(steps)
							for location, action in reversed(steps):
								increase_action(location, action, apply_score, .3, apply_score)
								apply_score -= deduce
							
			
			#update agent location
			last_step = (last_x, last_y)
			agent_location = (x, y)
			
			#end function
			return True


#world
goals = []
goal_count = 1
goal_score = 1.0
goal_color = (0, 255, 0)

fails = []
fail_count = 1
fail_score = -goal_score
fail_color = (255, 0, 0)

walls = []
wall_count = 2
wall_color = (0, 0, 0)

world_matrix = np.ones((x_tiles, y_tiles), dtype=datatype) * .1

used_spaces = []
for group, count, score in [(goals, goal_count, goal_score),
							(fails, fail_count, fail_score),
							(walls, wall_count, 0),
							]:
	for unit in range(count):
		while True:
			coords = (random.randint(0, x_tiles - 1), random.randint(0, y_tiles - 1))
			cx, cy = coords
			ax, ay = agent_location
			if cx not in [ax - 1, ax, ax + 1]:
				if cy not in [ay - 1, ay, ay + 1]:
					if (cx, cy) not in used_spaces: break
		group.append(coords)
		used_spaces.append(coords)
		x, y = coords
		world_matrix[x][y] = score

#window
background_color = (255, 255, 255)
window = pygame.display.set_mode( (x_tiles * tile_w, y_tiles * tile_h) )	#create pygame window

def draw_rect(coords, color):
	global window, tile_w, x_tiles, tile_h, y_tiles
	x, y = coords
	pygame.draw.rect(window, color, (x * tile_w, (tile_h * y_tiles) - (y * tile_h) - tile_h, tile_w, tile_h))

def draw_circle(coords, color):
	global window, tile_w, x_tiles, tile_h, y_tiles
	x, y = coords
	
	pygame.draw.circle(window, color, (x * tile_w + tile_w / 2, (tile_h * y_tiles) - (y * tile_h) - tile_h + tile_h / 2), tile_w / 2)

#for debugging
view_current_actions = False

#run
print('Learning how to get to the goal. This make take a while...')

is_complete = False
steps = None
last_steps = []

while app_running:
	
	#check restart
	if restart:
		restart = False
		agent_location = agent_start
		timestep = 1
		learning_rate = .99
		score = 1
		if steps:
			is_complete = steps == last_steps
			last_steps = list(steps)
		steps = []
	
	#move agent
	while True:
		current_location = agent_location
		get_max = get_max_action(agent_location)
		if move_agent(get_max): break
		else:
			x, y = agent_location
			agent_matrix[x][y][get_max] = min(agent_matrix[x][y]) - 1
	steps.append((current_location, get_max))
	
	#update learning
	timestep += 1
	learning_rate *= .99
	
	#refresh screen
	pygame.display.flip()
	window.fill(background_color)

	#draw special tiles
	for group, color in [	(goals, goal_color), (fails, fail_color),
							([agent_start], agent_start_color),
							(walls, wall_color),
						]:
		for coords in group: draw_rect(coords, color)

	#draw agent
	draw_circle(agent_location, agent_color)

	#check for events (exit)
	pygame.event.pump()
	for event in pygame.event.get():
		if event.type == pygame.QUIT: app_running = False

	#wait for refresh
	if is_complete: time.sleep(.1)
