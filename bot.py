# github.com/sofullstack
# obviously random, logs prediction history to produce the same predictions for repeated game-ids
import json
import datetime
import colorama
import re
import random
import discord

class Logger:
    def __init__(self, type):
        self.types = {
            'success' : f'✅ {colorama.Fore.LIGHTGREEN_EX} ',
            'failure'  : f'❌ {colorama.Fore.LIGHTRED_EX} ',
            'warning' : f'⚠️  {colorama.Fore.LIGHTYELLOW_EX} ',
        }
        self.type = type

    def log(self, msg: str):
        if self.type.lower() not in self.types:
            return Logger('failure').log('Invalid log type')
        
        # colorama.Fore.<self.types.get(type)> , datetime.datetime.now()<extraction_logic> , msg , colorama.Fore.RESET
        return print(f'{{}}{{}} | {{}}{{}}'.format(self.types.get(self.type.lower()), str(datetime.datetime.now()).split(' ')[1].split('.')[0], msg, colorama.Fore.RESET))

class Predictor:
    def __init__(self):
        self.history = json.load(open('data/history.json'))
        self.auth = json.load(open('data/auth.json'))

    def link(self, userid: str, authtoken: str):
        for auth in self.auth:
            if auth['authtoken'] == authtoken:
                return 'already linked'
            
            if auth['id'] == str(userid):
                return 'user already linked'
        
        self.auth.append({
            'id':str(userid),
            'authtoken':str(authtoken)
        })

        with open('data/auth.json','w') as f:
            json.dump(self.auth,f,indent=4)

        return 'linked'

    def unlink(self, userid: str):
        i=0
        found=False
        for auth in self.auth:
            i+=1
            if auth['id'] == str(userid):
                found=True
                break
        if found==True:
            self.auth.pop(i - 1)
            with open('data/auth.json','w') as f:
                json.dump(self.auth,f,indent=4)
            return 'unlinked'
        return 'not linked'
    
    def islinked(self, userid: str):
        for auth in self.auth:
            if auth['id'] == str(userid):
                return True
        return False
            
    def mines(self, safespots, gameid):
        valid = lambda id: bool(re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', id))
        if not valid(gameid):
            return 'invalid gameid'
        
        for pred in self.history:
            if pred['id'] == str(gameid):
                return pred['prediction']
        
        safespots = min(safespots, 25)
        grid = ['❌'] * 25
        predicted = random.sample(range(25), safespots)

        for pos in predicted:
            grid[pos] = '✅'

        gridstr = ""
        for i in range(0, 25, 5):
            gridstr += " ".join(grid[i:i+5]) + "\n"

        self.history.append({
            'id':str(gameid),
            'prediction':gridstr
        })

        with open('data/history.json','w') as f:
                json.dump(self.history,f,indent=4)

        return gridstr
    
    def towers(self, gameid):
        valid = lambda id: bool(re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', id))
        if not valid(gameid):
            return 'invalid gameid'
        
        for pred in self.history:
            if pred['id'] == str(gameid):
                return pred['prediction']
        
        grid = ['❌'] * 24
        predicted = [random.choice(range(i, i+3)) for i in range(0, 24, 3)]

        for pos in predicted:
            grid[pos] = '✅'

        gridstr = ""
        for i in range(0, 24, 3):
            gridstr += " ".join(grid[i:i+3]) + "\n"

        self.history.append({
            'id':str(gameid),
            'prediction':gridstr
        })

        with open('data/history.json','w') as f:
                json.dump(self.history,f,indent=4)

        return gridstr

bot = discord.Client(intents=discord.Intents.all())
tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await tree.sync(guild=discord.Object(json.load(open('config.json'))['guild']))
    Logger('success').log('CommandTree Synced')

@tree.command(
    name="link",
    description="✅ Connect your auth token to the bot.",
    guild=discord.Object(json.load(open('config.json'))['guild'])
)
async def link(interaction: discord.Interaction, authtoken: str):
    linked = Predictor().link(interaction.user.id,authtoken)
    if linked == 'already linked':
        return await interaction.response.send_message('This auth token is already linked.',ephemeral=True)
    if linked == 'user already linked':
        return await interaction.response.send_message('You have already linked an authtoken. Run `/unlink` in order to access this command again.',ephemeral=True)
    
    if authtoken.lower().startswith('3cm') == False:
        return interaction.response.send_message('Please provide a **valid** auth token. Contact staff for help with getting it.',ephemeral=True)
    
    return await interaction.response.send_message('Successfully linked auth token.',ephemeral=True)

@tree.command(
    name="unlink",
    description="❌ Disconnect your auth token from the bot.",
    guild=discord.Object(json.load(open('config.json'))['guild'])
)
async def unlink(interaction: discord.Interaction):
    linked = Predictor().unlink(interaction.user.id)
    if linked == 'not linked':
        return await interaction.response.send_message('You do not have an auth token linked.',ephemeral=True)
    
    return await interaction.response.send_message('Successfully unlinked auth token.',ephemeral=True)

@tree.command(
    name="mines",
    description="💣 Predict your sessions mines outcome.",
    guild=discord.Object(json.load(open('config.json'))['guild'])
)
async def mines(interaction: discord.Interaction, safespots: str, gameid: str):
    if Predictor().islinked(str(interaction.user.id)) == False:
        return await interaction.response.send_message('Please link your auth token using `/link` before prediction.', ephemeral=True)
    
    prediction = Predictor().mines(int(safespots),gameid)
    if prediction == 'invalid gameid':
        return await interaction.response.send_message('Please provid a **valid** and **active** gameid. Contact a staff member for help on getting the gameid.',ephemeral=True)
    
    return await interaction.response.send_message(prediction,ephemeral=True)

@tree.command(
    name="towers",
    description="🗼 Predict your sessions towers outcome.",
    guild=discord.Object(json.load(open('config.json'))['guild'])
)
async def mines(interaction: discord.Interaction, gameid: str):
    if Predictor().islinked(str(interaction.user.id)) == False:
        return await interaction.response.send_message('Please link your auth token using `/link` before prediction.')
    
    prediction = Predictor().towers(gameid)
    if prediction == 'invalid gameid':
        return await interaction.response.send_message('Please provid a **valid** and **active** gameid. Contact a staff member for help on getting the gameid.',ephemeral=True)
    
    return await interaction.response.send_message(prediction,ephemeral=True)

bot.run(json.load(open('config.json'))['token'])