import sys, pygame, math, random

# Episode begins when ball leaves paddle 1. Episode ends whenever ball reaches paddle 1, either by being returned or by p2 missing.

class PomgEnv():
	def __init__(self):

		pygame.init()

		self.size = (self.sWidth, self.sHeight) = (800, 600)
		self.gamespeed = 8 # Global game speed. WARNING: Frames will be missed if set over ~30.
		self.scoremax = 10
		self.play = True

		self.screen = pygame.display.set_mode(self.size)
		pygame.display.set_caption("Yep, It's Pomg!")
		self.clock = pygame.time.Clock()
		
		self.padding = 10
		self.court_left		= self.padding
		self.court_right	= self.sWidth-self.padding
		self.court_top		= self.padding
		self.court_bottom	= self.sHeight-self.padding
		
		
		self.p1 = Paddle(self.gamespeed)
		self.p1.x = self.court_left+10
		self.p1.y = self.sHeight/2
			
		self.p2 = Paddle(self.gamespeed)
		self.p2.x = self.court_right-self.p2.w-10
		self.p2.y = self.sHeight/2
		
		self.ball = Ball(self.gamespeed, self.p1, self.p2)

		
		## RandomAI Settings ##
		# Max drift distance allowed by each difficulty, expressed as percentage of paddle height
		self.drift_cap = {'Easy': 2.5, 'Medium': 2.0, 'Hard': 1.4, 'Perfect': 0.75}
		# Start two separate random seeds for two different players
		self.rand1 = random.Random(random.randint(1, 100))
		self.rand2 = random.Random(random.randint(1, 100)+100)


		## Initialize external AI Settings ##
		self.episodeEnded = False
		self.RF_hitball = False
		self.RF_distance = 0
		self.RF_boundary = 0
		
		self.printInfo = ["Test"]
		
	def rewardFunction(self, H, D, B):
		# H is True if the ball was hit, H is False if the ball was missed.
		h = 1 # value of hitting ball
		m = 0 # value of missing ball
		
		# D is abs value distance between center of ball and center of paddle (in y-direction)
		distRange = (self.court_bottom-self.ball.radius) - (self.court_top+(self.p1.h/2))  # largest possible dist
		d = 1 - D/distRange # Reward for getting close. D is in (0, 1) where 1 is a center hit, 0 is a max miss.
		
		# Score RF_boundary using exp function to model penalty. 
		# Model: f(x) = e^(a*x) - 1. Constants obtained using (0, 0) and (cap, 1).
		# Good for 1x gamespeed: (a, cap) = (0.00069315, 1000)
		# Good for 5x gamespeed: (a, cap) = (0.0013863, 500)
		# Good for 10x gamespeed: (a, cap) = (0.0027726, 250)
		
		a = 0.0027726
		cap = 250
		# 1 point is awarded for staying away from boundary, decreased towards 0 as more frames are spent on boundary.
		if B < cap:
			rwd_boundary = math.exp(a*B) - 1
		else:
			rwd_boundary = math.exp(a*cap) - 1
		
		b = 1 - rwd_boundary
		
		# Up to 1pt for distance, an extra 1pt for hitting ball, 0pt for missing ball, up to 1pt for staying off boundary
		return H*h + d + 2*b
		
		
	def reset(self):
		self.episodeEnded = False
		
		self.RF_boundary = 0
		
		# Update screen
		self.drawScreen(self.screen, self.ball, self.p1, self.p2)
		pygame.display.flip()
		
		return [self.p1.y, self.ball.x, self.ball.y, self.ball.xvel, self.ball.yvel]  # return state only

	def step(self, action):
	
		# self.clock.tick()
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				sys.exit()
			# # Check for input
			# elif event.type == pygame.KEYDOWN:
				# if event.key == pygame.K_UP:
					# p1.up()
					# p2.up()
				# if event.key == pygame.K_DOWN:
					# p1.down()
					# p2.down()
			# elif event.type == pygame.KEYUP:
				# if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
					# p1.stop()
					# p2.stop()

					
		if self.episodeEnded:
			print("Episode has ended. Run reset().")
			
		############################################
		##### Update ball and check collisions #####
		# Move ball
		self.ball.x = self.ball.x + self.ball.xvel
		self.ball.y = self.ball.y + self.ball.yvel
		
		if self.ball.y-self.ball.radius < self.court_top:	#top wall
			self.ball.y = self.court_top+self.ball.radius
			self.ball.yvel = -self.ball.yvel
		if self.ball.y+self.ball.radius > self.court_bottom:  #bottom wall
			self.ball.y = self.court_bottom-self.ball.radius
			self.ball.yvel = -self.ball.yvel
			
			
		# Check paddle collisions (Paddle 1)
		if self.ball.x-self.ball.radius <= self.p1.x+self.p1.w:
			
			self.episodeEnded = True
			self.RF_distance = math.fabs(self.ball.y - self.p1.center()[1])
			
			# Paddle missed ball
			if (self.ball.y+self.ball.radius < self.p1.y or self.ball.y-self.ball.radius > self.p1.y+self.p1.h):
				self.RF_hitball = False
				self.p2.score += 1
				self.ball.lastscore = 'p2'
				self.ball.reset()
			# Paddle hit ball
			else:
				self.RF_hitball = True
				# Find angle from center of paddle p1
				angle = math.atan((self.p1.center()[1]-self.ball.y) / (self.p1.center()[0]-self.ball.x))
				self.ball.xvel = 1*self.ball.speed*math.cos(angle)
				self.ball.yvel = self.ball.speed*math.sin(angle)

		# Check paddle collisions (Paddle 2)		
		if self.ball.x+self.ball.radius >= self.p2.x:
			# Paddle missed ball
			if (self.ball.y+self.ball.radius < self.p2.y or self.ball.y-self.ball.radius > self.p2.y+self.p2.h):
				self.p1.score += 1
				self.ball.lastscore = 'p1'
				self.episodeEnded = True
				self.ball.reset()
				
			# Paddle hit ball	
			else:
				# Find angle from center of paddle p2
				angle = math.atan((self.p2.center()[1]-self.ball.y) / (self.p2.center()[0]-self.ball.x))
				self.ball.xvel = -1*self.ball.speed*math.cos(angle)
				self.ball.yvel = -1*self.ball.speed*math.sin(angle)
		############################################
		############################################
		
		
		## METHOD 1: Keyboard control (Up and Down arrow keys) ##
		#control_keyboard(p1)
		#control_keyboard(p2)
		#########################################################
		
		## METHOD 2: RandomAI ##
		# Enter difficulty as 'Easy', 'Medium', 'Hard', or 'Perfect'
		#self.control_randomAI(p1, rand1, 'Hard')
		#self.control_randomAI(self.p2, self.rand2, 'Medium')
		############################
		
		## METHOD 3: RandomAI 2.0 ##
		# Enter difficulty as 'Easy', 'Medium', 'Hard', or 'Perfect'
		#self.control_randomAI2(p1, rand1, 'Hard')
		self.control_randomAI2(self.p2, self.rand2, 'Medium')
		############################
		
		## METHOD 4: External AI ##
		if(self.episodeEnded):
			rwd = self.rewardFunction(H=self.RF_hitball, D=self.RF_distance, B=self.RF_boundary)
		else:
			rwd = 0
		
		self.control_externalAI(self.p1, action)
		
		# Update screen
		self.drawScreen(self.screen, self.ball, self.p1, self.p2)
		pygame.display.flip()
		
		
		return [self.p1.y, self.ball.x, self.ball.y, self.ball.xvel, self.ball.yvel], rwd, self.episodeEnded  # return state, reward, and episode condition
	
	def drawScreen(self, screen, ball, p1, p2):
		black = (0, 0, 0)
		red = (255, 0, 0)
		blue = (0, 0, 255)
		white = (255, 255, 255)
		gray = (64, 64, 64)
		
		padding = self.padding
		cWidth = self.sWidth-2*padding
		cHeight = self.sHeight-2*padding
		
		
		# Draw background
		screen.fill(black)
		
		# Draw court
		pygame.draw.rect(screen, white, (padding, padding, self.sWidth-2*padding, self.sHeight-2*padding), 6)
		num_lines = 32
		line_height = 8
		for i in range(num_lines):
			pygame.draw.line(screen, white, ( self.sWidth/2, i*(cHeight/num_lines)+padding ), ( self.sWidth/2, i*(cHeight/num_lines)+padding+line_height ), 6)
			
		# Draw ball
		pygame.draw.circle(screen, white, (int(ball.x), int(ball.y)), ball.radius)
			
		# Draw paddles
		pygame.draw.rect(screen, white, (p1.x, p1.y, p1.w, p1.h))
		pygame.draw.rect(screen, white, (p2.x, p2.y, p2.w, p2.h))
		
		# DEBUG
		#pygame.draw.line(screen, red, (p1.center()[0], p1.center()[1]), (p2.center()[0], p1.center()[1]))  # p1 center line
		#pygame.draw.line(screen, blue, (p1.center()[0], p2.center()[1]), (p2.center()[0], p2.center()[1]))  # p2 center line
		#print(clock.get_fps())
		
		# Draw scores
		if pygame.font:
			font = pygame.font.Font(None, 100)
			
		p1scoretext = font.render(str(p1.score), 1, white)
		p2scoretext = font.render(str(p2.score), 1, white)
		
		p1scorepos = (self.sWidth/2 - font.size(str(p1.score))[0] - 35, 20)
		p2scorepos = (self.sWidth/2+35, 20)
		
		screen.blit(p1scoretext, p1scorepos)
		screen.blit(p2scoretext, p2scorepos)
		

		# Print info passed from NN
		offset = 20
		shift = 0
		start = len(self.printInfo)*offset + 20
		for j in self.printInfo:
			# Print
			if pygame.font:
				font = pygame.font.Font(None, 26)
			text = font.render(j, 1, (255, 48, 48))
			self.screen.blit(text, (self.sWidth*(1/2)+10, (self.sHeight-start)+shift))
			shift += offset
		
			
	def updatePrintInfo(self, info):
		# Format
		msgs = ["", "Confidence: ", "Average reward: ", "Last reward: "]
		for i, t in enumerate(info):
			info[i] = msgs[i] + str(t)
		
		# Update
		self.printInfo = info
		
		
		
	def getRanges(self):
		
		r1 = (self.court_top, self.court_bottom-self.p2.h) 							# p2.y
		r2 = (self.p1.x+self.p1.w+self.ball.radius, self.p2.x-self.ball.radius) 	# ball.x
		r3 = (self.court_top+self.ball.radius, self.court_bottom-self.ball.radius) 	# ball.y
		r4 = (-self.ball.speed*1, -self.ball.speed*math.cos(self.ball.maxangle)) 	# ball.xvel **only works for one volley
		r5 = (-self.ball.speed*math.sin(self.ball.maxangle), self.ball.speed*math.sin(self.ball.maxangle)) 	# ball.yvel
		
		return [r1, r2, r3, r4, r5]
	
	
	# ### Update paddles ###
	# ## METHOD 1: Keyboard control (Up and Down arrow keys) ##
	# def control_keyboard(p):
		# # Decide to move up, down, or stay still depending on velmod
		# p.y = p.y + p.velmod*p.speed
		# if (p.y <= court_top):
			# p.y = court_top
		# if (p.y+p.h >= court_bottom):
			# p.y = court_bottom-p.h
			
	## METHOD 2: RandomAI ##
	def control_randomAI(self, p, randX, diff):

		# Add randomness to movement so ball's velocity is random
		p.drift = p.drift + p.drift_sign*(randX.random()*0.2)*self.gamespeed
		
		if p.drift >= self.drift_cap[diff]*(p.h/2):
			p.drift_sign = -1
		if p.drift <= -self.drift_cap[diff]*(p.h/2):
			p.drift_sign = 1	
		# Randomly change direction of drift a certain percentage of the time.
		if random.random() < 0.001*self.gamespeed:
			p.drift_sign = -p.drift_sign
			
		p.y = self.ball.y - (p.h/2) + p.drift  # add randomness so ball's velocity is random
		if (p.y <= self.court_top):
			p.y = self.court_top
		if (p.y+p.h >= self.court_bottom):
			p.y = self.court_bottom-p.h

	## METHOD 3: RandomAI 2.0 ##
	def control_randomAI2(self, p, randX, diff):

		dist = p.center()[1] - self.ball.y
		if dist <= 0:
			# move up
			if math.fabs(dist) < p.h*0.4:
				p.y += p.speed * math.fabs( dist/(p.h*0.4) )  # scale speed down to 0 as paddle approaches center of ball
			else:
				p.y += p.speed
		else:
			# move down
			if math.fabs(dist) < p.h*0.4:
				p.y -= p.speed * math.fabs( dist/(p.h*0.4) )  # scale speed down to 0 as paddle approaches center of ball
			else:
				p.y -= p.speed
		
		if (p.y <= self.court_top):
			p.y = self.court_top
		if (p.y+p.h >= self.court_bottom):
			p.y = self.court_bottom-p.h	
			

	## METHOD 4: External AI ##
	def control_externalAI(self, p, a):
		# Decide to move up, down, or stay still.
		
		a = 2*a - 1 #for two outputs. a=0 moves up, a=1 moves down
		#a = a - 1 #for three outputs. a=0 moves up, a=1 stays still, a=2 moves down
		p.y = p.y + a*p.speed
		
		if (p.y <= self.court_top):
			p.y = self.court_top
			self.RF_boundary += 1
		elif (p.y+p.h >= self.court_bottom):
			p.y = self.court_bottom-p.h
			self.RF_boundary += 1
			


