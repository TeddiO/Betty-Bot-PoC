import websockets
import asyncio
import json, re
import requests
import chatter

botToken = ""
#Auth bot via this - https://discordapp.com/oauth2/authorize?scope=bot&permissions=o&client_id=<bot_user_here>
discordEntryUrl = "/gateway"
discordWebAPI = "https://discordapp.com/api"
discordAPI = None
heartbeatInterval = 0

specialHeaders = {"Authorization": f"Bot {botToken}", "Content-Type": "application/json; charset=UTF-8;"}

#Build up our auth token. Needed for when we first connect to the Discord Websockets API.
async def Authenticate(websocket):
	authDict = {
		"op": 2,
		"d": {
			"token": botToken,
			"properties": {},
			"compress": False,
			"large_threshold": 250
		}
	}
	return await websocket.send(json.dumps(authDict))

#Standard heartbeat so Discord knows we're still alive.
#The Discord docs seem to contradict itself on what actually needs to be sent,
#that said the below works without issue.
async def BotHeartbeat(websocket, interval):
	while True:
		await asyncio.sleep(heartbeatInterval / 1000)
		await websocket.send(json.dumps({"op": 1, "d": 0}))

async def CheckChatFunction(userID, strMessage, optionalContent):
	#Neat little regex strip that allows you to have chat commands.
	#Eg you can have !help or /help and both will point to the same command.
	checkForChatCommand = re.match("(?:!|/)([A-Za-z]+)\s?(?:(.+))?", strMessage)
	if not checkForChatCommand:
		return

	if hasattr(chatter, checkForChatCommand.group(1)):
		try:
			getattr(chatter, checkForChatCommand.group(1))(userID, checkForChatCommand.group(2), optionalContent)
		except Exception as Error:
			#Generic error handling here.
			pass
	return


async def RunBotFunctions():
	async with websockets.connect(f"{discordAPI}?v=6&encoding=json") as websocket:
		async for msg in websocket:
			jsonMsg = json.loads(msg)

			#When we're authenticating, Discord tells us
			#How often it wants us to talk back. It can also
			#Change these rates if they're having issues.
			if jsonMsg["op"] == 10:
				global heartbeatInterval
				heartbeatInterval = jsonMsg['d']["heartbeat_interval"]
				await Authenticate(websocket)

			#If we've authenticated and Discord says we're golden, start the heartbeat!
			if jsonMsg["op"] == 0 and jsonMsg["t"] == "READY":
				#Event loop to send a heartbeat every 10 seconds.
				asyncio.ensure_future(BotHeartbeat(websocket, heartbeatInterval))

			#Use this to monitor when a user talks.
			if jsonMsg["op"] == 0 and jsonMsg["t"] == "MESSAGE_CREATE":
				await CheckChatFunction(jsonMsg["d"]["author"]["id"], jsonMsg["d"]["content"], jsonMsg["d"])


async def BotStart():
	await RunBotFunctions()


#This is just some generic functions to get the bot ticking,
#loading the #API and so on.
def BotDeployment():

	apiData = requests.get(f"{discordWebAPI}{discordEntryUrl}")
	global discordAPI
	discordAPI = apiData.json()['url']

	try:
		#Typica asyncio event loop stuff.
		loop = asyncio.get_event_loop()
		loop.run_until_complete(BotStart())
		loop.close()
	except websockets.exceptions.ConnectionClosed:
		#Basic sane handling of a closed connection
		#If we terminate it on our end this won't get called, but
		#If discord closes it, this allows a reconnection.
		BotDeployment()

#And assuming you want to run the bot...
if __name__ == '__main__':
	BotDeployment()



