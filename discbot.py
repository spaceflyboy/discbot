import discord
from discord.ext import commands
import random
import queue
from discord.utils import get
import logging
import asyncio
logging.basicConfig(level=logging.INFO)
description = '''gaming'''

####TODO
    #eventually, maybe showinfo function using get_commands from Cog for help information (LOW PRIO)
    #role creation from scratch and maybe channel marking
    #hopefully eventually generalization across servers would be neato but would require large redesign to encapsulate instance data in something other than a cog (or maybe just a sublayer under the cog with a dict for server id --> state info or something

class QueueNode:
        def __init__(self, reqHolder, reqLen):
            self.reqHolder = reqHolder
            self.reqLen = reqLen   

class ReservationHandler(commands.Cog):
    
    def __init__(self, bot, requests, ioc_group, ioc_queue, active_reservation, ioc_role):
        self.bot = bot
        self.requests = requests
        self.ioc_group = ioc_group
        self.ioc_queue = ioc_queue
        self.active_reservation = active_reservation
        self.ioc_role = ioc_role
    
    @commands.command(pass_contex=True)
    async def ioc_res(self, ctx, len):
        #Assign IOC role 
        #On role state change, (elapsed reserved time slot, for example) it would be wise to flush the join requests dictionary.
        if self.ioc_role is None:
            self.ioc_role = get(ctx.message.guild.roles, id=730885871188049983)
            
        x = QueueNode(ctx.message.author, int(len))
        
        if self.active_reservation:     
            self.ioc_queue.put(x)
        else:
            await self.reserve(x)
        
    async def reserve(self, node: QueueNode):
        self.active_reservation = True;
        user = node.reqHolder
        timeblock = node.reqLen
    
        await user.add_roles(self.ioc_role)##
        elapsedTime = 0
    
        self.ioc_group.append(user)
        stepSize = 5
    
        while self.active_reservation and elapsedTime < timeblock:
            await asyncio.sleep(5)
            elapsedTime += stepSize
            print("reserve loop, elapsedTime = " + str(elapsedTime))
        
        print("Broke out of the reserve loop, elapsedTime = " + str(elapsedTime) + ", active_reservation = " + str(self.active_reservation))
        
        for person in self.ioc_group:
            await person.remove_roles(self.ioc_role)##
    
        self.ioc_group = []
        self.requests = []
    
        if not self.ioc_queue.empty():
            await self.reserve(self.ioc_queue.get())
        

    @commands.command(pass_context=True)
    async def ioc_req(self, ctx):
        if self.active_reservation:
            self.requests.append(ctx.message.author)
    
    @commands.command(pass_context=True)
    async def ioc_accept(self, ctx, user: discord.Member):
        if ctx.message.author in self.ioc_group and user in self.requests: #maybe just reservation holder, but this works for now.
            await user.add_roles(self.ioc_role)##
            self.ioc_group.append(user)
            #users with ioc or admin role can accept or reject that invitation.

    @commands.command(pass_context=True)
    async def ioc_reject(self, ctx, user: discord.Member):
        if ctx.message.author in self.ioc_group:
            self.requests.pop(user)
            #users with ioc or admin role can accept or reject that invitation.

    @commands.command(pass_context=True)
    async def ioc_extend(self, ctx):
        #Extend reserved block for current reservation holder.
        #Should probably only work if there is nobody waiting for the reservation to elapse in the queue, or maybe ask the first person in line if they're ok with the current group extending. needs some solution, anyway.
        pass
    
    @commands.command(pass_context=True)
    async def ioc_end(self, ctx):
        if self.active_reservation:
            self.ioc_group = []
            self.active_reservation = False
            
    @commands.command(pass_context=True)
    async def ioc_info(self, ctx):
        print("*** IOC_INFO:")
        print("\trequests list:")
        print("\t" + str(self.requests))
        print("\tioc group:")
        print("\t" + str(self.ioc_group))
        print("\tioc queue:")
        print("\t" + str(self.ioc_queue))
        print("\tioc queue isEmpty?")
        print("\t" + str(self.ioc_queue.empty()))
        print("\tactive_reservation")
        print("\t" + str(self.active_reservation))
        print("\tioc role")
        print("\t" + str(self.ioc_role))
        print("***")
        
requests = [] #list for persons seeking entry into a currently reserved invite-only-channel
ioc_group = [] #list of people in current reservation group
ioc_queue = queue.Queue(maxsize=0)  #queue of QueueNode objects representing the line for the reserved channel
active_reservation = False #shared flag representing state of ioc-channel
bot = commands.Bot(command_prefix='.', description=description)

bot.add_cog(ReservationHandler(bot, requests, ioc_group, ioc_queue, active_reservation, None))

@bot.event
async def on_ready():
    print('time for gaming'.format(bot))

@bot.command()
async def exit(ctx):
    await bot.logout()

token = ''
with open('discbot_token.txt') as f:
    token = next(f)
    
bot.run(token)

