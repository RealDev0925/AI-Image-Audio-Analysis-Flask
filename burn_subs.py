from moviepy.editor import TextClip, CompositeVideoClip, ColorClip
import numpy as np
from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips,VideoFileClip, ColorClip
import json 



def is_punctuation(char):
    # Add more punctuation characters if necessary
    punctuation_chars = ".,;!?-"
    return char in punctuation_chars

def split_text_into_lines(data):

    MaxChars = 21
    #maxduration in seconds
    MaxDuration = 3.0
    #Split if nothing is spoken (gap) for these many seconds
    MaxGap = 0.5

    subtitles = []
    line = []
    line_duration = 0
    line_chars = 0

    for idx, word_data in enumerate(data):
        word = word_data["word"]
        start = word_data["start"]
        end = word_data["end"]

        line.append(word_data)
        line_duration += end - start

        temp = " ".join(item["word"] for item in line)
        punctuation_exceeded = is_punctuation(word[-1])

        # Check if adding a new word exceeds the maximum character count or duration
        new_line_chars = len(temp)

        duration_exceeded = line_duration > MaxDuration 
        chars_exceeded = new_line_chars > MaxChars 
        if idx > 0:
            gap = word_data['start'] - data[idx-1]['end']
            maxgap_exceeded = gap > MaxGap
        else:
            maxgap_exceeded = False

        if duration_exceeded or chars_exceeded or maxgap_exceeded or punctuation_exceeded:
            if line:
                subtitle_line = {
                    "word": " ".join(item["word"] for item in line),
                    "start": line[0]["start"],
                    "end": line[-1]["end"],
                    "textcontents": line
                }
                subtitles.append(subtitle_line)
                line = []
                line_duration = 0
                line_chars = 0

    if line:
        subtitle_line = {
            "word": " ".join(item["word"] for item in line),
            "start": line[0]["start"],
            "end": line[-1]["end"],
            "textcontents": line
        }
        subtitles.append(subtitle_line)

    return subtitles

from PIL import ImageColor


