import re
from datetime import timedelta
import replicate
import os
from moviepy.editor import VideoFileClip
import json




from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()


def convert_seconds_to_time(seconds):
    # Convert seconds to a string in the format 'HH:MM:SS'
    return str(timedelta(seconds=seconds))

def generate_srt_content(word_segments, max_chars=1):
    # Initialize some stuff
    srt_content = ""
    current_block = ""
    srt_segment_n = 1  # This is the subtitle number in the SRT file
    previous_end = 0  # Keep track of where the last word ended

    # Loop through each word to make sure it has a start and end time
    for i, word in enumerate(word_segments):
        if 'start' not in word or 'end' not in word:
            word['start'] = previous_end
            word['end'] = previous_end + 4  # If we don't know when it ends, just add 4 seconds

        # Update the end time for the next loop
        previous_end = word['end']

    # If the first word doesn't start at 0, add an empty subtitle at the beginning
    if word_segments[0]['start'] != 0:
        srt_content += f"1\n00:00:00,000 --> {convert_seconds_to_time(word_segments[0]['start'])}\n\n"
        srt_segment_n = 2  # Start the next subtitle at 2

    # Initialize the start and end times for the first block
    block_start_time = convert_seconds_to_time(word_segments[0]['start'])
    block_end_time = block_start_time

    # Loop through each word to build the SRT content
    for word in word_segments:
        next_word = word["word"] + " "

        # Check if we should start a new subtitle block
        if re.search(r'[.!?]\s*$', current_block) or len(current_block + next_word) > max_chars:
            srt_content += f"{srt_segment_n}\n{block_start_time} --> {block_end_time}\n{current_block.strip()}\n\n"
            srt_segment_n += 1
            block_start_time = block_end_time
            current_block = next_word
        else:
            current_block += next_word
            block_end_time = convert_seconds_to_time(word['end'])

    # Don't forget the last block!
    if current_block.strip():
        srt_content += f"{srt_segment_n}\n{block_start_time} --> {block_end_time}\n{current_block.strip()}\n\n"

    return srt_content



def save_srt_to_file(save_to, srt_content):
    # Create the full path for the new SRT file
    file_path = f"uploads/{save_to}"

    # If the file already exists, delete it
    if os.path.exists(file_path):
        os.remove(file_path)

    # Write the new SRT content to the file
    with open(file_path, 'a', encoding='utf-8') as srtFile:
        srtFile.write(srt_content)

    return os.path.basename(file_path)

# # Example usage
# word_segments = [
#     {"word": "Hello", "start": 0.5, "end": 1},
#     {"word": "world", "start": 4, "end": 5},
#     {"word": ".", "start": 5, "end": 20}
# ]

# srt_content = generate_srt_content(word_segments)
# print(srt_content)  # This will print the SRT content
# # save_srt_to_file("example", srt_content)  # Uncomment this to save the SRT content to a file





import random
import requests
import funcs_supabase
import base64
import funcs_deepgram

def get_word_segments (audio_file_binary, text_only=False):
    
    # whisperx large on replicate.com 
    # output = replicate.run("daanelson/whisperx:9aa6ecadd30610b81119fc1b6807302fd18ca6cbb39b3216f430dcf23618cedd", input={"audio": audio_file_binary, "align_output": True})
    # audio_base64 = base64.b64encode(audio_file_binary).decode("utf-8")

    # whisperx medium on replicate
    output = replicate.run("carnifexer/whisperx:1e0315854645f245d04ff09f5442778e97b8588243c7fe40c644806bde297e04",input={"audio": audio_file_binary, "align_output": True})
   

    # print(output)
    # print(type(output))
    output = json.loads(output)

    return output







