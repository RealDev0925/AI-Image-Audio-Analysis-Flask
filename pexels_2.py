import os
import time
import requests
from dotenv import load_dotenv
from urllib.parse import urlparse
import random

# Custom modules for media and database operations
import media
import funcs_supabase

class PexelsProcessor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {'Authorization': api_key}
        self.base_url = 'https://api.pexels.com/videos/search'

    def get_media(self, query, per_page=30, orientation='landscape', max_retries=3, delay=5):
        """Fetch media from Pexels API."""
        params = {'query': query, 'per_page': per_page, 'orientation': orientation}
        with requests.Session() as session:
            session.headers.update(self.headers)
            for i in range(max_retries):
                try:
                    response = session.get(self.base_url, params=params)
                    response.raise_for_status()
                    print(response.json())
                    return response.json().get("videos", [])
                except requests.HTTPError as e:
                    print(f"HTTP error on attempt {i + 1}: {e}")
                except requests.RequestException as e:
                    print(f"Request exception on attempt {i + 1}: {e}")
                time.sleep(delay)
            print("Request failed after maximum retries.")
            return None

    def get_random_image(self, max_retries=3, delay=5):
        """Fetch a random image from Pexels and return the original image URL."""
        curated_url = 'https://api.pexels.com/v1/curated'
        params = {'per_page': 80}
        with requests.Session() as session:
            session.headers.update(self.headers)
            for i in range(max_retries):
                try:
                    response = session.get(curated_url, params=params)

                    response.raise_for_status()

                    photos = response.json().get("photos", [])
                    if photos:
                        photos_len = len(photos)
                        random_index = random.randint(0, photos_len - 1)
                
                        return photos[random_index]["src"]["original"]
                
                except requests.HTTPError as e:
                    print(f"HTTP error on attempt {i + 1}: {e}")
                except requests.RequestException as e:
                    print(f"Request exception on attempt {i + 1}: {e}")
                time.sleep(delay)
            print("Request failed after maximum retries.")
            return None

        
    @staticmethod
    def extract_description(url):
        """Extract description from Pexels URL."""
        parsed_url = urlparse(url)
        path_elements = parsed_url.path.split('/')
        path_element = next((el for el in reversed(path_elements) if el), None)
        return '-'.join(path_element.split('-')[:-1]).replace('-', ' ') if path_element else "Invalid URL"

    @staticmethod
    def download_image(image_url, folder='uploads'):
        """Download and save an image."""
        response = requests.get(image_url)
        if response.status_code == 200:
            parsed_url = urlparse(image_url)
            filename = os.path.basename(parsed_url.path)
            filepath = os.path.join(folder, filename)
            with open(filepath, 'wb') as f:
                f.write(response.content)
                print(f"Saved {filename} to disk.")
            return filepath
        else:
            print(f"Failed to download image: {image_url}")
            return None

    def process_item(self, item, keyword):
        """Process a single item from Pexels."""
        image_url = item["image"]
        filepath = self.download_image(image_url)
        if filepath:
            media_table_response = media.upload_media_to_supabase(filepath)
            os.remove(filepath)  # Delete image after processing
            media_id = media_table_response.get("id")
            current_url = media_table_response.get("url")

            # Determine media type
            type = "video" if item.get("video_files") else "image"
            remote_url = item.get("video_files", [{}])[0].get("link", None)
            description = self.extract_description(item.get("url"))

            new_data = {
            "url": None,
            "thumbnail_url": current_url,
            "url_remote": remote_url,
            "source_type": "stock",
            "source": "Pexels",
            "source_data": item,
            "type": type,
            "source_id": item.get("id"),
            "description": description,
            "input_phrase": keyword,
            }
            
            funcs_supabase.update_data("media", media_id, new_data)

def check_database_empty(pexels_id):
    """make sure we dont have the same id in the database"""
    table = "media"
    column = "source_id"
    id_check = funcs_supabase.select_data(table, column, pexels_id)
    if id_check:
        # print("The list is not empty. Stop")
        return False
    else:
        # print("The list is empty. Proceed")
        return True


def process_pexels_keywords(kw_list):
    success_counter = 0
    pexels_processor = PexelsProcessor(os.getenv('PEXELS_API_KEY'))

    for kw in kw_list:
        media_items = pexels_processor.get_media(kw)
        if media_items:
            for item in media_items:
                if check_database_empty(item.get("id")):
                    pexels_processor.process_item(item, kw)
                    time.sleep(3)
                    success_counter += 1
        else:
            print(f"No media found for {kw}.")
    print(f"Processed {success_counter} items.")


def random_image():
    load_dotenv()
    pexels_processor = PexelsProcessor(os.getenv('PEXELS_API_KEY'))
    random_image_url = pexels_processor.get_random_image()
    if random_image_url:
        print("Random image URL:", random_image_url)
    else:
        print("No random image found.")

    return random_image_url



# random_image()

# if __name__ == "__main__":
#     load_dotenv()
#     kw_list = ["Hot Dog", "Burger", "Fish And Chips"]
#     process_pexels_keywords(kw_list)
