from moviepy.editor import VideoFileClip, ImageClip, concatenate_videoclips, AudioFileClip
from moviepy.video.fx.all import crop
from moviepy.video.fx.all import speedx

def trim_clip(clip, start_trim, end_trim):
    """
    Trim a video clip to fit a new length between start_trim and end_trim.
    
    :param clip: VideoFileClip instance representing the video to trim.
    :param start_trim: Start trim point in seconds.
    :param end_trim: End trim point in seconds.
    
    :return: Adjusted video clip.
    """
    if start_trim < 0 or end_trim < 0:
        print("end_trim::",end_trim,"start_trim::",start_trim)
        raise ValueError("Start and end trim points must be non-negative.")
    if start_trim >= end_trim:
        raise ValueError("End trim point must be greater than start trim point.")

    trimmed_clip = clip.subclip(start_trim, None)  # Trim from start_trim to the end of the clip
    current_duration = trimmed_clip.duration

    if current_duration == (end_trim - start_trim):
        print("Clip is already the target duration.")
        return trimmed_clip
    elif (end_trim - start_trim) < current_duration:
        print("Trimming clip...")
        return trimmed_clip.subclip(0, end_trim - start_trim)
    else:
        print("Extending clip by slowing down...")
        # Calculate the factor by which to slow down the clip
        speed_factor = current_duration / (end_trim - start_trim)
        slowed_clip = trimmed_clip.fx(speedx, speed_factor)
        return slowed_clip

# Example usage
# clip = VideoFileClip("path_to_your_video.mp4")
# new_clip = trim_or_extend_clip(clip, start_trim=4, end_trim=8)
# new_clip.write_videofile("output_video.mp4")

def crop_clip(video_clip, width=900, height=900):
    """
    Crop a video to a specific size, maintaining its center.
    
    :param video_clip: VideoFileClip instance of the video.
    :param width: Desired width of the cropped video.
    :param height: Desired height of the cropped video.
    
    :return: Cropped (and possibly resized) VideoFileClip.
    """
    
    # If clip's width and height match the desired dimensions, return the clip
    if video_clip.w == width and video_clip.h == height:
        print("Video is already the desired size")
        return video_clip
    
    current_aspect_ratio = video_clip.w / video_clip.h
    target_aspect_ratio = width / height

    # Calculate the cropping dimensions based on the aspect ratios
    if current_aspect_ratio > target_aspect_ratio:
        crop_width = video_clip.h * target_aspect_ratio
        crop_height = video_clip.h
    else:
        crop_width = video_clip.w
        crop_height = video_clip.w / target_aspect_ratio

    # Crop the video clip
    cropped_clip = crop(video_clip, width=crop_width, height=crop_height, 
                        x_center=video_clip.w/2, y_center=video_clip.h/2)

    # Resize the cropped video to the desired dimensions
    resized_clip = cropped_clip.resize(width=width, height=height)

    return resized_clip


# Usage
# clip = VideoFileClip("composed_videos/final_video123/0.mp4")
# new_clip = crop_clip(clip, width=1600, height=900)
# new_clip.write_videofile("output_video_2.mp4")

