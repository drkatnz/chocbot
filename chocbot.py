import time
import pickle
import sys

from slackclient import SlackClient

from datetime import datetime
from dateutil.relativedelta import relativedelta


class Scoreboard(object):
    def __init__(self, type='Scoreboard'):
        self.last_update = None
        self.all_time = {}
        self.last_month = {}
        self.this_month = {}
        self.scoreboard_type = 'Scoreboard'
        
    def change_month(self):
        #change the month we are working with
        self.last_month = self.this_month
        self.this_month = {}
        
    def check_month(self):
        #checks we are in the same month
        current_time = datetime.now()
        if self.last_update is None:
            self.last_update = current_time
            return
        if self.last_update.month != current_time.month:
            self.change_month()
        self.last_update = current_time
        
    def add_score(self, user, score=1):
        #adds one value to the user's score        
        #check we haven't changed months
        self.check_month()
            
        #update this user        
        if user in self.this_month:
            self.this_month[user] = self.this_month[user] + score
        else:
            self.this_month[user] = score
            
        #update all time
        if user in self.all_time:
            self.all_time[user] = self.all_time[user] + score
        else:
            self.all_time[user] = score
            
            
    def reset(self):
        #resets state
        self.last_update = None
        self.all_time = {}
        self.last_month = {}
        self.this_month = {}
        
        
    def get_scoreboard(self):
        #gets the scoreboard for this month
        if len(self.this_month.items()) == 0:
            return "There's no awards for this month yet."
        
        sorted_by_value = sorted(self.this_month.items(), key=lambda x: x[1], reverse=True)
        response = self.scoreboard_type +' for {}\n--------------------------------\n'.format(self.last_update.strftime('%B'))
        for item in sorted_by_value:
            response += '{}: \t{}\n'.format(item[0],item[1])
            
        return response 
    
    def get_last_month_scoreboard(self):
        #gets the scoreboard for last month
        if len(self.last_month.items()) == 0:
            return "There's no awards for last month."
        
        sorted_by_value = sorted(self.last_month.items(), key=lambda x: x[1], reverse=True)
        
        last_month = self.last_update - relativedelta(months=1)
        response = self.scoreboard_type + ' for {}\n--------------------------------\n'.format(last_month.strftime('%B'))
        for item in sorted_by_value:
            response += '{}: \t{}\n'.format(item[0],item[1])
            
        return response 
 
    def get_all_time_scoreboard(self):
        #gets the scoreboard for last month
        if len(self.all_time.items()) == 0:
            return "There's no awards for last month."
        
        sorted_by_value = sorted(self.all_time.items(), key=lambda x: x[1], reverse=True)
        
        response = 'Overall ' + self.scoreboard_type.lower() + '\n--------------------------------\n'
        for item in sorted_by_value:
            response += '{}: \t{}\n'.format(item[0],item[1])
            
        return response 




 
class Bot(object):
    def __init__(self, key, codeword='iamgod'):
        self.slack_client = SlackClient(key)
        self.bot_name = "chocbot"
        self.bot_id = self.get_bot_id()
        print('My ID is:',self.bot_id)
        self.codeword = codeword
        
        self.scoreboard = Scoreboard()    
        self.nominators = Scoreboard('Nominators')
         
        if self.bot_id is None:
            exit("Error, could not find " + self.bot_name)
            
        self.restore_state()
     
        self.event = Event(self)
        self.listen()
     
    def get_bot_id(self):
        api_call = self.slack_client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and user.get('name') == self.bot_name:
                    return "<@" + user.get('id') + ">"
             
            return None
        
    def get_user_name(self, userid):
        api_call = self.slack_client.api_call("users.list")
        if api_call.get('ok'):
            # retrieve all users so we can find our bot
            users = api_call.get('members')
            for user in users:
                if 'name' in user and user.get('id') == userid:
                    return user.get('name')
             
        return None
             
    def listen(self):
        if self.slack_client.rtm_connect(with_team_state=False):
            print("Successfully connected, listening for commands")
            while True:
                self.event.wait_for_event()                 
                time.sleep(1)
        else:
            exit("Error, Connection Failed")
            
            
    def send_message(self, channel, message):
        #sends a message to the noted channel
        self.slack_client.api_call("chat.postMessage", channel=channel, text=message, as_user=True)
        
    def save_state(self, filename='bot_state.pkl'):
        #dumps the state out to an appropriate file
        try:
            state = {'scoreboard': self.scoreboard, 'nominators': self.nominators}
            pickle.dump(state, open(filename,'wb'))
        except:
            print('Count not save state. Is the location writeable?')
        
    def restore_state(self, filename='bot_state.pkl'):
        try:
            state = pickle.load(open(filename, 'rb'))
            self.scoreboard = state['scoreboard']
            self.nominators = state['nominators']
            print('Restored state from save file.')
        except:
            print('Save file not found')



