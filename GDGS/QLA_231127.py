import rhinoscriptsyntax as rs
import ghpythonlib.components as gh
import Rhino.Geometry as rg
import System.Drawing as sd
import math
import random
import copy
import os
import time
import scriptcontext 
import datetime  # For timing control
import Grasshopper

#  Save Images

# Function to save the active Rhino viewport as an image
def save_viewport_as_image(filepath):
    view = scriptcontext.doc.Views.ActiveView
    viewport = view.ActiveViewport
    bitmap = view.CaptureToBitmap(viewport.DisplayMode)  # Correctly use the display mode
    if bitmap is not None:
        bitmap.Save(filepath, sd.Imaging.ImageFormat.Png)
    else:
        print("Failed to capture the viewport.")


# Slow down the component and 
def updateComponent(ghenv):
    
    """ Updates this component, similar to using a grasshopper timer """
    
    # Define callback action
    def callBack(e):
        ghenv.Component.ExpireSolution(True)
        
    # Get grasshopper document
    ghDoc = ghenv.Component.OnPingDocument()
    
    # Schedule this component to expire
    ghDoc.ScheduleSolution(500,Grasshopper.Kernel.GH_Document.GH_ScheduleDelegate(callBack))

################################################################################
#  IMPORT JUNEY FILES
################################################################################
import Assembly as assembly
import Grammar as gr
import Rhino as rc
import Rules as rules
import GraphicStatics as gs

import RandomUtility as ru

reload (assembly)
reload (gs)
reload (rules)
reload (gr)

################################################################################
#  RL ENVIRONMENT
################################################################################

class Environment:
    def __init__(self,grammar, randomcomputation, assembly):
        self.randomcomputation = randomcomputation
        self.grammar = grammar
        self.assembly = assembly
        self.boundary = assembly.Boundary

        self.input_length = 0
       
    
    #def reset(self):
    def reset(self):
        # Reset the assembly to its initial state
        self.assembly = copy.deepcopy(scriptcontext.sticky['initial_assembly'])
        return self.assembly
        
        
    # Set the environment to the Go state    
    def start(self):
        # Reset the environment to the Go state
        self.assembly.MyState = rules.State.Go
        
        
    # Set the environment to the End state    
    def done(self):
        # Reset the environment to the Go state
        self.assembly.MyState = rules.State.End
        pass
        
    def is_done(self):
        """ temp = []
        for node in self.assembly.Nodes:
            for f in node.Forces:
                if f.Type == 3:
                    temp.append(f)
        if len(temp) == 0: """
        if self.assembly.MyState == rules.State.End:
            return True
            
        else:
            return False
        
    # Get the current state of the assembly which is all possible node rules    
    def get_state(self):
        if not self.is_done():
            state = self.assembly
            return self.get_possible_nodeactions(state)
        else:
            pass
        
    def get_possible_nodeactions(self, state): #include state
        # Use the GetPossibleRules method from the Grammar class to get the possible actions
        stateruleslist = []
        node_rule = []

        for node in self.assembly.Nodes:
            rules = self.grammar.GetPossibleNodeRules(state, node)
            for rule in rules:
                params = self.randomcomputation.GenerateRandomParams(rule)
                nodeindex = gs.GetNodeIndex(node, self.assembly)
                node_rule = [rule, params, nodeindex]
                stateruleslist.append(node_rule)
        return stateruleslist
        
    def step(self, action):
        # Apply the action to the environment and get the next state, reward, and done
        next_state = self.randomcomputation.ApplyRule(self.assembly, action) # Add rewards, done 
        
        # Calculate the reward
        reward = self.calculate_reward(next_state)

        # Check if the episode is done
        done = self.is_done()
        
        return next_state, reward, done 
    
    def calculate_reward(self, next_state):
        # Calculate the reward for the next state and action
        reward = 0

        for node in self.assembly.Nodes:
            if gh.PointInCurve(node.Coordinate, self.boundary)[0] == 0: #if node is outside the boundary ideally give a neg reward 
                reward += -1
            else:
                reward += 1

        # Check for overlapping members
        intersections = []
        for member in self.assembly.Members:
            node = gs.GetMemberNodes(member, self.assembly)
            
            member_pts = []
            for n in node:
                member_pts.append(n.Coordinate)
                
            for other_member in self.assembly.Members:
                if member != other_member:  # Avoid self-comparison
                    other_nodes = gs.GetMemberNodes(other_member, self.assembly)
                    other_pts = []
                    for o in other_nodes:
                        other_pts.append(o.Coordinate)
                    cp = gh.CurveXCurve(member, other_member)[0]
                    
                    if cp == member_pts[0] or cp == member_pts[1]: 
                        pass
                    else:
                        intersections.append(cp)
        # Add a penalty to the reward for each intersection
        reward -= len(intersections)

        
        length = self.assembly.GetLength()
        length_difference = abs(self.input_length - length)
        # Calculate the reward based on the length difference
        # If the length difference is 0 (i.e., the assembly length is exactly the target length), the reward is 1
        # If the length difference is greater than 0 (i.e., the assembly length is not the target length), the reward is -length_difference
        length_reward = 1 - length_difference if length_difference <= 1 else -length_difference
        
        
        # Normalize the length reward to be between -1 and 1
        max_length_difference = 5 # maximum possible length difference
        min_reward = -max_length_difference
        max_reward = 1
        normalized_length_reward = 2 * ((length_reward - min_reward) / (max_reward - min_reward)) - 1

        # Combine the rewards
        reward += normalized_length_reward

        return reward
    
    

