import json
import subprocess
import os
from moviepy.editor import VideoFileClip, AudioFileClip
import burn_subs_2

def get_default_config():
    # Returns a dictionary with default settings for the slideshow.
    return {
        "output_width": 1080,
        "output_height": 1080,
        "fps": 60,
        "zoom_rate": 0.1,
        "zoom_direction_x": "random",
        "zoom_direction_y": "random",
        "zoom_direction_z": "random",
        "scale_mode": "auto",
        "overwrite": True,
    }

def update_config(default, new):
    # Updates the default configuration with new settings.
    for key in new:
        if key in default:
            default[key] = new[key]
    return default



def prepare_slides(slideshow_data, transitions=False):
    # Prepares slide data for the slideshow.
    slides = []
    for i, scene in enumerate(slideshow_data["scenes_list"]):
        print(scene)

        rel_filepath = scene["downloaded_filename"]
        absolute_path = os.path.abspath(rel_filepath)

        if transitions:

            # Check if the file is a video or image
            if rel_filepath.endswith('.mp4'):  # If it's a video
                my_scene = {
                    "file": absolute_path,
                    "slide_duration": scene["length"],  # Use the duration as is
                    "transition": "none"  # No transition for videos
                }
            else:  # If it's an image
                # Determine the last slide to set fade_duration and transition differently
                is_last_slide = i == len(slideshow_data["scenes_list"]) - 1

                my_scene = {
                    "file": absolute_path,
                    "slide_duration": scene["length"] + (0 if is_last_slide else 1),  # Add 1 to all but last slide
                    "fade_duration": 0 if is_last_slide else 1,  # Set to 0 for last slide, 1 for others
                    "transition": "none" if is_last_slide else "fade"  # "none" for last slide, "fade" for others
                }
                
        else:
            my_scene = {
                "file": absolute_path,
                "slide_duration": scene["length"],  # Use the duration as is
                "transition": "none",  # No transition for videos
                "fade_duration": 0
            }

        slides.append(my_scene)
    return slides




def save_slideshow_config_as_json(updated_config, folder_path):
    # Saves the updated configuration as a JSON file.
    file_name = 'slideshow_data.json'
    json_file_path = os.path.join(folder_path, file_name)
    with open(json_file_path, 'w') as json_file:
        json.dump(updated_config, json_file, indent=4)
    return json_file_path


def run_slideshow_script(json_file_path, output_path):
    slideshow_app_path = "/Users/georgebennett/Downloads/kburns-slideshow-master/kbvs-cli.py"

    json_file_path_abs = os.path.abspath(json_file_path)
    output_path_abs = os.path.abspath(output_path)

    command = [
        "python",
        slideshow_app_path,  # Replace with the actual path to the script
        output_path_abs,
        "-f",
        json_file_path_abs
    ]
    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode == 0:
        print("Slideshow script executed successfully.")
        return output_path_abs
    else:
        print(f"Error in executing slideshow script: {result.stderr}")
        return None


#     slideshow_filepath =  f"{folder_path_abs}/slideshow16.mp4"

# command = [
#     "python", 
#     "kbvs-cli.py",
#     slideshow_filepath,
#     "-f", 
#     json_file_path
# ]

# # Execute the command
# print(command)
# subprocess.run(command)




# def finalize_video_with_audio_subs(video_path, project_folder, speech_clip, words_list):
#     # Adds audio and subtitles to the video.
#     clip = VideoFileClip(video_path)
#     with_subs_clip = burn_subs_2.get_subs_clip(words_list, clip)
#     with_audio_clip = with_subs_clip.set_audio(speech_clip)
#     final_video_path = os.path.join(project_folder, "final_vid.mp4")
#     with_audio_clip.write_videofile(final_video_path, audio_codec='aac', fps=60)
#     return final_video_path
