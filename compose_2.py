#%%
import random 
import os
from datetime import datetime

import funcs_supabase
import actions
import file_management
import video_processing
import pexels_2

from urllib.parse import urlparse, unquote
import requests

from moviepy.editor import VideoFileClip, concatenate_videoclips, ImageClip  
import moviepy.editor as mpy
from moviepy.video.fx.all import crop
from moviepy.editor import AudioFileClip
from moviepy.editor import VideoFileClip
import burn_subs    
import scene_timings
import media
from PIL import Image  # Make sure to import PIL at the top of your script
import numpy as np
import make_slideshow

import scene_timings_2
import burn_subs_2


class ComposeVideo:
    def __init__(self, project_id):
        self.project_id = project_id

        self.project_data = funcs_supabase.select_data("video_creator_projects", "id", self.project_id)[0]
        self.scenes_data = actions.get_active_scenes(self.project_id)
        
        
        self.video_clips_list = []
        self.speech_clip = None  # Class variable for storing the speech audio clip
        
        self.slideshow_data = {}
        
        
        
        now = datetime.now()
        formatted_timestamp = now.strftime("%Y%m%d%H%M%S")
        self.project_download_folder = f"composed_videos/{self.project_id}_{formatted_timestamp}"
        # Creating the directory if it doesn't exist
        if not os.path.exists(self.project_download_folder):
            os.makedirs(self.project_download_folder)




    def update_project_data(self, key, value):
        self.project_data[key] = value

    def get_project_data(self, key):
        return self.project_data.get(key, None)


    def add_scene(self, scene_data):
        self.scenes_data.append(scene_data)

    def get_all_scenes(self):
        return self.scenes_data

    def get_scene(self, scene_id):
        for scene in self.scenes_data:
            if scene['id'] == scene_id:
                return scene
        return None

    def update_scene(self, scene_id, key, value):
        scene = self.get_scene(scene_id)
        if scene is not None:
            scene[key] = value
        else:
            print(f"No scene found with ID {scene_id}")

    def get_scene_data(self, scene_id, key):
        scene = self.get_scene(scene_id)
        if scene is not None:
            return scene.get(key, None)
        else:
            print(f"No scene found with ID {scene_id}")
            return None


    def download_all_files_for_project(self):
        download_tasks = {}
        for scene in self.scenes_data:
            scene_id = scene['id']
            media_id = scene.get('final_clip')

            if media_id:
                # Fetch media information from a database
                media_info = funcs_supabase.select_data("media", "id", media_id)[0]
                url = media_info.get('url')
                media_type = media_info.get('type')
                url_remote = media_info.get('url_remote')

                if not url and url_remote:
                    url = url_remote

                if not url:
                    print(f"No URL found for media ID {media_id}, skipping...")
                    continue
            else:
                url = pexels_2.random_image()
                media_type = 'image'

            url_extension = file_management.get_url_file_extension(url)
            if not url_extension:
                url_extension = 'png' if media_type == 'image' else 'mp4'

            filename = f"{self.project_download_folder}/{media_id}.{url_extension}" if media_id else f"{self.project_download_folder}/{scene_id}_random.{url_extension}"

            download_tasks[scene_id] = (url, filename)

        # Downloading files concurrently
        downloaded_files = file_management.download_files([task[0] for task in download_tasks.values()], [task[1] for task in download_tasks.values()])

        # Updating each scene with its downloaded filename
        for scene_id, filename in zip(download_tasks, downloaded_files):
            print(f"Downloaded: {filename}")
            self.update_scene(scene_id, 'downloaded_filename', filename)

        return [task[1] for task in download_tasks.values()]


    def get_clips_for_project(self):
        self.video_clips_list = []  # Reset the list each time this method is called
        for scene in self.scenes_data:
            scene_id = scene['id']
            timings = scene['timings']
            length = timings['length']
            print("length:::::::",length)
            downloaded_filename = scene['downloaded_filename']

            if downloaded_filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                clip = VideoFileClip(downloaded_filename)
                clip.fps = clip.reader.fps  # Set the fps from the clip's reader

            elif downloaded_filename.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                clip = ImageClip(downloaded_filename, duration=length)
            else:
                print(f"Unsupported format: {downloaded_filename}")
                continue  # Skip this scene if the format is unsupported

            # Assuming trim_clip and crop_clip are predefined functions
            trimmed_clip = video_processing.trim_clip(clip, start_trim=0, end_trim=length)

            height = self.get_project_data('height') or 1080
            width = self.get_project_data('width') or 1080  # Adjusted to a more common width for videos

            resized_clip = video_processing.crop_clip(trimmed_clip, width=1080, height=1080)

            self.video_clips_list.append(resized_clip)

        return self.video_clips_list
    





    def process_and_overwrite_clips(self):

        # Writes the clips to the hard drive replacing the original files 

        # Process the clips
        processed_clips = self.get_clips_for_project()

        # Overwriting the original files with the processed clips
        for idx, scene in enumerate(self.scenes_data):
            scene_id = scene['id']
            downloaded_filename = scene['downloaded_filename']
            file_extension = downloaded_filename.split('.')[-1].lower()

            if processed_clips[idx]:
                processed_clip = processed_clips[idx]

                # Append '_2' before the file extension
                name_part, extension = os.path.splitext(downloaded_filename)
                new_filename = f"{name_part}_2{extension}"

                # For video files
                if file_extension in ['mp4', 'avi', 'mov', 'mkv']:
                    processed_clip.write_videofile(new_filename, codec="libx264", audio_codec='aac')
                
                # For image files
                elif file_extension in ['jpg', 'jpeg', 'png', 'bmp']:
                    # Convert the numpy array to a PIL Image object and save it
                    img = Image.fromarray(np.uint8(processed_clip.img))
                    img.save(new_filename)

                # Updating the scene with the new file information
                self.update_scene(scene_id, 'downloaded_filename', new_filename)
                print(f"Processed and overwritten: {new_filename}")


    def slideshow_prep(self):
        self.slideshow_data = {}  # Reset
        height = self.get_project_data('height') or 1080
        width = self.get_project_data('width') or 1080  
        self.slideshow_data['height'] = height
        self.slideshow_data['width'] = width
        self.slideshow_data['scenes_list'] = []

        for scene in self.scenes_data:
            scene_id = scene['id']
            timings = scene['timings']
            length = timings['length']
            downloaded_filename = scene['downloaded_filename']

            scene_data = {"scene_id": scene_id, "length": length, "downloaded_filename": downloaded_filename}
            self.slideshow_data['scenes_list'].append(scene_data)

        return self.slideshow_data
        





    def download_and_create_speech_clip(self):
        speech_audio = self.get_project_data('speech_audio')
        if not speech_audio:
            print("No speech audio URL found.")
            return

        # Assuming download_file_from_url is a predefined function
        speech_filepath = f"{self.project_download_folder}/speech.mp3"
        file_management.download_file_from_url(speech_audio, speech_filepath)

        # Assuming AudioFileClip is a predefined class/method
        self.speech_clip = AudioFileClip(speech_filepath)
        print(f"Speech clip duration: {self.speech_clip.duration}")
    
    
    def create_slideshow(self):
        slideshow_data = self.slideshow_prep()

        # Use functions from make_slideshow.py
        default_config = make_slideshow.get_default_config()
        updated_config = make_slideshow.update_config(default_config, slideshow_data)
        updated_config["slides"] = make_slideshow.prepare_slides(slideshow_data)

        # Save slideshow data as JSON
        json_file_path = make_slideshow.save_slideshow_config_as_json(updated_config, self.project_download_folder)

        # Run slideshow creation script
        slideshow_filepath = f"{self.project_download_folder}/slideshow.mp4"
        make_slideshow.run_slideshow_script(json_file_path, slideshow_filepath)

        self.update_project_data('slideshow_filepath', slideshow_filepath)

        return slideshow_filepath


        # # Add audio and subtitles to the slideshow
        # speech_clip = self.speech_clip  # Assuming this is set up earlier in the class
        # words_list = self.get_project_data('words_list')
        # make_slideshow.finalize_video_with_audio_subs(slideshow_filepath, self.project_download_folder, speech_clip, words_list)




