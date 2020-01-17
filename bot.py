import os
import json
import logging
import discord
from dotenv import load_dotenv
import asyncio
import requests

load_dotenv()
logging.basicConfig(
	format='%(asctime)s %(levelname)-8s %(message)s',
	level=logging.INFO,
	datefmt='%Y-%m-%d %H:%M:%S'
)
TOKEN = os.getenv('DISCORD_TOKEN')
CHANNEL = os.getenv('DISCORD_CHANNEL')
USER_ID = os.getenv('TWITCH_USER_ID')
CLIENT_ID = os.getenv('TWITCH_CLIENT_ID')
HEADERS = {
	'Client-ID': CLIENT_ID
}
client = discord.Client()
stream_live = False
init = True
channel = None

def main():
	if not TOKEN or not CHANNEL or not USER_ID or not CLIENT_ID:
		logging.error('Invalid configuration')
		for key, value in {'Token': TOKEN, 'Channel': CHANNEL, 'User-ID': USER_ID, 'Client-ID': CLIENT_ID}.items():
			if not value:
				logging.error(f'{key} missing')
		return
	client.run(TOKEN)

async def query_status():
	global stream_live, init
	logging.info('Querying stream status...')
	streamer_data = get_streamer_data(USER_ID)
	if len(streamer_data) > 0 and streamer_data[0]['type'] == 'live':
		logging.debug(streamer_data[0])
		if not stream_live and not init:
			game_data = get_game_name(streamer_data[0]['game_id'])
			await discord_notify(streamer_data[0], game_data)
		stream_live = True
	else:
		logging.info('Stream offline')
		stream_live = False
	init = False

def get_streamer_data(user_id: str):
	res = requests.get(url = 'https://api.twitch.tv/helix/streams', params = {'user_id': user_id}, headers = HEADERS)
	return res.json()['data']

def get_game_name(game_id: str):
	res = requests.get(url = 'https://api.twitch.tv/helix/games', params = {'id': game_id}, headers = HEADERS)
	if len(res.json()['data']) > 0:
		return res.json()['data'][0]['name']
	else:
		return 'unknown'

async def discord_notify(streamer_data, game_name):
	global channel
	logging.info(f'Stream went live! Notifying #{channel.name}')
	await channel.send(f"@here {streamer_data['user_name']} just went live!\n\
		Playing {game_name}\n\
		{streamer_data['title']}\n\
		Watch here: https://twitch.tv/{streamer_data['user_name']}")

@client.event
async def on_ready():
	global channel

	channel = client.get_channel(int(CHANNEL))
	logging.info(
		f'{client.user} has connected to Discord!\n'
		f'Sending notifications in #{channel.name}'
	)

	while True:
		await query_status()
		await asyncio.sleep(60)

if __name__ == "__main__":
    main()