class Event:
    def __init__(self, bot):
        self.bot = bot
        
     
    def wait_for_event(self):
        #waits for events and processes them when it gets one
        events = self.bot.slack_client.rtm_read()         
        if events and len(events) > 0:
            for event in events:
                if event['type'] == 'message': #only consider messages
                    #print(event)
                    if 'subtype' not in event:
                        self.parse_event(event)
                    
                    
    def get_named_users(self, text):
        #gets any users named in the text
        named_users = []
        for word in text.split():
            if word.startswith('<@') and word.endswith('>') and word !=  self.bot.bot_id:
                named_users.append(word)
        return named_users
    
    
    def parse_event(self, event):
        if event['type'] == 'message' and event['user'] != self.bot.bot_id: #don't consider own messages
            user = self.bot.get_user_name(event['user']) #person who sent message
            
            bot_named = self.bot.bot_id in event['text'] #is the bot referenced?
            channel = event['channel'] #what channel was this sent in?

            split = event['text'].split()
            
            #check if we are asking for the score
            score_commands = ['scoreboard', 'score', 'tally']
            score_nominator_commands = ['nominators', 'given', 'awarders']
            if bot_named and not set(score_commands).isdisjoint(split):
                print('Printing scoreboard.')
                if set(score_nominator_commands).isdisjoint(split):
                    #print the actual awarded board
                    if 'last month' in event['text']: #last month's scoreboard
                        self.bot.send_message(channel, self.bot.scoreboard.get_last_month_scoreboard())
                    elif 'alltime' in event['text'] or 'overall' in event['text']: #overall scoreboard
                        self.bot.send_message(channel, self.bot.scoreboard.get_all_time_scoreboard())
                    else:
                        self.bot.send_message(channel, self.bot.scoreboard.get_scoreboard())
                else:
                    #print the nominator board
                    if 'last month' in event['text']: #last month's scoreboard
                        self.bot.send_message(channel, self.bot.nominators.get_last_month_scoreboard())
                    elif 'alltime' in event['text'] or 'overall' in event['text']: #overall scoreboard
                        self.bot.send_message(channel, self.bot.nominators.get_all_time_scoreboard())
                    else:
                        self.bot.send_message(channel, self.bot.nominators.get_scoreboard())
                return #stop 
            
            #check to set if things need to be reset
            if bot_named and 'reset' in split and self.bot.codeword in split:
                print('Resetting scores.')
                self.bot.scoreboard.reset()
                self.bot.nominators.reset()
                self.bot.save_state()
                self.bot.send_message(channel, "I've reset the scores, Master.")
                return
            
            #check for awards...
            awards = [':kitkat:', ':chocolatebar:', ':chocolate:', ':taco:', 'taco', 'kitkat', 'chocolate']
            award_commands = ['give', 'award', 'won', 'grant', 'hand', 'win', 'gift']
            #does it contain reference to a user?
            if not set(awards).isdisjoint(split) and not set(award_commands).isdisjoint(split):
                #has triggers for an award
                print('Giving an award.')
                named_users = self.get_named_users(event['text'])
                if len(named_users) == 0:
                    #check if bot named
                    print('No named users')
                    if bot_named:
                        self.bot.send_message(channel, "Are you trying to give me an award? I have no hands!")
                        return
                    else:
                        self.bot.send_message(channel, "I'm sorry, I couldn't figure out who you want to give an award to.")
                        return
                else:
                    print('Adding scores for users...')
                    for a_user in set(named_users):
                        self.bot.scoreboard.add_score(a_user)
                    users = str(named_users[0] if len(set(named_users)) == 1 else ','.join(set(named_users)))
                    rewarded = "Hurrah! Awards for " + users + '!!!'
                    self.bot.send_message(channel, rewarded)
                    
                    #record nominators
                    self.bot.nominators.add_score(user, len(set(named_users)))
                    
                    #also log message that caused event
                    print('User:', user, '\tMessage:', event['text'])
                    
                    #save state, and wait for next event
                    self.bot.save_state()
                    return
            

# if run without arguments...
if __name__ == '__main__':
	if len(sys.argv) < 2:
		print('Usage: chocbot.py <API_KEY> [admin_password]')
		print('Admin password is iamgod by default.')
		print('Not enough arguments. You must provide an API key')
		exit()
	
	if len(sys.argv) >= 3:
		Bot(sys.argv[1], sys.argv[2])
	else:
		Bot(sys.argv[1])
