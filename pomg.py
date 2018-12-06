import sys, pygame, math, random

pygame.init()

size = (sWidth, sHeight) = (800, 600)
gamespeed = 1 # Global game speed. WARNING: Frames will be missed if set over ~30.
scoremax = 100
play = True
black = (0, 0, 0)
red = (255, 0, 0)
blue = (0, 0, 255)
white = (255, 255, 255)
gray = (64, 64, 64)

screen = pygame.display.set_mode(size)
pygame.display.set_caption("Pomg")
clock = pygame.time.Clock()

if pygame.font:
	font = pygame.font.Font(None, 100)
	p1scorepos = (sWidth/2-75, 20)
	p2scorepos = (sWidth/2+35, 20)
	
padding = 10
cWidth = sWidth-2*padding
cHeight = sHeight-2*padding

court_left		= padding
court_right		= sWidth-padding
court_top		= padding
court_bottom	= sHeight-padding


# Initialize ball settings
class Ball:
	radius = 10
	speed = 0.5*gamespeed
	x, y = 0, 0
	xvel, yvel = 0, 0
	lastscore = 'p2' # default to p2 so game starts with p1's serve
	
	def reset(self):
		# After a point, reset ball's location to side of player who was scored on
		if self.lastscore == 'p2':
			self.x = p1.x + p1.w + self.radius + 2
			self.y = p1.y + (p1.h/2)
			
			self.vel_init(1)
			
		if self.lastscore == 'p1':
			self.x = p2.x - self.radius - 2
			self.y = p2.y + (p2.h/2)
			
			self.vel_init(-1)
			
	def vel_init(self, dir):
		# Initialize ball velocity with negative x velocity for dir=-1 and positive x velocity for dir=1
		ball.xvel = dir*(random.random()*0.4 + 0.6)*ball.speed
		ball.yvel = (random.randint(0, 1)*2 - 1) * math.sqrt(ball.speed**2 - ball.xvel**2)  # the random call here chooses a direction, either 1 or -1

ball = Ball()


# Initialize paddle settings
class Paddle:
	h = 80
	w = 20
	speed = 0.4*gamespeed
	x, y = 0, 0
	velmod = 0	# -1 for up, 1 for down, 0 for stop
	score = 0
	center = (0,0)
	drift = 0
	drift_sign = 1
	
	def up(self):
		self.velmod = -1
	def down(self):
		self.velmod = 1
	def stop(self):
		self.velmod = 0
	
	def center(self):
		return (self.x+(self.w/2), self.y+(self.h/2))
		
	
p1 = Paddle()
p1.x = court_left+10
p1.y = sHeight/2
	
p2 = Paddle()
p2.x = court_right-p2.w-10
p2.y = sHeight/2

ball.reset()

## RandomAI Settings ##
# Max drift distance allowed by each difficulty, expressed as percentage of paddle height
drift_cap = {'Easy': 2.5, 'Medium': 2.0, 'Hard': 1.4, 'Perfect': 0.75}
# Start two separate random seeds for two different players
rand1 = random.Random(random.randint(1, 100))
rand2 = random.Random(random.randint(1, 100)+100)