################################################################################
#  RL AGENT
################################################################################

class QLearningAgent:
    def __init__(self, randomcomputation, environment, alpha=0.5, gamma=0.95, epsilon=0.1):
        self.randomcomputation = randomcomputation
        self.environment = environment
        self.learning_rate = alpha  # learning rate
        self.discount_factor = gamma  # discount factor
        self.exploration_rate = epsilon  # exploration rate
        self.exploration_decay = 0.995  # decay exploration rate after each episode
        self.q_table = {}  # initialize Q-table as an empty dictionary
        self.episode_rewards = []  # Ensure this is initialized

        
    def select_action(self, state):
        if random.uniform(0, 1) < self.exploration_rate:
            return random.choice(state)
        else:
            stup = tuple((s[0].Name, s[2]) for s in state)
            if stup in self.q_table and self.q_table[stup]['actions']:
                max_action_info = max(self.q_table[stup]['actions'].values(), key=lambda x: x['q_value'])
                max_action = max_action_info.get('original_action', [])
                return max_action
            else:
                return random.choice(state)
    
    def end_episode(self):
        # Decay exploration rate
        if self.exploration_rate > 0.01:
            self.exploration_rate *= self.exploration_decay# python
    

    def update(self, state, action, reward, next_state):
        # Create a tuple of the state 
        stup = tuple((s[0].Name, s[2]) for s in state)
        action_key = (action[0].Name, action[-1])

        # Check if the state exists in the q_table
        if stup not in self.q_table:
            self.q_table[stup] = {'actions': {}}

        # Check if the action exists for the state in the q_table
        if action_key not in self.q_table[stup]['actions']:
            self.q_table[stup]['actions'][action_key] = {'q_value': 0, 'n': 0, 'original_action': action}

        # Get the maximum q_value for the next state
        if next_state is not None:
            nstup = tuple((s[0].Name, s[2]) for s in next_state)
            next_state_actions = self.q_table.get(nstup, {'actions': {}})['actions']
            if next_state_actions:
                max_next_q_value = max(next_state_actions.values(), key=lambda x: x['q_value'])['q_value']
            else:
                max_next_q_value = 0  # or any other default value
        else:
            max_next_q_value = 0  # or any other default value

        # Update the q_value for the current state and action
        current_q_value = self.q_table[stup]['actions'][action_key]['q_value']
        n = self.q_table[stup]['actions'][action_key]['n']
        new_q_value = (n * current_q_value + reward + self.discount_factor * max_next_q_value) / (n + 1)
        self.q_table[stup]['actions'][action_key]['q_value'] = new_q_value
        self.q_table[stup]['actions'][action_key]['n'] += 1
    
    
        
    def train(self, episodes):
        self.episode_rewards = []  # Re-initialize at the start of training
        assembly_rewards = []

        for episode in range(episodes):
            if 'assembly_list' not in scriptcontext.sticky:
                scriptcontext.sticky['assembly_list'] = []
            if 'assembly_length' not in scriptcontext.sticky:
                scriptcontext.sticky['assembly_length'] = []
            if 'episode_reward' not in scriptcontext.sticky:
                scriptcontext.sticky['episode_reward'] = []

            env = self.environment
            env.reset()
            env.start()
            i = 0
            total_reward = 0

            while not env.is_done():
                state = env.get_state()
                action = self.select_action(state)
                step, reward, done = env.step(action)
                total_reward += reward
                next_state = env.get_state()
                self.update(state, action, reward, next_state)

                # Schedule the next solution in Grasshopper
                gh_doc = scriptcontext.ghdoc  # Access the Grasshopper document
                gh_doc.ScheduleSolution(1, self.Callback)  # Schedule solution 1 millisecond after current

                # Delay to ensure viewport updates
                time.sleep(0.1)

                if env.is_done():
                    scriptcontext.sticky['assembly_length'].append(env.assembly.GetLength())
                    scriptcontext.sticky['episode_reward'].append(total_reward)
                    self.episode_rewards.append(total_reward)  # Track episode rewards
                    assembly_rewards.append((env.assembly, total_reward))
                    break

                scriptcontext.sticky['episode_reward'].append(total_reward)
                self.episode_rewards.append(total_reward)  # Track episode rewards
                state = next_state

            self.end_episode()

            if i > 50:
                env.done()
                scriptcontext.sticky['assembly_length'].append(env.assembly.GetLength())
                i = 0
                break
            i += 1

        assembly_rewards = [(assembly, reward) for assembly, reward in assembly_rewards if all(gh.PointInCurve(node.Coordinate, env.boundary)[0] != 0 for node in assembly.Nodes)]
        assembly_rewards.sort(key=lambda x: x[1], reverse=True)
        top_assemblies = [assembly for assembly, reward in assembly_rewards[:5]]
        scriptcontext.sticky['assembly_list'].extend(top_assemblies)

