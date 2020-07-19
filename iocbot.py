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
    #although in practice they will likely not be encountered, I think there are some race conditions 
    ###if you type commands too fast- i.e. ending a reservation and calling end again before the next 
    ###reservation has been activated. I'm sure theres a way to synchronize this that wouldnt be too bad. 
    ###Perhaps even just a thread shared busy flag like we did in context switch in OS
    #improve ioc_help and clean up the other commands
    #join reservation in queue using member target or unique identifier or fuckin something
    #visual representation of the queue
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
    
    #Reserve invite-only-channel(s) for len minutes, hooked to the role specified by ioc_role (currently set up in this method, won't necessarily be forever)
    @commands.command(pass_contex=True)
    async def ioc_res(self, ctx, len):
    
        if self.ioc_role is None:
            #if server already has an invite-only-channel role, find it and use that one, otherwise create one from scratch (note this is not what the following line of code currently does, only a future plan)
            self.ioc_role = get(ctx.message.guild.roles, id=730885871188049983)
        
        timeblock = int(len)*60 #convert minutes -> seconds
        
        x = QueueNode(ctx.message.author, timeblock) #Pass reservation holder and reservation into a QueueNode object
        
        if self.active_reservation:     
            self.ioc_queue.put(x) #if someone has the room, queue up
        else:
            await self.reserve(x) #otherwise, reserve the room for timeblock's value in seconds
        
    async def reserve(self, node: QueueNode):
        
        self.active_reservation = True;
        user = node.reqHolder
        timeblock = node.reqLen
    
        await user.add_roles(self.ioc_role) #apply IOC role to user, fetched from the node parameter.
        elapsedTime = 0
    
        self.ioc_group.append(user)
        stepSize = 5
    
        while self.active_reservation and elapsedTime < timeblock: 
            await asyncio.sleep(5) #sleep and allow updates to the self.active_reservation flag
            elapsedTime += stepSize #this variable doesn't actually do anything but its kinda useful for debug info to make sure the loop works at intended.
            print("reserve loop, elapsedTime = " + str(elapsedTime))
        
        print("Broke out of the reserve loop, elapsedTime = " + str(elapsedTime) + ", active_reservation = " + str(self.active_reservation))
        
        for person in self.ioc_group:
            print("role remove loop")
            await person.remove_roles(self.ioc_role) #remove role from all persons in the reservation after that reservation has elapsed
    
        self.ioc_group = []
        self.requests = []
        #lists reset pog
        
        if not self.ioc_queue.empty(): #If somebody is queuing up, recursively reserve for that reservation holder! note: the function is also called from res_ioc
            await self.reserve(self.ioc_queue.get())
        

    @commands.command(pass_context=True)
    async def ioc_req(self, ctx):
        if self.active_reservation:
            #If there is a reservation that you could actually request entrance into, do so.
                #Eventually, I'd like for this to allow you to join a reservation thats in the queue as well
            self.requests.append(ctx.message.author)
            await ctx.message.channel.send("Requesting entrance into the active reservation")
    
    @commands.command(pass_context=True)
    async def ioc_accept(self, ctx, user: discord.Member):
        if ctx.message.author in self.ioc_group and user in self.requests: #maybe just reservation holder, but this works for now.
            await user.add_roles(self.ioc_role)##
            self.ioc_group.append(user)
            #users with ioc or admin role can accept or reject that invitation.

    @commands.command(pass_context=True)
    async def ioc_reject(self, ctx, user: discord.Member):
        if ctx.message.author in self.ioc_group and user in self.requests:
            self.requests.pop(user)
            #users with ioc or admin role can accept or reject that invitation.

    @commands.command(pass_context=True)
    async def ioc_extend(self, ctx):
        #Extend reserved block for current reservation holder.
        #Should probably only work if there is nobody waiting for the reservation to elapse in the queue, or maybe ask the first person in line if they're ok with the current group extending. needs some solution, anyway.
        pass
    
    @commands.command(pass_context=True)
    async def ioc_end(self, ctx):
        if self.active_reservation and ctx.message.author in self.ioc_group:
            #currently, anyone in a reservation can end that reservation. Not necessarily a problem, since you accept/reject requests to join, but it could still potentially be annoying.
            print("ioc_end test")
            self.active_reservation = False
            
    @commands.command(pass_context=True)
    async def ioc_info(self, ctx):
        #we dont have to talk about this ok i dont know how to do pretty formatting in python
        print("*** IOC_INFO:")
        print("\trequests list:")
        print("\t" + str(self.requests))
        print("\tioc group:")
        print("\t" + str(self.ioc_group))
        print("\tioc queue:")
        print("\t" + str(self.ioc_queue))
        print("\tioc queue isEmpty?")
        print("\t\t" + str(self.ioc_queue.empty()))
        print("\tactive_reservation")
        print("\t\t" + str(self.active_reservation))
        print("\tioc role")
        print("\t" + str(self.ioc_role))
        print("***")
    
    @commands.command(pass_context=True)
    async def ioc_viewq(self, ctx):
        s = ""
        i = 0
        temp = []
        
        if self.ioc_queue.empty():
            await ctx.message.channel.send("The queue is currently empty")
            
        else:    
            while not self.ioc_queue.empty():
                temp.append(self.ioc_queue.get())
                node = temp[i]
                s += "Queue Pos " + str(i) + ": " + node.reqHolder.nick + " for " + str(node.reqLen) + " minutes\n"
                i += 1
                
            index = 0
            while index < i:
                self.ioc_queue.put(temp[index])
                index+=1
            
            await ctx.message.channel.send(s)
        
    @commands.command(pass_context=True)
    async def ioc_help(self, ctx):
        #display command list in ctx.message.channel to assist with use
        await ctx.channel.send("IOC COMMAND LIST (they all start with .ioc_)\n\tres: reserve a time block (takes int parameter, currently seconds)\n\treq: request entrance (no visual cue atm)\n\tend: prematurely end reservation \n\taccept/reject to accept/reject requests, takes member tag as a param")
        
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

