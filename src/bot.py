import json, re, os, time, sys, urllib, asyncio
import aiohttp
import chatter


# Securely handle our token. We also might not always be using Docker so we'll add a backup.
temporaryToken = None
try:
	with open(f"/run/secrets/{os.getenv('BOT_TOKEN_DOCKER_SECRET_NAME', 'bot_token')}") as f:
		temporaryToken = f.read()
except:
	pass

botToken = os.getenv("BOT_TOKEN", temporaryToken)  
del temporaryToken

discordEntryUrl = "/gateway"
discordWebAPI = "https://discordapp.com/api"
discordAPI = None
heartbeatInterval = 0

specialHeaders = {"Authorization": f"Bot {botToken}", "Content-Type": "application/json; charset=UTF-8;"}
aioClientSession = None

#Build up our auth token. Needed for when we first connect to the Discord Websockets API.
async def Authenticate(websocket: aiohttp.ClientWebSocketResponse):
	authDict = {
		"op": 2,
		"d": {
			"token": botToken,
			"properties": {},
			"compress": False,
			"large_threshold": 250
		}
	}
	return await websocket.send_str(json.dumps(authDict))

# Standard heartbeat so Discord knows we're still alive.
# The Discord docs seem to contradict itself on what actually needs to be sent,
# that said the below works without issue.
async def BotHeartbeat(websocket: aiohttp.ClientWebSocketResponse, interval: int):
	while True:
		await asyncio.sleep(heartbeatInterval / 1000)
		await websocket.send_str(json.dumps({"op": 1, "d": 0}))

async def CheckChatFunction(userID: str, strMessage: str, optionalContent: any):
	# Allows for a user to use ! or / when calling a command.
	checkForChatCommand = re.match("(?:!|/)([A-Za-z]+)\s?(?:(.+))?", strMessage)
	if not checkForChatCommand:
		return

	if hasattr(chatter, checkForChatCommand.group(1)):
		try:
			await getattr(chatter, checkForChatCommand.group(1))(userID, checkForChatCommand.group(2), optionalContent)
		except Exception as Error:
			# Error handling goes here
			pass
	return

async def RunBotFunctions():
	global aioClientSession
	if aioClientSession is not None:
		aioClientSession.close()
	else:
		aioClientSession = aiohttp.ClientSession()

	async with aioClientSession.ws_connect(f"{discordAPI}?v=6&encoding=json") as websocket:
		async for msg in websocket:
			jsonMsg = json.loads(msg[1])

			# Ideal if you want to debug in the moment.
			if os.getenv("DEBUG_BOT", False):
				print(jsonMsg)

			if jsonMsg.get("retry_after") is not None:
				time.sleep(jsonMsg.get("retry_after"))

			if jsonMsg["op"] in [7, 9]: #Invalid Session, lets reboot.
				sys.exit()

			if jsonMsg["op"] == 10:
				global heartbeatInterval
				heartbeatInterval = jsonMsg['d']["heartbeat_interval"]
				await Authenticate(websocket)

			if jsonMsg["op"] == 0 and jsonMsg["t"] == "READY":
				# Event loop to send a heartbeat every 10 seconds.
				asyncio.ensure_future(BotHeartbeat(websocket, heartbeatInterval))

			# Message created? Lets see if we have a chat function we can use!
			if jsonMsg["op"] == 0 and jsonMsg["t"] == "MESSAGE_CREATE":
				await CheckChatFunction(jsonMsg["d"]["author"]["id"], jsonMsg["d"]["content"], jsonMsg["d"])

async def BotStart():
	await RunBotFunctions()

# This is just some generic functions to get the bot ticking,
# loading the API and so on.
def BotDeployment():

	apiDataInfo = urllib.request.Request(f"{discordWebAPI}{discordEntryUrl}", headers = {"User-Agent": os.getenv("DISCORD_API_USERAGENT", "BettyBot by Teddi")})
	apiData = urllib.request.urlopen(apiDataInfo)
	global discordAPI
	discordAPI = json.loads(apiData.read())['url']

	try:
		# Typical asyncio event loop stuff.
		loop = asyncio.get_event_loop()
		loop.run_until_complete(BotStart())
		loop.close()
	except asyncio.CancelledError as Error:
		# Basic sane handling of a closed connection
		# If we terminate it on our end this won't get called, but
		# If discord closes it, this allows a reconnection.
		# You may want to allow a time-delay if Discord is having a particularly
		# bad day.
		BotDeployment()

#And assuming you want to run the bot...
if __name__ == '__main__':
	BotDeployment()