def Callback(self, doc):
    """Callback to force a redraw in the viewport."""
    self.Component.ExpireSolution(False)  # Ensure this expires the solution correctly


#  Save Images

# Function to save the active Rhino viewport as an image
def save_viewport_as_image(filepath):
    view = scriptcontext.doc.Views.ActiveView
    viewport = view.ActiveViewport
    bitmap = view.CaptureToBitmap(viewport.DisplayMode)  # Correctly use the display mode
    if bitmap is not None:
        bitmap.Save(filepath, sd.Imaging.ImageFormat.Png)
    else:
        print("Failed to capture the viewport.")

################################################################################
#  IMPORT JUNEY FILES
################################################################################
import Assembly as assembly
import Grammar as gr
import Rhino as rc
import Rules as rules
import GraphicStatics as gs

import RandomUtility as ru

reload (assembly)
reload (gs)
reload (rules)
reload (gr)

################################################################################
#  RL ENVIRONMENT
################################################################################

class Environment:
    def __init__(self,grammar, randomcomputation, assembly):
        self.randomcomputation = randomcomputation
        self.grammar = grammar
        self.assembly = assembly
        self.boundary = assembly.Boundary

        self.input_length = 0
       
    
    #def reset(self):
    def reset(self):
        # Reset the assembly to its initial state
        self.assembly = copy.deepcopy(scriptcontext.sticky['initial_assembly'])
        return self.assembly
        
        
    # Set the environment to the Go state    
    def start(self):
        # Reset the environment to the Go state
        self.assembly.MyState = rules.State.Go
        
        
    # Set the environment to the End state    
    def done(self):
        # Reset the environment to the Go state
        self.assembly.MyState = rules.State.End
        pass
        
    def is_done(self):
        """ temp = []
        for node in self.assembly.Nodes:
            for f in node.Forces:
                if f.Type == 3:
                    temp.append(f)
        if len(temp) == 0: """
        if self.assembly.MyState == rules.State.End:
            return True
            
        else:
            return False
        
    # Get the current state of the assembly which is all possible node rules    
    def get_state(self):
        if not self.is_done():
            state = self.assembly
            return self.get_possible_nodeactions(state)
        else:
            pass
        
    def get_possible_nodeactions(self, state): #include state
        # Use the GetPossibleRules method from the Grammar class to get the possible actions
        stateruleslist = []
        node_rule = []

        for node in self.assembly.Nodes:
            rules = self.grammar.GetPossibleNodeRules(state, node)
            for rule in rules:
                params = self.randomcomputation.GenerateRandomParams(rule)
                nodeindex = gs.GetNodeIndex(node, self.assembly)
                node_rule = [rule, params, nodeindex]
                stateruleslist.append(node_rule)
        return stateruleslist
        
    def step(self, action):
        # Apply the action to the environment and get the next state, reward, and done
        next_state = self.randomcomputation.ApplyRule(self.assembly, action) # Add rewards, done 
        
        # Calculate the reward
        reward = self.calculate_reward(next_state)

        # Check if the episode is done
        done = self.is_done()
        
        return next_state, reward, done 
    
    def calculate_reward(self, next_state):
        # Calculate the reward for the next state and action
        reward = 0

        for node in self.assembly.Nodes:
            if gh.PointInCurve(node.Coordinate, self.boundary)[0] == 0: #if node is outside the boundary ideally give a neg reward 
                reward += -1
            else:
                reward += 1

        # Check for overlapping members
        intersections = []
        for member in self.assembly.Members:
            node = gs.GetMemberNodes(member, self.assembly)
            
            member_pts = []
            for n in node:
                member_pts.append(n.Coordinate)
                
            for other_member in self.assembly.Members:
                if member != other_member:  # Avoid self-comparison
                    other_nodes = gs.GetMemberNodes(other_member, self.assembly)
                    other_pts = []
                    for o in other_nodes:
                        other_pts.append(o.Coordinate)
                    cp = gh.CurveXCurve(member, other_member)[0]
                    
                    if cp == member_pts[0] or cp == member_pts[1]: 
                        pass
                    else:
                        intersections.append(cp)
        # Add a penalty to the reward for each intersection
        reward -= len(intersections)

        
        length = self.assembly.GetLength()
        length_difference = abs(self.input_length - length)
        # Calculate the reward based on the length difference
        # If the length difference is 0 (i.e., the assembly length is exactly the target length), the reward is 1
        # If the length difference is greater than 0 (i.e., the assembly length is not the target length), the reward is -length_difference
        length_reward = 1 - length_difference if length_difference <= 1 else -length_difference
        
        
        # Normalize the length reward to be between -1 and 1
        max_length_difference = 5 # maximum possible length difference
        min_reward = -max_length_difference
        max_reward = 1
        normalized_length_reward = 2 * ((length_reward - min_reward) / (max_reward - min_reward)) - 1

        # Combine the rewards
        reward += normalized_length_reward

        return reward
    
    