# Initialize ball settings
class Ball:
	def __init__(self, gamespeed, p1, p2):
		self.gamespeed = gamespeed
		self.p1 = p1
		self.p2 = p2
		
		self.speed = 0.75*gamespeed
	
	maxangle = math.radians(75) # max angle from x-axis (up or down) ball should leave at.
	radius = 10
	x, y = 0, 0
	xvel, yvel = 0, 0
	lastscore = 'p1'
	
	def reset(self):
		# After a point, reset ball's location to side of player who was scored on
		if self.lastscore == 'p2':
			self.x = self.p1.x + self.p1.w + self.radius + 2
			self.y = self.p1.y + (self.p1.h/2)
			
			self.vel_init(1)
			
		if self.lastscore == 'p1':
			self.x = self.p2.x - self.radius - 2
			self.y = self.p2.y + (self.p2.h/2)
			
			self.vel_init(-1)
			
	def vel_init(self, dir):
		# Initialize ball velocity with negative x velocity for dir=-1 and positive x velocity for dir=1
		#self.xvel = dir*(random.random()*0.4 + 0.6)*self.speed
		#self.yvel = (random.randint(0, 1)*2 - 1) * math.sqrt(self.speed**2 - self.xvel**2)  # the random call here chooses a direction, either 1 or -1
		
		angle = random.random()*self.maxangle
		self.xvel = dir * self.speed*math.cos(angle)
		self.yvel = (random.randint(0, 1)*2 - 1) * self.speed*math.sin(angle) # the random call here chooses a direction, either 1 or -1

		
# Initialize paddle settings
class Paddle:
	def __init__(self, gamespeed):
		self.gamespeed = gamespeed
		
		self.speed = 0.6*gamespeed
			
	h = 65 #default=80
	w = 20
	x, y = 0, 0
	velmod = 0	# -1 for up, 1 for down, 0 for stop
	score = 0
	center = (0,0)
	drift = 0
	drift_sign = 1
	
	def center(self):
		return (self.x+(self.w/2), self.y+(self.h/2))

	
	

	
	
	
	
	
	
	
	
	
	