from PIL import Image
from dotenv import load_dotenv
import os
import funcs_supabase
import asyncio
import cv2
import uuid
import replicate
import openai

from openai.embeddings_utils import get_embedding, cosine_similarity
from supabase import create_client, Client


load_dotenv()  # Load environment variables from .env file
# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
supabase_subdomain = "fpyltvtkpkrkzortucoa"


def upload_file(bucket: str, file_path: str, file_content, file_type="text/plain"):
    """Upload a file to storage."""
    return supabase.storage.from_(bucket).upload(file_path, file_content, {"content-type": file_type})


# bucket="media"
# file_path="uploads/p1.jpg"


def upload_get_url (bucket,file_path,file_content ):
    """Upload a file to storage and return the public URL."""
    resp = supabase.storage.from_(bucket).upload(file_path, file_content)
    print(resp)
    if resp.status_code == 200:
        return f"https://{supabase_subdomain}.supabase.co/storage/v1/object/public/{bucket}/{file_path}"
    else:
        return None





def identify_media_type(file_path):
    # List of file extensions for video and image files
    video_extensions = ['.mp4', '.mkv', '.flv', '.avi']
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']

    # Get the file extension
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension in video_extensions:
        return 'video'
    elif file_extension in image_extensions:
        return 'image'
    
    else:
        # If the file extension doesn't match, try reading the file
        try:
            img = Image.open(file_path)
            img.close()
            return 'image'
        except:
            pass

        try:
            cap = cv2.VideoCapture(file_path)
            if cap.isOpened():
                cap.release()
                return 'video'
        except:
            pass
    
    return 'unknown'




# Generates a unique identifier
def make_uuid():
    return str(uuid.uuid4())



def get_clip_data(video_path, output_folder='uploads', file_extension='png'):
    # Initialize VideoCapture object
    cap = cv2.VideoCapture(video_path)

    # Initialize dictionary to store video info
    video_info = {}

    # Check if the video file was opened successfully
    if not cap.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return None

    # Read the first frame from the video
    ret, frame = cap.read()

    # If the first frame was read successfully
    if ret:
        unique_name = make_uuid()
        output_path = f"{output_folder}/{unique_name}.{file_extension}"
        cv2.imwrite(output_path, frame)

        # Save video information
        video_info['thumbnail'] = output_path
        video_info['width'] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_info['height'] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video_info['fps'] = int(cap.get(cv2.CAP_PROP_FPS))
        video_info['frame_count'] = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_info['duration'] = video_info['frame_count'] / video_info['fps']
        video_info['fourcc'] = int(cap.get(cv2.CAP_PROP_FOURCC))
        video_info['is_color'] = True if len(frame.shape) == 3 else False
        video_info['aspect_ratio'] = video_info['width'] / video_info['height']

        # Release the VideoCapture object
        cap.release()

        return video_info
    else:
        print("Failed to retrieve the first frame")
        return None


def get_image_data(image_path):
    # Read the image
    image = cv2.imread(image_path)

    # If the image was read successfully
    if image is not None:
        # Get image dimensions
        height, width, channels = image.shape
        
        # Calculate mean color
        mean_color = cv2.mean(image)
        
        # Create and populate a dictionary with the image data
        image_data = {
            'dimensions': {
                'width': width,
                'height': height,
                'channels': channels
            },
            'mean_color': mean_color,
            'file_size': os.path.getsize(image_path),
            'file_type': os.path.splitext(image_path)[1][1:]  # Get the extension without the dot
        }
        
        return image_data
    else:
        print(f"Error: Could not read image at {image_path}")
        return None



import magic

import magic

def get_file_extension_from_binary(binary_data):
    mime = magic.Magic(mime=True)

    # Get MIME type from binary data
    mime_type = mime.from_buffer(binary_data)
    
    # Map of common MIME types to file extensions
    extension_map = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'application/pdf': '.pdf',
        'text/plain': '.txt',
        'text/html': '.html',
        'application/msword': '.doc',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
        'application/vnd.ms-excel': '.xls',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        'application/vnd.ms-powerpoint': '.ppt',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': '.pptx',
        'application/xml': '.xml',
        'application/json': '.json',
        'application/zip': '.zip',
        'audio/mpeg': '.mp3',
        'video/mp4': '.mp4',
        'application/x-7z-compressed': '.7z',
        'image/gif': '.gif',
        'image/svg+xml': '.svg',
        'text/csv': '.csv',
        'application/java-archive': '.jar',
        'application/x-tar': '.tar',
        'image/webp': '.webp',
        'audio/wav': '.wav',
        'audio/ogg': '.ogg',
        'video/ogg': '.ogv',
        'application/ogg': '.ogx',
        'font/otf': '.otf',
        'font/ttf': '.ttf',
        'font/woff': '.woff',
        'font/woff2': '.woff2',
        'application/epub+zip': '.epub',
        # Add more mappings as needed
    }
    
    # Get the extension from the map or return None if not found
    extension = extension_map.get(mime_type)
    
    if extension:
        print("Detected extension:", extension)
    else:
        print("No extension detected for MIME type:", mime_type)
    
    return extension, mime_type


# # In your upload function, you can use it like this:
# def upload_to_supabase(bucket, file_input, is_binary=False):
#     if is_binary:
#         file_content = file_input
#         file_extension = get_file_extension_from_binary(file_content)
#         print(file_extension)
#     else:
#         with open(file_input, "rb") as f:
#             file_content = f.read()
#         filename, file_extension = os.path.splitext(file_input)


#     # Rename the file using a unique identifier
#     new_filename = make_uuid() + file_extension

#     # Upload the file to the bucket
#     supabase_resp = upload_file(bucket, new_filename, file_content)
    