################################################################################
#  RL AGENT
################################################################################
class QLearningAgent:
    def __init__(self, randomcomputation, environment, gh_doc, alpha=0.5, gamma=0.95, epsilon=0.1):
        self.randomcomputation = randomcomputation
        self.environment = environment
        self.gh_doc = gh_doc  # Store the Grasshopper document reference
        self.learning_rate = alpha  # learning rate
        self.discount_factor = gamma  # discount factor
        self.exploration_rate = epsilon  # exploration rate
        self.exploration_decay = 0.995  # decay exploration rate after each episode
        self.q_table = {}  # initialize Q-table as an empty dictionary
        self.episode_rewards = []  # Ensure this is initialized

        
    def select_action(self, state):
        if random.uniform(0, 1) < self.exploration_rate:
            return random.choice(state)
        else:
            stup = tuple((s[0].Name, s[2]) for s in state)
            if stup in self.q_table and self.q_table[stup]['actions']:
                max_action_info = max(self.q_table[stup]['actions'].values(), key=lambda x: x['q_value'])
                max_action = max_action_info.get('original_action', [])
                return max_action
            else:
                return random.choice(state)
    
    def end_episode(self):
        # Decay exploration rate
        if self.exploration_rate > 0.01:
            self.exploration_rate *= self.exploration_decay# python
    

    def update(self, state, action, reward, next_state):
        # Create a tuple of the state 
        stup = tuple((s[0].Name, s[2]) for s in state)
        action_key = (action[0].Name, action[-1])

        # Check if the state exists in the q_table
        if stup not in self.q_table:
            self.q_table[stup] = {'actions': {}}

        # Check if the action exists for the state in the q_table
        if action_key not in self.q_table[stup]['actions']:
            self.q_table[stup]['actions'][action_key] = {'q_value': 0, 'n': 0, 'original_action': action}

        # Get the maximum q_value for the next state
        if next_state is not None:
            nstup = tuple((s[0].Name, s[2]) for s in next_state)
            next_state_actions = self.q_table.get(nstup, {'actions': {}})['actions']
            if next_state_actions:
                max_next_q_value = max(next_state_actions.values(), key=lambda x: x['q_value'])['q_value']
            else:
                max_next_q_value = 0  # or any other default value
        else:
            max_next_q_value = 0  # or any other default value

        # Update the q_value for the current state and action
        current_q_value = self.q_table[stup]['actions'][action_key]['q_value']
        n = self.q_table[stup]['actions'][action_key]['n']
        new_q_value = (n * current_q_value + reward + self.discount_factor * max_next_q_value) / (n + 1)
        self.q_table[stup]['actions'][action_key]['q_value'] = new_q_value
        self.q_table[stup]['actions'][action_key]['n'] += 1
    
    
        
    def train(self, episodes):
        self.episode_rewards = []  # Re-initialize at the start of training
        assembly_rewards = []

        for episode in range(episodes):
            if 'assembly_list' not in scriptcontext.sticky:
                scriptcontext.sticky['assembly_list'] = []
            if 'assembly_length' not in scriptcontext.sticky:
                scriptcontext.sticky['assembly_length'] = []
            if 'episode_reward' not in scriptcontext.sticky:
                scriptcontext.sticky['episode_reward'] = []

            env = self.environment
            env.reset()
            env.start()
            i = 0
            total_reward = 0

            while not env.is_done():
                state = env.get_state()
                action = self.select_action(state)
                step, reward, done = env.step(action)
                total_reward += reward
                next_state = env.get_state()
                self.update(state, action, reward, next_state)

                

                

                if env.is_done():
                    scriptcontext.sticky['assembly_length'].append(env.assembly.GetLength())
                    scriptcontext.sticky['episode_reward'].append(total_reward)
                    self.episode_rewards.append(total_reward)  # Track episode rewards
                    assembly_rewards.append((env.assembly, total_reward))
                    break

                scriptcontext.sticky['episode_reward'].append(total_reward)
                self.episode_rewards.append(total_reward)  # Track episode rewards
                state = next_state
                updateComponent(ghenv)
            self.end_episode()

            if i > 50:
                env.done()
                scriptcontext.sticky['assembly_length'].append(env.assembly.GetLength())
                i = 0
                break
            i += 1

        assembly_rewards = [(assembly, reward) for assembly, reward in assembly_rewards if all(gh.PointInCurve(node.Coordinate, env.boundary)[0] != 0 for node in assembly.Nodes)]
        assembly_rewards.sort(key=lambda x: x[1], reverse=True)
        top_assemblies = [assembly for assembly, reward in assembly_rewards[:5]]
        scriptcontext.sticky['assembly_list'].extend(top_assemblies)


