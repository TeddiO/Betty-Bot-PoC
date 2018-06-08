from bot import discordWebAPI, specialHeaders
import requests, re

#Below are some example functions you can use to call upon from your Bot.
#Obviously implementation doesn't have to follow the above with has/getattr,
#and helper functions are certainly ideal for a lot of this.
#but as a general, working PoC it works :)

def ping(userID, strMessage, *args):

	channelID = args[0]["channel_id"]
	msg = None
	if strMessage is None:
		msg = "Default Pong!"
	else:
		msg = f"PONG: {strMessage}"

	requests.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"{msg}"}, headers=specialHeaders)

#This function works by sending a PM to the user, as opposed to posting back in the public channel.
def pvtping(userID, strMessage, *args):
	msg = None
	if strMessage is None:
		msg = "Default Pong!"
	else:
		msg = f"PONG: {strMessage}"

	channel = requests.post(f"{discordWebAPI}/users/@me/channels", json={"recipient_id": userID}, headers=specialHeaders)
	channelData = channel.json()
	channelID = channelData["id"]
	requests.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"{msg}"}, headers=specialHeaders)


#Purges chat history based on the messageID. As per discord, you can
#specify before, after or "around" the target message.
def purge(userID, strMessage, *args):
	#You probably want protection here so people can't just use it :)

	channelID = args[0]["channel_id"]
	targetID = re.search("(?!@)(\d+)\s?", strMessage)

	#Discord applies an ID to each message. This is by far the easiest way to pick up and purge messages.
	if not targetID:
		requests.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"Couldn't find a messageID with that ID!"}, headers=specialHeaders)
		return

	targetID = targetID.group(1)

	messageFilter = re.search("(before|after|around)", strMessage)
	messageFilter = messageFilter.group(1) if messageFilter is not None else "around"

	#If we only want to filter a users messages (as opposed to the entire history from a point)
	#Then we can do this. If we find a player - ensure we only keep their messages.
	userSpecified = re.search("<@(\d+)>", strMessage)
	if userSpecified:
		userSpecified = userSpecified.group(1)
	else:
		userSpecified = False

	#How many messages we want to purge. Useful if you don't want to shred a users entire history
	#Note there's a Discord API cap of 100 at this time. Anything else gets capped accordingly.
	amount = re.search("\d+\s.*?(\d+)$", strMessage)
	if not amount:
		requests.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"Invalid amount specified!"}, headers=specialHeaders)
		return

	amount = amount.group(1)

	getMessages = requests.get(f"{discordWebAPI}/channels/{channelID}/messages", params={messageFilter: targetID, "limit": amount}, headers=specialHeaders)
	messageData = getMessages.json()

	messageIDs = []

	for v in messageData:
		if userSpecified and userSpecified == v["author"]["id"]:
			messageIDs.append(v["id"])
			continue
		else:
			messageIDs.append(v["id"])

	if len(messageIDs) == 0:
		requests.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"Cannot find a message with that ID."}, headers=specialHeaders)

	#Uses the bulk messaging system. Again capped to 100.
	requests.post(f"{discordWebAPI}/channels/{channelID}/messages/bulk-delete", json={"messages": messageIDs}, headers=specialHeaders)

	#We also choose to delete our command as we can see it's succesfully ran.
	requests.delete(f"{discordWebAPI}/channels/{channelID}/messages/{args[0]['id']}", headers=specialHeaders)



def help(userID, strMessage, *args):

	channelID = args[0]["channel_id"]

	helpMessage = """
This is a list of commands publically available.

All commands can use ! or / as a prefix.

!pvtping - Pings you in a PM
!purge <messageid> <amount> <before|after|around> <userfilter>
!ping - pong!
"""


	requests.post(f"{discordWebAPI}/channels/{channelID}/messages", json={"content": f"{helpMessage}"}, headers=specialHeaders)
