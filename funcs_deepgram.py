import requests
import os

def get_words(p_url):
    # Use this to get subtitles in English
    # url = "https://api.deepgram.com/v1/listen?model=whisper-large&language=en&punctuate=true&diarize=true&smart_format=true"
    # url = "https://api.deepgram.com/v1/listen?smart_format=true&punctuate=true&utterances=true&language=en&model=nova-2"    
    url = "https://api.deepgram.com/v1/listen?smart_format=true&punctuate=true&utterances=true&language=en&model=whisper-large"    


    payload = {
        "url": p_url
    }

    # Get the Deepgram secret from the environment variable
    deepgram_secret = "0bdf18a5b86bb1e6f052fd6e4e2de7f7c3bf633c"

    headers = {
        "Authorization": f"Token {deepgram_secret}",
        "Content-Type": "application/json"
    }

    response = requests.request("POST", url, headers=headers, json=payload)

    output = response.json()
    print(output)
    print("/n/n" )
    words = output['results']['channels'][0]['alternatives'][0]['words']
    for word in words:
        print(word['word'])

    return words

# my_file = "https://fpyltvtkpkrkzortucoa.supabase.co/storage/v1/object/public/media/726903182913934.mp3"
# output = get_words(my_file)
# print(output)
