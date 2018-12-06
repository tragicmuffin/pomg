# Neural Network to learn to play Pomg
# Jesse Williams
#
# Adapted from awjuliani's CartPole RL network:
#   https://medium.com/@awjuliani/super-simple-reinforcement-learning-tutorial-part-2-ded33892c724
#   https://github.com/awjuliani/DeepRL-Agents/blob/master/Vanilla-Policy.ipynb
#   CartPole Documentation: https://github.com/openai/gym/wiki/CartPole-v0
#
# INPUTS: ball x-velocity, ball y-velocity, ball x-position, ball y-position, paddle y-position, (paddle last-action?)
# OUTPUTS: go up, go down, stay still
# REWARD: N_1 points for every time ball bounces off of paddle, N_2 points for every point scored, N_3 points deducted for every opponent point scored,
#		  N_4 points for hitting ball closer to center of paddle
#
# Fully-connected RL NN with ?? input nodes, 1 hidden layer with ?? nodes, and ?? output nodes
#
#		 | -- O -- |
#	O -- | -- O -- |
#	O -- | -- O -- |
#	O -- | -- O -- | -- O
#	O -- | -- O -- | -- O
#	O -- | -- O -- |
#	O -- | -- O -- |
#		 | -- O -- |
#	^		  ^			^
# state_in  hidden	  output


# Ideas: Normalize state variables? Tweak rewards (add penalty for trying to move past court boundary)?
#		 Add reward for almost hitting ball?


import tensorflow as tf
import tensorflow.contrib.slim as slim 
# slim is a combination of several common tf contrib packages to allow for simpler code.
# i.e. tensorflow.contrib.slim.fuly_connected is actually referencing tensorflow.contrib.layers.fuly_connected
# Ref: https://github.com/tensorflow/tensorflow/tree/master/tensorflow/contrib/slim
import numpy as np
import os
#import gym
#import matplotlib.pyplot as plt
#%matplotlib inline
#import pomg_ForNNTraining_OneVolley as pomg
import pomg_ForNNTraining as pomg

try:
	xrange = xrange  # xrange is a Python 2.X only function
except:
	xrange = range
		
env = pomg.PomgEnv()

gamma = 0.99
a_size = 2

def discount_rewards(r):
	""" take 1D float array of rewards and compute discounted reward """
	# [..., 1.0, 1.0, 1.0, 1.0] --> [..., 3.94, 2.9701, 1.99, 1.0]
	# "Intuitively this allows each action to be a little bit responsible for not only the immediate reward, but all the rewards that followed."
	discounted_r = np.zeros_like(r)
	running_add = 0
	for t in reversed(xrange(0, r.size)):
		running_add = running_add * gamma + r[t]
		discounted_r[t] = running_add
	return discounted_r
	

class agent():
	def __init__(self, lr, s_size, a_size, h_size):
		#These lines establish the feed-forward part of the network. The agent takes a state and produces an action.
		self.state_in = tf.placeholder(shape=[None, s_size], dtype=tf.float32)
		hidden = slim.fully_connected(self.state_in, h_size, biases_initializer=None, activation_fn=tf.nn.relu) #one hidden layer
		self.output = slim.fully_connected(hidden, a_size, activation_fn=tf.nn.softmax, biases_initializer=None)
		self.chosen_action = tf.argmax(self.output,1)

		#The next six lines establish the training proceedure. We feed the reward and chosen action into the network
		#to compute the loss, and use it to update the network.
		self.reward_holder = tf.placeholder(shape=[None],dtype=tf.float32)
		self.action_holder = tf.placeholder(shape=[None],dtype=tf.int32)
		
		self.indexes = tf.range(0, tf.shape(self.output)[0]) * tf.shape(self.output)[1] + self.action_holder
		self.responsible_outputs = tf.gather(tf.reshape(self.output, [-1]), self.indexes)

		self.loss = -tf.reduce_mean(tf.log(self.responsible_outputs)*self.reward_holder)
		
		tvars = tf.trainable_variables()
		self.gradient_holders = []
		for idx,var in enumerate(tvars):
			placeholder = tf.placeholder(tf.float32,name=str(idx)+'_holder')
			self.gradient_holders.append(placeholder)
		
		self.gradients = tf.gradients(self.loss,tvars)
		
		optimizer = tf.train.AdamOptimizer(learning_rate=lr)
		self.update_batch = optimizer.apply_gradients(zip(self.gradient_holders,tvars))
	
	def normalizeFeatures(self, state):
		R = env.getRanges()  # returns a list of tuples containing (min, max) info for each feature
		i = 0
		
		for idx, s in enumerate(state):
			state[idx] = (s - R[idx][0])/(R[idx][1] - R[idx][0]) # Rescaling method
			
		return state
		
		
tf.reset_default_graph() #Clear the Tensorflow graph.

myAgent = agent(lr=0.001, s_size=5, a_size=a_size, h_size=15) #Load the agent.
# lr=learning rate, s_size=number of state parameters, a_size=number of possible actions, h_size=size of hidden layer