# def create_caption(textJSON, framesize, font="Impact", fontsize=60, color='white', highlight_bgcolor='black', stroke_color="black", stroke_width=2, align='center'):
# def create_caption(textJSON, framesize, font="Impact", fontsize=60, color='white', highlight_bgcolor='black', stroke_color="black", stroke_width=2, align='center', text_bg_color='blue', text_bg_opacity=0.5):
def create_caption(textJSON, framesize, font="Impact", fontsize=60, color='white', highlight_bgcolor='black', stroke_color="black", stroke_width=2, align='center', text_bg_color='blue', text_bg_opacity=0.5):


    # Calculate the total duration of the text
    full_duration = textJSON['end'] - textJSON['start']

    # Initialize variables
    word_clips = []
    xy_textclips_positions = []

    x_pos = 0
    y_pos = 0
    frame_width, frame_height = framesize
    x_buffer = frame_width * 1 / 10
    y_buffer = frame_height * 4 / 5

    yOffsetIfLineWrapped = 0 - fontsize


    # Convert color name to RGBA (assuming color name is valid)
    text_bg_rgba = ImageColor.getcolor(text_bg_color, "RGBA")

    # Adjust the alpha value to make the color semi-transparent
    text_bg_rgba_semitransparent = text_bg_rgba[:-1] + (int(text_bg_opacity * 255),)


    # Iterate through words
    for wordJSON in textJSON['textcontents']:
        # Calculate word's duration
        duration = wordJSON['end'] - wordJSON['start']

        # Create TextClip for word and space
        # word_clip = TextClip(wordJSON['word'], font=font, fontsize=fontsize, color=color, stroke_color=stroke_color, stroke_width=stroke_width, align=align, bg_color="blue").set_start(textJSON['start']).set_duration(full_duration)
        # word_clip_space = TextClip(" ", font=font, fontsize=fontsize, color=color, stroke_color=stroke_color, stroke_width=stroke_width, align=align, bg_color="blue").set_start(textJSON['start']).set_duration(full_duration)

        # Create TextClip for word and space (with semi-transparent background color)
        word_clip = (TextClip(wordJSON['word'], font=font, fontsize=fontsize, color=color, stroke_color=stroke_color, stroke_width=stroke_width, align=align)
                     .on_color(col_opacity=text_bg_opacity, size=(word_width+2*stroke_width, word_height+2*stroke_width), color=text_bg_rgba_semitransparent)
                     .set_start(textJSON['start']).set_duration(full_duration))
        
        word_clip_space = (TextClip(" ", font=font, fontsize=fontsize, color=color, stroke_color=stroke_color, stroke_width=stroke_width, align=align)
                           .on_color(col_opacity=text_bg_opacity, size=(space_width+2*stroke_width, space_height+2*stroke_width), color=text_bg_rgba_semitransparent)
                           .set_start(textJSON['start']).set_duration(full_duration))

        # Get the size of word and space
        word_width, word_height = word_clip.size
        space_width, space_height = word_clip_space.size

        # Check if the word needs to be moved to a new line
        if x_pos + word_width + space_width > frame_width - 2 * x_buffer:
            x_pos = 0
            y_pos = y_pos - yOffsetIfLineWrapped

        # Store info of each word_clip created
        info = {
            "x_pos": x_pos + x_buffer,
            "y_pos": y_pos + y_buffer,
            "width": word_width,
            "height": word_height,
            "word": wordJSON['word'],
            "start": wordJSON['start'],
            "end": wordJSON['end'],
            "duration": duration
        }
        xy_textclips_positions.append(info)

        # Set the position of the word and space
        word_clip = word_clip.set_position((x_pos + x_buffer, y_pos + y_buffer))
        word_clip_space = word_clip_space.set_position((x_pos + word_width + x_buffer, y_pos + y_buffer))

        # Update x_pos for the next word
        x_pos = x_pos + word_width + space_width

        # Append word and space clips to list
        word_clips.append(word_clip)
        word_clips.append(word_clip_space)

    # Iterate through xy_textclips_positions to create highlight word_clips
    for highlight_word in xy_textclips_positions:
        word_clip_highlight = TextClip(highlight_word['word'], font=font, fontsize=fontsize, color=color, bg_color=highlight_bgcolor, stroke_color=stroke_color, stroke_width=stroke_width, align=align).set_start(highlight_word['start']).set_duration(highlight_word['duration'])
        word_clip_highlight = word_clip_highlight.set_position((highlight_word['x_pos'], highlight_word['y_pos']))
        word_clips.append(word_clip_highlight)

    return word_clips



def get_subs_clip(words_list,input_video ):

    linelevel_subtitles = split_text_into_lines(words_list)

    # Load the input video
    # input_video = VideoFileClip(vid_with_audio)
    # get the frame size of the input video

    resolution = input_video.size
    # print(resolution)
    frame_size = (resolution[0],resolution[1])
    # frame_size = (900,900)

    all_linelevel_splits=[]

    for line in linelevel_subtitles:
        out = create_caption(line,frame_size)
        all_linelevel_splits.extend(out)



    # Get the duration of the input video
    input_video_duration = input_video.duration

    # Create a color clip with the given frame size, color, and duration
    # background_clip = ColorClip(size=frame_size, color=(0, 0, 0)).set_duration(input_video_duration)

    # If you want to overlay this on the original video uncomment this and also change frame_size, font size and color accordingly.
    final_video = CompositeVideoClip([input_video] + all_linelevel_splits)
    # final_video = CompositeVideoClip([input_video, all_linelevel_splits])  # By default, takes the duration of the longest clip


    return final_video


    # # final_video = CompositeVideoClip([background_clip] + all_linelevel_splits)
    # # Set the audio of the final video to be the same as the input video
    # final_video = final_video.set_audio(input_video.audio)
    # # Save the final clip as a video file with the audio included
    # final_video.write_videofile("final_output23.mp4", fps=24, codec="libx264", audio_codec="aac")


# print(TextClip.list('font'))