def process_word_segments(word_segments, text_only=False):

    """

    makes  alist of words. 

    how the word_segments arrive. 
    {'start': 0.268, 'end': 5.454, 'text': ' How to turn your phone into a gold mine, the best kept secret in the world until now.', 'words': [{'word': 'How', 'start': 0.268, 'end': 0.368, 'score': 0.999}, {'word': 'to', 'start': 0.408, 'end': 0.468, 'score': 0.75}, {'word': 'turn', 'start': 0.509, 'end': 0.669, 'score': 0.802}, {'word': 'your', 'start': 0.689, 'end': 0.809, 'score': 0.876}, {'word': 'phone', 'start': 0.829, 'end': 1.049, 'score': 0.805}, {'word': 'into', 'start': 1.069, 'end': 1.269, 'score': 0.856}, {'word': 'a', 'start': 1.309, 'end': 1.349, 'score': 0.499}, {'word': 'gold', 'start': 1.389, 'end': 1.61, 'score': 0.732}, {'word': 'mine,', 'start': 1.63, 'end': 1.85, 'score': 0.994}, {'word': 'the', 'start': 1.91, 'end': 1.99, 'score': 0.993}, {'word': 'best', 'start': 2.05, 'end': 2.27, 'score': 0.836}, {'word': 'kept', 'start': 2.33, 'end': 2.531, 'score': 0.918}, {'word': 'secret', 'start': 2.571, 'end': 2.871, 'score': 0.888}, {'word': 'in', 'start': 2.891, 'end': 2.951, 'score': 0.766}, {'word': 'the', 'start': 2.991, 'end': 3.051, 'score': 1.0}, {'word': 'world', 'start': 3.111, 'end': 3.351, 'score': 0.703}, {'word': 'until', 'start': 3.732, 'end': 4.032, 'score': 0.782}, {'word': 'now.', 'start': 4.112, 'end': 4.333, 'score': 0.873}]}
    {'start': 5.454, 'end': 13.262, 'text': 'Nope, this is not just a dream but a reality for numerous individuals who are already raking in enormous piles of money.', 'words': [{'word': 'Nope,', 'start': 5.454, 'end': 5.694, 'score': 0.675}, {'word': 'this', 'start': 5.754, 'end': 5.894, 'score': 0.994}, {'word': 'is', 'start': 5.974, 'end': 6.054, 'score': 0.732}, {'word': 'not', 'start': 6.094, 'end': 6.255, 'score': 0.782}, {'word': 'just', 'start': 6.295, 'end': 6.495, 'score': 0.744}, {'word': 'a', 'start': 6.535, 'end': 6.555, 'score': 0.998}, {'word': 'dream', 'start': 6.615, 'end': 6.855, 'score': 0.866}, {'word': 'but', 'start': 6.895, 'end': 7.015, 'score': 0.67}, {'word': 'a', 'start': 7.055, 'end': 7.095, 'score': 0.499}, {'word': 'reality', 'start': 7.155, 'end': 7.756, 'score': 0.799}, {'word': 'for', 'start': 7.796, 'end': 7.936, 'score': 0.886}, {'word': 'numerous', 'start': 7.996, 'end': 8.337, 'score': 0.868}, {'word': 'individuals', 'start': 8.397, 'end': 8.997, 'score': 0.778}, {'word': 'who', 'start': 9.338, 'end': 9.458, 'score': 0.872}, {'word': 'are', 'start': 9.518, 'end': 9.618, 'score': 0.806}, {'word': 'already', 'start': 9.758, 'end': 10.139, 'score': 0.838}, {'word': 'raking', 'start': 10.239, 'end': 10.619, 'score': 0.935}, {'word': 'in', 'start': 10.699, 'end': 10.779, 'score': 0.878}, {'word': 'enormous', 'start': 10.859, 'end': 11.34, 'score': 0.828}, {'word': 'piles', 'start': 11.38, 'end': 11.7, 'score': 0.706}, {'word': 'of', 'start': 11.76, 'end': 11.82, 'score': 0.75}, {'word': 'money.', 'start': 11.88, 'end': 13.082, 'score': 0.752}]}

    
    how we want them:
    [{'word': 'How', 'start': 0.268, 'end': 0.368, 'score': 0.999}, 
    {'word': 'to', 'start': 0.408, 'end': 0.468, 'score': 0.75}, 
    {'word': 'turn', 'start': 0.509, 'end': 0.669, 'score': 0.802}]

    """

    sentances = []
    list_of_word_dicts = []

    for item_1 in word_segments:
        sentance = item_1["text"]
        sentance.strip()
        sentances.append(sentance)

        if text_only:
            continue

        item_words = item_1['words']
        # print(item_words)
        for inner_words in item_words:
            list_of_word_dicts.append(inner_words)

    if text_only:
       sentances = "\n".join(sentances)
       return sentances


    else:
        # loop through list_of_word_dicts, strip all the text. 

        for word_dict in list_of_word_dicts:
            word_dict["word"] = word_dict["word"].strip()
        return list_of_word_dicts




