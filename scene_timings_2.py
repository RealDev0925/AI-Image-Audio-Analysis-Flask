import os
from pydub import AudioSegment
import requests
import funcs_supabase
import actions

class SceneTimings:
    def __init__(self, project_id):
        self.project_id = project_id
        self.active_scenes = actions.get_active_scenes(self.project_id)
        self.scene_text_list = [scene.get("scene_text") for scene in self.active_scenes]
        self.project_data = funcs_supabase.select_data("video_creator_projects", "id", self.project_id)[0]
        self.words_list = self.project_data.get("words_list")

    @staticmethod
    def clean_string(text):
        text = text.lower()
        allowed_characters = "abcdefghijklmnopqrstuvwxyz0123456789 "
        return "".join(char for char in text if char in allowed_characters)

    def process_scene(self, scene_text, word_number):
        scene_text = self.clean_string(scene_text)
        scene_words = scene_text.split()
        print(f"Scene words: {scene_words}")

        scene_fails = 0
        for scene_word in scene_words:
            word_from_word_list = self.words_list[word_number].get("word")
            word_from_word_list = self.clean_string(word_from_word_list)

            if scene_word != word_from_word_list:
                print(f"No match {scene_word} {word_from_word_list}")
                scene_fails += 1

            word_number += 1

        scene_word_count = len(scene_words)
        return word_number, scene_fails, scene_word_count

    def calculate_timings(self):
        scene_timings = []
        word_number = 0

        for scene_no, scene_text in enumerate(self.scene_text_list):
            print(f"Processing scene number: {scene_no}")

            word_number, scene_fails, scene_word_count = self.process_scene(scene_text, word_number)
            print(f"Scene complete - fails: {scene_fails} / {scene_word_count}")

            if scene_fails < 6:
                first_word = self.words_list[word_number - scene_word_count]
                last_word = self.words_list[word_number - 1]

                timing_info = {
                    "end": last_word["end"],
                    "start": first_word["start"],
                    "length": round(last_word["end"] - first_word["start"], 3)
                }
            else:
                print("Scene failed")
                timing_info = {"end": None, "start": None, "length": None}

            scene_timings.append(timing_info)

        print(scene_timings)
        return scene_timings



    def process_scene_timings(self, scene_timings_raw):
        audio_duration = self.get_audio_duration()

        scene_timings_processed = []
        for i, scene in enumerate(scene_timings_raw):
            if i == 0:
                scene["start"] = 0
            else:
                scene["start"] = scene_timings_raw[i-1]["end"]
            
            if i < len(scene_timings_raw) - 1:
                scene["end"] = scene_timings_raw[i+1]["start"]
            else:
                scene["end"] = audio_duration

            scene["start"] = round(scene["start"], 3)
            scene["end"] = round(scene["end"], 3)
            scene["length"] = round(scene["end"] - scene["start"], 3)

            scene_timings_processed.append(scene)

        return scene_timings_processed

    def update_timings_database(self, processed_scene_timings):
        if len(self.active_scenes) != len(processed_scene_timings):
            print("Scene count mismatch between database and processed timings.")
            return

        responses = []
        for i, scene in enumerate(processed_scene_timings):
            data_to_update = {
                "length": scene["length"],
                "start": scene["start"],
                "end": scene["end"]
            }

            scene_id = self.active_scenes[i]["id"]
            print(f"Updating scene {scene_id} with {data_to_update}")
            update_response = funcs_supabase.update_data("scenes", scene_id, {"timings": data_to_update})
            print(update_response)
            print("\n")
            responses.append(update_response)

        return responses

    def get_audio_duration(self):
        # Assume funcs_supabase.select_data() returns the necessary data
        audio_file_url = funcs_supabase.select_data("video_creator_projects", "id", self.project_id)[0].get("speech_audio")

        # Specify the folder where the audio file will be downloaded
        download_folder = "downloaded_audio/"
        os.makedirs(download_folder, exist_ok=True)

        # Extract the filename and create a path for the downloaded file
        filename = os.path.basename(audio_file_url)
        file_path = os.path.join(download_folder, filename)
        duration_seconds=0
        # Download the audio file
        response = requests.get(audio_file_url)
        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                file.write(response.content)

        else:
            raise Exception("Failed to download the audio file")
        
        try:
            # with Image.open(filepath) as im:
            # x, y = im.size
            # Load the audio file and get its duration
            audio = AudioSegment.from_file(file_path)
            print("audio-----:::",audio)
            duration_seconds = len(audio) / 1000  # pydub calculates in millisec
            print("duaration_seconds",duration_seconds)
        except:
            print("audio:::::::::::::::::")
        finally:
            # Delete the audio file after processing
            if os.path.exists(file_path):
               file.close()
               print("file path is ::::::",file_path)
            #    os.close()
            #    os.remove(file_path)

        return duration_seconds

# #

def project_scene_timings(project_id):
    scene_timing_instance = SceneTimings(project_id)
    raw_timings = scene_timing_instance.calculate_timings()  # Assuming calculate_timings is implemented as in previous examples
    processed_timings = scene_timing_instance.process_scene_timings(raw_timings)
    update_responses = scene_timing_instance.update_timings_database(processed_timings)
    return processed_timings
