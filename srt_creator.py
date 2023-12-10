import re
import os
from datetime import timedelta

def convert_seconds_to_time(seconds):
    """
    This helper function converts seconds to time in 'HH:MM:SS,mmm' format which is used in .srt files.

    Parameters:
    seconds (float): The time in seconds.

    Returns:
    str: The time in 'HH:MM:SS,mmm' format.
    """
    return str(timedelta(seconds=seconds))




def create_srt_file(save_to, result_aligned, max_chars):
    """
    This function creates a subtitle (srt) file from an aligned transcript. 
    Each subtitle block is as long as possible without exceeding a maximum number of characters, 
    splitting a word, or crossing a sentence boundary.

    Parameters:
    save_to (str): The path where the srt file will be saved.
    result_aligned (dict): The aligned transcript result.
    max_chars (int): The maximum number of characters per subtitle block.

    Returns:
    None
    """
    # Extract the word segments from the result
    word_segments = result_aligned["word_segments"]

    # Initialize previous_end
    previous_end = 0

    # Add start and end times if they are not present
    for i in range(len(word_segments)):
        if 'start' not in word_segments[i] and 'end' not in word_segments[i]:
            if i == len(word_segments) - 1:
                word_segments[i]['start'] = previous_end
                word_segments[i]['end'] = previous_end + 4
            else:
                word_segments[i]['start'] = previous_end
                if 'start' in word_segments[i + 1]:
                    word_segments[i]['end'] = word_segments[i + 1]['start']
                else:
                    word_segments[i]['end'] = previous_end + 4
        elif 'end' in word_segments[i]:
            previous_end = word_segments[i]['end']

    # Create the filename for the srt file
    file = "saved_srt_files/" + save_to + "_subtitles.srt"

    # Remove the existing srt file if it exists
    if os.path.exists(file):
        os.remove(file)

    # Start writing to the srt file
    with open(file, 'a', encoding='utf-8') as srtFile:
        # If the first word does not start at 0, add an empty subtitle at the beginning
        if word_segments[0]['start'] != 0:
            srtFile.write("1\n00:00:00,000 --> " + convert_seconds_to_time(word_segments[0]['start']) + "\n\n")

        # Initialize the variables for the current srt segment
        srt_segment_n = 1 if word_segments[0]['start'] == 0 else 2
        current_block = ""
        block_start_time = convert_seconds_to_time(word_segments[0]['start'])
        block_end_time = block_start_time

        # Generate srt segments
        for i, word in enumerate(word_segments):
            next_word = word["word"] + " "

            # Check if adding the word to the block would cross a sentence boundary or exceed the character limit
            if re.search(r'[.!?]\s*$', current_block) or len(current_block + next_word) > max_chars:
                # Write out the current block
                segment = f"{srt_segment_n}\n{block_start_time} --> {block_end_time}\n{current_block.strip()}\n\n"
                srtFile.write(segment)

                # Start a new block with the current word
                srt_segment_n += 1
                block_start_time = block_end_time
                current_block = next_word
            else:
                current_block += next_word
                block_end_time = convert_seconds_to_time(word['end'])

        # Write out the last block if there's anything left
        if current_block.strip() != "":
            segment = f"{srt_segment_n}\n{block_start_time} --> {block_end_time}\n{current_block.strip()}\n\n"
            srtFile.write(segment)

    file = os.path.basename(file)
    return file