while play:
	clock.tick()
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit()
		# Check for input
		elif event.type == pygame.KEYDOWN:
			if event.key == pygame.K_UP:
				p1.up()
				p2.up()
			if event.key == pygame.K_DOWN:
				p1.down()
				p2.down()
		elif event.type == pygame.KEYUP:
			if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
				p1.stop()
				p2.stop()

	screen.fill(black)
	
	### Draw court ###

	pygame.draw.rect(screen, white, (padding, padding, sWidth-2*padding, sHeight-2*padding), 6)
	num_lines = 32
	line_height = 8
	for i in range(num_lines):
		pygame.draw.line(screen, white, ( sWidth/2, i*(cHeight/num_lines)+padding ), ( sWidth/2, i*(cHeight/num_lines)+padding+line_height ), 6)
		
	
	### Update ball ###
	# Move ball
	ball.x = ball.x + ball.xvel
	ball.y = ball.y + ball.yvel
	
	# Check wall collisions
	# if ball.x-ball.radius < court_left:  #left wall
		# ball.x = court_left+ball.radius
		# ball.xvel = -ball.xvel
	# if ball.x+ball.radius > court_right:	#right wall
		# ball.x = court_right-ball.radius
		# ball.xvel = -ball.xvel
	if ball.y-ball.radius < court_top:	#top wall
		ball.y = court_top+ball.radius
		ball.yvel = -ball.yvel
	if ball.y+ball.radius > court_bottom:  #bottom wall
		ball.y = court_bottom-ball.radius
		ball.yvel = -ball.yvel
		
	# Check paddle collisions
	if ball.x-ball.radius <= p1.x+p1.w:
		# Paddle missed ball
		if (ball.y+ball.radius < p1.y or ball.y-ball.radius > p1.y+p1.h):
			p2.score += 1
			ball.lastscore = 'p2'
			ball.reset()
			
		# Paddle hit ball
		else:
			# Find angle from center of paddle p1
			angle = math.atan((p1.center()[1]-ball.y) / (p1.center()[0]-ball.x))
			ball.xvel = 1*ball.speed*math.cos(angle)
			ball.yvel = ball.speed*math.sin(angle)
			
			
	if ball.x+ball.radius >= p2.x:
		# Paddle missed ball
		if (ball.y+ball.radius < p2.y or ball.y-ball.radius > p2.y+p2.h):
			p1.score += 1
			ball.lastscore = 'p1'
			ball.reset()
			
		# Paddle hit ball	
		else:
			# Find angle from center of paddle p2
			angle = math.atan((p2.center()[1]-ball.y) / (p2.center()[0]-ball.x))
			ball.xvel = -1*ball.speed*math.cos(angle)
			ball.yvel = -1*ball.speed*math.sin(angle)
	
	# Draw ball
	pygame.draw.circle(screen, white, (int(ball.x), int(ball.y)), ball.radius)
	
	### Update paddles ###
	## METHOD 1: Keyboard control (Up and Down arrow keys) ##
	def control_keyboard(p):
		# Decide to move up, down, or stay still depending on velmod
		p.y = p.y + p.velmod*p.speed
		if (p.y <= court_top):
			p.y = court_top
		if (p.y+p.h >= court_bottom):
			p.y = court_bottom-p.h
	
	control_keyboard(p1)
	# control_keyboard(p2)
	
	## METHOD 2: RandomAI ##
	def control_RandomAI(p, randX, diff):
	
		# Add randomness to movement so ball's velocity is random
		global drift_cap
		p.drift = p.drift + p.drift_sign*(randX.random()*0.2)*gamespeed
		
		if p.drift >= drift_cap[diff]*(p.h/2):
			p.drift_sign = -1
		if p.drift <= -drift_cap[diff]*(p.h/2):
			p.drift_sign = 1	
		# Randomly change direction of drift a certain percentage of the time.
		if random.random() < 0.001*gamespeed:
			p.drift_sign = -p.drift_sign
			
		p.y = ball.y - (p.h/2) + p.drift  # add randomness so ball's velocity is random
		if (p.y <= court_top):
			p.y = court_top
		if (p.y+p.h >= court_bottom):
			p.y = court_bottom-p.h
		
	# Enter difficulty as 'Easy', 'Medium', 'Hard', or 'Perfect'
	#control_RandomAI(p1, rand1, 'Hard')
	#control_RandomAI(p2, rand2, 'Medium')

	## METHOD 3: RandomAI 2.0 ##
	def control_RandomAI2(p, randX, diff):
	
		# Add randomness to movement so ball's velocity is random
		global drift_cap
		p.drift = p.drift + p.drift_sign*(randX.random()*0.2)
		
		if p.drift >= drift_cap[diff]*(p.h/2):
			p.drift_sign = -1
		if p.drift <= -drift_cap[diff]*(p.h/2):
			p.drift_sign = 1	
		# Randomly change direction of drift a certain percentage of the time.
		if random.random() < 0.001*gamespeed:
			p.drift_sign = -p.drift_sign
		
		if p.center()[1] < ball.y:
			# move up
			p.y = (p.y + p.speed)# + p.drift  # add randomness so ball's velocity is random
		elif p.center()[1] > ball.y:
			# move down
			p.y = (p.y - p.speed)# + p.drift  # add randomness so ball's velocity is random
		print(p.drift)
		if (p.y <= court_top):
			p.y = court_top
		if (p.y+p.h >= court_bottom):
			p.y = court_bottom-p.h
	
	# Enter difficulty as 'Easy', 'Medium', 'Hard', or 'Perfect'
	#control_RandomAI2(p1, rand1, 'Easy')
	#control_RandomAI2(p2, rand2, 'Perfect')
			
		
	# Draw paddles
	pygame.draw.rect(screen, white, (p1.x, p1.y, p1.w, p1.h))
	pygame.draw.rect(screen, white, (p2.x, p2.y, p2.w, p2.h))
	
	# DEBUG
	#pygame.draw.line(screen, red, (p1.center()[0], p1.center()[1]), (p2.center()[0], p1.center()[1]))  # p1 center line
	#pygame.draw.line(screen, blue, (p1.center()[0], p2.center()[1]), (p2.center()[0], p2.center()[1]))  # p2 center line
	#print(clock.get_fps())
	
	# Draw scores
	p1scoretext = font.render(str(p1.score), 1, white)
	p2scoretext = font.render(str(p2.score), 1, white)
	screen.blit(p1scoretext, p1scorepos)
	screen.blit(p2scoretext, p2scorepos)
	
	# Update screen
	pygame.display.flip()
	
	if (p1.score == scoremax or p2.score == scoremax):
		break
		
	
while True:
	# Game over!
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			sys.exit()
	gameovertext = font.render("Game over!", 1, red)
	screen.blit(gameovertext, (sWidth/2-185, 100))
	
	# Update screen
	pygame.display.flip()
	
	
	
	
	