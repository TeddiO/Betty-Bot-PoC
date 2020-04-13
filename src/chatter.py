from bot import discordWebAPI, specialHeaders
import json, re, asyncio, aiohttp

# Below are some example functions you can use to call upon from your Bot.
# Obviously implementation doesn't have to follow the above with has/getattr,
# and helper functions are certainly ideal for a lot of this.
# but as a general, working PoC it works :)

sessionObject = aiohttp.ClientSession()

async def SendChannelMessage(text: str, channel: str, headers: dict = specialHeaders, typing: bool = False):
	await sessionObject.post(f"{discordWebAPI}/channels/{channel}/messages", json={"content": f"{text}"}, headers = headers)

async def SendUserMessage(text: str, user: str, headers: dict = specialHeaders, typing: bool = False):
	channelID = None

	channel = await sessionObject.post(f"{discordWebAPI}/users/@me/channels", json={"recipient_id": user}, headers = headers)
	channelData = await channel.json()
	channelID = channelData["id"]

	await sessionObject.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"{text}"}, headers = headers)
		
	if typing == True:
		await sessionObject.post(f"{discordWebAPI}/channels/{channelID}/typing", headers = headers)

async def ping(userID: str, strMessage: str, *args: dict):
	channelID = args[0]["channel_id"]
	
	msg = None
	if strMessage is None:
		msg = "Default Pong!"
	else:
		msg = f"PONG: {strMessage}"

	await SendChannelMessage(msg, channelID)

async def pvtping(userID: str, strMessage: str, *args: dict):
	msg = None
	if strMessage is None:
		msg = "Default Pong!"
	else:
		msg = f"PONG: {strMessage}"

	await SendUserMessage(msg, userID)


# Purges chat history based on the messageID. As per discord, you can
# specify before, after or "around" the target message.
async def purge(userID: str, strMessage: str, *args: dict):
	# You probably want protection here so people can't just use it :)

	channelID = args[0]["channel_id"]
	targetID = re.search(r"(?!@)(\d+)\s?", strMessage)

	# Discord applies an ID to each message. This is by far the easiest way to pick up and purge messages.
	if not targetID:
		return await sessionObject.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"Couldn't find a messageID with that ID!"}, headers=specialHeaders)

	targetID = targetID.group(1)

	messageFilter = re.search("(before|after|around)", strMessage)
	messageFilter = messageFilter.group(1) if messageFilter is not None else "around"

	# If we only want to filter a users messages (as opposed to the entire history from a point)
	# Then we can do this. If we find a player - ensure we only keep their messages.
	userSpecified = re.search(r"<@!(\d+)>", strMessage)
	if userSpecified:
		userSpecified = userSpecified.group(1)
	else:
		userSpecified = False

	# How many messages we want to purge. Useful if you don't want to shred a users entire history
	# Note there's a Discord API cap of 100 at this time. Anything else gets capped accordingly.
	amount = re.search(r"\d+\s.*?(\d+)$", strMessage)
	if not amount:
		return await sessionObject.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"Invalid amount specified!"}, headers=specialHeaders)
		
	amount = amount.group(1)
	messageIDs = []

	getMessages = await sessionObject.get(f"{discordWebAPI}/channels/{channelID}/messages", params={messageFilter: targetID, "limit": amount}, headers=specialHeaders)
	messageData = await getMessages.json()

	for v in messageData:
		if userSpecified and userSpecified == v["author"]["id"]:
			messageIDs.append(v["id"])
			continue
		else:
			messageIDs.append(v["id"])

	if len(messageIDs) == 0:
		return await SendChannelMessage("Cannot find a message with that ID.", channelID)
	
	# Uses the bulk messaging system. Again capped to 100.
	bulkDelete = await sessionObject.post(f"{discordWebAPI}/channels/{channelID}/messages/bulk-delete", json={"messages": messageIDs}, headers=specialHeaders)
	if bulkDelete.status == 400:
		await SendUserMessage(bulkDelete.json()["message"], userID)
	
	# We finish off by deleting our command.
	return await sessionObject.delete(f"{discordWebAPI}/channels/{channelID}/messages/{args[0]['id']}", headers=specialHeaders)

async def help(userID: str, strMessage: str, *args: dict):
	channelID = args[0]["channel_id"]
	helpMessage = """
This is a list of commands publically available.

All commands can use ! or / as a prefix.

!pvtping - Pings you in a PM
!purge <messageid> <amount> <before|after|around> <userfilter>
!ping - pong!
"""

	return await SendChannelMessage(helpMessage, channelID)
