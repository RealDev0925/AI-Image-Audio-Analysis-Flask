import json
from jinja2 import Template
import random
import uuid
import json
import urllib.request
import urllib.parse
import time
import requests

server_address = "comfy.ngrok.app"

client_id = str(uuid.uuid4())
# print(client_id)


def queue_prompt(prompt):
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p)
    req_url = f"https://{server_address}/prompt"
    response = requests.post(req_url, data=data)
    return response.json()


# Function to get an image from the server
def get_image(filename, subfolder, folder_type):
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    response = requests.get(f"https://{server_address}/view", params=params)
    return response.content


# Function to get the history of a prompt
def get_history(prompt_id):
    response = requests.get(f"https://{server_address}/history/{prompt_id}")
    return response.json()


def check_status(prompt_id):
    response = requests.get(f'https://{server_address}/prompt')
    if response.status_code == 200:
        data = json.loads(response.text)
        print(data)
        queue_remaining=data['exec_info']['queue_remaining']
        if queue_remaining == 0:
            print("done")
            return {'status': 'done'}
        else:
            print("not done")
            return {'status': 'not done'}



def get_images(prompt):
    # 1. Queue the prompt and get a prompt ID.
    queue_response = queue_prompt(prompt)
    prompt_id = queue_response['prompt_id']
    print(f"prompt_id: {prompt_id}")
    
    # Initialize an empty dictionary to store output images.
    output_images = {}

    # 2. Poll the server until the job corresponding to the prompt ID is done.
    while True:
        # Check the status of the prompt job.
        status = check_status(prompt_id)
        
        # If the status is 'done', break out of the loop.
        if status['status'] == 'done':
            break

        # Wait for 3 seconds before polling again.
        time.sleep(2)

    # 3. Retrieve the output history corresponding to the prompt ID.
    history = get_history(prompt_id)[prompt_id]
    # print("HISTORY")
    # print(history)

    # 4. Loop through the output history to gather image data.
    for node_id, node_output in history['outputs'].items():
        # Initialize an empty list to store images for each node.
        images_output = []
        
        # Check if 'images' key exists in the output for the current node.
        if 'images' in node_output:
            # Loop through each image and get its data.
            for image in node_output['images']:
                filename = image['filename']
                subfolder = image['subfolder']
                image_type = image['type']
                
                # Fetch the image data.
                image_data = get_image(filename, subfolder, image_type)
                
                # Append the image data to the list.
                images_output.append(image_data)
        
        # Store the list of images for the current node in the output_images dictionary.
        output_images[node_id] = images_output

    # 5. Return the output_images dictionary.
    return output_images


def collect_image_binaries(images_dict):
    image_binaries = []
    for node_id in images_dict:
        # print(f"node_id: {node_id}")

        for image_data in images_dict[node_id]:
            # print(f"image_data: {image_data}")
            image_binaries.append(image_data)
    return image_binaries


def get_models():
    req_url = f"https://{server_address}/object_info"
    response = requests.get(req_url)
    response= response.json()
    # models= response['CheckpointLoaderSimple']["input"]["required"]["ckpt_name"][0]
    models= response['CheckpointLoader']["input"]["required"]["ckpt_name"][0]
    print(models)
    return models



###################################
###################################
###################################
