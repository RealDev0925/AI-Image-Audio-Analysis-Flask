from moviepy.editor import TextClip, CompositeVideoClip, concatenate_videoclips,VideoFileClip, ColorClip
import numpy as np
import ffmpeg



def is_punctuation(char):
    # Add more punctuation characters if necessary
    punctuation_chars = ".,;!?-"
    return char in punctuation_chars

def split_text_into_lines(data):

    MaxChars = 18
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






def create_caption(textJSON, framesize, font = "Helvetica", color='white', highlight_color='yellow', stroke_color='black',stroke_width=1.5):
    wordcount = len(textJSON['textcontents'])
    full_duration = textJSON['end']-textJSON['start']

    word_clips = []
    xy_textclips_positions =[]

    x_pos = 0
    y_pos = 0
    line_width = 0  # Total width of words in the current line
    frame_width = framesize[0]
    frame_height = framesize[1]
    x_buffer = frame_width*1/10
    max_line_width = frame_width - 2 * (x_buffer)
    fontsize = int(frame_height * 0.075) #7.5 percent of video height

    space_width = ""
    space_height = ""

    for index,wordJSON in enumerate(textJSON['textcontents']):
      duration = wordJSON['end']-wordJSON['start']
      word_clip = TextClip(wordJSON['word'], font = font,fontsize=fontsize, color=color,stroke_color=stroke_color,stroke_width=stroke_width).set_start(textJSON['start']).set_duration(full_duration)
      word_clip_space = TextClip(" ", font = font,fontsize=fontsize, color=color).set_start(textJSON['start']).set_duration(full_duration)
      word_width, word_height = word_clip.size
      space_width,space_height = word_clip_space.size
      if line_width + word_width+ space_width <= max_line_width:
            # Store info of each word_clip created
            xy_textclips_positions.append({
                "x_pos":x_pos,
                "y_pos": y_pos,
                "width" : word_width,
                "height" : word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position((x_pos+ word_width, y_pos))

            x_pos = x_pos + word_width+ space_width
            line_width = line_width+ word_width + space_width

      else:
            # Move to the next line
            x_pos = 0
            y_pos = y_pos+ word_height+10
            line_width = word_width + space_width

            # Store info of each word_clip created
            xy_textclips_positions.append({
                "x_pos":x_pos,
                "y_pos": y_pos,
                "width" : word_width,
                "height" : word_height,
                "word": wordJSON['word'],
                "start": wordJSON['start'],
                "end": wordJSON['end'],
                "duration": duration
            })

            word_clip = word_clip.set_position((x_pos, y_pos))
            word_clip_space = word_clip_space.set_position((x_pos+ word_width , y_pos))
            x_pos = word_width + space_width


      word_clips.append(word_clip)
      word_clips.append(word_clip_space)


    for highlight_word in xy_textclips_positions:

      word_clip_highlight = TextClip(highlight_word['word'], font = font,fontsize=fontsize, color=highlight_color,stroke_color=stroke_color,stroke_width=stroke_width).set_start(highlight_word['start']).set_duration(highlight_word['duration'])
      word_clip_highlight = word_clip_highlight.set_position((highlight_word['x_pos'], highlight_word['y_pos']))
      word_clips.append(word_clip_highlight)

    return word_clips,xy_textclips_positions






import cv2
import numpy as np



def find_dominant_color_in_first_frame(clip, k=1):
    """
    Find the dominant color in the first frame of a MoviePy clip.
    
    :param clip: MoviePy VideoFileClip object
    :param k: Number of clusters for K-means
    :return: Dominant color in RGB format
    """
    # Get the first frame
    first_frame = clip.get_frame(0)

    # Convert the frame to BGR color space for OpenCV
    first_frame_bgr = cv2.cvtColor(first_frame, cv2.COLOR_RGB2BGR)

    # Reshape the image to a 2D array of pixels and 3 color values (RGB)
    pixels = np.float32(first_frame_bgr.reshape(-1, 3))

    # Define criteria for kmeans and apply kmeans()
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
    _, labels, centers = cv2.kmeans(pixels, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

    # Convert to int and get the dominant color
    dominant_color = np.uint8(centers)[0]

    # Convert dominant color from BGR to RGB
    return dominant_color[::-1]



def get_subs_clip(words_list,input_video):


    # Find the dominant color
    dominant_color = find_dominant_color_in_first_frame(input_video)
    print("Dominant color (RGB):", dominant_color)


    linelevel_subtitles = split_text_into_lines(words_list)
        
    frame_size = input_video.size

    first_frame = input_video.get_frame(0)



    all_linelevel_splits = []

    for line in linelevel_subtitles:
        out_clips,positions = create_caption(line, frame_size)

        max_width = 0
        max_height = 0

        for position in positions:
            x_pos, y_pos = position['x_pos'],position['y_pos']
            width, height = position['width'],position['height']

            max_width = max(max_width, x_pos + width)
            max_height = max(max_height, y_pos + height)

        color_clip = ColorClip(size=(int(max_width*1.1), int(max_height*1.1)), color=dominant_color)
        color_clip = color_clip.set_opacity(.6)
        color_clip = color_clip.set_start(line['start']).set_duration(line['end']-line['start'])

        clip_to_overlay = CompositeVideoClip([color_clip]+ out_clips)
        clip_to_overlay = clip_to_overlay.set_position(("center",0.8), relative=True)
        all_linelevel_splits.append(clip_to_overlay)

    final_video = CompositeVideoClip([input_video] + all_linelevel_splits)
    return final_video







# input_video = VideoFileClip("/Users/georgebennett/Documents/Code/script_writer/burn_subs_2_test.mp4")
# words_list = [{'end': 0.228, 'word': 'Once', 'score': 0.752, 'start': 0.088}, {'end': 0.488, 'word': 'upon', 'score': 0.761, 'start': 0.288}, {'end': 0.548, 'word': 'a', 'score': 1.0, 'start': 0.528}, {'end': 0.928, 'word': 'time,', 'score': 0.76, 'start': 0.608}, {'end': 1.068, 'word': 'in', 'score': 0.835, 'start': 0.988}, {'end': 1.128, 'word': 'a', 'score': 0.999, 'start': 1.108}, {'end': 1.548, 'word': 'small,', 'score': 0.882, 'start': 1.208}, {'end': 2.008, 'word': 'forgotten', 'score': 0.974, 'start': 1.628}, {'end': 2.389, 'word': 'village,', 'score': 0.805, 'start': 2.048}, {'end': 2.889, 'word': 'there', 'score': 0.801, 'start': 2.749}, {'end': 3.109, 'word': 'lived', 'score': 0.903, 'start': 2.929}, {'end': 3.189, 'word': 'a', 'score': 0.5, 'start': 3.149}, {'end': 3.409, 'word': 'young', 'score': 0.846, 'start': 3.229}, {'end': 3.789, 'word': 'person', 'score': 0.891, 'start': 3.469}, {'end': 4.029, 'word': 'named', 'score': 0.803, 'start': 3.829}, {'end': 4.489, 'word': 'Alex,', 'score': 0.807, 'start': 4.209}, {'end': 5.129, 'word': 'whose', 'score': 0.795, 'start': 4.949}, {'end': 5.409, 'word': 'days', 'score': 0.633, 'start': 5.149}, {'end': 5.609, 'word': 'were', 'score': 0.752, 'start': 5.469}, {'end': 5.909, 'word': 'spent', 'score': 0.792, 'start': 5.649}, {'end': 6.369, 'word': 'toiling', 'score': 0.798, 'start': 5.969}, {'end': 6.45, 'word': 'in', 'score': 0.762, 'start': 6.389}, {'end': 6.57, 'word': 'the', 'score': 0.833, 'start': 6.49}, {'end': 6.95, 'word': 'fields', 'score': 0.736, 'start': 6.61}, {'end': 7.17, 'word': 'under', 'score': 0.894, 'start': 7.01}, {'end': 7.31, 'word': 'the', 'score': 0.811, 'start': 7.21}, {'end': 7.57, 'word': 'harsh', 'score': 0.892, 'start': 7.33}, {'end': 7.91, 'word': 'sun.', 'score': 0.672, 'start': 7.63}, {'end': 9.41, 'word': "Alex's", 'score': 0.844, 'start': 9.05}, {'end': 9.87, 'word': 'clothes', 'score': 0.849, 'start': 9.47}, {'end': 10.05, 'word': 'were', 'score': 0.816, 'start': 9.91}, {'end': 10.63, 'word': 'threadbare,', 'score': 0.882, 'start': 10.11}, {'end': 11.131, 'word': 'and', 'score': 0.844, 'start': 11.051}, {'end': 11.271, 'word': 'their', 'score': 0.913, 'start': 11.151}, {'end': 11.611, 'word': 'meals', 'score': 0.764, 'start': 11.311}, {'end': 11.791, 'word': 'were', 'score': 0.856, 'start': 11.651}, {'end': 12.091, 'word': 'often', 'score': 0.821, 'start': 11.851}, {'end': 12.391, 'word': 'nothing', 'score': 0.776, 'start': 12.131}, {'end': 12.571, 'word': 'more', 'score': 0.865, 'start': 12.431}, {'end': 12.751, 'word': 'than', 'score': 0.659, 'start': 12.611}, {'end': 13.231, 'word': 'scraps,', 'score': 0.79, 'start': 12.811}, {'end': 13.931, 'word': 'but', 'score': 0.834, 'start': 13.831}, {'end': 14.091, 'word': 'they', 'score': 0.736, 'start': 13.951}, {'end': 14.451, 'word': 'harbored', 'score': 0.837, 'start': 14.111}, {'end': 14.531, 'word': 'a', 'score': 0.52, 'start': 14.491}, {'end': 14.871, 'word': 'dream', 'score': 0.785, 'start': 14.571}, {'end': 15.232, 'word': 'brighter', 'score': 0.821, 'start': 14.911}, {'end': 15.392, 'word': 'than', 'score': 0.875, 'start': 15.272}, {'end': 15.492, 'word': 'the', 'score': 0.839, 'start': 15.412}, {'end': 15.852, 'word': 'richest', 'score': 0.833, 'start': 15.532}, {'end': 16.172, 'word': 'gold.', 'score': 0.702, 'start': 15.872}, {'end': 17.752, 'word': 'One', 'score': 0.772, 'start': 17.652}, {'end': 17.992, 'word': 'day,', 'score': 0.75, 'start': 17.772}, {'end': 18.772, 'word': 'while', 'score': 0.796, 'start': 18.592}, {'end': 19.273, 'word': 'wandering', 'score': 0.757, 'start': 18.832}, {'end': 19.353, 'word': 'in', 'score': 0.903, 'start': 19.293}, {'end': 19.453, 'word': 'the', 'score': 1.0, 'start': 19.393}, {'end': 19.893, 'word': 'forest,', 'score': 0.759, 'start': 19.513}, {'end': 20.693, 'word': 'Alex', 'score': 0.815, 'start': 20.473}, {'end': 21.093, 'word': 'stumbled', 'score': 0.861, 'start': 20.733}, {'end': 21.393, 'word': 'upon', 'score': 0.822, 'start': 21.153}, {'end': 21.473, 'word': 'a', 'score': 0.5, 'start': 21.433}, {'end': 21.813, 'word': 'hidden,', 'score': 0.793, 'start': 21.533}, {'end': 22.353, 'word': 'ancient', 'score': 0.889, 'start': 22.073}, {'end': 22.953, 'word': 'library,', 'score': 0.719, 'start': 22.413}, {'end': 23.734, 'word': 'brimming', 'score': 0.817, 'start': 23.433}, {'end': 23.934, 'word': 'with', 'score': 0.696, 'start': 23.774}, {'end': 24.414, 'word': 'forgotten', 'score': 0.841, 'start': 24.014}, {'end': 24.834, 'word': 'knowledge', 'score': 0.792, 'start': 24.454}, {'end': 24.974, 'word': 'and', 'score': 0.605, 'start': 24.894}, {'end': 25.334, 'word': 'wisdom.', 'score': 0.931, 'start': 25.034}, {'end': 26.67, 'word': 'Night', 'score': 0.636, 'start': 26.47}, {'end': 26.93, 'word': 'after', 'score': 0.89, 'start': 26.73}, {'end': 27.191, 'word': 'night,', 'score': 0.754, 'start': 26.99}, {'end': 27.751, 'word': 'they', 'score': 0.92, 'start': 27.631}, {'end': 28.091, 'word': 'poured', 'score': 0.685, 'start': 27.791}, {'end': 28.291, 'word': 'over', 'score': 0.76, 'start': 28.151}, {'end': 28.391, 'word': 'the', 'score': 0.999, 'start': 28.331}, {'end': 28.731, 'word': 'books,', 'score': 0.875, 'start': 28.451}, {'end': 29.552, 'word': 'learning', 'score': 0.834, 'start': 29.252}, {'end': 29.812, 'word': 'about', 'score': 0.858, 'start': 29.592}, {'end': 30.292, 'word': 'science,', 'score': 0.917, 'start': 29.892}, {'end': 30.913, 'word': 'art,', 'score': 0.805, 'start': 30.753}, {'end': 31.433, 'word': 'and', 'score': 0.792, 'start': 31.353}, {'end': 31.513, 'word': 'the', 'score': 0.999, 'start': 31.453}, {'end': 31.933, 'word': 'secrets', 'score': 0.826, 'start': 31.573}, {'end': 32.053, 'word': 'of', 'score': 0.75, 'start': 31.993}, {'end': 32.153, 'word': 'the', 'score': 0.834, 'start': 32.073}, {'end': 32.654, 'word': 'universe.', 'score': 0.691, 'start': 32.234}, {'end': 33.855, 'word': 'With', 'score': 0.826, 'start': 33.734}, {'end': 34.035, 'word': 'this', 'score': 0.768, 'start': 33.895}, {'end': 34.575, 'word': 'newfound', 'score': 0.867, 'start': 34.115}, {'end': 34.975, 'word': 'knowledge,', 'score': 0.817, 'start': 34.615}, {'end': 35.816, 'word': 'Alyx', 'score': 0.724, 'start': 35.556}, {'end': 36.236, 'word': 'invented', 'score': 0.889, 'start': 35.856}, {'end': 36.316, 'word': 'a', 'score': 0.494, 'start': 36.276}, {'end': 36.896, 'word': 'remarkable', 'score': 0.885, 'start': 36.376}, {'end': 37.317, 'word': 'device', 'score': 0.878, 'start': 36.936}, {'end': 37.497, 'word': 'that', 'score': 0.757, 'start': 37.357}, {'end': 37.677, 'word': 'could', 'score': 0.897, 'start': 37.517}, {'end': 37.977, 'word': 'clean', 'score': 0.887, 'start': 37.717}, {'end': 38.317, 'word': 'water', 'score': 0.813, 'start': 38.037}, {'end': 38.497, 'word': 'with', 'score': 0.732, 'start': 38.357}, {'end': 39.018, 'word': 'incredible', 'score': 0.853, 'start': 38.537}, {'end': 39.618, 'word': 'efficiency,', 'score': 0.816, 'start': 39.058}, {'end': 40.939, 'word': 'revolutionizing', 'score': 0.876, 'start': 40.118}, {'end': 41.059, 'word': 'the', 'score': 0.833, 'start': 40.979}, {'end': 41.379, 'word': 'lives', 'score': 0.8, 'start': 41.099}, {'end': 41.499, 'word': 'of', 'score': 0.75, 'start': 41.439}, {'end': 41.799, 'word': 'many.', 'score': 0.784, 'start': 41.559}, {'end': 43.12, 'word': 'News', 'score': 0.851, 'start': 42.9}, {'end': 43.22, 'word': 'of', 'score': 0.75, 'start': 43.16}, {'end': 43.68, 'word': "Alyx's", 'score': 0.759, 'start': 43.32}, {'end': 44.161, 'word': 'invention', 'score': 0.915, 'start': 43.74}, {'end': 44.521, 'word': 'spread', 'score': 0.792, 'start': 44.221}, {'end': 44.741, 'word': 'like', 'score': 0.746, 'start': 44.561}, {'end': 45.421, 'word': 'wildfire,', 'score': 0.81, 'start': 44.801}, {'end': 46.102, 'word': 'bringing', 'score': 0.793, 'start': 45.802}, {'end': 46.442, 'word': 'wealth,', 'score': 0.777, 'start': 46.162}, {'end': 47.102, 'word': 'fame,', 'score': 0.778, 'start': 46.782}, {'end': 47.263, 'word': 'and', 'score': 0.675, 'start': 47.163}, {'end': 47.983, 'word': 'opportunities', 'score': 0.865, 'start': 47.323}, {'end': 48.363, 'word': 'beyond', 'score': 0.785, 'start': 48.043}, {'end': 48.543, 'word': 'their', 'score': 0.818, 'start': 48.403}, {'end': 49.024, 'word': 'wildest', 'score': 0.812, 'start': 48.583}, {'end': 49.384, 'word': 'dreams.', 'score': 0.824, 'start': 49.064}, {'end': 50.507, 'word': 'From', 'score': 0.895, 'start': 50.367}, {'end': 50.607, 'word': 'the', 'score': 0.832, 'start': 50.527}, {'end': 51.027, 'word': 'shadows', 'score': 0.878, 'start': 50.647}, {'end': 51.147, 'word': 'of', 'score': 0.689, 'start': 51.067}, {'end': 51.748, 'word': 'obscurity,', 'score': 0.775, 'start': 51.207}, {'end': 52.508, 'word': 'Alyx', 'score': 0.788, 'start': 52.268}, {'end': 52.628, 'word': 'had', 'score': 0.769, 'start': 52.528}, {'end': 52.968, 'word': 'risen', 'score': 0.875, 'start': 52.708}, {'end': 53.069, 'word': 'to', 'score': 0.942, 'start': 53.008}, {'end': 53.369, 'word': 'become', 'score': 0.925, 'start': 53.109}, {'end': 53.449, 'word': 'a', 'score': 0.5, 'start': 53.409}, {'end': 53.809, 'word': 'beacon', 'score': 0.872, 'start': 53.489}, {'end': 53.889, 'word': 'of', 'score': 0.75, 'start': 53.829}, {'end': 54.189, 'word': 'hope', 'score': 0.998, 'start': 53.969}, {'end': 54.389, 'word': 'and', 'score': 0.833, 'start': 54.309}, {'end': 54.93, 'word': 'innovation,', 'score': 0.929, 'start': 54.409}, {'end': 55.81, 'word': 'proving', 'score': 0.811, 'start': 55.51}, {'end': 55.95, 'word': 'that', 'score': 0.984, 'start': 55.85}, {'end': 56.27, 'word': 'even', 'score': 0.852, 'start': 56.09}, {'end': 56.39, 'word': 'the', 'score': 0.834, 'start': 56.31}, {'end': 56.851, 'word': 'humblest', 'score': 0.831, 'start': 56.43}, {'end': 57.351, 'word': 'beginnings', 'score': 0.868, 'start': 56.911}, {'end': 57.551, 'word': 'can', 'score': 0.982, 'start': 57.411}, {'end': 57.771, 'word': 'lead', 'score': 0.996, 'start': 57.591}, {'end': 57.931, 'word': 'to', 'score': 0.663, 'start': 57.811}, {'end': 58.672, 'word': 'extraordinary', 'score': 0.743, 'start': 57.991}, {'end': 59.212, 'word': 'destinies.', 'score': 0.831, 'start': 58.732}]

# # final_video = get_subs_clip(words_list, input_video)
# # # final_video.set_audio(input_video.audio)
# # final_video.write_videofile("output.mp4", fps=24, codec="libx264", audio_codec="aac")


