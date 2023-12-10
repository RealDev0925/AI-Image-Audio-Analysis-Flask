import os
import requests
from urllib.parse import urlparse, unquote

from urllib.parse import urlparse, unquote

def get_url_file_extension(url):
    """
    Extracts the file extension from a URL.

    Parameters:
    url (str): The URL from which to extract the file extension.

    Returns:
    str: The file extension without the leading dot, or an empty string if none is found.
    """

    try:
        # Unquote the URL to handle any encoded characters
        url = unquote(url)
        
        # Parse the URL into its components
        parsed_url = urlparse(url)

        # Split the path component of the URL to get the last part (typically the filename)
        path = parsed_url.path
        filename = path.split('/')[-1]

        # Split filename to get the extension, if present
        _, ext = os.path.splitext(filename)

        # Remove the leading dot and convert to lowercase
        return ext[1:].lower()
    
    except Exception as e:
        # In case of any error (e.g., bad URL format), return an empty string or handle as needed
        print(f"Error extracting file extension: {e}")
        return ""

# # Example usage
# url = "http://example.com/somefile.pdf?query=123"
# print(get_url_file_extension(url))  # Outputs 'pdf'


import os
import requests
from concurrent.futures import ThreadPoolExecutor

def download_file_from_url(url, save_path):
    """
    Download a single file from the provided URL and save it to the specified path.

    Parameters:
    - url (str): The URL of the file to download.
    - save_path (str): The local path where the file should be saved.
    
    Returns:
    - str: The save path of the downloaded file.
    """
    directory = os.path.dirname(save_path)
    os.makedirs(directory, exist_ok=True)
    
    response = requests.get(url, stream=True)
    response.raise_for_status()

    with open(save_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=8192):
            file.write(chunk)

    return save_path

def download_files(urls, save_paths):
    """
    Download multiple files from the provided URLs and save them to the specified paths.

    Parameters:
    - urls (list of str): The URLs of the files to download.
    - save_paths (list of str): The local paths where the files should be saved.
    
    Returns:
    - list of str: The save paths of the downloaded files.
    """
    with ThreadPoolExecutor() as executor:
        return list(executor.map(download_file_from_url, urls, save_paths))

# Example usage
# urls = ['http://example.com/file1', 'http://example.com/file2']
# save_paths = ['/path/to/save/file1', '/path/to/save/file2']
# downloaded_files = download_files(urls, save_paths)