# audio_filepath = "/Users/georgebennett/Documents/GitHub/script_writer/uploads/testsquare.mp3"
# audio_file_binary = open(audio_filepath, "rb")
# word_segments = get_word_segments(audio_file_binary)
# for word_segment in word_segments:
#     print(word_segment)




def make_download_links(list_of_links):
    # contains dicts with name and content 
    # turn it into one file with all the contents

    if len(list_of_links) == 1:
        first_link = list_of_links[0].get("contents")
        link = "/download/" + first_link
        return link

    # return a string containing one link    

    else:
        # zip the links together
        # make a new file
        # return the new file
        return "not implemented yet"




def transcriber_run(my_dict):
    link = my_dict.get("link")  # Seems unused; consider removing
    files = my_dict.get("files")
    characters_per_line = int(my_dict.get("characters_per_line", 0))
    text_only = my_dict.get("text_only")
    output_prep = []

    for file in files:
        file_output_prep = process_file(file, characters_per_line, text_only)
        output_prep.append(file_output_prep)

    download_link = make_download_links(output_prep)
    return download_link



def check_file_type(file_path):
    audio_extensions = ['.mp3', '.wav', '.flac', '.aac']
    video_extensions = ['.mp4', '.mkv', '.flv', '.avi']
    
    _, file_extension = os.path.splitext(file_path)
    
    if file_extension.lower() in audio_extensions:
        return 'audio'
    elif file_extension.lower() in video_extensions:
        return 'video'
    else:
        return 'unknown'




def process_file(file, characters_per_line, text_only):
    file_output_prep = {}
    filepath = f"uploads/{file['name']}"

    check = check_file_type(filepath)
    if check == 'video':
        filepath = convert_video_to_mp3(filepath)
    else: 
        filepath = filepath

    with open(filepath, "rb") as audio_file_binary:
        
        if text_only:
            text_transcription = get_word_segments(audio_file_binary, text_only=True)
            text_transcription = process_word_segments(text_transcription, text_only=True)

            final_filename = f"{file['name'].split('.')[0]}.txt"
            txt_filepath = save_srt_to_file(final_filename, text_transcription)
            
            return {
                "filename": file["name"],
                "contents": txt_filepath
            }
        
                
        word_segments = get_word_segments(audio_file_binary)
        text_transcription = process_word_segments(word_segments)
        srt_content = generate_srt_content(word_segments, max_chars=characters_per_line)
        final_filename = f"{file['name'].split('.')[0]}.srt"
        srt_filepath = save_srt_to_file(final_filename, srt_content)

        return {
            "filename": file["name"],
            "contents": srt_filepath
        }




def convert_video_to_mp3(input_video_path):
    # Create uploads folder if it doesn't exist
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    # Generate output file path
    output_audio_path = os.path.join('uploads', os.path.splitext(os.path.basename(input_video_path))[0] + '.mp3')
    
    # Load video file
    video = VideoFileClip(input_video_path)

    # Extract audio from the video
    audio = video.audio

    # Save audio to MP3 format
    audio.write_audiofile(output_audio_path)

    # Close the clips
    video.close()
    audio.close()
    
    return output_audio_path

# Example usage
# input_video_path = 'uploads/Cas1.mp4'
# output_audio_path = convert_video_to_mp3(input_video_path)
# print(f"MP3 file has been saved at: {output_audio_path}")







