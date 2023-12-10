import os
import time
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
import media  # Assuming you have a media module that provides upload_media_to_supabase
import funcs_supabase  # Assuming you have a funcs_supabase module that provides update_data
import concurrent.futures



# Configuration setup
load_dotenv()
API_KEY = os.getenv('PEXELS_API_KEY')
BASE_URL = 'https://api.pexels.com/videos/search'
HEADERS = {'Authorization': API_KEY}


def get_pexels_media(query, per_page=80, orientation='landscape', max_retries=3, delay=5):
    """Fetch media from Pexels API based on given query parameters."""
    params = {'query': query, 'per_page': per_page, 'orientation': orientation}

    with requests.Session() as session:
        session.headers.update(HEADERS)

        for i in range(max_retries):
            try:
                response = session.get(BASE_URL, params=params)
                response.raise_for_status()
                return response.json().get("videos", [])
            
            except requests.HTTPError as e:
                print(f"HTTP error on attempt {i + 1}: {e}")
            except requests.RequestException as e:
                print(f"Request failed on attempt {i + 1}: {e}")

            time.sleep(delay)

        print(f"Request failed after {max_retries} attempts.")
        return None


def get_description_from_pexels_url(url):
    """Extract description from Pexels URL."""
    parsed_url = urlparse(url)
    path_elements = parsed_url.path.split('/')
    path_element = next((el for el in reversed(path_elements) if el), None)
    
    if path_element:
        extracted_part = '-'.join(path_element.split('-')[:-1])
        return extracted_part.replace('-', ' ')
    else:
        return "Invalid URL"


def download_image(image_url, folder='uploads'):
    """Download and save an image from the given URL."""
    response = requests.get(image_url)
    parsed_url = urlparse(image_url)
    filename = os.path.basename(parsed_url.path)

    if response.status_code == 200:
        filepath = os.path.join(folder, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)
            print(f"Saved {filename} to disk.")
        return filepath
    else:
        print(f"Failed to download image from {image_url}")
        return None


def process_pexels_item(item, kw):
    """Process a single item from Pexels API response."""
    image_url = item["image"]
    filepath = download_image(image_url)
    
    if filepath:
            try:
                # Upload media to Supabase and fetch response
                media_table_response = media.upload_media_to_supabase(filepath)
                media_id = media_table_response.get("id")
                current_url = media_table_response.get("url")

                # Determine media type
                type = "video" if item.get("video_files") else "image"
                remote_url = item.get("video_files", [{}])[0].get("link", None)
                description = get_description_from_pexels_url(item.get("url"))

                new_data = {
                    "url": remote_url,
                    "thumbnail_url": current_url,
                    "url_remote": None,
                    "source_type": "stock",
                    "source": "Pexels",
                    "source_data": item,
                    "type": type,
                    "source_id": item.get("id"),
                    "description": description,
                    "input_phrase": kw,
                }

                # Update Supabase data
                rsp = funcs_supabase.update_data("media", media_id, new_data)
                # print(rsp)
            finally:
                # Delete the downloaded image
                os.remove(filepath)
                print(f"Deleted {filepath} from disk.")


def check_database_empty(pexels_id):
    """make sure we dont have the same id in the database"""
    table = "media"
    column = "source_id"
    id_check = funcs_supabase.select_data(table, column, pexels_id)
    if id_check:
        print("The list is not empty. Stop")
        return False
    else:
        print("The list is empty. Proceed")
        return True


# def process_pexels_kw_list(kw_list):
#     success_counter = 0
#     for kw in kw_list:
#         # query = "cute dog"
#         media_items = get_pexels_media(kw)
#         print(f"Processing {len(media_items)} items for {kw}...")
#         if media_items:
#             for item in media_items:
#                 proceed = check_database_empty(item.get("id"))
#                 if proceed:
#                     process_pexels_item(item, kw)
#                     time.sleep(3)
#                     success_counter += 1
#         else:
#             print("No media found for the given query.")

#     print(f"Successfully processed {success_counter} items.")


def process_pexels_item_concurrent(item, kw):
    """Wrap the process_pexels_item function to include error handling for concurrent execution."""
    try:
        if check_database_empty(item.get("id")):
            process_pexels_item(item, kw)
    except Exception as e:
        print(f"Error processing item: {e}")


def process_pexels_kw_list(kw_list):
    success_counter = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Create a list to hold all the futures
        futures = []
        for kw in kw_list:
            media_items = get_pexels_media(kw)
            print(f"Processing {len(media_items)} items for {kw}...")
            if media_items:
                for item in media_items:
                    # Schedule the process_pexels_item function to be executed concurrently
                    future = executor.submit(process_pexels_item_concurrent, item, kw)
                    futures.append(future)

        # Wait for all futures to complete and count successes
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()  # Retrieve the result to re-raise any exceptions
                success_counter += 1
            except Exception as e:
                print(f"An error occurred: {e}")

    print(f"Successfully processed {success_counter} items.")

# kw_list = ["Dubai"]
# process_pexels_kw_list(kw_list)
