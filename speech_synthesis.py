from elevenlabs.client import ElevenLabs
from elevenlabs import Voice, VoiceSettings, play
import requests
import json
import base64
import utils
import os
from pathlib import Path
from openai import OpenAI

OPEN_AI_SECRET_KEY = os.getenv("OPEN_AI_SECRET_KEY")
# OpenAI API client
open_ai_client = OpenAI(api_key=OPEN_AI_SECRET_KEY)

# ELevans Labs API client
elevan_labs_client = ElevenLabs(
  api_key= os.getenv('ELEVEN_LABS_SECRET_KEY')
)
# Check moderation status of a voice
def check_moderation_status(text):

    response = open_ai_client.moderations.create(input=text)

    output = response.results[0]
    
    return output

# Get Embedding 
def get_embedding(text, model="text-embedding-3-small"):

    response = open_ai_client.embeddings.create(
        input=text,
        model=model
    )

    output = response.data[0].embedding
    
    return output

# Define the function to generate TTS with timestamps
def generate_tts_with_timestamps(text, voice_id="21m00Tcm4TlvDq8ikWAM"):
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps"
    headers = {
        "Content-Type": "application/json",
        "xi-api-key": "sk_51d763ecf88595a359a9bb77fd318a7a6e71a4422005bb68"
    }
    data = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if response.status_code != 200:
        print(f"Error encountered, status: {response.status_code}, content: {response.text}")
        return

    response_dict = response.json()

    # Decode the audio and save as mp3 file
    audio_bytes = base64.b64decode(response_dict["audio_base64"])
    with open('output.mp3', 'wb') as f:
        f.write(audio_bytes)

    # Print the alignment for timestamps
    print(utils.characters_to_words(response_dict['alignment']['characters'], response_dict['alignment']['character_start_times_seconds'], response_dict['alignment']['character_end_times_seconds']))

# generate_tts_with_timestamps("Born and raised in the charming south, I can add a touch of sweet southern hospitality to your audiobooks and podcasts")
# check_moderation_status("Born and raised in the charming south, I can add a touch of sweet southern hospitality to your audiobooks and podcasts")