def fix_missing_time_stamps(word_list):
    """
    sometimes you get this situation:
    {'word': 'money.', 'start': 11.88, 'end': 13.082, 'score': 0.752}
    {'word': '72%'}
    {'word': 'of', 'start': 13.622, 'end': 13.682, 'score': 0.753}

    """

    try:
        fixed_list = []
        for i, word_dict in enumerate(word_list):
            new_dict = word_dict.copy()
            
            # If 'start' is missing in the current word dict
            if 'start' not in new_dict:
                # If it's the first element, set start to 0
                if i == 0:
                    new_dict['start'] = 0
                # Otherwise, set start to end of previous word
                else:
                    new_dict['start'] = fixed_list[-1].get('end', 0)
            
            # If 'end' is missing in the current word dict
            if 'end' not in new_dict:
                # If it's the last element, set end to start + 0.5 (or any other default duration)
                if i == len(word_list) - 1:
                    new_dict['end'] = new_dict['start'] + 0.5
                # Otherwise, set end to start of next word
                else:
                    new_dict['end'] = word_list[i + 1].get('start', new_dict['start'] + 0.5)

            fixed_list.append(new_dict)

        return fixed_list
    except Exception as e:
        print(f"An error occurred: {e}")
        return None



def generate_subtitle_blocks(words, char_limit):
    """
    makes blocks like this 
    {'text': 'How to turn your phone into a gold', 'start': None, 'end': 1.61}
    {'text': 'mine,', 'start': 1.63, 'end': 1.85}
    {'text': 'the best kept secret in the world until', 'start': None, 'end': 4.032}
    {'text': 'now.', 'start': 4.112, 'end': 4.333}
    {'text': 'Nope,', 'start': None, 'end': 5.694}
    """
    

    # Initialize variables
    blocks = []
    current_block = {"text": "", "start": None, "end": None}

    for word_info in words:
        word = word_info['word']
        start_time = word_info['start']
        end_time = word_info['end']

        # Check if the word ends with punctuation
        ends_in_punctuation = word[-1] in [".", ",", "!", "?", ";"]

        # New block length if this word is added
        new_block_length = len(current_block["text"]) + len(word) + (1 if current_block["text"] else 0)

        # Initialize start time if starting a new block
        if current_block["start"] is None:
            current_block["start"] = start_time

        # Append this word to the current block first, before checking for block completion
        if current_block["text"]:
            current_block["text"] += " "
        current_block["text"] += word
        current_block["end"] = end_time

        if new_block_length > char_limit or ends_in_punctuation:
            # Finalize and save the current block
            blocks.append(current_block.copy())

            # Start a new block
            current_block = {"text": "", "start": None, "end": None}

    # Add the last block if it's not empty
    if current_block["text"]:
        blocks.append(current_block)

    # Display the blocks
    for block in blocks:
        print(block)

    return blocks





def process_blocks(block_list):
    # Initialize an empty list to hold the processed blocks
    processed_blocks = []
    
    # Add an empty block that starts at 0 and ends at the start of the original first block
    if block_list:
        processed_blocks.append({'text': '', 'start': 0, 'end': block_list[0]['start']})
    
    # Loop through the list to process each block
    for i, block in enumerate(block_list):
        # Remove the block if it's the first one and the text is empty
        if i == 0 and not block['text'].strip():
            continue
        
        # Make the end time of a block the start time of the next block
        if i < len(block_list) - 1:
            block['end'] = block_list[i + 1]['start']
        
        processed_blocks.append(block)
    
    return processed_blocks


# processed_blocks = process_blocks(subtitle_blocks)
# print(processed_blocks)

