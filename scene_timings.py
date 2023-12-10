import actions
import funcs_supabase

def process_project_scenes(project_id):

    scene_timings_raw = []

    active_scenes = actions.get_active_scenes(project_id)

    # Check if active_scenes is None or empty before proceeding
    if not active_scenes:
        return "No active scenes available for this project."

    total_words_in_project = 0

    for scene_counter, scene in enumerate(active_scenes):
        scene_text = scene.get("scene_text", "")
        scene_id = scene.get("id")

        # If scene_text or scene_id is missing, skip to next iteration
        if not scene_text or scene_id is None:
            continue

        # print(scene_text)
        words_in_scene = scene_text.split()
        no_words_in_scene = len(words_in_scene)

        # print(f"scene has {no_words_in_scene} words")
        # print(f"the first word is {words_in_scene[0]}")
        # print(f"the last word is {words_in_scene[-1]}")

        total_words_in_project += no_words_in_scene
        first_word_location = total_words_in_project - no_words_in_scene
        last_word_location = total_words_in_project - 1

        # print(f"first word location: {first_word_location}")
        # print(f"last word location: {last_word_location}")

        words_list = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0].get("words_list")

        try:
            first_word_from_words_list = words_list[first_word_location]
            last_word_from_words_list = words_list[last_word_location]
        except IndexError:
            # Handle this error if word locations are out of bounds
            continue

        # print(f"first word from words list: {first_word_from_words_list}")
        # print(f"last word from words list: {last_word_from_words_list}")

        if scene_counter == 0:
            words_list[first_word_location]["start"] = 0

        scene_length = last_word_from_words_list["end"] - first_word_from_words_list["end"]
        scene_length = round(scene_length, 3)

        data_to_update = {
            "length": scene_length,
            "start": first_word_from_words_list["start"],
            "end": last_word_from_words_list["end"]
        }

        # funcs_supabase.update_data("scenes", scene_id, {"timings": data_to_update})
        # print(f"scene length: {scene_length}")
        # print("\n")

        scene_timings_raw.append(data_to_update)

    return scene_timings_raw
    
    
import os
from pydub import AudioSegment
import requests

def get_audio_duration(project_id):
    # Assume funcs_supabase.select_data() returns the necessary data
    audio_file_url = funcs_supabase.select_data("video_creator_projects", "id", project_id)[0].get("speech_audio")

    # Specify the folder where the audio file will be downloaded
    download_folder = "downloaded_audio"
    os.makedirs(download_folder, exist_ok=True)

    # Extract the filename and create a path for the downloaded file
    filename = os.path.basename(audio_file_url)
    file_path = os.path.join(download_folder, filename)

    # Download the audio file
    response = requests.get(audio_file_url)
    if response.status_code == 200:
        with open(file_path, 'wb') as file:
            file.write(response.content)
    else:
        raise Exception("Failed to download the audio file")

    try:
        # Load the audio file and get its duration
        audio = AudioSegment.from_file(file_path)
        duration_seconds = len(audio) / 1000  # pydub calculates in millisec
    finally:
        # Delete the audio file after processing
        if os.path.exists(file_path):
            os.remove(file_path)

    return duration_seconds


# # Usage example
# duration = get_audio_duration(27)
# print(f"The audio duration is {duration} seconds.")


def process_scene_timings(scene_timings_raw, project_id):
    audio_duration = get_audio_duration(project_id)
    
    scene_timings_processed = []
    for i, scene in enumerate(scene_timings_raw):

        # print(scene)

        # first scene starts at 0
        if i == 0:
            scene["start"] = 0
       
        # if not the first scene, the start time is the end time of the previous scene
        else:
            scene["start"] = scene_timings_raw[i-1]["end"]
        
        # if not the last scene, the end time is the start time of the next scene
        if i < len(scene_timings_raw) - 1:
            scene["end"] = scene_timings_raw[i+1]["start"]


        # if the last scene, end at the end of the audio
        else:
            scene["end"] = audio_duration

        
        
        scene["start"] = round(scene["start"], 3)
        scene["end"] = round(scene["end"], 3)

        # recalculate the length 
        scene["length"] = scene["end"] - scene["start"]

        # round the length to 3 decimal places
        scene["length"] = round(scene["length"], 3)


        scene_timings_processed.append(scene)

    return scene_timings_processed


def update_timings_database(processed_scene_timings, project_id):
    resp = []
    active_scenes = actions.get_active_scenes(project_id)

    if len(active_scenes) != len(processed_scene_timings):
        print("The number of scenes in the database and the number of scenes in the processed scene timings do not match.")
        return
    
    for i, scene in enumerate(processed_scene_timings):

        data_to_update = {
        "length": scene["length"],
        "start": scene["start"],
        "end": scene["end"]
        }

        scene_id = active_scenes[i]["id"]
        print(f"updating scene {scene_id} with {data_to_update}")
        update = funcs_supabase.update_data("scenes", scene_id, {"timings": data_to_update})
        print(update)
        print("\n")
        resp.append(update)

    return resp



def process(project_id):
    scene_timings_raw = process_project_scenes(project_id)
    print(scene_timings_raw)
    scene_timings_processed = process_scene_timings(scene_timings_raw, project_id)
    print(scene_timings_processed)
    update = update_timings_database(scene_timings_processed, project_id)
    print(update)
    return update

# process(39)