#     if supabase_resp.status_code == 200:
#         return f"https://{supabase_subdomain}.supabase.co/storage/v1/object/public/{bucket}/{new_filename}"
#     else:
#         return None

# import os

import os
import mimetypes
from uuid import uuid4

def upload_to_supabase(bucket, file_input, is_binary=False, custom_filename=None):
    # Determine file content and extension
    if is_binary:
        file_content = file_input
        file_extension, file_type = get_file_extension_from_binary(file_content)

    else:
        with open(file_input, "rb") as f:
            file_content = f.read()
        file_type, file_extension = mimetypes.guess_type(file_input)

    print(f"File type: {file_type}")
    
    # Default MIME type to 'text/plain' if it couldn't be determined
    file_type = file_type if file_type else 'text/plain'
        
    # If a custom filename is provided, use it. Otherwise, generate a unique identifier.
    new_filename = custom_filename if custom_filename else str(uuid4()) + file_extension

    # Upload the file to the bucket
    supabase_resp = upload_file(bucket, new_filename, file_content, file_type=file_type)
    
    if supabase_resp.status_code == 200:
        return f"https://{supabase_subdomain}.supabase.co/storage/v1/object/public/{bucket}/{new_filename}"
    else:
        return None





# caption image using replicate / blip
def get_caption(file_path):
    try:
        with open(file_path, "rb") as file:
            input_data = {"image": file}
            output = replicate.run(
                "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
                input=input_data
            )
            return output
    except Exception as e:
        return str(e)


def get_caption_from_binary(file_contents):
    try:
        input_data = {"image": file_contents}
        output = replicate.run(
            "salesforce/blip:2e1dddc8621f72155f24cf2e0adbde548458d3cab9f00c0139eea840d0ac4746",
            input=input_data
        )
        return output
    except Exception as e:
        return str(e)



def get_embeddings(input = ""):
    """Get the vector embeddings from openAI for a given input string."""


    # replace new lines with spaces
    input = input.replace("\n", " ")

    # remove extra spaces
    input = " ".join(input.split())


    response = openai.Embedding.create( 
        input= input,
        model="text-embedding-ada-002"
    )

    embeddings = response['data'][0]['embedding']
    return embeddings


def get_similarity(input1, input2):
    """Get the similarity between two strings."""

    embedding1 = get_embeddings(input1)
    embedding2 = get_embeddings(input2)

    similarity = cosine_similarity(embedding1, embedding2)
    return similarity



def process_video(bucket, filepath):
        file_type = "video"
        public_url = upload_to_supabase(bucket, filepath)
        
        if public_url:
            # Get thumbnail and other video clip data
            clip_data = get_clip_data(filepath)
            thumbnail_local_path = clip_data["thumbnail"]
            
            # Upload the thumbnail to Supabase
            thumbnail_url = upload_to_supabase(bucket, thumbnail_local_path)

            # Get the caption for the thumbnail
            caption = get_caption(thumbnail_local_path).replace("Caption: ", "")
            
            # Insert media info into 'media' table
            media_data = {
                "url": public_url,
                "type": file_type,
                "caption": caption,
                "old_filename": os.path.basename(filepath),
                "bucket": bucket,
                "filename": os.path.basename(public_url),
                "media_data": clip_data,
                "thumbnail_url": thumbnail_url,
            }
            media_table_response = funcs_supabase.insert_data("media", media_data)
            media_id = media_table_response['id']

            # Get caption embeddings and insert into 'vectors' table
            caption_vector = get_embeddings(caption)
            vector_data = {
                "context": "video_thumbnail_caption",
                "content": caption,
                "embedding": caption_vector,
                "media_table_id": media_id
            }
            funcs_supabase.insert_data("vectors", vector_data)
            print("Vector data updated")

            # Delete the local thumbnail file
            os.remove(thumbnail_local_path)

            # returns data from new row in media table 
            return media_table_response




# Function to handle image files
def process_image(bucket, filepath):
    # Upload the image to Supabase and get the public URL
    public_url = upload_to_supabase(bucket, filepath)
    
    print("uploaded")

    if public_url:
        # Get the caption for the image
        caption = get_caption(filepath).replace("Caption: ", "")
        print(caption)

        image_data = get_image_data(filepath)
        print(image_data)
        
        # Insert media info into 'media' table
        media_data = {
            "url": public_url,
            "type": "image",
            "caption": caption,
            "old_filename": os.path.basename(filepath),
            "bucket": bucket,
            "filename": os.path.basename(public_url),
            "media_data": image_data,
        }
        media_table_response = funcs_supabase.insert_data("media", media_data)
        media_id = media_table_response['id']
        print("Media data updated")

        # Get caption embeddings and insert into 'vectors' table
        caption_vector = get_embeddings(caption)
        vector_data = {
            "context": "image_media_caption",
            "content": caption,
            "embedding": caption_vector,
            "media_table_id": media_id
        }
        
        resp = funcs_supabase.insert_data("vectors", vector_data)
        # vector_id = resp["id"]
        print("Vector data updated")

        return media_table_response

def upload_media_to_supabase(filepath):
    bucket = "media"

    # Identify the file type (video, image, or unknown)
    file_type = identify_media_type(filepath)

    if file_type == "video":
        # Process video
        media_id = process_video(bucket, filepath)
        print("video processed")
        return media_id
        
    elif file_type == "image":
        # Process image
        media_id = process_image(bucket, filepath)
        print("image processed")
        return media_id

    else:
        print("Unsupported file type")




# file = "/Users/georgebennett/Dropbox/Affiliate Stuff/Swipe File - Landing Pages - Ads/Y2Mate.is - Scientific Breakthrough Melts 73lbs of Fat-aH0cs4hPgZE-720p-1652800643719.mp4"
# upload_media_to_supabase(file)
