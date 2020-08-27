#Discord bot that allows a deck of cards (image files on the host's machine) that can be drawn from
#Originally intended to be generalizable to have one bot host for many game instances, but that would 
#require file storage somewhere other than the host's machine if it was to be generalizable enough, and I just figured, why bother
#So in the end it was decided that a single game for a single bot instance was probably best. 
# - Planned: Save game state to allow 4 different saved games (potentially 4 different decks, I haven't figured out all the semantics there)

import discord
from discord.ext import commands
import random

description = "testing fate"
bot = commands.Bot(command_prefix='?', description=description)

deck = ['deck_back.png','balance_deck.png','comet_deck.png','donjon_deck.png']
autosaveflag = False

class GameState(object): #Class representing data for a deck/game, by server id
    deck = []
    active = []
    removed = []
    specialCards = []
        
    def __init__(self, deck, active, removed, specialCards):
        self.deck = deck
        self.active = active
        self.removed = removed
        self.specialCards = specialCards
    
    #def addCardToDeck() maybe this will be able to accept cards from within a server in the future
    
    def getDeckLength(self):
        return len(self.deck)
    def getDeck(self):
        return self.deck
    def getActiveDeckLength(self):
        return len(self.active)
    def getActiveDeck(self):
        return self.active
    def getRemovedLen(self):
        return len(self.removed)
    def getRemoved(self):
        return self.removed
    def markActive(self, card: str): #O(Deck_size)
        for x in self.removed:
           if x == card:
                self.removed.remove(x)
                self.active.append(card)
                return 0
        
        return -1
    def markInactive(self, card: str): #O(Deck_size)
        for x in self.active:
            if x == card:
                self.active.remove(x)
                self.removed.append(card)
                return 0
                
        return -1
        
    def getSpecialCards(self):
        return self.specialCards
        
    def addSpecialCard(self, card: str):
        #no error checking atm. This should only accept cards in the deck not currently marked as special. 
        self.specialCards.append(card)
        
    def removeSpecialCard(self, card: str): #barebones implementation, no error handling
        self.specialCards.remove(card)
        
    def isSpecial(self, card: str): #O(Deck_size), not great but idk if theres a faster way atm.
        for x in self.specialCards:
            if x == card:
                return True;
        return False;

        
def make_gameState():
    return GameState([], [], [], [])
        
gs = [make_gameState()]


###DEBUGGING#### (Not concerned with efficiency, will eventually be deprecated with new deck I/O system)
@bot.command(pass_context=True)
async def _showDeck(ctx):
    state = gs[0]
    myDeck = state.getDeck()
    print("Debug printing card names and indices in the deck")
    i = 0
    for card in myDeck:
        print(str(i) + " : " + myDeck[i])
        i += 1
    
    
@bot.command(pass_context=True)
async def _showActive(ctx):
    state = gs[0]
    myDeck = state.getActiveDeck()
    
    print("Debug printing active card deck")
    i = 0
    for card in myDeck:
        print(str(i) + " : " + myDeck[i])
        i += 1

@bot.command(pass_context=True)
async def _showSpecial(ctx):
    state = gs[0]
    myDeck = state.getSpecialCards()
    
    if len(myDeck) > 1:
        print("Debug printing special card list")
    i = 0
    for card in myDeck:
        print(str(i) + " : " + myDeck[i])
        i += 1

     
@bot.command()
async def _exit(ctx):
    await bot.logout()


@bot.command(pass_context=True)
async def _mCIS(ctx, i): #markCardIndexSpecial (active deck index for now)
    print("_mCIS: i = " + str(i))
    x = int(i)
    state = gs[0]
    myDeck = state.getActiveDeck()
    print(x)
    state.addSpecialCard(myDeck[x])
    
@bot.command(pass_context=True)
async def _uCIS(ctx, card_fileName: str): #unmark
    for card in gs[0].getDeck():
        if card == card_fileName and gs[0].isSpecial(card):
            gs[0].removeSpecialCard(card)
            

@bot.event
async def on_ready():
    print('The Deck has arrived! What fate awaits you? !draw and find out.'.format(bot))

def pollSaveSwitch() {
    return autosaveflag
}

async def autoSaveGameState() {
    int delay = 100 #change auto-save to disk frequency
    
    while pollSaveSwitch():
        asyncio.sleep(delay)
}
    
@bot.command(pass_context=True)
async def enableAutoSave(ctx) {
    autosaveflag = True
    bot.loop.create_task(autoSaveGameState())
}

@bot.command(pass_context=True)
async def disableAutoSave(ctx) {
    autosaveflag = False
}




@bot.command(pass_context=True)
async def startGame(ctx): #create a game state object for the current server
    #TODO: add a checker to see if game is already started/permission gate to prevent restarting mid-game
    
    #INTENDED DESIGN:
        #call startGame and it will look through server host's server bot location to find deck files.
        #then it will initialize deck, active, removed, and special (active/removed ought to be empty on initialization)

    gs[0] = GameState(deck, deck.copy(), [], []) #obv todo set up parameters as the rest of the tech is implemented
    
    await ctx.channel.send("session created/reset")    
    
@bot.command(pas_context=True)
async def draw(ctx): 
    if not gs:
        await ctx.channel.send("Game State uninitialized. Cannot draw a card until you set up a deck then call " + str(bot.command_prefix) + "startGame.");
    else:
        await cardGeneration(ctx, gs[0])
    
async def cardGeneration(ctx, gs: GameState): #Not an out-facing method. Idk how context shit works but do not make this a command
    cards = gs.getActiveDeck()
    activeLen = gs.getActiveDeckLength()
    if activeLen == 0:
       await ctx.channel.send("Active Deck returned a length of 0. That shouldn't be possible")
    else:
       card = random.choice(cards)
       if gs.isSpecial(card):
            gs.markInactive(card)
       await ctx.channel.send(file=discord.File(card));     
       
  
#We dont even really need to listen to messages, yet. Thats the point of @bot.command and using bot vs client.
#@bot.event
#async def on_message(message):
    #if message.author != bot.user:
   
      
print("does this actually fucking work?????")
bot.run('NzIwNzgxNTQ4ODE0NTk4MjA0.XuPnew.eScXFTCNWd3yXy2RHL9qIaTyLA0')