total_episodes = 100000 #Set total number of episodes to train agent on.
max_ep = 5000
update_frequency = 20
# We will update the weights of the network every 5 episodes. 
# Otherwise, each episode just uses the current weights to guess its actions.

init = tf.global_variables_initializer()

# Create a saver for writing training checkpoints.
saver = tf.train.Saver()
	
# Launch the tensorflow graph
with tf.Session() as sess:
	sess.run(init)
	i = 0
	k = 0
	total_reward = []
	total_length = []
	lastreward = 0
	writer = tf.summary.FileWriter("logs/", sess.graph)
	
	gradBuffer = sess.run(tf.trainable_variables())
	for ix,grad in enumerate(gradBuffer):
		gradBuffer[ix] = grad * 0  # zeros out gradBuffer, but also initializes it to proper form(?)
	
	a_dist_print = ['']*a_size

	# Restore checkpoint
	#fname = 'pomg_NN_gs' + str(env.gamespeed) + '.ckpt'
	#saver.restore(sess, 'logs/checkpoints/' + fname)
	#print("Checkpoint loaded. Model restored.")
	
	while i < total_episodes:
		s = env.reset()
		s = myAgent.normalizeFeatures(s)
		
		running_reward = 0
		ep_history = []
		for j in range(max_ep):
			a_dist = sess.run(myAgent.output, feed_dict={myAgent.state_in:[s]})  #get output of NN to find confidence distribution of actions
			
			#Probabilistically pick an action given our network outputs.
			a = np.random.choice(a_dist[0],p=a_dist[0])  # choose a random action weighted by the confidence of the action
			a = np.argmax(a_dist == a)  # return the index of the chosen action
			
			#Deterministically choose action by highest confidence.
			#a = np.argmax(a_dist)
			
			# "a_dist == a" creates a bool vector of size a_dist with True in positions where 'a' is a match and False otherwise.
			# Taking the argmax of this vector returns the index of the True entry since True=1 > False=0.

			s1,r,d = env.step(a) #Get our reward for taking an action.
			# s1 is the new state (4-vector), r is the reward (1 for every step pole is still upright)
			# d is the True/False indication of whether the episode has finished
			s1 = myAgent.normalizeFeatures(s1)
			
			ep_history.append([s,a,r,s1]) # add a row to the episode history
			
			s = s1
			running_reward += r
			
			
			##### Print Info #####
			try:
				avreward = np.mean(total_reward[-100:])
			except:
				avreward = 0
			
			if (j%15 == 0):  # to keep confidences from updating too often to be readable
				for ai, ax in enumerate(a_dist[0]):
					a_dist_print[ai] = '{0:.6f}'.format(ax)
				
			env.updatePrintInfo(['Episode: {0} | Frame: {1}'.format(i, j), 
								 'Up = {0:.2f}% | Down = {1:.2f}%'.format(float(a_dist_print[0])*100,float(a_dist_print[1])*100),
								 '{0:.6f}'.format(avreward), '{0:.6f}'.format(lastreward)])
			########################
			
			if d == True:
				# Update the network once env indicates episode has ended.
				ep_history = np.array(ep_history)
				ep_history[:,2] = discount_rewards(ep_history[:,2])  
				# Take third column of ep_history, containing record of previous rewards.
				# Replace record of rewards with discounted rewards.
				
				feed_dict={myAgent.reward_holder:ep_history[:,2], myAgent.action_holder:ep_history[:,1], myAgent.state_in:np.vstack(ep_history[:,0])}
				
				# Find gradients
				grads = sess.run(myAgent.gradients, feed_dict=feed_dict)
				for idx,grad in enumerate(grads):
					gradBuffer[idx] += grad

				# Every 'update_frequency' episodes, run 'update_batch' and flush gradient buffer.
				if i % update_frequency == 0 and i != 0:
					feed_dict = dictionary = dict(zip(myAgent.gradient_holders, gradBuffer))
					_ = sess.run(myAgent.update_batch, feed_dict=feed_dict)
					
					for ix,grad in enumerate(gradBuffer):
						gradBuffer[ix] = grad * 0
				
				total_reward.append(running_reward)
				total_length.append(j)
				lastreward = r
				break

		
			#Update our running tally of scores.
		if (i % 10 == 9) or (i==0):
			print('Now on episode {0} of {1}'.format(i+1, total_episodes))
			print('Average reward: {0}'.format(np.mean(total_reward[-100:])))  # mean of rewards from last 100 episodes
		
		if (i % 1000 == 999) or (i+1 == total_episodes):
			fname = 'pomg_NN_gs' + str(env.gamespeed) + '.ckpt'
			checkpoint_file = os.path.join('logs/checkpoints/', fname)
			saver.save(sess, checkpoint_file, global_step=i)
			print('<Checkpoint file saved>')
		
		i += 1
