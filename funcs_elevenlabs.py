import requests
import json
import random
from elevenlabs import set_api_key
elevenlabs_api_key = "d9824f8752565ea5e909ff4c45bc4693"
set_api_key(elevenlabs_api_key)



def get_voices():
    url = 'https://api.elevenlabs.io/v1/voices'
    headers = {
        'accept': 'application/json',
        'xi-api-key': elevenlabs_api_key
    }

    response = requests.get(url, headers=headers)
    

    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: {response.status_code}"




import json
import random
import requests

def text_to_speech(voice_id="flq6f7yk4E4fJM5XTYuZ", text="Hello world", stability=0, similarity_boost=0, style=0, use_speaker_boost=True):

    # rand_no = random.randint(0, 100000000)

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    params = {
        "optimize_streaming_latency": 0,
        "output_format": "mp3_44100_192"
    }
    
    headers = {
        "accept": "audio/mpeg",
        "xi-api-key": elevenlabs_api_key,  # Additional header
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "use_speaker_boost": use_speaker_boost
        }
    }
    
    response = requests.post(url, params=params, headers=headers, json=payload)
    print(response)

    if response.status_code == 200:
        return response.content
    else:
        print(f"An error occurred. HTTP Status Code: {response.status_code}. Response Text: {response.text}")




# Invoke the function
# text_to_speech()


# def get_tts_url (filepath):



# def binary_to_filename():
#     filename = f"uploads/{rand_no}.mp3"
#     with open(filename, "wb") as f:
#         f.write(response.content)

#     return filename