def upload_final_video(project_id, file_input):

    with open(file_input, "rb") as f:
        file_content = f.read()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    upload_filepath = f"final_media/{project_id}/{timestamp}.mp4"

    upload= funcs_supabase.upload_file("media", upload_filepath, file_content)

    final_link = f"https://fpyltvtkpkrkzortucoa.supabase.co/storage/v1/object/public/media/{upload_filepath}"

    funcs_supabase.update_data("video_creator_projects", project_id, {"final_media": final_link})

    print(final_link)
    return final_link



# def process (project_id):
#     project = ComposeVideo(project_id)
    
    

#     # scene_timing_instance = scene_timings_2.SceneTimings(project_id)
#     # # Process and update scene timings
#     # raw_timings = scene_timing_instance.calculate_timings()  # Assuming calculate_timings is implemented as in previous examples
#     # processed_timings = scene_timing_instance.process_scene_timings(raw_timings)
#     # update_responses = scene_timing_instance.update_timings_database(processed_timings)

#     scene_timings= scene_timings_2.project_scene_timings(project_id)


#     project.download_all_files_for_project()
#     # project.get_clips_for_project()
#     slidewhow_dict = project.slideshow_prep()
#     print(slidewhow_dict)


#     processed_clips = project.video_clips_list
#     min_fps = 24
#     for clip in processed_clips:
#         clip.audio = None


#     project.download_and_create_speech_clip()
#     speech_clip = project.speech_clip

#     final_clip_no_audio = concatenate_videoclips(processed_clips)
#     print(f"Final clip duration: {final_clip_no_audio.duration}")

#     # get subs clip
#     words_list = project.get_project_data('words_list')
#     with_subs_clip = burn_subs_2.get_subs_clip(words_list,final_clip_no_audio)
#     with_audio_clip = with_subs_clip.set_audio(speech_clip)
#     with_audio_clip.write_videofile("final_video_audio_subs.mp4", audio_codec='aac', fps=min_fps)

#     link = upload_final_video(project_id, "final_video_audio_subs.mp4")
#     return link

# # process(40) 


#%%

def process (project_id):
    # project_id = 40
    scene_timings= scene_timings_2.project_scene_timings(project_id)
    print("printscene_timings:::", scene_timings)

    project = ComposeVideo(project_id)
    project.download_all_files_for_project()
    project.process_and_overwrite_clips()
    project.get_clips_for_project()
    project.download_and_create_speech_clip()


    project.create_slideshow()

    slideshow_filepath = project.get_project_data('slideshow_filepath')
    print(slideshow_filepath)

    # burn subs

    slide_clip = VideoFileClip(slideshow_filepath)
    speech_clip = project.speech_clip

    words_list = project.get_project_data('words_list')
    clip_subs = burn_subs_2.get_subs_clip(words_list,slide_clip)
    clip_subs_audio = clip_subs.set_audio(speech_clip)

    downloads_folder = project.project_download_folder
    final_video_path = f"{downloads_folder}/final_video.mp4"
    clip_subs_audio.write_videofile(final_video_path, audio_codec='aac', fps=60)

    link = upload_final_video(project_id, final_video_path)
    return link



# %%
