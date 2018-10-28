# chocbot
Slack bot with basic functionality for rewarding users.

---

## Running

Use the following command to run the program:

`python chocbot.py <API_KEY> [admin_password]`

`API_KEY` is a value from Slack, starting `'xoxb-...'`

## Prerequisites


`slackclient==1.3.0
 python_dateutil==2.7.5`

You can install these with:

`pip install -r requirements.txt`

---

## Usage

### Rewarding a user
In the channel, you simply 'give' the intended person (use '@' person) a chocolate, chocolate bar, etc. You can give multiple people a reward in one go (just tag them all!).

Chocbot will respond in the channel to let you know the award has been given.

### Viewing the scoreboard
You can view the current scoreboard by tagging the bot and asking for the scoreboard (or tally), e.g. @chocbot scoreboard

You can view the last month, or all time scoreboard by using 'last month' or 'overall' in your request.

You can view the scoreboard for those who have nominated by using 'nominators' e.g. @chocbot nominators

### Resetting the bot
By default, the bot will save state.  To reset to be blank, use @chocbot reset adminpassword. The admin password must match the text you supplied when you started the bot.