def seconds_to_srt_time(seconds):
    """Convert seconds to SRT time format (HH:MM:SS,MMM)"""
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    milliseconds = int((seconds % 1) * 1000)
    seconds = int(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"



def blocks_to_srt(processed_blocks):
    """Convert list of processed blocks to SRT format"""
    srt_content = ""
    for i, block in enumerate(processed_blocks, 1):
        start_time = seconds_to_srt_time(block['start'])
        end_time = seconds_to_srt_time(block['end'])
        text = block['text']
        
        srt_content += f"{i}\n"
        srt_content += f"{start_time} --> {end_time}\n"
        srt_content += f"{text}\n\n"
    
    return srt_content


# srt_content = blocks_to_srt(processed_blocks)
# print(srt_content)

# # To write the content to an SRT file
# with open("output.srt", "w") as f:
#     f.write(srt_content)







import media
def get_subs_for_project(project_id, characters=10):
    """Fetches speech audio URL from the database and gets its subtitles."""
    # Fetch speech audio URL from the database
    speech_audio_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)
    speech_audio_url = speech_audio_data[0]['speech_audio']
    print(f"Speech audio URL: {speech_audio_url}")


    # Download the audio file into memory
    response = requests.get(speech_audio_url)

    rand_no = random.randint(0, 1000000000000000)

    filename = f"uploads/{rand_no}.mp3"

    # save to disk 
    with open(filename, "wb") as f:
        f.write(response.content)


    with open(filename, "rb") as audio_file_binary:
        print("about to get word segments")
        word_segments = get_word_segments(audio_file_binary)
        word_list = process_word_segments(word_segments)
        word_list = fix_missing_time_stamps(word_list)
        blocks_of_words = generate_subtitle_blocks(word_list, characters)
        blocks_of_words = process_blocks(blocks_of_words)


        # for item in blocks_of_words:
        #     print(item)
        #     print("-----")

        srt_content = blocks_to_srt(blocks_of_words)

        srt_filename = f"uploads/{rand_no}.srt"
        with open(srt_filename, "w") as f:
            f.write(srt_content)

        # open and get binary 
        with open(srt_filename, "rb") as f:
            srt_binary = f.read()

        url = media.upload_get_url("media", srt_filename, srt_binary)

        print(url)
        new_data = {"subtitles_file": url}
        update_project = funcs_supabase.update_data("video_creator_projects", project_id, new_data)
        print(update_project)



        remove = os.remove(srt_filename)
        remove = os.remove(filename)

        return url


# output = get_subs_for_project(17, characters=10)

import funcs_supabase
import media
import requests
import random
import actions



def modify_words_list_for_scenes(word_list, project_id):
    active_scenes = actions.get_active_scenes(project_id)

    scenes_words_count_list = []

    for scene in active_scenes:
        scene_text = scene.get("scene_text")
        no_words_in_scene = len(scene_text.split())
        scenes_words_count_list.append(no_words_in_scene)

    total_words_in_project = sum(scenes_words_count_list)

    words_list_length = len(word_list)

    if total_words_in_project == words_list_length:
        return word_list


def save_word_list_to_db(project_id):

    speech_audio_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)
    speech_audio_url = speech_audio_data[0]['speech_audio']
    print(f"Speech audio URL: {speech_audio_url}")

    # # Download the audio file into memory
    response = requests.get(speech_audio_url)
    rand_no = random.randint(0, 1000000000000000)
 
    filename = f"uploads/{rand_no}.mp3"
    # save to disk 
    with open(filename, "wb") as f:
        f.write(response.content)


    with open(filename, "rb") as audio_file_binary:
        print("get_word_segments")
        word_segments = get_word_segments(audio_file_binary)
        print(word_segments)
        print("process_word_segments")
        word_list = process_word_segments(word_segments)
        print("fix_missing_time_stamps")
        word_list = fix_missing_time_stamps(word_list)
        # print("modify_words_list_for_scenes")
        # word_list = modify_words_list_for_scenes(word_list, project_id)
        print(word_list)


    print("update_data")
    update_db = funcs_supabase.update_data("video_creator_projects", project_id, {"words_list": word_list})
    # print(update_db)

    remove = os.remove(filename)

    return update_db

# save_word_list_to_db(28)


def save_word_list_to_db_2(project_id):

    speech_audio_data = funcs_supabase.select_data("video_creator_projects", "id", project_id)
    speech_audio_url = speech_audio_data[0]['speech_audio']
    print(f"Speech audio URL: {speech_audio_url}")



    word_list = funcs_deepgram.get_words(speech_audio_url)
    print(word_list)
    # word_list = process_word_segments(word_segments)
    word_list = fix_missing_time_stamps(word_list)
    print(word_list)
    update_db = funcs_supabase.update_data("video_creator_projects", project_id, {"words_list": word_list})

    return update_db